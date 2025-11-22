import os
import winreg
from typing import Dict, List
from utils.path_check import analyze_paths, rebuild_path
from utils.logger import get_logger

LOGGER = get_logger('EnvKit')

USER = (winreg.HKEY_CURRENT_USER, r"Environment")
SYSTEM = (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment")

class EnvManager:
    def __init__(self, scope: str = 'user'):
        self.scope = scope

    def _root(self):
        return USER if self.scope == 'user' else SYSTEM

    def list(self) -> Dict[str, str]:
        root, sub = self._root()
        with winreg.OpenKey(root, sub) as key:
            result = {}
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    result[name] = value
                    i += 1
                except OSError:
                    break
            return result

    def get(self, name: str) -> str:
        root, sub = self._root()
        try:
            with winreg.OpenKey(root, sub) as key:
                value, _ = winreg.QueryValueEx(key, name)
                return value
        except OSError:
            return None

    def set(self, name: str, value: str):
        root, sub = self._root()
        with winreg.OpenKey(root, sub, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value)
        try:
            LOGGER.info(f'env set {self.scope} {name}')
        except Exception:
            pass

    def delete(self, name: str):
        root, sub = self._root()
        with winreg.OpenKey(root, sub, 0, winreg.KEY_SET_VALUE) as key:
            try:
                winreg.DeleteValue(key, name)
            except OSError:
                pass
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
