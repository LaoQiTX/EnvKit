import os
import dearpygui.dearpygui as dpg
from typing import List, Dict, Any, Optional
from core.env_manager import EnvManager
from utils.path_check import analyze_paths, rebuild_path, clean_path_entries, normalize_path
from utils.win_utils import choose_directory, open_in_explorer
from gui.theme import COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_EMPTY, COLOR_MUTED, COLOR_PRIMARY, create_button_theme

class PathViewUI:
    def __init__(self, get_scope_callback):
        self.get_scope = get_scope_callback
        self.table_id = None
        self.stats_text_id = None
        self.path_entries = [] # list of dicts from analyze_paths
        self.search_filter = ""
        self.status_message_id = None
        self.selected_idx = None

    def _get_manager(self) -> EnvManager:
        return EnvManager(self.get_scope())

    def refresh(self):
        m = self._get_manager()
        raw_path = m.get('PATH') or ''
        self.path_entries = analyze_paths(raw_path)
        self._render_rows()
        self._update_stats()

    def _update_stats(self):
        if not self.stats_text_id:
            return
        total = len(self.path_entries)
        valid = sum(1 for e in self.path_entries if e['exists'] and not e['duplicate'])
        invalid = sum(1 for e in self.path_entries if not e['exists'] and not e['is_empty'])
        dups = sum(1 for e in self.path_entries if e['duplicate'])
        empty = sum(1 for e in self.path_entries if e['is_empty'])
        
        stat_str = f"PATH 总项: {total}  |  有效: {valid}  |  失效/不存在: {invalid}  |  重复: {dups}  |  空路径: {empty}"
        dpg.set_value(self.stats_text_id, stat_str)

    def _render_rows(self):
        if not self.table_id or not dpg.does_item_exist(self.table_id):
            return
            
        children = dpg.get_item_children(self.table_id, 1) or []
        for c in children:
            dpg.delete_item(c)

        filter_txt = self.search_filter.lower().strip()

        for idx, entry in enumerate(self.path_entries):
            raw = entry['raw']
            if filter_txt and filter_txt not in raw.lower():
                continue

            row_id = dpg.add_table_row(parent=self.table_id)
            
            # 1. 序号与整行高亮选中 (行高 34px 全覆盖)
            is_sel = (idx == self.selected_idx)
            dpg.add_selectable(
                label=f"#{idx + 1}",
                parent=row_id,
                span_columns=True,
                height=34,
                default_value=is_sel,
                callback=self._on_row_select,
                user_data=(idx, raw)
            )
            
            # 2. 状态标签 (垂直居中)
            badge_text = "有效"
            badge_color = COLOR_SUCCESS
            if entry['is_empty']:
                badge_text = "空路径"
                badge_color = COLOR_EMPTY
            elif not entry['exists'] and entry['duplicate']:
                badge_text = "失效且重复"
                badge_color = (236, 72, 153, 255) # 粉红
            elif not entry['exists']:
                badge_text = "不存在/失效"
                badge_color = COLOR_DANGER
            elif entry['duplicate']:
                badge_text = f"重复 (同#{entry.get('first_seen_index', 0)+1})"
                badge_color = COLOR_WARNING
            elif entry.get('is_file'):
                badge_text = "指向文件"
                badge_color = COLOR_WARNING

            with dpg.group(parent=row_id):
                dpg.add_spacer(height=3)
                dpg.add_text(badge_text, color=badge_color)

            # 3. 启用复选框 (垂直居中)
            chk_tag = f"path_enabled_{idx}"
            with dpg.group(parent=row_id):
                dpg.add_spacer(height=2)
                dpg.add_checkbox(tag=chk_tag, default_value=True, callback=self._on_toggle_enable, user_data=idx)

            # 4. 路径文本 (垂直居中)
            disp_text = raw if raw else "(空条目 ;;)"
            with dpg.group(parent=row_id):
                dpg.add_spacer(height=3)
                dpg.add_text(disp_text, color=badge_color if not entry['exists'] else (240, 243, 246, 255))

            # 5. 操作按钮组 (垂直居中)
            with dpg.group(parent=row_id):
                dpg.add_spacer(height=1)
                btn_group = dpg.add_group(horizontal=True)
                dpg.add_button(label="▲", parent=btn_group, callback=self._move_item, user_data=(idx, -1), width=28)
                dpg.add_button(label="▼", parent=btn_group, callback=self._move_item, user_data=(idx, 1), width=28)
                dpg.add_button(label="置顶", parent=btn_group, callback=self._move_to_top, user_data=idx)
                
                if entry['exists']:
                    dpg.add_button(label="打开", parent=btn_group, callback=lambda s, d, u: open_in_explorer(u), user_data=normalize_path(raw))
                    
                dpg.add_button(label="删除", parent=btn_group, callback=self._delete_item, user_data=idx)

    def _on_row_select(self, sender, app_data, user_data):
        idx, raw = user_data
        self.selected_idx = idx
        dpg.set_value("path_add_input", raw)
        if self.status_message_id and dpg.does_item_exist(self.status_message_id):
            dpg.set_value(self.status_message_id, f"已选中第 #{idx + 1} 项，已填充至下方输入框。")

    def build(self):
        btn_primary = create_button_theme((37, 99, 235), (59, 130, 246), (29, 78, 216), text_color=(255, 255, 255))
        btn_success = create_button_theme((16, 185, 129), (52, 211, 153), (5, 150, 105), text_color=(255, 255, 255))
        btn_danger = create_button_theme((220, 38, 38), (239, 68, 68), (185, 28, 28), text_color=(255, 255, 255))

        # 状态概览横幅
        with dpg.group(horizontal=True):
            dpg.add_text("[PATH] 状态体检：", color=COLOR_PRIMARY)
            self.stats_text_id = dpg.add_text("加载中...")
            
        dpg.add_spacer(height=4)

        # 快捷工具栏 - 行 1: 治理动作按钮
        with dpg.group(horizontal=True):
            b_clean = dpg.add_button(label="一键清理无效与空路径", callback=self._auto_clean_invalid)
            dpg.bind_item_theme(b_clean, btn_danger)
            
            b_dedup = dpg.add_button(label="一键去除重复项", callback=self._auto_dedup)
            dpg.bind_item_theme(b_dedup, btn_success)
            
            b_apply = dpg.add_button(label="应用当前修改并广播生效", callback=self._save_and_apply)
            dpg.bind_item_theme(b_apply, btn_primary)

            dpg.add_button(label="刷新", callback=lambda s, d: self.refresh())

        dpg.add_spacer(height=3)

        # 快捷工具栏 - 行 2: 搜索过滤与排序提示
        with dpg.group(horizontal=True):
            dpg.add_text("搜索过滤:")
            dpg.add_input_text(hint="输入关键字筛选路径...", callback=self._on_search_change, width=220)
            dpg.add_spacer(width=15)
            dpg.add_text("提示: 排序越靠前优先检索，点击单条可自动载入下方输入框", color=COLOR_MUTED)

        dpg.add_spacer(height=6)

        # PATH 列表容器 (自适应高度，无外层多余滚动条)
        with dpg.child_window(height=-130, border=True, no_scrollbar=True):
            self.table_id = dpg.add_table(
                header_row=True,
                resizable=True,
                scrollY=True,
                height=-1,
                policy=dpg.mvTable_SizingStretchProp,
                row_background=True,
                borders_innerH=True,
                borders_outerH=True,
                borders_innerV=True,
                borders_outerV=True
            )
            dpg.add_table_column(label="序号", width_fixed=True, init_width_or_weight=60, parent=self.table_id)
            dpg.add_table_column(label="状态诊断", width_fixed=True, init_width_or_weight=130, parent=self.table_id)
            dpg.add_table_column(label="启用", width_fixed=True, init_width_or_weight=50, parent=self.table_id)
            dpg.add_table_column(label="完整路径", width_stretch=True, init_width_or_weight=450, parent=self.table_id)
            dpg.add_table_column(label="操作管理", width_fixed=True, init_width_or_weight=220, parent=self.table_id)

        dpg.add_spacer(height=6)

        # 新增 PATH 条目卡片 (固定高度紧凑排版，无滚动条)
        with dpg.child_window(height=115, border=True, no_scrollbar=True):
            with dpg.group(horizontal=True):
                dpg.add_text("新增 / 编辑 PATH 条目:")
                dpg.add_input_text(tag="path_add_input", hint="输入目录路径，或点击右侧浏览选择...", width=520)
                dpg.add_button(label="浏览文件夹...", callback=self._browse_folder)

            dpg.add_spacer(height=4)
            with dpg.group(horizontal=True):
                b_add_tail = dpg.add_button(label="添加至末尾", callback=self._add_path_tail)
                dpg.bind_item_theme(b_add_tail, btn_primary)
                
                b_add_head = dpg.add_button(label="添加至首部 (最高优先级)", callback=self._add_path_head)
                dpg.bind_item_theme(b_add_head, btn_success)
                
                dpg.add_button(label="清空输入", callback=lambda s, d: dpg.set_value("path_add_input", ""))

            dpg.add_spacer(height=3)
            self.status_message_id = dpg.add_text("", color=COLOR_SUCCESS)

        self.refresh()

    def _on_search_change(self, sender, data):
        self.search_filter = data
        self._render_rows()

    def _browse_folder(self, sender, data):
        folder = choose_directory(title="选择要添加到 PATH 的目录")
        if folder:
            dpg.set_value("path_add_input", folder)

    def _add_path_tail(self, sender, data):
        p = dpg.get_value("path_add_input").strip()
        if not p:
            return
        m = self._get_manager()
        cur = m.get('PATH') or ''
        parts = [e for e in cur.split(';') if e.strip()]
        parts.append(p)
        try:
            m.update_path_entries(parts)
            dpg.set_value("path_add_input", "")
            dpg.set_value(self.status_message_id, f"已成功将路径追加至 PATH 末尾: {p}")
            self.refresh()
        except Exception as e:
            dpg.set_value(self.status_message_id, f"写入失败: {e}")

    def _add_path_head(self, sender, data):
        p = dpg.get_value("path_add_input").strip()
        if not p:
            return
        m = self._get_manager()
        cur = m.get('PATH') or ''
        parts = [e for e in cur.split(';') if e.strip()]
        parts.insert(0, p)
        try:
            m.update_path_entries(parts)
            dpg.set_value("path_add_input", "")
            dpg.set_value(self.status_message_id, f"已成功将路径置顶至 PATH 首部: {p}")
            self.refresh()
        except Exception as e:
            dpg.set_value(self.status_message_id, f"写入失败: {e}")

    def _move_item(self, sender, app_data, user_data):
        idx, delta = user_data
        new_idx = idx + delta
        if 0 <= new_idx < len(self.path_entries):
            self.path_entries[idx], self.path_entries[new_idx] = self.path_entries[new_idx], self.path_entries[idx]
            self._save_entries_to_system()

    def _move_to_top(self, sender, app_data, user_data):
        idx = user_data
        if idx > 0:
            item = self.path_entries.pop(idx)
            self.path_entries.insert(0, item)
            self._save_entries_to_system()

    def _delete_item(self, sender, app_data, user_data):
        idx = user_data
        if 0 <= idx < len(self.path_entries):
            removed = self.path_entries.pop(idx)
            self._save_entries_to_system()
            dpg.set_value(self.status_message_id, f"已删除 PATH 项: {removed['raw']}")

    def _on_toggle_enable(self, sender, app_data, user_data):
        pass

    def _save_and_apply(self, sender=None, data=None):
        enabled_entries = []
        for idx, entry in enumerate(self.path_entries):
            chk_tag = f"path_enabled_{idx}"
            if dpg.does_item_exist(chk_tag):
                if dpg.get_value(chk_tag):
                    enabled_entries.append(entry['raw'])
            else:
                enabled_entries.append(entry['raw'])
                
        m = self._get_manager()
        try:
            m.update_path_entries(enabled_entries)
            dpg.set_value(self.status_message_id, "PATH 已成功保存并广播至 Windows 系统环境！")
            self.refresh()
        except Exception as e:
            dpg.set_value(self.status_message_id, f"保存失败: {e}")

    def _save_entries_to_system(self):
        raw_list = [e['raw'] for e in self.path_entries if e['raw'].strip()]
        m = self._get_manager()
        try:
            m.update_path_entries(raw_list)
            self.refresh()
        except Exception as e:
            dpg.set_value(self.status_message_id, f"更新失败: {e}")

    def _auto_clean_invalid(self, sender, data):
        m = self._get_manager()
        try:
            stats = m.clean_path(remove_invalid=True, remove_duplicates=False, remove_empty=True)
            msg = f"清理完成！已移除 {stats['removed_invalid']} 个失效路径，{stats['removed_empty']} 个空路径条目。"
            dpg.set_value(self.status_message_id, msg)
            self.refresh()
        except Exception as e:
            dpg.set_value(self.status_message_id, f"清理失败: {e}")

    def _auto_dedup(self, sender, data):
        m = self._get_manager()
        try:
            stats = m.clean_path(remove_invalid=False, remove_duplicates=True, remove_empty=True)
            msg = f"去重完成！已清理 {stats['removed_duplicate']} 个重复条目。"
            dpg.set_value(self.status_message_id, msg)
            self.refresh()
        except Exception as e:
            dpg.set_value(self.status_message_id, f"去重失败: {e}")
