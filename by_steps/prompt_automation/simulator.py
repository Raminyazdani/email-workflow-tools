from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Step:
    action: str
    active_before: str
    active_after_expected: str
    assumption: str
    failure_mode: str


def simulate_duplicate_back_send_forward(start_tab: str = "T0") -> List[Step]:
    """
    Small reasoning aid that models the intended browser sequence for one item.
    This does not talk to the browser; it only documents the assumptions.
    """
    steps = [
        Step(
            action="duplicate_current_tab",
            active_before=start_tab,
            active_after_expected="T1 (new duplicated tab)",
            assumption="Duplicate shortcut opens a new adjacent active duplicated tab",
            failure_mode="Browser remains on original tab, or duplicate opens elsewhere",
        ),
        Step(
            action="switch_to_previous_tab",
            active_before="T1",
            active_after_expected=start_tab,
            assumption="Previous-tab goes back to the original tab",
            failure_mode="Previous-tab lands one tab behind the original",
        ),
        Step(
            action="send_prompt_in_current_tab",
            active_before=start_tab,
            active_after_expected=start_tab,
            assumption="Input focus and slash command behave correctly in the active tab",
            failure_mode="Prompt goes to wrong page element or wrong browser tab",
        ),
        Step(
            action="switch_to_next_tab",
            active_before=start_tab,
            active_after_expected="T1 (clean duplicated template tab)",
            assumption="Next-tab returns to the clean duplicate created at step 1",
            failure_mode="Next-tab lands one tab ahead or behind if earlier assumptions failed",
        ),
    ]
    return steps
