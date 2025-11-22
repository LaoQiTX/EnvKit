import dearpygui.dearpygui as dpg
from core.env_manager import EnvManager
from utils.path_check import analyze_paths
from core.analyzer import Analyzer
from utils.path_check import normalize_path
from core.backup import backup, restore
from pathlib import Path
import os
import re
import json
import sys

class EnvUI:
    def __init__(self, analyzer: Analyzer):
        self.scope = 'user'
        self.manager = EnvManager(self.scope)
        self.analyzer = analyzer
        self.env_table_id = None
        self.path_table_id = None
        self.path_rows = []
        self.env_rows = []
        self.pending_env_name = None
        self.pending_path_idx = None
        self.backup_env_message_id = None
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys.argv[0]).resolve().parent
        else:
            self.base_dir = Path(__file__).resolve().parents[1]

    def refresh_vars(self):
        if self.env_table_id:
            children = dpg.get_item_children(self.env_table_id, 1) or []
            for c in children:
                dpg.delete_item(c)
        self.env_rows = []
        data = self.manager.list()
        for k, v in sorted(data.items()):
            row_id = dpg.add_table_row(parent=self.env_table_id)
            selectable_id = dpg.add_selectable(label=k, parent=row_id)
            dpg.add_text(v, parent=row_id)
            handler = dpg.add_item_handler_registry()
            dpg.add_item_clicked_handler(parent=handler, callback=self._on_env_row_click, user_data={'key': k, 'value': v})
            dpg.bind_item_handler_registry(selectable_id, handler)
            self.env_rows.append({'row_id': row_id, 'key': k, 'value': v, 'selectable_id': selectable_id})

    def refresh_path(self):
        if self.path_table_id:
            children = dpg.get_item_children(self.path_table_id, 1) or []
            for c in children:
                dpg.delete_item(c)
        self.path_rows = []
        entries = self.manager.list_path('PATH')
        for e in entries:
            row_id = dpg.add_table_row(parent=self.path_table_id)
            selectable_id = dpg.add_selectable(label=str(e['index']), parent=row_id)
            color = (255, 255, 255, 255)
            if not e['exists'] and e['duplicate']:
                color = (199, 21, 133, 255)
            elif not e['exists']:
                color = (220, 50, 47, 255)
            elif e['duplicate']:
                color = (255, 165, 0, 255)
            dpg.add_text(e['raw'], parent=row_id, color=color)
            dpg.add_text('是' if e['exists'] else '否', parent=row_id, color=(0, 200, 0, 255) if e['exists'] else (220, 50, 47, 255))
            dpg.add_text('是' if e['duplicate'] else '否', parent=row_id, color=(255, 165, 0, 255) if e['duplicate'] else (0, 200, 0, 255))
            tag = f'path_enable_{e["index"]}'
            dpg.add_checkbox(tag=tag, default_value=True, parent=row_id)
            handler = dpg.add_item_handler_registry()
            dpg.add_item_clicked_handler(parent=handler, callback=self._on_path_row_click, user_data={'index': e['index'], 'raw': e['raw'], 'tag': tag})
            dpg.bind_item_handler_registry(selectable_id, handler)
            self.path_rows.append({'index': e['index'], 'raw': e['raw'], 'tag': tag, 'row_id': row_id, 'selectable_id': selectable_id})

    def build(self):
        with dpg.window(modal=True, show=False, tag='confirm_delete_env', no_move=True, no_resize=True):
            dpg.add_text(tag='confirm_delete_env_text')
            with dpg.group(horizontal=True):
                dpg.add_button(label='确定删除', callback=self._confirm_delete_env_yes)
                dpg.add_button(label='取消', callback=lambda s,d: dpg.configure_item('confirm_delete_env', show=False))
        with dpg.window(modal=True, show=False, tag='confirm_delete_path', no_move=True, no_resize=True):
            dpg.add_text(tag='confirm_delete_path_text')
            with dpg.group(horizontal=True):
                dpg.add_button(label='确定删除', callback=self._confirm_delete_path_yes)
                dpg.add_button(label='取消', callback=lambda s,d: dpg.configure_item('confirm_delete_path', show=False))
        # 文件对话框延迟创建，避免打包环境初始化时可能的窗口库问题
        dpg.add_button(label='选择备份文件恢复环境变量', callback=self._open_env_restore_dialog)
        with dpg.group():
            dpg.add_text('作用域')
            dpg.add_radio_button(items=['user', 'system'], default_value='user', tag='scope_radio', callback=self._on_scope)
            dpg.add_button(label='刷新变量', callback=lambda s,d:self.refresh_vars())
            self.env_table_id = dpg.add_table(header_row=True)
            dpg.add_table_column(label='变量', parent=self.env_table_id)
            dpg.add_table_column(label='值', parent=self.env_table_id)
            dpg.add_button(label='新增变量', callback=self._add_var)
            dpg.add_button(label='删除变量', callback=self._del_var)
            dpg.add_input_text(label='变量名', tag='env_key')
            dpg.add_input_text(label='变量值', tag='env_val')
            dpg.add_button(label='分析选中变量', callback=self._analyze_selected)
            dpg.add_input_text(label='多选变量名,逗号分隔', tag='select_keys')
            with dpg.collapsing_header(label='PATH检测', default_open=True):
                dpg.add_button(label='刷新PATH', callback=lambda s,d:self.refresh_path())
                path_container = dpg.add_child_window(height=280, border=True)
                self.path_table_id = dpg.add_table(header_row=True, parent=path_container)
                dpg.add_table_column(label='索引', parent=self.path_table_id)
                dpg.add_table_column(label='路径', parent=self.path_table_id)
                dpg.add_table_column(label='存在', parent=self.path_table_id)
                dpg.add_table_column(label='重复', parent=self.path_table_id)
                dpg.add_table_column(label='启用', parent=self.path_table_id)
            dpg.add_input_text(label='新增路径', tag='path_new')
            dpg.add_button(label='添加到PATH', callback=self._add_path)
            dpg.add_input_int(label='删除索引', default_value=0, tag='path_index')
            dpg.add_button(label='删除PATH项', callback=self._del_path)
            dpg.add_button(label='应用启用/禁用', callback=self._apply_enable_disable)
            dpg.add_button(label='备份全部环境变量', callback=self._backup_env)
            self.backup_env_message_id = dpg.add_text('')
        self.refresh_vars()
        self.refresh_path()

    def _on_scope(self, sender, data):
        self.scope = dpg.get_value('scope_radio')
        self.manager = EnvManager(self.scope)
        self.refresh_vars()
        self.refresh_path()

    def _add_var(self, sender, data):
        k = dpg.get_value('env_key')
        v = dpg.get_value('env_val')
        if k:
            self.manager.set(k, v)
            self.refresh_vars()
        dpg.set_value('env_key', '')
        dpg.set_value('env_val', '')

    def _del_var(self, sender, data):
        k = dpg.get_value('env_key')
        if k:
            self.pending_env_name = k
            v = self.manager.get(k) or ''
            text = self._build_env_delete_warning(k, v) or '确认删除该变量?'
            dpg.set_value('confirm_delete_env_text', text)
            dpg.configure_item('confirm_delete_env', show=True)
        dpg.set_value('env_key', '')
        dpg.set_value('env_val', '')

    def _add_path(self, sender, data):
        newp = dpg.get_value('path_new')
        cur = self.manager.get('PATH') or ''
        parts = cur.split(';') if cur else []
        parts.append(newp)
        self.manager.update_path_entries(parts)
        self.refresh_path()
        dpg.set_value('path_new', '')

    def _del_path(self, sender, data):
        idx = dpg.get_value('path_index')
        cur = self.manager.get('PATH') or ''
        parts = cur.split(';') if cur else []
        if 0 <= idx < len(parts):
            self.pending_path_idx = idx
            raw = parts[idx]
            exists = False
            try:
                exists = os.path.exists(normalize_path(raw))
            except Exception:
                exists = False
            text = self._build_path_delete_warning(idx, raw, exists, parts) or '确认删除该PATH项?'
            dpg.set_value('confirm_delete_path_text', text)
            dpg.configure_item('confirm_delete_path', show=True)
        dpg.set_value('path_index', 0)

    def _analyze_selected(self, sender, data):
        keys = dpg.get_value('select_keys')
        items = []
        if keys:
            for k in [x.strip() for x in keys.split(',') if x.strip()]:
                v = self.manager.get(k)
                items.append({'kind': 'env', 'key': k, 'value': v})
        res = self.analyzer.analyze(items)
        dpg.set_value('analysis_output_env', json.dumps(res, ensure_ascii=False))
        dpg.set_value('select_keys', '')

    def _confirm_delete_env_yes(self, sender, data):
        if self.pending_env_name:
            try:
                self.manager.delete(self.pending_env_name)
                self.refresh_vars()
            finally:
                dpg.set_value('env_key', '')
                dpg.set_value('env_val', '')
                dpg.configure_item('confirm_delete_env', show=False)
                self.pending_env_name = None

    def _confirm_delete_path_yes(self, sender, data):
        if self.pending_path_idx is not None:
            cur = self.manager.get('PATH') or ''
            parts = cur.split(';') if cur else []
            if 0 <= self.pending_path_idx < len(parts):
                parts.pop(self.pending_path_idx)
                self.manager.update_path_entries(parts)
                self.refresh_path()
            dpg.set_value('path_index', 0)
            dpg.configure_item('confirm_delete_path', show=False)
            self.pending_path_idx = None

    def _build_env_delete_warning(self, name: str, value: str):
        reasons = []
        critical = {'PATH','PATHEXT','SystemRoot','ProgramFiles','ProgramFiles(x86)','USERPROFILE','TEMP','TMP','COMSPEC','JAVA_HOME','PYTHONPATH','GOROOT','NODE_HOME'}
        if name in critical:
            reasons.append('关键变量')
        if value:
            if ';' in value:
                parts = [p for p in value.split(';') if p]
                for p in parts:
                    try:
                        if os.path.exists(normalize_path(p)):
                            reasons.append('包含有效路径')
                            break
                    except Exception:
                        pass
            elif ('\\' in value or '/' in value):
                try:
                    if os.path.exists(normalize_path(value)):
                        reasons.append('指向存在路径')
                except Exception:
                    pass
            if re.search(r'%[^%]+%', value):
                reasons.append('包含变量引用')
        if reasons:
            return '该变量可能重要：' + '，'.join(reasons) + '。是否继续?'
        return None

    def _build_path_delete_warning(self, idx: int, raw: str, exists: bool, parts: list):
        reasons = []
        if exists:
            reasons.append('路径存在')
        sys_dirs = ['C:\\Windows','C:\\Windows\\System32']
        try:
            rp = normalize_path(raw)
            for sd in sys_dirs:
                if rp.lower().startswith(sd.lower()):
                    reasons.append('系统目录')
                    break
        except Exception:
            pass
        if parts.count(raw) > 1:
            reasons.append('重复条目')
        if idx <= 5:
            reasons.append('靠前优先级高')
        if reasons and exists:
            return '该PATH项谨慎删除：' + '，'.join(reasons) + '。是否继续?'
        if exists:
            return '该路径存在，谨慎删除。是否继续?'
        return None

    def _on_env_row_click(self, sender, app_data, user_data):
        if dpg.is_mouse_button_double_clicked(dpg.mvMouseButton_Left):
            k = user_data['key']
            v = user_data['value']
            dpg.set_value('env_key', k)
            dpg.set_value('env_val', v)
            cur = dpg.get_value('select_keys') or ''
            keys = [x.strip() for x in cur.split(',') if x.strip()]
            if k not in keys:
                keys.append(k)
            dpg.set_value('select_keys', ','.join(keys))

    def _on_path_row_click(self, sender, app_data, user_data):
        if dpg.is_mouse_button_double_clicked(dpg.mvMouseButton_Left):
            idx = user_data['index']
            tag = user_data['tag']
            cur = dpg.get_value(tag)
            dpg.set_value(tag, not cur)
            dpg.set_value('path_index', idx)

    def _apply_enable_disable(self, sender, data):
        cur = self.manager.get('PATH') or ''
        parts = cur.split(';') if cur else []
        enabled = []
        for row in self.path_rows:
            if dpg.get_value(row['tag']):
                enabled.append(row['raw'])
        self.manager.update_path_entries(enabled)
        self.refresh_path()

    def _backup_env(self, sender, data):
        env_data = self.manager.list()
        out_dir = str(self.base_dir / '.backup')
        path = backup(env_data, {}, out_dir, category='env')
        dpg.set_value(self.backup_env_message_id, f'已备份: {path}')

    def _env_restore_selected(self, sender, app_data):
        fp = app_data.get('file_path_name') if isinstance(app_data, dict) else None
        if not fp:
            return
        j = restore(fp)
        env_data = j.get('env', {})
        for k, v in env_data.items():
            self.manager.set(k, v)
        self.refresh_vars()

    def _open_env_restore_dialog(self, sender, data):
        if not dpg.does_item_exist('env_restore_dialog'):
            with dpg.file_dialog(directory_selector=False, show=False, tag='env_restore_dialog', callback=self._env_restore_selected):
                dpg.add_file_extension(".json")
        dpg.configure_item('env_restore_dialog', show=True)
