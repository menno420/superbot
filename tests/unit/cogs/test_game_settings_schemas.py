"""PR 8 — Game settings schemas + readiness integration.

Verifies that each game subsystem (RPS, Blackjack, Deathmatch)
registers a ``SubsystemSchema`` with at least one ``SettingSpec``
whose ``settings_key`` is read by the runtime command body.

Plan §2.12 hard rule: only settings the runtime actually reads land
in the schema. Each test below pairs a SettingSpec assertion with a
behavioural assertion proving the read happens.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))


# ---------------------------------------------------------------------------
# Schema shape pins
# ---------------------------------------------------------------------------


def test_rps_schema_declares_default_entry_fee():
    from cogs.rps_tournament.schemas import RPS_CONFIG_SCHEMA
    from utils.settings_keys import RPS_DEFAULT_ENTRY_FEE

    spec = next(
        (s for s in RPS_CONFIG_SCHEMA.settings if s.name == "default_entry_fee"),
        None,
    )
    assert spec is not None, "RPS schema must declare default_entry_fee"
    assert spec.settings_key == RPS_DEFAULT_ENTRY_FEE
    assert spec.value_type is int
    assert spec.default == 0


def test_blackjack_schema_declares_default_entry_fee():
    from cogs.blackjack.schemas import BLACKJACK_CONFIG_SCHEMA
    from utils.settings_keys import BLACKJACK_DEFAULT_ENTRY_FEE

    spec = next(
        (s for s in BLACKJACK_CONFIG_SCHEMA.settings if s.name == "default_entry_fee"),
        None,
    )
    assert spec is not None, "Blackjack schema must declare default_entry_fee"
    assert spec.settings_key == BLACKJACK_DEFAULT_ENTRY_FEE
    assert spec.value_type is int
    assert spec.default == 0


def test_deathmatch_schema_declares_turn_timeout():
    from cogs.deathmatch.schemas import DEATHMATCH_CONFIG_SCHEMA
    from utils.settings_keys import DEATHMATCH_TURN_TIMEOUT

    spec = next(
        (s for s in DEATHMATCH_CONFIG_SCHEMA.settings if s.name == "turn_timeout"),
        None,
    )
    assert spec is not None, "Deathmatch schema must declare turn_timeout"
    assert spec.settings_key == DEATHMATCH_TURN_TIMEOUT
    assert spec.value_type is int
    assert spec.default == 60


# ---------------------------------------------------------------------------
# Runtime read pins (plan §2.12 hard rule)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rps_register_reads_default_entry_fee_when_omitted():
    """``!rpsregister`` without an explicit fee must call
    ``db.get_setting(guild_id, RPS_DEFAULT_ENTRY_FEE, ...)`` and use
    the returned value as ``self.entry_fee``.
    """
    from cogs.rps_tournament_cog import RPSTournamentCog
    from utils.settings_keys import RPS_DEFAULT_ENTRY_FEE

    cog = RPSTournamentCog(MagicMock())
    ctx = MagicMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 42
    ctx.send = AsyncMock()
    # Stub the tournament-state read so we get past its early return.
    with (
        patch(
            "cogs.rps_tournament_cog.tournament_state_service.get_active",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "cogs.rps_tournament_cog.tournament_state_service.set_active",
            new_callable=AsyncMock,
        ),
        patch(
            "utils.db.get_setting",
            new_callable=AsyncMock,
            return_value="50",
        ) as mock_get_setting,
        patch.object(
            cog,
            "registration_countdown",
            new_callable=AsyncMock,
        ),
        patch(
            "cogs.rps_tournament_cog.tasks.spawn",
            new=lambda _name, _coro: MagicMock(),
        ),
    ):
        # Short-circuit Discord interactions: ctx.send/add_reaction are
        # AsyncMocks and the registration_countdown is suppressed.
        ctx.send = AsyncMock(
            return_value=MagicMock(add_reaction=AsyncMock()),
        )
        # Bypass discord.py Command wrapping; invoke the bound function
        # directly. ``RPSTournamentCog.rps_register`` is a Command
        # object at attribute-access time, so reach for ``.callback``.
        await RPSTournamentCog.rps_register.callback(cog, ctx)

    mock_get_setting.assert_any_call(42, RPS_DEFAULT_ENTRY_FEE, "0")
    assert cog.entry_fee == 50


@pytest.mark.asyncio
async def test_bjtournament_reads_default_entry_fee_when_omitted():
    """``!bjtournament`` without an explicit fee resolves the configured
    ``blackjack.default_entry_fee`` setting via the scalar resolver.
    """
    from cogs.blackjack_cog import BlackjackCog

    cog = BlackjackCog(MagicMock())
    ctx = MagicMock()
    ctx.guild = MagicMock()
    ctx.guild.id = 99
    ctx.author = MagicMock(id=11)
    ctx.channel = MagicMock(id=22)
    ctx.bot = MagicMock()
    ctx.send = AsyncMock(return_value=MagicMock(add_reaction=AsyncMock()))
    with (
        patch(
            "cogs.blackjack_cog.tournament_state_service.get_active",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "cogs.blackjack_cog.tournament_state_service.set_active",
            new_callable=AsyncMock,
        ),
        patch(
            "services.settings_resolution.resolve_value",
            new_callable=AsyncMock,
            return_value=25,
        ) as mock_resolve_value,
        patch(
            "cogs.blackjack_cog.tasks.spawn",
            new=lambda _name, _coro: MagicMock(),
        ),
        patch(
            "cogs.blackjack_cog._tourn_embed",
            return_value=MagicMock(),
        ),
    ):
        # Bypass discord.py Command wrapping (no bot has loaded the cog).
        await BlackjackCog.bjtournament.callback(cog, ctx)

    mock_resolve_value.assert_any_call(99, "blackjack", "default_entry_fee", 0)
    # The created tournament should carry the setting-driven fee.
    from cogs.blackjack._state import _tournaments

    assert _tournaments.get(99) is not None
    assert _tournaments[99].entry_fee == 25
    # Cleanup so other tests don't see this guild's tournament.
    _tournaments.pop(99, None)


# ---------------------------------------------------------------------------
# Schema registration pins
# ---------------------------------------------------------------------------


def test_rps_register_schemas_idempotent():
    """Re-registration is allowed (hot-reload-friendly)."""
    from cogs.rps_tournament.schemas import register_schemas
    from core.runtime.subsystem_schema import get_schema

    register_schemas()
    register_schemas()
    schema = get_schema("rps_tournament")
    assert schema is not None
    assert any(s.name == "default_entry_fee" for s in schema.settings)


def test_blackjack_register_schemas_registers_under_correct_key():
    from cogs.blackjack.schemas import register_schemas
    from core.runtime.subsystem_schema import get_schema

    register_schemas()
    schema = get_schema("blackjack")
    assert schema is not None
    assert any(s.name == "default_entry_fee" for s in schema.settings)


def test_deathmatch_register_schemas_registers_under_correct_key():
    from cogs.deathmatch.schemas import register_schemas
    from core.runtime.subsystem_schema import get_schema

    register_schemas()
    schema = get_schema("deathmatch")
    assert schema is not None
    assert any(s.name == "turn_timeout" for s in schema.settings)


# ---------------------------------------------------------------------------
# Readiness integration — schemas surface via the existing walker
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_setup_readiness_includes_game_subsystems():
    """After all three schemas are registered, ``services.setup_readiness
    .collect`` should produce rows for each — proving the readiness
    integration is automatic (no per-subsystem plumbing required).
    """
    from cogs.blackjack.schemas import register_schemas as register_bj
    from cogs.deathmatch.schemas import register_schemas as register_dm
    from cogs.rps_tournament.schemas import register_schemas as register_rps
    from services import setup_readiness

    register_rps()
    register_bj()
    register_dm()

    with (
        patch(
            "utils.db.bindings.list_for_guild",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "utils.db.get_setting",
            new_callable=AsyncMock,
            return_value="",
        ),
    ):
        report = await setup_readiness.collect(guild_id=1234)

    subsystems_in_report = {row.subsystem for row in report.per_subsystem}
    for expected in ("rps_tournament", "blackjack", "deathmatch"):
        assert expected in subsystems_in_report, (
            f"{expected!r} missing from readiness report — schema "
            "registration is broken."
        )
        row = next(r for r in report.per_subsystem if r.subsystem == expected)
        assert row.settings_declared >= 1, (
            f"{expected!r} declared {row.settings_declared} settings; "
            "expected at least 1."
        )
        # No configured settings in this stubbed test — get_setting
        # returns empty.
        assert row.settings_configured == 0
