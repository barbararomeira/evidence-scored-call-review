"""Rebuild docs/demo.gif from whatever the code actually prints today.

    python3 docs/make_demo_gif.py

The previous demo.gif had no generator. It was recorded once and the numbers were baked into
pixels, so when the fixtures grew it kept showing "20 calls · 14 pitches" while the code printed
25 and 19 — a screenshot quietly disagreeing with the thing it was a screenshot of. An asset
nobody can regenerate is an asset that goes stale silently, which is the same reason the hero
frames and the team one-pager both ship with builders.

Requires Pillow. Nothing else in this repo does; the pipeline itself is stdlib only.
"""
from __future__ import annotations

import pathlib
import subprocess
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("needs Pillow:  python3 -m pip install pillow")

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "demo.gif"

BG, FG, DIM = "#1E2128", "#D7DAE0", "#8A9099"
GREEN, AMBER, BLUE = "#7FB894", "#D6A247", "#7FA8C9"
FONT = "/System/Library/Fonts/Menlo.ttc"
SIZE, LEAD, PAD = 13, 19, 18
WIDTH = 820

COMMANDS = [
    ("python3 run_day.py --mock --date 2026-05-21", ["run_day.py", "--mock", "--date", "2026-05-21"]),
    ("python3 run_week.py --mock", ["run_week.py", "--mock"]),
]


def capture() -> list[str]:
    lines: list[str] = []
    for shown, argv in COMMANDS:
        lines.append(f"$ {shown}")
        r = subprocess.run([sys.executable, *argv], cwd=ROOT, capture_output=True, text=True)
        body = [l.rstrip() for l in (r.stdout or r.stderr).splitlines()]
        # the coaching-file list at the end is noise in a demo; stop at it
        cut = next((i for i, l in enumerate(body) if l.strip().startswith("Message checks written")), len(body))
        lines += body[:cut]
        lines.append("")
    return [l for l in lines if l is not None]


def colour(line: str) -> str:
    s = line.strip()
    if s.startswith("$"):
        return GREEN
    if "not enough data yet" in s or "not scored" in s or s.startswith("—"):
        return AMBER
    if s.startswith("Every scored point") or s.startswith("Scored for message"):
        return BLUE
    if s.startswith("call ") or set(s) <= set("─ "):
        return DIM
    return FG


def render(lines: list[str], upto: int, font, height: int) -> Image.Image:
    im = Image.new("RGB", (WIDTH, height), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, WIDTH, 26], fill="#282C34")
    for i, c in enumerate(("#E06C60", "#D6A247", "#7FB894")):
        d.ellipse([PAD + i * 17, 9, PAD + i * 17 + 9, 18], fill=c)
    d.text((WIDTH // 2 - 92, 7), "evidence-scored-call-review", font=font, fill=DIM)
    y = 38
    for line in lines[:upto]:
        d.text((PAD, y), line[:96], font=font, fill=colour(line))
        y += LEAD
    return im


def main() -> int:
    lines = capture()
    font = ImageFont.truetype(FONT, SIZE)
    height = 38 + LEAD * len(lines) + PAD
    # reveal a few lines at a time, then hold on the finished screen
    steps = list(range(0, len(lines) + 1, 2)) + [len(lines)]
    frames = [render(lines, n, font, height) for n in steps]
    durations = [110] * (len(frames) - 1) + [4000]
    frames = [f.quantize(colors=64, method=Image.MAXCOVERAGE) for f in frames]
    frames[0].save(OUT, save_all=True, append_images=frames[1:], duration=durations,
                   loop=0, optimize=True, disposal=2)
    print(f"{OUT.relative_to(ROOT)} — {OUT.stat().st_size // 1024} KB, "
          f"{len(frames)} frames, {len(lines)} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
