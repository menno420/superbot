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

    # DM greeting needs only the master + dm flag (no channel) and counts as an
    # action on its own.
    dm_only = WelcomePolicy(enabled=True, join_enabled=False, dm_enabled=True)
    assert dm_only.dm_on_join
    assert dm_only.any_action_enabled
    assert not dm_only.greet_on_join
    # Master off → DM suppressed like every other action.
    assert not WelcomePolicy(enabled=False, dm_enabled=True).dm_on_join
    # DM defaults off.
    assert not WelcomePolicy(enabled=True).dm_on_join


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


# ---------------------------------------------------------------------------
# Multiple / random messages (completion punch-list #2)
# ---------------------------------------------------------------------------


def test_split_message_variants_single_message_is_one_variant():
    # No separator → exactly the one message, unchanged (back-compat).
    assert welcome_config.split_message_variants("Welcome {user}!") == [
        "Welcome {user}!"
    ]


def test_split_message_variants_splits_on_dash_rule_and_strips():
    raw = "Hey {user}!\n---\nWelcome aboard {user}\n-----\n  Glad you're here  "
    assert welcome_config.split_message_variants(raw) == [
        "Hey {user}!",
        "Welcome aboard {user}",
        "Glad you're here",
    ]


def test_split_message_variants_drops_empty_blocks_and_bare_separators():
    # Whitespace-only / separator-only blocks are not real variants.
    assert welcome_config.split_message_variants("   \n---\n---\n  ") == []
    # A dash line inside otherwise-empty text yields no variants.
    assert welcome_config.split_message_variants("---") == []


def test_split_message_variants_requires_three_dashes():
    # A two-dash line is content, not a separator.
    assert welcome_config.split_message_variants("a\n--\nb") == ["a\n--\nb"]


def test_pick_message_single_variant_is_deterministic():
    import random

    # One variant → always that variant, regardless of rng.
    for seed in range(5):
        assert (
            welcome_config.pick_message("only one", rng=random.Random(seed))
            == "only one"
        )


def test_pick_message_chooses_among_variants_with_seeded_rng():
    import random

    raw = "one\n---\ntwo\n---\nthree"
    variants = {
        welcome_config.pick_message(raw, rng=random.Random(s)) for s in range(20)
    }
    # Every pick is a real variant…
    assert variants <= {"one", "two", "three"}
    # …and across seeds we see more than one (it actually randomises).
    assert len(variants) > 1


def test_pick_message_fails_open_on_empty_template():
    import random

    # Degenerate value (no real variants) → returns the raw template, never
    # raises, so the render path stays fail-open.
    assert welcome_config.pick_message("---", rng=random.Random(0)) == "---"


# ---------------------------------------------------------------------------
# Join-delay age-gating helper (account_is_too_young)
# ---------------------------------------------------------------------------


def test_account_is_too_young_gate_off_is_always_false():
    import datetime as dt

    now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    created = now - dt.timedelta(days=0)  # created right now
    # min_age_days=0 disables the gate entirely.
    assert (
        welcome_config.account_is_too_young(created, min_age_days=0, now=now) is False
    )


def test_account_is_too_young_below_threshold_is_true():
    import datetime as dt

    now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    created = now - dt.timedelta(days=2)  # 2 days old
    assert welcome_config.account_is_too_young(created, min_age_days=7, now=now) is True


def test_account_is_too_young_at_or_above_threshold_is_false():
    import datetime as dt

    now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    created = now - dt.timedelta(days=10)  # 10 days old, gate is 7
    assert (
        welcome_config.account_is_too_young(created, min_age_days=7, now=now) is False
    )


def test_account_is_too_young_unknown_age_fails_open():
    import datetime as dt

    now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    # None created_at → treated as old enough (greet), never raises.
    assert welcome_config.account_is_too_young(None, min_age_days=7, now=now) is False


def test_account_is_too_young_mixed_awareness_does_not_raise():
    import datetime as dt

    now = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
    naive = dt.datetime(2026, 1, 1)  # naive — comparison would TypeError
    # Tolerated: returns False rather than raising.
    assert welcome_config.account_is_too_young(naive, min_age_days=7, now=now) is False


# ---------------------------------------------------------------------------
# Policy convenience properties (age gate + delete-after)
# ---------------------------------------------------------------------------


def test_age_gate_enabled_property():
    assert WelcomePolicy(min_account_age_days=0).age_gate_enabled is False
    assert WelcomePolicy(min_account_age_days=7).age_gate_enabled is True


def test_greeting_delete_after_property():
    assert WelcomePolicy(delete_after_seconds=0).greeting_delete_after is None
    assert WelcomePolicy(delete_after_seconds=30).greeting_delete_after == 30.0


def test_policy_defaults_keep_new_options_off():
    # A fresh policy is byte-identical to v1: no gate, no auto-delete.
    p = WelcomePolicy()
    assert p.min_account_age_days == welcome_config.DEFAULT_MIN_ACCOUNT_AGE_DAYS == 0
    assert p.delete_after_seconds == welcome_config.DEFAULT_DELETE_AFTER_SECONDS == 0
    assert p.age_gate_enabled is False
    assert p.greeting_delete_after is None
