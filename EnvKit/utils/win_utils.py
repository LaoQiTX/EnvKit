import sys
import os
import ctypes
from ctypes import wintypes
from pathlib import Path
from typing import Optional, List, Tuple

def is_admin() -> bool:
    """检查当前进程是否具有管理员特权"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def restart_as_admin():
    """以管理员身份重新启动当前程序（弹出 UAC 提权提示）"""
    try:
        if getattr(sys, 'frozen', False):
            exe = sys.executable
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        else:
            exe = sys.executable
            # 如果作为脚本运行，第一个参数是脚本路径
            script = os.path.abspath(sys.argv[0])
            args = [f'"{script}"'] + [f'"{arg}"' for arg in sys.argv[1:]]
            params = " ".join(args)
        
        ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
        if ret > 32:
            # 提权成功：关闭当前非管理员进程窗口，只保留提权后的新窗口
            try:
                import dearpygui.dearpygui as dpg
                dpg.stop_dearpygui()
            except Exception:
                pass
            os._exit(0)
    except Exception as e:
        return str(e)
    return None

def notify_environment_change():
    """
    向 Windows 所有顶级窗口广播 WM_SETTINGCHANGE 消息，通知环境变量已更新。
    让后续打开的命令行窗口和应用程序立即生效，无需注销或重启电脑。
    """
    try:
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        result = ctypes.c_ulong()
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            "Environment",
            SMTO_ABORTIFHUNG,
            3000,
            ctypes.byref(result)
        )
    except Exception:
        pass

def open_in_explorer(path: str):
    """在 Windows 资源管理器中打开指定路径或选中文件"""
    try:
        p = os.path.abspath(path)
        if os.path.isdir(p):
            os.startfile(p)
        elif os.path.isfile(p):
            os.system(f'explorer.exe /select,"{p}"')
        elif os.path.exists(os.path.dirname(p)):
            os.startfile(os.path.dirname(p))
    except Exception:
        pass

def choose_file(
    initial_dir: Optional[str] = None,
    file_types: Optional[List[Tuple[str, str]]] = None,
    title: str = "选择文件"
) -> Optional[str]:
    """
    打开 Windows 原生文件选择对话框。
    比 ImGui 内部文件浏览器更稳定，完全支持所有盘符、中文路径和网络共享。
    """
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        
        types = file_types or [("JSON 文件", "*.json"), ("所有文件", "*.*")]
        fp = filedialog.askopenfilename(
            parent=root,
            initialdir=initial_dir or os.getcwd(),
            title=title,
            filetypes=types
        )
        root.destroy()
        return fp if fp else None
    except Exception:
        return None

def choose_directory(initial_dir: Optional[str] = None, title: str = "选择文件夹") -> Optional[str]:
    """打开 Windows 原生文件夹选择对话框"""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        
        dp = filedialog.askdirectory(
            parent=root,
            initialdir=initial_dir or os.getcwd(),
            title=title
        )
        root.destroy()
        return dp if dp else None
    except Exception:
        return None
