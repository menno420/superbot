"""Phase S2.5 / O-1 — tests for the diagnostics-backed !platform subcommands.

The existing tests in test_platform_commands.py cover the R1 commands
(status / anchors / identity).  These tests cover the new subcommands
added in S2.5 that read from services.diagnostics_service:

    !platform runtime   · !platform caches   · !platform locks [prefix]
    !platform tasks     · !platform views    · !platform sessions [subsystem]
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.send = AsyncMock()
    return ctx


def _make_cog():
    from cogs.diagnostic_cog import DiagnosticCog

    return DiagnosticCog(bot=MagicMock())


# ---------------------------------------------------------------------------
# !platform runtime — snapshot_all roll-up
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_platform_runtime_renders_one_field_per_provider():
    cog = _make_cog()
    ctx = _make_ctx()

    fake_snap = {
        "guild_config": {"size": 5, "versions_tracked": 2},
        "scope_locks": {"total": 3, "held": 1, "by_prefix": {"counting": 3}},
    }
    with patch(
        "services.diagnostics_service.snapshot_all",
        return_value=fake_snap,
    ):
        await cog.platform_runtime.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    embed = ctx.send.call_args.kwargs["embed"]
    field_names = {f.name for f in embed.fields}
    assert field_names == {"guild_config", "scope_locks"}


# ---------------------------------------------------------------------------
# !platform caches — two fields, one per cache
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_platform_caches_shows_both_cache_providers():
    cog = _make_cog()
    ctx = _make_ctx()

    def fake_snapshot(name):
        return {
            "guild_config": {"size": 7, "versions_tracked": 3},
            "governance_cache": {"size": 12, "guilds_versioned": 4},
        }[name]

    with patch(
        "services.diagnostics_service.snapshot",
        side_effect=fake_snapshot,
    ):
        await cog.platform_caches.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    field_names = {f.name for f in embed.fields}
    assert "guild_config" in field_names
    assert "governance_cache" in field_names


@pytest.mark.asyncio
async def test_platform_caches_handles_missing_provider_gracefully():
    cog = _make_cog()
    ctx = _make_ctx()

    def fake_snapshot(name):
        if name == "governance_cache":
            raise KeyError("not registered")
        return {"size": 0, "versions_tracked": 0}

    with patch(
        "services.diagnostics_service.snapshot",
        side_effect=fake_snapshot,
    ):
        await cog.platform_caches.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    # Missing provider surfaces as "_error" key in its field value.
    governance_field = next(f for f in embed.fields if f.name == "governance_cache")
    assert "not registered" in governance_field.value


# ---------------------------------------------------------------------------
# !platform locks — filter behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_platform_locks_renders_full_snapshot_when_no_prefix():
    cog = _make_cog()
    ctx = _make_ctx()

    with patch(
        "services.diagnostics_service.snapshot",
        return_value={
            "total": 5,
            "held": 2,
            "by_prefix": {"counting": 3, "tournament": 2},
        },
    ):
        await cog.platform_locks.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    assert "total: **5**" in embed.description
    assert "held: **2**" in embed.description
    by_prefix_field = next(f for f in embed.fields if f.name == "By prefix")
    assert "counting" in by_prefix_field.value
    assert "tournament" in by_prefix_field.value


@pytest.mark.asyncio
async def test_platform_locks_filter_excludes_other_prefixes():
    cog = _make_cog()
    ctx = _make_ctx()

    with patch(
        "services.diagnostics_service.snapshot",
        return_value={
            "total": 5,
            "held": 2,
            "by_prefix": {"counting": 3, "tournament": 2},
        },
    ):
        await cog.platform_locks.callback(cog, ctx, "counting")

    embed = ctx.send.call_args.kwargs["embed"]
    assert "filter: `counting`" in embed.description
    by_prefix_field = next(f for f in embed.fields if f.name == "By prefix")
    assert "counting" in by_prefix_field.value
    assert "tournament" not in by_prefix_field.value


@pytest.mark.asyncio
async def test_platform_locks_empty_state_renders_none():
    cog = _make_cog()
    ctx = _make_ctx()

    with patch(
        "services.diagnostics_service.snapshot",
        return_value={"total": 0, "held": 0, "by_prefix": {}},
    ):
        await cog.platform_locks.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    by_prefix_field = next(f for f in embed.fields if f.name == "By prefix")
    assert "none" in by_prefix_field.value


# ---------------------------------------------------------------------------
# !platform tasks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_platform_tasks_renders_active_count_and_names():
    cog = _make_cog()
    ctx = _make_ctx()

    with patch(
        "services.diagnostics_service.snapshot",
        return_value={
            "active_count": 2,
            "names": ["counting:save:1", "xp:flush"],
        },
    ):
        await cog.platform_tasks.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    assert "2 active" in embed.description
    names_field = next(f for f in embed.fields if f.name == "Names")
    assert "counting:save:1" in names_field.value
    assert "xp:flush" in names_field.value


# ---------------------------------------------------------------------------
# !platform views
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_platform_views_renders_registered_subsystems():
    cog = _make_cog()
    ctx = _make_ctx()

    with patch(
        "services.diagnostics_service.snapshot",
        return_value={
            "registered_count": 3,
            "subsystems": ["economy", "mining", "role"],
        },
    ):
        await cog.platform_views.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    assert "3 registered" in embed.description
    subsystems_field = next(f for f in embed.fields if f.name == "Subsystems")
    for name in ("economy", "mining", "role"):
        assert name in subsystems_field.value


# ---------------------------------------------------------------------------
# !platform sessions — DB-backed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_platform_sessions_renders_all_subsystems_when_no_filter():
    cog = _make_cog()
    ctx = _make_ctx()

    rows = [
        {"subsystem": "economy", "n": 7},
        {"subsystem": "role", "n": 3},
    ]
    with patch(
        "cogs.diagnostic_cog.db.fetchall",
        new_callable=AsyncMock,
        return_value=rows,
    ) as fetchall:
        await cog.platform_sessions.callback(cog, ctx)

    fetchall.assert_awaited_once()
    sql = fetchall.await_args.args[0]
    assert "WHERE subsystem" not in sql  # no filter clause
    embed = ctx.send.call_args.kwargs["embed"]
    assert "all subsystems" in embed.description
    by_sub = next(f for f in embed.fields if f.name == "By subsystem")
    assert "economy" in by_sub.value
    assert "role" in by_sub.value


@pytest.mark.asyncio
async def test_platform_sessions_filter_passes_to_sql_param():
    cog = _make_cog()
    ctx = _make_ctx()

    with patch(
        "cogs.diagnostic_cog.db.fetchall",
        new_callable=AsyncMock,
        return_value=[{"subsystem": "economy", "n": 7}],
    ) as fetchall:
        await cog.platform_sessions.callback(cog, ctx, "economy")

    fetchall.assert_awaited_once()
    sql, params = fetchall.await_args.args
    assert "WHERE subsystem=$1" in sql
    assert params == ("economy",)
    embed = ctx.send.call_args.kwargs["embed"]
    assert "filter: `economy`" in embed.description


@pytest.mark.asyncio
async def test_platform_sessions_db_failure_surfaces_to_user():
    cog = _make_cog()
    ctx = _make_ctx()

    with patch(
        "cogs.diagnostic_cog.db.fetchall",
        new_callable=AsyncMock,
        side_effect=RuntimeError("connection refused"),
    ):
        await cog.platform_sessions.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    msg = ctx.send.call_args.args[0]
    assert "DB query failed" in msg
    assert "connection refused" in msg
