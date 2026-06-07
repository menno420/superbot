"""Tests for services.moderation_config (server-management PR10).

The policy read model + the pure DM renderer that
``services.moderation_service`` applies at its mutation seam.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from services import moderation_config
from services.moderation_config import ModerationPolicy, render_dm_message

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
        "dm_template": "bye {user}",
        "require_reason": True,
        "ban_delete_message_days": 3,
        "max_timeout_minutes": 120,
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
        dm_template="bye {user}",
        require_reason=True,
        ban_delete_message_days=3,
        max_timeout_minutes=120,
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
