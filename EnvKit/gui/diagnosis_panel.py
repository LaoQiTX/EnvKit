import json
import dearpygui.dearpygui as dpg
from typing import List, Dict, Any, Optional
from core.analyzer import Analyzer
from core.env_manager import EnvManager
from gui.theme import (
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_MUTED,
    COLOR_PRIMARY, create_button_theme
)

class DiagnosisUI:
    def __init__(self, analyzer: Analyzer):
        self.analyzer = analyzer
        self.output_text_id = None
        self.stats_id = None
        self.pending_items = []
        self.current_model = None

    def set_items_to_diagnose(self, items: List[Dict[str, Any]]):
        """由其他 Tab（环境变量或注册表）传递选中的项并自动触发分析"""
        self.pending_items = items
        self.run_diagnosis()

    def build(self):
        btn_primary = create_button_theme((37, 99, 235), (59, 130, 246), (29, 78, 216))
        btn_success = create_button_theme((16, 185, 129), (52, 211, 153), (5, 150, 105))

        with dpg.group(horizontal=True):
            dpg.add_text("[模型] 选择分析模型:")
            models = self.analyzer.models()
            model_names = [m['name'] for m in models]
            def_model = self.analyzer.client.default_model or (model_names[0] if model_names else 'local-rules')
            self.current_model = def_model
            
            dpg.add_combo(
                items=model_names,
                default_value=def_model,
                width=180,
                tag='diag_model_combo',
                callback=self._on_model_select
            )

            dpg.add_spacer(width=10)
            b_full = dpg.add_button(label="[体检] 一键全系统体检", callback=self._scan_full_system)
            dpg.bind_item_theme(b_full, btn_primary)

            b_path = dpg.add_button(label="[PATH] PATH 专项诊断", callback=self._scan_path_only)
            dpg.bind_item_theme(b_path, btn_success)

            dpg.add_button(label="[复制] 复制分析报告", callback=self._copy_report)

        dpg.add_spacer(height=6)

        # 状态概括
        with dpg.group(horizontal=True):
            dpg.add_text("体检概况：", color=COLOR_PRIMARY)
            self.stats_id = dpg.add_text("点击上方按钮开始体检或从其他标签页双击变量发送分析", color=COLOR_MUTED)

        dpg.add_spacer(height=6)

        # 诊断与大模型建议报告展示窗口 (自适应高度，无外层多余滚动条)
        with dpg.child_window(height=-10, border=True, no_scrollbar=True):
            self.output_text_id = dpg.add_input_text(
                multiline=True,
                readonly=True,
                width=-1,
                height=-1,
                default_value=(
                    "欢迎使用 EnvKit 智能诊断中心！\n\n"
                    "功能说明：\n"
                    "1.【一键全系统体检】：全面扫描当前用户的环境变量、系统核心环境变量及 PATH 路径，"
                    "排查空路径、失效不存在路径、重复路径、以及未定义变量引用等隐患。\n"
                    "2.【PATH 专项诊断】：专门针对 Windows PATH 长度超限、失效条目及冗余项进行专项检查。\n"
                    "3.【大模型深度解读】：支持配置 DeepSeek、OpenAI、Ollama 等模型，为您提供详细的变量功能释义、"
                    "关联软件分析和安全清理建议。\n\n"
                    "提示：您也可以在【环境变量】或【注册表】标签页选中任意变量，点击“发送到 AI 深入分析”直接导入此处。"
                )
            )

    def _on_model_select(self, sender, data):
        self.current_model = data

    def run_diagnosis(self, items: Optional[List[Dict[str, Any]]] = None):
        items_to_run = items if items is not None else self.pending_items
        if not items_to_run:
            dpg.set_value(self.stats_id, "未指定要分析的变量或注册表项！")
            return

        model_name = dpg.get_value('diag_model_combo') or self.current_model
        dpg.set_value(self.stats_id, f"正在通过 [{model_name}] 进行深度诊断，请稍候...")

        res = self.analyzer.analyze(items_to_run, model_name=model_name)
        self._display_result(res, len(items_to_run))

    def _scan_full_system(self, sender, data):
        user_mgr = EnvManager('user')
        sys_mgr = EnvManager('system')
        user_vars = user_mgr.list()
        sys_vars = sys_mgr.list()

        items = []
        for k, v in user_vars.items():
            items.append({'kind': 'env', 'scope': 'user', 'key': f'用户变量: {k}', 'value': v})
        for k, v in sys_vars.items():
            items.append({'kind': 'env', 'scope': 'system', 'key': f'系统变量: {k}', 'value': v})

        self.run_diagnosis(items)

    def _scan_path_only(self, sender, data):
        user_mgr = EnvManager('user')
        sys_mgr = EnvManager('system')
        u_path = user_mgr.get('PATH') or ''
        s_path = sys_mgr.get('PATH') or ''

        items = [
            {'kind': 'env', 'scope': 'user', 'key': '用户 PATH', 'value': u_path},
            {'kind': 'env', 'scope': 'system', 'key': '系统 PATH', 'value': s_path}
        ]
        self.run_diagnosis(items)

    def _display_result(self, res: dict, total_items: int):
        summary_text = res.get('summary', '')
        suggestions = res.get('suggestions', [])
        err = res.get('error')

        issue_count = 0
        for s in suggestions:
            issue_count += len(s.get('items', []))

        stat_msg = f"共扫描 {total_items} 项  |  发现潜在异常: {issue_count} 处  |  分析引擎: {res.get('model', 'Engine')}"
        if err:
            stat_msg += f" (提示: {err})"
            
        dpg.set_value(self.stats_id, stat_msg)
        dpg.set_value(self.output_text_id, summary_text)

    def _copy_report(self, sender, data):
        txt = dpg.get_value(self.output_text_id)
        if txt:
            dpg.set_clipboard_text(txt)
            dpg.set_value(self.stats_id, "报告已复制到剪贴板！")
