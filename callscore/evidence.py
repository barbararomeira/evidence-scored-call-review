"""Decision 4: no quote, no credit — and no quote, no penalty either.

Requiring evidence only for positive verdicts produces a scorer that is rigorous about praise
and casual about blame, which is backwards for something a person is measured on.

A quote also has to come from the right mouth (Decision 12). Checking only that a line appears
*somewhere* in the transcript lets the buyer's words score as the rep's delivery — which is
exactly the echo the rubric deliberately refuses to score, arriving through the back door. The
mirror holds too: engagement measures what the buyer did, so its evidence must be the buyer
talking, not the rep describing enthusiasm on their behalf.
"""
from __future__ import annotations

from .attribution import turns


def normalise(s: str) -> str:
    return " ".join((s or "").lower().replace("\u2019", "'").split())

def quote_supported(quote: str | None, transcript: str) -> bool:
    """A verdict's quote must actually appear in the call it claims to come from."""
    if not quote:
        return False
    return normalise(quote) in normalise(transcript)

def said_by(quote: str, transcript: str, speaker: str) -> bool:
    """Did `speaker` say this line, rather than it merely appearing in the call?"""
    q = normalise(quote)
    return any(who == speaker and q in normalise(text) for who, text in turns(transcript))


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
            elif status == "delivered" and not said_by(v["quote"], transcript, "REP"):
                problems.append(
                    f"{key}: delivered, but the quote is not something the rep said — "
                    "the buyer using your words is echo, not delivery")
    return problems


def verify_engagement(engagement: dict, transcript: str) -> list[str]:
    """Engagement is what the buyer did, so its evidence has to be the buyer talking."""
    problems = []
    for comp, v in (engagement or {}).items():
        for item in (v if isinstance(v, list) else [v]):
            if not isinstance(item, dict):
                continue
            q = item.get("quote")
            if not q:
                continue
            if not quote_supported(q, transcript):
                problems.append(f"engagement.{comp}: quote not found in the transcript")
            elif not said_by(q, transcript, "PROSPECT"):
                problems.append(
                    f"engagement.{comp}: evidence is not the buyer speaking — "
                    "engagement cannot be scored from the rep's own words")
    return problems
