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

from callscore import dynamics, render, tips  # noqa: E402
from run_day import process, team_medians  # noqa: E402
from run_week import collect, follow_through, most_missed, week_of  # noqa: E402

DOCS = ROOT / "docs"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600;700&family=Space+Mono:wght@700&display=swap');
:root{
  --noir:#23252B; --blue:#47809E; --blue-fill:#93B8CA; --blue-wash:#EAF2F6;
  --pink:#C4718D; --pink-fill:#EEBCCA; --pink-wash:#FAEEF2;
  --matcha:#75905A; --matcha-fill:#B2C49C; --matcha-wash:#F0F4E9;
  --muted:#8A9099; --line:#E7EBEF;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Inter,-apple-system,'Segoe UI',Helvetica,sans-serif;background:#F4F6F8;padding:26px;color:var(--noir)}
.card{background:#fff;border-radius:16px;border:1px solid var(--line);
      box-shadow:0 1px 2px rgba(35,37,43,.05);padding:24px 26px;max-width:740px}
.top{display:flex;align-items:center;gap:12px;padding-bottom:14px;border-bottom:1px solid var(--line);margin-bottom:16px}
.av{width:40px;height:40px;border-radius:10px;background:var(--blue);color:#fff;font-weight:700;font-size:17px;
    display:flex;align-items:center;justify-content:center;font-family:'Playfair Display',Georgia,serif}
.who{font-family:'Playfair Display',Georgia,serif;font-weight:700;font-size:18px;color:var(--noir)}
.sub{font-size:12.5px;color:var(--muted);margin-top:2px}
.stamp{font-family:'Space Mono',Menlo,monospace;font-weight:700;font-size:9.5px;letter-spacing:1.6px;
       text-transform:uppercase;padding:3px 9px;border-radius:4px;background:var(--blue-wash);
       color:var(--blue);margin-left:9px;vertical-align:3px}
.tiles{display:flex;gap:9px;margin-bottom:18px}
.tile{flex:1;background:#FBFCFD;border:1px solid var(--line);border-radius:10px;padding:10px 12px}
.tl{font-family:'Space Mono',Menlo,monospace;font-size:9px;letter-spacing:1px;text-transform:uppercase;
    color:var(--muted);font-weight:700}
.tv{font-size:20px;font-weight:700;color:var(--noir);margin-top:4px}
.tv small{font-size:12px;font-weight:600;color:var(--muted)}
.tteam{font-size:11px;color:var(--muted);margin-top:3px}
h3{font-family:'Space Mono',Menlo,monospace;font-size:10px;letter-spacing:1.4px;text-transform:uppercase;
   margin:16px 0 6px;font-weight:700}
.good h3{color:var(--matcha)}.miss h3{color:var(--pink)}.do h3{color:var(--blue)}.tips h3{color:var(--noir)}
p{font-size:13.5px;line-height:1.6;color:#33373E}
.q{border-left:3px solid var(--blue-fill);padding-left:12px;margin-top:8px;font-style:italic;
   color:#5B636B;font-size:13px}
.bar{height:7px;background:var(--line);border-radius:4px;overflow:hidden;margin-top:4px}
.bar span{display:block;height:100%;background:var(--blue-fill)}
.bar.low span{background:var(--pink-fill)}
.row{display:flex;align-items:center;gap:12px;margin-bottom:8px}
.row .lab{width:210px;font-size:12.5px}
.row .num{width:58px;text-align:right;font-size:12.5px;font-weight:700}
.row .track{flex:1}
.split{display:flex;gap:11px;margin:14px 0 4px}
.big{flex:1;border-radius:11px;padding:13px 15px}
.big.on{background:var(--matcha-wash);border:1px solid var(--matcha-fill)}
.big.off{background:var(--pink-wash);border:1px solid var(--pink-fill)}
.bignum{font-family:'Playfair Display',Georgia,serif;font-size:27px;font-weight:700}
.biglab{font-size:11.5px;color:#6B737B;margin-top:3px}
.note{font-size:11.5px;color:var(--muted);font-style:italic;margin-top:12px;line-height:1.55}
.leg{font-size:10.5px;color:var(--muted);margin-top:-6px}
.tiprow{display:flex;align-items:flex-start;gap:10px;padding:9px 0;border-top:1px solid var(--line)}
.pill{font-family:'Space Mono',Menlo,monospace;font-size:9px;font-weight:700;letter-spacing:.8px;
      text-transform:uppercase;padding:4px 8px;border-radius:4px;white-space:nowrap}
.pill.adopted{background:var(--matcha-wash);color:var(--matcha)}
.pill.partial{background:var(--blue-wash);color:var(--blue)}
.pill.notyet{background:var(--pink-wash);color:var(--pink)}
.pill.none{background:#F2F4F6;color:var(--muted)}
.tipid{font-family:'Space Mono',Menlo,monospace;font-size:10px;color:var(--muted)}
"""


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


EXAMPLES = ROOT / "examples"
PDF_NAMES = {"example-daily-coaching": "02_daily_coaching_Ana",
             "example-weekly-coaching": "03_weekly_coaching_Ana",
             "example-messaging-analysis": "05_weekly_messaging_analysis"}


def shot(html: str, name: str, w: int, h: int):
    """PNG for the README, PDF for examples/ — same HTML, so they always agree."""
    tmp = DOCS / f"_{name}.html"
    page = (f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{CSS}"
            f"@page{{size:{w+40}px {h+40}px;margin:0}}body{{padding:20px}}"
            f"</style></head><body>{html}</body></html>")
    tmp.write_text(page)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                    f"--screenshot={DOCS / (name + '.png')}", f"--window-size={w},{h}",
                    "--force-device-scale-factor=2", f"file://{tmp}"], capture_output=True)
    pdf = EXAMPLES / f"{PDF_NAMES[name]}.pdf"
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", f"file://{tmp}"], capture_output=True)
    tmp.unlink()
    print(f"  docs/{name}.png  +  examples/{pdf.name}")


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
        <div><div class="who">Ana <span class="stamp">daily</span></div>
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
    </div>""", "example-daily-coaching", 790, 455)

    # ---------- ② weekly coaching ----------
    wk = [r for r in week_rows if r["rep"] == "Ana"]
    wp = [r for r in wk if r["message"]]
    w2 = [r for r in wk if week_of(r["date"]) == "week 2"]
    w1 = [r for r in wk if week_of(r["date"]) == "week 1"]
    el, hits, of_n = most_missed([r for r in w2 if r["message"]])
    wteam = {
        "delivered": round(statistics.median([r["message"]["delivered"] for r in week_rows if r["message"]])),
        "engagement": round(statistics.median([r["engagement"]["score"] for r in week_rows])),
        "step": round(statistics.median([r["engagement"]["next_step_level"] for r in week_rows])),
    }
    now_d = round(statistics.mean([r["message"]["delivered"] for r in w2 if r["message"]]))
    prev_d = round(statistics.mean([r["message"]["delivered"] for r in w1 if r["message"]]))
    now_e = round(statistics.median([r["engagement"]["score"] for r in w2]))
    prev_e = round(statistics.median([r["engagement"]["score"] for r in w1]))
    now_s = round(statistics.median([r["engagement"]["next_step_level"] for r in w2]))
    w2p = [r for r in w2 if r["message"]]
    lo = min(r["message"]["delivered"] for r in w2p)
    hi = max(r["message"]["delivered"] for r in w2p)
    weakest = min(w2p, key=lambda r: r["message"]["delivered"])
    ft = follow_through("Ana", week_rows)
    best = max(w2, key=lambda r: r["engagement"]["score"])
    open_tips = tips.register("Ana", w1, w2, "2026W21")
    types = {}
    for r in w2:                      # the reporting week, not the whole span
        types[r["call_type"]] = types.get(r["call_type"], 0) + 1
    mix = " · ".join(f"{v} {k}" for k, v in sorted(types.items(), key=lambda kv: -kv[1]))

    def delta(now, before):
        if now == before:
            return '<span style="color:#8A9099">= same as last week</span>'
        arrow, col = ("▲", "#75905A") if now > before else ("▼", "#C4718D")
        return f'<span style="color:{col}">{arrow} from {before} last week</span>'

    PILL = {"Adopted": "adopted", "Partial": "partial", "Not yet": "notyet", "No evidence yet": "none"}
    tiprows = ""
    for t in open_tips:
        tiprows += (f'<div class="tiprow"><span class="pill {PILL[t["status"]]}">{t["status"]}</span>'
                    f'<div><div style="font-size:13px">Say <strong>{render.LABELS[t["element"]]}</strong> '
                    f'before you move into the product '
                    f'<span class="tipid">· {t["id"]}</span></div>'
                    f'<div style="font-size:11.5px;color:#8A9099;margin-top:2px">'
                    f'raised after {t["missed_then"]} of {t["of_then"]} pitches missed it · '
                    f'{t["evidence"]}</div></div></div>')

    shot(f"""<div class="card">
      <div class="top"><div class="av">A</div>
        <div><div class="who">Ana <span class="stamp">weekly</span></div>
        <div class="sub">week of 26–29 May 2026 · {len(w2)} calls: {mix}</div></div></div>

      <div class="tiles">
        <div class="tile"><div class="tl">Message delivered</div>
          <div class="tv">{now_d} <small>of 6</small></div>
          <div class="tteam">{delta(now_d, prev_d)}<br>team {wteam['delivered']} of 6</div></div>
        <div class="tile"><div class="tl">Engagement</div>
          <div class="tv">{now_e}<small>/100</small></div>
          <div class="tteam">{delta(now_e, prev_e)}<br>team {wteam['engagement']}/100</div></div>
        <div class="tile"><div class="tl">Next step</div>
          <div class="tv">{now_s} <small>of 4</small></div>
          <div class="tteam">team {wteam['step']} of 4</div></div>
        <div class="tile"><div class="tl">Consistency</div>
          <div class="tv">{lo}–{hi} <small>of 6</small></div>
          <div class="tteam">{weakest['account']} pulls the bottom</div></div>
      </div>

      <div class="good"><h3>Since last week</h3>
        <p>{ft.replace('*Last week you were skipping ', '<strong>Last week you were skipping ').replace('* — ', '</strong> — ')}</p></div>

      <div class="good"><h3>What worked</h3>
        <p>{best['account']} was your strongest call — engagement {best['engagement']['score']}/100.</p></div>

      <div class="miss"><h3>The pattern to fix</h3>
        <p><strong>{render.LABELS[el].capitalize()}</strong> went unsaid in <strong>{hits} of your
        {of_n} pitches</strong>. One call is a slip; {hits} is a habit.</p></div>

      <div class="do"><h3>What to improve</h3><p>Say {render.LABELS[el]} out loud before you move
        into the product. <em>Done looks like:</em> it appears in the first two minutes.</p></div>

      <div class="tips"><h3>Your open tips</h3>{tiprows}</div>
    </div>""", "example-weekly-coaching", 800, 545)

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

    tally = dynamics.roll_up(week_rows)
    mx = max(max(v["lifts"], v["drops"]) for v in tally.values()) or 1
    dynrows = ""
    for el, v in sorted(tally.items(), key=lambda kv: -kv[1]["lifts"]):
        dynrows += (f'<div class="row"><div class="lab">{render.LABELS[el]}</div>'
                    f'<div class="track"><div class="bar"><span style="width:{v["lifts"]/mx*100:.0f}%">'
                    f'</span></div></div>'
                    f'<div class="num" style="width:96px;font-weight:600;font-size:11.5px">'
                    f'<span style="color:var(--matcha)">{v["lifts"]} lifts</span> · '
                    f'<span style="color:var(--pink)">{v["drops"]}</span></div></div>')

    reprows = ('<div class="row" style="font-family:\'Space Mono\',monospace;font-size:9px;'
               'letter-spacing:1px;text-transform:uppercase;color:#8A9099;margin-bottom:4px">'
               '<div class="lab">rep</div><div class="track">pitches · elements · framing pair</div>'
               '<div class="num" style="width:74px">eng.</div></div>')
    for rep in sorted({r["rep"] for r in week_rows}):
        rp = [r for r in pitches if r["rep"] == rep]
        if not rp:
            continue
        avg = round(statistics.mean([r["message"]["delivered"] for r in rp]), 1)
        fp = sum(1 for r in rp if r["message"]["framing_pair"])
        eng = round(statistics.median([r["engagement"]["score"] for r in week_rows if r["rep"] == rep]))
        reprows += (f'<div class="row"><div class="lab" style="font-weight:600">{rep}</div>'
                    f'<div class="track" style="font-size:12.5px;color:#5B636B">{len(rp)} pitches · '
                    f'{avg} of 6 elements · framing pair {fp} of {len(rp)}</div>'
                    f'<div class="num" style="width:74px">{eng}/100</div></div>')

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
        '<div class="leg"><span style="color:#C9DBE4">&#9646;</span> week 1 &nbsp;'
        '<span style="color:var(--blue)">&#9646;</span> week 2 &nbsp;&middot; out of 6</div></div>'
        '</div>')

    shot(f"""<div class="card">
      <div class="top"><div class="av" style="background:var(--matcha)">M</div>
        <div><div class="who">Messaging analysis <span class="stamp">weekly</span></div>
        <div class="sub">18–29 May 2026 · {len(week_rows)} calls · {len(pitches)} pitches ·
        {len(week_rows) - len(pitches)} carried no product story</div></div></div>

      <h3 style="color:var(--blue);margin-top:2px">The trend</h3>
      {charts}

      <h3 style="color:var(--blue)">Is the team sticking to the message?</h3>
      <p style="margin-bottom:11px">The framing pair — the problem <em>and</em> the category, landing
      together — held in <strong>{len(framing)} of {len(pitches)} pitches</strong>.</p>
      {bars}

      <h3 style="color:var(--blue);margin-top:16px">Is it landing?</h3>
      <div class="split">
        <div class="big on"><div class="bignum">{on}<span style="font-size:14px">/100</span></div>
          <div class="biglab">pitches where the framing landed &nbsp;·&nbsp; n={len(framing)}</div></div>
        <div class="big off"><div class="bignum">{off}<span style="font-size:14px">/100</span></div>
          <div class="biglab">where it did not &nbsp;·&nbsp; n={len(pitches) - len(framing)}</div></div>
      </div>
      <p class="note">Read that as a hypothesis, not a finding. Reps who deliver the whole message may
      also be working better accounts — with this many calls the two cannot be separated.</p>

      <h3 style="color:var(--blue);margin-top:16px">What earns attention, what loses the room</h3>
      <p style="margin-bottom:9px;font-size:12.5px;color:#6B737B">A lift is the buyer saying
      something real straight after an element lands. A drop is three or more rep turns with no
      reply, or an explicit deflection.</p>
      {dynrows}

      <h3 style="color:var(--blue);margin-top:16px">Who is delivering it</h3>
      {reprows}

      <h3 style="color:var(--matcha);margin-top:15px">Where it came back at us</h3>
      <div class="q">“{echo['echo'][0]['quote']}”<br><span style="font-style:normal;font-size:11.5px">
      — {echo['account']} · recorded, never scored</span></div>
    </div>""", "example-messaging-analysis", 830, 1145)


if __name__ == "__main__":
    main()
