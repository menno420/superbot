"""Tests for !ai memory — chat-memory status embed.

PR-3 contract:

* The command needs a guild context; refuses in DMs.
* "Mode" field reads from ``snapshot.memory.window_minutes`` (0 →
  "Minimal — last 3 messages only"; >0 → "Time window: N min").
* "This channel cached turns" reads from
  ``ai_conversation_service.channel_stats(guild_id)`` for ``ctx.channel.id``.
* "Last reply used memory" renders ``—`` until PR-5 populates
  ``audit.latest['memory_turns_used']``.
* Empty cache + populated cache both render without raising.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from cogs.ai_cog import AICog, build_memory_embed
from services import ai_config_projection_service, ai_conversation_service

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_buffers():
    ai_conversation_service._reset_for_tests()
    yield
    ai_conversation_service._reset_for_tests()


def _ctx(guild_id: int | None = 1, channel_id: int = 100):
    ctx = MagicMock()
    ctx.guild = SimpleNamespace(id=guild_id) if guild_id else None
    ctx.channel = SimpleNamespace(id=channel_id, mention=f"<#{channel_id}>")
    ctx.author = SimpleNamespace(id=42)
    ctx.send = AsyncMock()
    return ctx


def _snapshot(
    *,
    window_minutes: int = 0,
    scan_enabled: bool = False,
    guild_channel_count: int = 0,
    guild_total_turns: int = 0,
    cached_channel_count: int = 0,
    cached_total_turns: int = 0,
    audit_latest: dict | None = None,
) -> ai_config_projection_service.AIConfigSnapshot:
    """Build a snapshot with the memory / audit fields we exercise."""
    return ai_config_projection_service.AIConfigSnapshot(
        guild_id=1,
        policy=ai_config_projection_service.PolicySnapshot(guild_id=1),
        memory=ai_config_projection_service.MemorySnapshot(
            window_minutes=window_minutes,
            scan_enabled=scan_enabled,
            cached_channel_count=cached_channel_count,
            cached_total_turns=cached_total_turns,
            per_channel_cap=200,
            channel_lru_cap=50,
            min_floor_turns=3,
            guild_channel_count=guild_channel_count,
            guild_total_turns=guild_total_turns,
        ),
        provider=ai_config_projection_service.ProviderSnapshot(
            enabled=False,
            default_provider="deterministic",
            setup_advisor_provider=None,
            provider_active=None,
            degraded=False,
            last_error_type=None,
            last_fallback_reason=None,
            requests_observed=0,
            failures_observed=0,
            redaction_enabled=True,
        ),
        projection=ai_config_projection_service.ProjectionSnapshot(),
        instruction=ai_config_projection_service.InstructionSnapshot(),
        audit=ai_config_projection_service.AuditSnapshot(latest=audit_latest),
    )


def _patch_snapshot(monkeypatch, snap) -> None:
    monkeypatch.setattr(
        ai_config_projection_service,
        "build_snapshot",
        AsyncMock(return_value=snap),
    )


# ---------------------------------------------------------------------------
# Embed builder (sync) — exercised directly so we don't need cog state.
# ---------------------------------------------------------------------------


def test_memory_embed_window_zero_renders_minimal():
    snap = _snapshot(window_minutes=0)
    embed = build_memory_embed(snap, channel_id=100, channel_turn_count=0)
    blob = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
    assert "Minimal — last 3 messages only" in blob


def test_memory_embed_window_positive_renders_time_window():
    snap = _snapshot(window_minutes=30)
    embed = build_memory_embed(snap, channel_id=100, channel_turn_count=12)
    blob = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
    assert "Time window: 30 min" in blob
    # Channel turn count rendered.
    assert "12" in blob


def test_memory_embed_last_reply_renders_dash_when_field_missing():
    """When the audit row has no ``memory_turns_used`` (pre-PR-5), the
    embed renders the dash placeholder rather than raising."""
    snap = _snapshot(audit_latest={"decision": "replied"})
    embed = build_memory_embed(snap, channel_id=100, channel_turn_count=0)
    last_reply_field = next(
        f for f in embed.fields if f.name == "Last reply used memory"
    )
    assert last_reply_field.value == "—"


def test_memory_embed_last_reply_renders_value_when_field_present():
    snap = _snapshot(
        audit_latest={"decision": "replied", "memory_turns_used": 7},
    )
    embed = build_memory_embed(snap, channel_id=100, channel_turn_count=0)
    last_reply_field = next(
        f for f in embed.fields if f.name == "Last reply used memory"
    )
    assert last_reply_field.value == "7"


def test_memory_embed_scan_status():
    snap_on = _snapshot(scan_enabled=True)
    embed_on = build_memory_embed(snap_on, channel_id=100, channel_turn_count=0)
    scan_on_field = next(f for f in embed_on.fields if f.name == "Discord history scan")
    assert scan_on_field.value == "on"

    snap_off = _snapshot(scan_enabled=False)
    embed_off = build_memory_embed(snap_off, channel_id=100, channel_turn_count=0)
    scan_off_field = next(
        f for f in embed_off.fields if f.name == "Discord history scan"
    )
    assert scan_off_field.value == "off"


# ---------------------------------------------------------------------------
# Command — DM rejection.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_memory_requires_guild_context(monkeypatch):
    cog = AICog(bot=MagicMock())
    ctx = _ctx(guild_id=None)
    await cog.ai_memory.callback(cog, ctx)
    msg = ctx.send.await_args.args[0]
    assert "guild context" in msg


# ---------------------------------------------------------------------------
# Command — happy paths.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_memory_command_empty_cache(monkeypatch):
    """With no cached turns, the embed renders 0 for this channel +
    0 for the guild total without raising."""
    _patch_snapshot(monkeypatch, _snapshot(window_minutes=30))

    cog = AICog(bot=MagicMock())
    ctx = _ctx(guild_id=1, channel_id=100)
    await cog.ai_memory.callback(cog, ctx)

    embed = ctx.send.await_args.kwargs["embed"]
    this_channel_field = next(
        f for f in embed.fields if f.name == "This channel cached turns"
    )
    assert "0" in this_channel_field.value


@pytest.mark.asyncio
async def test_memory_command_populated_cache(monkeypatch):
    """The current channel's cached-turn count comes from
    ai_conversation_service.channel_stats — populate the buffer and
    confirm the embed shows the right count."""
    ai_conversation_service.append(
        1,
        100,
        user_id=1,
        role="user",
        text="hello",
    )
    ai_conversation_service.append(
        1,
        100,
        user_id=1,
        role="user",
        text="world",
    )
    # Different channel — should NOT count toward this-channel field.
    ai_conversation_service.append(
        1,
        200,
        user_id=1,
        role="user",
        text="elsewhere",
    )
    _patch_snapshot(
        monkeypatch,
        _snapshot(
            window_minutes=30,
            guild_channel_count=2,
            guild_total_turns=3,
        ),
    )

    cog = AICog(bot=MagicMock())
    ctx = _ctx(guild_id=1, channel_id=100)
    await cog.ai_memory.callback(cog, ctx)

    embed = ctx.send.await_args.kwargs["embed"]
    this_channel_field = next(
        f for f in embed.fields if f.name == "This channel cached turns"
    )
    # Channel 100 has 2 turns; channel 200 is excluded.
    assert "2" in this_channel_field.value
    # Guild count reflects the snapshot value.
    guild_field = next(f for f in embed.fields if f.name == "Guild cached channels")
    assert "2" in guild_field.value


# ---------------------------------------------------------------------------
# Schema hint copy — the operator-facing "Minimal" rename.
# ---------------------------------------------------------------------------


def test_memory_window_setting_hint_mentions_minimal():
    """``ai_memory_window_minutes`` hint copy explains the 'Minimal'
    semantics so operators understand that 0 ≠ off."""
    from cogs.ai.schemas import AI_CONFIG_SCHEMA

    spec = next(
        s for s in AI_CONFIG_SCHEMA.settings if s.name == "ai_memory_window_minutes"
    )
    assert "Minimal" in spec.hint
    assert "3 messages only" in spec.hint or "3-turn floor" in spec.hint
