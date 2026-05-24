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
        "utils.db.fetchall",
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
        "utils.db.fetchall",
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
        "utils.db.fetchall",
        new_callable=AsyncMock,
        side_effect=RuntimeError("connection refused"),
    ):
        await cog.platform_sessions.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    msg = ctx.send.call_args.args[0]
    assert "DB query failed" in msg
    assert "connection refused" in msg


# ---------------------------------------------------------------------------
# !platform slow — Phase S3.2 / O-3
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_platform_slow_shows_empty_state_when_no_entries():
    from core.runtime import slow_path_log

    slow_path_log._reset_for_tests()
    cog = _make_cog()
    ctx = _make_ctx()

    await cog.platform_slow.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    assert "No slow paths recorded" in (embed.fields[0].name if embed.fields else "")


@pytest.mark.asyncio
async def test_platform_slow_shows_recent_entries_most_recent_first():
    from core.runtime import slow_path_log

    slow_path_log._reset_for_tests()
    slow_path_log.configure(threshold_ms=10.0)
    for i in range(3):
        slow_path_log.maybe_record("db_query", f"q{i}", 100.0 + i)

    cog = _make_cog()
    ctx = _make_ctx()
    await cog.platform_slow.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    # Most recent first: q2, q1, q0
    field_names = [f.name for f in embed.fields]
    assert field_names == ["db_query: q2", "db_query: q1", "db_query: q0"]


@pytest.mark.asyncio
async def test_platform_slow_limit_argument_caps_field_count():
    from core.runtime import slow_path_log

    slow_path_log._reset_for_tests()
    slow_path_log.configure(threshold_ms=10.0)
    for i in range(10):
        slow_path_log.maybe_record("db_query", f"q{i}", 100.0)

    cog = _make_cog()
    ctx = _make_ctx()
    await cog.platform_slow.callback(cog, ctx, 3)

    embed = ctx.send.call_args.kwargs["embed"]
    assert len(embed.fields) == 3  # capped at limit=3


# ---------------------------------------------------------------------------
# !platform lifecycle — dedicated lifecycle embed
#
# The lifecycle provider is already rolled into !platform runtime, but
# operators looking for shutdown/restart context shouldn't have to scan
# the multi-provider dump.  This command formats phase, pending request,
# and the recent_events ring buffer (including close_executing entries
# from the close-driver) into a focused single-purpose embed.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_platform_lifecycle_renders_running_phase_with_no_pending():
    """Healthy path: RUNNING phase, no pending request, no events recorded."""
    cog = _make_cog()
    ctx = _make_ctx()

    snap = {
        "phase": "RUNNING",
        "can_accept_commands": True,
        "pending": None,
        "remaining_shutdown_seconds": None,
        "recent_events": [],
    }
    with patch("services.diagnostics_service.snapshot", return_value=snap):
        await cog.platform_lifecycle.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    assert "RUNNING" in (embed.description or "")
    field_names = {f.name for f in embed.fields}
    assert field_names == {"Pending request", "Recent events"}
    pending_field = next(f for f in embed.fields if f.name == "Pending request")
    assert pending_field.value.strip().startswith("_none_") or "none" in pending_field.value


@pytest.mark.asyncio
async def test_platform_lifecycle_renders_pending_shutdown_with_grace():
    """DRAINING phase with grace-remaining displays the grace value so
    operators can see how much time the request has left before the
    close-driver will fire."""
    cog = _make_cog()
    ctx = _make_ctx()

    snap = {
        "phase": "DRAINING",
        "can_accept_commands": False,
        "pending": {
            "kind": "shutdown",
            "reason": "sigterm",
            "actor": "signal_handler",
            "grace_seconds": 30.0,
        },
        "remaining_shutdown_seconds": 12.5,
        "recent_events": [],
    }
    with patch("services.diagnostics_service.snapshot", return_value=snap):
        await cog.platform_lifecycle.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    pending_field = next(f for f in embed.fields if f.name == "Pending request")
    assert "shutdown" in pending_field.value
    assert "sigterm" in pending_field.value
    assert "signal_handler" in pending_field.value
    assert "12.5" in pending_field.value  # grace remaining


@pytest.mark.asyncio
async def test_platform_lifecycle_renders_close_executing_event_newest_first():
    """The close-driver records ``close_executing`` events; they must
    surface in this embed so an operator can confirm the executor ran
    after intent was recorded.  Recent events are oldest-last in the
    snapshot but should be displayed newest-first."""
    cog = _make_cog()
    ctx = _make_ctx()

    snap = {
        "phase": "DRAINING",
        "can_accept_commands": False,
        "pending": {
            "kind": "shutdown",
            "reason": "sigterm",
            "actor": "signal_handler",
        },
        "remaining_shutdown_seconds": None,
        "recent_events": [
            {
                "name": "shutdown_requested",
                "phase": "RUNNING",
                "actor": "signal_handler",
                "reason": "sigterm",
            },
            {
                "name": "phase:DRAINING",
                "phase": "DRAINING",
                "actor": None,
                "reason": "sigterm",
            },
            {
                "name": "close_executing",
                "phase": "DRAINING",
                "actor": "signal_handler",
                "reason": "sigterm",
            },
        ],
    }
    with patch("services.diagnostics_service.snapshot", return_value=snap):
        await cog.platform_lifecycle.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    events_field = next(f for f in embed.fields if f.name.startswith("Recent events"))
    body = events_field.value
    # All three event names should be present.
    assert "close_executing" in body
    assert "shutdown_requested" in body
    assert "phase:DRAINING" in body
    # Newest-first ordering: close_executing must appear before
    # shutdown_requested in the rendered text.
    assert body.index("close_executing") < body.index("shutdown_requested")


@pytest.mark.asyncio
async def test_platform_lifecycle_degrades_gracefully_when_provider_unregistered():
    """Mirror build_caches_embed's KeyError fallback — render an
    informative embed instead of letting the exception escape into
    ctx.send."""
    cog = _make_cog()
    ctx = _make_ctx()

    with patch(
        "services.diagnostics_service.snapshot",
        side_effect=KeyError("lifecycle"),
    ):
        await cog.platform_lifecycle.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    assert "not registered" in (embed.description or "")


@pytest.mark.asyncio
async def test_lifecycle_shortcut_command_reuses_build_lifecycle_embed():
    """``!lifecycle`` (alias ``!lc``) is a top-level shortcut for
    ``!platform lifecycle``.  Operators don't need to remember the
    ``platform`` prefix during an incident.  Verifies the command
    produces the same lifecycle embed as the platform subcommand."""
    cog = _make_cog()
    ctx = _make_ctx()

    snap = {
        "phase": "RUNNING",
        "can_accept_commands": True,
        "pending": None,
        "remaining_shutdown_seconds": None,
        "recent_events": [],
    }
    with patch("services.diagnostics_service.snapshot", return_value=snap):
        await cog.lifecycle_shortcut.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    embed = ctx.send.call_args.kwargs["embed"]
    assert "RUNNING" in (embed.description or "")


def test_lifecycle_shortcut_exposes_lc_alias():
    """The ``lc`` alias is the expected operator shorthand — assert it
    explicitly so a future refactor cannot drop it without notice."""
    from cogs.diagnostic_cog import DiagnosticCog

    cmd = DiagnosticCog.lifecycle_shortcut
    assert "lc" in cmd.aliases
    assert cmd.name == "lifecycle"


# ---------------------------------------------------------------------------
# build_lifecycle_embed — close-outcome metadata rendering.
#
# The diagnostics_snapshot now carries per-event ``metadata`` so the
# embed can summarize kind / duration / timeout inline.  These tests
# pin the rendering so dashboards built on the operator-channel embeds
# do not silently drop the close-outcome detail.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_platform_lifecycle_renders_close_completed_duration_metadata():
    """A ``close_completed`` event with ``duration_seconds`` metadata
    must surface the duration in the Recent events field so the embed
    is self-contained — no Prometheus lookup required for normal
    shutdown / restart sequences."""
    cog = _make_cog()
    ctx = _make_ctx()

    snap = {
        "phase": "STOPPED",
        "can_accept_commands": False,
        "startup_duration_observed": True,
        "pending": {
            "kind": "shutdown",
            "reason": "sigterm",
            "actor": "signal_handler",
        },
        "remaining_shutdown_seconds": None,
        "recent_events": [
            {
                "name": "close_executing",
                "phase": "DRAINING",
                "actor": "signal_handler",
                "reason": "sigterm",
                "metadata": {"kind": "shutdown"},
            },
            {
                "name": "close_completed",
                "phase": "DRAINING",
                "actor": "signal_handler",
                "reason": "sigterm",
                "metadata": {
                    "kind": "shutdown",
                    "duration_seconds": 1.234,
                },
            },
        ],
    }
    with patch("services.diagnostics_service.snapshot", return_value=snap):
        await cog.platform_lifecycle.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    events_field = next(f for f in embed.fields if f.name.startswith("Recent events"))
    body = events_field.value
    assert "close_completed" in body
    # Duration rendered compactly so it fits the 1024-char field.
    assert "dur=1.23s" in body


@pytest.mark.asyncio
async def test_platform_lifecycle_renders_close_timeout_metadata():
    """A ``close_timeout`` event surfaces ``timeout_seconds`` so
    operators see what budget the driver actually used — useful when
    the constant has been tuned away from the default 20 s."""
    cog = _make_cog()
    ctx = _make_ctx()

    snap = {
        "phase": "DRAINING",
        "can_accept_commands": False,
        "startup_duration_observed": True,
        "pending": {
            "kind": "restart",
            "reason": "!restart",
            "actor": "op",
        },
        "remaining_shutdown_seconds": None,
        "recent_events": [
            {
                "name": "close_timeout",
                "phase": "DRAINING",
                "actor": "op",
                "reason": "!restart",
                "metadata": {
                    "kind": "restart",
                    "timeout_seconds": 20.0,
                },
            },
        ],
    }
    with patch("services.diagnostics_service.snapshot", return_value=snap):
        await cog.platform_lifecycle.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    events_field = next(f for f in embed.fields if f.name.startswith("Recent events"))
    body = events_field.value
    assert "close_timeout" in body
    assert "kind=restart" in body
    assert "timeout=20.00s" in body


@pytest.mark.asyncio
async def test_platform_lifecycle_renders_startup_observed_flag():
    """The embed description surfaces the one-shot
    ``startup_duration_observed`` flag so operators can confirm
    cold-boot timing was captured without scrolling to Prometheus."""
    cog = _make_cog()
    ctx = _make_ctx()

    snap = {
        "phase": "RUNNING",
        "can_accept_commands": True,
        "startup_duration_observed": True,
        "pending": None,
        "remaining_shutdown_seconds": None,
        "recent_events": [],
    }
    with patch("services.diagnostics_service.snapshot", return_value=snap):
        await cog.platform_lifecycle.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    description = embed.description or ""
    assert "Startup observed" in description
    assert "yes" in description


@pytest.mark.asyncio
async def test_platform_lifecycle_events_field_stays_under_discord_limit():
    """Discord caps embed field values at 1024 chars.  The lifecycle
    embed must respect that limit even when every event carries
    metadata (which can balloon the rendered line length)."""
    cog = _make_cog()
    ctx = _make_ctx()

    snap = {
        "phase": "DRAINING",
        "can_accept_commands": False,
        "startup_duration_observed": True,
        "pending": {
            "kind": "shutdown",
            "reason": "sigterm",
            "actor": "signal_handler",
        },
        "remaining_shutdown_seconds": None,
        "recent_events": [
            {
                "name": "close_completed",
                "phase": "DRAINING",
                "actor": "signal_handler",
                "reason": "sigterm" * 20,  # long reason
                "metadata": {"kind": "shutdown", "duration_seconds": 1.0},
            }
        ]
        * 20,  # 20 chunky events
    }
    with patch("services.diagnostics_service.snapshot", return_value=snap):
        await cog.platform_lifecycle.callback(cog, ctx)

    embed = ctx.send.call_args.kwargs["embed"]
    events_field = next(f for f in embed.fields if f.name.startswith("Recent events"))
    assert len(events_field.value) <= 1024
