"""Tests for the mod panel embed's Bot-readiness field (server-management PR10).

``_build_mod_panel_embed(guild)`` appends a read-only readiness field; the
no-guild call (persistent-view restore) must not.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from cogs.moderation._helpers import _build_mod_panel_embed

_READINESS = "🤖 Bot readiness"


def _guild(
    *,
    ban: bool = True,
    kick: bool = True,
    timeout: bool = True,
    top_position: int = 5,
    top_name: str = "Galaxy Bot",
) -> MagicMock:
    guild = MagicMock()
    perms = MagicMock()
    perms.ban_members = ban
    perms.kick_members = kick
    perms.moderate_members = timeout
    perms.administrator = False
    guild.me.guild_permissions = perms
    guild.me.top_role.position = top_position
    guild.me.top_role.name = top_name
    return guild


def test_embed_without_guild_has_no_readiness_field():
    embed = _build_mod_panel_embed()
    assert _READINESS not in [f.name for f in embed.fields]


def test_embed_with_guild_adds_readiness_field():
    embed = _build_mod_panel_embed(_guild())
    field = next(f for f in embed.fields if f.name == _READINESS)
    assert "🟢" in field.value
    assert "**Galaxy Bot**" in field.value


def test_embed_readiness_field_flags_missing_permission():
    embed = _build_mod_panel_embed(_guild(ban=False))
    field = next(f for f in embed.fields if f.name == _READINESS)
    assert "Ban Members" in field.value
