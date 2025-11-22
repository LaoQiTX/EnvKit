import dearpygui.dearpygui as dpg
from core.reg_manager import RegManager
from core.analyzer import Analyzer
import json
from core.backup import backup, restore
from pathlib import Path
import os
from utils.path_check import normalize_path
import re
import sys

class RegUI:
    def __init__(self, analyzer: Analyzer):
        self.root = 'HKCU'
        self.m = RegManager(self.root)
        self.analyzer = analyzer
        self.table_id = None
        self.message_id = None
        self.pending_reg_name = None
        self.backup_reg_message_id = None
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys.argv[0]).resolve().parent
        else:
            self.base_dir = Path(__file__).resolve().parents[1]

    def build(self):
        with dpg.window(modal=True, show=False, tag='confirm_delete_reg', no_move=True, no_resize=True):
            dpg.add_text(tag='confirm_delete_reg_text')
            with dpg.group(horizontal=True):
                dpg.add_button(label='确定删除', callback=self._confirm_delete_reg_yes)
                dpg.add_button(label='取消', callback=lambda s,d: dpg.configure_item('confirm_delete_reg', show=False))
        # 文件对话框延迟创建，避免打包环境初始化时可能的窗口库问题
        dpg.add_button(label='选择备份文件恢复子键', callback=self._open_reg_restore_dialog)
        with dpg.group():
            dpg.add_radio_button(tag='reg_root', items=['HKCU', 'HKLM'], default_value='HKCU', callback=self._on_root)
            dpg.add_input_text(tag='reg_subkey', label='子键', default_value=self._default_subkey())
            dpg.add_button(label='列出值', callback=self._list_values)
            self.table_id = dpg.add_table(header_row=True)
            dpg.add_table_column(label='名称', parent=self.table_id)
            dpg.add_table_column(label='值', parent=self.table_id)
            dpg.add_input_text(tag='reg_name', label='名称')
            dpg.add_input_text(tag='reg_value', label='值')
            dpg.add_button(label='设置值', callback=self._set_value)
            dpg.add_button(label='删除值', callback=self._del_value)
            dpg.add_input_text(tag='reg_select_names', label='多选名称,逗号分隔')
            dpg.add_button(label='分析选中值', callback=self._analyze_selected)
            dpg.add_input_text(tag='analysis_output_reg', label='分析结果', multiline=True, readonly=True)
            dpg.add_button(label='备份当前子键', callback=self._backup_subkey)
            self.message_id = dpg.add_text('')
            self.backup_reg_message_id = dpg.add_text('')

    def _on_root(self, sender, data):
        self.root = dpg.get_value('reg_root')
        self.m = RegManager(self.root)
        dpg.set_value('reg_subkey', self._default_subkey())

    def _list_values(self, sender, data):
        subkey = dpg.get_value('reg_subkey')
        if self.table_id:
            children = dpg.get_item_children(self.table_id, 1) or []
            for c in children:
                dpg.delete_item(c)
        items = self.m.list_values(subkey)
        value_counts = {}
        for it in items:
            vstr = str(it['value'])
            value_counts[vstr] = value_counts.get(vstr, 0) + 1
        if not items:
            dpg.set_value(self.message_id, '无法列出，可能路径不存在或无权限')
        else:
            dpg.set_value(self.message_id, '')
            for item in items:
                row_id = dpg.add_table_row(parent=self.table_id)
                selectable_id = dpg.add_selectable(label=item['name'], parent=row_id)
                val = item['value']
                vstr = str(val)
                is_path_like = isinstance(val, str) and ("\\" in val or "/" in val)
                exists = False
                if is_path_like:
                    try:
                        exists = os.path.exists(normalize_path(val))
                    except Exception:
                        exists = False
                duplicate_value = value_counts.get(vstr, 0) > 1
                color = (255, 255, 255, 255)
                if is_path_like and not exists and duplicate_value:
                    color = (199, 21, 133, 255)
                elif is_path_like and not exists:
                    color = (220, 50, 47, 255)
                elif duplicate_value:
                    color = (255, 165, 0, 255)
                dpg.add_text(vstr, parent=row_id, color=color)
                handler = dpg.add_item_handler_registry()
                dpg.add_item_clicked_handler(parent=handler, callback=self._on_reg_row_click, user_data={'name': item['name'], 'value': item['value']})
                dpg.bind_item_handler_registry(selectable_id, handler)

    def _set_value(self, sender, data):
        subkey = dpg.get_value('reg_subkey')
        name = dpg.get_value('reg_name')
        value = dpg.get_value('reg_value')
        if subkey and name:
            try:
                self.m.set_value(subkey, name, value)
                dpg.set_value(self.message_id, '已设置')
                self._list_values(sender, data)
            except Exception:
                dpg.set_value(self.message_id, '写入失败，需管理员权限或路径错误')
        dpg.set_value('reg_name', '')
        dpg.set_value('reg_value', '')

    def _del_value(self, sender, data):
        subkey = dpg.get_value('reg_subkey')
        name = dpg.get_value('reg_name')
        if subkey and name:
            self.pending_reg_name = name
            val, _ = self.m.get_value(subkey, name)
            text = self._build_reg_delete_warning(subkey, name, val) or '确认删除该注册表值?'
            dpg.set_value('confirm_delete_reg_text', text)
            dpg.configure_item('confirm_delete_reg', show=True)
        dpg.set_value('reg_name', '')
        dpg.set_value('reg_value', '')

    def _analyze_selected(self, sender, data):
        subkey = dpg.get_value('reg_subkey')
        names = dpg.get_value('reg_select_names')
        items = []
        if names:
            for n in [x.strip() for x in names.split(',') if x.strip()]:
                v, _ = self.m.get_value(subkey, n)
                items.append({'kind': 'reg', 'key': f'{self.root}\\{subkey}\\{n}', 'value': v})
        res = self.analyzer.analyze(items)
        dpg.set_value('analysis_output_reg', json.dumps(res, ensure_ascii=False))
        dpg.set_value('reg_select_names', '')

    def _on_reg_row_click(self, sender, app_data, user_data):
        if dpg.is_mouse_button_double_clicked(dpg.mvMouseButton_Left):
            name = user_data['name']
            value = user_data['value']
            dpg.set_value('reg_name', name)
            dpg.set_value('reg_value', str(value))
            cur = dpg.get_value('reg_select_names') or ''
            names = [x.strip() for x in cur.split(',') if x.strip()]
            if name not in names:
                names.append(name)
            dpg.set_value('reg_select_names', ','.join(names))

    def _backup_subkey(self, sender, data):
        subkey = dpg.get_value('reg_subkey')
        items = self.m.list_values(subkey)
        reg_data = {f'{self.root}\\{subkey}\\{i["name"]}': i['value'] for i in items}
        out_dir = str(self.base_dir / '.backup')
        meta = {'root': self.root, 'subkey': subkey}
        path = backup({}, reg_data, out_dir, category='reg', meta=meta)
        dpg.set_value(self.backup_reg_message_id, f'已备份: {path}')

    def _reg_restore_selected(self, sender, app_data):
        fp = app_data.get('file_path_name') if isinstance(app_data, dict) else None
        if not fp:
            return
        j = restore(fp)
        reg_data = j.get('reg', {})
        for k, v in reg_data.items():
            if k.startswith(f'{self.root}\\'):
                parts = k.split('\\')
                sub = '\\'.join(parts[1:-1])
                name = parts[-1]
                self.m.set_value(sub, name, v)
        self._list_values(sender, app_data)

    def _open_reg_restore_dialog(self, sender, data):
        if not dpg.does_item_exist('reg_restore_dialog'):
            with dpg.file_dialog(directory_selector=False, show=False, tag='reg_restore_dialog', callback=self._reg_restore_selected):
                dpg.add_file_extension('.json')
        dpg.configure_item('reg_restore_dialog', show=True)

    def _default_subkey(self) -> str:
        if self.root == 'HKLM':
            return 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment'
        return 'Environment'

    def _confirm_delete_reg_yes(self, sender, data):
        subkey = dpg.get_value('reg_subkey')
        if self.pending_reg_name:
            try:
                self.m.delete_value(subkey, self.pending_reg_name)
                dpg.set_value(self.message_id, '已删除')
                self._list_values(sender, data)
            except Exception:
                dpg.set_value(self.message_id, '删除失败，需管理员权限或路径错误')
            dpg.configure_item('confirm_delete_reg', show=False)
            self.pending_reg_name = None

    def _build_reg_delete_warning(self, subkey: str, name: str, value):
        reasons = []
        critical_names = {'Path','PATH','TEMP','TMP','JAVA_HOME','PYTHONPATH'}
        if name in critical_names:
            reasons.append('关键名称')
        critical_keys = ['Environment','SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment','SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run','SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce']
        for ck in critical_keys:
            if subkey.lower() == ck.lower():
                reasons.append('关键子键')
                break
        if value is not None:
            if isinstance(value, str) and ('\\' in value or '/' in value):
                try:
                    if os.path.exists(normalize_path(value)):
                        reasons.append('指向存在路径')
                except Exception:
                    pass
            if isinstance(value, str) and re.search(r'%[^%]+%', value):
                reasons.append('包含变量引用')
        if reasons:
            return '该注册表值谨慎删除：' + '，'.join(reasons) + '。是否继续?'
        return None
