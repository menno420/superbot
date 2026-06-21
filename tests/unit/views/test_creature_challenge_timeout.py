"""creature_battle challenge view — timeout-expiry behavior.

accept/decline call ``self.stop()`` (cancelling the timeout), so ``on_timeout``
fires only on a genuinely-unanswered challenge. These pins keep the silent-timeout
gap closed (an unanswered challenge says so; a resolved one is never overwritten).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from views.creature_battle.challenge import CreatureBattleChallengeView


def _member(uid: int, name: str):
    return SimpleNamespace(id=uid, mention=f"<@{uid}>", display_name=name)


def _view() -> CreatureBattleChallengeView:
    view = CreatureBattleChallengeView(_member(1, "Ada"), _member(2, "Bo"), 99)
    view.message = SimpleNamespace(edit=AsyncMock(), id=123)
    return view


@pytest.mark.asyncio
async def test_unanswered_challenge_edits_to_an_expiry_notice():
    view = _view()
    await view.on_timeout()
    view.message.edit.assert_awaited_once()
    _, kwargs = view.message.edit.await_args
    assert "expired" in kwargs["content"]
    assert "Bo" in kwargs["content"]  # the opponent who didn't respond
    # All buttons disabled on the edited view.
    assert all(getattr(c, "disabled", False) for c in view.children)


@pytest.mark.asyncio
async def test_resolved_challenge_is_not_overwritten_on_a_late_timeout():
    view = _view()
    view._resolved = True  # accept/decline already answered it
    await view.on_timeout()
    view.message.edit.assert_not_awaited()


@pytest.mark.asyncio
async def test_on_timeout_without_a_message_is_a_noop():
    view = CreatureBattleChallengeView(_member(1, "Ada"), _member(2, "Bo"), 99)
    view.message = None
    # Must not raise.
    await view.on_timeout()
