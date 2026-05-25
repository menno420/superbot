"""AI readiness scan — each chain link's failure modes.

Pins:

* Resolver dry-run is always invoked with ``dry_run=True``.
* The provider, ai_enabled, nl_or_scoped, permissions, memory, and
  recent-denials links each produce the expected status under their
  failure mode (and ``ok`` / ``info`` under their happy path).
* The chain summary flips from "Ready" → "Ready with caveat" → "Not
  ready" based on the worst finding status.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from services import (
    ai_conversation_service,
    ai_decision_audit_service,
    ai_diagnostics_service,
    ai_memory_service,
    ai_natural_language_policy,
    ai_readiness_service,
)
from utils.db import ai as ai_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _seed_diagnostics(monkeypatch, **overrides):
    base = {
        "enabled": False,
        "default_provider": "deterministic",
        "setup_advisor_provider": "deterministic",
        "provider_active": None,
        "degraded": False,
        "last_error_type": None,
        "last_fallback_reason": None,
        "requests_observed": 0,
        "failures_observed": 0,
        "redaction_enabled": True,
    }
    base.update(overrides)
    monkeypatch.setattr(
        ai_diagnostics_service,
        "snapshot_for_cog",
        lambda: dict(base),
    )


def _seed_no_overrides(monkeypatch):
    monkeypatch.setattr(ai_db, "list_channel_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_category_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_role_policies", AsyncMock(return_value=[]))


def _seed_empty_audit(monkeypatch):
    monkeypatch.setattr(
        ai_decision_audit_service, "query", AsyncMock(return_value=[]),
    )


def _seed_memory(monkeypatch, window=0, scan=False):
    monkeypatch.setattr(
        ai_memory_service,
        "read_memory_settings",
        AsyncMock(return_value=(window, scan)),
    )


def _seed_resolve(monkeypatch):
    """Default fake resolver — channel allowed, recorded dry_run."""
    captured: dict[str, object] = {}

    async def _fake_resolve(ctx, *, dry_run=False):
        captured["dry_run"] = dry_run
        captured["ctx"] = ctx
        return ai_natural_language_policy.PolicyDecision(
            allowed=True,
            reason_code=__import__(
                "core.runtime.ai.contracts",
                fromlist=["PolicyDenialReason"],
            ).PolicyDenialReason.NONE,
            effective_min_level=2,
            effective_cooldown=30,
            effective_mode="always_reply",
            effective_source="guild",
        )

    monkeypatch.setattr(ai_natural_language_policy, "resolve", _fake_resolve)
    return captured


def _settings_resolution_stub(monkeypatch, values=None):
    from services import settings_resolution

    async def _resolve(_g, _s, name):
        if values and name in values:
            return SimpleNamespace(value=values[name], valid=True, diagnostics=())
        return None

    monkeypatch.setattr(settings_resolution, "resolve_setting", _resolve)


@pytest.fixture(autouse=True)
def _reset_conv_cache():
    ai_conversation_service._reset_for_tests()


class _FakeTextChannel:
    """Concrete stand-in for a Discord text channel.

    Used in place of a real ``discord.TextChannel`` so the readiness
    service's isinstance check can be exercised via monkeypatch (the
    tests replace ``ai_readiness_service.discord.TextChannel`` with
    this class).
    """

    def __init__(self, perms, guild) -> None:
        self.id = 200
        self.guild = guild
        self.category = None
        self._perms = perms

    def permissions_for(self, _member):
        return self._perms


def _fake_channel(
    *,
    view: bool = True,
    send: bool = True,
    read_history: bool = True,
    in_cache: bool = True,
) -> _FakeTextChannel:
    perms = SimpleNamespace(
        view_channel=view,
        send_messages=send,
        read_message_history=read_history,
    )
    bot_member = SimpleNamespace(id=42) if in_cache else None
    guild = SimpleNamespace(id=100, me=bot_member)
    return _FakeTextChannel(perms, guild)


def _enabled_policy_row(**overrides):
    row = {
        "guild_id": 1,
        "enabled": True,
        "natural_language_enabled": True,
        "default_provider": "openai",
        "default_model": "gpt-4o-mini",
        "minimum_level_default": 2,
        "cooldown_seconds": 30,
        "fresh_user_mention_allowance": 1,
        "guild_instruction_profile_id": None,
        "generation": 1,
    }
    row.update(overrides)
    return row


# ---------------------------------------------------------------------------
# Individual link checks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_provider_missing_is_error(monkeypatch):
    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))
    _seed_no_overrides(monkeypatch)
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider=None)

    report = await ai_readiness_service.scan(1, bot=object())
    finding = next(f for f in report.findings if f.name == "provider_configured")
    assert finding.status == "error"


@pytest.mark.asyncio
async def test_provider_degraded_is_warn(monkeypatch):
    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))
    _seed_no_overrides(monkeypatch)
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(
        monkeypatch,
        default_provider="openai",
        degraded=True,
        last_error_type="HTTPTimeout",
    )

    report = await ai_readiness_service.scan(1, bot=object())
    finding = next(f for f in report.findings if f.name == "provider_configured")
    assert finding.status == "warn"
    assert "HTTPTimeout" in finding.detail


@pytest.mark.asyncio
async def test_ai_enabled_no_row_is_error(monkeypatch):
    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))
    _seed_no_overrides(monkeypatch)
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    report = await ai_readiness_service.scan(1, bot=object())
    finding = next(f for f in report.findings if f.name == "ai_enabled")
    assert finding.status == "error"
    assert "no typed ai policy row" in finding.detail.lower()


@pytest.mark.asyncio
async def test_ai_enabled_off_is_error(monkeypatch):
    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(return_value=_enabled_policy_row(enabled=False)),
    )
    _seed_no_overrides(monkeypatch)
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    report = await ai_readiness_service.scan(1, bot=object())
    finding = next(f for f in report.findings if f.name == "ai_enabled")
    assert finding.status == "error"


@pytest.mark.asyncio
async def test_nl_off_no_scoped_is_warn(monkeypatch):
    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(return_value=_enabled_policy_row(natural_language_enabled=False)),
    )
    _seed_no_overrides(monkeypatch)
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    report = await ai_readiness_service.scan(1, bot=object())
    finding = next(f for f in report.findings if f.name == "nl_enabled_or_scoped")
    assert finding.status == "warn"


@pytest.mark.asyncio
async def test_nl_off_with_scoped_is_ok(monkeypatch):
    monkeypatch.setattr(
        ai_db,
        "get_guild_policy",
        AsyncMock(return_value=_enabled_policy_row(natural_language_enabled=False)),
    )
    monkeypatch.setattr(
        ai_db,
        "list_channel_policies",
        AsyncMock(return_value=[{"channel_id": 999, "mode": "always_reply"}]),
    )
    monkeypatch.setattr(ai_db, "list_category_policies", AsyncMock(return_value=[]))
    monkeypatch.setattr(ai_db, "list_role_policies", AsyncMock(return_value=[]))
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    report = await ai_readiness_service.scan(1, bot=object())
    finding = next(f for f in report.findings if f.name == "nl_enabled_or_scoped")
    assert finding.status == "ok"


@pytest.mark.asyncio
async def test_resolver_skipped_when_no_channel(monkeypatch):
    monkeypatch.setattr(
        ai_db, "get_guild_policy", AsyncMock(return_value=_enabled_policy_row()),
    )
    _seed_no_overrides(monkeypatch)
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    report = await ai_readiness_service.scan(1, bot=object())
    finding = next(f for f in report.findings if f.name == "resolver_decision")
    assert finding.status == "skipped"


@pytest.mark.asyncio
async def test_resolver_dry_run_is_invoked_with_dry_run_true(monkeypatch):
    monkeypatch.setattr(
        ai_db, "get_guild_policy", AsyncMock(return_value=_enabled_policy_row()),
    )
    _seed_no_overrides(monkeypatch)
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch)
    captured = _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    channel = _fake_channel()
    # Monkey isinstance check: the production code accepts real Discord
    # channel types. For the test, we install a TextChannel subclass
    # check that recognises our SimpleNamespace.
    monkeypatch.setattr(
        ai_readiness_service.discord,
        "TextChannel",
        type(channel),
    )

    await ai_readiness_service.scan(1, bot=object(), channel=channel)
    assert captured["dry_run"] is True


@pytest.mark.asyncio
async def test_resolver_deny_is_warn(monkeypatch):
    from core.runtime.ai.contracts import PolicyDenialReason

    async def _fake_resolve(_ctx, *, dry_run=False):
        return ai_natural_language_policy.PolicyDecision(
            allowed=False,
            reason_code=PolicyDenialReason.BELOW_MIN_LEVEL,
            effective_min_level=5,
            effective_cooldown=30,
            effective_mode="always_reply",
            effective_source="guild",
        )

    monkeypatch.setattr(
        ai_db, "get_guild_policy", AsyncMock(return_value=_enabled_policy_row()),
    )
    _seed_no_overrides(monkeypatch)
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch)
    monkeypatch.setattr(ai_natural_language_policy, "resolve", _fake_resolve)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    channel = _fake_channel()
    monkeypatch.setattr(
        ai_readiness_service.discord, "TextChannel", type(channel),
    )
    report = await ai_readiness_service.scan(1, bot=object(), channel=channel)
    finding = next(f for f in report.findings if f.name == "resolver_decision")
    assert finding.status == "warn"
    assert "BELOW_MIN_LEVEL" in finding.detail


@pytest.mark.asyncio
async def test_permissions_skipped_when_no_channel(monkeypatch):
    monkeypatch.setattr(
        ai_db, "get_guild_policy", AsyncMock(return_value=_enabled_policy_row()),
    )
    _seed_no_overrides(monkeypatch)
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    report = await ai_readiness_service.scan(1, bot=object())
    finding = next(f for f in report.findings if f.name == "bot_permissions")
    assert finding.status == "skipped"


@pytest.mark.asyncio
async def test_permissions_missing_send_is_error(monkeypatch):
    monkeypatch.setattr(
        ai_db, "get_guild_policy", AsyncMock(return_value=_enabled_policy_row()),
    )
    _seed_no_overrides(monkeypatch)
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    channel = _fake_channel(send=False)
    monkeypatch.setattr(
        ai_readiness_service.discord, "TextChannel", type(channel),
    )
    report = await ai_readiness_service.scan(1, bot=object(), channel=channel)
    finding = next(f for f in report.findings if f.name == "bot_permissions")
    assert finding.status == "error"
    assert "send_messages" in finding.detail


@pytest.mark.asyncio
async def test_permissions_scan_enabled_requires_read_history(monkeypatch):
    monkeypatch.setattr(
        ai_db, "get_guild_policy", AsyncMock(return_value=_enabled_policy_row()),
    )
    _seed_no_overrides(monkeypatch)
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch, window=30, scan=True)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    channel = _fake_channel(read_history=False)
    monkeypatch.setattr(
        ai_readiness_service.discord, "TextChannel", type(channel),
    )
    report = await ai_readiness_service.scan(1, bot=object(), channel=channel)
    finding = next(f for f in report.findings if f.name == "bot_permissions")
    assert finding.status == "error"
    assert "read_message_history" in finding.detail


@pytest.mark.asyncio
async def test_memory_status_is_info(monkeypatch):
    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))
    _seed_no_overrides(monkeypatch)
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch, window=30, scan=True)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    report = await ai_readiness_service.scan(1, bot=object())
    finding = next(f for f in report.findings if f.name == "memory_status")
    assert finding.status == "info"
    assert "30 min window" in finding.detail


@pytest.mark.asyncio
async def test_recent_denials_pure_replies_is_ok(monkeypatch):
    monkeypatch.setattr(
        ai_db, "get_guild_policy", AsyncMock(return_value=_enabled_policy_row()),
    )
    _seed_no_overrides(monkeypatch)
    monkeypatch.setattr(
        ai_decision_audit_service,
        "query",
        AsyncMock(return_value=[{"decision": "replied"}] * 5),
    )
    _seed_memory(monkeypatch)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    report = await ai_readiness_service.scan(1, bot=object())
    finding = next(f for f in report.findings if f.name == "recent_denials")
    assert finding.status == "ok"


@pytest.mark.asyncio
async def test_recent_denials_with_failures_is_warn(monkeypatch):
    monkeypatch.setattr(
        ai_db, "get_guild_policy", AsyncMock(return_value=_enabled_policy_row()),
    )
    _seed_no_overrides(monkeypatch)
    monkeypatch.setattr(
        ai_decision_audit_service,
        "query",
        AsyncMock(
            return_value=[
                {"decision": "replied"},
                {"decision": "denied"},
                {"decision": "errored"},
            ],
        ),
    )
    _seed_memory(monkeypatch)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    report = await ai_readiness_service.scan(1, bot=object())
    finding = next(f for f in report.findings if f.name == "recent_denials")
    assert finding.status == "warn"


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summary_not_ready_on_any_error(monkeypatch):
    """A single error link flips the summary to 'Not ready: ...'."""
    monkeypatch.setattr(ai_db, "get_guild_policy", AsyncMock(return_value=None))
    _seed_no_overrides(monkeypatch)
    _seed_empty_audit(monkeypatch)
    _seed_memory(monkeypatch)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    report = await ai_readiness_service.scan(1, bot=object())
    assert report.summary.startswith("Not ready:")


@pytest.mark.asyncio
async def test_summary_ready_when_all_ok_or_info(monkeypatch):
    monkeypatch.setattr(
        ai_db, "get_guild_policy", AsyncMock(return_value=_enabled_policy_row()),
    )
    _seed_no_overrides(monkeypatch)
    monkeypatch.setattr(
        ai_decision_audit_service,
        "query",
        AsyncMock(return_value=[{"decision": "replied"}]),
    )
    _seed_memory(monkeypatch)
    _seed_resolve(monkeypatch)
    _settings_resolution_stub(monkeypatch)
    _seed_diagnostics(monkeypatch, default_provider="openai")

    report = await ai_readiness_service.scan(1, bot=object())
    # No channel → resolver+permissions are 'skipped' but not error/warn,
    # so the summary should still read "Ready".
    assert report.summary == "Ready" or report.summary.startswith("Ready with caveat")


def test_status_codes_exported() -> None:
    assert ai_readiness_service.STATUS_OK == "ok"
    assert ai_readiness_service.STATUS_ERROR == "error"
    assert "skipped" in ai_readiness_service.STATUS_CODES
