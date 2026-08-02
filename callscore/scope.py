"""The scope gate.

Decision 3: a call that was never a pitch gets NO message score — not a zero. A score that is
always available and sometimes meaningless is worse than one that refuses to exist.
"""
from __future__ import annotations

from .config import scope_rules

PROMISES = ("promise_visibility", "promise_proactive", "promise_moat", "promise_durable")

def in_scope(call_type: str, adherence: dict | None = None) -> tuple[bool, str]:
    """Return (in_scope, reason). Call type decides; the promise heuristic is the backstop."""
    rules = scope_rules()
    if call_type in rules["out_of_scope"]:
        return False, rules["out_of_scope"][call_type]
    if adherence:
        na = sum(1 for k in PROMISES if adherence.get(k, {}).get("status") == "n/a")
        if na >= 3:
            return False, ("three or more promises not applicable — no product story was told, "
                           "so this was not a pitch")
    if call_type in rules["in_scope"]:
        return True, "pitch call"
    return True, f"unrecognised call type {call_type!r} — scored, but worth checking the rubric"
