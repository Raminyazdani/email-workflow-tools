from __future__ import annotations

import sys
import time
import ctypes
from typing import Optional, Tuple

try:
    import keyboard as _keyboard
except Exception:
    _keyboard = None

try:
    import pyperclip as _pyperclip
except Exception:
    _pyperclip = None

try:
    from pynput import mouse as _pynput_mouse
except Exception:
    _pynput_mouse = None

from .config import AutomationConfig
from .state import StateManager
from .repository import PromptRepository


def _require_keyboard():
    if _keyboard is None:
        raise RuntimeError("Missing dependency: 'keyboard'. Install requirements.txt before running this launcher.")
    return _keyboard


def _require_pyperclip():
    if _pyperclip is None:
        raise RuntimeError("Missing dependency: 'pyperclip'. Install requirements.txt before running this launcher.")
    return _pyperclip


def _require_mouse_module():
    if _pynput_mouse is None:
        raise RuntimeError("Missing dependency: 'pynput'. Install requirements.txt before using mouse-based focus or mouse position capture.")
    return _pynput_mouse


def enable_windows_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class BrowserInputController:
    def __init__(self, config: AutomationConfig, state_manager: StateManager):
        self.config = config
        self.state_manager = state_manager
        self.mouse_position_1: Optional[Tuple[int, int]] = None
        self.mouse_position_2: Optional[Tuple[int, int]] = None

    def press_shortcut(self, shortcut: str, sleep_after: float = 0.0) -> None:
        keyboard = _require_keyboard()
        keyboard.press_and_release(shortcut)
        if sleep_after > 0:
            time.sleep(sleep_after)

    def type_text(self, text: str, sleep_after: float = 0.0) -> None:
        keyboard = _require_keyboard()
        keyboard.write(text)
        if sleep_after > 0:
            time.sleep(sleep_after)

    def copy_to_clipboard(self, text: str) -> None:
        pyperclip = _require_pyperclip()
        pyperclip.copy(text)
        time.sleep(self.config.timing.time_sleep)

    def remember_mouse_positions(self) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        mouse = _require_mouse_module()
        positions = []

        def on_click(x, y, button, pressed):
            if pressed:
                pos = (int(x), int(y))
                positions.append(pos)
                self.state_manager.log_event(f"Saved mouse position {len(positions)}: {pos}")
                if len(positions) >= 2:
                    return False

        self.state_manager.log_event("Click 2 positions with your mouse...")
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

        if len(positions) < 2:
            raise RuntimeError("Could not capture 2 mouse positions.")

        return positions[0], positions[1]

    def save_mouse_positions(self) -> None:
        if self.state_manager.is_workflow_running():
            self.state_manager.log_event("Save mouse positions skipped: workflow is currently running.")
            return

        try:
            self.mouse_position_1, self.mouse_position_2 = self.remember_mouse_positions()
            self.state_manager.log_event(
                f"Mouse positions saved: {self.mouse_position_1} | {self.mouse_position_2}"
            )
        except Exception as exc:
            self.state_manager.mark_error(exc)

    def focus_input_box(self) -> None:
        focus_mode = self.config.input.input_focus_mode
        timing = self.config.timing

        if focus_mode == "shortcut":
            self.state_manager.set_status(
                action=f"Focusing input via {self.config.input.input_focus_shortcut}"
            )
            self.press_shortcut(
                self.config.input.input_focus_shortcut,
                timing.wait_after_input_focus,
            )
            return

        mouse = _require_mouse_module()
        controller = mouse.Controller()

        if focus_mode == "mouse":
            if self.mouse_position_1 is None:
                raise RuntimeError("Mouse position 1 is not saved yet.")

            self.state_manager.set_status(
                action=f"Focusing input via mouse click at {self.mouse_position_1}"
            )
            controller.position = self.mouse_position_1
            time.sleep(timing.time_sleep)
            controller.click(mouse.Button.left, 1)
            time.sleep(timing.wait_after_input_focus)
            return

        if focus_mode == "mouse_double":
            if self.mouse_position_1 is None or self.mouse_position_2 is None:
                raise RuntimeError("Mouse positions are not saved yet.")

            self.state_manager.set_status(
                action=(
                    f"Focusing input via mouse clicks at "
                    f"{self.mouse_position_1} and {self.mouse_position_2}"
                )
            )
            controller.position = self.mouse_position_1
            time.sleep(timing.time_sleep)
            controller.click(mouse.Button.left, 1)
            time.sleep(timing.time_sleep)
            controller.position = self.mouse_position_2
            time.sleep(timing.time_sleep)
            controller.click(mouse.Button.left, 1)
            time.sleep(timing.wait_after_input_focus)
            return

        raise ValueError(f"Unknown INPUT_FOCUS_MODE: {focus_mode}")

    def duplicate_current_tab(self) -> None:
        self.state_manager.set_status(
            action=f"Duplicating current tab ({self.config.input.duplicate_tab_shortcut})"
        )
        self.press_shortcut(
            self.config.input.duplicate_tab_shortcut,
            self.config.timing.wait_after_duplicate_tab,
        )

    def switch_to_previous_tab(self) -> None:
        self.state_manager.set_status(
            action=(
                f"Switching back to previous/original tab "
                f"({self.config.input.previous_tab_shortcut})"
            )
        )
        self.press_shortcut(
            self.config.input.previous_tab_shortcut,
            self.config.timing.wait_after_switch_tab,
        )

    def switch_to_next_tab(self) -> None:
        self.state_manager.set_status(
            action=f"Switching to next tab ({self.config.input.next_tab_shortcut})"
        )
        self.press_shortcut(
            self.config.input.next_tab_shortcut,
            self.config.timing.wait_after_switch_tab,
        )

    def activate_web_mode(self) -> None:
        self.focus_input_box()
        self.state_manager.set_status(
            action=f"Typing slash command: {self.config.input.slash_command}"
        )
        self.type_text(
            self.config.input.slash_command,
            self.config.timing.wait_after_slash_command_typed,
        )
        self.state_manager.set_status(action="Confirming slash command")
        self.press_shortcut(
            self.config.input.send_shortcut,
            self.config.timing.wait_after_slash_command_enter,
        )

    def paste_prompt_only(self, content: str) -> None:
        self.state_manager.set_status(action="Copying prompt to clipboard")
        self.copy_to_clipboard(content)
        self.state_manager.set_status(
            action=f"Pasting prompt ({self.config.input.paste_shortcut})"
        )
        self.press_shortcut(
            self.config.input.paste_shortcut,
            self.config.timing.wait_after_paste,
        )

    def send_current_input(self) -> None:
        self.state_manager.set_status(action="Sending prompt")
        self.press_shortcut(
            self.config.input.send_shortcut,
            self.config.timing.wait_after_send,
        )

    def send_prompt_in_current_tab(self, content: str) -> None:
        self.activate_web_mode()
        self.paste_prompt_only(content)
        self.send_current_input()

    def copy_current_url(self) -> str:
        pyperclip = _require_pyperclip()
        self.state_manager.set_status(
            action=(
                f"Copying current URL ({self.config.input.focus_address_bar_shortcut} -> "
                f"{self.config.input.copy_selected_shortcut})"
            )
        )
        pyperclip.copy("")
        time.sleep(self.config.timing.time_sleep)
        self.press_shortcut(self.config.input.focus_address_bar_shortcut, self.config.timing.time_sleep)
        self.press_shortcut(self.config.input.copy_selected_shortcut, self.config.timing.wait_after_copy_url)
        copied = (pyperclip.paste() or "").strip()
        self.press_shortcut(self.config.input.escape_shortcut, self.config.timing.time_sleep)
        if not copied:
            raise RuntimeError("Copied browser URL is empty.")
        return copied

    def close_current_tab(self) -> None:
        self.state_manager.set_status(
            action=f"Closing current tab ({self.config.input.close_tab_shortcut})"
        )
        self.press_shortcut(
            self.config.input.close_tab_shortcut,
            self.config.timing.wait_after_close_tab,
        )


class TabSendStrategy:
    """
    Current strategy:
    1. duplicate current clean template tab
    2. browser is expected to activate the new duplicate
    3. switch back to the original tab
    4. send the prompt in the original tab
    5. switch forward to the clean duplicated tab for the next cycle
    """

    def __init__(self, config: AutomationConfig, state_manager: StateManager, controller: BrowserInputController):
        self.config = config
        self.state_manager = state_manager
        self.controller = controller

    def execute_template_cycle(self, content: str, prompt_name: str) -> None:
        self.state_manager.log_event(
            f"Template cycle start [{prompt_name}] | strategy={self.config.input.duplicate_tab_strategy_name}"
        )

        self.controller.duplicate_current_tab()
        self.state_manager.log_event(
            f"Assumption: duplicate created a new active adjacent tab for [{prompt_name}]"
        )

        self.controller.switch_to_previous_tab()
        self.state_manager.log_event(
            f"Assumption: previous-tab returned to original send target for [{prompt_name}]"
        )

        self.controller.send_prompt_in_current_tab(content)
        self.state_manager.log_event(f"Prompt typed and sent in original tab [{prompt_name}]")

        self.controller.switch_to_next_tab()
        self.state_manager.log_event(
            f"Assumption: next-tab moved onto clean duplicated template tab for [{prompt_name}]"
        )


class TabSendCaptureUrlCloseStrategy:
    """
    Variant strategy for step 8.

    Flow per item:
    1. duplicate the current clean template tab
    2. browser is expected to activate the new duplicate
    3. switch back to the original tab
    4. capture the current/original URL as baseline
    5. send the prompt in the original tab
    6. for up to N seconds, poll the current URL every M seconds
    7. if the URL changes, persist {prompt_file_name: url}
    8. if the URL does not change within the window, mark failure and continue
    9. close the current sent tab
    10. browser is expected to activate the clean duplicate automatically

    This keeps the old workflow shape while replacing the fixed sleep-based
    capture with change detection.
    """

    def __init__(
        self,
        config: AutomationConfig,
        state_manager: StateManager,
        controller: BrowserInputController,
        repository: PromptRepository,
    ):
        self.config = config
        self.state_manager = state_manager
        self.controller = controller
        self.repository = repository

    def _wait_for_url_change(self, baseline_url: str, prompt_name: str) -> str | None:
        wait_window = max(
            0.0,
            float(getattr(self.config.timing, "url_change_wait_window_seconds", 10.0)),
        )
        poll_interval = max(
            0.1,
            float(getattr(self.config.timing, "url_change_poll_interval_seconds", 1.0)),
        )

        if wait_window <= 0:
            try:
                current_url = self.controller.copy_current_url()
            except Exception as exc:
                self.state_manager.log_event(
                    f"URL check failed immediately [{prompt_name}] | error={exc}"
                )
                return None
            return current_url if current_url.strip() != baseline_url.strip() else None

        deadline = time.time() + wait_window
        check_index = 0

        while True:
            remaining = max(0.0, deadline - time.time())
            if remaining <= 0:
                break

            sleep_for = min(poll_interval, remaining)
            time.sleep(sleep_for)

            check_index += 1
            remaining_after_sleep = max(0.0, deadline - time.time())

            self.state_manager.set_status(
                action=(
                    f"Waiting for URL change [{prompt_name}] | "
                    f"check {check_index} | remaining {remaining_after_sleep:.1f}s"
                )
            )

            try:
                current_url = self.controller.copy_current_url()
            except Exception as exc:
                self.state_manager.log_event(
                    f"URL check failed [{prompt_name}] | check={check_index} | error={exc}"
                )
                continue

            if current_url.strip() != baseline_url.strip():
                return current_url

        return None

    def execute_template_cycle(self, content: str, prompt_name: str) -> None:
        self.state_manager.log_event(
            f"Template cycle start [{prompt_name}] | strategy=duplicate_back_send_wait_for_url_change_close"
        )

        self.controller.duplicate_current_tab()
        self.state_manager.log_event(
            f"Assumption: duplicate created a new active adjacent clean tab for [{prompt_name}]"
        )

        self.controller.switch_to_previous_tab()
        self.state_manager.log_event(
            f"Assumption: previous-tab returned to original send target for [{prompt_name}]"
        )

        try:
            baseline_url = self.controller.copy_current_url()
            self.state_manager.log_event(
                f"Baseline URL captured [{prompt_name}] -> {baseline_url}"
            )

            self.controller.send_prompt_in_current_tab(content)
            self.state_manager.log_event(
                f"Prompt typed and sent in original tab [{prompt_name}]"
            )

            changed_url = self._wait_for_url_change(baseline_url, prompt_name)

            if changed_url is not None:
                self.repository.record_prompt_url(prompt_name, changed_url)
                self.state_manager.log_event(
                    f"Detected changed URL for [{prompt_name}] -> {changed_url}"
                )
            else:
                wait_window = float(
                    getattr(self.config.timing, "url_change_wait_window_seconds", 10.0)
                )
                self.state_manager.mark_error(
                    f"URL change timeout [{prompt_name}] | baseline={baseline_url} | waited={wait_window:.1f}s"
                )

        except Exception as exc:
            self.state_manager.mark_error(f"Per-item failure [{prompt_name}] | {exc}")

        finally:
            try:
                self.controller.close_current_tab()
                self.state_manager.log_event(
                    f"Assumption: closing sent tab activated the clean duplicated tab for [{prompt_name}]"
                )
            except Exception as close_exc:
                self.state_manager.mark_error(
                    f"Close-tab failure [{prompt_name}] | {close_exc}"
                )