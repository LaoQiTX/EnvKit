import os
import hashlib

def normalize_path(p: str) -> str:
    return os.path.normpath(os.path.expandvars(p.strip()))

def analyze_paths(path_string: str, separator: str = ';') -> list:
    entries = [e for e in path_string.split(separator) if e is not None]
    seen = {}
    result = []
    for idx, raw in enumerate(entries):
        n = normalize_path(raw)
        h = hashlib.sha1(n.encode('utf-8')).hexdigest()
        duplicate = h in seen
        exists = os.path.isdir(n)
        shadowed = False
        if not duplicate:
            seen[h] = idx
        else:
            shadowed = True
        result.append({'index': idx, 'raw': raw, 'normalized': n, 'exists': exists, 'duplicate': duplicate, 'shadowed': shadowed})
    return result

def rebuild_path(entries: list, separator: str = ';') -> str:
    filtered = [e for e in entries if e and isinstance(e, str)]
    return separator.join(filtered)
