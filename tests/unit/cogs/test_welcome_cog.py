"""Unit tests for the welcome cog status surface (cogs.welcome_cog).

Focused on ``_policy_embed`` — the read-only status preview rendered by
``!welcome`` and the Help hook — and specifically the multiple/random-message
preview (completion punch-list #2): the preview shows the **first** variant with
a "1 of N random variants" note instead of dumping the raw separator-laden value.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import discord

from cogs.welcome_cog import WelcomeCog
from services.welcome_config import WelcomePolicy


def _guild() -> MagicMock:
    g = MagicMock(spec=discord.Guild)
    g.id = 1
    g.name = "Demo"
    g.member_count = 1235
    g.get_channel.return_value = None
    g.get_role.return_value = None
    return g


def _field_by_name_prefix(
    embed: discord.Embed, prefix: str
) -> discord.embeds.EmbedProxy:
    for field in embed.fields:
        if field.name.startswith(prefix):
            return field
    raise AssertionError(f"no field starting with {prefix!r}")


def test_policy_embed_single_message_has_no_variant_note():
    policy = WelcomePolicy(enabled=True, join_message="Welcome {user}!")
    embed = WelcomeCog._policy_embed(_guild(), policy)
    field = _field_by_name_prefix(embed, "Join message preview")
    # A single message: no "random variants" suffix, placeholders expanded.
    assert field.name == "Join message preview"
    assert field.value == "Welcome @NewMember!"


def test_policy_embed_multi_variant_shows_count_and_first_variant():
    policy = WelcomePolicy(
        enabled=True,
        join_message="First {user}\n---\nSecond {user}\n---\nThird {user}",
    )
    embed = WelcomeCog._policy_embed(_guild(), policy)
    field = _field_by_name_prefix(embed, "Join message preview")
    assert field.name == "Join message preview (1 of 3 random variants)"
    # Shows the FIRST variant rendered — never the raw "---" separators.
    assert field.value == "First @NewMember"
    assert "---" not in field.value


def test_policy_embed_shows_dm_preview_when_dm_enabled():
    policy = WelcomePolicy(
        enabled=True,
        dm_enabled=True,
        dm_message="DM hi {user}",
    )
    embed = WelcomeCog._policy_embed(_guild(), policy)
    field = _field_by_name_prefix(embed, "DM message preview")
    assert field.value == "DM hi @NewMember"
    # DM on/off is surfaced in the status body.
    assert "DM on join" in embed.description


def test_policy_embed_no_dm_preview_when_dm_disabled():
    policy = WelcomePolicy(enabled=True, dm_enabled=False)
    embed = WelcomeCog._policy_embed(_guild(), policy)
    assert not any(f.name.startswith("DM message preview") for f in embed.fields)


def test_policy_embed_leave_variant_note_when_leave_enabled():
    policy = WelcomePolicy(
        enabled=True,
        leave_enabled=True,
        leave_message="Bye {user}\n---\nFarewell {user}",
    )
    embed = WelcomeCog._policy_embed(_guild(), policy)
    field = _field_by_name_prefix(embed, "Leave message preview")
    assert field.name == "Leave message preview (1 of 2 random variants)"
    assert field.value == "Bye NewMember"


def test_policy_embed_shows_age_gate_when_set():
    policy = WelcomePolicy(enabled=True, min_account_age_days=7)
    embed = WelcomeCog._policy_embed(_guild(), policy)
    assert "Min account age" in embed.description
    assert "7d" in embed.description
    # …and is absent when the gate is off.
    off = WelcomeCog._policy_embed(_guild(), WelcomePolicy(enabled=True))
    assert "Min account age" not in off.description


def test_policy_embed_shows_auto_delete_when_set():
    policy = WelcomePolicy(enabled=True, delete_after_seconds=30)
    embed = WelcomeCog._policy_embed(_guild(), policy)
    assert "Auto-delete greeting after" in embed.description
    assert "30s" in embed.description
    # …and is absent when off.
    off = WelcomeCog._policy_embed(_guild(), WelcomePolicy(enabled=True))
    assert "Auto-delete greeting after" not in off.description
