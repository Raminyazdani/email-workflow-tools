from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


def ensure_dir(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def clean_list(values: list[Any] | None) -> list[Any]:
    if not values:
        return []
    return [value for value in values if value not in (None, "")]


_EMPTY_DICT_VALUES = (None, "", [], {})


def clean_dict(values: dict[str, Any] | None) -> dict[str, Any]:
    if not values:
        return {}
    return {key: value for key, value in values.items() if key and value not in _EMPTY_DICT_VALUES}


def timestamped_name(prefix: str, suffix: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{stamp}{suffix}"
