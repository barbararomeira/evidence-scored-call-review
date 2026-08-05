"""Did the rep this call is filed under actually speak on it?

The gate exists because of a real failure. A call was booked on one rep's calendar — their name
was in the meeting title and the invitee list — and run by a colleague. The pipeline read the
name from the invite rather than from the transcript, credited both, and sent that rep a
coaching message about a call they were never on. It praised them for opening on the problem and
criticised them for missing the differentiator. Every sentence described someone else.

The lesson generalises past sales calls: **whoever the record says was there is metadata, and
metadata is a claim, not evidence.** Calendar invitations, ticket assignees, PR authors and
"reported by" fields all describe who was *supposed* to be involved. Only the artifact itself —
the transcript, the diff, the thread — shows who actually was.

So the rule is the same one the scorer already applies to every point it awards: no quote, no
credit. A rep with no turns in the transcript has said nothing to score and nothing to coach.
"""
from __future__ import annotations

import re

SPEAKER = re.compile(r"^([A-Z][A-Z _-]*[A-Z]|[A-Z]):", re.M)
REP_LABEL = "REP"


def speaking_turns(body: str) -> dict:
    """Count turns per speaker label, e.g. {'REP': 12, 'PROSPECT': 9, 'COLLEAGUE': 14}."""
    counts: dict = {}
    for line in body.splitlines():
        m = SPEAKER.match(line.strip())
        if m:
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    return counts


def rep_spoke(body: str) -> tuple[bool, int]:
    """(did the filed rep speak, how many turns)."""
    n = speaking_turns(body).get(REP_LABEL, 0)
    return n > 0, n


def check(rep: str, body: str) -> tuple[bool, str]:
    """Return (attributable, reason). False means: score nothing, coach nobody, from this call.

    Deliberately not a warning. A call the rep did not speak on cannot produce a fair number
    about them in either direction, so it must not reach the scorer at all.
    """
    spoke, n = rep_spoke(body)
    if spoke:
        return True, f"{n} speaking turns"
    others = ", ".join(f"{k} {v}" for k, v in sorted(speaking_turns(body).items())) or "nobody"
    return False, (
        f"filed under {rep}, who has no speaking turns — the call was carried by {others}. "
        "Booked on their calendar, run by someone else."
    )
