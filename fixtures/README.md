# Fixtures

**These are not real calls.** Every transcript, company, person and quote here is invented. The reps are called Ana, Ben and Chloe; the buyers are companies that do not exist. No customer,
employer or colleague appears in this repo, and no real scores were used to build it.

The demo sells a generic B2B SaaS product to operations teams. That is deliberate: the rubric is
a config file, so the domain is a one-file swap, and a neutral example keeps the focus on the
scoring design rather than the industry.

## Shape

| Field | Where | Notes |
|---|---|---|
| `call_id`, `date`, `rep`, `call_type`, `account`, `duration_min` | transcript front matter | `rep` is an invented first name — Ana, Ben, Chloe |
| `adherence.<element>.{status,quote,timestamp}` | call record | `delivered` / `absent` / `n/a`, each with the quote that justifies it |
| `engagement.{next_step_reached,own_situations,excitement,back_and_forth}` | call record | counts and quotes, never impressions |
| `echo` | call record | recorded, never scored |
| `scoring_scope` | call record | `full` or `engagement_only` |

Every quote in `call_records/` appears verbatim in the matching transcript. `run_day.py` verifies
this on every run, so the fixtures cannot drift from the claims made about them.

## The story this data tells

Six calls, three reps, over four days.

| Rep | What their calls show |
|---|---|
| **Ana** | The most dangerous pattern: covers the promises well (4 of 6) but never frames the problem or names the category. A coverage score alone would call this a good week. `framing_pair` is what catches it. |
| **Ben** | Genuinely on message. The only call scoring 6 of 6, the highest engagement, and the only echo — the prospect restating the framing in their own words, unprompted. |
| **Chloe** | Improving. An intro that lands 1 of 6, then two days later a discovery call at 4 of 6 *with* the framing pair. The trend is the point, not either number. |

Two calls are deliberately **not pitches** — a pricing negotiation and a nine-minute scheduling
call. They exist so the scope gate has something to refuse. Under a rubric without that gate they
would both score zero, and one rep would appear to have failed a call where there was no pitch to
deliver. The nine-minute call also exercises the short-call rule: its back-and-forth is bucketed
on the raw count rather than extrapolated to half an hour.
