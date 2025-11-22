import winreg
from typing import List, Dict
from utils.logger import get_logger

LOGGER = get_logger('EnvKit')

ROOTS = {
    'HKCU': winreg.HKEY_CURRENT_USER,
    'HKLM': winreg.HKEY_LOCAL_MACHINE
}

class RegManager:
    def __init__(self, root: str = 'HKCU'):
        self.root = ROOTS.get(root, winreg.HKEY_CURRENT_USER)

    def list_values(self, subkey: str) -> List[dict]:
        try:
            with winreg.OpenKey(self.root, subkey) as key:
                result = []
                i = 0
                while True:
                    try:
                        name, value, vtype = winreg.EnumValue(key, i)
                        result.append({'name': name, 'value': value, 'type': vtype})
                        i += 1
                    except OSError:
                        break
                return result
        except OSError:
            return []

    def get_value(self, subkey: str, name: str):
        try:
            with winreg.OpenKey(self.root, subkey) as key:
                value, vtype = winreg.QueryValueEx(key, name)
                return value, vtype
        except OSError:
            return None, None

    def set_value(self, subkey: str, name: str, value, vtype=winreg.REG_SZ):
        with winreg.CreateKey(self.root, subkey) as key:
            winreg.SetValueEx(key, name, 0, vtype, value)
        try:
            LOGGER.info(f'reg set {subkey} {name}')
        except Exception:
            pass

    def delete_value(self, subkey: str, name: str):
        try:
            with winreg.OpenKey(self.root, subkey, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, name)
        except OSError:
            pass
        try:
            LOGGER.info(f'reg delete {subkey} {name}')
        except Exception:
            pass
