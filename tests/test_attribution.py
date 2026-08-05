"""The attribution gate: a rep is only scored on calls they actually spoke on.

Regression cover for a real incident. A call was booked on one rep's calendar — their name in
the meeting title and the invitee list — and run by a colleague. The pipeline read the rep from
the invite instead of the transcript and sent that rep a coaching message about a call they were
never on, praising them for an opening someone else delivered.
"""
import pathlib

from callscore import attribution
from callscore.extractors import base

FIXTURES = pathlib.Path(__file__).resolve().parent.parent / "fixtures" / "transcripts"

SPOKE = """REP: How do you find out when something has gone off track?
PROSPECT: Someone tells us, always after the fact.
REP: That is the pattern everywhere.
"""

SILENT = """COLLEAGUE: How do you find out when something has gone off track?
PROSPECT: Someone tells us, always after the fact.
COLLEAGUE: That is the pattern everywhere.
"""


def test_counts_turns_per_speaker():
    assert attribution.speaking_turns(SPOKE) == {"REP": 2, "PROSPECT": 1}


def test_rep_who_spoke_is_attributable():
    ok, why = attribution.check("Ana", SPOKE)
    assert ok and "2 speaking turns" in why


def test_rep_who_never_spoke_is_not_attributable():
    ok, why = attribution.check("Ana", SILENT)
    assert not ok
    assert "no speaking turns" in why
    assert "Ana" in why          # the message has to name who was wrongly credited
    assert "COLLEAGUE" in why    # and who actually carried the call


def test_gate_refuses_rather_than_scoring_zero():
    """The failure mode is a *plausible* score, not an obvious one.

    Silence must not read as 'delivered nothing' — that is a number about a person who was not
    there. The call has to leave the pipeline instead.
    """
    assert attribution.rep_spoke(SILENT) == (False, 0)
    assert attribution.rep_spoke(SPOKE)[0] is True


def test_the_unattributable_fixture_is_excluded_from_a_real_run():
    """End-to-end: c-0440 is filed under Ana but carried by a colleague."""
    t = base.load_transcript(FIXTURES / "c-0440.md")
    assert t.rep == "Ana"
    assert attribution.check(t.rep, t.body)[0] is False

    import run_day
    rows, _, unattributed = run_day.process(FIXTURES, "mock", None, "2026-05-29")

    assert "c-0440" not in [r["call_id"] for r in rows], "unattributable call reached the scorer"
    assert "c-0440" in [u["call_id"] for u in unattributed]
    assert "Ana" not in [r["rep"] for r in rows], "Ana was coached on a call she did not speak on"


def test_every_scored_fixture_has_its_rep_speaking():
    """No fixture should be quietly scoring a rep who never opened their mouth."""
    for path in sorted(FIXTURES.glob("*.md")):
        t = base.load_transcript(path)
        ok, why = attribution.check(t.rep, t.body)
        if path.name == "c-0440.md":
            assert not ok
        else:
            assert ok, f"{path.name}: {why}"
