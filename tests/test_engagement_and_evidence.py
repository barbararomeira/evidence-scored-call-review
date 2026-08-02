"""Weights, the short-call rule, and evidence in both directions."""
import json, pathlib
from callscore.evidence import quote_supported, verify
from callscore.score_engagement import score

RUBRIC = json.loads((pathlib.Path(__file__).resolve().parent.parent /
                     "rubric" / "engagement_rubric.json").read_text())

def test_weights_sum_to_100():
    assert sum(c["weight"] for c in RUBRIC["components"]) == 100

def test_echo_is_declared_but_never_scored():
    scored_ids = {c["id"] for c in RUBRIC["components"]}
    assert "echo" not in scored_ids
    assert any(x["id"] == "echo" for x in RUBRIC["recorded_not_scored"])

def _eng(level=0, situations=0, excitement=0, q=0, turns=0, per30=0):
    return {"next_step_reached": {"level": level},
            "own_situations": [{}] * situations, "excitement": [{}] * excitement,
            "back_and_forth": {"questions": q, "substantive_turns": turns, "per_30min": per30}}

def test_short_call_uses_raw_count_not_extrapolation():
    """A 9-minute logistics call must not be inflated to half an hour of engagement."""
    short = score(_eng(q=1, turns=3, per30=13), duration_min=9)
    long_ = score(_eng(q=1, turns=3, per30=13), duration_min=30)
    assert short["components"]["back_and_forth"] < long_["components"]["back_and_forth"]

def test_excitement_is_capped():
    three = score(_eng(excitement=3), 30)["score"]
    ten = score(_eng(excitement=10), 30)["score"]
    assert three == ten

def test_quote_must_appear_in_its_own_transcript():
    assert quote_supported("the daily routine changes", "so the daily routine changes, and it holds")
    assert not quote_supported("we guarantee 40% savings", "so the daily routine changes")

def test_absent_verdicts_need_evidence_too():
    problems = verify({"category": {"status": "absent", "quote": None}}, "any transcript")
    assert problems and "no quote" in problems[0]
