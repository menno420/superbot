"""Unit tests for the privileged-tier slash front doors (PR E2).

Pins the contract for ``/admin``, ``/settings``, ``/moderation``, and
``/platform``:

* Each slash command is registered on its owning cog.
* Each carries a runtime permission check via
  ``@app_commands.checks.has_permissions`` AND the corresponding
  ``@app_commands.default_permissions`` Discord-side visibility hint.
  Both layers must be present so the gate works regardless of
  whether the guild's Discord client respects the visibility hint.
* Successful callbacks respond ephemerally.
* Each callback delegates to the existing panel builder — no
  business-logic duplication.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest
from discord.ext import commands

from cogs.admin_cog import AdminCog
from cogs.diagnostic_cog import DiagnosticCog
from cogs.moderation_cog import ModerationCog
from cogs.settings_cog import SettingsCog


def _interaction(user_id: int = 1) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    user = MagicMock(spec=discord.Member)
    user.id = user_id
    interaction.user = user
    interaction.guild = MagicMock()
    interaction.guild_id = 42
    interaction.channel = MagicMock()
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


def _has_app_command(cog: commands.Cog, name: str) -> bool:
    return any(cmd.name == name for cmd in cog.walk_app_commands())


def _get_app_command(cog: commands.Cog, name: str):
    for cmd in cog.walk_app_commands():
        if cmd.name == name:
            return cmd
    raise AssertionError(f"No app command named {name!r}")


# ---------------------------------------------------------------------------
# Each privileged slash command is registered
# ---------------------------------------------------------------------------


def test_admin_cog_has_slash_command():
    assert _has_app_command(AdminCog(MagicMock(spec=commands.Bot)), "admin")


def test_settings_cog_has_slash_command():
    assert _has_app_command(SettingsCog(MagicMock(spec=commands.Bot)), "settings")


def test_moderation_cog_has_slash_command():
    assert _has_app_command(
        ModerationCog(MagicMock(spec=commands.Bot)),
        "moderation",
    )


def test_diagnostic_cog_has_platform_slash_command():
    assert _has_app_command(DiagnosticCog(MagicMock(spec=commands.Bot)), "platform")


# ---------------------------------------------------------------------------
# Each privileged slash carries default_permissions (Discord UI hide)
# ---------------------------------------------------------------------------


def test_admin_slash_default_permissions_administrator():
    cmd = _get_app_command(AdminCog(MagicMock(spec=commands.Bot)), "admin")
    perms = cmd.default_permissions
    assert perms is not None
    assert perms.administrator is True


def test_settings_slash_default_permissions_administrator():
    cmd = _get_app_command(SettingsCog(MagicMock(spec=commands.Bot)), "settings")
    perms = cmd.default_permissions
    assert perms is not None
    assert perms.administrator is True


def test_moderation_slash_default_permissions_moderate_members():
    cmd = _get_app_command(
        ModerationCog(MagicMock(spec=commands.Bot)),
        "moderation",
    )
    perms = cmd.default_permissions
    assert perms is not None
    assert perms.moderate_members is True


def test_platform_slash_default_permissions_administrator():
    cmd = _get_app_command(DiagnosticCog(MagicMock(spec=commands.Bot)), "platform")
    perms = cmd.default_permissions
    assert perms is not None
    assert perms.administrator is True


# ---------------------------------------------------------------------------
# Each privileged slash carries a runtime has_permissions check
# ---------------------------------------------------------------------------


def _has_runtime_permission_check(cmd) -> bool:
    """Return True if ``cmd.checks`` contains a runtime admin check.

    Either discord.py's ``has_permissions`` or the owner-aware
    ``perms_or_owner`` / ``app_perms_or_owner`` (and the ``admin_or_owner``
    wrappers) that replaced every ``has_permissions(...)`` bot-wide (Q-0212) —
    all register a predicate on ``Command.checks``; match on the qualified name
    (every owner-aware check's predicate qualname contains ``_or_owner``).
    """
    for check in cmd.checks:
        qn = getattr(check, "__qualname__", "")
        if "has_permissions" in qn or "_or_owner" in qn:
            return True
    return False


def test_admin_slash_has_runtime_admin_check():
    cmd = _get_app_command(AdminCog(MagicMock(spec=commands.Bot)), "admin")
    assert _has_runtime_permission_check(cmd)


def test_settings_slash_has_runtime_admin_check():
    cmd = _get_app_command(SettingsCog(MagicMock(spec=commands.Bot)), "settings")
    assert _has_runtime_permission_check(cmd)


def test_moderation_slash_has_runtime_mod_check():
    cmd = _get_app_command(
        ModerationCog(MagicMock(spec=commands.Bot)),
        "moderation",
    )
    assert _has_runtime_permission_check(cmd)


def test_platform_slash_has_runtime_admin_check():
    cmd = _get_app_command(DiagnosticCog(MagicMock(spec=commands.Bot)), "platform")
    assert _has_runtime_permission_check(cmd)


# ---------------------------------------------------------------------------
# Successful callbacks respond ephemerally and reuse existing builders
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_slash_responds_ephemerally():
    cog = AdminCog(MagicMock(spec=commands.Bot))
    interaction = _interaction()

    fake_embed = discord.Embed(title="Admin")
    fake_view = discord.ui.View()

    with patch.object(
        cog,
        "build_help_menu_view",
        AsyncMock(return_value=(fake_embed, fake_view)),
    ):
        await cog.admin_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    _args, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("embed") is fake_embed
    assert kwargs.get("view") is fake_view
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_settings_slash_responds_ephemerally():
    cog = SettingsCog(MagicMock(spec=commands.Bot))
    interaction = _interaction()

    fake_embed = discord.Embed(title="Settings")
    fake_view = discord.ui.View()

    with patch.object(
        cog,
        "build_help_menu_view",
        AsyncMock(return_value=(fake_embed, fake_view)),
    ):
        await cog.settings_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    _args, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("embed") is fake_embed
    assert kwargs.get("view") is fake_view
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_moderation_slash_responds_ephemerally():
    cog = ModerationCog(MagicMock(spec=commands.Bot))
    interaction = _interaction()

    fake_embed = discord.Embed(title="Moderation")
    fake_view = discord.ui.View()

    with patch.object(
        cog,
        "build_help_menu_view",
        AsyncMock(return_value=(fake_embed, fake_view)),
    ):
        await cog.moderation_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    _args, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("embed") is fake_embed
    assert kwargs.get("view") is fake_view
    assert kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_platform_slash_responds_ephemerally():
    cog = DiagnosticCog(MagicMock(spec=commands.Bot))
    interaction = _interaction()

    fake_embed = discord.Embed(title="Platform")
    fake_view = discord.ui.View()

    with patch.object(
        cog,
        "build_platform_help_menu_view",
        AsyncMock(return_value=(fake_embed, fake_view)),
    ):
        await cog.platform_slash.callback(cog, interaction)

    interaction.response.send_message.assert_awaited_once()
    _args, kwargs = interaction.response.send_message.call_args
    assert kwargs.get("embed") is fake_embed
    assert kwargs.get("view") is fake_view
    assert kwargs.get("ephemeral") is True


# ---------------------------------------------------------------------------
# Descriptions present for Discord's autocomplete UI
# ---------------------------------------------------------------------------


def test_privileged_slash_callbacks_have_descriptions():
    cogs = [
        AdminCog(MagicMock(spec=commands.Bot)),
        SettingsCog(MagicMock(spec=commands.Bot)),
        ModerationCog(MagicMock(spec=commands.Bot)),
        DiagnosticCog(MagicMock(spec=commands.Bot)),
    ]
    seen: set[str] = set()
    for cog in cogs:
        for cmd in cog.walk_app_commands():
            if cmd.name in {"admin", "settings", "moderation", "platform"}:
                seen.add(cmd.name)
                assert cmd.description, (
                    f"/{cmd.name} has empty description — Discord requires "
                    f"a non-empty description on slash commands."
                )
    assert seen == {"admin", "settings", "moderation", "platform"}
