import os
import hashlib
from typing import List, Dict, Tuple

def normalize_path(p: str) -> str:
    """
    规整化 Windows 路径：
    去除首尾空白与包裹的双引号/单引号，展开环境变量引用，最后转为标准系统路径。
    """
    if not p:
        return ""
    cleaned = p.strip().strip('"').strip("'")
    if not cleaned:
        return ""
    expanded = os.path.expandvars(cleaned)
    return os.path.normpath(expanded)

def analyze_paths(path_string: str, separator: str = ';') -> List[Dict]:
    """
    分析 PATH 字符串中所有条目的状态：
    - is_empty: 是否为空条目（例如连续分号 ;; 或末尾分号）
    - exists: 目录是否存在于磁盘上（避免将空路径规整为 '.' 误报存在）
    - is_file: 是否错误地指向了具体文件而非目录
    - duplicate: 是否为重复条目（Windows 下大小写不敏感匹配）
    - shadowed: 是否因靠前的相同条目而被遮蔽
    """
    if not path_string:
        return []
    
    entries = path_string.split(separator)
    seen_normalized = {}  # normalized_lower -> first_seen_index
    result = []
    
    for idx, raw in enumerate(entries):
        raw_stripped = raw.strip()
        cleaned = raw_stripped.strip('"').strip("'")
        
        if not cleaned:
            # 空条目识别
            result.append({
                'index': idx,
                'raw': raw,
                'normalized': '',
                'exists': False,
                'is_empty': True,
                'is_file': False,
                'duplicate': False,
                'shadowed': False,
                'reason': '空路径（多余分号）'
            })
            continue
        
        n = normalize_path(raw)
        # Windows 文件系统对路径大小写不敏感
        n_folded = n.lower() if os.name == 'nt' else n
        
        duplicate = n_folded in seen_normalized
        shadowed = duplicate
        if not duplicate:
            seen_normalized[n_folded] = idx
            
        exists_dir = os.path.isdir(n)
        is_file = os.path.isfile(n)
        
        reason = '正常'
        if not exists_dir and not is_file:
            reason = '路径不存在'
        elif is_file:
            reason = '错误指向了文件而非目录'
        elif duplicate:
            reason = f'与第 {seen_normalized[n_folded]} 项重复'
            
        result.append({
            'index': idx,
            'raw': raw,
            'normalized': n,
            'exists': exists_dir,
            'is_empty': False,
            'is_file': is_file,
            'duplicate': duplicate,
            'shadowed': shadowed,
            'first_seen_index': seen_normalized.get(n_folded, idx),
            'reason': reason
        })
        
    return result

def rebuild_path(entries: List[str], separator: str = ';') -> str:
    """过滤空条目并重构 PATH 字符串"""
    filtered = [e.strip() for e in entries if e and isinstance(e, str) and e.strip()]
    return separator.join(filtered)

def clean_path_entries(
    entries: List[str],
    remove_invalid: bool = True,
    remove_duplicates: bool = True,
    remove_empty: bool = True
) -> Tuple[List[str], Dict[str, int]]:
    """
    一键清理 PATH 条目并返回统计信息
    """
    stats = {
        'removed_empty': 0,
        'removed_invalid': 0,
        'removed_duplicate': 0,
        'total_removed': 0
    }
    seen = set()
    cleaned = []
    
    for raw in entries:
        raw_stripped = raw.strip()
        cleaned_path = raw_stripped.strip('"').strip("'")
        
        if not cleaned_path:
            if remove_empty:
                stats['removed_empty'] += 1
                continue
            else:
                cleaned.append(raw)
                continue
                
        n = normalize_path(raw)
        n_folded = n.lower() if os.name == 'nt' else n
        
        if remove_duplicates and n_folded in seen:
            stats['removed_duplicate'] += 1
            continue
            
        if remove_invalid and not os.path.isdir(n):
            stats['removed_invalid'] += 1
            continue
            
        seen.add(n_folded)
        cleaned.append(raw)
        
    stats['total_removed'] = stats['removed_empty'] + stats['removed_invalid'] + stats['removed_duplicate']
    return cleaned, stats
