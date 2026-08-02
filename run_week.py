#!/usr/bin/env python3
"""Weekly run: the two things a single day cannot answer.

    python3 run_week.py --mock

Produces:
  1. a weekly coaching message per rep — the same shape as the daily one, but a pattern
     across the week instead of one call
  2. a messaging analysis — is the message itself working, separate from who delivered it

Both read the call records the daily run already produced. Nothing re-reads a transcript.
"""
from __future__ import annotations

import argparse
import pathlib
import statistics
import sys

from callscore import render, scope
from callscore.extractors import base, get
from callscore.score_engagement import score as score_engagement
from callscore.score_message import score as score_message

ROOT = pathlib.Path(__file__).resolve().parent
MIN_N_FOR_VERDICT = 5


def collect(transcript_dir: pathlib.Path, extractor_name: str) -> list:
    extractor = get(extractor_name)
    rows = []
    for path in sorted(transcript_dir.glob("*.md")):
        t = base.load_transcript(path)
        record = extractor.extract(t)
        ok, reason = scope.in_scope(t.call_type, record["adherence"])
        rows.append({
            "call_id": t.call_id, "rep": t.rep, "call_type": t.call_type, "account": t.account,
            "date": t.date, "scope_reason": reason,
            "message": score_message(record["adherence"]) if ok else None,
            "engagement": score_engagement(record["engagement"], t.duration_min),
            "echo": record.get("echo", []), "record": record,
        })
    return rows


def messaging_analysis(rows: list, week: str) -> str:
    """Four questions, in this order. Conversion before speed — money before velocity."""
    pitches = [r for r in rows if r["message"]]
    refused = [r for r in rows if not r["message"]]
    framing = [r for r in pitches if r["message"]["framing_pair"]]
    n = len(pitches)

    def verdict(count, total):
        return "" if total >= MIN_N_FOR_VERDICT else f"  ·  n={total} — not enough data yet"

    # per element, how often it was delivered when it applied
    ids = ["problem_framing", "category", "promise_visibility",
           "promise_proactive", "promise_moat", "promise_durable"]
    per_element = []
    for i in ids:
        appl = [r for r in pitches if r["record"]["adherence"][i]["status"] in ("delivered", "absent")]
        deliv = [r for r in appl if r["record"]["adherence"][i]["status"] == "delivered"]
        per_element.append((render.LABELS[i], len(deliv), len(appl)))

    echoes = [(r["account"], r["echo"][0]["quote"]) for r in rows if r["echo"]]

    out = [f"# Messaging analysis — {week}", "",
           f"{len(rows)} calls · {n} pitches · {len(refused)} carried no product story", "",
           "## 1. Is the team sticking to the message?", ""]
    out.append(f"The framing pair — the problem *and* the category, landing together — held in "
               f"**{len(framing)} of {n} pitches**.{verdict(len(framing), n)}")
    out += ["", "| element | delivered | when it applied |", "|:--|--:|--:|"]
    for label, d, a in per_element:
        out.append(f"| {label} | {d} | {a} |")
    out += ["", "The bottom of that table is where a message dies quietly: the promises get covered "
                "because they are in the deck, and the frame around them does not.", ""]

    out += ["## 2. Is it landing?", ""]
    med = round(statistics.median([r["engagement"]["score"] for r in rows]))
    with_pair = [r["engagement"]["score"] for r in pitches if r["message"]["framing_pair"]]
    without = [r["engagement"]["score"] for r in pitches if not r["message"]["framing_pair"]]
    out.append(f"Median engagement across every call: **{med}/100**.")
    if with_pair and without:
        out.append("")
        out.append(f"Pitches where the framing pair landed: **{round(statistics.mean(with_pair))}/100** "
                   f"(n={len(with_pair)}). Where it did not: **{round(statistics.mean(without))}/100** "
                   f"(n={len(without)}).")
        out.append("")
        out.append("> Read that as a hypothesis, not a finding. Reps who deliver the whole message may "
                   "also be working better accounts — with this many calls the two cannot be separated.")
    if echoes:
        out += ["", "**Where the message came back at us**, unprompted — the strongest qualitative "
                    "signal there is, and deliberately never scored:", ""]
        for acct, q in echoes:
            out.append(f'> *"{q}"*  \n> — {acct}')
    out += ["", "## 3. Are we converting better?", "",
            "Not answerable yet. Comparing deals sold on the new message against the rest needs the "
            "CRM join and enough closed deals on each side; this run has neither.", "",
            "## 4. Are deals moving faster?", "",
            "Same answer, same reason. Both sections stay in the report saying nothing rather than "
            "disappearing, so the gap is visible instead of forgotten.", "",
            "---", "",
            f"*Sources: {len(rows)} call records, {week}. Every figure above is reproducible by "
            f"running this repo.*"]
    return "\n".join(out)


def weekly_coaching(rep: str, rows: list, week: str, team: dict) -> str:
    """Same shape as the daily message. The difference is the window and the emphasis."""
    mine = [r for r in rows if r["rep"] == rep]
    pitches = [r for r in mine if r["message"]]
    if not mine:
        return ""
    avg_delivered = round(statistics.mean([r["message"]["delivered"] for r in pitches])) if pitches else None
    med_eng = round(statistics.median([r["engagement"]["score"] for r in mine]))
    med_step = round(statistics.median([r["engagement"]["next_step_level"] for r in mine]))

    lines = [f"*{rep} — week of {week}*",
             f"{len(mine)} calls ({len(pitches)} pitch{'' if len(pitches) == 1 else 'es'}, "
             f"{len(mine) - len(pitches)} commercial or logistics)", "", "*Where you land*"]
    if avg_delivered is not None:
        lines.append(f"Message delivered — you {avg_delivered} of 6 · team {team['delivered']} of 6")
    lines += [f"Engagement — you {med_eng}/100 · team {team['engagement']}/100",
              f"Next step reached — you {med_step} of 4 · team {team['next_step']} of 4"]

    best = max(mine, key=lambda r: r["engagement"]["score"])
    if best["echo"]:
        worked = (f'{best["account"]} was your strongest call this week, and they put your framing '
                  f'in their own words: "{best["echo"][0]["quote"]}"')
    else:
        worked = (f'{best["account"]} was your strongest call this week — engagement '
                  f'{best["engagement"]["score"]}/100.')
    lines += ["", "*What worked*", worked]

    # A weekly miss is a pattern, not an incident.
    if pitches:
        counts = {}
        for r in pitches:
            for m in r["message"]["missing"]:
                counts[m] = counts.get(m, 0) + 1
        if counts:
            worst, hits = max(counts.items(), key=lambda kv: kv[1])
            example = next(r for r in pitches if worst in r["message"]["missing"])
            lines += ["", "*What you missed*",
                      f"{render.LABELS[worst].capitalize()} went unsaid in {hits} of your "
                      f"{len(pitches)} pitch{'' if len(pitches) == 1 else 'es'} this week — "
                      f"{example['account']} is the clearest example.",
                      "", "*What to improve*",
                      f"Say {render.LABELS[worst]} out loud before you move into the product. "
                      "Done looks like: it appears in the first two minutes of the call."]
        else:
            lines += ["", "*What to improve*",
                      "Nothing to change: every element your calls had room for landed."]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--extractor", default=None)
    ap.add_argument("--transcripts", default=None)
    ap.add_argument("--week", default="18–21 May 2026")
    ap.add_argument("--out", default="outputs")
    args = ap.parse_args()
    if not args.mock and not args.extractor:
        ap.error("pass --mock to run offline, or --extractor to use a model")

    tdir = pathlib.Path(args.transcripts) if args.transcripts else ROOT / "fixtures" / "transcripts"
    rows = collect(tdir, "mock" if args.mock else args.extractor)
    pitches = [r for r in rows if r["message"]]
    team = {
        "delivered": round(statistics.median([r["message"]["delivered"] for r in pitches])),
        "engagement": round(statistics.median([r["engagement"]["score"] for r in rows])),
        "next_step": round(statistics.median([r["engagement"]["next_step_level"] for r in rows])),
    }

    outdir = ROOT / args.out
    (outdir / "weekly").mkdir(parents=True, exist_ok=True)
    written = []

    analysis = messaging_analysis(rows, args.week)
    p = outdir / "weekly" / "messaging-analysis.md"
    p.write_text(analysis + "\n"); written.append(p)

    for rep in sorted({r["rep"] for r in rows}):
        msg = weekly_coaching(rep, rows, args.week, team)
        p = outdir / "weekly" / f"coaching-{rep}.md"
        p.write_text(msg + "\n"); written.append(p)

    # Summary to stdout: the findings, not a file list.
    framing = [r for r in pitches if r["message"]["framing_pair"]]
    with_pair = [r["engagement"]["score"] for r in framing]
    without = [r["engagement"]["score"] for r in pitches if not r["message"]["framing_pair"]]
    ids = ["problem_framing", "category", "promise_visibility",
           "promise_proactive", "promise_moat", "promise_durable"]
    weakest = min(ids, key=lambda i: sum(
        1 for r in pitches if r["record"]["adherence"][i]["status"] == "delivered"))
    weak_n = sum(1 for r in pitches if r["record"]["adherence"][weakest]["status"] == "delivered")

    print(f"\nWeek of {args.week}  ·  {len(rows)} calls  ·  {len(pitches)} pitches  "
          f"·  {len(rows) - len(pitches)} not pitches\n")
    print(f"  Framing pair landed        {len(framing)} of {len(pitches)} pitches")
    if with_pair and without:
        gap = round(statistics.mean(with_pair) - statistics.mean(without))
        print(f"  Engagement when it landed  {round(statistics.mean(with_pair))}/100  "
              f"(n={len(with_pair)})")
        print(f"  ...and when it did not     {round(statistics.mean(without))}/100  "
              f"(n={len(without)})   → {gap:+} points")
    print(f"  Weakest element            {render.LABELS[weakest]} — delivered in "
          f"{weak_n} of {len(pitches)}")
    print(f"  Echo, recorded not scored  {sum(1 for r in rows if r['echo'])} of {len(rows)}")
    print("\n  Written:")
    for p in written:
        print(f"    {p.relative_to(ROOT)}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
