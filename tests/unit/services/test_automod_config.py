"""Unit tests for the automod config read model (services.automod_config)."""

from __future__ import annotations

import pytest

from services import automod_config
from services.automod_config import AutomodPolicy, parse_id_csv


def test_parse_id_csv_tolerant():
    assert parse_id_csv("1, 2 ,3") == frozenset({1, 2, 3})
    assert parse_id_csv("") == frozenset()
    # Malformed tokens are skipped, not raised — the read model must never fail.
    assert parse_id_csv("1, oops, 3") == frozenset({1, 3})


def test_any_rule_enabled():
    assert not AutomodPolicy(enabled=True).any_rule_enabled
    assert AutomodPolicy(enabled=True, spam_enabled=True).any_rule_enabled
    assert AutomodPolicy(enabled=True, mentions_enabled=True).any_rule_enabled
    assert AutomodPolicy(
        enabled=True, cross_channel_spam_enabled=True
    ).any_rule_enabled
    assert AutomodPolicy(enabled=True, duplicate_enabled=True).any_rule_enabled


def test_defaults_are_all_off():
    pol = AutomodPolicy()
    assert pol.enabled is False
    assert not pol.any_rule_enabled


@pytest.mark.asyncio
async def test_load_policy_composes_typed_values(monkeypatch):
    stored = {
        "enabled": True,
        "spam_enabled": True,
        "spam_count": 8,
        "cross_channel_spam_enabled": True,
        "cross_channel_spam_count": 3,
        "duplicate_enabled": True,
        "duplicate_count": 4,
        "exempt_roles": "10, 20",
        "exempt_channels": "30",
    }

    async def fake_resolve(guild_id, subsystem, name, fallback):
        assert subsystem == "automod"
        return stored.get(name, fallback)

    import services.settings_resolution as sr

    monkeypatch.setattr(sr, "resolve_value", fake_resolve)

    pol = await automod_config.load_policy(guild_id=123)
    assert pol.enabled is True
    assert pol.spam_enabled is True
    assert pol.spam_count == 8
    assert pol.cross_channel_spam_enabled is True
    assert pol.cross_channel_spam_count == 3
    assert pol.duplicate_enabled is True
    assert pol.duplicate_count == 4
    assert pol.exempt_role_ids == frozenset({10, 20})
    assert pol.exempt_channel_ids == frozenset({30})
    # Unset fields fall back to the canonical defaults.
    assert pol.invites_enabled is automod_config.DEFAULT_INVITES_ENABLED
    assert pol.caps_percent == automod_config.DEFAULT_CAPS_PERCENT
