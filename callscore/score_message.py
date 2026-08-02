"""How much of the message was delivered.

Score = delivered / applicable. No weights, no penalties — six yes/no checks (Decision 5).
`framing_pair` is reported separately because coverage scoring is structurally blind to it
(Decision 7): every promise can land while the frame around them is the old pitch.
"""
from __future__ import annotations

from .config import message_rubric

def score(adherence: dict) -> dict:
    rubric = message_rubric()
    ids = [e["id"] for e in rubric["elements"]]
    applicable = [i for i in ids if adherence.get(i, {}).get("status") in ("delivered", "absent")]
    delivered = [i for i in applicable if adherence[i]["status"] == "delivered"]

    pair_ids = rubric["framing_pair"]["elements"]
    pair = all(adherence.get(i, {}).get("status") == "delivered" for i in pair_ids)

    return {
        "delivered": len(delivered),
        "applicable": len(applicable),
        "score": round(len(delivered) / len(applicable) * 100) if applicable else None,
        "framing_pair": pair,
        "missing": [i for i in applicable if i not in delivered],
    }
