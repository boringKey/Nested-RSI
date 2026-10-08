"""Small JSON receipt writer; callers choose their artifact directory."""
import json
from pathlib import Path


def write_json(path, value):
    if path is not None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
