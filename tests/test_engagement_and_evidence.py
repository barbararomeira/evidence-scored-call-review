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


# ── Decision 13: the score has to be able to go down ─────────────────────────────────────

def _warm():
    return {"next_step_reached": {"level": 1}, "own_situations": [1, 2, 3],
            "excitement": [{"quote": "a"}, {"quote": "b"}, {"quote": "c"}],
            "back_and_forth": {"questions": 4, "substantive_turns": 6, "per_30min": 10}}


def test_reservations_pull_the_score_down():
    warm = score(_warm(), 40)["score"]
    cooled = score(dict(_warm(), reservations=[
        {"quote": "I don't know if there's a big need for it right now", "late": True}]), 40)
    assert cooled["score"] < warm
    assert cooled["deduction"] > 0


def test_a_late_but_outweighs_an_early_one():
    early = score(dict(_warm(), reservations=[{"quote": "x", "late": False}]), 40)["score"]
    late = score(dict(_warm(), reservations=[{"quote": "x", "late": True}]), 40)["score"]
    assert late < early, "a reservation at the end of a call has to count for more"


def test_three_warm_lines_then_a_no_does_not_read_as_engaged():
    """The MillerKnoll shape: polite enthusiasm, then the rest of the call is the 'but'."""
    r = score(dict(_warm(), reservations=[
        {"quote": "I don't know if there's a big need for it currently right now", "late": True},
        {"quote": "it's more of a nice to have", "late": True},
        {"quote": "if we're insourcing something", "late": False}]), 40)
    assert r["score"] < 40, f"scored {r['score']} on a call that ended in a polite no"


def test_deduction_is_bounded_and_the_score_never_goes_negative():
    """The cap is deliberate: reservations are evidence of hesitancy, not proof of a dead deal.

    What kills a deal is the next-step ladder, which is a separate component. A noisy extraction
    pulling out ten hedges must not be able to erase a call that genuinely had substance in it.
    """
    r = score(dict(_warm(), reservations=[{"quote": str(i), "late": True} for i in range(20)]), 40)
    assert r["deduction"] == 45, "deduction must stop at the documented cap"
    assert r["score"] == r["positive"] - r["deduction"] >= 0

    thin = dict(_warm(), next_step_reached={"level": 0}, own_situations=[], excitement=[],
                back_and_forth={"questions": 0, "substantive_turns": 0, "per_30min": 0})
    assert score(dict(thin, reservations=[{"quote": "no", "late": True}] * 4), 40)["score"] == 0


def test_no_reservations_means_no_change():
    assert score(_warm(), 40)["score"] == score(dict(_warm(), reservations=[]), 40)["score"]


def test_expected_elements_are_declared_per_call_type():
    from callscore.config import expected_for
    assert "problem_framing" in expected_for("proposal"), \
        "opening on the problem IS the proposal meeting — it must not read as an achievement"
    assert expected_for("discovery") == set()
