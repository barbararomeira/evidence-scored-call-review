"""The tips register: what a rep was told, and whether it stuck.

A message check that raises a new tip every week and never checks the last one trains people
to ignore it. Tips here get a stable id and a status that is *derived from later calls*, never
self-reported and never guessed.

Deterministic by construction: the tip for a week is the element that rep missed most often in
it, and the status is whatever their later calls show. Same evidence, same tip, same status.
"""
from __future__ import annotations

ADOPTED, PARTIAL, NOT_YET, NO_EVIDENCE = "Adopted", "Partial", "Not yet", "No evidence yet"


def _missed_most(pitches: list) -> tuple:
    counts: dict = {}
    for r in pitches:
        for m in r["message"]["missing"]:
            counts[m] = counts.get(m, 0) + 1
    if not counts:
        return None, 0
    return max(counts.items(), key=lambda kv: kv[1])


def tip_id(week_label: str, rep: str, n: int = 1) -> str:
    return f"TIP-{week_label.replace(' ', '').upper()}-{rep.upper()}-{n:02d}"


def register(rep: str, earlier: list, later: list, week_label: str) -> list:
    """Tips raised from `earlier` calls, with status judged against `later` ones.

    Returns a list of dicts: id, element, raised (what they were told), status, evidence.
    """
    pitches = [r for r in earlier if r["message"]]
    if not pitches:
        return []
    element, missed = _missed_most(pitches)
    if not element:
        return []

    later_pitches = [r for r in later if r["message"]]
    landed = [r for r in later_pitches
              if r["record"]["adherence"][element]["status"] == "delivered"]

    if not later_pitches:
        status = NO_EVIDENCE
        evidence = "no pitch calls since — nothing to judge it on yet"
    elif len(landed) == len(later_pitches):
        status = ADOPTED
        where = landed[0]["account"]
        evidence = (f"landed in {'the one pitch since' if len(landed) == 1 else f'all {len(landed)} pitches since'}"
                    f" — {where} is the clearest")
    elif landed:
        status = PARTIAL
        evidence = f"landed in {len(landed)} of {len(later_pitches)} pitches since"
    else:
        status = NOT_YET
        evidence = f"still missing in all {len(later_pitches)} pitches since"

    return [{
        "id": tip_id(week_label, rep),
        "element": element,
        "missed_then": missed,
        "of_then": len(pitches),
        "status": status,
        "evidence": evidence,
    }]
