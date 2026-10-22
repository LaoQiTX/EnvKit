import sys
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
from gui.skills_view import SkillsViewUI
from gui.diagnosis_panel import DiagnosisUI
from gui.config_panel import ConfigUI
from gui.theme import (
    setup_global_theme, toggle_global_theme, get_current_theme_mode,
    COLOR_SUCCESS, COLOR_WARNING, COLOR_PRIMARY, COLOR_MUTED, create_button_theme
)

NAV_VIEWS = [
    ('nav_env', 'view_env', '[环境] 环境变量'),
    ('nav_path', 'view_path', '[PATH] PATH 治理'),
    ('nav_reg', 'view_reg', '[注册表] 注册表管理'),
    ('nav_skills', 'view_skills', '[技能箱] 本地技能箱'),
    ('nav_diag', 'view_diag', '[AI] AI 智能诊断'),
    ('nav_cfg', 'view_cfg', '[设置] 设置与模型'),
]

def build_ui():
    config_path = get_model_config_path()
    analyzer = Analyzer(str(config_path))
    skill_manager = SkillManager()
    setup_global_theme()

    # 预建深浅色导航按钮主题
    nav_active_dark = create_button_theme((37, 99, 235), (59, 130, 246), (29, 78, 216), text_color=(255, 255, 255))
    nav_inactive_dark = create_button_theme((34, 38, 48), (45, 52, 68), (34, 38, 48), text_color=(220, 226, 235))
    
    nav_active_light = create_button_theme((37, 99, 235), (59, 130, 246), (29, 78, 216), text_color=(255, 255, 255))
    nav_inactive_light = create_button_theme((236, 240, 248), (220, 228, 240), (208, 218, 232), text_color=(35, 45, 60))
    
    btn_admin = create_button_theme((217, 119, 6), (245, 158, 11), (180, 83, 9))
    current_active_nav = ['nav_env']

    diag_ui = None
    skills_ui = None

    def _get_nav_themes():
        is_dark = (get_current_theme_mode() == 'dark')
        return (nav_active_dark if is_dark else nav_active_light,
                nav_inactive_dark if is_dark else nav_inactive_light)

    def _update_nav_themes():
        act_theme, inact_theme = _get_nav_themes()
        for nav_id, _, _ in NAV_VIEWS:
            if dpg.does_item_exist(nav_id):
                dpg.bind_item_theme(nav_id, act_theme if nav_id == current_active_nav[0] else inact_theme)

    def _switch_view(target_nav_id, target_view_id):
        current_active_nav[0] = target_nav_id
        for nav_id, view_id, _ in NAV_VIEWS:
            if dpg.does_item_exist(view_id):
                dpg.configure_item(view_id, show=(view_id == target_view_id))
        _update_nav_themes()

    def _on_toggle_theme(sender, data):
        new_mode = toggle_global_theme()
        lbl = "[主题] 切换为浅色模式" if new_mode == 'dark' else "[主题] 切换为深色模式"
        dpg.set_item_label('btn_theme_toggle', lbl)
        _update_nav_themes()

    def _jump_to_diagnose(items):
        _switch_view('nav_diag', 'view_diag')
        if diag_ui:
            diag_ui.set_items_to_diagnose(items)

    with dpg.window(tag='EnvKit', no_move=True, no_resize=True, no_close=True):
        with dpg.group(horizontal=True):
            # ==========================================
            # 左侧导航侧边栏 (Sidebar Navigation)
            # ==========================================
            with dpg.child_window(width=220, height=-1, border=True):
                # 品牌 Logo 与标题 (移除 emoji，无问号乱码)
                with dpg.group(horizontal=True):
                    dpg.add_text("EnvKit", color=COLOR_PRIMARY)
                    dpg.add_text("Pro", color=COLOR_SUCCESS)
                    
                dpg.add_text("轻量环境与注册表管理", color=COLOR_MUTED)
                dpg.add_separator()
                dpg.add_spacer(height=6)

                act_theme, inact_theme = _get_nav_themes()

                # 导航按钮
                for nav_id, view_id, label in NAV_VIEWS:
                    btn = dpg.add_button(
                        tag=nav_id,
                        label=f" {label}",
                        width=-1,
                        height=38,
                        callback=lambda s, d, u: _switch_view(u[0], u[1]),
                        user_data=(nav_id, view_id)
                    )
                    dpg.bind_item_theme(btn, act_theme if nav_id == 'nav_env' else inact_theme)
                    dpg.add_spacer(height=3)

                dpg.add_spacer(height=25)
                dpg.add_separator()

                # 主题切换与系统状态
                with dpg.group():
                    dpg.add_spacer(height=4)
                    
                    cur_mode = get_current_theme_mode()
                    theme_lbl = "[主题] 切换为浅色模式" if cur_mode == 'dark' else "[主题] 切换为深色模式"
                    dpg.add_button(
                        tag='btn_theme_toggle',
                        label=theme_lbl,
                        width=-1,
                        height=32,
                        callback=_on_toggle_theme
                    )

                    dpg.add_spacer(height=6)
                    ram_mb = get_process_memory_mb()
                    dpg.add_text(f"内存占用: ~{ram_mb} MB", color=(52, 211, 153, 255))
                    
                    has_admin = is_admin()
                    if has_admin:
                        dpg.add_text("● 管理员权限模式", color=COLOR_SUCCESS)
                    else:
                        dpg.add_text("○ 普通用户权限", color=COLOR_WARNING)
                        b_uac = dpg.add_button(
                            label="以管理员身份运行",
                            width=-1,
                            callback=lambda s, d: restart_as_admin()
                        )
                        dpg.bind_item_theme(b_uac, btn_admin)

                    dpg.add_spacer(height=4)
                    dpg.add_button(
                        label="[备份] 打开备份目录",
                        width=-1,
                        callback=lambda s, d: open_in_explorer(str(get_backup_dir()))
                    )

            # ==========================================
            # 右侧主内容展示区 (Main Content View)
            # ==========================================
            with dpg.child_window(width=-1, height=-1, border=True, tag='content_area'):
                # 1. 环境变量视图
                with dpg.group(tag='view_env', show=True):
                    env_ui = EnvUI(analyzer, on_send_to_diagnose=_jump_to_diagnose)
                    env_ui.build()

                # 2. PATH 治理视图
                with dpg.group(tag='view_path', show=False):
                    path_ui = PathViewUI(get_scope_callback=env_ui.get_current_scope)
                    path_ui.build()

                # 3. 注册表视图
                with dpg.group(tag='view_reg', show=False):
                    reg_ui = RegUI(analyzer, on_send_to_diagnose=_jump_to_diagnose)
                    reg_ui.build()

                # 4. 本地技能箱视图
                with dpg.group(tag='view_skills', show=False):
                    skills_ui = SkillsViewUI(skill_manager)
                    skills_ui.build()

                # 5. AI 智能诊断视图
                with dpg.group(tag='view_diag', show=False):
                    diag_ui = DiagnosisUI(analyzer)
                    diag_ui.build()

                # 6. 设置与模型视图
                with dpg.group(tag='view_cfg', show=False):
                    config_ui = ConfigUI(analyzer)
                    config_ui.build()
