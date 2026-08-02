"""Model backends. The interface is the only seam where a model touches this system."""
from __future__ import annotations

from .base import Extractor, load_transcript
from .mock import MockExtractor

def get(name: str) -> Extractor:
    """Config-selected backend. `mock` is the default so the repo runs with no key and no network."""
    if name == "mock":
        return MockExtractor()
    if name in ("claude_api", "claude_cli", "codex_cli", "ollama"):
        raise NotImplementedError(
            f"The {name} backend is not wired up in v0.1. The interface it must implement is in "
            "callscore/extractors/base.py — one method, ~40 lines. See the README section "
            "'Bring your own model'."
        )
    raise ValueError(f"unknown extractor: {name}")
