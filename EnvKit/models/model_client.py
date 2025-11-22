import json
import os
from pathlib import Path
import urllib.request
import urllib.error

class ModelClient:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.models = []
        self.default_model = None
        self.load()

    def load(self):
        p = Path(self.config_path)
        if not p.exists():
            self.models = [{'name': 'local-rules', 'type': 'rule'}]
            self.default_model = 'local-rules'
            return
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.models = data.get('models', [{'name': 'local-rules', 'type': 'rule'}])
        self.default_model = data.get('default', self.models[0]['name'] if self.models else 'local-rules')

    def available(self) -> list:
        return self.models

    def set_default(self, name: str):
        self.default_model = name
        self.save()

    def add_model(self, model_def: dict):
        name = model_def.get('name')
        if not name:
            return
        if any(m.get('name') == name for m in self.models):
            for i, m in enumerate(self.models):
                if m.get('name') == name:
                    self.models[i] = model_def
                    break
        else:
            self.models.append(model_def)
        if not self.default_model:
            self.default_model = name
        self.save()

    def remove_model(self, name: str):
        self.models = [m for m in self.models if m.get('name') != name]
        if self.default_model == name:
            self.default_model = self.models[0]['name'] if self.models else None
        self.save()

    def save(self):
        data = {'models': self.models, 'default': self.default_model}
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def analyze(self, items: list, model_name: str = None) -> dict:
        m = model_name or self.default_model
        mdef = next((x for x in self.models if x.get('name') == m), {'type': 'rule'})
        t = mdef.get('type')
        if t == 'rule':
            return self._rule_analyze(items)
        if t == 'http':
            return self._http_analyze(items, mdef)
        return self._rule_analyze(items)

    def _rule_analyze(self, items: list) -> dict:
        env_issues = []
        reg_issues = []
        for it in items:
            k = it.get('key')
            v = it.get('value')
            kind = it.get('kind')
            if kind == 'env':
                if not v:
                    env_issues.append({'key': k, 'issue': 'empty'})
                elif ';' in v and len(v) > 4096:
                    env_issues.append({'key': k, 'issue': 'oversize'})
            if kind == 'reg':
                if v is None:
                    reg_issues.append({'key': k, 'issue': 'missing'})
        suggestions = []
        if env_issues:
            suggestions.append({'type': 'env', 'items': env_issues})
        if reg_issues:
            suggestions.append({'type': 'reg', 'items': reg_issues})
        return {'suggestions': suggestions}

    def _http_analyze(self, items: list, mdef: dict) -> dict:
        endpoint = mdef.get('endpoint')
        api_key = mdef.get('api_key')
        payload = {'items': items, 'model': mdef.get('model')}
        if not endpoint:
            return self._rule_analyze(items)
        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(endpoint, data=data, headers={'Content-Type': 'application/json'})
            if api_key:
                req.add_header('Authorization', f'Bearer {api_key}')
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = resp.read().decode('utf-8')
                j = json.loads(res)
                if isinstance(j, dict) and 'suggestions' in j:
                    return j
        except Exception:
            pass
        return self._rule_analyze(items)
