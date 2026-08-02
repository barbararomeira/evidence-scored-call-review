"""Applicability arithmetic, and the framing pair that coverage scoring cannot see."""
from callscore.score_message import score

D = {"status": "delivered", "quote": "q"}
A = {"status": "absent", "quote": "q"}
NA = {"status": "n/a", "quote": None}

def test_not_applicable_leaves_the_denominator():
    """A short call is not punished for elements it had no room for."""
    r = score({"problem_framing": D, "category": D, "promise_visibility": D,
               "promise_proactive": NA, "promise_moat": NA, "promise_durable": NA})
    assert (r["delivered"], r["applicable"], r["score"]) == (3, 3, 100)

def test_absent_stays_in_the_denominator():
    r = score({"problem_framing": D, "category": A, "promise_visibility": D,
               "promise_proactive": A, "promise_moat": D, "promise_durable": A})
    assert (r["delivered"], r["applicable"], r["score"]) == (3, 6, 50)

def test_framing_pair_is_independent_of_the_score():
    """Four promises can land while the frame stays the old pitch — the calibration failure."""
    r = score({"problem_framing": A, "category": A, "promise_visibility": D,
               "promise_proactive": D, "promise_moat": D, "promise_durable": D})
    assert r["score"] == 67
    assert r["framing_pair"] is False
