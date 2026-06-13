"""Unit tests for the welcome config read model (services.welcome_config)."""

from __future__ import annotations

import pytest

from services import welcome_config
from services.welcome_config import WelcomePolicy, parse_id, render_template


def test_parse_id_tolerant():
    assert parse_id("123") == 123
    assert parse_id(" 456 ") == 456
    assert parse_id("") is None
    assert parse_id(None) is None
    # Malformed input degrades to None, never raises — the read model must
    # never fail on a fat-fingered id.
    assert parse_id("oops") is None


def test_render_template_substitutes_placeholders():
    out = render_template(
        "Hi {user}, welcome to {server} — member #{count}!",
        member_name="@Astro",
        guild_name="Demo",
        member_count=1235,
    )
    assert out == "Hi @Astro, welcome to Demo — member #1,235!"


def test_render_template_is_injection_safe():
    # Stray / unknown braces render literally rather than raising KeyError
    # (the str.format trap the read model deliberately avoids).
    out = render_template(
        "{user} {unknown} {0} literal {",
        member_name="Astro",
        guild_name="Demo",
        member_count=5,
    )
    assert out == "Astro {unknown} {0} literal {"


def test_action_predicates_require_master_and_resource():
    # Master off → nothing fires even with everything else set.
    off = WelcomePolicy(enabled=False, join_enabled=True, channel_id=1, entry_role_id=2)
    assert not off.greet_on_join
    assert not off.assigns_entry_role
    assert not off.any_action_enabled

    # Join greeting needs the master + join flag + a channel.
    no_channel = WelcomePolicy(enabled=True, join_enabled=True, channel_id=None)
    assert not no_channel.greet_on_join
    greet = WelcomePolicy(enabled=True, join_enabled=True, channel_id=10)
    assert greet.greet_on_join
    assert greet.any_action_enabled

    # Farewell is independent and defaults off.
    assert not greet.greet_on_leave
    farewell = WelcomePolicy(enabled=True, leave_enabled=True, channel_id=10)
    assert farewell.greet_on_leave

    # Entry role works without a channel (no greeting, role only).
    role_only = WelcomePolicy(enabled=True, join_enabled=False, entry_role_id=99)
    assert role_only.assigns_entry_role
    assert role_only.any_action_enabled
    assert not role_only.greet_on_join


def test_defaults_master_off_join_on():
    pol = WelcomePolicy()
    assert pol.enabled is False  # master off — a fresh guild is unaffected
    assert pol.join_enabled is True  # but join greeting is the sensible default
    assert pol.leave_enabled is False
    assert pol.channel_id is None
    assert pol.entry_role_id is None
    assert not pol.any_action_enabled  # gated by the master switch


@pytest.mark.asyncio
async def test_load_policy_composes_typed_values(monkeypatch):
    stored = {
        "enabled": True,
        "join_enabled": True,
        "leave_enabled": True,
        "channel": "555",
        "entry_role": "777",
        "join_message": "hi {user}",
    }

    async def fake_resolve(guild_id, subsystem, name, fallback):
        assert subsystem == "welcome"
        return stored.get(name, fallback)

    import services.settings_resolution as sr

    monkeypatch.setattr(sr, "resolve_value", fake_resolve)

    pol = await welcome_config.load_policy(guild_id=123)
    assert pol.enabled is True
    assert pol.channel_id == 555
    assert pol.entry_role_id == 777
    assert pol.join_message == "hi {user}"
    # Unset fields fall back to the canonical defaults.
    assert pol.leave_message == welcome_config.DEFAULT_LEAVE_MESSAGE
    assert pol.greet_on_join and pol.greet_on_leave and pol.assigns_entry_role


@pytest.mark.asyncio
async def test_load_policy_blank_channel_degrades_to_none(monkeypatch):
    async def fake_resolve(guild_id, subsystem, name, fallback):
        if name == "enabled":
            return True
        return fallback  # channel stays the "" default → parse_id → None

    import services.settings_resolution as sr

    monkeypatch.setattr(sr, "resolve_value", fake_resolve)

    pol = await welcome_config.load_policy(guild_id=1)
    assert pol.channel_id is None
    assert not pol.greet_on_join  # no destination → no greeting
