from __future__ import annotations

import time
from datetime import datetime

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.progress_bar import ProgressBar
from rich.rule import Rule

from .config import AutomationConfig
from .repository import PromptRepository
from .state import StateManager
from .timing import format_hms, format_timestamp, format_wallclock_from_now
from .pipeline import FullPipelineRunner


class DashboardBuilder:
    def __init__(
        self,
        config: AutomationConfig,
        state_manager: StateManager,
        repository: PromptRepository,
        pipeline_runner: FullPipelineRunner,
    ):
        self.config = config
        self.state_manager = state_manager
        self.repository = repository
        self.pipeline_runner = pipeline_runner

    def build_header_panel(self, snapshot, disk_counts, pending_files_snapshot):
        header = Table.grid(expand=True)
        header.add_column(justify="left", ratio=3)
        header.add_column(justify="center", ratio=2)
        header.add_column(justify="right", ratio=3)

        left_text = Text()
        left_text.append(self.config.ui.title, style="bold cyan")
        left_text.append("\n")
        left_text.append(f"Mode: {snapshot['current_mode']}", style="bold white")
        left_text.append("  |  ")
        left_text.append(
            f"Status: {snapshot['current_status']}",
            style="bold green" if snapshot["workflow_running"] else "bold yellow",
        )

        center_text = Text()
        center_text.append("Now\n", style="bold magenta")
        center_text.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="bold white")

        if snapshot["workflow_running"] and snapshot["session_total_files"] > 0:
            live_total = snapshot["session_total_files"]
            live_done = snapshot["session_processed_files"]
            live_pending = max(0, live_total - live_done)

            right_text = Text()
            right_text.append("Files (live session)\n", style="bold blue")
            right_text.append(
                f"Total: {live_total} | Done: {live_done} | Pending: {live_pending}",
                style="bold white",
            )
        else:
            right_text = Text()
            right_text.append("Files (disk state)\n", style="bold blue")
            right_text.append(
                f"Total: {disk_counts['total_prompt_files']} | "
                f"Done: {disk_counts['done_outputs']} | "
                f"Pending: {disk_counts['pending_files']}",
                style="bold white",
            )

        header.add_row(left_text, center_text, right_text)
        return Panel(header, border_style="bright_blue")

    def build_overview_panel(self, snapshot):
        table = Table(expand=True, box=None, show_header=False, pad_edge=False)
        table.add_column("k", style="bold cyan", width=22)
        table.add_column("v", style="white")

        table.add_row("Current action", snapshot["current_action"])
        table.add_row("Current prompt", snapshot["current_prompt_name"])
        table.add_row(
            "Current burst",
            f"{snapshot['session_current_burst']}/{snapshot['session_total_bursts']}"
            if snapshot["session_total_bursts"]
            else "-",
        )
        table.add_row(
            "Item in burst",
            f"{snapshot['session_current_item_in_burst']}/{snapshot['session_current_burst_size']}"
            if snapshot["session_current_burst_size"]
            else "-",
        )
        table.add_row(
            "Processed files",
            f"{snapshot['session_processed_files']}/{snapshot['session_total_files']}",
        )
        table.add_row(
            "Pending burst plan",
            " | ".join(str(x) for x in snapshot["pending_burst_plan"])
            if snapshot["pending_burst_plan"]
            else "-",
        )
        table.add_row("Input focus mode", self.config.input.input_focus_mode)
        table.add_row("Tab strategy", self.config.input.duplicate_tab_strategy_name)
        table.add_row("Last error", snapshot["last_error"])

        return Panel(table, title="Overview", border_style="cyan")

    def build_timing_panel(self, snapshot):
        now = time.time()
        elapsed = (now - snapshot["session_started_at"]) if snapshot["session_started_at"] else 0.0
        remaining = self.pipeline_runner.estimate_remaining_seconds_from_snapshot(snapshot)
        eta_finish = format_wallclock_from_now(remaining) if snapshot["workflow_running"] else "-"
        estimated_total = (
            snapshot["session_estimated_total_seconds"]
            if snapshot["current_mode"] == "full_pipeline"
            else 0.0
        )

        table = Table(expand=True, box=None, show_header=False, pad_edge=False)
        table.add_column("k", style="bold magenta", width=24)
        table.add_column("v", style="white")

        table.add_row("Elapsed", format_hms(elapsed))
        table.add_row("Estimated remaining", format_hms(remaining))
        table.add_row("ETA finish", eta_finish)
        table.add_row("Estimated total", format_hms(estimated_total) if estimated_total else "-")
        table.add_row("Active wait", snapshot["active_wait_label"])
        table.add_row("Active wait remaining", format_hms(snapshot["active_wait_remaining_seconds"]))
        table.add_row("Last session mode", snapshot["last_session_mode"])
        table.add_row("Last session duration", format_hms(snapshot["last_session_duration_seconds"]))
        table.add_row("Last session finished", format_timestamp(snapshot["last_session_finished_at"]))

        return Panel(table, title="Timing", border_style="magenta")

    def build_progress_panel(self, snapshot):
        elapsed = 0.0
        if snapshot["session_started_at"]:
            elapsed = time.time() - snapshot["session_started_at"]

        remaining_estimate = self.pipeline_runner.estimate_remaining_seconds_from_snapshot(snapshot)
        session_total_display = snapshot["session_total_files"]
        session_total_bar = max(1, session_total_display)
        session_completed = min(snapshot["session_processed_files"], session_total_bar)

        session_bar = ProgressBar(
            total=session_total_bar,
            completed=session_completed,
            width=36,
        )

        table = Table(expand=True, box=None, show_header=False, pad_edge=False)
        table.add_column("label", style="bold green", width=20)
        table.add_column("bar", width=38)
        table.add_column("count", justify="right", width=10)
        table.add_column("elapsed", justify="right", width=10)
        table.add_column("remaining", justify="right", width=10)

        table.add_row(
            "Session progress",
            session_bar,
            f"{snapshot['session_processed_files']}/{snapshot['session_total_files']}",
            format_hms(elapsed),
            format_hms(remaining_estimate),
        )

        if snapshot["active_wait_total_seconds"] > 0:
            wait_total = max(1.0, snapshot["active_wait_total_seconds"])
            wait_completed = max(0.0, wait_total - snapshot["active_wait_remaining_seconds"])
            wait_bar = ProgressBar(total=wait_total, completed=wait_completed, width=36)

            table.add_row(
                "Active wait",
                wait_bar,
                f"{int(wait_completed)}/{int(wait_total)}",
                format_hms(elapsed),
                format_hms(snapshot["active_wait_remaining_seconds"]),
            )
        else:
            empty_wait_bar = ProgressBar(total=1, completed=0, width=36)
            table.add_row(
                "Active wait",
                empty_wait_bar,
                "-",
                format_hms(elapsed),
                "-",
            )

        return Panel(table, title="Progress", border_style="green")

    def build_queue_panel(self, pending_files_snapshot):
        table = Table(expand=True)
        table.add_column("#", style="bold yellow", width=4, justify="right")
        table.add_column("Pending prompt file", style="white")

        if pending_files_snapshot:
            for idx, file_name in enumerate(
                pending_files_snapshot[: self.config.ui.show_next_files],
                start=1,
            ):
                table.add_row(str(idx), file_name)
        else:
            table.add_row("-", "No pending files")

        return Panel(table, title="Next Pending Files", border_style="yellow")

    def build_logs_panel(self, snapshot):
        logs = snapshot["logs"] or ["No logs yet"]
        text = Text()
        for line in logs:
            text.append(line + "\n", style="white")
        return Panel(text, title="Recent Logs", border_style="bright_black")

    def build_hotkeys_panel(self):
        table = Table(expand=True, box=None, show_header=False, pad_edge=False)
        table.add_column("key", style="bold green", width=22)
        table.add_column("action", style="white")

        table.add_row(self.config.hotkeys.start_full_pipeline, "Start full pipeline")
        table.add_row(self.config.hotkeys.reload_pending, "Reload pending prompts")
        table.add_row(self.config.hotkeys.save_mouse_positions, "Save 2 mouse positions")
        table.add_row(self.config.hotkeys.emergency_terminate, "Emergency terminate")

        return Panel(table, title="Hotkeys", border_style="blue")

    def build_footer_panel(self):
        text = Text()
        text.append("Burst config: ", style="bold cyan")
        text.append(
            f"enabled={self.config.burst.enable_burst_mode}, "
            f"first={self.config.burst.first_burst_size}, "
            f"next={self.config.burst.next_burst_size}",
            style="white",
        )
        text.append("  |  ")
        text.append("Waits: ", style="bold magenta")
        text.append(
            f"between items={self.config.timing.wait_between_items_in_burst_seconds}s, "
            f"after burst={self.config.timing.wait_after_burst_seconds}s",
            style="white",
        )
        text.append("  |  ")
        text.append("Strategy: ", style="bold yellow")
        text.append(self.config.input.duplicate_tab_strategy_name, style="white")

        return Panel(text, border_style="bright_blue")

    def build(self):
        disk_counts = self.repository.disk_counts()
        pending_files_snapshot = self.state_manager.pending_snapshot()
        snapshot = self.state_manager.snapshot()

        header = self.build_header_panel(snapshot, disk_counts, pending_files_snapshot)

        top_row = Table.grid(expand=True)
        top_row.add_column(ratio=1)
        top_row.add_column(ratio=1)
        top_row.add_row(
            self.build_overview_panel(snapshot),
            self.build_timing_panel(snapshot),
        )

        middle_row = Table.grid(expand=True)
        middle_row.add_column(ratio=1)
        middle_row.add_column(ratio=1)
        middle_row.add_row(
            self.build_progress_panel(snapshot),
            self.build_queue_panel(pending_files_snapshot),
        )

        bottom_row = Table.grid(expand=True)
        bottom_row.add_column(ratio=1)
        bottom_row.add_column(ratio=1)
        bottom_row.add_row(
            self.build_logs_panel(snapshot),
            self.build_hotkeys_panel(),
        )

        body = Group(
            header,
            Rule(style="bright_black"),
            top_row,
            Rule(style="bright_black"),
            middle_row,
            Rule(style="bright_black"),
            bottom_row,
            Rule(style="bright_black"),
            self.build_footer_panel(),
        )

        return Align.left(body)
