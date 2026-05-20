from typing import Any, Dict, List

def safe_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(safe_str(v) for v in value)
    return str(value)

def get_nested(d: Dict[str, Any], path: List[str], default=None):
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur
