import os
import winreg
from typing import Dict, List, Tuple, Any
from utils.path_check import analyze_paths, rebuild_path, clean_path_entries, normalize_path
from utils.win_utils import notify_environment_change
from utils.logger import get_logger

LOGGER = get_logger('EnvKit')

USER = (winreg.HKEY_CURRENT_USER, r"Environment")
SYSTEM = (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment")

class EnvManager:
    def __init__(self, scope: str = 'user'):
        self.scope = scope

    def _root(self):
        return USER if self.scope == 'user' else SYSTEM

    def list(self) -> Dict[str, str]:
        root, sub = self._root()
        result = {}
        try:
            with winreg.OpenKey(root, sub, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        result[name] = str(value) if value is not None else ''
                        i += 1
                    except OSError:
                        break
        except OSError:
            pass
        return result

    def get(self, name: str) -> str:
        root, sub = self._root()
        try:
            with winreg.OpenKey(root, sub, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, name)
                return str(value) if value is not None else ''
        except OSError:
            return None

    def set(self, name: str, value: str):
        root, sub = self._root()
        vtype = winreg.REG_EXPAND_SZ if ('%' in value or name.upper() == 'PATH') else winreg.REG_SZ
        try:
            with winreg.OpenKey(root, sub, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, name, 0, vtype, value)
        except PermissionError as e:
            raise PermissionError(f"权限不足：修改 {self.scope} 作用域环境变量需要管理员特权，请以管理员身份运行。") from e
        except OSError as e:
            raise OSError(f"注册表写入失败: {e}") from e

        notify_environment_change()
        try:
            LOGGER.info(f'env set {self.scope} {name}')
        except Exception:
            pass

    def delete(self, name: str):
        root, sub = self._root()
        try:
            with winreg.OpenKey(root, sub, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
        except PermissionError as e:
            raise PermissionError(f"权限不足：删除 {self.scope} 作用域环境变量需要管理员特权，请以管理员身份运行。") from e
        except FileNotFoundError:
            pass
        except OSError as e:
            raise OSError(f"注册表删除失败: {e}") from e

        notify_environment_change()
        try:
            LOGGER.info(f'env delete {self.scope} {name}')
        except Exception:
            pass

    def list_path(self, name: str = 'PATH') -> List[dict]:
        v = self.get(name) or ''
        return analyze_paths(v)

    def update_path_entries(self, entries: List[str], name: str = 'PATH'):
        newv = rebuild_path(entries)
        self.set(name, newv)
        try:
            LOGGER.info(f'env path update {self.scope} {name}')
        except Exception:
            pass

    def clean_path(
        self,
        remove_invalid: bool = True,
        remove_duplicates: bool = True,
        remove_empty: bool = True,
        name: str = 'PATH'
    ) -> Dict[str, int]:
        """一键清理 PATH 并返回清理统计"""
        cur = self.get(name) or ''
        entries = cur.split(';') if cur else []
        cleaned, stats = clean_path_entries(entries, remove_invalid, remove_duplicates, remove_empty)
        if stats['total_removed'] > 0:
            self.update_path_entries(cleaned, name)
        return stats
