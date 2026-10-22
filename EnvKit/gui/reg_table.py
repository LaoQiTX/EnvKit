import os
import dearpygui.dearpygui as dpg
from typing import List, Dict, Any, Optional
from core.reg_manager import RegManager, PRESET_KEYS, TYPE_MAP, STR_TO_TYPE
from core.analyzer import Analyzer
from core.backup import backup, restore
from utils.path_helper import get_backup_dir
from utils.win_utils import choose_file, open_in_explorer
from utils.path_check import normalize_path
from gui.theme import (
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_MUTED,
    COLOR_PRIMARY, create_button_theme
)

class RegUI:
    def __init__(self, analyzer: Analyzer, on_send_to_diagnose=None):
        self.root = 'HKCU'
        self.m = RegManager(self.root)
        self.analyzer = analyzer
        self.on_send_to_diagnose = on_send_to_diagnose
        self.table_id = None
        self.status_message_id = None
        self.pending_delete_name = None
        self.search_filter = ""
        self.items_cache = []

    def build(self):
        btn_primary = create_button_theme((37, 99, 235), (59, 130, 246), (29, 78, 216))
        btn_danger = create_button_theme((220, 38, 38), (239, 68, 68), (185, 28, 28))
        btn_success = create_button_theme((16, 185, 129), (52, 211, 153), (5, 150, 105))

        # 删除确认弹窗
        with dpg.window(modal=True, show=False, tag='modal_delete_reg_confirm', no_move=True, no_resize=True, width=420, height=190):
            dpg.add_text("[提示] 确认删除注册表键值？", color=COLOR_WARNING)
            dpg.add_separator()
            dpg.add_text(tag='modal_delete_reg_text', wrap=390)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                b_del_yes = dpg.add_button(label="确认删除", callback=self._do_delete_confirmed)
                dpg.bind_item_theme(b_del_yes, btn_danger)
                dpg.add_button(label="取消", callback=lambda s, d: dpg.configure_item('modal_delete_reg_confirm', show=False))

        # 顶部配置栏
        with dpg.group(horizontal=True):
            dpg.add_text("根键:")
            dpg.add_radio_button(
                items=['HKCU (当前用户)', 'HKLM (本地计算机)'],
                default_value='HKCU (当前用户)',
                horizontal=True,
                tag='reg_root_radio',
                callback=self._on_root_change
            )
            dpg.add_spacer(width=20)
            dpg.add_text("常用快捷子键:")
            preset_labels = [p['label'] for p in PRESET_KEYS]
            dpg.add_combo(
                items=preset_labels,
                default_value=preset_labels[0],
                width=240,
                callback=self._on_preset_selected
            )

        dpg.add_spacer(height=4)

        with dpg.group(horizontal=True):
            dpg.add_text("子键路径:")
            dpg.add_input_text(tag='reg_subkey_input', default_value='Environment', width=520)
            b_list = dpg.add_button(label="查询列出值", callback=self._list_values)
            dpg.bind_item_theme(b_list, btn_primary)
            
            b_bak = dpg.add_button(label="备份当前子键", callback=self._backup_subkey)
            dpg.bind_item_theme(b_bak, btn_success)
            
            dpg.add_button(label="从备份恢复...", callback=self._restore_subkey)

        dpg.add_spacer(height=4)

        with dpg.group(horizontal=True):
            dpg.add_text("过滤搜索:")
            dpg.add_input_text(hint="输入名称或内容筛选...", callback=self._on_search_change, width=240)

        dpg.add_spacer(height=6)

        # 注册表键值列表
        with dpg.child_window(height=380, border=True):
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
            dpg.add_table_column(label="名称 (单击选中载入编辑)", width_stretch=True, init_width_or_weight=220, parent=self.table_id)
            dpg.add_table_column(label="类型", width_fixed=True, init_width_or_weight=130, parent=self.table_id)
            dpg.add_table_column(label="数值状态", width_fixed=True, init_width_or_weight=130, parent=self.table_id)
            dpg.add_table_column(label="数值数据 (Value Data)", width_stretch=True, init_width_or_weight=450, parent=self.table_id)

        dpg.add_spacer(height=6)

        # 底部编辑卡片
        with dpg.child_window(height=180, border=True):
            dpg.add_text("[编辑] 注册表键值编辑（新建/修改/删除）：", color=COLOR_PRIMARY)
            with dpg.group(horizontal=True):
                dpg.add_text("名称:")
                dpg.add_input_text(tag="reg_val_name", width=220)
                dpg.add_text("类型:")
                dpg.add_combo(tag="reg_val_type", items=list(STR_TO_TYPE.keys()), default_value='REG_SZ', width=150)
                dpg.add_text("数值数据:")
                dpg.add_input_text(tag="reg_val_data", width=420)

            dpg.add_spacer(height=6)
            with dpg.group(horizontal=True):
                b_set = dpg.add_button(label="设置 / 保存键值", callback=self._set_value)
                dpg.bind_item_theme(b_set, btn_primary)

                b_del = dpg.add_button(label="删除该键值", callback=self._request_delete)
                dpg.bind_item_theme(b_del, btn_danger)

                dpg.add_button(label="清空输入", callback=self._clear_inputs)
                
                if self.on_send_to_diagnose:
                    dpg.add_button(label="发送到 AI 深入分析", callback=self._send_to_diagnose)

            self.status_message_id = dpg.add_text("", color=COLOR_SUCCESS)

        self._list_values()

    def _on_root_change(self, sender, data):
        self.root = 'HKCU' if 'HKCU' in data else 'HKLM'
        self.m = RegManager(self.root)
        if self.root == 'HKLM':
            dpg.set_value('reg_subkey_input', r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment')
        else:
            dpg.set_value('reg_subkey_input', r'Environment')
        self._list_values()

    def _on_preset_selected(self, sender, data):
        preset = next((p for p in PRESET_KEYS if p['label'] == data), None)
        if preset:
            self.root = preset['root']
            self.m = RegManager(self.root)
            radio_val = 'HKCU (当前用户)' if self.root == 'HKCU' else 'HKLM (本地计算机)'
            dpg.set_value('reg_root_radio', radio_val)
            dpg.set_value('reg_subkey_input', preset['subkey'])
            self._list_values()

    def _on_search_change(self, sender, data):
        self.search_filter = data
        self._render_rows()

    def _clear_inputs(self, sender=None, data=None):
        dpg.set_value("reg_val_name", "")
        dpg.set_value("reg_val_data", "")

    def _list_values(self, sender=None, data=None):
        subkey = dpg.get_value('reg_subkey_input').strip()
        try:
            self.items_cache = self.m.list_values(subkey)
            dpg.set_value(self.status_message_id, f"成功获取 {len(self.items_cache)} 个注册表项")
        except PermissionError:
            self.items_cache = []
            dpg.set_value(self.status_message_id, "权限不足：读取此注册表子键需要管理员权限！")
        except Exception as e:
            self.items_cache = []
            dpg.set_value(self.status_message_id, f"查询失败: {e}")
            
        self._render_rows()

    def _render_rows(self):
        if not self.table_id or not dpg.does_item_exist(self.table_id):
            return
            
        children = dpg.get_item_children(self.table_id, 1) or []
        for c in children:
            dpg.delete_item(c)

        flt = self.search_filter.lower().strip()

        for item in self.items_cache:
            name = item['name']
            val = item['value']
            val_str = str(val)
            
            if flt and (flt not in name.lower() and flt not in val_str.lower()):
                continue

            row_id = dpg.add_table_row(parent=self.table_id)
            
            # 名称（整行高亮，单击任意处可载入编辑）
            dpg.add_selectable(
                label=name,
                parent=row_id,
                span_columns=True,
                callback=self._on_row_click,
                user_data=item
            )

            # 类型
            dpg.add_text(item.get('type_str', 'REG_SZ'), parent=row_id, color=COLOR_MUTED)

            # 状态检测
            badge = "常规"
            badge_color = COLOR_MUTED
            is_path_like = isinstance(val, str) and ('\\' in val or '/' in val)
            if is_path_like:
                norm = normalize_path(val)
                if os.path.exists(norm):
                    badge = "指向存在文件"
                    badge_color = COLOR_SUCCESS
                else:
                    badge = "路径不存在"
                    badge_color = COLOR_DANGER

            dpg.add_text(badge, parent=row_id, color=badge_color)

            # 数据值
            disp_val = val_str if len(val_str) <= 120 else val_str[:117] + "..."
            dpg.add_text(disp_val, parent=row_id)

    def _on_row_click(self, sender, app_data, user_data):
        name = user_data['name']
        val = user_data['value']
        vtype_str = user_data.get('type_str', 'REG_SZ')
        dpg.set_value("reg_val_name", name)
        dpg.set_value("reg_val_data", str(val))
        if vtype_str in STR_TO_TYPE:
            dpg.set_value("reg_val_type", vtype_str)
        if self.status_message_id and dpg.does_item_exist(self.status_message_id):
            dpg.set_value(self.status_message_id, f"已选中注册表键值 [{name}]，可在下方直接修改或删除。")

    def _set_value(self, sender, data):
        subkey = dpg.get_value('reg_subkey_input').strip()
        name = dpg.get_value('reg_val_name').strip()
        val = dpg.get_value('reg_val_data')
        t_str = dpg.get_value('reg_val_type')
        vtype = STR_TO_TYPE.get(t_str, 1)

        if not subkey or not name:
            dpg.set_value(self.status_message_id, "错误：子键路径和名称均不能为空！")
            return
            
        try:
            self.m.set_value(subkey, name, val, vtype)
            dpg.set_value(self.status_message_id, f"成功保存注册表键值 [{name}]！")
            self._list_values()
        except PermissionError:
            dpg.set_value(self.status_message_id, "权限不足：修改此项需要管理员权限！")
        except Exception as e:
            dpg.set_value(self.status_message_id, f"保存失败: {e}")

    def _request_delete(self, sender, data):
        name = dpg.get_value('reg_val_name').strip()
        subkey = dpg.get_value('reg_subkey_input').strip()
        if not name:
            dpg.set_value(self.status_message_id, "请先选择要删除的注册表键值！")
            return

        self.pending_delete_name = name
        text = f"确定要永久删除注册表项 [{self.root}\\{subkey}] 下的键值 [{name}] 吗？\n请确认该键值非关键系统依赖。"
        dpg.set_value('modal_delete_reg_text', text)
        dpg.configure_item('modal_delete_reg_confirm', show=True)

    def _do_delete_confirmed(self, sender, data):
        name = self.pending_delete_name
        subkey = dpg.get_value('reg_subkey_input').strip()
        dpg.configure_item('modal_delete_reg_confirm', show=False)
        if not name:
            return

        try:
            self.m.delete_value(subkey, name)
            self._clear_inputs()
            dpg.set_value(self.status_message_id, f"成功删除注册表键值 [{name}]！")
            self._list_values()
        except PermissionError:
            dpg.set_value(self.status_message_id, "权限不足：删除此键值需要管理员权限！")
        except Exception as e:
            dpg.set_value(self.status_message_id, f"删除失败: {e}")
        finally:
            self.pending_delete_name = None

    def _backup_subkey(self, sender, data):
        subkey = dpg.get_value('reg_subkey_input').strip()
        items = self.m.list_values(subkey)
        reg_map = {f"{self.root}\\{subkey}\\{i['name']}": {'value': i['value'], 'type': i['type']} for i in items}
        meta = {'root': self.root, 'subkey': subkey}
        path = backup({}, reg_map, category='reg', meta=meta)
        dpg.set_value(self.status_message_id, f"当前注册表子键已备份至: {path}")

    def _restore_subkey(self, sender, data):
        initial_dir = str(get_backup_dir())
        chosen = choose_file(
            initial_dir=initial_dir,
            file_types=[("EnvKit 注册表备份 (*.json)", "*.json"), ("所有文件", "*.*")],
            title="选择要恢复的注册表备份文件"
        )
        if not chosen:
            return
            
        try:
            data = restore(chosen)
            reg_map = data.get('reg', {})
            restored = 0
            for full_key, item_val in reg_map.items():
                if full_key.startswith(f"{self.root}\\"):
                    parts = full_key.split('\\')
                    sub = '\\'.join(parts[1:-1])
                    name = parts[-1]
                    val = item_val.get('value') if isinstance(item_val, dict) else item_val
                    vtype = item_val.get('type', 1) if isinstance(item_val, dict) else 1
                    self.m.set_value(sub, name, val, vtype)
                    restored += 1
            dpg.set_value(self.status_message_id, f"成功从备份恢复了 {restored} 个注册表键值！")
            self._list_values()
        except Exception as e:
            dpg.set_value(self.status_message_id, f"恢复失败: {e}")

    def _send_to_diagnose(self, sender, data):
        subkey = dpg.get_value('reg_subkey_input').strip()
        name = dpg.get_value('reg_val_name').strip()
        val = dpg.get_value('reg_val_data')
        if not name:
            dpg.set_value(self.status_message_id, "请先选择一个键值进行分析！")
            return
        if self.on_send_to_diagnose:
            self.on_send_to_diagnose([{'kind': 'reg', 'key': f"{self.root}\\{subkey}\\{name}", 'value': val}])
