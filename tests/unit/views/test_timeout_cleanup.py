"""Regression tests for Tier 3 view-timeout cleanup contracts.

Four `on_timeout` callbacks across four views were inconsistent with
the rest of the codebase:

* `_RankView.on_timeout` used ``await self.message.edit(view=None)``
  which strips the dropdown entirely.  Users had to re-run ``/rank``
  to switch stat view.  Fixed to match the standard disable-and-edit
  shape (greyed-out select stays on the card).
* `_RpsPvpChallengeView.on_timeout` and `_ChallengeView.on_timeout`
  (blackjack PvP) disabled children and edited the message but never
  called ``self.stop()`` — the Python-side view object lingered in
  discord.py's dispatch table after the message went terminal.
* `_RpsView.on_timeout` (solo) was missing the ``self.message is
  None`` guard that ``_RpsSoloResultView.on_timeout`` already has;
  the bare ``try/except`` caught the AttributeError but the explicit
  guard matches the canonical shape elsewhere.

These tests pin each contract.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest


def _member(id_: int = 1) -> MagicMock:
    m = MagicMock(spec=discord.Member)
    m.id = id_
    m.display_name = f"User{id_}"
    m.mention = f"<@{id_}>"
    return m


# ---------------------------------------------------------------------------
# _RankView.on_timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rank_view_timeout_disables_select_in_place():
    """`on_timeout` must keep the dropdown visible but disabled —
    not strip it via ``view=None`` (which forces a re-run of /rank).
    """
    from views.xp.rank_view import _RankView

    member = _member()
    guild = MagicMock(spec=discord.Guild)
    view = _RankView(member, guild, current_stat="both")
    view.message = MagicMock()
    view.message.edit = AsyncMock()

    await view.on_timeout()

    view.message.edit.assert_awaited_once()
    kwargs = view.message.edit.await_args.kwargs
    assert kwargs.get("view") is view, "must edit with view=self, not view=None"
    for child in view.children:
        assert child.disabled is True
    assert view.is_finished()


@pytest.mark.asyncio
async def test_rank_view_timeout_noops_when_message_unset():
    from views.xp.rank_view import _RankView

    member = _member()
    guild = MagicMock(spec=discord.Guild)
    view = _RankView(member, guild, current_stat="both")
    assert view.message is None
    await view.on_timeout()  # must not raise


# ---------------------------------------------------------------------------
# _RpsPvpChallengeView.on_timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rps_pvp_challenge_timeout_disables_and_stops():
    from views.rps.pvp_challenge import _RpsPvpChallengeView

    view = _RpsPvpChallengeView(
        challenger=_member(1),
        opponent=_member(2),
        guild_id=99,
        bet=0,
    )
    view.message = MagicMock()
    view.message.edit = AsyncMock()

    await view.on_timeout()

    view.message.edit.assert_awaited_once()
    for child in view.children:
        assert child.disabled is True
    assert view.is_finished(), "missing self.stop() — view stays in dispatch table"


@pytest.mark.asyncio
async def test_rps_pvp_challenge_timeout_stops_even_when_message_unset():
    from views.rps.pvp_challenge import _RpsPvpChallengeView

    view = _RpsPvpChallengeView(
        challenger=_member(1),
        opponent=_member(2),
        guild_id=99,
        bet=0,
    )
    assert view.message is None
    await view.on_timeout()  # must not raise
    assert view.is_finished()


# ---------------------------------------------------------------------------
# Blackjack _ChallengeView.on_timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_blackjack_challenge_timeout_disables_and_stops():
    from views.blackjack.pvp_view import _ChallengeView

    view = _ChallengeView(
        challenger=_member(1),
        opponent=_member(2),
        guild_id=99,
        bet=10,
    )
    view.message = MagicMock()
    view.message.edit = AsyncMock()

    await view.on_timeout()

    view.message.edit.assert_awaited_once()
    for child in view.children:
        assert child.disabled is True
    assert view.is_finished()


@pytest.mark.asyncio
async def test_blackjack_challenge_timeout_stops_even_when_message_unset():
    from views.blackjack.pvp_view import _ChallengeView

    view = _ChallengeView(
        challenger=_member(1),
        opponent=_member(2),
        guild_id=99,
        bet=10,
    )
    assert view.message is None
    await view.on_timeout()  # must not raise
    assert view.is_finished()


# ---------------------------------------------------------------------------
# _RpsView.on_timeout (solo) — message-None guard
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rps_solo_view_timeout_noops_when_message_unset():
    """Mirrors the explicit guard already present on
    ``_RpsSoloResultView.on_timeout``.
    """
    from views.rps.solo_play import _RpsView

    view = _RpsView(_member(1), guild_id=99, bet=0)
    assert view.message is None
    await view.on_timeout()  # must not raise


@pytest.mark.asyncio
async def test_rps_solo_view_timeout_disables_when_message_set():
    from views.rps.solo_play import _RpsView

    view = _RpsView(_member(1), guild_id=99, bet=0)
    view.message = MagicMock()
    view.message.edit = AsyncMock()

    await view.on_timeout()

    view.message.edit.assert_awaited_once()
    for child in view.children:
        assert child.disabled is True
