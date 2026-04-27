import json
from pathlib import Path
from typing import Any, Dict, Optional


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def resolve_ground_truth_path(
    default_path: Path,
    override: Optional[Path] = None,
) -> Path:
    if override is not None and override.is_file():
        return override
    return default_path
