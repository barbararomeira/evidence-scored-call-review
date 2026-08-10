#!/usr/bin/env python3
"""Daily run: transcripts in, scored table and a per-rep message check out.

    python3 run_day.py --mock                 # offline, no key, no network
    python3 run_day.py --mock --rep Ben      # one rep
    python3 run_day.py --transcripts ./calls --extractor claude_cli

Every step after extraction is deterministic Python. The model's only job is turning a
transcript into a call record (Decision 1).
"""
from __future__ import annotations

import argparse, json, pathlib, statistics, sys

from callscore import attribution, evidence, render, scope
from callscore.extractors import base, get
from callscore.score_engagement import score as score_engagement
from callscore.score_message import score as score_message

ROOT = pathlib.Path(__file__).resolve().parent
MIN_N_FOR_VERDICT = 5  # Decision 9: print n always, suppress the verdict below this


def process(transcript_dir: pathlib.Path, extractor_name: str, rep_filter: str | None,
            date_filter: str | None = None):
    extractor = get(extractor_name)
    rows, problems, unattributed = [], [], []

    for path in sorted(transcript_dir.glob("*.md")):
        t = base.load_transcript(path)
        if rep_filter and t.rep != rep_filter:
            continue
        if date_filter and t.date != date_filter:
            continue

        # Attribution gate, first, before anything is scored or even extracted into a row: the
        # rep this call is filed under has to appear in the transcript. Metadata says who was
        # invited; only the transcript shows who was there (Decision 11). Such a call leaves the
        # pipeline here rather than carrying a null through it, so no aggregate, median or
        # line of a message check can accidentally include a call its rep never spoke on.
        # A transcript that cannot tell speakers apart cannot support a claim about either
        # of them (Decision 12) — check that before asking who spoke.
        diar_ok, diar_why = attribution.diarisation_ok(t.body)
        attributable, why = attribution.check(t.rep, t.body) if diar_ok else (False, diar_why)
        if not attributable:
            unattributed.append({"call_id": t.call_id, "rep": t.rep, "account": t.account,
                                 "date": t.date, "reason": why})
            continue

        record = extractor.extract(t)

        # Evidence gate: a verdict whose quote isn't in the call is not a verdict (Decision 4).
        problems += [f"{t.call_id}: {p}" for p in evidence.verify(record["adherence"], t.body)]
        problems += [f"{t.call_id}: {p}" for p in evidence.verify_engagement(record["engagement"], t.body)]

        ok, reason = scope.in_scope(t.call_type, record["adherence"])
        message = score_message(record["adherence"]) if ok else None

        rows.append({
            "call_id": t.call_id, "rep": t.rep, "call_type": t.call_type, "account": t.account,
            "date": t.date, "message": message, "scope_reason": reason,
            "engagement": score_engagement(record["engagement"], t.duration_min),
            "rep_turns": attribution.rep_spoke(t.body)[1],
            "echo": record.get("echo", []), "record": record,
        })
    return rows, problems, unattributed


def team_medians(rows):
    pitches = [r for r in rows if r["message"]]
    return {
        "delivered": round(statistics.median([r["message"]["delivered"] for r in pitches])) if pitches else 0,
        "engagement": round(statistics.median([r["engagement"]["score"] for r in rows])),
        "next_step": round(statistics.median([r["engagement"]["next_step_level"] for r in rows])),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--mock", action="store_true", help="replay fixture call records: offline, no key")
    ap.add_argument("--extractor", default=None, help="claude_api | claude_cli | codex_cli | ollama")
    ap.add_argument("--transcripts", default=None, help="folder of transcript .md files")
    ap.add_argument("--rep", default=None, help="only this rep")
    ap.add_argument("--date", default=None, help="only this day, e.g. 2026-05-26 (a daily run is one day)")
    ap.add_argument("--out", default="outputs", help="where message checks are written")
    args = ap.parse_args()

    if not args.mock and not args.extractor:
        ap.error("pass --mock to run offline, or --extractor to use a model")

    tdir = pathlib.Path(args.transcripts) if args.transcripts else ROOT / "fixtures" / "transcripts"
    rows, problems, unattributed = process(tdir, "mock" if args.mock else args.extractor, args.rep, args.date)

    if not rows:
        print(f"No transcripts found in {tdir}")
        return 0

    try:
        shown = tdir.relative_to(ROOT)          # never print the machine's absolute paths
    except ValueError:
        shown = tdir
    when = f" on {args.date}" if args.date else ""
    print(f"\n{len(rows)} calls{when} from {shown}\n")
    print(render.scored_table(rows))

    # Say what was dropped and why. A silent exclusion looks the same as full coverage.
    for u in unattributed:
        print(f"\n  {u['call_id']} ({u['account']}) — not scored: {u['reason']}")

    scored = [r for r in rows if r["message"]]
    refused = [r for r in rows if not r["message"]]
    framing = sum(1 for r in scored if r["message"]["framing_pair"])

    print(f"\n  Scored for message:  {len(scored)} of {len(rows)} calls")
    for r in refused:
        print(f"    out of scope — {r['call_id']} ({r['call_type']}): {r['scope_reason']}")

    # Decision 9: the number always prints; the verdict does not, below n=5.
    verdict = "" if len(scored) >= MIN_N_FOR_VERDICT else f"   n={len(scored)} — not enough data yet"
    print(f"  Framing pair landed: {framing} of {len(scored)} pitches{verdict}")
    print(f"  Echo (recorded, never scored): {sum(1 for r in rows if r['echo'])} of {len(rows)}")

    if problems:
        print("\n  Evidence problems (verdicts without a quote found in the call):")
        for p in problems:
            print(f"    {p}")
    else:
        print("  Every scored point carries a verbatim quote found in its own transcript.")

    outdir = ROOT / args.out / "message-checks"
    outdir.mkdir(parents=True, exist_ok=True)
    team = team_medians(rows)
    print("\n  Message checks written:")
    for rep in sorted({r["rep"] for r in rows}):
        msg = render.message_check(rep, rows[0]["date"], rows, team)
        p = outdir / f"{rows[0]['date']}_{rep}.md"
        p.write_text(msg + "\n")
        print(f"    {p.relative_to(ROOT)}")

    (ROOT / args.out / "rows.json").write_text(json.dumps(
        [{k: v for k, v in r.items() if k != "record"} for r in rows], indent=2))
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
