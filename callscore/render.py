"""Markdown and stdout rendering. No dependencies: markdown is what a coaching message is."""
from __future__ import annotations


LABELS = {
    "problem_framing": "the problem", "category": "the category",
    "promise_visibility": "see what is happening", "promise_proactive": "be told, not go looking",
    "promise_moat": "what no other system can do", "promise_durable": "value that lasts",
}

def scored_table(rows: list) -> str:
    """Aligned terminal table. Columns are fixed width so nothing shifts when a call is refused."""
    H = f"{'call':<8}{'rep':<8}{'type':<12}{'message':>14}  {'framing':<8}{'engage':>7}  {'echo':<5}"
    out = [H, "─" * len(H)]
    for r in rows:
        if r["message"] is None:
            msg, framing = "not a pitch", "—"
        else:
            m = r["message"]
            msg = f"{m['delivered']} of 6 · {m['score']}"
            framing = "yes" if m["framing_pair"] else "no"
        out.append(f"{r['call_id']:<8}{r['rep']:<8}{r['call_type']:<12}{msg:>14}  {framing:<8}"
                   f"{r['engagement']['score']:>7}  {'yes' if r['echo'] else '—':<5}")
    return "\n".join(out)


def coaching_message(rep: str, day: str, rows: list[dict], team: dict) -> str:
    """Deterministic selection (Decision 11): the same evidence always produces the same coaching."""
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
    lines = [f"*{rep} — {day}*",
             f"{len(mine)} call{'' if len(mine) == 1 else 's'} ({made_of})",
             "",
             "*Where you land*"]
    if avg_delivered is not None:
        lines.append(f"Message delivered — you {avg_delivered} of 6 · team {team['delivered']} of 6")
    lines.append(f"Engagement — you {avg_eng}/100 · team {team['engagement']}/100")
    # Median, not max: one commercial call reaching "asked for pricing" should not present as
    # the rep's typical outcome.
    mine_step = round(statistics.median([r["engagement"]["next_step_level"] for r in mine]))
    lines.append(f"Next step reached — you {mine_step} of 4 · team {team['next_step']} of 4")

    best = max(mine, key=lambda r: r["engagement"]["score"])
    # An echo and an enthusiastic aside are different things. Saying "they gave your framing
    # back" over an excitement quote would be the exact failure this system exists to prevent.
    if best["echo"]:
        proof = f', and they put your framing in their own words: "{best["echo"][0]["quote"]}"'
    elif best["record"]["engagement"].get("excitement"):
        proof = f'. The moment worth repeating: "{best["record"]["engagement"]["excitement"][0]["quote"]}"'
    else:
        proof = "."
    lines += ["", "*What worked*",
              f"{best['account']} was your strongest call — engagement {best['engagement']['score']}/100{proof}"]

    missed = [r for r in pitches if r["message"]["missing"]]
    if missed:
        worst = min(missed, key=lambda r: r["message"]["score"])
        names = ", ".join(LABELS[m] for m in worst["message"]["missing"])
        lines += ["", "*What you missed*",
                  f"On {worst['account']} you did not land: {names}. "
                  f"That call delivered {worst['message']['delivered']} of "
                  f"{worst['message']['applicable']} elements."]
        if not any(r["message"]["framing_pair"] for r in pitches):
            lines.append("Across every pitch this run, the problem and the category never landed together — "
                         "that pair is what separates the new message from the old pitch.")
        lines += ["", "*What to improve*",
                  f"Say {LABELS[worst['message']['missing'][0]]} out loud before you move into the product. "
                  "Done looks like: it appears in the first two minutes of the call."]
    elif pitches:
        # Nothing was missed. Say so plainly rather than manufacturing a tip — a tip nobody
        # needed is worse than no tip.
        lines += ["", "*What to improve*",
                  "Nothing to change from these calls: every element the call had room for landed."]
    return "\n".join(lines)
