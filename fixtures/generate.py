#!/usr/bin/env python3
"""Generate synthetic calls, deterministically.

Six calls in this repo are hand-written (`c-0412`–`c-0417`). The rest are composed here from a
bank of lines, to a spec, so there are enough calls for the aggregates to mean something —
without pretending a five-call sample is a trend.

The important property: **every quote in a generated call record is lifted verbatim from the
text this script wrote into the transcript.** The evidence check in `run_day.py` verifies that
on every run, so the fixtures cannot drift from the claims made about them.

    python3 fixtures/generate.py          # rewrites the generated calls in place

Seeded, so the same spec always produces the same calls.
"""
from __future__ import annotations

import json
import pathlib
import random

HERE = pathlib.Path(__file__).resolve().parent
TRANSCRIPTS = HERE / "transcripts"
RECORDS = HERE / "call_records"

# --- what a rep says when an element lands -------------------------------------------------
DELIVERED = {
    "problem_framing": [
        "Most teams find out what went wrong after it has already cost them the week",
        "The pattern we see is that nobody knows until someone complains, and by then it is a week old",
        "Managers spend their mornings assembling a picture instead of acting on one",
    ],
    "category": [
        "The way to think about it is an operating layer for how the team runs, not a reporting tool",
        "We are the system you run the work with, not a dashboard bolted onto what you already have",
        "It is an operating layer for the work itself, which is a different thing from reporting on it",
    ],
    "promise_visibility": [
        "The current state is visible without anyone being asked for an update",
        "You stop chasing people for status, because the state is just there",
        "Nobody has to prepare a status pack, because the status is live",
    ],
    "promise_proactive": [
        "When something drifts, the person who owns it gets told rather than having to go looking",
        "The exception comes to you, instead of waiting in a dashboard for someone to open it",
        "You get told when it matters, which is the opposite of hunting through reports",
    ],
    "promise_moat": [
        "Your systems record transactions, they do not see the work between transactions",
        "The stack you have knows an approval happened, not that it sat with someone for nine days",
        "Everything you own records events; the loss happens in the gaps between them",
    ],
    "promise_durable": [
        "The daily routine changes, so the gain holds instead of decaying after rollout",
        "It is not a project that improves a number once and then drifts back",
        "What stops it fading is that the work runs through it every day, not once a quarter",
    ],
}

OPENERS = [
    "Thanks for making the time. Where would you like to start?",
    "Good to meet you. I thought I would keep this short and leave room for questions.",
    "Appreciate the call. Tell me what prompted you to take it.",
]

# --- what the buyer says -------------------------------------------------------------------
SITUATIONS = [
    "Our onboarding handoff takes anywhere between two and six weeks and nobody can tell me why",
    "We lost a supplier last quarter over something that sat in a queue for nine days",
    "My team builds a status pack every Monday that is obsolete by Tuesday afternoon",
    "Approvals go into legal and we genuinely do not know when they will come out",
    "The same ticket bounces between two teams twice before anyone notices",
    "We run the whole thing in spreadsheets and three people maintain them",
    "Our quality holds sit for days because nobody owns the escalation",
    "Half my week is asking four people for the same update",
]
EXCITEMENT = [
    "That is exactly what we have been trying to get visibility on",
    "Okay, that is a real difference from what we looked at before",
    "I want my team to see this",
    "That would give me back the first hour of every day",
]
ECHO = [
    "So it accounts for the time between the events, not just the events themselves",
    "Right, so you are the layer we actually run the work on, not another report",
    "Meaning we would stop finding out after the fact — that is the difference",
]
QUESTIONS = [
    "How long does it take to get the first workflow live?",
    "Does this replace what we have or sit next to it?",
    "How noisy is that in practice? Our last tool got muted within a month.",
    "Who normally owns this internally on your customers' side?",
    "What does it need from my team during setup?",
    "How do you handle the data staying in the EU?",
]
NEXT_STEP = {
    0: [("So I will leave it there for now.", "I do not think this is a priority for us this year.")],
    1: [("Shall I send something over?", "Send me some material and I will have a look.")],
    2: [("Should we get a proper session in the calendar?", "Yes, let us book something for next week.")],
    3: [("Who else would need to see this?", "Let me take it to my director — she would have to sponsor it.")],
    4: [("Happy to put numbers together whenever it is useful.",
         "Send me pricing and I will get it in front of procurement this week.")],
}


def build_call(spec: dict, rng: random.Random) -> tuple[str, dict]:
    """Compose one transcript and the matching call record. Quotes come from the same strings."""
    lines, adherence, used_time = [], {}, 2
    lines.append(f"REP: {rng.choice(OPENERS)}")
    lines.append(f"PROSPECT: {rng.choice(SITUATIONS)}")

    delivered = set(spec["delivered"])
    all_elements = list(DELIVERED)
    opener_anchor = lines[0][5:]

    for el in all_elements:
        if spec["scope"] == "engagement_only":
            adherence[el] = {"status": "n/a", "quote": None, "timestamp": None}
            continue
        if el in delivered:
            line = rng.choice(DELIVERED[el])
            used_time += 2
            ts = f"{used_time:02d}:{rng.randint(10, 55)}"
            lines.append(f"REP: {line}.")
            adherence[el] = {"status": "delivered", "quote": line, "timestamp": ts}
        else:
            adherence[el] = {"status": "absent", "quote": opener_anchor,
                             "timestamp": "00:05"}

    situations, excitement, echo = [], [], []
    for _ in range(spec["situations"]):
        s = rng.choice([x for x in SITUATIONS if x not in [q["quote"] for q in situations]])
        used_time += 1
        lines.append(f"PROSPECT: {s}.")
        situations.append({"what": s[:48].lower(), "quote": s, "timestamp": f"{used_time:02d}:20"})
    for _ in range(spec["excitement"]):
        e = rng.choice([x for x in EXCITEMENT if x not in [q["quote"] for q in excitement]])
        used_time += 1
        lines.append(f"PROSPECT: {e}.")
        excitement.append({"quote": e, "timestamp": f"{used_time:02d}:40"})
    if spec.get("echo"):
        q = rng.choice(ECHO)
        used_time += 1
        lines.append(f"PROSPECT: {q}.")
        echo.append({"quote": q, "timestamp": f"{used_time:02d}:15"})

    for _ in range(spec["questions"]):
        lines.append(f"PROSPECT: {rng.choice(QUESTIONS)}")
        lines.append("REP: Good question — let me answer that properly.")

    rep_close, buyer_close = rng.choice(NEXT_STEP[spec["next_step"]])
    lines.append(f"REP: {rep_close}")
    lines.append(f"PROSPECT: {buyer_close}")

    front = (f"---\ncall_id: {spec['call_id']}\ndate: {spec['date']}\nrep: {spec['rep']}\n"
             f"call_type: {spec['call_type']}\naccount: {spec['account']}\n"
             f"duration_min: {spec['duration_min']}\n---\n\n")
    transcript = front + "\n".join(lines) + "\n"

    record = {
        "call_id": spec["call_id"], "date": spec["date"], "rep": spec["rep"],
        "call_type": spec["call_type"], "account": spec["account"],
        "duration_min": spec["duration_min"], "scoring_scope": spec["scope"],
        "adherence": adherence,
        "engagement": {
            "next_step_reached": {"level": spec["next_step"], "quote": buyer_close,
                                  "timestamp": f"{spec['duration_min'] - 1:02d}:30"},
            "own_situations": situations, "excitement": excitement,
            "back_and_forth": {"questions": spec["questions"],
                               "substantive_turns": spec["turns"],
                               "per_30min": round((spec["questions"] + spec["turns"])
                                                  * 30 / spec["duration_min"])},
        },
        "echo": echo, "flags": [], "scoring_version": "v1",
    }
    return transcript, record


# --- the story the generated calls tell ----------------------------------------------------
# Ana covers the promises but rarely frames; Ben is on message; Chloe improves across the two
# weeks; Dev is new and inconsistent. Six calls are not pitches at all.
P = ["problem_framing", "category", "promise_visibility", "promise_proactive",
     "promise_moat", "promise_durable"]

SPECS = [
    # week 1
    dict(call_id="c-0418", date="2026-05-19", rep="Ana", call_type="discovery", account="Perch Software",
         duration_min=28, scope="full", delivered=P[2:], next_step=3, situations=2, excitement=1,
         questions=4, turns=7),
    dict(call_id="c-0419", date="2026-05-20", rep="Ana", call_type="demo", account="Tessellate",
         duration_min=31, scope="full", delivered=P[2:] + ["problem_framing"], next_step=2,
         situations=2, excitement=1, questions=3, turns=8),
    dict(call_id="c-0420", date="2026-05-20", rep="Ben", call_type="discovery", account="Kestrel Ops",
         duration_min=29, scope="full", delivered=P, next_step=3, situations=3, excitement=2,
         questions=5, turns=9, echo=True),
    dict(call_id="c-0421", date="2026-05-21", rep="Ben", call_type="intro", account="Aster Logistics",
         duration_min=20, scope="full", delivered=P[:4], next_step=2, situations=2, excitement=1,
         questions=3, turns=5),
    dict(call_id="c-0422", date="2026-05-21", rep="Chloe", call_type="demo", account="Marlow Group",
         duration_min=26, scope="full", delivered=P[:2] + P[2:4], next_step=2, situations=1,
         excitement=1, questions=3, turns=6),
    dict(call_id="c-0423", date="2026-05-22", rep="Dev", call_type="intro", account="Wren Retail",
         duration_min=17, scope="full", delivered=[P[2]], next_step=1, situations=1, excitement=0,
         questions=2, turns=3),
    dict(call_id="c-0424", date="2026-05-22", rep="Dev", call_type="pricing", account="Perch Software",
         duration_min=21, scope="engagement_only", delivered=[], next_step=4, situations=1,
         excitement=0, questions=4, turns=6),
    # week 2
    dict(call_id="c-0425", date="2026-05-26", rep="Ana", call_type="discovery", account="Halden Foods",
         duration_min=30, scope="full", delivered=P[2:] + ["category"], next_step=3, situations=3,
         excitement=1, questions=4, turns=8),
    dict(call_id="c-0426", date="2026-05-26", rep="Ben", call_type="demo", account="Kestrel Ops",
         duration_min=33, scope="full", delivered=P, next_step=4, situations=3, excitement=3,
         questions=5, turns=11, echo=True),
    dict(call_id="c-0427", date="2026-05-27", rep="Ben", call_type="implementation",
         account="Cobalt Systems", duration_min=24, scope="engagement_only", delivered=[],
         next_step=3, situations=2, excitement=0, questions=3, turns=7),
    dict(call_id="c-0428", date="2026-05-27", rep="Chloe", call_type="discovery",
         account="Ironwood Health", duration_min=27, scope="full", delivered=P[:5], next_step=3,
         situations=2, excitement=2, questions=4, turns=8, echo=True),
    dict(call_id="c-0429", date="2026-05-28", rep="Chloe", call_type="scheduling",
         account="Marlow Group", duration_min=8, scope="engagement_only", delivered=[],
         next_step=2, situations=0, excitement=0, questions=1, turns=2),
    dict(call_id="c-0430", date="2026-05-28", rep="Dev", call_type="discovery", account="Wren Retail",
         duration_min=25, scope="full", delivered=P[:2] + [P[3]], next_step=2, situations=2,
         excitement=1, questions=3, turns=6),
    dict(call_id="c-0431", date="2026-05-29", rep="Dev", call_type="technical_scoping",
         account="Ironwood Health", duration_min=22, scope="engagement_only", delivered=[],
         next_step=2, situations=2, excitement=0, questions=4, turns=7),
]


def main():
    rng = random.Random(20260518)
    for spec in SPECS:
        transcript, record = build_call(spec, rng)
        (TRANSCRIPTS / f"{spec['call_id']}.md").write_text(transcript)
        (RECORDS / f"{spec['call_id']}.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"wrote {len(SPECS)} generated calls "
          f"({sum(1 for s in SPECS if s['scope'] == 'full')} pitches, "
          f"{sum(1 for s in SPECS if s['scope'] != 'full')} not pitches)")


if __name__ == "__main__":
    main()
