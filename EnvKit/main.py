import dearpygui.dearpygui as dpg
from gui.main_window import build_ui
import ctypes
import traceback
import sys

def _setup_font():
    with dpg.font_registry():
        candidates = [
            r"C:\\Windows\\Fonts\\msyh.ttc",
            r"C:\\Windows\\Fonts\\SimHei.ttf",
            r"C:\\Windows\\Fonts\\SimSun.ttf",
            r"C:\\Windows\\Fonts\\Microsoft YaHei.ttf"
        ]
        path = None
        for p in candidates:
            try:
                with open(p, 'rb') as _:
                    path = p
                    break
            except Exception:
                continue
        if path:
            with dpg.font(path, 16) as font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)
            dpg.bind_font(font)

def main():
    try:
        dpg.create_context()
        if not getattr(sys, 'frozen', False):
            _setup_font()
        build_ui()
        dpg.create_viewport(title='EnvKit', width=1024, height=768)
        dpg.setup_dearpygui()
        dpg.set_primary_window('EnvKit', True)
        dpg.show_viewport()
        dpg.start_dearpygui()
    except Exception:
        try:
            ctypes.windll.user32.MessageBoxW(None, "程序异常，请在命令行运行查看详细错误", "EnvKit", 0x10)
        except Exception:
            pass
    finally:
        try:
            dpg.destroy_context()
        except Exception:
            pass

if __name__ == '__main__':
    main()
