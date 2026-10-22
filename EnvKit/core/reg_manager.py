import winreg
from typing import List, Dict, Tuple, Any, Optional
from utils.logger import get_logger

LOGGER = get_logger('EnvKit')

ROOTS = {
    'HKCU': winreg.HKEY_CURRENT_USER,
    'HKLM': winreg.HKEY_LOCAL_MACHINE
}

TYPE_MAP = {
    winreg.REG_SZ: 'REG_SZ',
    winreg.REG_EXPAND_SZ: 'REG_EXPAND_SZ',
    winreg.REG_DWORD: 'REG_DWORD',
    winreg.REG_QWORD: 'REG_QWORD',
    winreg.REG_MULTI_SZ: 'REG_MULTI_SZ',
    winreg.REG_BINARY: 'REG_BINARY'
}

STR_TO_TYPE = {v: k for k, v in TYPE_MAP.items()}

PRESET_KEYS = [
    {
        'label': '用户环境变量 (HKCU)',
        'root': 'HKCU',
        'subkey': r'Environment'
    },
    {
        'label': '系统环境变量 (HKLM)',
        'root': 'HKLM',
        'subkey': r'SYSTEM\CurrentControlSet\Control\Session Manager\Environment'
    },
    {
        'label': '当前用户开机自启 (HKCU Run)',
        'root': 'HKCU',
        'subkey': r'Software\Microsoft\Windows\CurrentVersion\Run'
    },
    {
        'label': '系统开机自启 (HKLM Run)',
        'root': 'HKLM',
        'subkey': r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run'
    },
    {
        'label': '应用执行别名 (HKLM App Paths)',
        'root': 'HKLM',
        'subkey': r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths'
    }
]

class RegManager:
    def __init__(self, root: str = 'HKCU'):
        self.root_str = root
        self.root = ROOTS.get(root, winreg.HKEY_CURRENT_USER)

    def list_values(self, subkey: str) -> List[dict]:
        subkey_clean = subkey.strip('\\')
        result = []
        try:
            with winreg.OpenKey(self.root, subkey_clean, 0, winreg.KEY_READ) as key:
                i = 0
                while True:
                    try:
                        name, value, vtype = winreg.EnumValue(key, i)
                        result.append({
                            'name': name if name else '(默认)',
                            'value': value,
                            'type': vtype,
                            'type_str': TYPE_MAP.get(vtype, f'TYPE_{vtype}')
                        })
                        i += 1
                    except OSError:
                        break
        except PermissionError as e:
            raise PermissionError(f"无法读取该注册表项，需要管理员权限: {e}") from e
        except OSError:
            return []
        return result

    def get_value(self, subkey: str, name: str) -> Tuple[Any, Optional[int]]:
        subkey_clean = subkey.strip('\\')
        actual_name = '' if name == '(默认)' else name
        try:
            with winreg.OpenKey(self.root, subkey_clean, 0, winreg.KEY_READ) as key:
                value, vtype = winreg.QueryValueEx(key, actual_name)
                return value, vtype
        except OSError:
            return None, None

    def set_value(self, subkey: str, name: str, value: Any, vtype: int = winreg.REG_SZ):
        subkey_clean = subkey.strip('\\')
        actual_name = '' if name == '(默认)' else name
        
        # 针对 REG_DWORD 处理字符串输入转 int
        if vtype == winreg.REG_DWORD:
            try:
                value = int(value)
            except Exception:
                value = 0
                
        try:
            with winreg.CreateKey(self.root, subkey_clean) as key:
                winreg.SetValueEx(key, actual_name, 0, vtype, value)
        except PermissionError as e:
            raise PermissionError(f"权限不足：修改 {self.root_str} 下该子键需要管理员权限，请以管理员身份运行。") from e
        except OSError as e:
            raise OSError(f"注册表写入失败: {e}") from e

        try:
            LOGGER.info(f'reg set {self.root_str}\\{subkey_clean} {actual_name}')
        except Exception:
            pass

    def delete_value(self, subkey: str, name: str):
        subkey_clean = subkey.strip('\\')
        actual_name = '' if name == '(默认)' else name
        try:
            with winreg.OpenKey(self.root, subkey_clean, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, actual_name)
        except PermissionError as e:
            raise PermissionError(f"权限不足：删除 {self.root_str} 下该值需要管理员权限，请以管理员身份运行。") from e
        except OSError as e:
            raise OSError(f"注册表删除失败: {e}") from e

        try:
            LOGGER.info(f'reg delete {self.root_str}\\{subkey_clean} {actual_name}')
        except Exception:
            pass
