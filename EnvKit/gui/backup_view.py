import os
import json
import time
from pathlib import Path
import dearpygui.dearpygui as dpg

from core.backup import backup, restore
from core.env_manager import EnvManager
from utils.path_helper import get_backup_dir
from utils.win_utils import open_in_explorer
from gui.theme import (
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_MUTED,
    COLOR_PRIMARY, create_button_theme
)

class BackupViewUI:
    def __init__(self, on_restore_callback=None):
        self.on_restore_callback = on_restore_callback
        self.table_id = None
        self.preview_text_id = None
        self.status_text_id = None
        self.selected_file = None

    def refresh(self):
        if not self.table_id or not dpg.does_item_exist(self.table_id):
            return
            
        children = dpg.get_item_children(self.table_id, 1) or []
        for c in children:
            dpg.delete_item(c)

        backup_dir = get_backup_dir()
        if not backup_dir.exists():
            return

        files = sorted(backup_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
        
        btn_restore = create_button_theme((46, 95, 204), (36, 77, 176), (25, 60, 145), text_color=(255, 255, 255))
        btn_danger = create_button_theme((164, 68, 54), (190, 80, 65), (140, 55, 45), text_color=(255, 255, 255))

        for f in files:
            stat = f.stat()
            mtime_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
            size_kb = max(1, stat.st_size // 1024)
            
            category = "通用快照"
            cat_color = COLOR_MUTED
            if "env" in f.name.lower():
                category = "环境变量"
                cat_color = COLOR_PRIMARY
            elif "reg" in f.name.lower():
                category = "注册表"
                cat_color = COLOR_WARNING

            row_id = dpg.add_table_row(parent=self.table_id)
            
            # 1. 时间戳与选中高亮 (行高 34px 全覆盖)
            dpg.add_selectable(
                label=mtime_str,
                parent=row_id,
                span_columns=True,
                height=34,
                callback=self._on_select_snapshot,
                user_data=str(f)
            )

            # 2. 类别 (垂直居中)
            with dpg.group(parent=row_id):
                dpg.add_spacer(height=3)
                dpg.add_text(category, color=cat_color)

            # 3. 文件名 (垂直居中)
            with dpg.group(parent=row_id):
                dpg.add_spacer(height=3)
                dpg.add_text(f.name)

            # 4. 文件大小 (垂直居中)
            with dpg.group(parent=row_id):
                dpg.add_spacer(height=3)
                dpg.add_text(f"{size_kb} KB", color=COLOR_MUTED)

            # 5. 操作组 (垂直居中)
            with dpg.group(parent=row_id):
                dpg.add_spacer(height=1)
                actions_grp = dpg.add_group(horizontal=True)
                b_res = dpg.add_button(
                    label="恢复",
                    parent=actions_grp,
                    callback=self._do_restore,
                    user_data=str(f)
                )
                dpg.bind_item_theme(b_res, btn_restore)

                dpg.add_button(
                    label="定位",
                    parent=actions_grp,
                    callback=lambda s, d, u: open_in_explorer(u),
                    user_data=str(f)
                )

                b_del = dpg.add_button(
                    label="删除",
                    parent=actions_grp,
                    callback=self._do_delete,
                    user_data=str(f)
                )
                dpg.bind_item_theme(b_del, btn_danger)

    def _on_select_snapshot(self, sender, app_data, user_data):
        file_path = user_data
        self.selected_file = file_path
        try:
            with open(file_path, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            pretty = json.dumps(data, ensure_ascii=False, indent=2)
            if self.preview_text_id and dpg.does_item_exist(self.preview_text_id):
                dpg.set_value(self.preview_text_id, pretty)
            if self.status_text_id and dpg.does_item_exist(self.status_text_id):
                dpg.set_value(self.status_text_id, f"已载入快照预览: {Path(file_path).name}")
        except Exception as e:
            if self.preview_text_id and dpg.does_item_exist(self.preview_text_id):
                dpg.set_value(self.preview_text_id, f"读取失败: {e}")

    def _do_restore(self, sender, app_data, user_data):
        file_path = user_data
        try:
            data = restore(file_path)
            env_map = data.get('env', {})
            reg_map = data.get('reg', {})
            
            restored_env = 0
            if env_map:
                u_mgr = EnvManager('user')
                for k, v in env_map.items():
                    u_mgr.set(k, v)
                    restored_env += 1

            if self.status_text_id and dpg.does_item_exist(self.status_text_id):
                dpg.set_value(self.status_text_id, f"成功还原快照！恢复了 {restored_env} 项环境变量数据。")

            if self.on_restore_callback:
                self.on_restore_callback()
        except Exception as e:
            if self.status_text_id and dpg.does_item_exist(self.status_text_id):
                dpg.set_value(self.status_text_id, f"恢复失败: {e}")

    def _do_delete(self, sender, app_data, user_data):
        file_path = user_data
        try:
            os.remove(file_path)
            if self.status_text_id and dpg.does_item_exist(self.status_text_id):
                dpg.set_value(self.status_text_id, f"已安全删除快照文件: {Path(file_path).name}")
            self.refresh()
            if self.preview_text_id and dpg.does_item_exist(self.preview_text_id):
                dpg.set_value(self.preview_text_id, "")
        except Exception as e:
            if self.status_text_id and dpg.does_item_exist(self.status_text_id):
                dpg.set_value(self.status_text_id, f"删除失败: {e}")

    def _create_env_backup(self, sender=None, data=None):
        u_mgr = EnvManager('user')
        vars_map = u_mgr.list()
        path = backup(vars_map, {}, category='env', meta={'trigger': 'ManualSnapshot'})
        if self.status_text_id and dpg.does_item_exist(self.status_text_id):
            dpg.set_value(self.status_text_id, f"快照创建成功: {Path(path).name}")
        self.refresh()

    def build(self):
        btn_primary = create_button_theme((46, 95, 204), (36, 77, 176), (25, 60, 145), text_color=(255, 255, 255))

        # 面包屑与大标题
        dpg.add_text("工作区 > 快照与备份", color=COLOR_MUTED)
        dpg.add_spacer(height=2)
        dpg.add_text("快照与备份", color=COLOR_PRIMARY)
        dpg.add_text("系统级修改前自动生成的安全快照，每一次更改都可追溯、可回滚。", color=COLOR_MUTED)
        dpg.add_spacer(height=8)

        # 工具栏
        with dpg.group(horizontal=True):
            b_create = dpg.add_button(label="[+] 立即生成环境快照", callback=self._create_env_backup)
            dpg.bind_item_theme(b_create, btn_primary)

            dpg.add_button(label="[目录] 打开备份文件夹", callback=lambda s, d: open_in_explorer(str(get_backup_dir())))
            dpg.add_button(label="刷新快照列表", callback=lambda s, d: self.refresh())

        dpg.add_spacer(height=6)

        # 左右双栏：左侧快照列表，右侧 JSON 内容检视 (自适应高度，无多余嵌套滚动条)
        with dpg.group(horizontal=True):
            with dpg.child_window(width=-450, height=-30, border=True, no_scrollbar=True):
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
                dpg.add_table_column(label="快照生成时间", width_stretch=True, init_width_or_weight=170, parent=self.table_id)
                dpg.add_table_column(label="类别", width_fixed=True, init_width_or_weight=90, parent=self.table_id)
                dpg.add_table_column(label="快照文件名", width_stretch=True, init_width_or_weight=220, parent=self.table_id)
                dpg.add_table_column(label="大小", width_fixed=True, init_width_or_weight=60, parent=self.table_id)
                dpg.add_table_column(label="操作管理", width_fixed=True, init_width_or_weight=160, parent=self.table_id)

            with dpg.child_window(width=-1, height=-30, border=True, no_scrollbar=True):
                dpg.add_text("快照详情预览", color=COLOR_PRIMARY)
                dpg.add_separator()
                self.preview_text_id = dpg.add_input_text(
                    multiline=True,
                    readonly=True,
                    width=-1,
                    height=-1,
                    default_value="点击左侧快照项即可在此预览快照 JSON 完整结构。"
                )

        dpg.add_spacer(height=4)
        self.status_text_id = dpg.add_text("就绪。快照在执行破坏性修改或一键清理前会自动生成。", color=COLOR_MUTED)
        self.refresh()
