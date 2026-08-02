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

from callscore import render, scope, tips
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


def week_of(date: str) -> str:
    """The fixture spans two weeks: 18–22 May and 26–29 May."""
    return "week 1" if date <= "2026-05-22" else "week 2"


def most_missed(pitches: list) -> tuple:
    """The element a rep skipped most often. Returns (element_id, times_missed, of_n)."""
    counts = {}
    for r in pitches:
        for m in r["message"]["missing"]:
            counts[m] = counts.get(m, 0) + 1
    if not counts:
        return None, 0, len(pitches)
    el, n = max(counts.items(), key=lambda kv: kv[1])
    return el, n, len(pitches)


def follow_through(rep: str, rows: list) -> str | None:
    """Did last week's weakest element improve this week? This is what a day cannot tell you."""
    prev = [r for r in rows if r["rep"] == rep and r["message"] and week_of(r["date"]) == "week 1"]
    now = [r for r in rows if r["rep"] == rep and r["message"] and week_of(r["date"]) == "week 2"]
    if not prev or not now:
        return None
    el, missed, of_n = most_missed(prev)
    if not el:
        return None
    landed = sum(1 for r in now if r["record"]["adherence"][el]["status"] == "delivered")
    label = render.LABELS[el]
    n_now = len(now)
    then = f"missed in {missed} of {of_n} {'pitch' if of_n == 1 else 'pitches'}"
    head = f"*Last week you were skipping {label}* — {then}."
    if landed == n_now:
        after = ("This week it landed in the one pitch you had."
                 if n_now == 1 else f"This week it landed in all {n_now}.")
        return f"{head} {after} That is the change, and it held."
    if landed:
        return f"{head} This week it landed in {landed} of {n_now}. Moving, not fixed."
    tail = "your only pitch" if n_now == 1 else f"any of your {n_now}"
    return f"{head} This week it did not land in {tail}. Same gap, second week."


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
    """The same shape as the daily message, plus the three things a day cannot give you:
    a trend against last week, the spread across a week's calls, and whether the last
    thing you were told actually changed anything."""
    mine = [r for r in rows if r["rep"] == rep]
    pitches = [r for r in mine if r["message"]]
    if not mine:
        return ""
    this_wk = [r for r in mine if week_of(r["date"]) == "week 2"] or mine
    prev_wk = [r for r in mine if week_of(r["date"]) == "week 1"]

    def avg_delivered(rs):
        ps = [r for r in rs if r["message"]]
        return round(statistics.mean([r["message"]["delivered"] for r in ps])) if ps else None

    now_d, prev_d = avg_delivered(this_wk), avg_delivered(prev_wk)
    now_e = round(statistics.median([r["engagement"]["score"] for r in this_wk]))
    prev_e = round(statistics.median([r["engagement"]["score"] for r in prev_wk])) if prev_wk else None

    def arrow(now, before):
        if before is None or now == before:
            return "="
        return f"↑ from {before}" if now > before else f"↓ from {before}"

    types = {}
    for r in mine:
        types[r["call_type"]] = types.get(r["call_type"], 0) + 1
    mix = " · ".join(f"{v} {k}" for k, v in sorted(types.items(), key=lambda kv: -kv[1]))

    lines = [f"*{rep} — week of {week}*",
             f"{len(mine)} calls: {mix}", "", "*Where you land*"]
    if now_d is not None:
        lines.append(f"Message delivered — you {now_d} of 6 ({arrow(now_d, prev_d)}) · "
                     f"team {team['delivered']} of 6")
    lines.append(f"Engagement — you {now_e}/100 ({arrow(now_e, prev_e)}) · team {team['engagement']}/100")

    # Spread: a day has one call, a week has a range. Consistency is its own signal.
    if len(pitches) > 1:
        lo = min(r["message"]["delivered"] for r in pitches)
        hi = max(r["message"]["delivered"] for r in pitches)
        if lo != hi:
            weakest = min(pitches, key=lambda r: r["message"]["delivered"])
            lines.append(f"Consistency — your pitches ran {lo} to {hi} of 6. "
                         f"The {weakest['account']} call is the one pulling the bottom.")

    best = max(mine, key=lambda r: r["engagement"]["score"])
    if best["echo"]:
        worked = (f'{best["account"]} was your strongest call, and they put your framing in their '
                  f'own words: "{best["echo"][0]["quote"]}"')
    else:
        worked = (f'{best["account"]} was your strongest call — engagement '
                  f'{best["engagement"]["score"]}/100.')
    lines += ["", "*What worked*", worked]

    ft = follow_through(rep, rows)
    if ft:
        lines += ["", "*Since last week*", ft]

    if pitches:
        el, hits, of_n = most_missed(pitches)
        if el:
            example = next(r for r in pitches if el in r["message"]["missing"])
            lines += ["", "*The pattern to fix*",
                      f"{render.LABELS[el].capitalize()} went unsaid in {hits} of your {of_n} "
                      f"{'pitch' if of_n == 1 else 'pitches'} — {example['account']} is the clearest "
                      f"example." + (f" One call is a slip; {hits} is a habit." if hits > 1 else ""),
                      "", "*What to improve*",
                      f"Say {render.LABELS[el]} out loud before you move into the product. "
                      "Done looks like: it appears in the first two minutes of the call."]
        else:
            lines += ["", "*What to improve*",
                      "Nothing to change: every element your calls had room for landed."]

    open_tips = tips.register(rep, [r for r in mine if week_of(r["date"]) == "week 1"],
                              [r for r in mine if week_of(r["date"]) == "week 2"], "2026W21")
    if open_tips:
        lines += ["", "*Your open tips*"]
        for t in open_tips:
            lines.append(f"{t['id']} — say {render.LABELS[t['element']]} before you move into the "
                         f"product · {t['status']}: {t['evidence']}")
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
