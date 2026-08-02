"""Build the README hero GIF from the stage frames in `docs/frames/`.

    python3 docs/make_hero_gif.py

Each frame lights up one more step of the pipeline, so the animation reads as the shape of the
system rather than as decoration. The last frame holds long enough to actually be read.

One non-obvious thing, because it cost an evening: **each frame gets its own colour table.**
Only the final frame contains the green node, so a palette sampled across all four frames sees
green as 0.08% of the pixels and drops it — the node renders grey and the payoff disappears.
GIF allows a local colour table per frame; Pillow writes one when the frames arrive already
quantised individually. MAXCOVERAGE is used over the default MEDIANCUT for the same reason: it
keeps small regions of saturated colour that a frequency-driven method discards.

Requires Pillow. Nothing else in this repo does — the pipeline itself is stdlib only.
"""
from __future__ import annotations

import pathlib
import sys

try:
    from PIL import Image, ImageSequence
except ImportError:
    sys.exit("needs Pillow:  python3 -m pip install pillow")

DOCS = pathlib.Path(__file__).parent
OUT = DOCS / "how-it-works.gif"
HOLD_MS = 900          # per build-up frame
FINAL_MS = 3200        # the complete pipeline, long enough to read


def build() -> pathlib.Path:
    paths = sorted(DOCS.glob("frames/stage-*.png"))
    if not paths:
        sys.exit(f"no frames found in {DOCS / 'frames'}")

    frames = [
        Image.open(p).convert("RGB").quantize(colors=256, method=Image.MAXCOVERAGE)
        for p in paths
    ]
    durations = [HOLD_MS] * (len(frames) - 1) + [FINAL_MS]
    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return OUT


def check(out: pathlib.Path) -> None:
    """The green node is the thing most likely to be silently lost. Assert it survived."""
    last = list(ImageSequence.Iterator(Image.open(out)))[-1].convert("RGB")
    green = sum(1 for p in last.getdata() if p[1] > p[0] + 25 and p[1] > p[2] + 25)
    print(f"{out.relative_to(DOCS.parent)} — {out.stat().st_size // 1024} KB, "
          f"{len(list(ImageSequence.Iterator(Image.open(out))))} frames, {green} green px")
    if green < 500:
        sys.exit("the green node did not survive quantisation — see the note in this file")


if __name__ == "__main__":
    check(build())
