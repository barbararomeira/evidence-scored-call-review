"""Decision 4: no quote, no credit — and no quote, no penalty either.

Requiring evidence only for positive verdicts produces a scorer that is rigorous about praise
and casual about blame, which is backwards for something a person is measured on.
"""
from __future__ import annotations


def normalise(s: str) -> str:
    return " ".join((s or "").lower().replace("\u2019", "'").split())

def quote_supported(quote: str | None, transcript: str) -> bool:
    """A verdict's quote must actually appear in the call it claims to come from."""
    if not quote:
        return False
    return normalise(quote) in normalise(transcript)

def verify(adherence: dict, transcript: str) -> list[str]:
    """Return human-readable problems. Empty list means every verdict is evidenced."""
    problems = []
    for key, v in adherence.items():
        status = v.get("status")
        if status in ("delivered", "absent"):
            if not v.get("quote"):
                problems.append(f"{key}: {status} with no quote")
            elif not quote_supported(v["quote"], transcript):
                problems.append(f"{key}: quote not found in the transcript")
    return problems
