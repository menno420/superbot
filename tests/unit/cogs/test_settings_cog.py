"""Unit tests for cogs.settings_cog — S5.

Covers cog registration, the SUBSYSTEMS entry, the feature-flag
gate (ON / OFF), the !settings command behaviour, and the
build_help_menu_view direct-navigation hook.
"""

from __future__ import annotations

import pytest

from cogs import settings_cog
from core.runtime import feature_flags
from utils.subsystem_registry import SUBSYSTEMS

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _FakeGuild:
    def __init__(self, guild_id: int = 1):
        self.id = guild_id


class _FakeMember:
    def __init__(self, member_id: int = 7):
        self.id = member_id


class _FakeContext:
    def __init__(self, guild: _FakeGuild | None = None):
        self.guild = guild
        self.author = _FakeMember()
        self.sent_embeds: list = []
        self.channel = self

    async def send(self, *args, **kwargs):
        embed = kwargs.get("embed")
        if embed is not None:
            self.sent_embeds.append(embed)

        class _Msg:
            id = 1

        return _Msg()


class _FakeInteraction:
    def __init__(self, guild_id: int | None = 1):
        self.guild_id = guild_id
        self.user = _FakeMember()


# ---------------------------------------------------------------------------
# SUBSYSTEMS entry
# ---------------------------------------------------------------------------


def test_settings_subsystem_registered():
    assert "settings" in SUBSYSTEMS
    meta = SUBSYSTEMS["settings"]
    assert meta["visibility_tier"] == "administrator"
    assert "settings" in meta["entry_points"]
    assert "settings.manager.view" in meta["capabilities"]


def test_settings_subsystem_emoji_and_display_name():
    meta = SUBSYSTEMS["settings"]
    assert meta["emoji"] == "⚙️"
    assert meta["display_name"] == "Settings Manager"


# ---------------------------------------------------------------------------
# Feature flag
# ---------------------------------------------------------------------------


def test_feature_flag_declared_default_off():
    flag = feature_flags.get("settings.manager_cog.enabled")
    assert flag is not None
    assert flag.default_value is False
    assert flag.owner == "platform"


# ---------------------------------------------------------------------------
# !settings command — gate behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_settings_command_returns_disabled_embed_when_flag_off(
    monkeypatch,
):
    async def _flag_off(_name, _guild_id):
        return False

    monkeypatch.setattr(feature_flags, "is_enabled", _flag_off)
    cog = settings_cog.SettingsCog(bot=None)  # type: ignore[arg-type]
    ctx = _FakeContext(guild=_FakeGuild())
    await cog.settings_root.callback(cog, ctx)
    assert len(ctx.sent_embeds) == 1
    embed = ctx.sent_embeds[0]
    assert "disabled" in (embed.title or "").lower()


@pytest.mark.asyncio
async def test_settings_command_opens_hub_when_flag_on(monkeypatch):
    async def _flag_on(_name, _guild_id):
        return True

    monkeypatch.setattr(feature_flags, "is_enabled", _flag_on)
    cog = settings_cog.SettingsCog(bot=None)  # type: ignore[arg-type]
    ctx = _FakeContext(guild=_FakeGuild())
    await cog.settings_root.callback(cog, ctx)
    assert len(ctx.sent_embeds) == 1
    embed = ctx.sent_embeds[0]
    # The hub embed title is the settings emoji + name.
    assert "Settings Manager" in (embed.title or "")


@pytest.mark.asyncio
async def test_settings_gate_treats_flag_failure_as_off(monkeypatch):
    async def _flag_raises(_name, _guild_id):
        raise RuntimeError("flag eval failure")

    monkeypatch.setattr(feature_flags, "is_enabled", _flag_raises)
    cog = settings_cog.SettingsCog(bot=None)  # type: ignore[arg-type]
    ctx = _FakeContext(guild=_FakeGuild())
    await cog.settings_root.callback(cog, ctx)
    # Closed gate on failure — returns the disabled embed, not the hub.
    assert len(ctx.sent_embeds) == 1
    assert "disabled" in (ctx.sent_embeds[0].title or "").lower()


# ---------------------------------------------------------------------------
# build_help_menu_view direct-nav hook
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_help_hook_returns_hub_when_flag_on(monkeypatch):
    async def _flag_on(_name, _guild_id):
        return True

    monkeypatch.setattr(feature_flags, "is_enabled", _flag_on)
    cog = settings_cog.SettingsCog(bot=None)  # type: ignore[arg-type]
    interaction = _FakeInteraction()
    embed, view = await cog.build_help_menu_view(interaction)  # type: ignore[arg-type]
    assert "Settings Manager" in (embed.title or "")
    # The hub view contains a Select for subsystems + four buttons; total >= 5.
    assert len(view.children) >= 5


@pytest.mark.asyncio
async def test_help_hook_returns_disabled_view_when_flag_off(monkeypatch):
    async def _flag_off(_name, _guild_id):
        return False

    monkeypatch.setattr(feature_flags, "is_enabled", _flag_off)
    cog = settings_cog.SettingsCog(bot=None)  # type: ignore[arg-type]
    interaction = _FakeInteraction()
    embed, view = await cog.build_help_menu_view(interaction)  # type: ignore[arg-type]
    assert "disabled" in (embed.title or "").lower()
    # The disabled-hook view ships empty (help cog appends its back button).
    assert len(view.children) == 0


# ---------------------------------------------------------------------------
# Static helpers
# ---------------------------------------------------------------------------


def test_disabled_embed_mentions_flag_name():
    embed = settings_cog._disabled_embed()
    description = embed.description or ""
    assert "settings.manager_cog.enabled" in description


# ---------------------------------------------------------------------------
# !settings access subcommand (Phase 6 — access-policy explorer)
# ---------------------------------------------------------------------------


def test_settings_root_is_a_group_after_phase_6():
    """``!settings`` was a single command; Phase 6 converts it to a group so
    ``!settings access`` can hang off it without losing the bare-command UX."""
    from discord.ext import commands

    assert isinstance(settings_cog.SettingsCog.settings_root, commands.Group)
    assert settings_cog.SettingsCog.settings_root.invoke_without_command is True


def test_settings_access_subcommand_registered():
    """The ``access`` subcommand must exist on the settings group."""
    sub = settings_cog.SettingsCog.settings_root.get_command("access")
    assert sub is not None
    assert sub.name == "access"


@pytest.mark.asyncio
async def test_settings_access_opens_explorer_view_regardless_of_gate(monkeypatch):
    """The access explorer is a separate diagnostic — it must not share the
    Settings Manager gate. Even when the gate is OFF, ``!settings access``
    opens the explorer.
    """
    from unittest.mock import AsyncMock, MagicMock

    async def _flag_off(_name, _guild_id):
        return False

    monkeypatch.setattr(feature_flags, "is_enabled", _flag_off)
    monkeypatch.setattr(
        "governance.get_visible_subsystems",
        AsyncMock(return_value={"settings"}),
    )
    # GovernanceContext.from_ctx reads ctx.guild / ctx.author / ctx.channel;
    # the _FakeContext above satisfies enough of that interface.
    fake_gctx = MagicMock()
    monkeypatch.setattr(
        "governance.GovernanceContext.from_ctx",
        lambda _ctx: fake_gctx,
    )

    cog = settings_cog.SettingsCog(bot=None)  # type: ignore[arg-type]
    ctx = _FakeContext(guild=_FakeGuild())
    await cog.settings_access.callback(cog, ctx)

    assert len(ctx.sent_embeds) == 1
    embed = ctx.sent_embeds[0]
    title = (embed.title or "").lower()
    assert "access" in title


def test_setup_function_exists_and_adds_cog():
    """The discord.py extension entry point must exist."""
    assert callable(settings_cog.setup)
