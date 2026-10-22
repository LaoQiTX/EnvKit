from typing import List, Dict, Any, Optional, Tuple
from models.model_client import ModelClient
from utils.logger import get_logger

LOGGER = get_logger('EnvKit')

class Analyzer:
    def __init__(self, config_path: str):
        self.client = ModelClient(config_path)

    def models(self) -> list:
        return self.client.available()

    def set_default(self, name: str):
        self.client.set_default(name)

    def analyze(self, items: List[Dict[str, Any]], model_name: Optional[str] = None) -> dict:
        try:
            LOGGER.info(f'analyze model={model_name or self.client.default_model} items={len(items)}')
        except Exception:
            pass
        return self.client.analyze(items, model_name)

    def analyze_full_system(self, user_vars: Dict[str, str], sys_vars: Dict[str, str], model_name: Optional[str] = None) -> dict:
        """全量体检：分析所有用户环境变量、系统环境变量以及 PATH"""
        items = []
        for k, v in user_vars.items():
            items.append({'kind': 'env', 'scope': 'user', 'key': f'[用户] {k}', 'value': v})
        for k, v in sys_vars.items():
            items.append({'kind': 'env', 'scope': 'system', 'key': f'[系统] {k}', 'value': v})
        return self.analyze(items, model_name)

    def test_connection(self, model_name: str) -> Tuple[bool, str]:
        return self.client.test_connection(model_name)

    def add_model(self, model_def: dict):
        self.client.add_model(model_def)

    def remove_model(self, name: str):
        self.client.remove_model(name)
