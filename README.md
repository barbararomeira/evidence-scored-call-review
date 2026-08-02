# Evidence-scored call coaching

![python](https://img.shields.io/badge/python-3.9%2B-blue) ![runs offline](https://img.shields.io/badge/runs-offline%20%C2%B7%20no%20API%20key-success) ![license](https://img.shields.io/badge/license-MIT-lightgrey)

> A template for **grading conversations against a rubric you can defend**: read each transcript once, score it only where the rubric applies, require a verbatim quote for every point given *or withheld*, and refuse to state a verdict until there are enough calls to justify one.

![demo](docs/demo.gif)

The example in this repo is a sales team checking whether reps actually deliver a new positioning message. The pattern works anywhere a human judgment becomes a number someone is measured on — support-ticket QA, interview scorecards, teaching observations, compliance call review. The failure modes are the same everywhere: scoring things the rubric was never meant to cover, awarding points with no evidence, and calling a trend off four data points.

---

## What it does

Point it at a folder of call transcripts. It gives you, per call:

| | |
|---|---|
| **How much of your message was delivered** | six things you decided to say, counted — and only on calls where a pitch belonged |
| **How the buyer responded** | next step reached, situations they described, excitement, real back-and-forth |
| **A coaching message per rep** | what worked, what they missed, one thing to change — every claim quoting the call |

---

## Quickstart

No install, no API key, no network:

```bash
git clone https://github.com/barbararomeira/evidence-scored-call-coaching
cd evidence-scored-call-coaching
python3 run_day.py --mock
```

You get this, over six invented calls from three reps:

| call | rep | type | message delivered | framing pair | engagement | echo |
|:--|:--|:--|:-:|:-:|:-:|:-:|
| c-0412 | Ana | discovery | **4** of 6 | ✗ | 67 / 100 | — |
| c-0413 | Ana | pricing | *not a pitch* | — | 67 / 100 | — |
| c-0414 | Ben | demo | **6** of 6 | ✓ | 93 / 100 | ✓ |
| c-0415 | Ben | scheduling | *not a pitch* | — | 26 / 100 | — |
| c-0416 | Chloe | intro | **1** of 6 | ✗ | 35 / 100 | — |
| c-0417 | Chloe | discovery | **4** of 6 | ✓ | 60 / 100 | — |

*Message delivered* counts how many of your six message elements the rep actually said, out of the number that call had room for. *Framing pair* is whether the two that matter most — the problem and the category — landed **together**. *Engagement* is what the buyer did, scored out of 100.

> **Scored for message:** 4 of 6 calls — `c-0413` and `c-0415` were never pitches
> **Framing pair landed:** 2 of 4 pitches · `n=4 — not enough data yet`
> **Echo:** 1 of 6, recorded and never scored
> **Every scored point carries a verbatim quote found in its own transcript.**

Three things in that table are the whole design:

1. **Two calls have no score at all**, not a zero. A pricing negotiation isn't a bad pitch — it isn't a pitch.
2. **One number refuses to be interpreted.** It prints, then says the sample is too small to mean anything.
3. **Ana looks fine and isn't.** Four of six elements delivered, twice — but the framing pair never lands. A coverage score alone calls that a good week.

### The three things it writes

<table>
<tr><td width="33%" valign="top">

**① Daily coaching**
per rep, on yesterday's calls

</td><td width="33%" valign="top">

**② Weekly coaching**
same shape, a pattern across the week

</td><td width="33%" valign="top">

**③ Messaging analysis**
about the message, not the person

</td></tr>
</table>

**① Daily — what one rep receives:**

> **Ana — 2026-05-18** · 2 calls (1 pitch, 1 commercial or logistics)
>
> | | you | team |
> |:--|:--|:--|
> | Message delivered | 4 of 6 | 4 of 6 |
> | Engagement | 67 / 100 | 64 / 100 |
> | Next step reached | 4 of 4 | 3 of 4 |
>
> **What worked** — Beacon Analytics was your strongest call, engagement 67/100. The moment worth repeating: *"Okay. This is interesting."*
>
> **What you missed** — On Beacon Analytics you did not land: the problem, the category.
>
> **What to improve** — Say the problem out loud before you move into the product. Done looks like: it appears in the first two minutes of the call.

**② Weekly — the same rep, same format, but now a pattern:**

> **Ana — week of 18–21 May 2026** · 5 calls (4 pitches, 1 commercial)
>
> | | you | team |
> |:--|:--|:--|
> | Message delivered | 4 of 6 | 4 of 6 |
> | Engagement | 67 / 100 | 60 / 100 |
>
> **What you missed** — The problem went unsaid in **3 of your 4 pitches** this week — Beacon Analytics is the clearest example.

A day says *you skipped it on this call*. A week says *you skip it*. Same message shape, different claim — which is the only reason the weekly one exists.

**③ Messaging analysis — a different document, for a different question:**

> **Is the team sticking to the message?**
> The framing pair — the problem *and* the category, landing together — held in **8 of 14 pitches**.
>
> | element | delivered | when it applied |
> |:--|--:|--:|
> | the problem | 9 | 14 |
> | the category | 9 | 14 |
> | see what is happening | 13 | 14 |
> | be told, not go looking | 12 | 14 |
> | what no other system can do | 8 | 14 |
> | value that lasts | 7 | 14 |
>
> **Is it landing?**
> Pitches where the framing pair landed: **73/100** (n=8). Where it did not: **56/100** (n=6).
>
> *Read that as a hypothesis, not a finding. Reps who deliver the whole message may also be working better accounts — with this many calls the two cannot be separated.*

Notice what the daily run refused to say and the weekly run would: on three calls it prints `n=3 — not enough data yet`; on fourteen it gives you the number. Same rule, different sample.

All five outputs are committed in **[`examples/`](examples/)**.

`--mock` swaps **only** the extraction step, replaying pre-recorded call records from `fixtures/`. Every gate, score, coaching selection and rollup after that is real code executing. Want to read before running? [`examples/`](examples/) has the committed output.

---

## The four jobs, and which one thinks

Only the first touches a model. Everything else is deterministic Python reading what it produced — which is why the same evidence always yields the same coaching, and why a rep asking *"why this?"* gets a rule rather than a shrug.

| | job | runs | reads | writes | model? |
|:-:|:--|:--|:--|:--|:-:|
| ① | **Extract** — read the call once, produce evidence | per call, daily | the transcript | one `call_record.json`, a quote behind every verdict | **yes** — the only one |
| ② | **Score & coach** — gate, score, tell each rep | daily | the day's call records | scored table + `coaching/<date>_<rep>.md` | no |
| ③ | **Coach the week** — the same message, wider window | weekly | 7 days of call records | `weekly/coaching-<rep>.md` | no |
| ④ | **Analyse the message** — is it working at all | weekly | all call records | `weekly/messaging-analysis.md` | no |

② and ③ deliberately produce the **same shape** — a rep should not have to learn two formats. The difference is the claim: a day says *you skipped it on this call*, a week says *you skip it*.

④ is a different document for a different reader. It is about the message, not about a person, and it never names a rep.

```mermaid
flowchart TD
    T[transcripts] --> A1

    subgraph ONE["① Extract · the only model step"]
      A1[read each call once<br/>quote behind every verdict]
    end

    A1 --> R[(call records<br/>evidence + counts)]

    subgraph DAILY["② Daily · deterministic"]
      D1[scope gate → two scores] --> D2[coaching message per rep]
    end

    subgraph WEEKLY["③ + ④ Weekly · deterministic"]
      W1[same message, 7-day window<br/>patterns not incidents]
      W2[messaging analysis<br/>per element · engagement gap · echo]
    end

    R --> D1
    R --> W1
    R --> W2

    D2 --> O1([a rep reads this])
    W1 --> O1
    W2 --> O2([whoever owns the message reads this])

    classDef llm fill:#e1f5ff,stroke:#0969da,color:#000
    classDef python fill:#f6f8fa,stroke:#656d76,color:#000
    classDef io fill:#dafbe1,stroke:#1a7f37,color:#000
    class A1 llm
    class D1,D2,W1,W2 python
    class T,R,O1,O2 io
```

---

## Finding your way around

| If you want to… | Go here |
|---|---|
| see what it produces, without cloning | [`examples/`](examples/) |
| change what gets scored | [`rubric/`](rubric/) — four files, the only ones you edit |
| understand why it works this way | [`DECISIONS.md`](DECISIONS.md) — 10 entries, chose / considered / why |
| see the calls it runs on | [`fixtures/`](fixtures/) — invented transcripts and the story they tell |
| plug in your own model | [`callscore/extractors/base.py`](callscore/extractors/base.py) — one method |
| read the scoring itself | [`callscore/score_message.py`](callscore/score_message.py) · [`score_engagement.py`](callscore/score_engagement.py) · [`scope.py`](callscore/scope.py) |

---

## What makes this worth copying

**1. Extract once, analyse many times.** The transcript is the expensive input and the only non-deterministic step. One pass produces one call record; the message score, the engagement score and the coaching all read *that*, never the transcript again. Cost becomes linear in calls rather than calls × metrics — and, more importantly, the numbers can't contradict each other. Two passes over the same call can disagree about whether the rep named the category, and then a coaching message contradicts the dashboard.

**2. Refusing to score is a feature.** A pricing negotiation is not a bad pitch; it isn't a pitch. Calls outside the rubric's scope get `message: None` and a printed reason, never a zero. A score that is always available and sometimes meaningless is worse than one that admits when the question doesn't apply.

**3. Evidence in both directions.** Every verdict carries a quote, and `run_day.py` checks that the quote actually appears in that transcript. `absent` needs evidence too — the passage where the element should have been. One-directional evidence produces a scorer that is rigorous about praise and casual about blame, which is backwards for something a person is measured on.

**4. Print n, and shut up below five.** Thin aggregates still show their number, but the interpretation is replaced by `not enough data yet`. Hiding them teaches people the report is unreliable; confidence intervals are the right statistics and the wrong interface.

**5. Two scores, never blended.** *Message delivered* is about whether the rep said what the company decided to say. *Engagement* is about whether the buyer leaned in — partly the rep, largely the account. Averaging them lets a great meeting with an off-message pitch hide inside a mediocre number, which is the one thing this exists to detect.

Full reasoning, including what was considered and rejected, in [`DECISIONS.md`](DECISIONS.md).

---

## Why "extract once" is the whole architecture

```mermaid
flowchart LR
    T[transcript<br/>expensive to read] --> R[(call record<br/>quotes + counts)]
    R --> A[message score]
    R --> B[engagement score]
    R --> C[coaching]
    R --> D[weekly rollup]
    R --> E[whatever you add next]

    classDef io fill:#dafbe1,stroke:#1a7f37,color:#000
    classDef python fill:#f6f8fa,stroke:#656d76,color:#000
    class T,R io
    class A,B,C,D,E python
```

Adding a new question about your calls costs one consumer of the record, not another pass over the transcripts. In the system this pattern came from, the calls were already being read every morning for a completely different purpose; the second question cost one extra extraction step, not a new pipeline.

## What is scored, what is refused, what is only recorded

| | | |
|---|---|---|
| **Message delivered** | the problem · the category | reported *together* as the **framing pair** |
| | see what is happening · be told, not go looking | |
| | what no other system can do · value that lasts | |
| **Engagement** | next step reached | 35 |
| | their own situations | 25 |
| | excitement | 20 |
| | back-and-forth | 20 |
| **Recorded, never scored** | echo — the buyer restating your framing in their own words | the best signal there is, and the one that dies if you count it |
| **Refused a score** | pricing · scheduling · implementation · scoping | no pitch was delivered, so there is nothing to grade |

The framing pair is reported separately from the coverage score because a call can deliver four promises cleanly while the frame around them is still the old pitch — and counting elements cannot see that. Echo stays unscored on purpose: the moment it earns points, people start fishing for it.

---

## Use it on your own calls

**1. Rewrite the rubric.** [`rubric/`](rubric/) is the only place you need to touch: `positioning.md` (prose, for the model), `message_rubric.json` (the elements), `engagement_rubric.json` (the weights — a test enforces they sum to 100), `scope.json` (which call types the message rubric applies to, and why). Nothing about the domain is hardcoded in Python.

**2. Point it at your transcripts.** The input contract is a folder of markdown files with front matter (`call_id`, `date`, `rep`, `call_type`, `duration_min`) and `REP:` / `PROSPECT:` turns. Any notetaker that exports text can feed it.

```bash
python3 run_day.py --transcripts ./my_calls --extractor claude_cli
```

**3. Bring your own model.** `callscore/extractors/base.py` defines one method. `mock` ships working; `claude_api`, `claude_cli`, `codex_cli` and `ollama` are named stubs that raise with instructions — roughly 40 lines each, and deliberately not written for you, so nobody inherits a vendor choice they didn't make.

---

## Tests

**13 tests** covering: the scope gate refusing rather than zeroing · not-applicable elements leaving the denominator while absent ones stay in · the framing pair being independent of the coverage score · engagement weights summing to 100 · echo declared but never scored · the short-call rule refusing to extrapolate a nine-minute call · excitement capped · quotes verified against their own transcript · absent verdicts requiring evidence too.

```bash
python3 -m pytest tests -q
```

## Not built, on purpose

CRM connectors · audio and diarisation · a web UI · a database · delivery and scheduling · running one installation for several teams at once. Each is a real piece of work and none of it is the interesting part. This is one team, one rubric, files on disk.

## License

MIT.
