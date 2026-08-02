#!/usr/bin/env python3
"""Render the example outputs as images for the README.

Values come from the pipeline itself, not from parsing the markdown, so the pictures cannot
drift from what the code produces.

    python3 docs/make_visuals.py        # needs Chrome; writes docs/*.png
"""
from __future__ import annotations

import pathlib
import statistics
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from callscore import render  # noqa: E402
from run_day import process, team_medians  # noqa: E402
from run_week import collect  # noqa: E402

DOCS = ROOT / "docs"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,'Segoe UI',Inter,Helvetica,Arial,sans-serif;background:#eef1f4;padding:26px}
.card{background:#fff;border-radius:14px;border:1px solid #e3e7eb;box-shadow:0 1px 3px rgba(16,22,26,.07);
      padding:22px 24px;max-width:720px}
.top{display:flex;align-items:center;gap:11px;padding-bottom:13px;border-bottom:1px solid #eef1f4;margin-bottom:15px}
.av{width:38px;height:38px;border-radius:9px;background:#47809E;color:#fff;font-weight:700;font-size:16px;
    display:flex;align-items:center;justify-content:center}
.who{font-weight:700;font-size:15px;color:#1b1f24}
.sub{font-size:12.5px;color:#7d858e;margin-top:1px}
.tiles{display:flex;gap:9px;margin-bottom:17px}
.tile{flex:1;background:#f7f9fb;border:1px solid #e8ecf0;border-radius:9px;padding:9px 11px}
.tl{font-size:10px;letter-spacing:.7px;text-transform:uppercase;color:#8b939b;font-weight:700}
.tv{font-size:19px;font-weight:700;color:#1b1f24;margin-top:3px}
.tv small{font-size:12px;font-weight:600;color:#9aa1a8}
.tteam{font-size:11px;color:#8b939b;margin-top:2px}
h3{font-size:11px;letter-spacing:.8px;text-transform:uppercase;margin:15px 0 6px;font-weight:700}
.good h3{color:#2f8f52}.miss h3{color:#c07a1e}.do h3{color:#47809E}
p{font-size:13.5px;line-height:1.55;color:#2c3238}
.q{border-left:3px solid #d9e2e8;padding-left:11px;margin-top:7px;font-style:italic;color:#5b636b;font-size:13px}
.bar{height:7px;background:#eef1f4;border-radius:4px;overflow:hidden;margin-top:4px}
.bar span{display:block;height:100%;background:#93B8CA}
.bar.low span{background:#e0a94f}
.row{display:flex;align-items:center;gap:11px;margin-bottom:8px}
.row .lab{width:210px;font-size:12.5px;color:#2c3238}
.row .num{width:56px;text-align:right;font-size:12.5px;font-weight:700;color:#1b1f24}
.row .track{flex:1}
.split{display:flex;gap:11px;margin:14px 0 4px}
.big{flex:1;border-radius:10px;padding:12px 14px}
.big.on{background:#eef6f0;border:1px solid #cfe6d8}
.big.off{background:#fbf3e8;border:1px solid #f0dfc4}
.bignum{font-size:25px;font-weight:700;color:#1b1f24}
.biglab{font-size:11.5px;color:#6b737b;margin-top:2px}
.note{font-size:11.5px;color:#8b939b;font-style:italic;margin-top:11px;line-height:1.5}
.hdr{font-size:17px;font-weight:700;color:#1b1f24}
.leg{font-size:10.5px;color:#8b939b;margin-top:-6px}
.chip{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;
      padding:3px 8px;border-radius:20px;background:#eef4f8;color:#47809E;margin-left:8px;vertical-align:2px}
"""


def week_of(date: str) -> str:
    """Two fixture weeks: 18–22 May and 26–29 May."""
    return "week 1" if date <= "2026-05-22" else "week 2"


def svg_trend(weeks: list, framing: list, engagement: list) -> str:
    """Week-over-week: framing-pair share as bars, median engagement as a line over them."""
    W, H, PAD_L, PAD_B, TOP = 330, 150, 30, 24, 12
    plot_h = H - PAD_B - TOP
    bw, gap = 62, 76
    parts = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    for gy in (0, 25, 50, 75, 100):
        y = TOP + plot_h - plot_h * gy / 100
        parts.append(f'<line x1="{PAD_L}" y1="{y:.0f}" x2="{W-10}" y2="{y:.0f}" stroke="#eef1f4"/>')
        parts.append(f'<text x="{PAD_L-6}" y="{y+3:.0f}" font-size="8" fill="#a5acb3" '
                     f'text-anchor="end">{gy}</text>')
    for i, (wk, f, e) in enumerate(zip(weeks, framing, engagement)):
        x = PAD_L + 22 + i * (bw + gap)
        h = plot_h * f / 100
        parts.append(f'<rect x="{x}" y="{TOP+plot_h-h:.0f}" width="{bw}" height="{h:.0f}" rx="3" fill="#93B8CA"/>')
        parts.append(f'<text x="{x+bw/2:.0f}" y="{TOP+plot_h-h+15:.0f}" font-size="11" font-weight="700" '
                     f'fill="#ffffff" text-anchor="middle">{f}%</text>')
        parts.append(f'<text x="{x+bw/2:.0f}" y="{H-8}" font-size="9.5" fill="#7d858e" '
                     f'text-anchor="middle">{wk}</text>')
    pts = [(PAD_L + 22 + i * (bw + gap) + bw / 2, TOP + plot_h - plot_h * e / 100)
           for i, e in enumerate(engagement)]
    parts.append('<polyline points="' + " ".join(f"{x:.0f},{y:.0f}" for x, y in pts) +
                 '" fill="none" stroke="#75905A" stroke-width="2"/>')
    for (x, y), e in zip(pts, engagement):
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4" fill="#fff" stroke="#75905A" stroke-width="2"/>')
        parts.append(f'<text x="{x:.0f}" y="{y-11:.0f}" font-size="10" font-weight="700" fill="#5d7548" '
                     f'text-anchor="middle">{e}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_reps(names: list, w1: list, w2: list) -> str:
    """Message elements delivered per rep, week 1 vs week 2."""
    W, H, TOP, PAD_B = 330, 150, 12, 24
    plot_h = H - PAD_B - TOP
    group, bw = 78, 22
    parts = [f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
    for gy in (0, 2, 4, 6):
        y = TOP + plot_h - plot_h * gy / 6
        parts.append(f'<line x1="24" y1="{y:.0f}" x2="{W-8}" y2="{y:.0f}" stroke="#eef1f4"/>')
        parts.append(f'<text x="18" y="{y+3:.0f}" font-size="8" fill="#a5acb3" text-anchor="end">{gy}</text>')
    for i, (n, a, b) in enumerate(zip(names, w1, w2)):
        x = 30 + i * group
        for j, (v, col) in enumerate(((a, "#cfdde5"), (b, "#47809E"))):
            h = plot_h * v / 6
            parts.append(f'<rect x="{x + j*(bw+4)}" y="{TOP+plot_h-h:.0f}" width="{bw}" '
                         f'height="{h:.0f}" rx="3" fill="{col}"/>')
            parts.append(f'<text x="{x + j*(bw+4) + bw/2:.0f}" y="{TOP+plot_h-h-4:.0f}" font-size="9" '
                         f'font-weight="700" fill="#5b636b" text-anchor="middle">{v}</text>')
        parts.append(f'<text x="{x+bw+2:.0f}" y="{H-8}" font-size="9.5" fill="#7d858e" '
                     f'text-anchor="middle">{n}</text>')
    parts.append("</svg>")
    return "".join(parts)


def shot(html: str, name: str, w: int, h: int):
    tmp = DOCS / f"_{name}.html"
    tmp.write_text(f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{CSS}</style></head>"
                   f"<body>{html}</body></html>")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                    f"--screenshot={DOCS / (name + '.png')}", f"--window-size={w},{h}",
                    "--force-device-scale-factor=2", f"file://{tmp}"],
                   capture_output=True)
    tmp.unlink()
    print(f"  docs/{name}.png")


def tiles(you_msg, team_msg, you_eng, team_eng, you_step, team_step):
    return f"""<div class="tiles">
      <div class="tile"><div class="tl">Message delivered</div>
        <div class="tv">{you_msg} <small>of 6</small></div><div class="tteam">team {team_msg} of 6</div></div>
      <div class="tile"><div class="tl">Engagement</div>
        <div class="tv">{you_eng}<small>/100</small></div><div class="tteam">team {team_eng}/100</div></div>
      <div class="tile"><div class="tl">Next step reached</div>
        <div class="tv">{you_step} <small>of 4</small></div><div class="tteam">team {team_step} of 4</div></div>
    </div>"""


def main():
    rows, _ = process(ROOT / "fixtures" / "transcripts", "mock", None, None)
    team = team_medians(rows)
    week_rows = collect(ROOT / "fixtures" / "transcripts", "mock")
    print("rendering:")

    # ---------- ① daily coaching ----------
    mine = [r for r in rows if r["rep"] == "Ana" and r["date"] == "2026-05-18"]
    pitch = [r for r in mine if r["message"]]
    best = max(mine, key=lambda r: r["engagement"]["score"])
    exc = best["record"]["engagement"]["excitement"]
    shot(f"""<div class="card">
      <div class="top"><div class="av">A</div>
        <div><div class="who">Ana <span class="chip">daily</span></div>
        <div class="sub">2026-05-18 · 2 calls (1 pitch, 1 commercial or logistics)</div></div></div>
      {tiles(pitch[0]['message']['delivered'], team['delivered'],
             round(statistics.median([r['engagement']['score'] for r in mine])), team['engagement'],
             round(statistics.median([r['engagement']['next_step_level'] for r in mine])), team['next_step'])}
      <div class="good"><h3>What worked</h3><p>{best['account']} was your strongest call —
        engagement {best['engagement']['score']}/100.</p>
        <div class="q">“{exc[0]['quote']}”</div></div>
      <div class="miss"><h3>What you missed</h3><p>On {pitch[0]['account']} you did not land:
        <strong>the problem</strong> and <strong>the category</strong> — the two that separate the new
        message from the old pitch.</p></div>
      <div class="do"><h3>What to improve</h3><p>Say the problem out loud before you move into the product.
        <em>Done looks like:</em> it appears in the first two minutes of the call.</p></div>
    </div>""", "example-daily-coaching", 790, 470)

    # ---------- ② weekly coaching ----------
    wk = [r for r in week_rows if r["rep"] == "Ana"]
    wp = [r for r in wk if r["message"]]
    counts = {}
    for r in wp:
        for m in r["message"]["missing"]:
            counts[m] = counts.get(m, 0) + 1
    worst, hits = max(counts.items(), key=lambda kv: kv[1])
    wteam = {
        "delivered": round(statistics.median([r["message"]["delivered"] for r in week_rows if r["message"]])),
        "engagement": round(statistics.median([r["engagement"]["score"] for r in week_rows])),
        "next_step": round(statistics.median([r["engagement"]["next_step_level"] for r in week_rows])),
    }
    wbest = max(wk, key=lambda r: r["engagement"]["score"])
    shot(f"""<div class="card">
      <div class="top"><div class="av">A</div>
        <div><div class="who">Ana <span class="chip">weekly</span></div>
        <div class="sub">week of 18–21 May 2026 · {len(wk)} calls ({len(wp)} pitches)</div></div></div>
      {tiles(round(statistics.mean([r['message']['delivered'] for r in wp])), wteam['delivered'],
             round(statistics.median([r['engagement']['score'] for r in wk])), wteam['engagement'],
             round(statistics.median([r['engagement']['next_step_level'] for r in wk])), wteam['next_step'])}
      <div class="good"><h3>What worked</h3><p>{wbest['account']} was your strongest call this week —
        engagement {wbest['engagement']['score']}/100.</p></div>
      <div class="miss"><h3>What you missed</h3><p><strong>{render.LABELS[worst].capitalize()}</strong>
        went unsaid in <strong>{hits} of your {len(wp)} pitches</strong> this week.
        A day says you skipped it on one call; a week says you skip it.</p></div>
      <div class="do"><h3>What to improve</h3><p>Say {render.LABELS[worst]} out loud before you move into
        the product. <em>Done looks like:</em> it appears in the first two minutes of the call.</p></div>
    </div>""", "example-weekly-coaching", 790, 430)

    # ---------- ③ messaging analysis ----------
    pitches = [r for r in week_rows if r["message"]]
    framing = [r for r in pitches if r["message"]["framing_pair"]]
    on = round(statistics.mean([r["engagement"]["score"] for r in framing]))
    off = round(statistics.mean([r["engagement"]["score"] for r in pitches
                                 if not r["message"]["framing_pair"]]))
    ids = ["problem_framing", "category", "promise_visibility", "promise_proactive",
           "promise_moat", "promise_durable"]
    bars = ""
    for i in ids:
        appl = [r for r in pitches if r["record"]["adherence"][i]["status"] in ("delivered", "absent")]
        d = sum(1 for r in appl if r["record"]["adherence"][i]["status"] == "delivered")
        pct = round(d / len(appl) * 100)
        bars += (f'<div class="row"><div class="lab">{render.LABELS[i]}</div>'
                 f'<div class="track"><div class="bar{" low" if pct < 60 else ""}">'
                 f'<span style="width:{pct}%"></span></div></div>'
                 f'<div class="num">{d} of {len(appl)}</div></div>')
    echo = next(r for r in week_rows if r["echo"])

    wk_names, wk_framing, wk_eng, rep_w1, rep_w2 = [], [], [], [], []
    for wk in ("week 1", "week 2"):
        wr = [r for r in week_rows if week_of(r["date"]) == wk]
        wp2 = [r for r in wr if r["message"]]
        wk_names.append(wk)
        wk_framing.append(round(sum(1 for r in wp2 if r["message"]["framing_pair"]) / len(wp2) * 100))
        wk_eng.append(round(statistics.median([r["engagement"]["score"] for r in wr])))
    reps = sorted({r["rep"] for r in week_rows})
    for rep in reps:
        for bucket, wk in ((rep_w1, "week 1"), (rep_w2, "week 2")):
            rp = [r for r in week_rows if r["rep"] == rep and r["message"]
                  and week_of(r["date"]) == wk]
            bucket.append(round(statistics.mean([r["message"]["delivered"] for r in rp])) if rp else 0)

    charts = (
        '<div style="display:flex;gap:14px;margin:4px 0">'
        '<div style="flex:1"><div class="tl" style="margin-bottom:3px">'
        'Framing pair &amp; engagement, by week</div>' + svg_trend(wk_names, wk_framing, wk_eng) +
        '<div class="leg"><span style="color:#93B8CA">&#9646;</span> framing pair, % of pitches'
        ' &nbsp; <span style="color:#75905A">&#9679;</span> median engagement</div></div>'
        '<div style="flex:1"><div class="tl" style="margin-bottom:3px">'
        'Elements delivered, per rep</div>' + svg_reps(reps, rep_w1, rep_w2) +
        '<div class="leg"><span style="color:#cfdde5">&#9646;</span> week 1 &nbsp;'
        '<span style="color:#47809E">&#9646;</span> week 2 &nbsp;&middot; out of 6</div></div>'
        '</div>')

    shot(f"""<div class="card">
      <div class="top"><div class="av" style="background:#75905A">M</div>
        <div><div class="who">Messaging analysis <span class="chip">weekly</span></div>
        <div class="sub">18–29 May 2026 · {len(week_rows)} calls · {len(pitches)} pitches ·
        {len(week_rows) - len(pitches)} carried no product story</div></div></div>

      <h3 style="color:#47809E;margin-top:2px">The trend</h3>
      {charts}

      <h3 style="color:#47809E">Is the team sticking to the message?</h3>
      <p style="margin-bottom:11px">The framing pair — the problem <em>and</em> the category, landing
      together — held in <strong>{len(framing)} of {len(pitches)} pitches</strong>.</p>
      {bars}

      <h3 style="color:#47809E;margin-top:16px">Is it landing?</h3>
      <div class="split">
        <div class="big on"><div class="bignum">{on}<span style="font-size:14px">/100</span></div>
          <div class="biglab">pitches where the framing landed &nbsp;·&nbsp; n={len(framing)}</div></div>
        <div class="big off"><div class="bignum">{off}<span style="font-size:14px">/100</span></div>
          <div class="biglab">where it did not &nbsp;·&nbsp; n={len(pitches) - len(framing)}</div></div>
      </div>
      <p class="note">Read that as a hypothesis, not a finding. Reps who deliver the whole message may
      also be working better accounts — with this many calls the two cannot be separated.</p>

      <h3 style="color:#2f8f52;margin-top:15px">Where it came back at us</h3>
      <div class="q">“{echo['echo'][0]['quote']}”<br><span style="font-style:normal;font-size:11.5px">
      — {echo['account']} · recorded, never scored</span></div>
    </div>""", "example-messaging-analysis", 830, 730)


if __name__ == "__main__":
    main()
