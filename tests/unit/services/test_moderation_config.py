"""Tests for services.moderation_config (server-management PR10).

The policy read model + the pure DM renderer that
``services.moderation_service`` applies at its mutation seam.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from services import moderation_config
from services.moderation_config import (
    EscalationDecision,
    ModerationPolicy,
    evaluate_escalation,
    render_dm_message,
)

# ---------------------------------------------------------------------------
# ModerationPolicy derived properties
# ---------------------------------------------------------------------------


def test_default_policy_is_behaviour_preserving():
    policy = ModerationPolicy()
    assert policy.dm_on_action is False
    assert policy.dm_template == ""
    assert policy.require_reason is False
    assert policy.ban_delete_message_days == 0
    assert policy.max_timeout_minutes == 40320  # 28 days, Discord's max
    # Default ban purge is a no-op; default ceiling is Discord's hard max.
    assert policy.ban_delete_message_seconds == 0
    assert policy.effective_max_timeout_minutes == 40320
    # Escalation defaults reproduce today's warn→auto-timeout→reset ladder.
    assert policy.warn_threshold == 3
    assert policy.warn_timeout_minutes == 10
    assert policy.warn_escalation_action == "timeout"
    # Post-action cleanup is off by default (behaviour-preserving).
    assert policy.post_action_cleanup == "none"
    assert policy.post_action_cleanup_limit == 100
    assert policy.effective_post_action_cleanup_limit == 100
    # Public moderation log is off by default (no channel, no actions).
    assert policy.public_log_channel == ""
    assert policy.public_log_channel_id == 0
    assert policy.public_log_actions == "none"
    # Per-action DM list defaults to all four notify-eligible actions, so the
    # gate is purely the master switch until an owner narrows it (today's
    # behaviour when DMs are turned on).
    assert policy.dm_action_set == frozenset({"warn", "timeout", "kick", "ban"})


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("warn,timeout,kick,ban", {"warn", "timeout", "kick", "ban"}),
        ("warn,timeout", {"warn", "timeout"}),
        (" Warn , BAN ", {"warn", "ban"}),  # case/space tolerant
        ("warn,warn,warn", {"warn"}),  # de-duplicated
        ("warn,bogus,auto_delete", {"warn"}),  # unknown tokens dropped fail-safe
        ("", set()),  # empty = no action DMs
        ("nonsense", set()),
    ],
)
def test_dm_action_set_parses_and_validates(raw, expected):
    assert ModerationPolicy(dm_actions=raw).dm_action_set == frozenset(expected)
    # The module-level helper is the shared source of truth.
    assert moderation_config.parse_dm_actions(raw) == frozenset(expected)


@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        ("spam", True),
        ("  trailing  ", True),
        ("", False),
        ("   ", False),
        (None, False),
        ("No reason provided", False),  # placeholder counts as no reason
        ("no reason provided", False),
    ],
)
def test_has_reason_is_placeholder_aware(reason, expected):
    assert moderation_config.has_reason(reason) is expected


def test_ban_delete_seconds_clamps_into_discord_window():
    # In-range days convert to seconds.
    assert (
        ModerationPolicy(ban_delete_message_days=1).ban_delete_message_seconds == 86400
    )
    assert (
        ModerationPolicy(ban_delete_message_days=7).ban_delete_message_seconds
        == 7 * 86400
    )
    # Out-of-range values are clamped defensively (never raise at guild.ban).
    assert (
        ModerationPolicy(ban_delete_message_days=99).ban_delete_message_seconds
        == 7 * 86400
    )
    assert ModerationPolicy(ban_delete_message_days=-5).ban_delete_message_seconds == 0


def test_effective_timeout_ceiling_clamps_into_discord_window():
    assert ModerationPolicy(max_timeout_minutes=60).effective_max_timeout_minutes == 60
    # Above Discord's 28-day max clamps down.
    assert (
        ModerationPolicy(max_timeout_minutes=10**9).effective_max_timeout_minutes
        == 40320
    )
    # Below 1 minute clamps up.
    assert ModerationPolicy(max_timeout_minutes=0).effective_max_timeout_minutes == 1


# ---------------------------------------------------------------------------
# load_policy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_load_policy_maps_resolved_values():
    resolved = {
        "dm_on_action": True,
        "dm_actions": "warn,ban",
        "dm_template": "bye {user}",
        "require_reason": True,
        "ban_delete_message_days": 3,
        "max_timeout_minutes": 120,
        "warn_threshold": 5,
        "warn_timeout_minutes": 25,
        "warn_escalation_action": "kick",
        "post_action_cleanup": "both",
        "post_action_cleanup_limit": 200,
        "public_log_channel": "987654321",
        "public_log_actions": "removals",
    }

    async def _fake_resolve(guild_id, subsystem, name, fallback):
        assert subsystem == "moderation"
        return resolved[name]

    with patch(
        "services.settings_resolution.resolve_value",
        side_effect=_fake_resolve,
    ):
        policy = await moderation_config.load_policy(42)

    assert policy == ModerationPolicy(
        dm_on_action=True,
        dm_actions="warn,ban",
        dm_template="bye {user}",
        require_reason=True,
        ban_delete_message_days=3,
        max_timeout_minutes=120,
        warn_threshold=5,
        warn_timeout_minutes=25,
        warn_escalation_action="kick",
        post_action_cleanup="both",
        post_action_cleanup_limit=200,
        public_log_channel="987654321",
        public_log_actions="removals",
    )


@pytest.mark.asyncio
async def test_load_policy_falls_back_to_defaults():
    """When the resolver yields the fallback (no spec / empty KV) the policy
    is the canonical default baseline."""

    async def _echo_fallback(guild_id, subsystem, name, fallback):
        return fallback

    with patch(
        "services.settings_resolution.resolve_value",
        side_effect=_echo_fallback,
    ):
        policy = await moderation_config.load_policy(7)

    assert policy == ModerationPolicy()


# ---------------------------------------------------------------------------
# evaluate_escalation — the pure warn-ladder decision
# ---------------------------------------------------------------------------


def test_escalation_below_threshold_returns_none():
    policy = ModerationPolicy(warn_threshold=3)
    assert evaluate_escalation(1, policy) is None
    assert evaluate_escalation(2, policy) is None


def test_escalation_default_action_is_timeout_at_threshold():
    policy = ModerationPolicy()  # threshold 3, timeout 10, action "timeout"
    decision = evaluate_escalation(3, policy)
    assert decision == EscalationDecision(action="timeout", timeout_minutes=10)
    # At or above the threshold escalates.
    assert evaluate_escalation(9, policy) == EscalationDecision(
        action="timeout", timeout_minutes=10
    )


@pytest.mark.parametrize("action", ["kick", "ban"])
def test_escalation_non_timeout_actions_carry_no_duration(action):
    policy = ModerationPolicy(warn_threshold=2, warn_escalation_action=action)
    decision = evaluate_escalation(2, policy)
    assert decision == EscalationDecision(action=action, timeout_minutes=0)


def test_escalation_none_disables_escalation():
    policy = ModerationPolicy(warn_threshold=1, warn_escalation_action="none")
    assert evaluate_escalation(99, policy) is None


def test_escalation_unknown_action_fails_safe_to_none():
    """A malformed stored action never performs an unintended kick/ban."""
    policy = ModerationPolicy(warn_threshold=1, warn_escalation_action="explode")
    assert evaluate_escalation(99, policy) is None


def test_escalation_respects_configured_timeout_minutes():
    policy = ModerationPolicy(warn_threshold=5, warn_timeout_minutes=45)
    assert evaluate_escalation(5, policy) == EscalationDecision(
        action="timeout", timeout_minutes=45
    )


# ---------------------------------------------------------------------------
# cleanup_applies_to / effective_post_action_cleanup_limit (PR10 fourth slice)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("setting", "action", "expected"),
    [
        ("none", "kick", False),
        ("none", "ban", False),
        ("kick", "kick", True),
        ("kick", "ban", False),
        ("ban", "ban", True),
        ("ban", "kick", False),
        ("both", "kick", True),
        ("both", "ban", True),
        ("garbage", "kick", False),  # fail-safe: unknown value never sweeps
    ],
)
def test_cleanup_applies_to(setting, action, expected):
    policy = ModerationPolicy(post_action_cleanup=setting)
    assert moderation_config.cleanup_applies_to(action, policy) is expected


def test_effective_cleanup_limit_clamps_into_window():
    assert (
        ModerationPolicy(post_action_cleanup_limit=50).effective_post_action_cleanup_limit
        == 50
    )
    # Above the automatic-sweep ceiling clamps down.
    assert (
        ModerationPolicy(
            post_action_cleanup_limit=10**6
        ).effective_post_action_cleanup_limit
        == 500
    )
    # Below 1 clamps up.
    assert (
        ModerationPolicy(post_action_cleanup_limit=0).effective_post_action_cleanup_limit
        == 1
    )


# ---------------------------------------------------------------------------
# public_log_includes / public_log_channel_id (PR10 fifth slice)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("actions", "action", "expected"),
    [
        ("none", "ban", False),
        ("none", "warn", False),
        ("bans", "ban", True),
        ("bans", "kick", False),
        ("removals", "kick", True),
        ("removals", "ban", True),
        ("removals", "warn", False),
        ("all", "warn", True),
        ("all", "timeout", True),
        ("all", "ban", True),
        # never-public actions stay private under every selector
        ("all", "unban", False),
        ("all", "clearwarnings", False),
        ("all", "post_action_cleanup", False),
        ("garbage", "ban", False),  # fail-safe
    ],
)
def test_public_log_includes(actions, action, expected):
    policy = ModerationPolicy(public_log_actions=actions)
    assert moderation_config.public_log_includes(action, policy) is expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("987654321", 987654321), ("", 0), ("  42 ", 42), ("notanid", 0), ("-5", 0)],
)
def test_public_log_channel_id_parsing(raw, expected):
    assert ModerationPolicy(public_log_channel=raw).public_log_channel_id == expected


# ---------------------------------------------------------------------------
# render_dm_message — built-in bodies
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("action", "verb"),
    [
        ("warn", "warned"),
        ("timeout", "timed out"),
        ("kick", "kicked"),
        ("ban", "banned"),
    ],
)
def test_render_builtin_includes_action_and_guild(action, verb):
    body = render_dm_message(
        action=action, guild_name="Cool Guild", reason="being loud"
    )
    assert verb in body
    assert "**Cool Guild**" in body
    assert "**Reason:** being loud" in body


def test_render_builtin_omits_reason_when_placeholder_or_empty():
    for reason in ("", "   ", "No reason provided", "no reason provided"):
        body = render_dm_message(action="ban", guild_name="G", reason=reason)
        assert "Reason" not in body
        assert "banned" in body


# ---------------------------------------------------------------------------
# render_dm_message — custom template
# ---------------------------------------------------------------------------


def test_render_custom_template_substitutes_all_tokens():
    body = render_dm_message(
        action="kick",
        guild_name="My Server",
        reason="spamming",
        target_name="Alice",
        template="Hi {user}, you were {action} from {guild}. Why: {reason}",
    )
    assert body == "Hi Alice, you were kicked from My Server. Why: spamming"


def test_render_custom_template_empty_reason_becomes_dash():
    body = render_dm_message(
        action="warn",
        guild_name="G",
        reason="",
        template="reason={reason}",
    )
    assert body == "reason=—"


def test_render_custom_template_missing_target_defaults_to_you():
    body = render_dm_message(
        action="ban",
        guild_name="G",
        reason="x",
        template="bye {user}",
    )
    assert body == "bye you"


def test_render_custom_template_does_not_use_str_format():
    """A stray brace / attribute expression in operator input must not raise
    or leak — only the four known tokens are replaced."""
    body = render_dm_message(
        action="ban",
        guild_name="G",
        reason="x",
        template="literal {0.__class__} and {unknown} stay verbatim",
    )
    assert body == "literal {0.__class__} and {unknown} stay verbatim"
