"""Phase 2c PR-9 — XP opt-out gate in cogs.xp.listener.

Verifies the gate's behavior matrix:

* ``participation.enabled`` OFF (declared default) → XP awarded
  regardless of participation state (pre-PR-9 parity).
* ``participation.enabled`` ON + user OPTED_OUT → XP NOT awarded.
* ``participation.enabled`` ON + user OPTED_IN → XP awarded.
* ``participation.enabled`` ON + user NOT_SET → XP awarded.
* Flag evaluator failure → gate falls open (XP awarded).
* Participation accessor failure → gate falls open (XP awarded).

The gate is the only PR-9 mutation to the XP hot path; the rest of
``handle_message`` (cooldown, cache, level-up announce) is exercised
by the existing ``tests/unit/cogs/test_xp_cog_caching.py`` suite.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.user_config_accessors import ParticipationState


def _make_message(*, guild_id: int = 99, user_id: int = 1):
    msg = MagicMock()
    msg.author = MagicMock()
    msg.author.bot = False
    msg.author.id = user_id
    msg.guild = MagicMock()
    msg.guild.id = guild_id
    return msg


def _patch_xp_pipeline(*, on_cooldown: bool = False):
    """Patch the XP message-handling dependencies.

    Returns a context manager that yields the mocked
    ``xp_service.award`` so tests can assert whether it was awaited.
    """
    from contextlib import contextmanager

    from core.runtime import guild_config
    from core.runtime.config_arbitration import ConfigReadResult

    @contextmanager
    def _ctx():
        guild_config._reset_for_tests()
        last_xp = 0 if not on_cooldown else 9999999999  # far future on cooldown
        db_row = {"last_xp": last_xp, "messages": 1}
        with (
            patch(
                "cogs.xp.listener.db.get_xp",
                new_callable=AsyncMock,
                return_value=db_row,
            ),
            patch(
                "utils.guild_config_accessors.db.get_setting",
                new_callable=AsyncMock,
            ) as get_setting,
            patch(
                "core.runtime.config_arbitration.get_xp_announce_channel",
                new_callable=AsyncMock,
                return_value=ConfigReadResult(
                    value=None,
                    source="missing",
                    binding_status="n/a",
                    flag_state="off",
                    diagnostics=[],
                ),
            ),
            patch(
                "cogs.xp.listener.check_cooldown",
                return_value=(on_cooldown, 0),
            ),
            patch(
                "cogs.xp.listener.xp_service.award",
                new_callable=AsyncMock,
            ) as mock_award,
        ):

            async def reply(guild_id, key, default=""):  # noqa: ARG001
                return {
                    "xp_min": "15",
                    "xp_max": "25",
                    "xp_cooldown": "60",
                }.get(key, default)

            get_setting.side_effect = reply
            mock_award.return_value = MagicMock(
                new_xp=100,
                new_level=1,
                leveled_up=False,
            )
            yield mock_award
        guild_config._reset_for_tests()

    return _ctx()


# ---------------------------------------------------------------------------
# Flag OFF: behavior unchanged
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flag_off_awards_xp_regardless_of_participation_state():
    """Default state: ``participation.enabled`` OFF.

    XP behaves exactly as it did pre-PR-9; the gate never blocks.
    """
    from cogs.xp.listener import handle_message

    with (
        _patch_xp_pipeline() as mock_award,
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=False,
        ),
        # Even if get_participation returns OPTED_OUT, the gate must
        # not consult it when the flag is OFF — we verify by asserting
        # XP was awarded regardless.
        patch(
            "utils.user_config_accessors.get_participation",
            new_callable=AsyncMock,
            return_value=ParticipationState.OPTED_OUT,
        ),
    ):
        bot = MagicMock()
        await handle_message(bot, _make_message())
    mock_award.assert_awaited_once()


@pytest.mark.asyncio
async def test_flag_off_does_not_call_get_participation():
    """With the flag OFF, the accessor must never be invoked (perf + correctness)."""
    from cogs.xp.listener import handle_message

    with (
        _patch_xp_pipeline() as mock_award,
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "utils.user_config_accessors.get_participation",
            new_callable=AsyncMock,
        ) as mock_get,
    ):
        bot = MagicMock()
        await handle_message(bot, _make_message())
    mock_get.assert_not_awaited()
    mock_award.assert_awaited_once()


# ---------------------------------------------------------------------------
# Flag ON
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flag_on_opted_out_blocks_xp():
    from cogs.xp.listener import handle_message

    with (
        _patch_xp_pipeline() as mock_award,
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "utils.user_config_accessors.get_participation",
            new_callable=AsyncMock,
            return_value=ParticipationState.OPTED_OUT,
        ),
    ):
        bot = MagicMock()
        await handle_message(bot, _make_message())
    mock_award.assert_not_awaited()


@pytest.mark.asyncio
async def test_flag_on_opted_in_awards_xp():
    from cogs.xp.listener import handle_message

    with (
        _patch_xp_pipeline() as mock_award,
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "utils.user_config_accessors.get_participation",
            new_callable=AsyncMock,
            return_value=ParticipationState.OPTED_IN,
        ),
    ):
        bot = MagicMock()
        await handle_message(bot, _make_message())
    mock_award.assert_awaited_once()


@pytest.mark.asyncio
async def test_flag_on_not_set_awards_xp():
    """NOT_SET treats the user as not-opted-out (default-allow)."""
    from cogs.xp.listener import handle_message

    with (
        _patch_xp_pipeline() as mock_award,
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "utils.user_config_accessors.get_participation",
            new_callable=AsyncMock,
            return_value=ParticipationState.NOT_SET,
        ),
    ):
        bot = MagicMock()
        await handle_message(bot, _make_message())
    mock_award.assert_awaited_once()


# ---------------------------------------------------------------------------
# Fail-open: a transient error in the gate never blocks XP
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_flag_evaluator_failure_falls_open():
    """If is_enabled raises, treat as flag OFF — XP is awarded."""
    from cogs.xp.listener import handle_message

    with (
        _patch_xp_pipeline() as mock_award,
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            side_effect=RuntimeError("evaluator crashed"),
        ),
        patch(
            "utils.user_config_accessors.get_participation",
            new_callable=AsyncMock,
            return_value=ParticipationState.OPTED_OUT,
        ),
    ):
        bot = MagicMock()
        await handle_message(bot, _make_message())
    mock_award.assert_awaited_once()


@pytest.mark.asyncio
async def test_participation_accessor_failure_falls_open():
    """If get_participation raises, treat as not-opted-out — XP is awarded."""
    from cogs.xp.listener import handle_message

    with (
        _patch_xp_pipeline() as mock_award,
        patch(
            "core.runtime.feature_flags.is_enabled",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "utils.user_config_accessors.get_participation",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB blip"),
        ),
    ):
        bot = MagicMock()
        await handle_message(bot, _make_message())
    mock_award.assert_awaited_once()


# ---------------------------------------------------------------------------
# Centralisation invariant — the gate lives in one helper, not scattered
# across the listener body.
# ---------------------------------------------------------------------------


def test_xp_listener_has_centralised_gate_helper():
    """The gate is a single named helper, not inlined into handle_message."""
    import cogs.xp.listener as listener_module

    assert hasattr(
        listener_module,
        "_xp_participation_allowed",
    ), "XP participation gate must be a named helper for testability + reuse"
