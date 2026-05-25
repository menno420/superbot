"""Tests for !ai policy — effective-policy embed via resolver dry-run.

PR-2 contract:

* The prefix command + slash twin call
  ``ai_natural_language_policy.resolve(ctx, dry_run=True)`` to compute
  the effective policy for a channel.
* DM context (no guild) returns a friendly error.
* A non-text-channel context returns a friendly error.
* The optional channel argument is honored — when omitted, the current
  channel is used.
* The embed renders the resolver's precedence trace.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from cogs.ai_cog import AICog
from core.runtime.ai.contracts import PolicyDenialReason
from services import (
    ai_config_projection_service,
)
from services import ai_natural_language_policy as nlp

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _FakeTextChannel:
    """Stand-in that the cog's ``isinstance(_, discord.TextChannel)``
    check accepts after we monkeypatch ``discord.TextChannel`` to this
    class for the test.
    """

    def __init__(self, channel_id: int = 555, category_id: int | None = 200) -> None:
        self.id = channel_id
        self.name = "general"
        self.mention = f"<#{channel_id}>"
        self.category_id = category_id


def _fake_member(member_id: int = 99, roles: list[int] | None = None) -> MagicMock:
    member = MagicMock()
    member.id = member_id
    member.mention = f"<@{member_id}>"
    member.guild_permissions.administrator = True
    role_objs = []
    for role_id in roles or []:
        role = MagicMock()
        role.id = role_id
        role_objs.append(role)
    member.roles = role_objs
    return member


def _ctx(
    *,
    guild_id: int | None = 1,
    channel: _FakeTextChannel | None = None,
    author: MagicMock | None = None,
):
    ctx = MagicMock()
    ctx.guild = SimpleNamespace(id=guild_id) if guild_id else None
    ctx.channel = channel if channel is not None else _FakeTextChannel()
    ctx.author = author if author is not None else _fake_member()
    ctx.send = AsyncMock()
    return ctx


def _stub_snapshot() -> ai_config_projection_service.AIConfigSnapshot:
    """Minimal snapshot — populated enough for the ancillary field."""
    return ai_config_projection_service.AIConfigSnapshot(
        guild_id=1,
        policy=ai_config_projection_service.PolicySnapshot(
            guild_id=1,
            enabled=True,
            natural_language_enabled=True,
            default_provider="openai",
            default_model="gpt-4o-mini",
            channel_override_count=2,
            category_override_count=1,
            role_override_count=0,
        ),
        memory=ai_config_projection_service.MemorySnapshot(
            window_minutes=30,
            scan_enabled=False,
            cached_channel_count=0,
            cached_total_turns=0,
            per_channel_cap=200,
            channel_lru_cap=50,
            min_floor_turns=3,
        ),
        provider=ai_config_projection_service.ProviderSnapshot(
            enabled=True,
            default_provider="openai",
            setup_advisor_provider="openai",
            provider_active="openai",
            degraded=False,
            last_error_type=None,
            last_fallback_reason=None,
            requests_observed=0,
            failures_observed=0,
            redaction_enabled=True,
        ),
        projection=ai_config_projection_service.ProjectionSnapshot(),
        instruction=ai_config_projection_service.InstructionSnapshot(),
        audit=ai_config_projection_service.AuditSnapshot(),
    )


def _patch_resolve(monkeypatch, *, allowed: bool = True) -> dict[str, object]:
    """Stub ``nlp.resolve`` and return a dict recording the dry_run flag."""
    captured: dict[str, object] = {"calls": []}

    async def _fake_resolve(ctx, *, dry_run=False):
        captured["calls"].append(dry_run)
        return nlp.PolicyDecision(
            allowed=allowed,
            reason_code=(
                PolicyDenialReason.NONE
                if allowed
                else PolicyDenialReason.CHANNEL_DISABLED
            ),
            effective_min_level=2,
            effective_cooldown=30,
            effective_mode="always_reply" if allowed else "disabled",
            effective_source="channel",
            precedence_trace=(
                "guild_ai_gate: AI enabled=true",
                "channel_policy: mode=always_reply min_level=2 cooldown=30s",
                "final_decision: allowed min_level=2 cooldown=30s",
            ),
        )

    monkeypatch.setattr(nlp, "resolve", _fake_resolve)
    return captured


def _patch_xp(monkeypatch, level: int = 10) -> None:
    async def _xp(_g, _u):
        record = MagicMock()
        record.level = level
        return record

    monkeypatch.setattr("services.xp_service.get_user_record", _xp)


def _patch_snapshot(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_config_projection_service,
        "build_snapshot",
        AsyncMock(return_value=_stub_snapshot()),
    )


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_policy_requires_guild_context():
    cog = AICog(bot=MagicMock())
    ctx = _ctx(guild_id=None)
    await cog.ai_policy.callback(cog, ctx)
    msg = ctx.send.await_args.args[0]
    assert "guild context" in msg


@pytest.mark.asyncio
async def test_policy_rejects_non_text_channel(monkeypatch):
    """If the current channel is not a TextChannel (DM, voice, etc.),
    the command sends a friendly error rather than crashing."""
    cog = AICog(bot=MagicMock())
    # Use a SimpleNamespace channel that does NOT pass isinstance(_, discord.TextChannel).
    ctx = _ctx(channel=SimpleNamespace(id=999))
    await cog.ai_policy.callback(cog, ctx)
    msg = ctx.send.await_args.args[0]
    assert "text-channel" in msg


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_policy_invokes_resolver_with_dry_run_true(monkeypatch):
    """Both with/without-mention resolutions pass dry_run=True."""
    monkeypatch.setattr(
        "cogs.ai_cog.discord.TextChannel",
        _FakeTextChannel,
    )
    monkeypatch.setattr(
        "views.ai.policy.preview_view.discord.TextChannel",
        _FakeTextChannel,
    )
    captured = _patch_resolve(monkeypatch)
    _patch_xp(monkeypatch)
    _patch_snapshot(monkeypatch)

    cog = AICog(bot=MagicMock())
    ctx = _ctx()
    await cog.ai_policy.callback(cog, ctx)

    # Exactly two resolves (with/without mention), both dry_run=True.
    assert captured["calls"] == [True, True]


@pytest.mark.asyncio
async def test_policy_embed_renders_trace(monkeypatch):
    monkeypatch.setattr("cogs.ai_cog.discord.TextChannel", _FakeTextChannel)
    monkeypatch.setattr(
        "views.ai.policy.preview_view.discord.TextChannel",
        _FakeTextChannel,
    )
    _patch_resolve(monkeypatch)
    _patch_xp(monkeypatch)
    _patch_snapshot(monkeypatch)

    cog = AICog(bot=MagicMock())
    ctx = _ctx()
    await cog.ai_policy.callback(cog, ctx)

    # Embed sent
    _, kwargs = ctx.send.await_args
    embed: discord.Embed = kwargs["embed"]
    assert "Effective Policy" in (embed.title or "")
    body = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
    # Trace lines from the stubbed resolver appear in the embed.
    assert "channel_policy: mode=always_reply" in body
    assert "final_decision: allowed" in body
    # Ancillary "Context" field carries override counts from the snapshot.
    assert "Overrides:" in body
    assert "2 channel" in body
    assert "1 category" in body


@pytest.mark.asyncio
async def test_policy_honours_explicit_channel_argument(monkeypatch):
    """When ``channel=...`` is passed, the resolver runs against THAT
    channel (not ctx.channel)."""
    monkeypatch.setattr("cogs.ai_cog.discord.TextChannel", _FakeTextChannel)
    monkeypatch.setattr(
        "views.ai.policy.preview_view.discord.TextChannel",
        _FakeTextChannel,
    )

    captured_ctx: list[nlp.MessageContext] = []

    async def _fake_resolve(ctx, *, dry_run=False):
        captured_ctx.append(ctx)
        return nlp.PolicyDecision(
            allowed=True,
            reason_code=PolicyDenialReason.NONE,
            effective_min_level=2,
            effective_cooldown=30,
            effective_mode="always_reply",
            effective_source="channel",
            precedence_trace=("ok",),
        )

    monkeypatch.setattr(nlp, "resolve", _fake_resolve)
    _patch_xp(monkeypatch)
    _patch_snapshot(monkeypatch)

    cog = AICog(bot=MagicMock())
    here = _FakeTextChannel(channel_id=100)
    there = _FakeTextChannel(channel_id=999)
    ctx = _ctx(channel=here)
    await cog.ai_policy.callback(cog, ctx, channel=there)

    # Both resolves target channel_id=999, the explicit argument.
    assert all(c.channel_id == 999 for c in captured_ctx)


@pytest.mark.asyncio
async def test_policy_defaults_to_current_channel(monkeypatch):
    monkeypatch.setattr("cogs.ai_cog.discord.TextChannel", _FakeTextChannel)
    monkeypatch.setattr(
        "views.ai.policy.preview_view.discord.TextChannel",
        _FakeTextChannel,
    )
    captured_ctx: list[nlp.MessageContext] = []

    async def _fake_resolve(ctx, *, dry_run=False):
        captured_ctx.append(ctx)
        return nlp.PolicyDecision(
            allowed=True,
            reason_code=PolicyDenialReason.NONE,
            effective_min_level=2,
            effective_cooldown=30,
            effective_mode="always_reply",
            effective_source="channel",
            precedence_trace=("ok",),
        )

    monkeypatch.setattr(nlp, "resolve", _fake_resolve)
    _patch_xp(monkeypatch)
    _patch_snapshot(monkeypatch)

    cog = AICog(bot=MagicMock())
    here = _FakeTextChannel(channel_id=42)
    ctx = _ctx(channel=here)
    await cog.ai_policy.callback(cog, ctx)

    # Resolver targeted ctx.channel since no explicit channel argument.
    assert all(c.channel_id == 42 for c in captured_ctx)
