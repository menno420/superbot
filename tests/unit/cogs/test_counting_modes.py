"""Regression tests for counting game modes: skip and random.

skip: ``skip N`` must step by N anchored at 1 (1, 1+N, 1+2N, …).
Previously it counted +1 and merely omitted a hardcoded ``[5,10]`` list,
so it was visually identical to normal counting.

random: a guess-the-secret-number game — the bot announces a window
containing a hidden target; a wrong guess halves the window toward the
target (min width 10) WITHOUT resetting the count; a correct guess
advances the count and rolls a fresh target + window.
"""

from __future__ import annotations

from types import SimpleNamespace

from cogs.counting import game_logic
from cogs.counting.handler import compute_decision


def _msg(content: str):
    return SimpleNamespace(
        content=content,
        author=SimpleNamespace(id=1, mention="<@1>", bot=False),
    )


def _state(mode: str, **over) -> dict:
    base = {
        "mode": mode,
        "current_count": 0,
        "last_user": None,
        "taking_turns": False,
        "reset_on_wrong_count": False,
        "leaderboard": {},
        "sequence_index": 0,
        "step": 1,
    }
    base.update(over)
    return base


# --- skip -------------------------------------------------------------------


def test_skip_steps_by_n_from_one():
    cd = _state("skip", step=5)
    seq = []
    for _ in range(5):
        nxt = game_logic.calculate_expected_count(cd, cd["current_count"], "skip")
        cd["current_count"] = nxt  # simulate accepting nxt
        seq.append(nxt)
    assert seq == [1, 6, 11, 16, 21]


def test_skip_rejects_off_step_number():
    cd = _state("skip", step=5, current_count=1)
    d = compute_decision(message=_msg("2"), channel_data=cd, user_id="1")
    assert d.accepted is False
    assert "6" in (d.reply or "")


def test_skip_accepts_on_step_number():
    cd = _state("skip", step=5, current_count=1)
    d = compute_decision(message=_msg("6"), channel_data=cd, user_id="1")
    assert d.accepted is True
    assert cd["current_count"] == 6


# --- random -----------------------------------------------------------------


def test_start_random_round_target_inside_window_above_count():
    for _ in range(50):
        target, lo, hi = game_logic.start_random_round(7)
        assert lo <= target <= hi
        assert target > 7
        assert lo > 7  # the whole window sits above the current count
        assert hi - lo >= 10


def test_narrow_random_range_halves_keeps_target_floors_at_10():
    lo, hi = 0, 200
    target = 123
    prev = hi - lo
    for _ in range(12):
        lo, hi = game_logic.narrow_random_range(lo, hi, target)
        assert lo <= target <= hi  # target stays inside
        assert hi - lo >= 10  # never below width 10
        assert hi - lo <= prev  # never widens
        prev = hi - lo
    assert hi - lo == 10  # converges to the floor


def test_random_correct_guess_advances_and_rerolls():
    cd = _state("random", next_expected=42, range_lo=30, range_hi=60)
    d = compute_decision(message=_msg("42"), channel_data=cd, user_id="1")
    assert d.accepted is True
    assert cd["current_count"] == 42
    assert cd["next_expected"] > 42  # fresh target above the new count
    assert cd["range_lo"] <= cd["next_expected"] <= cd["range_hi"]
    assert cd["leaderboard"]["1"] == 1


def test_random_wrong_guess_narrows_without_reset():
    cd = _state("random", current_count=0, next_expected=42, range_lo=30, range_hi=60)
    d = compute_decision(message=_msg("31"), channel_data=cd, user_id="1")
    assert d.accepted is False
    assert d.delete_message is False  # guesses are part of play, not deleted
    assert cd["current_count"] == 0  # a wrong guess does NOT reset
    assert cd["range_lo"] <= 42 <= cd["range_hi"]
    assert (cd["range_hi"] - cd["range_lo"]) <= 30  # window narrowed


def test_random_reinitialises_when_state_missing():
    cd = _state("random", next_expected=None, range_lo=None, range_hi=None)
    compute_decision(message=_msg("5"), channel_data=cd, user_id="1")
    assert isinstance(cd["next_expected"], int)
    assert isinstance(cd["range_lo"], int)
    assert isinstance(cd["range_hi"], int)
    assert cd["range_lo"] <= cd["next_expected"] <= cd["range_hi"]
