from __future__ import annotations

import os
import time
from pathlib import Path

from .config import load_config_from_json
from .state import StateManager
from .repository import PromptRepository
from .input_actions import (
    enable_windows_dpi_awareness,
    BrowserInputController,
    TabSendStrategy,
    TabSendCaptureUrlCloseStrategy,
)
from .pipeline import FullPipelineRunner
from .dashboard import DashboardBuilder


def emergency_terminate(state_manager: StateManager):
    try:
        state_manager.log_event("EMERGENCY TERMINATE requested.")
    finally:
        os._exit(1)


def run_dashboard_launcher(
    config_json_path: str | Path,
    strategy_name: str = "default",
) -> None:
    import keyboard
    from rich.console import Console
    from rich.live import Live

    config_json_path = Path(config_json_path)

    enable_windows_dpi_awareness()
    config = load_config_from_json(config_json_path)
    state_manager = StateManager(log_lines=config.ui.log_lines)
    repository = PromptRepository(config)
    repository.ensure_directories()
    repository.reload_pending_into_state(state_manager)

    controller = BrowserInputController(config, state_manager)

    if strategy_name == "default":
        tab_strategy = TabSendStrategy(config, state_manager, controller)
    elif strategy_name == "capture_url_close":
        tab_strategy = TabSendCaptureUrlCloseStrategy(config, state_manager, controller, repository)
    else:
        raise ValueError(f"Unknown strategy_name: {strategy_name}")

    pipeline_runner = FullPipelineRunner(config, state_manager, repository, tab_strategy)
    dashboard = DashboardBuilder(config, state_manager, repository, pipeline_runner)

    state_manager.log_event(
        f"Dashboard initialized from JSON config: {config_json_path} | strategy={strategy_name}"
    )

    keyboard.add_hotkey(
        config.hotkeys.start_full_pipeline,
        pipeline_runner.run_full_pipeline,
    )
    keyboard.add_hotkey(
        config.hotkeys.reload_pending,
        pipeline_runner.reload_pending_safe,
    )
    keyboard.add_hotkey(
        config.hotkeys.save_mouse_positions,
        controller.save_mouse_positions,
    )
    keyboard.add_hotkey(
        config.hotkeys.emergency_terminate,
        lambda: emergency_terminate(state_manager),
    )

    console = Console()

    with Live(
        dashboard.build(),
        console=console,
        refresh_per_second=config.ui.refresh_per_second,
        screen=config.ui.use_alternate_screen,
        transient=False,
    ) as live:
        try:
            while True:
                live.update(dashboard.build())
                time.sleep(1 / max(1, config.ui.refresh_per_second))
        except KeyboardInterrupt:
            state_manager.log_event("Exiting...")
