import json
import re
from typing import Any

def parse_json(text: str):
    if not text or not text.strip():
        return None, "JSON input is empty."
    try:
        return json.loads(text), None
    except json.JSONDecodeError as e:
        line = e.lineno
        col = e.colno
        return None, f"JSONDecodeError: {e.msg} (line {line}, column {col})"

def validate_json(text: str):
    result = {
        "valid": False, "error": None, "line": None, "column": None,
        "data": None, "root_type": None, "characters": len(text or ""),
        "lines": len((text or "").splitlines()) if text else 0
    }
    try:
        data = json.loads(text)
        result.update(valid=True, data=data, root_type=type(data).__name__)
    except json.JSONDecodeError as e:
        result.update(error=f"{e.msg} (line {e.lineno}, column {e.colno})",
                      line=e.lineno, column=e.colno)
    return result

def format_json(obj: Any, indent=2, sort_keys=False, ensure_ascii=False):
    return json.dumps(obj, indent=indent, sort_keys=sort_keys,
                      ensure_ascii=ensure_ascii, default=str)

def minify_json(obj: Any, sort_keys=False, ensure_ascii=False):
    return json.dumps(obj, separators=(",", ":"), sort_keys=sort_keys,
                      ensure_ascii=ensure_ascii, default=str)

def json_stats(value):
    counts = {"objects": 0, "arrays": 0, "strings": 0, "numbers": 0,
              "booleans": 0, "nulls": 0, "max_depth": 0}

    def walk(v, depth=0):
        counts["max_depth"] = max(counts["max_depth"], depth)
        if isinstance(v, dict):
            counts["objects"] += 1
            for x in v.values(): walk(x, depth + 1)
        elif isinstance(v, list):
            counts["arrays"] += 1
            for x in v: walk(x, depth + 1)
        elif isinstance(v, bool):
            counts["booleans"] += 1
        elif isinstance(v, (int, float)):
            counts["numbers"] += 1
        elif isinstance(v, str):
            counts["strings"] += 1
        elif v is None:
            counts["nulls"] += 1

    walk(value)
    return counts

def _display(v):
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    if v is None:
        return "null"
    if isinstance(v, bool):
        return str(v).lower()
    return str(v)

def flatten_json(data):
    rows = []
    def walk(v, path="$"):
        if isinstance(v, dict):
            for k, value in v.items():
                walk(value, f"{path}.{k}" if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", str(k)) else f"{path}['{k}']")
        elif isinstance(v, list):
            for i, value in enumerate(v):
                walk(value, f"{path}[{i}]")
        else:
            rows.append([path, type(v).__name__, _display(v)])
    walk(data)
    return rows

def _tokenize(path):
    if path == "$":
        return []
    if not path.startswith("$"):
        raise ValueError("Path must start with $.")
    tokens = []
    i = 1
    while i < len(path):
        if path[i] == ".":
            i += 1
            m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", path[i:])
            if not m:
                raise ValueError("Invalid dot property.")
            tokens.append(m.group(0))
            i += len(m.group(0))
        elif path[i] == "[":
            end = path.find("]", i)
            if end == -1:
                raise ValueError("Missing ].")
            inside = path[i+1:end].strip()
            if inside.isdigit():
                tokens.append(int(inside))
            elif (inside.startswith("'") and inside.endswith("'")) or (
                inside.startswith('"') and inside.endswith('"')
            ):
                tokens.append(inside[1:-1])
            else:
                raise ValueError("Array indexes must be numeric or object keys must be quoted.")
            i = end + 1
        else:
            raise ValueError("Unexpected character in path.")
    return tokens

def jsonpath_query(data, path):
    try:
        tokens = _tokenize(path)
        value = data
        for token in tokens:
            if isinstance(token, int):
                if not isinstance(value, list) or token >= len(value):
                    return None, False, "Array index not found."
                value = value[token]
            else:
                if not isinstance(value, dict) or token not in value:
                    return None, False, f"Property '{token}' not found."
                value = value[token]
        return value, True, "OK"
    except (ValueError, TypeError) as e:
        return None, False, str(e)

def diff_json(a, b):
    changes = []
    def walk(x, y, path="$"):
        if type(x) != type(y):
            changes.append({"Path": path, "Change": "Type changed",
                            "Before": _display(x), "After": _display(y)})
            return
        if isinstance(x, dict):
            keys = sorted(set(x) | set(y), key=str)
            for k in keys:
                p = f"{path}.{k}" if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", str(k)) else f"{path}['{k}']"
                if k not in x:
                    changes.append({"Path": p, "Change": "Added", "Before": "", "After": _display(y[k])})
                elif k not in y:
                    changes.append({"Path": p, "Change": "Removed", "Before": _display(x[k]), "After": ""})
                else:
                    walk(x[k], y[k], p)
        elif isinstance(x, list):
            n = max(len(x), len(y))
            for i in range(n):
                p = f"{path}[{i}]"
                if i >= len(x):
                    changes.append({"Path": p, "Change": "Added", "Before": "", "After": _display(y[i])})
                elif i >= len(y):
                    changes.append({"Path": p, "Change": "Removed", "Before": _display(x[i]), "After": ""})
                else:
                    walk(x[i], y[i], p)
        elif x != y:
            changes.append({"Path": path, "Change": "Modified", "Before": _display(x), "After": _display(y)})
    walk(a, b)
    return changes
