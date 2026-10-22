import sys
import os
from pathlib import Path

def get_base_dir() -> Path:
    """
    获取应用程序的基础根目录（用于存放可写配置、日志和备份）。
    - 打包为 EXE 时（PyInstaller / Nuitka）：返回 exe 所在目录
    - 作为 Python 脚本运行时：返回 EnvKit 源码根目录
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    # 源码模式：Path(__file__).resolve().parents[1] 是 EnvKit 目录
    return Path(__file__).resolve().parents[1]

def get_bundle_dir() -> Path:
    """
    获取只读捆绑资源目录。
    - PyInstaller 单文件时：sys._MEIPASS
    - 其他情况：返回基础根目录
    """
    if getattr(sys, 'frozen', False):
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]

def get_model_config_path() -> Path:
    """
    获取可写配置文件 model_config.json 的路径。
    若目标文件尚不存在，会自动从捆绑资源复制或生成默认配置，并确保父目录存在。
    彻底解决打包后无法读取目录的问题。
    """
    base = get_base_dir()
    target_path = base / 'models' / 'model_config.json'
    if not target_path.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)
        bundle_path = get_bundle_dir() / 'models' / 'model_config.json'
        if bundle_path.exists():
            try:
                import shutil
                shutil.copy2(bundle_path, target_path)
                return target_path
            except Exception:
                pass
        
        # 默认配置模板
        import json
        default_cfg = {
            "models": [
                {
                    "name": "local-rules",
                    "type": "rule"
                },
                {
                    "name": "deepseek-chat",
                    "type": "openai",
                    "endpoint": "https://api.deepseek.com/v1/chat/completions",
                    "model": "deepseek-chat",
                    "api_key": ""
                }
            ],
            "default": "local-rules"
        }
        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                json.dump(default_cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return target_path

def get_backup_dir() -> Path:
    """
    获取备份目录，自动确保目录存在。
    """
    base = get_base_dir()
    backup_path = base / '.backup'
    backup_path.mkdir(parents=True, exist_ok=True)
    return backup_path
