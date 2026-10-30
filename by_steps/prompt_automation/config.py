from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict


@dataclass
class PathConfig:
    prompts_folder_path: str = "./steps/step_2"
    output_folder_path: str = "./outputs/step_4"
    prompt_url_map_output_path: str = "./outputs/prompt_to_url_map.json"


@dataclass
class PatternConfig:
    prompt_file_pattern: str = r"prompt_(\d+)\.txt$"
    output_file_patterns: tuple = (
        r"output_step_4_(\d+)\.json$",
        r"group_(\d+)\.json$",
        r".*?(\d+)\.json$",
    )


@dataclass
class TimingConfig:
    time_sleep: float = 0.30
    initial_countdown_seconds: int = 5
    wait_after_duplicate_tab: float = 0.80
    wait_after_input_focus: float = 0.40
    wait_after_slash_command_typed: float = 0.30
    wait_after_slash_command_enter: float = 0.60
    wait_after_paste: float = 0.40
    wait_after_send: float = 0.50
    wait_after_switch_tab: float = 0.30

    # legacy / backward-compatible
    wait_before_capture_url: float = 1.50

    # new URL-change detection behavior
    url_change_wait_window_seconds: float = 10.0
    url_change_poll_interval_seconds: float = 1.0

    wait_after_copy_url: float = 0.20
    wait_after_close_tab: float = 0.40
    wait_between_items_in_burst_seconds: int = 10
    wait_after_burst_seconds: int = 600
    rich_wait_update_interval_seconds: int = 1
    estimated_extra_action_overhead_seconds: float = 0.50


@dataclass
class BurstConfig:
    enable_burst_mode: bool = True
    first_burst_size: int = 3
    next_burst_size: int = 5


@dataclass
class InputConfig:
    slash_command: str = "/web"
    input_focus_mode: str = "shortcut"  # shortcut | mouse | mouse_double

    duplicate_tab_shortcut: str = "ctrl+shift+k"
    previous_tab_shortcut: str = "ctrl+shift+tab"
    next_tab_shortcut: str = "ctrl+tab"
    input_focus_shortcut: str = "shift+esc"
    paste_shortcut: str = "ctrl+v"
    send_shortcut: str = "enter"
    focus_address_bar_shortcut: str = "ctrl+l"
    copy_selected_shortcut: str = "ctrl+c"
    escape_shortcut: str = "esc"
    close_tab_shortcut: str = "ctrl+w"

    duplicate_tab_strategy_name: str = "duplicate_new_active_tab_then_return_and_send"
    duplicate_switch_expectation: str = "new_duplicated_tab_becomes_active_and_is_adjacent"
    close_tab_switch_expectation: str = "closing_sent_tab_activates_clean_duplicate"


@dataclass
class HotkeyConfig:
    start_full_pipeline: str = "ctrl+alt+shift+f5"
    reload_pending: str = "ctrl+alt+shift+f6"
    emergency_terminate: str = "ctrl+alt+shift+f8"
    save_mouse_positions: str = "ctrl+alt+shift+f10"


@dataclass
class UIConfig:
    use_alternate_screen: bool = True
    refresh_per_second: int = 4
    log_lines: int = 10
    show_next_files: int = 8
    title: str = "Prompt Automation Dashboard"


@dataclass
class SafetyConfig:
    block_parallel_workflows: bool = True


@dataclass
class AutomationConfig:
    paths: PathConfig = field(default_factory=PathConfig)
    patterns: PatternConfig = field(default_factory=PatternConfig)
    timing: TimingConfig = field(default_factory=TimingConfig)
    burst: BurstConfig = field(default_factory=BurstConfig)
    input: InputConfig = field(default_factory=InputConfig)
    hotkeys: HotkeyConfig = field(default_factory=HotkeyConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    safety: SafetyConfig = field(default_factory=SafetyConfig)


def build_default_config() -> AutomationConfig:
    return AutomationConfig()


def config_to_dict(config: AutomationConfig) -> Dict[str, Any]:
    return asdict(config)


def build_config_from_dict(data: Dict[str, Any]) -> AutomationConfig:
    data = data or {}
    default = build_default_config()

    paths_data = data.get("paths", {}) or {}
    patterns_data = data.get("patterns", {}) or {}
    timing_data = data.get("timing", {}) or {}
    burst_data = data.get("burst", {}) or {}
    input_data = data.get("input", {}) or {}
    hotkeys_data = data.get("hotkeys", {}) or {}
    ui_data = data.get("ui", {}) or {}
    safety_data = data.get("safety", {}) or {}

    patterns_output = patterns_data.get(
        "output_file_patterns",
        default.patterns.output_file_patterns,
    )

    return AutomationConfig(
        paths=PathConfig(**{**asdict(default.paths), **paths_data}),
        patterns=PatternConfig(
            **{
                **asdict(default.patterns),
                **patterns_data,
                "output_file_patterns": tuple(patterns_output),
            }
        ),
        timing=TimingConfig(**{**asdict(default.timing), **timing_data}),
        burst=BurstConfig(**{**asdict(default.burst), **burst_data}),
        input=InputConfig(**{**asdict(default.input), **input_data}),
        hotkeys=HotkeyConfig(**{**asdict(default.hotkeys), **hotkeys_data}),
        ui=UIConfig(**{**asdict(default.ui), **ui_data}),
        safety=SafetyConfig(**{**asdict(default.safety), **safety_data}),
    )


def load_config_from_json(path: str | Path) -> AutomationConfig:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return build_config_from_dict(data)


def save_config_to_json(config: AutomationConfig, path: str | Path) -> None:
    path = Path(path)
    if path.parent:
        path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(config_to_dict(config), f, ensure_ascii=False, indent=2)
