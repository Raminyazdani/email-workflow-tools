from __future__ import annotations

import threading
from typing import List, Protocol

from .config import AutomationConfig
from .repository import PromptRepository
from .state import StateManager
from .timing import (
    live_countdown,
    controlled_sleep,
    normalize_non_negative_int,
    normalize_positive_int,
)


class TemplateCycleStrategy(Protocol):
    def execute_template_cycle(self, content: str, prompt_name: str) -> None: ...


class FullPipelineRunner:
    def __init__(
        self,
        config: AutomationConfig,
        state_manager: StateManager,
        repository: PromptRepository,
        tab_strategy: TemplateCycleStrategy,
    ):
        self.config = config
        self.state_manager = state_manager
        self.repository = repository
        self.tab_strategy = tab_strategy
        self.execution_lock = threading.Lock()

    def try_enter_workflow(self, workflow_name: str) -> bool:
        if not self.config.safety.block_parallel_workflows:
            return True

        acquired = self.execution_lock.acquire(blocking=False)
        if not acquired:
            self.state_manager.log_event(
                f"Cannot start '{workflow_name}': another workflow is already running."
            )
            return False
        return True

    def leave_workflow(self) -> None:
        if self.config.safety.block_parallel_workflows and self.execution_lock.locked():
            self.execution_lock.release()

    def reload_pending_safe(self) -> None:
        if self.state_manager.is_workflow_running():
            self.state_manager.log_event("Reload skipped: workflow is currently running.")
            return
        self.repository.reload_pending_into_state(self.state_manager)

    def build_bursts(self, files: List[str]) -> List[List[str]]:
        first_burst_size = normalize_positive_int(self.config.burst.first_burst_size, 1)
        next_burst_size = normalize_positive_int(self.config.burst.next_burst_size, 1)

        files = list(files)
        total_files = len(files)

        if total_files == 0:
            return []

        if not self.config.burst.enable_burst_mode:
            return [files]

        bursts = []
        current_index = 0
        burst_counter = 0

        while current_index < total_files:
            burst_counter += 1
            current_size = first_burst_size if burst_counter == 1 else next_burst_size
            end_index = min(current_index + current_size, total_files)

            if end_index <= current_index:
                end_index = current_index + 1

            bursts.append(files[current_index:end_index])
            current_index = end_index

        return bursts

    def estimate_one_duplicate_send_seconds(self) -> float:
        t = self.config.timing
        return (
                t.wait_after_duplicate_tab
                + t.wait_after_input_focus
                + t.wait_after_slash_command_typed
                + t.wait_after_slash_command_enter
                + t.time_sleep
                + t.wait_after_paste
                + t.wait_after_send
                + t.wait_after_switch_tab
                + getattr(
            t,
            "url_change_wait_window_seconds",
            getattr(t, "wait_before_capture_url", 0.0),
        )
                + getattr(t, "wait_after_copy_url", 0.0)
                + getattr(t, "wait_after_close_tab", 0.0)
                + t.estimated_extra_action_overhead_seconds
        )

    def estimate_full_pipeline_seconds_from_plan(self, plan_counts: List[int]) -> float:
        counts = [max(0, int(x)) for x in plan_counts if int(x) > 0]
        if not counts:
            return 0.0

        total = float(self.config.timing.initial_countdown_seconds)
        send_seconds = self.estimate_one_duplicate_send_seconds()
        between_items = max(0, self.config.timing.wait_between_items_in_burst_seconds)
        after_burst = max(0, self.config.timing.wait_after_burst_seconds)

        for count in counts:
            total += count * send_seconds
            if count > 1:
                total += (count - 1) * between_items

        if len(counts) > 1:
            total += (len(counts) - 1) * after_burst

        return total

    def estimate_remaining_seconds_from_snapshot(self, snapshot) -> float:
        active_wait_remaining = max(0.0, snapshot["active_wait_remaining_seconds"])
        plan = [int(x) for x in snapshot["pending_burst_plan"] if int(x) > 0]

        if snapshot["current_mode"] == "full_pipeline":
            send_seconds = self.estimate_one_duplicate_send_seconds()
            between_items = max(0, self.config.timing.wait_between_items_in_burst_seconds)
            after_burst = max(0, self.config.timing.wait_after_burst_seconds)

            remaining = active_wait_remaining

            for count in plan:
                remaining += count * send_seconds
                if count > 1:
                    remaining += (count - 1) * between_items

            if len(plan) > 1:
                remaining += (len(plan) - 1) * after_burst

            return remaining

        return 0.0

    def process_burst(self, files: List[str], burst_number: int, total_bursts: int) -> None:
        wait_between_items = normalize_non_negative_int(
            self.config.timing.wait_between_items_in_burst_seconds,
            0,
        )
        burst_size = len(files)

        self.state_manager.set_status(
            status="Running",
            action=f"Starting burst {burst_number}/{total_bursts}",
            prompt="-",
        )
        self.state_manager.log_event(
            f"Starting burst {burst_number}/{total_bursts} | items={burst_size}"
        )

        for item_index, file_name in enumerate(files, start=1):
            self.state_manager.set_burst_position(burst_number, burst_size, item_index)
            self.state_manager.set_status(
                status="Running",
                action=f"Burst {burst_number}/{total_bursts} | item {item_index}/{burst_size}",
                prompt=file_name,
            )

            content = self.repository.read_prompt_file(file_name)
            self.tab_strategy.execute_template_cycle(content, file_name)

            self.state_manager.mark_item_sent(file_name)
            self.state_manager.log_event(f"Prompt sent: {file_name}")

            is_last_item_in_burst = item_index == burst_size
            if not is_last_item_in_burst and wait_between_items > 0:
                controlled_sleep(
                    wait_between_items,
                    f"Waiting between items in burst {burst_number}",
                    self.state_manager,
                    self.config.timing.rich_wait_update_interval_seconds,
                )

        self.state_manager.drop_finished_leading_bursts()
        self.state_manager.log_event(f"Burst {burst_number}/{total_bursts} finished.")

    def run_full_pipeline(self) -> None:
        if not self.try_enter_workflow("full_pipeline"):
            return

        try:
            pending = self.repository.reload_pending_into_state(self.state_manager)
            if not pending:
                self.state_manager.log_event("No pending prompt files found.")
                return

            files = list(pending)
            bursts = self.build_bursts(files)
            burst_plan = [len(b) for b in bursts]
            total_bursts = len(bursts)
            wait_after_burst = normalize_non_negative_int(
                self.config.timing.wait_after_burst_seconds,
                0,
            )

            estimated_total_seconds = self.estimate_full_pipeline_seconds_from_plan(
                burst_plan
            )
            self.state_manager.start_session(
                "full_pipeline",
                len(files),
                burst_plan,
                estimated_total_seconds,
            )

            self.state_manager.log_event(
                f"Full pipeline started | files={len(files)} | bursts={burst_plan}"
            )

            live_countdown(
                self.config.timing.initial_countdown_seconds,
                "Full pipeline starts",
                self.state_manager,
                self.config.timing.rich_wait_update_interval_seconds,
            )

            for burst_index, burst_files in enumerate(bursts, start=1):
                self.process_burst(burst_files, burst_index, total_bursts)

                is_last_burst = burst_index == total_bursts
                if not is_last_burst and wait_after_burst > 0:
                    controlled_sleep(
                        wait_after_burst,
                        f"Waiting after burst {burst_index}/{total_bursts}",
                        self.state_manager,
                        self.config.timing.rich_wait_update_interval_seconds,
                    )

            self.state_manager.log_event("Full pipeline finished.")
        except Exception as exc:
            self.state_manager.mark_error(exc)
        finally:
            self.state_manager.finish_session()
            self.leave_workflow()
