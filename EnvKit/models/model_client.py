import json
import os
import re
from pathlib import Path
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Tuple
from utils.path_check import normalize_path

class ModelClient:
    def __init__(self, config_path: str):
        self.config_path = str(config_path)
        self.models = []
        self.default_model = None
        self.load()

    def load(self):
        p = Path(self.config_path)
        if not p.exists():
            self.models = [
                {'name': 'local-rules', 'type': 'rule'},
                {
                    'name': 'deepseek-chat',
                    'type': 'openai',
                    'endpoint': 'https://api.deepseek.com/v1/chat/completions',
                    'model': 'deepseek-chat',
                    'api_key': ''
                }
            ]
            self.default_model = 'local-rules'
            self.save()
            return
            
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.models = data.get('models', [{'name': 'local-rules', 'type': 'rule'}])
            self.default_model = data.get('default', self.models[0]['name'] if self.models else 'local-rules')
        except Exception:
            self.models = [{'name': 'local-rules', 'type': 'rule'}]
            self.default_model = 'local-rules'

    def available(self) -> List[Dict[str, Any]]:
        return self.models

    def set_default(self, name: str):
        self.default_model = name
        self.save()

    def add_model(self, model_def: Dict[str, Any]):
        name = model_def.get('name')
        if not name:
            return
        found = False
        for i, m in enumerate(self.models):
            if m.get('name') == name:
                self.models[i] = model_def
                found = True
                break
        if not found:
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
        p = Path(self.config_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {'models': self.models, 'default': self.default_model}
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def analyze(self, items: List[Dict[str, Any]], model_name: Optional[str] = None) -> Dict[str, Any]:
        m = model_name or self.default_model
        mdef = next((x for x in self.models if x.get('name') == m), {'type': 'rule'})
        mtype = mdef.get('type')
        
        if mtype == 'rule':
            return self._rule_analyze(items)
        elif mtype == 'openai':
            return self._openai_analyze(items, mdef)
        elif mtype == 'http':
            return self._http_analyze(items, mdef)
            
        return self._rule_analyze(items)

    def test_connection(self, model_name: str) -> Tuple[bool, str]:
        """测试指定模型的 API 连通性"""
        mdef = next((x for x in self.models if x.get('name') == model_name), None)
        if not mdef:
            return False, "模型配置不存在"
        if mdef.get('type') == 'rule':
            return True, "本地内置规则引擎，随时可用无需网络连接"
            
        endpoint = mdef.get('endpoint')
        if not endpoint:
            return False, "未填写 HTTP 端点 URL"
            
        test_items = [{'kind': 'env', 'key': 'TEST_VAR', 'value': 'C:\\Windows'}]
        try:
            if mdef.get('type') == 'openai':
                res = self._openai_analyze(test_items, mdef)
            else:
                res = self._http_analyze(test_items, mdef)
                
            if res.get('error'):
                return False, res['error']
            return True, "连接成功！模型已正常响应分析"
        except Exception as e:
            return False, f"连接异常: {e}"

    def _rule_analyze(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        env_issues = []
        reg_issues = []
        suggestions = []
        
        # 收集系统已有变量名，用于检查引用不存在的变量
        known_vars = set(os.environ.keys())
        for it in items:
            if it.get('kind') == 'env' and it.get('key'):
                known_vars.add(it['key'])
                
        for it in items:
            k = it.get('key', '')
            v = it.get('value')
            kind = it.get('kind')
            
            if kind == 'env':
                if v is None or v == '':
                    env_issues.append({'key': k, 'issue': 'empty', 'desc': '变量值为空，可能为无用残留项'})
                    continue
                if len(v) > 2048:
                    env_issues.append({'key': k, 'issue': 'oversize', 'desc': f'变量长度为 {len(v)} 字符，超过 2048 限制，可能导致部分程序截断'})
                    
                # 检查未定义环境变量引用 %VAR%
                refs = re.findall(r'%([^%]+)%', v)
                for r in refs:
                    if r.upper() not in [x.upper() for x in known_vars]:
                        env_issues.append({'key': k, 'issue': 'dangling_ref', 'desc': f'引用了未定义的环境变量 %{r}%'})
                        
                # 检查分号分隔路径（如 PATH）
                if ';' in v:
                    parts = v.split(';')
                    empty_count = sum(1 for p in parts if not p.strip())
                    if empty_count > 0:
                        env_issues.append({'key': k, 'issue': 'empty_path', 'desc': f'包含 {empty_count} 个空路径条目（多余分号）'})
                        
                    seen = set()
                    dups = []
                    for p in parts:
                        clean_p = p.strip().strip('"').strip("'")
                        if not clean_p:
                            continue
                        p_lower = clean_p.lower()
                        if p_lower in seen and p_lower not in dups:
                            dups.append(clean_p)
                        seen.add(p_lower)
                    if dups:
                        env_issues.append({'key': k, 'issue': 'duplicate_paths', 'desc': f'包含重复路径: {", ".join(dups[:3])}'})
                        
                # 检查单一路径是否存在
                elif '\\' in v or '/' in v:
                    norm = normalize_path(v)
                    if not os.path.exists(norm):
                        env_issues.append({'key': k, 'issue': 'broken_path', 'desc': f'指向的路径不存在: {norm}'})

            elif kind == 'reg':
                if v is None:
                    reg_issues.append({'key': k, 'issue': 'missing', 'desc': '注册表项或键值不存在'})
                elif isinstance(v, str):
                    if ('\\' in v or '/' in v):
                        norm = normalize_path(v)
                        if not os.path.exists(norm):
                            reg_issues.append({'key': k, 'issue': 'broken_path', 'desc': f'指向的文件/目录不存在: {norm}'})
                    if '%' in v and it.get('type') == 1: # REG_SZ with %var%
                        reg_issues.append({'key': k, 'issue': 'unexpanded_reg_sz', 'desc': '字符串包含 %变量%，但类型为普通 REG_SZ，Windows不会自动展开，建议改为 REG_EXPAND_SZ'})

        if env_issues:
            suggestions.append({'type': 'env', 'items': env_issues})
        if reg_issues:
            suggestions.append({'type': 'reg', 'items': reg_issues})
            
        summary_lines = []
        if not suggestions:
            summary_lines.append("未发现明显异常或错误，各项参数配置正常。")
        else:
            summary_lines.append(f"本地规则检测共发现 {len(env_issues) + len(reg_issues)} 处潜在问题：")
            for iss in env_issues:
                summary_lines.append(f"- [环境变量] {iss['key']}: {iss['desc']}")
            for iss in reg_issues:
                summary_lines.append(f"- [注册表] {iss['key']}: {iss['desc']}")
                
        return {
            'model': 'local-rules',
            'suggestions': suggestions,
            'summary': "\n".join(summary_lines)
        }

    def _openai_analyze(self, items: List[Dict[str, Any]], mdef: Dict[str, Any]) -> Dict[str, Any]:
        """通过 OpenAI / DeepSeek 标准 Chat Completions 协议分析"""
        endpoint = mdef.get('endpoint') or 'https://api.deepseek.com/v1/chat/completions'
        api_key = mdef.get('api_key', '').strip()
        model = mdef.get('model') or 'deepseek-chat'
        
        # 预先做一次本地规则汇总作为参考基准
        local_res = self._rule_analyze(items)
        
        items_desc = []
        for it in items:
            kind = "环境变量" if it.get('kind') == 'env' else "注册表"
            items_desc.append(f"[{kind}] 名称: {it.get('key')} | 当前取值: {it.get('value')}")
            
        prompt = (
            f"请作为 Windows 系统和运维专家，分析以下环境变量和注册表项：\n"
            f"{chr(10).join(items_desc)}\n\n"
            f"本地规则预检信息：\n{local_res.get('summary', '')}\n\n"
            f"请从以下几个方面给出专业评估：\n"
            f"1. 每个变量/注册表的作用和归属应用\n"
            f"2. 是否存在失效路径、空路径、冲突或冗余重复项\n"
            f"3. 安全性与稳定性影响（删除或修改的潜在风险）\n"
            f"4. 具体的优化与清理操作建议"
        )
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一位资深的 Windows 系统架构师与运维专家。请对用户提供的环境变量或注册表项进行专业分析，指出其中的安全隐患、性能问题、空路径/失效路径、冗余重复项，并给出具体修改或清理建议。语言简洁、排版优雅、分点说明。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3
        }
        
        try:
            req_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(endpoint, data=req_data, headers={'Content-Type': 'application/json'})
            if api_key:
                req.add_header('Authorization', f'Bearer {api_key}')
                
            with urllib.request.urlopen(req, timeout=25) as resp:
                resp_json = json.loads(resp.read().decode('utf-8'))
                choices = resp_json.get('choices', [])
                if choices and 'message' in choices[0]:
                    ai_content = choices[0]['message'].get('content', '')
                    return {
                        'model': model,
                        'suggestions': local_res.get('suggestions', []),
                        'summary': ai_content
                    }
        except urllib.error.HTTPError as e:
            err_msg = f"HTTP {e.code}: {e.reason}"
            try:
                err_detail = e.read().decode('utf-8')
                err_msg += f" - {err_detail[:120]}"
            except Exception:
                pass
            return {
                'model': model,
                'error': err_msg,
                'suggestions': local_res.get('suggestions', []),
                'summary': f"AI 接口请求失败 ({err_msg})。\n以下为本地规则分析结果：\n\n{local_res.get('summary', '')}"
            }
        except Exception as e:
            return {
                'model': model,
                'error': str(e),
                'suggestions': local_res.get('suggestions', []),
                'summary': f"调用大模型异常 ({e})。\n以下为本地规则分析结果：\n\n{local_res.get('summary', '')}"
            }
            
        return local_res

    def _http_analyze(self, items: List[Dict[str, Any]], mdef: Dict[str, Any]) -> Dict[str, Any]:
        """原生自定义 HTTP Webhook 格式"""
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
            with urllib.request.urlopen(req, timeout=15) as resp:
                res = resp.read().decode('utf-8')
                j = json.loads(res)
                if isinstance(j, dict):
                    return j
        except Exception as e:
            local = self._rule_analyze(items)
            local['error'] = str(e)
            return local
        return self._rule_analyze(items)
