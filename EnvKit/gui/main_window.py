import sys
import platform
from pathlib import Path
import dearpygui.dearpygui as dpg

from core.analyzer import Analyzer
from core.skill_manager import SkillManager
from utils.path_helper import get_model_config_path, get_backup_dir
from utils.win_utils import is_admin, restart_as_admin, open_in_explorer
from utils.perf_utils import get_process_memory_mb

from gui.env_table import EnvUI
from gui.path_view import PathViewUI
from gui.reg_table import RegUI
from gui.backup_view import BackupViewUI
from gui.skills_view import SkillsViewUI
from gui.diagnosis_panel import DiagnosisUI
from gui.config_panel import ConfigUI
from gui.theme import (
    setup_global_theme, toggle_global_theme, get_current_theme_mode,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_PRIMARY, COLOR_MUTED, create_button_theme
)

# 侧边栏导航定义（严格对齐设计稿结构与功能体系）
NAV_CONFIG_SECTION = [
    ('nav_env', 'view_env', '环境变量'),
    ('nav_reg', 'view_reg', '注册表'),
    ('nav_backup', 'view_backup', '快照与备份'),
    ('nav_skills', 'view_skills', '本地技能箱'),
]

NAV_WORKFLOW_SECTION = [
    ('nav_diag', 'view_diag', 'AI 智能诊断'),
    ('nav_path', 'view_path', 'PATH 治理'),
    ('nav_cfg', 'view_cfg', '设置与模型'),
]

ALL_NAV = NAV_CONFIG_SECTION + NAV_WORKFLOW_SECTION
NAV_VIEWS = ALL_NAV # 供测试向后兼容

def build_ui():
    config_path = get_model_config_path()
    analyzer = Analyzer(str(config_path))
    skill_manager = SkillManager()
    setup_global_theme()

    # 预建设计稿色系导航按钮主题
    nav_active_dark = create_button_theme((41, 62, 102), (86, 135, 240), (60, 105, 210), text_color=(226, 233, 246))
    nav_inactive_dark = create_button_theme((23, 29, 42), (32, 43, 62), (23, 29, 42), text_color=(166, 181, 207))
    
    nav_active_light = create_button_theme((229, 237, 252), (215, 226, 248), (198, 215, 245), text_color=(46, 95, 204))
    nav_inactive_light = create_button_theme((240, 243, 249), (229, 237, 252), (215, 226, 248), text_color=(94, 110, 134))
    
    btn_admin = create_button_theme((145, 96, 31), (180, 120, 40), (120, 80, 25), text_color=(255, 255, 255))
    current_active_nav = ['nav_env']

    diag_ui = None
    env_ui = None
    reg_ui = None
    backup_ui = None

    def _get_nav_themes():
        is_dark = (get_current_theme_mode() == 'dark')
        return (nav_active_dark if is_dark else nav_active_light,
                nav_inactive_dark if is_dark else nav_inactive_light)

    def _update_nav_themes():
        act_theme, inact_theme = _get_nav_themes()
        for nav_id, _, _ in ALL_NAV:
            if dpg.does_item_exist(nav_id):
                dpg.bind_item_theme(nav_id, act_theme if nav_id == current_active_nav[0] else inact_theme)

    def _switch_view(target_nav_id, target_view_id):
        current_active_nav[0] = target_nav_id
        for nav_id, view_id, _ in ALL_NAV:
            if dpg.does_item_exist(view_id):
                dpg.configure_item(view_id, show=(view_id == target_view_id))
        _update_nav_themes()

    def _jump_to_diagnose(items):
        _switch_view('nav_diag', 'view_diag')
        if diag_ui:
            diag_ui.set_items_to_diagnose(items)

    def _jump_to_env(key_name):
        _switch_view('nav_env', 'view_env')
        if env_ui:
            env_ui.selected_key = key_name
            env_ui.is_new_mode = False
            env_ui.refresh_vars()

    def _on_toggle_theme(sender, data):
        new_mode = toggle_global_theme()
        lbl = "切换为浅色模式" if new_mode == 'dark' else "切换为深色模式"
        dpg.set_item_label('btn_theme_toggle', lbl)
        _update_nav_themes()

    # 顶层主窗口
    with dpg.window(tag='EnvKit', no_move=True, no_resize=True, no_close=True):
        with dpg.group(horizontal=True):
            # ==========================================
            # 1. 左侧导航侧边栏 (Sidebar - 宽度 228，设计稿严格一致)
            # ==========================================
            with dpg.child_window(width=228, height=-1, border=True):
                # 顶部品牌 Logo 与应用副标 (设计稿一致)
                with dpg.group(horizontal=True):
                    dpg.add_text("[envkit]", color=COLOR_PRIMARY)
                    dpg.add_text("本地环境工作台", color=COLOR_MUTED)

                dpg.add_spacer(height=6)

                # 本机工作区卡片 (设计稿一致)
                win_ver = "Windows 11" if "11" in platform.version() or "10.0.2" in platform.version() else "Windows 10"
                with dpg.child_window(height=58, border=True):
                    dpg.add_text("本机工作区", color=COLOR_PRIMARY)
                    dpg.add_text(f"{win_ver} / 64-bit", color=COLOR_MUTED)

                dpg.add_spacer(height=8)

                act_theme, inact_theme = _get_nav_themes()

                # 分组 1: 配置管理
                dpg.add_text("配置管理", color=COLOR_MUTED)
                dpg.add_spacer(height=2)
                for nav_id, view_id, label in NAV_CONFIG_SECTION:
                    btn = dpg.add_button(
                        tag=nav_id,
                        label=f"  {label}",
                        width=-1,
                        height=36,
                        callback=lambda s, d, u: _switch_view(u[0], u[1]),
                        user_data=(nav_id, view_id)
                    )
                    dpg.bind_item_theme(btn, act_theme if nav_id == 'nav_env' else inact_theme)
                    dpg.add_spacer(height=2)

                dpg.add_spacer(height=6)
                dpg.add_separator()
                dpg.add_spacer(height=6)

                # 分组 2: 工作流与分析
                dpg.add_text("工作流与分析", color=COLOR_MUTED)
                dpg.add_spacer(height=2)
                for nav_id, view_id, label in NAV_WORKFLOW_SECTION:
                    btn = dpg.add_button(
                        tag=nav_id,
                        label=f"  {label}",
                        width=-1,
                        height=36,
                        callback=lambda s, d, u: _switch_view(u[0], u[1]),
                        user_data=(nav_id, view_id)
                    )
                    dpg.bind_item_theme(btn, inact_theme)
                    dpg.add_spacer(height=2)

                dpg.add_spacer(height=14)
                dpg.add_separator()
                dpg.add_spacer(height=6)

                # 侧栏底部：设计稿“先预览，再应用”理念卡片与系统状态
                with dpg.group():
                    with dpg.child_window(height=82, border=True):
                        dpg.add_text("先预览，再应用", color=COLOR_PRIMARY)
                        dpg.add_text("修改前生成快照，每一次更改都可追溯、可回滚。", color=COLOR_MUTED, wrap=190)

                    dpg.add_spacer(height=6)

                    # 主题切换按钮
                    cur_mode = get_current_theme_mode()
                    theme_lbl = "切换为浅色模式" if cur_mode == 'dark' else "切换为深色模式"
                    dpg.add_button(
                        tag='btn_theme_toggle',
                        label=theme_lbl,
                        width=-1,
                        height=30,
                        callback=_on_toggle_theme
                    )

                    dpg.add_spacer(height=4)
                    ram_mb = get_process_memory_mb()
                    dpg.add_text(f"内存占用: ~{ram_mb} MB", color=COLOR_SUCCESS)

                    has_admin = is_admin()
                    if has_admin:
                        dpg.add_text("● 管理员权限模式", color=COLOR_SUCCESS)
                    else:
                        dpg.add_text("○ 普通用户权限", color=COLOR_WARNING)
                        b_uac = dpg.add_button(
                            label="提权运行",
                            width=-1,
                            callback=lambda s, d: restart_as_admin()
                        )
                        dpg.bind_item_theme(b_uac, btn_admin)

            # ==========================================
            # 2. 右侧主工作区呈现容器
            # ==========================================
            with dpg.child_window(width=-1, height=-1, border=False, tag='content_area'):
                # 1. 环境变量视图 (双栏：表格 + 详情栏)
                with dpg.group(tag='view_env', show=True):
                    env_ui = EnvUI(analyzer, on_send_to_diagnose=_jump_to_diagnose)
                    env_ui.build()

                # 2. 注册表视图 (双栏：键值表格 + 详情栏)
                with dpg.group(tag='view_reg', show=False):
                    reg_ui = RegUI(analyzer, on_send_to_diagnose=_jump_to_diagnose, on_jump_to_env=_jump_to_env)
                    reg_ui.build()

                # 3. 快照与备份视图
                with dpg.group(tag='view_backup', show=False):
                    backup_ui = BackupViewUI(on_restore_callback=lambda: env_ui.refresh_vars() if env_ui else None)
                    backup_ui.build()

                # 4. PATH 治理全屏视图
                with dpg.group(tag='view_path', show=False):
                    path_ui = PathViewUI(get_scope_callback=env_ui.get_current_scope)
                    path_ui.build()

                # 5. 本地技能箱视图
                with dpg.group(tag='view_skills', show=False):
                    skills_ui = SkillsViewUI(skill_manager)
                    skills_ui.build()

                # 6. AI 智能诊断视图
                with dpg.group(tag='view_diag', show=False):
                    diag_ui = DiagnosisUI(analyzer)
                    diag_ui.build()

                # 7. 设置与模型视图
                with dpg.group(tag='view_cfg', show=False):
                    config_ui = ConfigUI(analyzer)
                    config_ui.build()
