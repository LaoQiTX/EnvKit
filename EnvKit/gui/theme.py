import json
import dearpygui.dearpygui as dpg
from pathlib import Path
from utils.path_helper import get_base_dir

# 常用语义色
COLOR_SUCCESS = (16, 185, 129, 255)
COLOR_DANGER = (239, 68, 68, 255)
COLOR_WARNING = (245, 158, 11, 255)
COLOR_EMPTY = (168, 85, 247, 255)
COLOR_MUTED = (156, 163, 175, 255)
COLOR_PRIMARY = (59, 130, 246, 255)
COLOR_WHITE = (243, 244, 246, 255)

# 主题状态存储
_CURRENT_THEME = "dark"
_GLOBAL_THEME_OBJECTS = {}

def _get_pref_file() -> Path:
    return get_base_dir() / "theme_pref.txt"

def load_theme_preference() -> str:
    pref_file = _get_pref_file()
    if pref_file.exists():
        try:
            val = pref_file.read_text(encoding='utf-8').strip().lower()
            if val in ('dark', 'light'):
                return val
        except Exception:
            pass
    return "dark"

def save_theme_preference(mode: str):
    try:
        _get_pref_file().write_text(mode, encoding='utf-8')
    except Exception:
        pass

def get_current_theme_mode() -> str:
    global _CURRENT_THEME
    return _CURRENT_THEME

def build_dark_theme():
    """现代极简暗黑模式 (Slate Dark)"""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            # 基础几何圆角与内边距 (适配 20 号字)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 9, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 6, 5)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)

            # 颜色方案
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (24, 26, 32))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (30, 33, 42))
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (34, 38, 48))
            dpg.add_theme_color(dpg.mvThemeCol_Border, (50, 56, 70))
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))
            
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (38, 43, 55))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (48, 54, 70))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (58, 65, 85))
            
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (32, 36, 46))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (28, 31, 40))
            
            # Tab 选项卡
            dpg.add_theme_color(dpg.mvThemeCol_Tab, (32, 36, 46))
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (59, 130, 246, 180))
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, (59, 130, 246))
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, (30, 34, 44))
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, (45, 52, 68))
            
            # 按钮默认样式
            dpg.add_theme_color(dpg.mvThemeCol_Button, (45, 52, 68))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (59, 130, 246))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (37, 99, 235))
            
            # 表格样式
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, (34, 38, 50))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, (26, 29, 37))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, (32, 36, 46))
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, (44, 50, 64))
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, (55, 62, 80))
            
            # 文字与高亮
            dpg.add_theme_color(dpg.mvThemeCol_Text, (240, 243, 246))
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (120, 126, 140))
            dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, (59, 130, 246, 120))
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (59, 130, 246))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (59, 130, 246))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (37, 99, 235))
            dpg.add_theme_color(dpg.mvThemeCol_Separator, (46, 52, 66))
            dpg.add_theme_color(dpg.mvThemeCol_Header, (45, 52, 68, 180))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (59, 130, 246, 200))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (37, 99, 235, 230))
    return theme

def build_light_theme():
    """现代纯净明亮模式 (macOS / Win11 Light)"""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            # 基础几何圆角与内边距 (适配 20 号字)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 9, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 6, 5)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)

            # 颜色方案
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (244, 246, 249))
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (255, 255, 255))
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (255, 255, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Border, (222, 226, 235))
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))
            
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (238, 242, 248))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (226, 232, 242))
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (214, 222, 236))
            
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (230, 235, 245))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (240, 243, 248))
            
            # Tab 选项卡
            dpg.add_theme_color(dpg.mvThemeCol_Tab, (232, 236, 244))
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (59, 130, 246, 120))
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, (59, 130, 246))
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, (238, 242, 248))
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, (220, 226, 238))
            
            # 按钮默认样式
            dpg.add_theme_color(dpg.mvThemeCol_Button, (235, 239, 246))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (218, 226, 240))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (198, 210, 232))
            
            # 表格样式
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, (236, 240, 248))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, (255, 255, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, (247, 249, 252))
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, (226, 231, 240))
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, (208, 215, 228))
            
            # 文字与高亮（高对比度深灰与纯黑，极易阅读）
            dpg.add_theme_color(dpg.mvThemeCol_Text, (30, 36, 48))
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (140, 146, 160))
            dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, (59, 130, 246, 90))
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (37, 99, 235))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (59, 130, 246))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (37, 99, 235))
            dpg.add_theme_color(dpg.mvThemeCol_Separator, (222, 226, 235))
            dpg.add_theme_color(dpg.mvThemeCol_Header, (220, 230, 248, 180))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (200, 218, 248, 220))
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (180, 206, 248, 240))
    return theme

def setup_global_theme():
    """初始化全局主题，恢复用户保存的深色/浅色偏好"""
    global _CURRENT_THEME, _GLOBAL_THEME_OBJECTS
    _CURRENT_THEME = load_theme_preference()
    _GLOBAL_THEME_OBJECTS['dark'] = build_dark_theme()
    _GLOBAL_THEME_OBJECTS['light'] = build_light_theme()
    dpg.bind_theme(_GLOBAL_THEME_OBJECTS[_CURRENT_THEME])

def toggle_global_theme() -> str:
    """切换全局主题模式并保存偏好"""
    global _CURRENT_THEME, _GLOBAL_THEME_OBJECTS
    _CURRENT_THEME = 'light' if _CURRENT_THEME == 'dark' else 'dark'
    save_theme_preference(_CURRENT_THEME)
    
    if _CURRENT_THEME not in _GLOBAL_THEME_OBJECTS:
        _GLOBAL_THEME_OBJECTS['dark'] = build_dark_theme()
        _GLOBAL_THEME_OBJECTS['light'] = build_light_theme()
        
    dpg.bind_theme(_GLOBAL_THEME_OBJECTS[_CURRENT_THEME])
    return _CURRENT_THEME

def create_button_theme(bg_color, hover_color, active_color, text_color=None):
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, bg_color)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover_color)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, active_color)
            if text_color:
                dpg.add_theme_color(dpg.mvThemeCol_Text, text_color)
    return theme
