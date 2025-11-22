import json
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger

LOGGER = get_logger('EnvKit')

def backup(env_data: dict, reg_data: dict, out_dir: str, category: str = None, meta: dict = None) -> str:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    prefix = 'backup-env' if category == 'env' else 'backup-reg' if category == 'reg' else 'backup'
    name = f'{prefix}-{ts}.json'
    path = str(Path(out_dir) / name)
    data = {'env': env_data, 'reg': reg_data, 'category': category, 'meta': meta or {}}
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    try:
        LOGGER.info(f'backup write {path}')
    except Exception:
        pass
    return path

def restore(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        j = json.load(f)
    try:
        LOGGER.info(f'backup restore {file_path}')
    except Exception:
        pass
    return j
