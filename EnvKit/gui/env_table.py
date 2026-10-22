import os
import re
import ctypes
import dearpygui.dearpygui as dpg
from typing import Dict, List, Any, Optional

try:
    _RESIZE_CURSOR = ctypes.windll.user32.LoadCursorW(None, 32644) # IDC_SIZEWE (左右双向调节光标)
except Exception:
    _RESIZE_CURSOR = None
from core.env_manager import EnvManager
from core.analyzer import Analyzer
from core.backup import backup, restore
from utils.path_helper import get_backup_dir
from utils.win_utils import choose_file, choose_directory, open_in_explorer
from utils.path_check import normalize_path, analyze_paths, clean_path_entries
from gui.theme import (
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_MUTED,
    COLOR_PRIMARY, COLOR_EMPTY, create_button_theme, create_splitter_theme,
    get_table_row_selected_color
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
        self.count_badge_user = None
        self.count_badge_sys = None
        self.footer_count_id = None
        self.status_banner_id = None
        self.search_filter = ""
        self.vars_cache = {}
        
        # 详情面板状态与可拖拽分割条尺寸
        self.selected_key = None
        self.is_new_mode = False
        self.detail_container_id = None
        self.detail_title_id = None
        self.detail_scope_badge_id = None
        
        # PATH 专属状态
        self.path_entries = []
        self.detail_width = 420
        self.is_dragging = False
        self.left_pane_tag = 'env_left_pane'
        self.right_pane_tag = 'env_right_pane'
        self.splitter_tag = 'env_splitter_bar'

    def get_current_scope(self) -> str:
        return self.scope

    def refresh_vars(self):
        self.vars_cache = self.manager.list()
        self._render_rows()
        self._update_badges()
        
        # 如果当前未选中或选中的键已不存在，默认选中第一项或 PATH
        if not self.selected_key or self.selected_key not in self.vars_cache:
            for k in ['Path', 'PATH']:
                if k in self.vars_cache:
                    self.selected_key = k
                    break
            if not self.selected_key and self.vars_cache:
                self.selected_key = sorted(self.vars_cache.keys())[0]
                
        self._render_detail_panel()

    def _update_badges(self):
        # 统计数量
        u_count = len(EnvManager('user').list())
        s_count = len(EnvManager('system').list())
        if self.count_badge_user and dpg.does_item_exist(self.count_badge_user):
            dpg.set_value(self.count_badge_user, f"[{u_count}]")
        if self.count_badge_sys and dpg.does_item_exist(self.count_badge_sys):
            dpg.set_value(self.count_badge_sys, f"[{s_count}]")
        if self.footer_count_id and dpg.does_item_exist(self.footer_count_id):
            dpg.set_value(self.footer_count_id, f"{len(self.vars_cache)} 个变量")

    def _render_rows(self):
        if not self.table_id or not dpg.does_item_exist(self.table_id):
            return
            
        children = dpg.get_item_children(self.table_id, 1) or []
        for c in children:
            dpg.delete_item(c)

        flt = self.search_filter.lower().strip()
        row_idx = 0
        sel_color = get_table_row_selected_color()

        for k, v in sorted(self.vars_cache.items(), key=lambda x: x[0].upper()):
            if flt and (flt not in k.lower() and flt not in v.lower()):
                continue

            row_id = dpg.add_table_row(parent=self.table_id)
            is_sel = (k == self.selected_key and not self.is_new_mode)

            # 1. 变量名称（整行满格高亮选择，依靠单元格 padding 自然垂直居中）
            dpg.add_selectable(
                label=k,
                parent=row_id,
                span_columns=True,
                default_value=is_sel,
                callback=self._on_row_selected,
                user_data=k
            )

            # 2. 变量值概览
            is_path_var = (k.upper() == 'PATH')
            if is_path_var:
                parts_count = len([p for p in v.split(';') if p.strip()])
                disp_val = f"{parts_count} 个路径条目"
                val_color = COLOR_PRIMARY
            else:
                disp_val = v if len(v) <= 80 else v[:77] + "..."
                val_color = COLOR_MUTED

            dpg.add_text(disp_val, parent=row_id, color=val_color)

            # 3. 状态标签 (设计稿美学：常规 / 正常 / 提示 / 关键)
            badge_text = "正常"
            badge_color = COLOR_MUTED
            if is_path_var:
                entries = analyze_paths(v)
                invalids = sum(1 for e in entries if not e['exists'] and not e['is_empty'])
                dups = sum(1 for e in entries if e['duplicate'])
                if invalids > 0 or dups > 0:
                    badge_text = f"{invalids + dups} 项提示"
                    badge_color = COLOR_WARNING
                else:
                    badge_text = "正常"
                    badge_color = COLOR_SUCCESS
            elif k in CRITICAL_ENV_VARS:
                badge_text = "系统关键"
                badge_color = COLOR_PRIMARY
            elif '\\' in v or '/' in v:
                norm = normalize_path(v)
                if os.path.exists(norm):
                    badge_text = "单路径"
                    badge_color = COLOR_SUCCESS
                else:
                    badge_text = "路径失效"
                    badge_color = COLOR_DANGER
            elif not v:
                badge_text = "空值"
                badge_color = COLOR_DANGER

            dpg.add_text(badge_text, parent=row_id, color=badge_color)

            # 满格行背景着色：如果是当前选中行，直接以设计稿纯色填充全行单元格（无缝贴合、无内缩）
            if is_sel:
                dpg.set_table_row_color(self.table_id, row_idx, sel_color)
            else:
                dpg.unset_table_row_color(self.table_id, row_idx)
            row_idx += 1

    def _on_row_selected(self, sender, app_data, user_data):
        self.selected_key = user_data
        self.is_new_mode = False
        self._render_rows()
        self._render_detail_panel()

    def _switch_to_new_mode(self, sender=None, data=None):
        self.is_new_mode = True
        self.selected_key = None
        self._render_rows()
        self._render_detail_panel()

    def _render_detail_panel(self):
        """根据当前选中变量（普通变量 / PATH / 新建）动态构建右侧连续详情编辑区"""
        if not self.detail_container_id or not dpg.does_item_exist(self.detail_container_id):
            return

        children = dpg.get_item_children(self.detail_container_id, 1) or []
        for c in children:
            dpg.delete_item(c)

        btn_primary = create_button_theme((46, 95, 204), (36, 77, 176), (25, 60, 145), text_color=(255, 255, 255))
        btn_danger = create_button_theme((164, 68, 54), (190, 80, 65), (140, 55, 45), text_color=(255, 255, 255))
        btn_success = create_button_theme((16, 185, 129), (52, 211, 153), (5, 150, 105), text_color=(255, 255, 255))

        # -------------------------------------------------------------
        # 模式 1: 新建变量模式
        # -------------------------------------------------------------
        if self.is_new_mode:
            dpg.add_text("变量详情", parent=self.detail_container_id, color=COLOR_MUTED)
            dpg.add_text("新建环境变量", parent=self.detail_container_id, color=COLOR_PRIMARY)
            scope_str = "用户变量 (User)" if self.scope == 'user' else "系统变量 (System)"
            dpg.add_text(f"作用域: {scope_str}", parent=self.detail_container_id, color=COLOR_MUTED)
            dpg.add_separator(parent=self.detail_container_id)
            dpg.add_spacer(height=6, parent=self.detail_container_id)

            dpg.add_text("变量名称:", parent=self.detail_container_id)
            dpg.add_input_text(tag="detail_new_key", hint="如 MY_PROJECT_ROOT", width=-1, parent=self.detail_container_id)
            dpg.add_spacer(height=4, parent=self.detail_container_id)

            dpg.add_text("变量值:", parent=self.detail_container_id)
            dpg.add_input_text(tag="detail_new_val", hint="输入值或路径...", multiline=True, height=120, width=-1, parent=self.detail_container_id)
            dpg.add_spacer(height=10, parent=self.detail_container_id)

            with dpg.group(horizontal=True, parent=self.detail_container_id):
                b_save = dpg.add_button(label="[保存] 立即创建变量", callback=self._do_create_new)
                dpg.bind_item_theme(b_save, btn_primary)
                dpg.add_button(label="取消", callback=lambda s, d: self._cancel_new_mode())
            return

        # -------------------------------------------------------------
        # 模式 2: 未选中任何变量
        # -------------------------------------------------------------
        if not self.selected_key or self.selected_key not in self.vars_cache:
            dpg.add_text("变量详情", parent=self.detail_container_id, color=COLOR_MUTED)
            dpg.add_text("未选择变量", parent=self.detail_container_id)
            dpg.add_text("在左侧列表中点击任意行即可在此连续编辑，或点击“+ 新建变量”。", parent=self.detail_container_id, color=COLOR_MUTED, wrap=340)
            return

        k = self.selected_key
        v = self.vars_cache.get(k, "")
        is_path = (k.upper() == 'PATH')

        # 头部面包屑与大变量名
        dpg.add_text("变量详情", parent=self.detail_container_id, color=COLOR_MUTED)
        with dpg.group(horizontal=True, parent=self.detail_container_id):
            dpg.add_text(k, color=COLOR_PRIMARY)
            dpg.add_spacer(width=6)
            scope_tag = "[用户变量]" if self.scope == 'user' else "[系统变量]"
            dpg.add_text(scope_tag, color=COLOR_MUTED)

        # -------------------------------------------------------------
        # 模式 3: PATH 变量的专属详情与排序视图 (设计稿核心体验)
        # -------------------------------------------------------------
        if is_path:
            dpg.add_text("按顺序查找可执行文件。越靠上的路径，优先级越高。", parent=self.detail_container_id, color=COLOR_MUTED, wrap=350)
            dpg.add_separator(parent=self.detail_container_id)
            dpg.add_spacer(height=4, parent=self.detail_container_id)

            self.path_entries = analyze_paths(v)
            invalids = [e for e in self.path_entries if not e['exists'] and not e['is_empty']]
            dups = [e for e in self.path_entries if e['duplicate']]
            
            with dpg.group(horizontal=True, parent=self.detail_container_id):
                dpg.add_text("路径条目", color=COLOR_PRIMARY)
                dpg.add_text(f"({len(self.path_entries)} 项)", color=COLOR_MUTED)

            if invalids or dups:
                warn_msg = f"[!] {len(invalids)} 个路径不可用，{len(dups)} 个重复"
                dpg.add_text(warn_msg, parent=self.detail_container_id, color=COLOR_WARNING)
            else:
                dpg.add_text("[√] 所有 PATH 条目均有效且无重复", parent=self.detail_container_id, color=COLOR_SUCCESS)

            dpg.add_spacer(height=4, parent=self.detail_container_id)

            # 条目滚屏列表容器 (占满详情区绝大部分垂直空间，底部固定保留操作条)
            with dpg.child_window(height=-85, border=True, no_scrollbar=False, parent=self.detail_container_id):
                for idx, entry in enumerate(self.path_entries):
                    p_raw = entry['raw']
                    with dpg.group(horizontal=True):
                        idx_str = f"{idx + 1:02d}"
                        dpg.add_text(idx_str, color=COLOR_MUTED)
                        
                        # 状态提示
                        stat_color = COLOR_MUTED
                        stat_tip = ""
                        if not entry['exists'] and not entry['is_empty']:
                            stat_color = COLOR_DANGER
                            stat_tip = " (不存在)"
                        elif entry['duplicate']:
                            stat_color = COLOR_WARNING
                            stat_tip = " (重复)"

                        dpg.add_text(f"{p_raw}{stat_tip}", color=stat_color, wrap=260)

                    with dpg.group(horizontal=True):
                        dpg.add_button(label="▲", callback=self._move_path_entry, user_data=(idx, -1), width=24)
                        dpg.add_button(label="▼", callback=self._move_path_entry, user_data=(idx, 1), width=24)
                        dpg.add_button(label="置顶", callback=self._top_path_entry, user_data=idx)
                        dpg.add_button(label="删除", callback=self._del_path_entry, user_data=idx)
                        if entry['exists']:
                            dpg.add_button(label="打开", callback=lambda s, d, u: open_in_explorer(u), user_data=normalize_path(p_raw))

                    dpg.add_separator()

            dpg.add_spacer(height=4, parent=self.detail_container_id)

            # PATH 操作组：固定停靠在变量详情区域的最底部
            with dpg.group(parent=self.detail_container_id):
                with dpg.group(horizontal=True):
                    dpg.add_input_text(tag="detail_path_add_input", hint="输入目录路径以添加新条目...", width=-140)
                    dpg.add_button(label="浏览...", callback=self._browse_path_folder)
                    b_add = dpg.add_button(label="[+] 添加", callback=self._add_path_entry)
                    dpg.bind_item_theme(b_add, btn_primary)

                dpg.add_spacer(height=3)
                with dpg.group(horizontal=True):
                    b_clean = dpg.add_button(label="一键清理无效与重复", callback=self._clean_path_oneclick)
                    dpg.bind_item_theme(b_clean, btn_danger)
                    
                    b_apply = dpg.add_button(label="保存并广播生效", callback=self._save_path_to_system)
                    dpg.bind_item_theme(b_apply, btn_success)

        # -------------------------------------------------------------
        # 模式 4: 普通环境变量的详情与编辑视图
        # -------------------------------------------------------------
        else:
            dpg.add_separator(parent=self.detail_container_id)
            dpg.add_spacer(height=6, parent=self.detail_container_id)

            dpg.add_text("变量名称:", parent=self.detail_container_id)
            dpg.add_input_text(tag="detail_edit_key", default_value=k, width=-1, parent=self.detail_container_id)
            dpg.add_spacer(height=6, parent=self.detail_container_id)

            dpg.add_text("变量值:", parent=self.detail_container_id)
            dpg.add_input_text(tag="detail_edit_val", default_value=v, multiline=True, height=140, width=-1, parent=self.detail_container_id)
            dpg.add_spacer(height=6, parent=self.detail_container_id)

            # 属性与有效性检测
            badge_desc = "普通文本值"
            badge_c = COLOR_MUTED
            if k in CRITICAL_ENV_VARS:
                badge_desc = "属于 Windows 系统关键运行变量，请谨慎修改"
                badge_c = COLOR_WARNING
            elif '\\' in v or '/' in v:
                norm = normalize_path(v)
                if os.path.exists(norm):
                    badge_desc = f"[√] 路径有效且存在: {norm}"
                    badge_c = COLOR_SUCCESS
                else:
                    badge_desc = f"[×] 目标路径在磁盘中不存在: {norm}"
                    badge_c = COLOR_DANGER
            elif re.search(r'%[^%]+%', v):
                badge_desc = "包含嵌套环境变量引用，Windows 动态展开"
                badge_c = COLOR_PRIMARY

            dpg.add_text(badge_desc, parent=self.detail_container_id, color=badge_c, wrap=340)
            dpg.add_spacer(height=12, parent=self.detail_container_id)

            # 动作按钮
            with dpg.group(horizontal=True, parent=self.detail_container_id):
                b_save = dpg.add_button(label="[保存] 更新变量", callback=self._save_regular_var)
                dpg.bind_item_theme(b_save, btn_primary)

                b_del = dpg.add_button(label="[删除] 删除变量", callback=self._request_delete)
                dpg.bind_item_theme(b_del, btn_danger)

                if self.on_send_to_diagnose:
                    dpg.add_button(label="[AI] 深入分析", callback=self._send_selected_to_diagnose)

    def _cancel_new_mode(self):
        self.is_new_mode = False
        self._render_detail_panel()

    def _do_create_new(self, sender, data):
        k = dpg.get_value("detail_new_key").strip()
        v = dpg.get_value("detail_new_val")
        if not k:
            self._set_banner("错误：变量名称不能为空！", is_error=True)
            return
        try:
            self.manager.set(k, v)
            self.selected_key = k
            self.is_new_mode = False
            self.refresh_vars()
            self._set_banner(f"成功创建环境变量 [{k}]！")
        except PermissionError:
            self._set_banner("权限不足：修改系统变量需以管理员身份运行！", is_error=True)
        except Exception as e:
            self._set_banner(f"创建失败: {e}", is_error=True)

    def _save_regular_var(self, sender, data):
        new_k = dpg.get_value("detail_edit_key").strip()
        new_v = dpg.get_value("detail_edit_val")
        old_k = self.selected_key

        if not new_k:
            self._set_banner("错误：变量名称不能为空！", is_error=True)
            return

        try:
            # 如果改名，先删旧后写新
            if old_k and old_k != new_k:
                self.manager.delete(old_k)
            self.manager.set(new_k, new_v)
            self.selected_key = new_k
            self.refresh_vars()
            self._set_banner(f"成功保存环境变量 [{new_k}]！")
        except PermissionError:
            self._set_banner("权限不足：修改系统变量需以管理员身份运行！", is_error=True)
        except Exception as e:
            self._set_banner(f"保存失败: {e}", is_error=True)

    def _request_delete(self, sender, data):
        k = self.selected_key
        if not k:
            return
        self.pending_delete_name = k
        text = f"您确定要永久删除 [{self.scope}] 作用域下的环境变量 [{k}] 吗？\n删除前系统已自动生成备份快照。"
        dpg.set_value('modal_delete_env_text', text)
        dpg.configure_item('modal_delete_env_confirm', show=True)

    def _do_delete_confirmed(self, sender, data):
        k = self.pending_delete_name
        dpg.configure_item('modal_delete_env_confirm', show=False)
        if not k:
            return
        try:
            # 自动预先备份
            backup(self.vars_cache, {}, category='env', meta={'action': 'delete', 'key': k})
            self.manager.delete(k)
            self.selected_key = None
            self.refresh_vars()
            self._set_banner(f"已成功删除环境变量 [{k}]！")
        except PermissionError:
            self._set_banner("权限不足：删除系统变量需以管理员身份运行！", is_error=True)
        except Exception as e:
            self._set_banner(f"删除失败: {e}", is_error=True)
        finally:
            self.pending_delete_name = None

    def _browse_path_folder(self, sender, data):
        folder = choose_directory(title="选择要添加到 PATH 的目录")
        if folder:
            dpg.set_value("detail_path_add_input", folder)

    def _add_path_entry(self, sender, data):
        p = dpg.get_value("detail_path_add_input").strip()
        if not p:
            return
        cur_v = self.vars_cache.get(self.selected_key, "")
        parts = [e for e in cur_v.split(';') if e.strip()]
        parts.append(p)
        try:
            self.manager.update_path_entries(parts)
            dpg.set_value("detail_path_add_input", "")
            self.refresh_vars()
            self._set_banner(f"已向 PATH 追加路径: {p}")
        except Exception as e:
            self._set_banner(f"写入失败: {e}", is_error=True)

    def _move_path_entry(self, sender, app_data, user_data):
        idx, delta = user_data
        new_idx = idx + delta
        if 0 <= new_idx < len(self.path_entries):
            self.path_entries[idx], self.path_entries[new_idx] = self.path_entries[new_idx], self.path_entries[idx]
            raws = [e['raw'] for e in self.path_entries if e['raw'].strip()]
            self.manager.update_path_entries(raws)
            self.refresh_vars()

    def _top_path_entry(self, sender, app_data, user_data):
        idx = user_data
        if idx > 0:
            item = self.path_entries.pop(idx)
            self.path_entries.insert(0, item)
            raws = [e['raw'] for e in self.path_entries if e['raw'].strip()]
            self.manager.update_path_entries(raws)
            self.refresh_vars()

    def _del_path_entry(self, sender, app_data, user_data):
        idx = user_data
        if 0 <= idx < len(self.path_entries):
            removed = self.path_entries.pop(idx)
            raws = [e['raw'] for e in self.path_entries if e['raw'].strip()]
            self.manager.update_path_entries(raws)
            self.refresh_vars()
            self._set_banner(f"已从 PATH 移除: {removed['raw']}")

    def _clean_path_oneclick(self, sender, data):
        try:
            stats = self.manager.clean_path(remove_invalid=True, remove_duplicates=True, remove_empty=True)
            msg = f"PATH 深度整理完毕：清理了 {stats['removed_invalid']} 处失效路径，{stats['removed_duplicate']} 处重复项。"
            self.refresh_vars()
            self._set_banner(msg)
        except Exception as e:
            self._set_banner(f"清理失败: {e}", is_error=True)

    def _save_path_to_system(self, sender, data):
        raws = [e['raw'] for e in self.path_entries if e['raw'].strip()]
        try:
            self.manager.update_path_entries(raws)
            self.refresh_vars()
            self._set_banner("PATH 已成功保存并广播至 Windows 系统全局！")
        except Exception as e:
            self._set_banner(f"广播保存失败: {e}", is_error=True)

    def _backup_all(self, sender, data):
        path = backup(self.vars_cache, {}, category='env', meta={'scope': self.scope})
        self._set_banner(f"环境变量快照已导出至: {path}")

    def _restore_from_backup(self, sender, data):
        initial_dir = str(get_backup_dir())
        chosen = choose_file(
            initial_dir=initial_dir,
            file_types=[("EnvKit 快照备份 (*.json)", "*.json"), ("所有文件", "*.*")],
            title="选择要还原的环境变量快照文件"
        )
        if not chosen:
            return
        try:
            data = restore(chosen)
            env_map = data.get('env', {})
            if not env_map:
                self._set_banner("备份文件中未找到有效的环境变量数据！", is_error=True)
                return
            for k, v in env_map.items():
                self.manager.set(k, v)
            self.refresh_vars()
            self._set_banner(f"成功从快照恢复了 {len(env_map)} 项环境变量！")
        except Exception as e:
            self._set_banner(f"恢复失败: {e}", is_error=True)

    def _send_selected_to_diagnose(self, sender, data):
        k = self.selected_key
        v = self.vars_cache.get(k, "")
        if k and self.on_send_to_diagnose:
            self.on_send_to_diagnose([{'kind': 'env', 'scope': self.scope, 'key': k, 'value': v}])

    def _set_banner(self, msg: str, is_error: bool = False):
        if self.status_banner_id and dpg.does_item_exist(self.status_banner_id):
            dpg.set_value(self.status_banner_id, msg)
            dpg.configure_item(self.status_banner_id, color=COLOR_DANGER if is_error else COLOR_SUCCESS)

    def build(self):
        btn_primary = create_button_theme((46, 95, 204), (36, 77, 176), (25, 60, 145), text_color=(255, 255, 255))
        btn_danger = create_button_theme((164, 68, 54), (190, 80, 65), (140, 55, 45), text_color=(255, 255, 255))

        # 删除确认弹窗
        with dpg.window(modal=True, show=False, tag='modal_delete_env_confirm', no_move=True, no_resize=True, width=440, height=210):
            dpg.add_text("[提示] 确认删除环境变量？", color=COLOR_WARNING)
            dpg.add_separator()
            dpg.add_text(tag='modal_delete_env_text', wrap=410)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                b_del_yes = dpg.add_button(label="确认永久删除", callback=self._do_delete_confirmed)
                dpg.bind_item_theme(b_del_yes, btn_danger)
                dpg.add_button(label="取消", callback=lambda s, d: dpg.configure_item('modal_delete_env_confirm', show=False))

        splitter_theme = create_splitter_theme()

        # =============================================================
        # 双栏现代化架构：左侧主工作区 (Table)，中间拖拽分割条，右侧连续详情区 (Details)
        # =============================================================
        with dpg.group(horizontal=True):
            # ---------------------------------------------------------
            # 1. 中部主工作区 (Middle Content Workspace) - 动态自适应宽度
            # ---------------------------------------------------------
            with dpg.child_window(tag=self.left_pane_tag, width=-self.detail_width - 12, height=-1, border=True, no_scrollbar=True):
                # 面包屑与大标题 (设计稿一致)
                dpg.add_text("工作区 > 环境变量", color=COLOR_MUTED)
                dpg.add_spacer(height=2)
                dpg.add_text("环境变量", color=COLOR_PRIMARY)
                dpg.add_text("查看变量、整理路径，让每个开发环境都有据可循。", color=COLOR_MUTED)
                dpg.add_spacer(height=8)

                # 工具栏 1: 搜索与核心动作
                with dpg.group(horizontal=True):
                    dpg.add_input_text(hint="搜索变量名称或值... (Ctrl K)", callback=self._on_search_change, width=280)
                    
                    b_new = dpg.add_button(label="[+] 新建变量", callback=self._switch_to_new_mode)
                    dpg.bind_item_theme(b_new, btn_primary)

                    dpg.add_button(label="[导出] 快照", callback=self._backup_all)
                    dpg.add_button(label="[导入] 还原", callback=self._restore_from_backup)

                dpg.add_spacer(height=6)

                # 作用域选项卡 (设计稿标签页风格)
                with dpg.group(horizontal=True):
                    b_user = dpg.add_button(label="用户变量", callback=lambda s, d: self._switch_scope('user'))
                    self.count_badge_user = dpg.add_text("[0]", color=COLOR_PRIMARY)
                    dpg.add_spacer(width=15)
                    
                    b_sys = dpg.add_button(label="系统变量", callback=lambda s, d: self._switch_scope('system'))
                    self.count_badge_sys = dpg.add_text("[0]", color=COLOR_MUTED)

                dpg.add_separator()
                dpg.add_spacer(height=4)

                # 变量列表表格：直接设置 scrollY=True, height=-42，去除纵向分割线，保证整行无缝纯色高亮
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
                col_name = dpg.add_table_column(label="变量名称", width_stretch=True, init_width_or_weight=200, parent=self.table_id)
                col_val = dpg.add_table_column(label="值 / 路径条目", width_stretch=True, init_width_or_weight=420, parent=self.table_id)
                col_status = dpg.add_table_column(label="状态", width_fixed=True, init_width_or_weight=110, parent=self.table_id)

                for col in (col_name, col_val, col_status):
                    if dpg.does_item_exist('font_header'):
                        dpg.bind_item_font(col, 'font_header')

                dpg.add_spacer(height=4)

                # 底部信息条与状态横幅
                with dpg.group(horizontal=True):
                    self.footer_count_id = dpg.add_text("0 个变量", color=COLOR_MUTED)
                    dpg.add_button(label="刷新", callback=lambda s, d: self.refresh_vars())
                    dpg.add_spacer(width=20)
                    self.status_banner_id = dpg.add_text("当前没有待应用的更改，修改将先在此预览并生成快照。", color=COLOR_MUTED)

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
        if not dpg.does_item_exist('env_splitter_handler_reg'):
            with dpg.handler_registry(tag='env_splitter_handler_reg'):
                dpg.add_mouse_move_handler(callback=self._on_mouse_move)
                dpg.add_mouse_drag_handler(button=0, threshold=0.0, callback=self._on_mouse_drag)
                dpg.add_mouse_release_handler(button=0, callback=self._on_mouse_release)

        self.refresh_vars()

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

    def _switch_scope(self, scope_str: str):
        self.scope = scope_str
        self.manager = EnvManager(self.scope)
        self.selected_key = None
        self.is_new_mode = False
        self.refresh_vars()

    def _on_search_change(self, sender, data):
        self.search_filter = data
        self._render_rows()
