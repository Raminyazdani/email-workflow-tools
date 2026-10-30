from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from collections import deque
from datetime import datetime
from typing import Deque, List, Optional, Dict, Any


@dataclass
class RunState:
    log_lines: int
    lock: threading.Lock = field(default_factory=threading.Lock)
    logs: Deque[str] = field(init=False)

    workflow_running: bool = False
    current_status: str = "Idle"
    current_action: str = "Waiting for hotkey"
    current_prompt_name: str = "-"
    current_mode: str = "idle"

    session_started_at: Optional[float] = None
    session_finished_at: Optional[float] = None
    session_total_files: int = 0
    session_processed_files: int = 0
    session_total_bursts: int = 0
    session_current_burst: int = 0
    session_current_burst_size: int = 0
    session_current_item_in_burst: int = 0
    session_estimated_total_seconds: float = 0.0

    pending_burst_plan: List[int] = field(default_factory=list)
    pending_prompt_queue: Deque[str] = field(default_factory=deque)

    active_wait_label: str = "-"
    active_wait_total_seconds: float = 0.0
    active_wait_remaining_seconds: float = 0.0

    last_session_mode: str = "-"
    last_session_duration_seconds: float = 0.0
    last_session_total_files: int = 0
    last_session_finished_at: Optional[float] = None

    last_error: str = "-"

    def __post_init__(self):
        self.logs = deque(maxlen=self.log_lines)


class StateManager:
    def __init__(self, log_lines: int):
        self.state = RunState(log_lines=log_lines)

    def log_event(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        with self.state.lock:
            self.state.logs.appendleft(f"[{timestamp}] {message}")

    def replace_pending_queue(self, file_names: List[str]) -> None:
        with self.state.lock:
            self.state.pending_prompt_queue = deque(file_names)
        self.log_event(f"Pending prompts reloaded: {len(file_names)}")

    def pending_snapshot(self) -> List[str]:
        with self.state.lock:
            return list(self.state.pending_prompt_queue)

    def is_workflow_running(self) -> bool:
        with self.state.lock:
            return self.state.workflow_running

    def set_status(self, status: Optional[str] = None, action: Optional[str] = None, prompt: Optional[str] = None) -> None:
        with self.state.lock:
            if status is not None:
                self.state.current_status = status
            if action is not None:
                self.state.current_action = action
            if prompt is not None:
                self.state.current_prompt_name = prompt

    def set_wait(self, label: str, total_seconds: float, remaining_seconds: float) -> None:
        with self.state.lock:
            self.state.active_wait_label = label
            self.state.active_wait_total_seconds = max(0.0, float(total_seconds))
            self.state.active_wait_remaining_seconds = max(0.0, float(remaining_seconds))

    def clear_wait(self) -> None:
        with self.state.lock:
            self.state.active_wait_label = "-"
            self.state.active_wait_total_seconds = 0.0
            self.state.active_wait_remaining_seconds = 0.0

    def start_session(self, mode: str, total_files: int, burst_plan: List[int], estimated_total_seconds: float) -> None:
        with self.state.lock:
            self.state.workflow_running = True
            self.state.current_mode = mode
            self.state.current_status = "Running"
            self.state.current_action = "Starting session"
            self.state.current_prompt_name = "-"
            self.state.session_started_at = time.time()
            self.state.session_finished_at = None
            self.state.session_total_files = total_files
            self.state.session_processed_files = 0
            self.state.session_total_bursts = len(burst_plan)
            self.state.session_current_burst = 0
            self.state.session_current_burst_size = 0
            self.state.session_current_item_in_burst = 0
            self.state.pending_burst_plan = list(burst_plan)
            self.state.active_wait_label = "-"
            self.state.active_wait_total_seconds = 0.0
            self.state.active_wait_remaining_seconds = 0.0
            self.state.last_error = "-"
            self.state.session_estimated_total_seconds = estimated_total_seconds

        self.log_event(f"Session started: {mode} | files={total_files}")

    def finish_session(self) -> None:
        with self.state.lock:
            finished_at = time.time()
            finished_mode = self.state.current_mode
            finished_total_files = self.state.session_total_files
            duration = 0.0

            if self.state.session_started_at:
                duration = finished_at - self.state.session_started_at

            self.state.workflow_running = False
            self.state.current_status = "Idle"
            self.state.current_action = "Waiting for hotkey"
            self.state.current_prompt_name = "-"
            self.state.current_mode = "idle"
            self.state.session_finished_at = finished_at

            self.state.last_session_mode = finished_mode
            self.state.last_session_duration_seconds = duration
            self.state.last_session_total_files = finished_total_files
            self.state.last_session_finished_at = finished_at

            self.state.session_total_files = 0
            self.state.session_processed_files = 0
            self.state.session_total_bursts = 0
            self.state.session_current_burst = 0
            self.state.session_current_burst_size = 0
            self.state.session_current_item_in_burst = 0
            self.state.session_estimated_total_seconds = 0.0
            self.state.pending_burst_plan = []
            self.state.session_started_at = None

        self.clear_wait()

    def set_burst_position(self, burst_idx: int, burst_size: int, item_idx: int) -> None:
        with self.state.lock:
            self.state.session_current_burst = burst_idx
            self.state.session_current_burst_size = burst_size
            self.state.session_current_item_in_burst = item_idx

    def mark_item_sent(self, file_name: str) -> None:
        with self.state.lock:
            self.state.session_processed_files += 1

            try:
                self.state.pending_prompt_queue.remove(file_name)
            except ValueError:
                pass

            if self.state.pending_burst_plan and self.state.pending_burst_plan[0] > 0:
                self.state.pending_burst_plan[0] -= 1

    def drop_finished_leading_bursts(self) -> None:
        with self.state.lock:
            while self.state.pending_burst_plan and self.state.pending_burst_plan[0] <= 0:
                self.state.pending_burst_plan.pop(0)

    def mark_error(self, message: Exception | str) -> None:
        with self.state.lock:
            self.state.last_error = str(message)
        self.log_event(f"ERROR: {message}")

    def snapshot(self) -> Dict[str, Any]:
        with self.state.lock:
            return {
                "workflow_running": self.state.workflow_running,
                "current_status": self.state.current_status,
                "current_action": self.state.current_action,
                "current_prompt_name": self.state.current_prompt_name,
                "current_mode": self.state.current_mode,
                "session_started_at": self.state.session_started_at,
                "session_finished_at": self.state.session_finished_at,
                "session_total_files": self.state.session_total_files,
                "session_processed_files": self.state.session_processed_files,
                "session_total_bursts": self.state.session_total_bursts,
                "session_current_burst": self.state.session_current_burst,
                "session_current_burst_size": self.state.session_current_burst_size,
                "session_current_item_in_burst": self.state.session_current_item_in_burst,
                "session_estimated_total_seconds": self.state.session_estimated_total_seconds,
                "pending_burst_plan": list(self.state.pending_burst_plan),
                "pending_prompt_queue": list(self.state.pending_prompt_queue),
                "active_wait_label": self.state.active_wait_label,
                "active_wait_total_seconds": self.state.active_wait_total_seconds,
                "active_wait_remaining_seconds": self.state.active_wait_remaining_seconds,
                "last_session_mode": self.state.last_session_mode,
                "last_session_duration_seconds": self.state.last_session_duration_seconds,
                "last_session_total_files": self.state.last_session_total_files,
                "last_session_finished_at": self.state.last_session_finished_at,
                "last_error": self.state.last_error,
                "logs": list(self.state.logs),
            }
