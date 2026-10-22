import dearpygui.dearpygui as dpg

COLOR_SUCCESS = (16, 185, 129, 255)
COLOR_DANGER = (239, 68, 68, 255)
COLOR_WARNING = (245, 158, 11, 255)
COLOR_EMPTY = (168, 85, 247, 255)
COLOR_MUTED = (156, 163, 175, 255)
COLOR_PRIMARY = (59, 130, 246, 255)
COLOR_WHITE = (243, 244, 246, 255)

def setup_global_theme():
    """构建现代暗黑风格全局主题"""
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            # 基础几何圆角与内边距
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 6)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 4)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 6)
            dpg.add_theme_style(dpg.mvStyleVar_CellPadding, 6, 4)
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

    dpg.bind_theme(global_theme)

def create_button_theme(bg_color, hover_color, active_color):
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvButton):
            dpg.add_theme_color(dpg.mvThemeCol_Button, bg_color)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, hover_color)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, active_color)
    return theme
