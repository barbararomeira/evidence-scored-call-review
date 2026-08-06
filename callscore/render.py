"""Markdown and stdout rendering. No dependencies: markdown is what a message check is."""
from __future__ import annotations

from .config import expected_for


LABELS = {
    "problem_framing": "the problem", "category": "the category",
    "promise_visibility": "see what is happening", "promise_proactive": "be told, not go looking",
    "promise_moat": "what no other system can do", "promise_durable": "value that lasts",
}

def scored_table(rows: list) -> str:
    """Aligned terminal table. Columns are fixed width so nothing shifts when a call is refused."""
    H = f"{'call':<8}{'rep':<8}{'type':<12}{'message':>12}  {'framing':<9}{'engagement':>11}  {'echo':<5}"
    out = [H, "─" * len(H)]
    for r in rows:
        if r["message"] is None:
            msg, framing = "not a pitch", "—"
        else:
            m = r["message"]
            msg = f"{m['delivered']} of 6"
            framing = "yes" if m["framing_pair"] else "no"
        out.append(f"{r['call_id']:<8}{r['rep']:<8}{r['call_type']:<12}{msg:>12}  {framing:<9}"
                   f"{str(r['engagement']['score']) + '/100':>11}  {'yes' if r['echo'] else '—':<5}")
    return "\n".join(out)


def message_check(rep: str, day: str, rows: list[dict], team: dict) -> str:
    """Deterministic selection (Decision 11): the same evidence always produces the same message check."""
    import statistics
    mine = [r for r in rows if r["rep"] == rep]
    pitches = [r for r in mine if r["message"]]
    delivered = [r["message"]["delivered"] for r in pitches]
    avg_delivered = round(sum(delivered) / len(delivered)) if delivered else None
    avg_eng = round(sum(r["engagement"]["score"] for r in mine) / len(mine))

    n_pitch, n_other = len(pitches), len(mine) - len(pitches)
    made_of = f"{n_pitch} pitch" + ("" if n_pitch == 1 else "es")
    if n_other:
        made_of += f", {n_other} commercial or logistics"
    # No scores in the daily message, and no comparison to anybody (Decision 14). One to four
    # calls cannot support a number about a person, and a team median across two or three reps is
    # one colleague wearing a disguise. Numbers live in the weekly, beside the rep's own last week.
    lines = [f"*{rep} — {day}*",
             f"{len(mine)} call{'' if len(mine) == 1 else 's'} analysed ({made_of})"]

    # Reservations belong in the message: a rep reading "your strongest call, 74/100" about a
    # call that ended in a polite no has to argue with the report, which costs more attention
    # than it saves (Decision 13).
    best = max(mine, key=lambda r: r["engagement"]["score"])
    held_back = best["record"].get("engagement", {}).get("reservations") or []
    # An echo and an enthusiastic aside are different things. Saying "they gave your framing
    # back" over an excitement quote would be the exact failure this system exists to prevent.
    if best["echo"]:
        proof = f', and they put your framing in their own words: "{best["echo"][0]["quote"]}"'
    elif best["record"]["engagement"].get("excitement"):
        proof = f'. The moment worth repeating: "{best["record"]["engagement"]["excitement"][0]["quote"]}"'
    else:
        proof = "."
    held = [(r, x) for r in mine for x in (r["record"].get("engagement", {}).get("reservations") or [])]
    if held:
        lines += ["", "*Objections you faced*"]
        for r, x in held[:3]:
            late = " — and it came late in the call" if x.get("late") else ""
            lines.append(f'▸ "{x.get("quote", "")}" — {r["account"]}{late}')
        lines.append("What you said back is in the call; this reports what was asked, not what "
                     "the answer should have been.")
    else:
        lines += ["", "*Objections you faced*",
                  "Nothing recorded as an unresolved objection. Read that as empty rather than clean."]

    lines += ["", "*What worked*",
              f"{best['account']} was the call the buyer leaned into most{proof}"]
    if held_back:
        q = held_back[0].get("quote", "")
        lines.append(f'Read with the reservation, though: "{q}"'
                     + (" — and it came late in the call." if held_back[0].get("late") else ""))

    # An element that is the point of the meeting is not an achievement. Delivering the problem
    # frame on a proposal call is the meeting; only its absence is worth saying.
    for r in pitches:
        exp = expected_for(r["call_type"])
        r["_notable_missing"] = [m for m in r["message"]["missing"]]
        r["_expected_missing"] = [m for m in r["message"]["missing"] if m in exp]

    missed = [r for r in pitches if r["message"]["missing"]]
    if missed:
        worst = min(missed, key=lambda r: r["message"]["score"])
        names = ", ".join(LABELS[m] for m in worst["message"]["missing"])
        lines += ["", "*What to do differently*",
                  f"On {worst['account']} you did not land: {names}."]
        if not any(r["message"]["framing_pair"] for r in pitches):
            lines.append("Across every pitch this run, the problem and the category never landed together — "
                         "that pair is what separates the new message from the old pitch.")
        lines += ["",
                  f"Say {LABELS[worst['message']['missing'][0]]} out loud before you move into the product. "
                  "Done looks like: it appears in the first two minutes of the call."]
    elif pitches:
        # Nothing was missed. Say so plainly rather than manufacturing a tip — a tip nobody
        # needed is worse than no tip.
        lines += ["",
                  "Nothing to change from these calls: every element the call had room for landed."]
    # Naming the specific unknown is what makes the rest credible. A rep told where the system is
    # blind argues with it less and uses it more.
    gaps = []
    if any(r["engagement"].get("next_step_level") in (None, 0) for r in mine):
        gaps.append("no next step was reached on at least one of these calls")
    if not held:
        gaps.append("nothing the buyer pushed back on was captured")
    lines += ["", "*What I can't see*",
              "Tone, and the room. " + ("Also: " + "; ".join(gaps) + "." if gaps else
                                        "Nothing else stands out as missing from these calls.")]

    return "\n".join(lines)
