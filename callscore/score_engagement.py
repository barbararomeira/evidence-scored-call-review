"""What the prospect actually did.

Weighted composite, minus what they held back. Echo is recorded elsewhere and never summed in
(Decision 6): the moment it counts, reps fish for it and the signal dies.

The deduction exists because the first version could only go up (Decision 13). Positive moments
accumulated and nothing represented a "but", so a buyer who said three warm things and then
explained for twenty minutes why not came out as an engaged call. Reservations late in the call
count double, because that is where a call actually lands.
"""
from __future__ import annotations

from .config import engagement_rubric

def _bucket(count: int, buckets: dict) -> int:
    for label, pts in buckets.items():
        if label.endswith("+"):
            if count >= int(label[:-1]):
                return pts
        elif "-" in label:
            lo, hi = (int(x) for x in label.split("-"))
            if lo <= count <= hi:
                return pts
        elif count == int(label):
            return pts
    return 0

def score(engagement: dict, duration_min: int) -> dict:
    r = {c["id"]: c for c in engagement_rubric()["components"]}
    parts = {}

    lvl = engagement["next_step_reached"]["level"]
    parts["next_step_reached"] = lvl / 4 * r["next_step_reached"]["weight"]

    n = len(engagement.get("own_situations", []))
    scale = r["own_situations"]["scale"]
    parts["own_situations"] = scale["3+"] if n >= 3 else scale[str(n)]

    cap = r["excitement"]["cap"]
    per = r["excitement"]["weight"] / cap
    parts["excitement"] = min(len(engagement.get("excitement", [])), cap) * per

    bf = engagement["back_and_forth"]
    raw = bf["questions"] + bf["substantive_turns"]
    # Short-call rule: extrapolating a 9-minute logistics call to half an hour manufactures
    # engagement that was never there.
    count = raw if duration_min < 15 else bf["per_30min"]
    parts["back_and_forth"] = _bucket(count, r["back_and_forth"]["buckets"])

    positive = sum(parts.values())

    res = engagement.get("reservations", []) or []
    rr = engagement_rubric().get("reservations", {})
    each, cap = rr.get("points_each", 12), rr.get("max_deduction", 45)
    mult = rr.get("late_multiplier", 2.0)
    weight = sum(mult if (r or {}).get("late") else 1.0 for r in res)
    deduction = min(weight * each, cap)

    return {"score": max(0, round(positive - deduction)),
            "positive": round(positive),
            "deduction": round(deduction),
            "reservations": res,
            "components": {k: round(v, 1) for k, v in parts.items()},
            "next_step_level": lvl}
