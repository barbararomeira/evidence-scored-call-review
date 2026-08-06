"""Where a call gained the room, and where it lost it.

A score tells you what was said. This tells you what it *did* — which parts of the message earn
a reaction and which are followed by silence. It is derived from the transcript and the call
record together, deterministically: no model, no extra pass, nothing to configure.

- **Lift** — the buyer says something substantive immediately after an element lands.
- **Drop** — the rep runs three or more turns with no buyer input, or the buyer deflects.

Neither changes any score. They are the diagnosis behind the number, and the thing a rep can
actually act on: "the differentiator earns questions, the durability claim is where the room
goes quiet" is useful. "You scored 4 of 6" is not.
"""
from __future__ import annotations

import re

DEFLECTIONS = ("send me", "have a look", "not a priority", "let me think",
               "come back to", "circle back", "not sure where it fits")
MONOLOGUE_TURNS = 3


def _turns(body: str) -> list:
    out = []
    for line in body.splitlines():
        line = line.strip()
        m = re.match(r"^(REP|PROSPECT):\s*(.*)$", line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def _substantive(text: str) -> bool:
    return "?" in text or len(text.split()) >= 8


def analyse(record: dict, body: str) -> dict:
    """Return {'lifts': [...], 'drops': [...]}, each entry tagged with the element in play."""
    turns = _turns(body)
    lifts, drops = [], []

    # An element lands, and the buyer immediately says something real → lift.
    for element, v in record.get("adherence", {}).items():
        if v.get("status") != "delivered" or not v.get("quote"):
            continue
        needle = v["quote"].lower()[:60]
        for i, (who, text) in enumerate(turns):
            if who != "REP" or needle not in text.lower():
                continue
            for who2, text2 in turns[i + 1:i + 3]:
                if who2 == "PROSPECT" and _substantive(text2):
                    lifts.append({"element": element, "quote": text2})
                    break
            break

    # Long stretches with no buyer input, and explicit deflections → drop.
    run, run_start = 0, None
    for i, (who, text) in enumerate(turns):
        if who == "REP":
            run += 1
            run_start = run_start if run_start is not None else i
        else:
            if run >= MONOLOGUE_TURNS:
                drops.append({"element": _element_in_play(record, turns, run_start, i),
                              "why": f"{run} rep turns with no buyer input"})
            run, run_start = 0, None
            if any(d in text.lower() for d in DEFLECTIONS):
                drops.append({"element": None, "why": f'buyer deflected: "{text[:60]}"'})
    if run >= MONOLOGUE_TURNS:
        drops.append({"element": _element_in_play(record, turns, run_start, len(turns)),
                      "why": f"{run} rep turns with no buyer input"})
    return {"lifts": lifts, "drops": drops}


def _element_in_play(record: dict, turns: list, start: int, end: int) -> str | None:
    """Which element was being delivered during a monologue, if any."""
    said = [t[1].lower() for t in turns[start:end]]
    last, last_at = None, -1
    for element, v in record.get("adherence", {}).items():
        if v.get("status") != "delivered" or not v.get("quote"):
            continue
        needle = v["quote"].lower()[:40]
        for i, line in enumerate(said):
            if needle in line and i > last_at:
                last, last_at = element, i
    return last


def roll_up(rows: list) -> dict:
    """Aggregate lifts and drops per element across many calls."""
    tally: dict = {}
    for r in rows:
        d = r.get("dynamics") or {}
        for ev in d.get("lifts", []):
            tally.setdefault(ev["element"], {"lifts": 0, "drops": 0})["lifts"] += 1
        for ev in d.get("drops", []):
            if ev["element"]:
                tally.setdefault(ev["element"], {"lifts": 0, "drops": 0})["drops"] += 1
    return tally
