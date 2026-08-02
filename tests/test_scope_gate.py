"""The scope gate is the reason this repo exists. Pin it."""
from callscore.scope import in_scope

NA = {"status": "n/a", "quote": None}

def test_pricing_call_is_refused_not_zeroed():
    ok, reason = in_scope("pricing", {})
    assert ok is False
    assert "price" in reason.lower()

def test_pitch_call_is_scored():
    ok, _ = in_scope("discovery", {})
    assert ok is True

def test_three_not_applicable_promises_means_it_was_not_a_pitch():
    adherence = {"promise_visibility": NA, "promise_proactive": NA, "promise_moat": NA,
                 "promise_durable": {"status": "delivered", "quote": "x"}}
    ok, reason = in_scope("discovery", adherence)
    assert ok is False
    assert "not a pitch" in reason

def test_unknown_call_type_is_scored_but_flagged():
    ok, reason = in_scope("webinar", {})
    assert ok is True
    assert "unrecognised" in reason
