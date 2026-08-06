# Examples

Every output this repo produces, committed so you can read them before cloning anything.
All of them are regenerated from the code — if they ever disagree with it, they are the stale ones.

| # | File | What it is | Produced by |
|---|---|---|---|
| 1 | [`01_daily_run.txt`](01_daily_run.txt) | One day's calls, scored | `python3 run_day.py --mock --date 2026-05-21` |
| 2 | [`02_daily_message_check_Ana.pdf`](02_daily_message_check_Ana.pdf) | **The daily message check** — one rep, yesterday's calls | `python3 run_day.py --mock` → `docs/make_visuals.py` |
| 3 | [`03_weekly_message_check_Ana.pdf`](03_weekly_message_check_Ana.pdf) | **The weekly message check** — trend, consistency, follow-through | `python3 run_week.py --mock` → `docs/make_visuals.py` |
| 4 | [`04_weekly_run.txt`](04_weekly_run.txt) | The week's findings at a glance | `python3 run_week.py --mock` |
| 5 | [`05_weekly_messaging_analysis.pdf`](05_weekly_messaging_analysis.pdf) | **Messaging analysis** — with week-over-week charts | `python3 run_week.py --mock` → `docs/make_visuals.py` |

The runs write Markdown; `docs/make_visuals.py` renders the same values as PDF and PNG from the
pipeline itself, never by parsing the Markdown — so the pretty version cannot say something the
code does not.

## Why the weekly is not just the daily again

They share a format on purpose — a rep should not have to learn two. What differs is what a week
can know and a day cannot:

| | daily | weekly |
|---|---|---|
| Trend | — | your own numbers against last week |
| Consistency | one call, no spread | the range across your pitches, and which call pulls the bottom |
| Follow-through | — | **did the thing you were told last week actually change?** |
| The miss | *you skipped it on this call* | *you skip it* — a habit, with the count |

The follow-through line is the reason the weekly exists. It reads last week's most-missed element,
then checks this week's calls for it, and says plainly whether it moved.
