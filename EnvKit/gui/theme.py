import json
import dearpygui.dearpygui as dpg
from pathlib import Path
from utils.path_helper import get_base_dir

# -------------------------------------------------------------
# 设计稿配色规范 (来自 design-notes.md 与 SVG 调色板)
# -------------------------------------------------------------
# 亮色模式 (Light):
#   --bg: #FAFBFD (250, 251, 253)
#   --sidebar-bg: #F0F3F9 (240, 243, 249)
#   --surface: #FDFEFF (253, 254, 255)
#   --surface-alt: #F4F7FC (244, 247, 252)
#   --text: #202D43 (32, 45, 67)
#   --muted: #5E6E86 (94, 110, 134)
#   --line: #DBE3EF (219, 227, 239)
#   --accent: #2E5FCC (46, 95, 204)
#   --accent-hover: (36, 77, 176)
#   --selected: #E5EDFC (229, 237, 252)
#
# 暗色模式 (Dark):
#   --bg: #171D2A (23, 29, 42)
#   --sidebar-bg: #131925 (19, 25, 37)
#   --surface: #1C2433 (28, 36, 51)
#   --surface-alt: #202B3E (32, 43, 62)
#   --text: #E2E9F6 (226, 233, 246)
#   --muted: #A6B5CF (166, 181, 207)
#   --line: #33425D (51, 66, 93)
#   --accent: #5687F0 (86, 135, 240)
#   --selected: #293E66 (41, 62, 102)
# -------------------------------------------------------------

# 常用语义色
COLOR_PRIMARY = (46, 95, 204, 255)       # 钴蓝强调色 #2E5FCC
COLOR_PRIMARY_DARK = (86, 135, 240, 255) # 深色模式浅蓝强调色 #5687F0
COLOR_SUCCESS = (16, 185, 129, 255)      # 成功绿
COLOR_WARNING = (145, 96, 31, 255)       # 设计稿路径警告黄 #91601F
COLOR_DANGER = (164, 68, 54, 255)        # 设计稿错误红 #A44436
COLOR_EMPTY = (140, 100, 210, 255)       # 紫色
COLOR_MUTED = (94, 110, 134, 255)        # 次要灰蓝 #5E6E86
COLOR_WHITE = (248, 250, 255, 255)

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
    """深色模式 (海军蓝表面与浅蓝强调色，设计稿一致)"""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            # 圆角规则：输入框/按钮 6，行选择 5，状态标签 4，面板 7
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 7)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 5)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 8)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 5)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)
            dpg.add_theme_style(dpg.mvStyleVar_SelectableTextAlign, 0.0, 0.5)

            # 颜色方案
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (23, 29, 42))        # #171D2A
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (28, 36, 51))         # #1C2433
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (32, 43, 62))         # #202B3E
            dpg.add_theme_color(dpg.mvThemeCol_Border, (51, 66, 93))          # #33425D
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))
            
            # 滚动条设计：透明轨道 + 8px 极细浮动药丸滑块，杜绝宽厚丑陋滚动条
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (86, 135, 240, 90))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (86, 135, 240, 180))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (86, 135, 240, 250))
            
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (32, 43, 62))         # #202B3E
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (41, 62, 102)) # #293E66
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (50, 75, 120))
            
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (28, 36, 51))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (19, 25, 37))
            
            # Tab 选项卡
            dpg.add_theme_color(dpg.mvThemeCol_Tab, (32, 43, 62))
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (86, 135, 240, 160))
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, (86, 135, 240))
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, (23, 29, 42))
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, (41, 62, 102))
            
            # 按钮默认样式
            dpg.add_theme_color(dpg.mvThemeCol_Button, (38, 52, 75))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (86, 135, 240))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (60, 105, 210))
            
            # 表格样式与单元格间距优化 (垂直内边距设为 0，使选中整行覆盖全单元格)
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, (32, 43, 62))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, (28, 36, 51))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, (32, 43, 62))
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, (51, 66, 93))
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, (65, 84, 118))
            
            # 文字与选中高亮 (纯正不透明度与悬停色，整行高亮无缝覆盖)
            dpg.add_theme_color(dpg.mvThemeCol_Text, (226, 233, 246))         # #E2E9F6
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (120, 135, 160))
            dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, (86, 135, 240, 120))
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (86, 135, 240))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (86, 135, 240))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (115, 155, 245))
            dpg.add_theme_color(dpg.mvThemeCol_Separator, (51, 66, 93))
            dpg.add_theme_color(dpg.mvThemeCol_Header, (41, 62, 102, 255))    # 纯色选中背景 #293E66
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (56, 85, 140, 240)) # 纯净悬停背景
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (60, 105, 210, 255))

        with dpg.theme_component(dpg.mvTable):
            # 表格单元格垂直 padding 紧凑化，让 selectable(span_columns) 完美贴合表格行上下边缘
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 10, 0)
    return theme

def build_light_theme():
    """浅色模式 (冷白与浅蓝表面、钴蓝强调色，设计稿一致)"""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            # 圆角规则：输入框/按钮 6，行选择 5，状态标签 4，面板 7
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 7)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 5)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 8)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 5)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)
            dpg.add_theme_style(dpg.mvStyleVar_SelectableTextAlign, 0.0, 0.5)

            # 颜色方案
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (250, 251, 253))      # #FAFBFD
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (253, 254, 255))       # #FDFEFF
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (255, 255, 255))
            dpg.add_theme_color(dpg.mvThemeCol_Border, (219, 227, 239))        # #DBE3EF
            dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))
            
            # 滚动条设计：透明轨道 + 8px 极细浮动药丸滑块
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (0, 0, 0, 0))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, (46, 95, 204, 70))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, (46, 95, 204, 160))
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabActive, (46, 95, 204, 230))
            
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (244, 247, 252))       # #F4F7FC
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (229, 237, 252))# #E5EDFC
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (215, 226, 248))
            
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (240, 243, 249))
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (244, 247, 252))
            
            # Tab 选项卡
            dpg.add_theme_color(dpg.mvThemeCol_Tab, (240, 243, 249))
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (46, 95, 204, 120))
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, (46, 95, 204))       # #2E5FCC
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocused, (244, 247, 252))
            dpg.add_theme_color(dpg.mvThemeCol_TabUnfocusedActive, (229, 237, 252))
            
            # 按钮默认样式
            dpg.add_theme_color(dpg.mvThemeCol_Button, (244, 247, 252))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (229, 237, 252))
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (210, 222, 245))
            
            # 表格样式与单元格间距优化 (垂直内边距设为 0，使选中整行覆盖全单元格)
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, (244, 247, 252))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, (253, 254, 255))
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, (244, 247, 252))
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, (219, 227, 239))
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, (200, 210, 225))
            
            # 文字与选中高亮 (高辨识度纯色选中背景)
            dpg.add_theme_color(dpg.mvThemeCol_Text, (32, 45, 67))             # #202D43
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (130, 142, 160))
            dpg.add_theme_color(dpg.mvThemeCol_TextSelectedBg, (46, 95, 204, 80))
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (46, 95, 204))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (46, 95, 204))
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (36, 77, 176))
            dpg.add_theme_color(dpg.mvThemeCol_Separator, (219, 227, 239))
            dpg.add_theme_color(dpg.mvThemeCol_Header, (215, 228, 250, 255))   # 浅蓝选中 #D7E4FA
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (232, 240, 254, 255)) # 悬停
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (198, 215, 245, 255))

        with dpg.theme_component(dpg.mvTable):
            # 表格单元格垂直 padding 紧凑化，让 selectable(span_columns) 完美贴合表格行上下边缘
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 10, 0)
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

def create_splitter_theme(mode: str = None):
    """精致的可拖拽分割线主题：平时呈现细微中性发丝线，悬停时点亮为蓝色光晕，拖拽时呈深度强调色"""
    m = mode or get_current_theme_mode()
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            if m == 'light':
                dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 0, 0, 0))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (46, 95, 204, 150))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (36, 77, 176, 240))
                dpg.add_theme_color(dpg.mvThemeCol_Border, (215, 222, 232, 200))
            else:
                dpg.add_theme_color(dpg.mvThemeCol_Button, (0, 0, 0, 0))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (86, 135, 240, 160))
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (46, 95, 204, 240))
                dpg.add_theme_color(dpg.mvThemeCol_Border, (51, 66, 93, 180))
                
            dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 0, 0)
    return theme
