from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .utils import clean_dict, clean_list, ensure_dir


@dataclass(slots=True)
class BrowserConfig:
    start_url: str = ""
    user_data_dir_name: str = ""
    profile_directory: str = ""
    arguments: list[str] = field(default_factory=list)
    prefs: dict[str, Any] = field(default_factory=dict)
    experimental_options: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PathsConfig:
    download_dir_name: str = "downloads"
    artifacts_dir_name: str = "artifacts"


@dataclass(slots=True)
class TimeoutsConfig:
    implicit: float = 0
    page_load: float = 30
    script: float = 30


@dataclass(slots=True)
class StepSetup:
    step_file: Path
    config_file: Path
    project_root: Path
    browser: BrowserConfig
    paths: PathsConfig
    timeouts: TimeoutsConfig
    user_data_dir: Path
    download_dir: Path
    artifacts_dir: Path
    raw_config: dict[str, Any]


class ConfigError(RuntimeError):
    pass


def resolve_step_config_path(step_file: str | Path) -> Path:
    step_path = Path(step_file).resolve()
    return step_path.with_name(f"{step_path.stem}_config.json")


def load_step_setup(step_file: str | Path) -> StepSetup:
    step_path = Path(step_file).resolve()
    if not step_path.exists():
        raise FileNotFoundError(f"Step script not found: {step_path}")

    config_path = resolve_step_config_path(step_path)
    if not config_path.exists():
        raise FileNotFoundError(
            f"Config file not found for step script '{step_path.name}': {config_path.name}"
        )

    raw = _read_json(config_path)
    browser = _parse_browser_config(raw.get("browser"), step_path)
    paths = _parse_paths_config(raw.get("paths"))
    timeouts = _parse_timeouts_config(raw.get("timeouts"))

    project_root = step_path.parent
    user_data_dir = _resolve_dir(project_root, browser.user_data_dir_name)
    download_dir = ensure_dir(project_root / paths.download_dir_name)
    artifacts_dir = ensure_dir(project_root / paths.artifacts_dir_name)

    return StepSetup(
        step_file=step_path,
        config_file=config_path,
        project_root=project_root,
        browser=browser,
        paths=paths,
        timeouts=timeouts,
        user_data_dir=user_data_dir,
        download_dir=download_dir,
        artifacts_dir=artifacts_dir,
        raw_config=raw,
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path.name}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"Top-level config in {path.name} must be a JSON object.")
    return data


def _parse_browser_config(raw: Any, step_path: Path) -> BrowserConfig:
    raw = raw or {}
    if not isinstance(raw, dict):
        raise ConfigError("'browser' must be a JSON object.")

    default_user_data_name = f"{step_path.stem}_user_data"

    return BrowserConfig(
        start_url=_as_text(raw.get("start_url", "")),
        user_data_dir_name=_as_text(raw.get("user_data_dir_name", default_user_data_name)) or default_user_data_name,
        profile_directory=_as_text(raw.get("profile_directory", "")),
        arguments=[str(value) for value in clean_list(raw.get("arguments"))],
        prefs=clean_dict(raw.get("prefs")),
        experimental_options=clean_dict(raw.get("experimental_options")),
    )


def _parse_paths_config(raw: Any) -> PathsConfig:
    raw = raw or {}
    if not isinstance(raw, dict):
        raise ConfigError("'paths' must be a JSON object.")

    download_dir_name = _as_text(raw.get("download_dir_name", "downloads")) or "downloads"
    artifacts_dir_name = _as_text(raw.get("artifacts_dir_name", "artifacts")) or "artifacts"

    return PathsConfig(
        download_dir_name=download_dir_name,
        artifacts_dir_name=artifacts_dir_name,
    )


def _parse_timeouts_config(raw: Any) -> TimeoutsConfig:
    raw = raw or {}
    if not isinstance(raw, dict):
        raise ConfigError("'timeouts' must be a JSON object.")

    return TimeoutsConfig(
        implicit=_as_number(raw.get("implicit", 0), "timeouts.implicit"),
        page_load=_as_number(raw.get("page_load", 30), "timeouts.page_load"),
        script=_as_number(raw.get("script", 30), "timeouts.script"),
    )


def _as_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _as_number(value: Any, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"'{field_name}' must be a number.") from exc

    if number < 0:
        raise ConfigError(f"'{field_name}' cannot be negative.")
    return number
def _resolve_dir(base: Path, value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / value
    return ensure_dir(path)