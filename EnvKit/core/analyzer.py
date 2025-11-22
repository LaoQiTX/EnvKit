from typing import List, Dict
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

    def analyze(self, items: List[Dict], model_name: str = None) -> dict:
        try:
            LOGGER.info(f'analyze model={model_name or self.client.default_model} items={len(items)}')
        except Exception:
            pass
        return self.client.analyze(items, model_name)

    def add_model(self, model_def: dict):
        self.client.add_model(model_def)

    def remove_model(self, name: str):
        self.client.remove_model(name)
