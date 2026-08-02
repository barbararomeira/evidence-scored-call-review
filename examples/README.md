# Examples

Every output this repo produces, committed so you can read them before cloning anything.
All five are regenerated from the code — if they ever disagree with it, they are the stale ones.

| # | File | What it is | Produced by |
|---|---|---|---|
| 1 | [`01_daily_run.txt`](01_daily_run.txt) | One day's calls, scored | `python3 run_day.py --mock --date 2026-05-21` |
| 2 | [`02_daily_coaching_Ana.md`](02_daily_coaching_Ana.md) | **Daily coaching** — one rep, yesterday's calls | `python3 run_day.py --mock` |
| 3 | [`03_weekly_coaching_Ana.md`](03_weekly_coaching_Ana.md) | **Weekly coaching** — same shape, a pattern across the week | `python3 run_week.py --mock` |
| 4 | [`04_weekly_run.txt`](04_weekly_run.txt) | The week's findings at a glance | `python3 run_week.py --mock` |
| 5 | [`05_weekly_messaging_analysis.md`](05_weekly_messaging_analysis.md) | **Messaging analysis** — is the message working, separately from who delivered it | `python3 run_week.py --mock` |

The daily and weekly coaching deliberately share a format. A rep should not have to learn two.
The messaging analysis is a different document for a different reader: it is about the message,
not about a person.
