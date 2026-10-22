import sys
import os
import ctypes
import traceback
from pathlib import Path

# Windows 高 DPI 缩放支持，确保字体与界面高分屏下锐利不模糊
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import dearpygui.dearpygui as dpg
from gui.main_window import build_ui

def _setup_font():
    """配置高质量中文字体（支持正文与加大加粗表头字体）"""
    with dpg.font_registry():
        candidates = [
            r"C:\Windows\Fonts\msyh.ttc",
            r"C:\Windows\Fonts\msyhbd.ttc",
            r"C:\Windows\Fonts\SimHei.ttf",
            r"C:\Windows\Fonts\SimSun.ttf",
            r"C:\Windows\Fonts\Microsoft YaHei.ttf"
        ]
        chosen_path = None
        for p in candidates:
            if os.path.exists(p):
                chosen_path = p
                break
                
        if chosen_path:
            # 1. 通用正文字体 (20px)
            with dpg.font(chosen_path, 20, tag='font_body') as font_body:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)
                dpg.add_font_range(0x0020, 0x007E)
                dpg.add_font_range(0x25A0, 0x25FF)
            dpg.bind_font(font_body)

            # 2. 表头专用加大加粗字体 (22px，解决表头字太小问题)
            bold_path = r"C:\Windows\Fonts\msyhbd.ttc" if os.path.exists(r"C:\Windows\Fonts\msyhbd.ttc") else chosen_path
            with dpg.font(bold_path, 22, tag='font_header') as font_header:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)
                dpg.add_font_range(0x0020, 0x007E)
                dpg.add_font_range(0x25A0, 0x25FF)

def main():
    try:
        dpg.create_context()
        _setup_font()
        build_ui()
        
        dpg.create_viewport(
            title='EnvKit',
            width=1420,
            height=890,
            min_width=1120,
            min_height=700
        )
        dpg.setup_dearpygui()
        dpg.set_primary_window('EnvKit', True)
        dpg.show_viewport()

        # 安全设置中文窗口标题（避免 DearPyGui C++ 层的 UTF-8 视口标题奔溃问题）
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, 'EnvKit')
            if hwnd:
                ctypes.windll.user32.SetWindowTextW(hwnd, 'envkit - 本地环境工作台')
        except Exception:
            pass

        dpg.start_dearpygui()
    except Exception as e:
        err_msg = traceback.format_exc()
        try:
            ctypes.windll.user32.MessageBoxW(
                None,
                f"EnvKit 运行异常：\n\n{err_msg}\n请在命令行运行查看详细日志。",
                "EnvKit 错误",
                0x10
            )
        except Exception:
            pass
    finally:
        try:
            dpg.destroy_context()
        except Exception:
            pass

if __name__ == '__main__':
    main()
