"""The one seam where a model touches this system.

Everything downstream — both scores, the scope gate, the message check, the weekly rollup — is
deterministic Python reading the call record this produces. That is what makes "extract once,
analyse many times" true rather than a slogan (Decision 1).

To add a backend: implement `extract`, return a dict matching the call-record shape in
`fixtures/call_records/`, and register it in `__init__.get`. The prompt should hand the model
`rubric/positioning.md` plus `rubric/message_rubric.json` and require a verbatim quote for
every verdict — including every `absent`.
"""
from __future__ import annotations

from dataclasses import dataclass
import pathlib, re

@dataclass
class Transcript:
    call_id: str
    date: str
    rep: str
    call_type: str
    account: str
    duration_min: int
    body: str

def load_transcript(path: pathlib.Path) -> Transcript:
    raw = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
    if not m:
        raise ValueError(f"{path.name}: expected YAML front matter with call_id, date, rep, call_type")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return Transcript(
        call_id=meta["call_id"], date=meta["date"], rep=meta["rep"],
        call_type=meta["call_type"], account=meta.get("account", ""),
        duration_min=int(meta.get("duration_min", 0)), body=m.group(2),
    )

class Extractor:
    """Transcript in, one call record out. Nothing else in this repo calls a model."""
    def extract(self, t: Transcript) -> dict:
        raise NotImplementedError
