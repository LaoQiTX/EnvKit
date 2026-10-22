import dearpygui.dearpygui as dpg
from typing import Dict, Any
from core.analyzer import Analyzer
from utils.path_helper import get_backup_dir
from utils.win_utils import open_in_explorer
from gui.theme import (
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_MUTED,
    COLOR_PRIMARY, create_button_theme
)

class ConfigUI:
    def __init__(self, analyzer: Analyzer):
        self.analyzer = analyzer
        self.status_message_id = None
        self.model_list_id = None

    def build(self):
        btn_primary = create_button_theme((37, 99, 235), (59, 130, 246), (29, 78, 216))
        btn_danger = create_button_theme((220, 38, 38), (239, 68, 68), (185, 28, 28))
        btn_success = create_button_theme((16, 185, 129), (52, 211, 153), (5, 150, 105))

        with dpg.group(horizontal=True):
            # 左侧：模型列表管理
            with dpg.child_window(width=340, height=560, border=True):
                dpg.add_text("📋 已配置模型列表", color=COLOR_PRIMARY)
                dpg.add_spacer(height=4)
                
                self.model_list_id = dpg.add_listbox(
                    items=[self._format_model_item(m) for m in self.analyzer.models()],
                    num_items=12,
                    callback=self._on_select_model
                )
                
                dpg.add_spacer(height=8)
                b_def = dpg.add_button(label="设为默认模型", callback=self._set_default)
                dpg.bind_item_theme(b_def, btn_success)
                
                b_del = dpg.add_button(label="删除选中模型", callback=self._delete_selected)
                dpg.bind_item_theme(b_del, btn_danger)
                
                dpg.add_button(label="测试模型连接", callback=self._test_connection)
                dpg.add_button(label="刷新列表", callback=self._refresh_list)

            # 右侧：添加 / 编辑模型 & 数据管理
            with dpg.child_window(width=680, height=560, border=True):
                dpg.add_text("⚙️ 添加 / 编辑大模型配置", color=COLOR_PRIMARY)
                dpg.add_spacer(height=4)
                
                # 快捷模板按钮
                with dpg.group(horizontal=True):
                    dpg.add_text("快捷填入预设模板:")
                    dpg.add_button(label="DeepSeek", callback=self._fill_deepseek)
                    dpg.add_button(label="OpenAI", callback=self._fill_openai)
                    dpg.add_button(label="Ollama 本地", callback=self._fill_ollama)

                dpg.add_separator()
                dpg.add_spacer(height=4)

                dpg.add_text("模型配置名称:")
                dpg.add_input_text(tag='cfg_model_name', hint="例如：deepseek-chat 或 my-ollama", width=450)

                dpg.add_text("协议类型:")
                dpg.add_radio_button(
                    tag='cfg_model_type',
                    items=['openai (标准大模型协议)', 'rule (内置本地规则)', 'http (自定义Webhook)'],
                    default_value='openai (标准大模型协议)',
                    horizontal=True
                )

                dpg.add_text("API 端点 URL (Endpoint):")
                dpg.add_input_text(
                    tag='cfg_model_endpoint',
                    default_value='https://api.deepseek.com/v1/chat/completions',
                    width=550
                )

                dpg.add_text("模型名称 (Model Identifier):")
                dpg.add_input_text(tag='cfg_model_model', default_value='deepseek-chat', width=350)

                dpg.add_text("API 密钥 (API Key):")
                dpg.add_input_text(tag='cfg_model_key', hint="Bearer Token 或 sk-...", password=True, width=450)

                dpg.add_spacer(height=8)
                with dpg.group(horizontal=True):
                    b_save = dpg.add_button(label="保存模型配置", callback=self._save_model)
                    dpg.bind_item_theme(b_save, btn_primary)
                    dpg.add_button(label="清空表单", callback=self._clear_form)

                dpg.add_spacer(height=16)
                dpg.add_separator()
                dpg.add_spacer(height=6)

                # 本地数据与备份管理
                dpg.add_text("💾 存储与备份管理", color=COLOR_PRIMARY)
                dpg.add_text(f"备份文件存放目录: {get_backup_dir()}", color=COLOR_MUTED)
                dpg.add_spacer(height=4)
                dpg.add_button(label="📂 在文件资源管理器中打开备份目录", callback=lambda s, d: open_in_explorer(str(get_backup_dir())))

                dpg.add_spacer(height=8)
                self.status_message_id = dpg.add_text("", color=COLOR_SUCCESS)

    def _format_model_item(self, m: Dict[str, Any]) -> str:
        name = m.get('name', 'unnamed')
        mtype = m.get('type', 'rule')
        is_default = (name == self.analyzer.client.default_model)
        star = " ★ [默认]" if is_default else ""
        return f"{name} ({mtype}){star}"

    def _extract_name_from_display(self, disp_str: str) -> str:
        if not disp_str:
            return ""
        return disp_str.split(' ')[0]

    def _on_select_model(self, sender, data):
        name = self._extract_name_from_display(data)
        mdef = next((m for m in self.analyzer.models() if m.get('name') == name), None)
        if not mdef:
            return

        dpg.set_value('cfg_model_name', mdef.get('name', ''))
        
        mtype = mdef.get('type', 'openai')
        if mtype == 'rule':
            dpg.set_value('cfg_model_type', 'rule (内置本地规则)')
        elif mtype == 'http':
            dpg.set_value('cfg_model_type', 'http (自定义Webhook)')
        else:
            dpg.set_value('cfg_model_type', 'openai (标准大模型协议)')
            
        dpg.set_value('cfg_model_endpoint', mdef.get('endpoint', ''))
        dpg.set_value('cfg_model_model', mdef.get('model', ''))
        dpg.set_value('cfg_model_key', mdef.get('api_key', ''))

    def _fill_deepseek(self, sender, data):
        dpg.set_value('cfg_model_name', 'deepseek-chat')
        dpg.set_value('cfg_model_type', 'openai (标准大模型协议)')
        dpg.set_value('cfg_model_endpoint', 'https://api.deepseek.com/v1/chat/completions')
        dpg.set_value('cfg_model_model', 'deepseek-chat')
        dpg.set_value(self.status_message_id, "已载入 DeepSeek 模板，请填写您的 API Key 后保存")

    def _fill_openai(self, sender, data):
        dpg.set_value('cfg_model_name', 'gpt-4o-mini')
        dpg.set_value('cfg_model_type', 'openai (标准大模型协议)')
        dpg.set_value('cfg_model_endpoint', 'https://api.openai.com/v1/chat/completions')
        dpg.set_value('cfg_model_model', 'gpt-4o-mini')
        dpg.set_value(self.status_message_id, "已载入 OpenAI 模板，请填写您的 API Key 后保存")

    def _fill_ollama(self, sender, data):
        dpg.set_value('cfg_model_name', 'ollama-qwen')
        dpg.set_value('cfg_model_type', 'openai (标准大模型协议)')
        dpg.set_value('cfg_model_endpoint', 'http://localhost:11434/v1/chat/completions')
        dpg.set_value('cfg_model_model', 'qwen2.5')
        dpg.set_value('cfg_model_key', 'ollama')
        dpg.set_value(self.status_message_id, "已载入 Ollama 本地模型模板（免API Key）")

    def _clear_form(self, sender=None, data=None):
        dpg.set_value('cfg_model_name', '')
        dpg.set_value('cfg_model_endpoint', '')
        dpg.set_value('cfg_model_model', '')
        dpg.set_value('cfg_model_key', '')

    def _set_default(self, sender, data):
        raw = dpg.get_value(self.model_list_id)
        name = self._extract_name_from_display(raw)
        if name:
            self.analyzer.set_default(name)
            dpg.set_value(self.status_message_id, f"已将 [{name}] 设为默认分析模型！")
            self._refresh_list()

    def _delete_selected(self, sender, data):
        raw = dpg.get_value(self.model_list_id)
        name = self._extract_name_from_display(raw)
        if name == 'local-rules':
            dpg.set_value(self.status_message_id, "基础内置规则不允许删除！")
            return
        if name:
            self.analyzer.remove_model(name)
            dpg.set_value(self.status_message_id, f"已删除模型配置: {name}")
            self._refresh_list()
            self._clear_form()

    def _test_connection(self, sender, data):
        raw = dpg.get_value(self.model_list_id)
        name = self._extract_name_from_display(raw)
        if not name:
            dpg.set_value(self.status_message_id, "请先在列表中选中一个模型！")
            return
            
        dpg.set_value(self.status_message_id, f"正在测试 [{name}] 连通性...")
        ok, msg = self.analyzer.test_connection(name)
        if ok:
            dpg.set_value(self.status_message_id, f"✅ 连接成功: {msg}")
        else:
            dpg.set_value(self.status_message_id, f"❌ 测试失败: {msg}")

    def _refresh_list(self, sender=None, data=None):
        items = [self._format_model_item(m) for m in self.analyzer.models()]
        dpg.configure_item(self.model_list_id, items=items)

    def _save_model(self, sender, data):
        name = dpg.get_value('cfg_model_name').strip()
        type_str = dpg.get_value('cfg_model_type')
        endpoint = dpg.get_value('cfg_model_endpoint').strip()
        model = dpg.get_value('cfg_model_model').strip()
        key = dpg.get_value('cfg_model_key').strip()

        if not name:
            dpg.set_value(self.status_message_id, "错误：模型配置名称不能为空！")
            return

        mtype = 'openai'
        if 'rule' in type_str:
            mtype = 'rule'
        elif 'http' in type_str:
            mtype = 'http'

        mdef = {'name': name, 'type': mtype}
        if mtype in ('openai', 'http'):
            mdef['endpoint'] = endpoint
            if model:
                mdef['model'] = model
            if key:
                mdef['api_key'] = key

        self.analyzer.add_model(mdef)
        self._refresh_list()
        dpg.set_value(self.status_message_id, f"已成功保存模型 [{name}]！")
