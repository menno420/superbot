"""PR G1 — RPS PvP pending matches persist to game_state across restarts.

Bets are NOT pre-debited for PvP matches, so this is the lowest-stakes
tier-A cog.  Adoption here establishes the pattern that G2-G6 follow:

  * Save on every state-changing event (challenge accept, each move
    pick).
  * Clear on natural resolution.
  * On cog_load, list active rows and clear — live views cannot be
    re-attached after a process bounce so resume is impossible; the
    cancel-and-clear semantics match the audit's Option 2.
  * On ``on_guild_remove``, wipe rows for the departing guild.

What this PR does NOT verify (deferred to later cogs):
  * Refund-on-restart — RPS PvP doesn't pre-debit.
  * Two-player concurrent state writes from different processes —
    out of scope until a multi-process deploy lands.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _row(id_, version=1, **kwargs):
    base = {
        "id": id_,
        "guild_id": kwargs.get("guild_id", 111),
        "user_id": kwargs.get("user_id", 100),
        "channel_id": kwargs.get("channel_id", 999),
        "subsystem": "rps_pvp_pending",
        "state": kwargs.get("state", {"p1_id": 100, "p2_id": 200, "choices": {}}),
        "version": version,
        "updated_at": "2025-01-01",
    }
    base.update(
        {k: v for k, v in kwargs.items() if k not in {"state", "guild_id", "user_id", "channel_id"}},
    )
    return base


def test_pvp_challenge_accept_wired_to_save():
    """Source-level check: the accept callback calls ``game_state_service.save``
    with the canonical user id and the constants from ``_helpers``.

    Direct invocation is awkward because discord.py wraps the button
    callback in an ``_ItemCallback``; a source-grep is sufficient
    given how small and well-scoped the wiring is.  ``record_choice``
    and ``_resolve`` are regular methods and ARE invoked directly in
    the tests below.
    """
    import inspect

    from views.rps import pvp_challenge

    src = inspect.getsource(pvp_challenge)
    # Save is called with the canonical user id helper.
    assert "rps_pvp_canonical_user_id" in src
    assert "game_state_service.save" in src
    assert "RPS_PVP_PENDING_SUBSYSTEM" in src
    assert "RPS_PVP_PENDING_VERSION" in src


@pytest.mark.asyncio
async def test_record_choice_updates_persisted_state():
    """Every time a player picks a move, the persisted choices update."""
    from views.rps.pvp_play import _RpsPvpPlayView

    p1 = MagicMock()
    p1.id = 100
    p2 = MagicMock()
    p2.id = 200
    channel = MagicMock()
    channel.id = 999
    view = _RpsPvpPlayView(p1, p2, guild_id=111, bet=50, channel=channel)
    view.message = MagicMock()
    view.message.edit = AsyncMock()
    channel.send = AsyncMock()

    with (
        patch(
            "views.rps.pvp_play.game_state_service.save",
            new_callable=AsyncMock,
        ) as mock_save,
        patch(
            "views.rps.pvp_play.game_state_service.clear",
            new_callable=AsyncMock,
        ),
        patch(
            "views.rps.pvp_play.economy_service.credit",
            new_callable=AsyncMock,
        ),
        patch(
            "views.rps.pvp_play.economy_service.debit",
            new_callable=AsyncMock,
        ),
    ):
        await view.record_choice(100, "rock")
        # First save: one choice recorded.
        first = mock_save.await_args_list[0].kwargs
        assert first["state"]["choices"] == {"100": "rock"}
        # No resolve yet — second player hasn't picked.
        await view.record_choice(200, "paper")
        # Second save: both choices recorded.
        second = mock_save.await_args_list[1].kwargs
        assert second["state"]["choices"] == {"100": "rock", "200": "paper"}


@pytest.mark.asyncio
async def test_resolve_clears_persisted_state():
    """After both players pick and the result lands, the persisted row
    is removed via clear (natural completion).
    """
    from views.rps.pvp_play import _RpsPvpPlayView

    p1 = MagicMock()
    p1.id = 100
    p1.mention = "<@100>"
    p2 = MagicMock()
    p2.id = 200
    p2.mention = "<@200>"
    channel = MagicMock()
    channel.id = 999
    channel.send = AsyncMock()
    view = _RpsPvpPlayView(p1, p2, guild_id=111, bet=50, channel=channel)
    view.message = MagicMock()
    view.message.edit = AsyncMock()

    with (
        patch(
            "views.rps.pvp_play.game_state_service.save",
            new_callable=AsyncMock,
        ),
        patch(
            "views.rps.pvp_play.game_state_service.clear",
            new_callable=AsyncMock,
        ) as mock_clear,
        patch(
            "views.rps.pvp_play.economy_service.credit",
            new_callable=AsyncMock,
        ),
        patch(
            "views.rps.pvp_play.economy_service.debit",
            new_callable=AsyncMock,
        ),
    ):
        await view.record_choice(100, "rock")
        await view.record_choice(200, "scissors")  # rock beats scissors
    mock_clear.assert_awaited_once()
    kwargs = mock_clear.await_args.kwargs
    assert kwargs["guild_id"] == 111
    assert kwargs["user_id"] == 100  # canonical = min(p1, p2)
    assert kwargs["channel_id"] == 999
    assert kwargs["subsystem"] == "rps_pvp_pending"


@pytest.mark.asyncio
async def test_cog_load_clears_orphan_rows():
    """On cog_load, _recover_rps_pvp_pending lists every active row and
    clears each by id.  No refund — RPS PvP doesn't pre-debit.
    """
    from cogs.rps_tournament_cog import RPSTournamentCog

    cog = RPSTournamentCog.__new__(RPSTournamentCog)

    stale = [_row(7), _row(8), _row(9)]
    with (
        patch(
            "services.game_state_service.list_active_for_subsystem",
            new_callable=AsyncMock,
            return_value=stale,
        ),
        patch(
            "services.game_state_service.clear_by_id",
            new_callable=AsyncMock,
        ) as mock_clear,
    ):
        await cog._recover_rps_pvp_pending()
    assert mock_clear.await_count == 3
    cleared_ids = {c.args[0] for c in mock_clear.await_args_list}
    assert cleared_ids == {7, 8, 9}


@pytest.mark.asyncio
async def test_cog_load_drops_version_mismatch_rows():
    """A row whose stored version doesn't match the current
    RPS_PVP_PENDING_VERSION is cleared, not resumed.  Live view
    objects can't be reconstructed anyway, so version-aware behaviour
    only diverges in log output.
    """
    from cogs.rps_tournament_cog import RPSTournamentCog

    cog = RPSTournamentCog.__new__(RPSTournamentCog)
    stale = [_row(42, version=99)]  # future-version payload
    with (
        patch(
            "services.game_state_service.list_active_for_subsystem",
            new_callable=AsyncMock,
            return_value=stale,
        ),
        patch(
            "services.game_state_service.clear_by_id",
            new_callable=AsyncMock,
        ) as mock_clear,
    ):
        await cog._recover_rps_pvp_pending()
    mock_clear.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_cog_load_no_rows_is_noop():
    from cogs.rps_tournament_cog import RPSTournamentCog

    cog = RPSTournamentCog.__new__(RPSTournamentCog)
    with (
        patch(
            "services.game_state_service.list_active_for_subsystem",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "services.game_state_service.clear_by_id",
            new_callable=AsyncMock,
        ) as mock_clear,
    ):
        await cog._recover_rps_pvp_pending()
    mock_clear.assert_not_called()


@pytest.mark.asyncio
async def test_cog_load_list_failure_is_logged_not_raised():
    from cogs.rps_tournament_cog import RPSTournamentCog

    cog = RPSTournamentCog.__new__(RPSTournamentCog)
    with patch(
        "services.game_state_service.list_active_for_subsystem",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB down"),
    ):
        # Must not raise.
        await cog._recover_rps_pvp_pending()


@pytest.mark.asyncio
async def test_on_guild_remove_wipes_pending_rows_for_guild():
    from cogs.rps_tournament_cog import RPSTournamentCog

    cog = RPSTournamentCog.__new__(RPSTournamentCog)
    guild = MagicMock()
    guild.id = 999
    rows = [_row(1, guild_id=999), _row(2, guild_id=999)]
    with (
        patch(
            "services.game_state_service.list_active_for_subsystem",
            new_callable=AsyncMock,
            return_value=rows,
        ) as mock_list,
        patch(
            "services.game_state_service.clear_by_id",
            new_callable=AsyncMock,
        ) as mock_clear,
    ):
        await cog.on_guild_remove(guild)
    # The list call is scoped to the departing guild.
    assert mock_list.await_args.kwargs.get("guild_id") == 999
    assert mock_clear.await_count == 2
