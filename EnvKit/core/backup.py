import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from utils.logger import get_logger
from utils.path_helper import get_backup_dir

LOGGER = get_logger('EnvKit')

def backup(
    env_data: Dict[str, Any],
    reg_data: Dict[str, Any],
    out_dir: Optional[str] = None,
    category: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None
) -> str:
    """创建环境变量或注册表备份 JSON 文件"""
    directory = Path(out_dir) if out_dir else get_backup_dir()
    directory.mkdir(parents=True, exist_ok=True)
    
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    prefix = 'backup-env' if category == 'env' else 'backup-reg' if category == 'reg' else 'backup'
    file_name = f'{prefix}-{ts}.json'
    file_path = directory / file_name
    
    data = {
        'version': '2.0',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'category': category,
        'meta': meta or {},
        'env': env_data,
        'reg': reg_data
    }
    
    with open(str(file_path), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    try:
        LOGGER.info(f'Backup saved successfully: {file_path}')
    except Exception:
        pass
        
    return str(file_path)

def restore(file_path: str) -> Dict[str, Any]:
    """读取备份 JSON 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    try:
        LOGGER.info(f'Backup loaded from: {file_path}')
    except Exception:
        pass
    return data
