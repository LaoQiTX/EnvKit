import os
import ctypes
import dearpygui.dearpygui as dpg
from typing import List, Dict, Any, Optional
from core.reg_manager import RegManager, PRESET_KEYS, TYPE_MAP, STR_TO_TYPE

try:
    _RESIZE_CURSOR = ctypes.windll.user32.LoadCursorW(None, 32644) # IDC_SIZEWE
except Exception:
    _RESIZE_CURSOR = None
from core.analyzer import Analyzer
from core.backup import backup, restore
from utils.path_helper import get_backup_dir
from utils.win_utils import choose_file, open_in_explorer
from utils.path_check import normalize_path
from gui.theme import (
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_MUTED,
    COLOR_PRIMARY, create_button_theme, create_splitter_theme,
    get_table_row_selected_color
)

class RegUI:
    def __init__(self, analyzer: Analyzer, on_send_to_diagnose=None, on_jump_to_env=None):
        self.root = 'HKCU'
        self.m = RegManager(self.root)
        self.analyzer = analyzer
        self.on_send_to_diagnose = on_send_to_diagnose
        self.on_jump_to_env = on_jump_to_env
        
        self.table_id = None
        self.footer_count_id = None
        self.status_banner_id = None
        self.search_filter = ""
        self.items_cache = []
        
        # 详情面板状态与可拖拽分割条
        self.selected_item = None
        self.is_new_mode = False
        self.detail_container_id = None
        self.detail_width = 410
        self.is_dragging = False
        self.left_pane_tag = 'reg_left_pane'
        self.right_pane_tag = 'reg_right_pane'
        self.splitter_tag = 'reg_splitter_bar'

    def _list_values(self):
        subkey = dpg.get_value('reg_address_input').strip() if dpg.does_item_exist('reg_address_input') else 'Environment'
        try:
            self.items_cache = self.m.list_values(subkey)
            self._render_rows()
            self._set_banner(f"就绪。当前子键读取到 {len(self.items_cache)} 项注册表值。")
        except PermissionError:
            self.items_cache = []
            self._render_rows()
            self._set_banner("权限不足：读取此注册表项需要管理员权限！", is_error=True)
        except Exception as e:
            self.items_cache = []
            self._render_rows()
            self._set_banner(f"读取失败: {e}", is_error=True)

        # 默认选中第一项
        if self.items_cache and not self.is_new_mode:
            self.selected_item = self.items_cache[0]
        else:
            self.selected_item = None
        self._render_detail_panel()

    def _render_rows(self):
        if not self.table_id or not dpg.does_item_exist(self.table_id):
            return

        children = dpg.get_item_children(self.table_id, 1) or []
        for c in children:
            dpg.delete_item(c)

        flt = self.search_filter.lower().strip()
        filtered_count = 0
        row_idx = 0
        sel_color = get_table_row_selected_color()

        for item in self.items_cache:
            name = item['name']
            val = str(item['value'])
            t_str = item.get('type_str', 'REG_SZ')

            if flt and (flt not in name.lower() and flt not in val.lower()):
                continue

            filtered_count += 1
            row_id = dpg.add_table_row(parent=self.table_id)
            is_sel = (self.selected_item and self.selected_item['name'] == name and not self.is_new_mode)

            # 1. 名称（单击整行在右侧直接连续编辑，无人工高度，自然垂直居中）
            dpg.add_selectable(
                label=name if name else "(默认)",
                parent=row_id,
                span_columns=True,
                default_value=is_sel,
                callback=self._on_row_selected,
                user_data=item
            )

            # 2. 类型
            dpg.add_text(t_str, parent=row_id, color=COLOR_MUTED)

            # 3. 数据
            disp_val = val if len(val) <= 80 else val[:77] + "..."
            dpg.add_text(disp_val, parent=row_id)

            if is_sel:
                dpg.set_table_row_color(self.table_id, row_idx, sel_color)
            else:
                dpg.unset_table_row_color(self.table_id, row_idx)
            row_idx += 1

        if self.footer_count_id and dpg.does_item_exist(self.footer_count_id):
            dpg.set_value(self.footer_count_id, f"{len(self.items_cache)} 个值")

    def _on_row_selected(self, sender, app_data, user_data):
        self.selected_item = user_data
        self.is_new_mode = False
        self._render_rows()
        self._render_detail_panel()

    def _switch_to_new_mode(self, sender=None, data=None):
        self.is_new_mode = True
        self.selected_item = None
        self._render_rows()
        self._render_detail_panel()

    def _render_detail_panel(self):
        if not self.detail_container_id or not dpg.does_item_exist(self.detail_container_id):
            return

        children = dpg.get_item_children(self.detail_container_id, 1) or []
        for c in children:
            dpg.delete_item(c)

        btn_primary = create_button_theme((46, 95, 204), (36, 77, 176), (25, 60, 145), text_color=(255, 255, 255))
        btn_danger = create_button_theme((164, 68, 54), (190, 80, 65), (140, 55, 45), text_color=(255, 255, 255))

        subkey = dpg.get_value('reg_address_input') if dpg.does_item_exist('reg_address_input') else 'Environment'
        full_key_path = f"{self.root}\\{subkey}"

        # -------------------------------------------------------------
        # 模式 1: 新建值模式
        # -------------------------------------------------------------
        if self.is_new_mode:
            dpg.add_text("值详情", parent=self.detail_container_id, color=COLOR_MUTED)
            dpg.add_text("新建注册表值", parent=self.detail_container_id, color=COLOR_PRIMARY)
            dpg.add_text(f"所在键: {full_key_path}", parent=self.detail_container_id, color=COLOR_MUTED, wrap=340)
            dpg.add_separator(parent=self.detail_container_id)
            dpg.add_spacer(height=6, parent=self.detail_container_id)

            dpg.add_text("值名称:", parent=self.detail_container_id)
            dpg.add_input_text(tag="reg_detail_new_name", hint="留空表示 (默认) 项", width=-1, parent=self.detail_container_id)
            dpg.add_spacer(height=4, parent=self.detail_container_id)

            dpg.add_text("类型:", parent=self.detail_container_id)
            dpg.add_combo(tag="reg_detail_new_type", items=list(STR_TO_TYPE.keys()), default_value='REG_SZ', width=-1, parent=self.detail_container_id)
            dpg.add_spacer(height=4, parent=self.detail_container_id)

            dpg.add_text("数值数据 (Data):", parent=self.detail_container_id)
            dpg.add_input_text(tag="reg_detail_new_data", multiline=True, height=120, width=-1, parent=self.detail_container_id)
            dpg.add_spacer(height=10, parent=self.detail_container_id)

            with dpg.group(horizontal=True, parent=self.detail_container_id):
                b_save = dpg.add_button(label="[保存] 写入注册表", callback=self._do_create_new)
                dpg.bind_item_theme(b_save, btn_primary)
                dpg.add_button(label="取消", callback=lambda s, d: self._cancel_new_mode())
            return

        # -------------------------------------------------------------
        # 模式 2: 未选中值
        # -------------------------------------------------------------
        if not self.selected_item:
            dpg.add_text("值详情", parent=self.detail_container_id, color=COLOR_MUTED)
            dpg.add_text("未选择注册表项", parent=self.detail_container_id)
            dpg.add_text("在左侧表格中点击任意注册表项查看详情与编辑，或点击“+ 新建值”。", parent=self.detail_container_id, color=COLOR_MUTED, wrap=340)
            return

        item = self.selected_item
        name = item['name']
        val = str(item['value'])
        t_str = item.get('type_str', 'REG_SZ')

        # 头部面包屑与值名
        dpg.add_text("值详情", parent=self.detail_container_id, color=COLOR_MUTED)
        with dpg.group(horizontal=True, parent=self.detail_container_id):
            dpg.add_text(name if name else "(默认)", color=COLOR_PRIMARY)
            dpg.add_spacer(width=6)
            dpg.add_text(f"[{t_str}]", color=COLOR_MUTED)

        dpg.add_separator(parent=self.detail_container_id)
        dpg.add_spacer(height=4, parent=self.detail_container_id)

        # 1. 所在键
        dpg.add_text("所在键:", parent=self.detail_container_id, color=COLOR_MUTED)
        with dpg.group(horizontal=True, parent=self.detail_container_id):
            dpg.add_input_text(default_value=full_key_path, readonly=True, width=280)
            dpg.add_button(label="复制", callback=lambda s, d: dpg.set_clipboard_text(full_key_path))

        dpg.add_spacer(height=6, parent=self.detail_container_id)

        # 2. 值名称
        dpg.add_text("值名称:", parent=self.detail_container_id, color=COLOR_MUTED)
        dpg.add_input_text(tag="reg_detail_edit_name", default_value=name, width=-1, parent=self.detail_container_id)

        dpg.add_spacer(height=6, parent=self.detail_container_id)

        # 3. 类型
        dpg.add_text("类型:", parent=self.detail_container_id, color=COLOR_MUTED)
        dpg.add_combo(tag="reg_detail_edit_type", items=list(STR_TO_TYPE.keys()), default_value=t_str, width=-1, parent=self.detail_container_id)

        dpg.add_spacer(height=6, parent=self.detail_container_id)

        # 4. 数值数据
        dpg.add_text("数值数据 (Value Data):", parent=self.detail_container_id, color=COLOR_MUTED)
        dpg.add_input_text(tag="reg_detail_edit_data", default_value=val, multiline=True, height=130, width=-1, parent=self.detail_container_id)

        dpg.add_spacer(height=6, parent=self.detail_container_id)

        # 5. 关联环境变量卡片 (设计稿特色)
        is_env_key = ('Environment' in subkey)
        if is_env_key and name:
            with dpg.child_window(height=60, border=True, no_scrollbar=True, parent=self.detail_container_id):
                dpg.add_text("关联环境变量：此值也直接对应 Windows 环境变量", color=COLOR_PRIMARY)
                if self.on_jump_to_env:
                    dpg.add_button(label="在环境变量中查看 ->", callback=lambda s, d: self.on_jump_to_env(name))

            dpg.add_spacer(height=6, parent=self.detail_container_id)

        # 6. 保存与删除按钮组
        with dpg.group(horizontal=True, parent=self.detail_container_id):
            b_save = dpg.add_button(label="[保存] 更新键值", callback=self._save_value)
            dpg.bind_item_theme(b_save, btn_primary)

            b_del = dpg.add_button(label="[删除] 删除此键值", callback=self._request_delete)
            dpg.bind_item_theme(b_del, btn_danger)

            if self.on_send_to_diagnose:
                dpg.add_button(label="[AI] 分析", callback=self._send_to_diagnose)

    def _cancel_new_mode(self):
        self.is_new_mode = False
        self._render_detail_panel()

    def _do_create_new(self, sender, data):
        subkey = dpg.get_value('reg_address_input').strip()
        name = dpg.get_value("reg_detail_new_name").strip()
        t_str = dpg.get_value("reg_detail_new_type")
        val = dpg.get_value("reg_detail_new_data")
        vtype = STR_TO_TYPE.get(t_str, 1)

        try:
            self.m.set_value(subkey, name, val, vtype)
            self.is_new_mode = False
            self._list_values()
            self._set_banner(f"成功创建注册表键值 [{name}]！")
        except PermissionError:
            self._set_banner("权限不足：写入此注册表子键需管理员权限！", is_error=True)
        except Exception as e:
            self._set_banner(f"创建失败: {e}", is_error=True)

    def _save_value(self, sender, data):
        subkey = dpg.get_value('reg_address_input').strip()
        name = dpg.get_value("reg_detail_edit_name").strip()
        t_str = dpg.get_value("reg_detail_edit_type")
        val = dpg.get_value("reg_detail_edit_data")
        vtype = STR_TO_TYPE.get(t_str, 1)

        try:
            self.m.set_value(subkey, name, val, vtype)
            self._list_values()
            self._set_banner(f"成功保存注册表键值 [{name}]！")
        except PermissionError:
            self._set_banner("权限不足：修改此项需要管理员权限！", is_error=True)
        except Exception as e:
            self._set_banner(f"保存失败: {e}", is_error=True)

    def _request_delete(self, sender, data):
        if not self.selected_item:
            return
        name = self.selected_item['name']
        self.pending_delete_name = name
        subkey = dpg.get_value('reg_address_input').strip()
        text = f"您确定要删除 [{self.root}\\{subkey}] 下的键值 [{name}] 吗？"
        dpg.set_value('modal_delete_reg_text', text)
        dpg.configure_item('modal_delete_reg_confirm', show=True)

    def _do_delete_confirmed(self, sender, data):
        name = self.pending_delete_name
        dpg.configure_item('modal_delete_reg_confirm', show=False)
        if not name:
            return
        subkey = dpg.get_value('reg_address_input').strip()
        try:
            self.m.delete_value(subkey, name)
            self.selected_item = None
            self._list_values()
            self._set_banner(f"已成功删除键值 [{name}]！")
        except PermissionError:
            self._set_banner("权限不足：删除此项需管理员权限！", is_error=True)
        except Exception as e:
            self._set_banner(f"删除失败: {e}", is_error=True)
        finally:
            self.pending_delete_name = None

    def _backup_subkey(self, sender=None, data=None):
        subkey = dpg.get_value('reg_address_input').strip()
        full_path = f"{self.root}\\{subkey}"
        data_to_bak = {f"{full_path}\\{it['name']}": it['value'] for it in self.items_cache}
        path = backup({}, data_to_bak, category='reg', meta={'subkey': full_path})
        self._set_banner(f"子键快照已成功导出至: {path}")

    def _restore_subkey(self, sender=None, data=None):
        initial_dir = str(get_backup_dir())
        chosen = choose_file(
            initial_dir=initial_dir,
            file_types=[("EnvKit 注册表备份 (*.json)", "*.json"), ("所有文件", "*.*")],
            title="选择要还原的注册表备份文件"
        )
        if not chosen:
            return
        try:
            data = restore(chosen)
            reg_map = data.get('reg', {})
            if not reg_map:
                self._set_banner("备份文件中未找到有效的注册表数据！", is_error=True)
                return
            subkey = dpg.get_value('reg_address_input').strip()
            restored = 0
            for k, v in reg_map.items():
                val_name = k.split('\\')[-1]
                self.m.set_value(subkey, val_name, v, 1)
                restored += 1
            self._list_values()
            self._set_banner(f"成功从快照还原了 {restored} 项键值！")
        except Exception as e:
            self._set_banner(f"还原失败: {e}", is_error=True)

    def _send_to_diagnose(self, sender, data):
        if not self.selected_item or not self.on_send_to_diagnose:
            return
        name = self.selected_item['name']
        val = str(self.selected_item['value'])
        subkey = dpg.get_value('reg_address_input').strip()
        full_key = f"{self.root}\\{subkey}"
        self.on_send_to_diagnose([{'kind': 'reg', 'scope': self.root, 'key': f"{full_key}\\{name}", 'value': val}])

    def _set_banner(self, msg: str, is_error: bool = False):
        if self.status_banner_id and dpg.does_item_exist(self.status_banner_id):
            dpg.set_value(self.status_banner_id, msg)
            dpg.configure_item(self.status_banner_id, color=COLOR_DANGER if is_error else COLOR_SUCCESS)

    def build(self):
        btn_primary = create_button_theme((46, 95, 204), (36, 77, 176), (25, 60, 145), text_color=(255, 255, 255))
        btn_danger = create_button_theme((164, 68, 54), (190, 80, 65), (140, 55, 45), text_color=(255, 255, 255))

        # 删除确认弹窗
        with dpg.window(modal=True, show=False, tag='modal_delete_reg_confirm', no_move=True, no_resize=True, width=440, height=200):
            dpg.add_text("[提示] 确认删除注册表键值？", color=COLOR_WARNING)
            dpg.add_separator()
            dpg.add_text(tag='modal_delete_reg_text', wrap=410)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                b_del_yes = dpg.add_button(label="确认删除", callback=self._do_delete_confirmed)
                dpg.bind_item_theme(b_del_yes, btn_danger)
                dpg.add_button(label="取消", callback=lambda s, d: dpg.configure_item('modal_delete_reg_confirm', show=False))

        splitter_theme = create_splitter_theme()

        # =============================================================
        # 双栏现代化架构：左侧主工作区 (Values)，中间拖拽分割条，右侧连续详情区 (Details)
        # =============================================================
        with dpg.group(horizontal=True):
            # ---------------------------------------------------------
            # 1. 中部主工作区 (Middle Content Workspace) - 动态自适应宽度
            # ---------------------------------------------------------
            with dpg.child_window(tag=self.left_pane_tag, width=-self.detail_width - 12, height=-1, border=True, no_scrollbar=True):
                # 面包屑与大标题
                dpg.add_text("工作区 > 注册表", color=COLOR_MUTED)
                dpg.add_spacer(height=2)
                dpg.add_text("注册表", color=COLOR_PRIMARY)
                dpg.add_text("按键浏览配置，查看类型和值，并在应用前核对差异。", color=COLOR_MUTED)
                dpg.add_spacer(height=8)

                # 根键切换与快捷预设
                with dpg.group(horizontal=True):
                    dpg.add_button(label="HKEY_CURRENT_USER (当前用户)", callback=lambda s, d: self._switch_root('HKCU'))
                    dpg.add_spacer(width=10)
                    dpg.add_button(label="HKEY_LOCAL_MACHINE (本机系统)", callback=lambda s, d: self._switch_root('HKLM'))
                    dpg.add_spacer(width=20)
                    
                    dpg.add_text("常用快捷子键:")
                    preset_labels = [p['label'] for p in PRESET_KEYS]
                    dpg.add_combo(
                        items=preset_labels,
                        default_value=preset_labels[0],
                        width=210,
                        callback=self._on_preset_selected
                    )

                dpg.add_spacer(height=4)

                # 导航地址栏 (设计稿地址导航条)
                with dpg.group(horizontal=True):
                    dpg.add_text("计算机 >", color=COLOR_MUTED)
                    self.root_label_id = dpg.add_text(f"{self.root} >", color=COLOR_PRIMARY)
                    dpg.add_input_text(tag='reg_address_input', default_value='Environment', width=320)
                    dpg.add_button(label="跳转查询", callback=lambda s, d: self._list_values())
                    
                    b_new = dpg.add_button(label="[+] 新建值", callback=self._switch_to_new_mode)
                    dpg.bind_item_theme(b_new, btn_primary)

                    dpg.add_button(label="[导出] 快照", callback=self._backup_subkey)
                    dpg.add_button(label="[导入] 还原", callback=self._restore_subkey)

                dpg.add_spacer(height=6)

                # 过滤搜索框
                with dpg.group(horizontal=True):
                    dpg.add_input_text(hint="搜索此键中的值名称或内容... (Ctrl K)", callback=self._on_search_change, width=320)

                dpg.add_separator()
                dpg.add_spacer(height=4)

                # 键值表格：直接设置 scrollY=True, height=-42，去除纵向分割线，保证整行无缝纯色高亮
                self.table_id = dpg.add_table(
                    header_row=True,
                    resizable=True,
                    scrollY=True,
                    height=-42,
                    policy=dpg.mvTable_SizingStretchProp,
                    row_background=False,
                    borders_innerH=True,
                    borders_outerH=False,
                    borders_innerV=False,
                    borders_outerV=False
                )
                c_name = dpg.add_table_column(label="名称", width_stretch=True, init_width_or_weight=200, parent=self.table_id)
                c_type = dpg.add_table_column(label="类型", width_fixed=True, init_width_or_weight=130, parent=self.table_id)
                c_data = dpg.add_table_column(label="数据", width_stretch=True, init_width_or_weight=400, parent=self.table_id)

                for col in (c_name, c_type, c_data):
                    if dpg.does_item_exist('font_header'):
                        dpg.bind_item_font(col, 'font_header')

                dpg.add_spacer(height=4)

                # 底部信息条与状态横幅
                with dpg.group(horizontal=True):
                    self.footer_count_id = dpg.add_text("0 个值", color=COLOR_MUTED)
                    dpg.add_button(label="刷新", callback=lambda s, d: self._list_values())
                    dpg.add_spacer(width=20)
                    self.status_banner_id = dpg.add_text("当前没有待应用的更改 | 应用前将自动备份", color=COLOR_MUTED)

            # ---------------------------------------------------------
            # 2. 中间精致发丝拖拽分割线 (6px 优雅感应带，悬停蓝光 + ↔ 调节光标)
            # ---------------------------------------------------------
            b_split = dpg.add_button(
                tag=self.splitter_tag,
                label="",
                width=6,
                height=-1
            )
            dpg.bind_item_theme(b_split, splitter_theme)

            # ---------------------------------------------------------
            # 3. 右侧连续编辑与详情栏 (Right Details Panel)
            # ---------------------------------------------------------
            with dpg.child_window(tag=self.right_pane_tag, width=self.detail_width, height=-1, border=True, no_scrollbar=True):
                self.detail_container_id = dpg.add_group()

        # 注册鼠标与拖拽事件监听器 (鼠标绝对位置 1:1 跟随驱动，绝不乱跳)
        if not dpg.does_item_exist('reg_splitter_handler_reg'):
            with dpg.handler_registry(tag='reg_splitter_handler_reg'):
                dpg.add_mouse_move_handler(callback=self._on_mouse_move)
                dpg.add_mouse_drag_handler(button=0, threshold=0.0, callback=self._on_mouse_drag)
                dpg.add_mouse_release_handler(button=0, callback=self._on_mouse_release)

        self._list_values()

    def _on_mouse_move(self, sender=None, app_data=None, user_data=None):
        if dpg.does_item_exist(self.splitter_tag):
            if dpg.is_item_hovered(self.splitter_tag) or self.is_dragging:
                if _RESIZE_CURSOR:
                    ctypes.windll.user32.SetCursor(_RESIZE_CURSOR)

        if self.is_dragging:
            if not dpg.is_mouse_button_down(0):
                self.is_dragging = False
                return
            mx = dpg.get_mouse_pos()[0]
            vw = dpg.get_viewport_width()
            right_edge = vw - 20
            # 绝对跟随光标驱动：光标到哪，分割线中心就在哪，杜绝漂移和跳变
            new_w = max(260, min(820, int(right_edge - mx - 3)))
            if new_w != self.detail_width:
                self.detail_width = new_w
                dpg.set_item_width(self.left_pane_tag, -self.detail_width - 10)
                dpg.set_item_width(self.right_pane_tag, self.detail_width)

    def _on_mouse_drag(self, sender, app_data, user_data):
        if dpg.does_item_exist(self.splitter_tag) and dpg.is_item_active(self.splitter_tag):
            self.is_dragging = True
            self._on_mouse_move()

    def _on_mouse_release(self, sender, app_data, user_data):
        self.is_dragging = False

    def _switch_root(self, root_str: str):
        self.root = root_str
        self.m = RegManager(self.root)
        if dpg.does_item_exist(self.root_label_id):
            dpg.set_value(self.root_label_id, f"{self.root} >")
        if self.root == 'HKLM':
            dpg.set_value('reg_address_input', r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment')
        else:
            dpg.set_value('reg_address_input', r'Environment')
        self._list_values()

    def _on_preset_selected(self, sender, data):
        preset = next((p for p in PRESET_KEYS if p['label'] == data), None)
        if preset:
            self.root = preset['root']
            self.m = RegManager(self.root)
            if dpg.does_item_exist(self.root_label_id):
                dpg.set_value(self.root_label_id, f"{self.root} >")
            dpg.set_value('reg_address_input', preset['subkey'])
            self._list_values()

    def _on_search_change(self, sender, data):
        self.search_filter = data
        self._render_rows()
