"""Loads the rubric. These four files are the only thing a user should need to edit."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUBRIC = ROOT / "rubric"

def _load(name):
    return json.loads((RUBRIC / name).read_text())

def message_rubric():    return _load("message_rubric.json")
def engagement_rubric(): return _load("engagement_rubric.json")
def scope_rules():       return _load("scope.json")


def expected_for(call_type: str) -> set:
    """Elements that are table stakes for this kind of meeting (Decision 13)."""
    m = message_rubric().get("expected_by_call_type", {})
    return set(m.get(call_type, []))
