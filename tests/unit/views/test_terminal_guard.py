"""Unit tests for the settle-once game-view terminal guard.

Covers the cross-game terminal contract (``SettleOnceMixin``): the first
``claim_settlement()`` wins, every later call short-circuits, and the claim is
per-instance (no class-level state leak between views).
"""

from __future__ import annotations

import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from views.terminal_guard import SettleOnceMixin  # noqa: E402


class _Settleable(SettleOnceMixin):
    """Minimal host for the mixin (no discord.ui.View needed for the logic)."""


def test_first_claim_wins_then_loses() -> None:
    obj = _Settleable()
    assert obj.is_settled is False
    assert obj.claim_settlement() is True
    assert obj.is_settled is True
    # Every later claim short-circuits.
    assert obj.claim_settlement() is False
    assert obj.claim_settlement() is False
    assert obj.is_settled is True


def test_claim_is_per_instance() -> None:
    a = _Settleable()
    b = _Settleable()
    assert a.claim_settlement() is True
    # b is untouched — the claim wrote an instance attribute on a, not the class.
    assert b.is_settled is False
    assert b.claim_settlement() is True


def test_unclaimed_default_is_false_without_init() -> None:
    # The mixin declares no __init__; the class-level default is the unclaimed
    # state, so a freshly constructed host reads False before any claim.
    assert _Settleable().is_settled is False
