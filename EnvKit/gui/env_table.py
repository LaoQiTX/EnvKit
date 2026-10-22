import os
import re
import dearpygui.dearpygui as dpg
from typing import Dict, List, Any, Optional
from core.env_manager import EnvManager
from core.analyzer import Analyzer
from core.backup import backup, restore
from utils.path_helper import get_backup_dir
from utils.win_utils import choose_file, open_in_explorer
from utils.path_check import normalize_path
from gui.theme import (
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_MUTED,
    COLOR_PRIMARY, create_button_theme
)

CRITICAL_ENV_VARS = {
    'PATH', 'PATHEXT', 'SystemRoot', 'windir', 'ProgramFiles', 'ProgramFiles(x86)',
    'ProgramData', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP',
    'COMSPEC', 'JAVA_HOME', 'PYTHONPATH', 'GOROOT', 'NODE_HOME'
}

class EnvUI:
    def __init__(self, analyzer: Analyzer, on_send_to_diagnose=None):
        self.scope = 'user'
        self.manager = EnvManager(self.scope)
        self.analyzer = analyzer
        self.on_send_to_diagnose = on_send_to_diagnose
        self.table_id = None
        self.count_text_id = None
        self.status_message_id = None
        self.pending_delete_name = None
        self.search_filter = ""
        self.vars_cache = {}

    def get_current_scope(self) -> str:
        return self.scope

    def refresh_vars(self):
        self.vars_cache = self.manager.list()
        self._render_rows()
        if self.count_text_id and dpg.does_item_exist(self.count_text_id):
            dpg.set_value(self.count_text_id, f"当前共 {len(self.vars_cache)} 个变量")

    def _render_rows(self):
        if not self.table_id or not dpg.does_item_exist(self.table_id):
            return
            
        children = dpg.get_item_children(self.table_id, 1) or []
        for c in children:
            dpg.delete_item(c)

        flt = self.search_filter.lower().strip()

        for k, v in sorted(self.vars_cache.items(), key=lambda x: x[0].upper()):
            if flt and (flt not in k.lower() and flt not in v.lower()):
                continue

            row_id = dpg.add_table_row(parent=self.table_id)
            
            # 变量名（可点击）
            sel_id = dpg.add_selectable(label=k, parent=row_id)
            handler = dpg.add_item_handler_registry()
            dpg.add_item_clicked_handler(
                parent=handler,
                callback=self._on_row_click,
                user_data={'key': k, 'value': v}
            )
            dpg.bind_item_handler_registry(sel_id, handler)

            # 属性标记
            badge = "常规"
            badge_color = COLOR_MUTED
            if k in CRITICAL_ENV_VARS:
                badge = "系统关键"
                badge_color = COLOR_WARNING
            elif ';' in v:
                badge = f"路径集合 ({len(v.split(';'))}项)"
                badge_color = COLOR_PRIMARY
            elif '\\' in v or '/' in v:
                badge = "单路径"
                badge_color = COLOR_SUCCESS if os.path.exists(normalize_path(v)) else COLOR_DANGER
            elif not v:
                badge = "空值"
                badge_color = COLOR_DANGER

            dpg.add_text(badge, parent=row_id, color=badge_color)

            # 变量值（过长时截断显示）
            disp_val = v if len(v) <= 120 else v[:117] + "..."
            dpg.add_text(disp_val, parent=row_id)

    def _on_row_click(self, sender, app_data, user_data):
        k = user_data['key']
        v = user_data['value']
        dpg.set_value('env_input_key', k)
        dpg.set_value('env_input_val', v)

    def build(self):
        btn_primary = create_button_theme((37, 99, 235), (59, 130, 246), (29, 78, 216))
        btn_danger = create_button_theme((220, 38, 38), (239, 68, 68), (185, 28, 28))
        btn_success = create_button_theme((16, 185, 129), (52, 211, 153), (5, 150, 105))

        # 删除确认弹窗
        with dpg.window(modal=True, show=False, tag='modal_delete_env_confirm', no_move=True, no_resize=True, width=420, height=200):
            dpg.add_text("⚠️ 确认删除环境变量？", color=COLOR_WARNING)
            dpg.add_separator()
            dpg.add_text(tag='modal_delete_env_text', wrap=390)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                b_del_yes = dpg.add_button(label="确认永久删除", callback=self._do_delete_confirmed)
                dpg.bind_item_theme(b_del_yes, btn_danger)
                dpg.add_button(label="取消", callback=lambda s, d: dpg.configure_item('modal_delete_env_confirm', show=False))

        # 顶部工具栏
        with dpg.group(horizontal=True):
            dpg.add_text("作用域:")
            dpg.add_radio_button(
                items=['用户变量 (User)', '系统变量 (System)'],
                default_value='用户变量 (User)',
                horizontal=True,
                tag='env_scope_radio',
                callback=self._on_scope_change
            )
            dpg.add_spacer(width=15)
            self.count_text_id = dpg.add_text("共 0 个变量", color=COLOR_MUTED)
            dpg.add_spacer(width=15)
            dpg.add_text("搜索:")
            dpg.add_input_text(hint="筛选变量名或变量值...", callback=self._on_search_change, width=180)
            dpg.add_button(label="刷新列表", callback=lambda s, d: self.refresh_vars())
            
            b_bak = dpg.add_button(label="一键备份全部变量", callback=self._backup_all)
            dpg.bind_item_theme(b_bak, btn_success)
            
            dpg.add_button(label="从备份文件恢复...", callback=self._restore_from_backup)

        dpg.add_spacer(height=6)

        # 变量列表容器
        with dpg.child_window(height=390, border=True):
            self.table_id = dpg.add_table(
                header_row=True,
                resizable=True,
                policy=dpg.mvTable_SizingStretchProp,
                row_background=True,
                borders_innerH=True,
                borders_outerH=True,
                borders_innerV=True,
                borders_outerV=True
            )
            dpg.add_table_column(label="变量名 (双击快速编辑)", width_stretch=True, init_width_or_weight=220, parent=self.table_id)
            dpg.add_table_column(label="属性状态", width_fixed=True, init_width_or_weight=130, parent=self.table_id)
            dpg.add_table_column(label="变量值", width_stretch=True, init_width_or_weight=550, parent=self.table_id)

        dpg.add_spacer(height=6)

        # 底部编辑与操作卡片
        with dpg.child_window(height=170, border=True):
            dpg.add_text("📝 变量详情与操作（支持新建、修改或删除）：", color=COLOR_PRIMARY)
            with dpg.group(horizontal=True):
                dpg.add_text("变量名:")
                dpg.add_input_text(tag="env_input_key", width=250)
                dpg.add_text("变量值:")
                dpg.add_input_text(tag="env_input_val", width=550)

            dpg.add_spacer(height=4)
            with dpg.group(horizontal=True):
                b_save = dpg.add_button(label="保存 / 更新变量", callback=self._save_var)
                dpg.bind_item_theme(b_save, btn_primary)

                b_del = dpg.add_button(label="删除当前变量", callback=self._request_delete)
                dpg.bind_item_theme(b_del, btn_danger)

                dpg.add_button(label="清空输入框", callback=self._clear_inputs)
                
                if self.on_send_to_diagnose:
                    dpg.add_button(label="发送到 AI 进行深入分析", callback=self._send_selected_to_diagnose)

            self.status_message_id = dpg.add_text("", color=COLOR_SUCCESS)

        self.refresh_vars()

    def _on_scope_change(self, sender, data):
        self.scope = 'user' if 'User' in data else 'system'
        self.manager = EnvManager(self.scope)
        self.refresh_vars()

    def _on_search_change(self, sender, data):
        self.search_filter = data
        self._render_rows()

    def _clear_inputs(self, sender=None, data=None):
        dpg.set_value("env_input_key", "")
        dpg.set_value("env_input_val", "")

    def _save_var(self, sender, data):
        k = dpg.get_value("env_input_key").strip()
        v = dpg.get_value("env_input_val")
        if not k:
            dpg.set_value(self.status_message_id, "错误：变量名不能为空！")
            return
            
        try:
            self.manager.set(k, v)
            dpg.set_value(self.status_message_id, f"成功更新环境变量 [{k}]，已通知系统全局生效！")
            self.refresh_vars()
        except PermissionError as e:
            dpg.set_value(self.status_message_id, f"权限不足：修改系统变量需以管理员身份运行！")
        except Exception as e:
            dpg.set_value(self.status_message_id, f"保存失败: {e}")

    def _request_delete(self, sender, data):
        k = dpg.get_value("env_input_key").strip()
        if not k:
            dpg.set_value(self.status_message_id, "请先选择或输入要删除的变量名！")
            return

        self.pending_delete_name = k
        v = self.manager.get(k) or ''
        warning_reasons = []
        
        if k in CRITICAL_ENV_VARS:
            warning_reasons.append("属于系统核心运行变量")
        if v and os.path.exists(normalize_path(v)):
            warning_reasons.append("指向存在且有效的系统路径")
        if re.search(r'%[^%]+%', v):
            warning_reasons.append("包含嵌套环境变量引用")

        text = f"您确定要永久删除 [{self.scope}] 作用域下的环境变量 [{k}] 吗？"
        if warning_reasons:
            text += f"\n\n⚠️ 风险提示：该变量 { '，'.join(warning_reasons) }，删除可能导致相关软件无法启动！"
            
        dpg.set_value('modal_delete_env_text', text)
        dpg.configure_item('modal_delete_env_confirm', show=True)

    def _do_delete_confirmed(self, sender, data):
        k = self.pending_delete_name
        dpg.configure_item('modal_delete_env_confirm', show=False)
        if not k:
            return
            
        try:
            self.manager.delete(k)
            self._clear_inputs()
            dpg.set_value(self.status_message_id, f"已成功删除环境变量 [{k}]！")
            self.refresh_vars()
        except PermissionError:
            dpg.set_value(self.status_message_id, "权限不足：删除系统变量需以管理员身份运行！")
        except Exception as e:
            dpg.set_value(self.status_message_id, f"删除失败: {e}")
        finally:
            self.pending_delete_name = None

    def _backup_all(self, sender, data):
        env_data = self.manager.list()
        backup_path = backup(env_data, {}, category='env', meta={'scope': self.scope})
        dpg.set_value(self.status_message_id, f"环境变量已成功备份至: {backup_path}")

    def _restore_from_backup(self, sender, data):
        initial_dir = str(get_backup_dir())
        chosen = choose_file(
            initial_dir=initial_dir,
            file_types=[("EnvKit 备份文件 (*.json)", "*.json"), ("所有文件", "*.*")],
            title="选择要恢复的环境变量备份文件"
        )
        if not chosen:
            return
            
        try:
            data = restore(chosen)
            env_map = data.get('env', {})
            if not env_map:
                dpg.set_value(self.status_message_id, "备份文件中未找到有效的环境变量数据！")
                return
                
            restored_count = 0
            for k, v in env_map.items():
                self.manager.set(k, v)
                restored_count += 1
                
            self.refresh_vars()
            dpg.set_value(self.status_message_id, f"成功从备份恢复了 {restored_count} 个环境变量！")
        except Exception as e:
            dpg.set_value(self.status_message_id, f"恢复失败: {e}")

    def _send_selected_to_diagnose(self, sender, data):
        k = dpg.get_value("env_input_key").strip()
        v = dpg.get_value("env_input_val")
        if not k:
            dpg.set_value(self.status_message_id, "请先选择一个变量进行分析！")
            return
        if self.on_send_to_diagnose:
            self.on_send_to_diagnose([{'kind': 'env', 'scope': self.scope, 'key': k, 'value': v}])
