from __future__ import annotations

import time
from datetime import datetime, timedelta

from .state import StateManager


def normalize_positive_int(value, default=1):
    try:
        value = int(value)
    except Exception:
        return default
    return value if value > 0 else default


def normalize_non_negative_int(value, default=0):
    try:
        value = int(value)
    except Exception:
        return default
    return value if value >= 0 else default


def format_hms(seconds):
    if seconds is None:
        return "-"
    seconds = max(0, int(round(seconds)))
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_timestamp(ts):
    if not ts:
        return "-"
    return datetime.fromtimestamp(ts).strftime("%H:%M:%S")


def format_wallclock_from_now(seconds):
    if seconds is None:
        return "-"
    when = datetime.now() + timedelta(seconds=max(0, int(seconds)))
    return when.strftime("%H:%M:%S")


def live_countdown(seconds: int, label: str, state_manager: StateManager, update_interval_seconds: int) -> None:
    seconds = normalize_non_negative_int(seconds, 0)
    update_interval_seconds = normalize_positive_int(update_interval_seconds, 1)

    if seconds <= 0:
        return

    end_time = time.time() + seconds
    while True:
        remaining = max(0.0, end_time - time.time())
        state_manager.set_wait(label, seconds, remaining)
        state_manager.set_status(action=f"{label} | remaining {format_hms(remaining)}")
        if remaining <= 0:
            break
        time.sleep(min(update_interval_seconds, remaining))
    state_manager.clear_wait()


def controlled_sleep(seconds: int, reason: str, state_manager: StateManager, update_interval_seconds: int) -> None:
    seconds = normalize_non_negative_int(seconds, 0)
    update_interval_seconds = normalize_positive_int(update_interval_seconds, 1)

    if seconds <= 0:
        return

    end_time = time.time() + seconds
    while True:
        remaining = max(0.0, end_time - time.time())
        state_manager.set_wait(reason, seconds, remaining)
        state_manager.set_status(action=f"{reason} | remaining {format_hms(remaining)}")
        if remaining <= 0:
            break
        time.sleep(min(update_interval_seconds, remaining))
    state_manager.clear_wait()
