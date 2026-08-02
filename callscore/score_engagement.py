"""What the prospect actually did.

Weighted composite. Echo is recorded elsewhere and never summed in (Decision 6): the moment
it counts, reps fish for it and the signal dies.
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

    return {"score": round(sum(parts.values())), "components": {k: round(v, 1) for k, v in parts.items()},
            "next_step_level": lvl}
