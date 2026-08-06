"""Offline extractor: replays a pre-recorded call record for each fixture transcript.

The mock swaps ONLY this step. Every score, gate, selection and rollup downstream is
real code executing — which is the point of putting the seam here.
"""
from __future__ import annotations

import json, pathlib
from .base import Extractor, Transcript

RECORDS = pathlib.Path(__file__).resolve().parent.parent.parent / "fixtures" / "call_records"

class MockExtractor(Extractor):
    def extract(self, t: Transcript) -> dict:
        p = RECORDS / f"{t.call_id}.json"
        if not p.exists():
            raise FileNotFoundError(
                f"No mock record for {t.call_id}. Mock mode replays fixtures/call_records/; "
                "to score your own transcripts you need a real backend."
            )
        return json.loads(p.read_text())
