"""Tests for the command_routing resolver + writer.

Covers the scope-chain walk (channel → category → guild → default-true)
and the writer's pass-through to the DB primitives.  The DB primitives
themselves are mocked so the tests stay asyncpg-free.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services import command_routing

# ---------------------------------------------------------------------------
# is_cog_enabled — scope chain
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_is_cog_enabled_returns_true_when_no_policy_rows():
    """A fresh guild with no policy rows defaults to enabled for every cog."""
    with patch(
        "services.command_routing.db.get_one",
        new=AsyncMock(return_value=None),
    ) as get_mock:
        result = await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=999,
            category_id=42,
        )
    assert result is True
    # Three lookups: channel, category, guild.
    assert get_mock.await_count == 3


@pytest.mark.asyncio
async def test_is_cog_enabled_returns_channel_override_when_present():
    """Channel scope wins over category and guild."""
    async def fake_get(guild_id, scope, scope_id, cog):
        if scope == "channel" and scope_id == 999:
            return {"enabled": False}
        return None

    with patch("services.command_routing.db.get_one", new=fake_get):
        result = await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=999,
            category_id=42,
        )
    assert result is False


@pytest.mark.asyncio
async def test_is_cog_enabled_walks_to_category_when_channel_unset():
    async def fake_get(guild_id, scope, scope_id, cog):
        if scope == "channel":
            return None
        if scope == "category" and scope_id == 42:
            return {"enabled": True}
        return None

    with patch("services.command_routing.db.get_one", new=fake_get):
        result = await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=999,
            category_id=42,
        )
    assert result is True


@pytest.mark.asyncio
async def test_is_cog_enabled_walks_to_guild_when_channel_and_category_unset():
    async def fake_get(guild_id, scope, scope_id, cog):
        if scope == "guild" and scope_id is None:
            return {"enabled": False}
        return None

    with patch("services.command_routing.db.get_one", new=fake_get):
        result = await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=999,
            category_id=42,
        )
    assert result is False


@pytest.mark.asyncio
async def test_is_cog_enabled_skips_channel_lookup_when_channel_id_none():
    """DM-like context (no channel) skips the channel-scope query."""
    with patch(
        "services.command_routing.db.get_one",
        new=AsyncMock(return_value=None),
    ) as get_mock:
        await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=None,
            category_id=42,
        )
    # Two lookups: category, guild.
    assert get_mock.await_count == 2


@pytest.mark.asyncio
async def test_is_cog_enabled_skips_category_lookup_when_category_id_none():
    with patch(
        "services.command_routing.db.get_one",
        new=AsyncMock(return_value=None),
    ) as get_mock:
        await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=999,
            category_id=None,
        )
    # Two lookups: channel, guild.
    assert get_mock.await_count == 2


@pytest.mark.asyncio
async def test_is_cog_enabled_default_true_when_only_guild_lookup_runs():
    """No channel + no category + no guild policy row → still enabled."""
    with patch(
        "services.command_routing.db.get_one",
        new=AsyncMock(return_value=None),
    ):
        result = await command_routing.is_cog_enabled(
            guild_id=1,
            cog_name="games",
            channel_id=None,
            category_id=None,
        )
    assert result is True


# ---------------------------------------------------------------------------
# set_policy — the canonical routing mutation owner (Batch 3, RS03):
# old-value read + write + audit emission with real prev_value + typed result.
# ---------------------------------------------------------------------------


def _set_policy_patches(old_row, audit_ok: bool = True):
    return (
        patch(
            "services.command_routing.db.get_one",
            AsyncMock(return_value=old_row),
        ),
        patch(
            "services.command_routing.db.set_one",
            new_callable=AsyncMock,
        ),
        patch(
            "services.command_routing.emit_audit_action",
            AsyncMock(return_value=audit_ok),
        ),
    )


@pytest.mark.asyncio
async def test_set_policy_writes_through_db_layer_and_returns_result():
    get_mock, set_mock, emit_mock = _set_policy_patches(old_row=None)
    with get_mock, set_mock as set_one, emit_mock:
        result = await command_routing.set_policy(
            guild_id=1,
            scope_type="category",
            scope_id=42,
            cog_name="games",
            enabled=False,
            actor_id=99,
        )
    set_one.assert_awaited_once_with(
        guild_id=1,
        scope_type="category",
        scope_id=42,
        cog_name="games",
        enabled=False,
        actor_id=99,
    )
    assert isinstance(result, command_routing.RoutingMutationResult)
    assert result.mutation_id
    assert result.old_enabled is None  # no previous row existed
    assert result.new_enabled is False
    assert result.scope_type == "category"
    assert result.scope_id == 42
    assert result.cog_name == "games"
    assert result.audit_emitted is True


@pytest.mark.asyncio
async def test_set_policy_audits_with_real_prev_value_when_row_existed():
    get_mock, set_mock, emit_mock = _set_policy_patches(
        old_row={"enabled": True, "actor_id": 5, "updated_at": None},
    )
    with get_mock, set_mock, emit_mock as emit:
        result = await command_routing.set_policy(
            guild_id=1,
            scope_type="channel",
            scope_id=555,
            cog_name="economy",
            enabled=False,
            actor_id=99,
        )
    emit.assert_awaited_once()
    kwargs = emit.await_args.kwargs
    assert kwargs["subsystem"] == "cog_routing"
    assert kwargs["mutation_type"] == "set_cog_routing"
    assert kwargs["scope"] == "channel"
    assert kwargs["guild_id"] == 1
    assert kwargs["actor_id"] == 99
    assert kwargs["prev_value"] == "enabled"  # the real old state, not None
    assert kwargs["new_value"] == "disabled"
    assert kwargs["target"] == "channel:555:economy"
    assert kwargs["mutation_id"] == result.mutation_id
    assert result.old_enabled is True


@pytest.mark.asyncio
async def test_set_policy_audits_prev_value_none_when_no_row_existed():
    get_mock, set_mock, emit_mock = _set_policy_patches(old_row=None)
    with get_mock, set_mock, emit_mock as emit:
        await command_routing.set_policy(
            guild_id=1,
            scope_type="guild",
            scope_id=None,
            cog_name="games",
            enabled=True,
            actor_id=99,
        )
    kwargs = emit.await_args.kwargs
    assert kwargs["prev_value"] is None  # scope rode the default-true chain
    assert kwargs["new_value"] == "enabled"
    assert kwargs["target"] == "guild:guild:games"


@pytest.mark.asyncio
async def test_set_policy_surfaces_audit_failure_without_raising():
    """Audit emission is best-effort (the committed write stands); the
    publish-accepted flag rides the typed result."""
    get_mock, set_mock, emit_mock = _set_policy_patches(
        old_row=None,
        audit_ok=False,
    )
    with get_mock, set_mock as set_one, emit_mock:
        result = await command_routing.set_policy(
            guild_id=1,
            scope_type="guild",
            scope_id=None,
            cog_name="games",
            enabled=False,
            actor_id=99,
        )
    set_one.assert_awaited_once()
    assert result.audit_emitted is False
    assert result.new_enabled is False


# ---------------------------------------------------------------------------
# list_for_guild — passthrough
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_for_guild_passes_through_to_db_layer():
    rows = [{"scope_type": "guild", "cog_name": "games", "enabled": True}]
    with patch(
        "services.command_routing.db.list_for_guild",
        new=AsyncMock(return_value=rows),
    ):
        result = await command_routing.list_for_guild(1)
    assert result == rows
