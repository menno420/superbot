"""services.btd6_version_announce — setting I/O + announcement posting."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_version_announce as announce  # noqa: E402
from utils.settings_keys import BTD6_VERSION_ANNOUNCEMENT_CHANNEL  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_module():
    announce._reset_for_tests()
    yield
    announce._reset_for_tests()


# ---------------------------------------------------------------------------
# Setting read/write (this module owns the key)
# ---------------------------------------------------------------------------


async def test_set_channel_persists_int_as_str(monkeypatch):
    set_setting = AsyncMock()
    monkeypatch.setattr("utils.db.set_setting", set_setting)

    await announce.set_channel(guild_id=123, channel_id=456)

    set_setting.assert_awaited_once_with(
        123,
        BTD6_VERSION_ANNOUNCEMENT_CHANNEL,
        "456",
    )


async def test_clear_channel_writes_empty(monkeypatch):
    set_setting = AsyncMock()
    monkeypatch.setattr("utils.db.set_setting", set_setting)

    await announce.clear_channel(guild_id=123)

    set_setting.assert_awaited_once_with(123, BTD6_VERSION_ANNOUNCEMENT_CHANNEL, "")


def _patch_binding(monkeypatch, target_id=None):
    """Patch the version_announce_channel binding read (Q-0064 dual-read)."""
    monkeypatch.setattr(
        "core.runtime.bindings.get_binding",
        AsyncMock(return_value=MagicMock(target_id=target_id)),
    )


async def test_get_channel_id_reads_setting(monkeypatch):
    """KV fallback: with no binding bound, the legacy pointer answers."""
    _patch_binding(monkeypatch, target_id=None)
    monkeypatch.setattr("utils.db.get_setting", AsyncMock(return_value="789"))

    assert await announce.get_channel_id(guild_id=123) == "789"


# ---------------------------------------------------------------------------
# Binding-first precedence (Settings Phase 2, Q-0064)
# ---------------------------------------------------------------------------


async def test_get_channel_id_prefers_bound_binding(monkeypatch):
    """A bound version_announce_channel binding wins over the KV pointer."""
    _patch_binding(monkeypatch, target_id=555)
    kv = AsyncMock(return_value="789")
    monkeypatch.setattr("utils.db.get_setting", kv)

    assert await announce.get_channel_id(guild_id=123) == "555"
    kv.assert_not_awaited()  # the legacy lane was never consulted


async def test_binding_read_failure_degrades_to_kv(monkeypatch):
    """A broken binding read must not kill announcements — KV lane answers."""
    monkeypatch.setattr(
        "core.runtime.bindings.get_binding",
        AsyncMock(side_effect=RuntimeError("db down")),
    )
    monkeypatch.setattr("utils.db.get_setting", AsyncMock(return_value="789"))

    assert await announce.get_channel_id(guild_id=123) == "789"


async def test_resolve_channel_uses_bound_channel(monkeypatch):
    """The send path resolves the bound channel object directly."""
    import discord

    channel = MagicMock(spec=discord.TextChannel)
    guild = MagicMock()
    guild.id = 123
    guild.get_channel_or_thread = MagicMock(return_value=channel)
    _patch_binding(monkeypatch, target_id=555)

    assert await announce._resolve_channel(guild) is channel
    guild.get_channel_or_thread.assert_called_once_with(555)


async def test_resolve_channel_bound_but_missing_skips(monkeypatch):
    """A bound-but-deleted channel skips the announcement (loud log) rather
    than silently falling back to a stale KV pointer the operator replaced."""
    guild = MagicMock()
    guild.id = 123
    guild.get_channel_or_thread = MagicMock(return_value=None)
    _patch_binding(monkeypatch, target_id=555)

    assert await announce._resolve_channel(guild) is None


# ---------------------------------------------------------------------------
# Posting
# ---------------------------------------------------------------------------


async def test_announces_to_resolved_channel(monkeypatch):
    channel = MagicMock()
    channel.send = AsyncMock()
    monkeypatch.setattr(
        "services.btd6_version_announce._resolve_channel",
        AsyncMock(return_value=channel),
    )
    bot = MagicMock()
    bot.guilds = [MagicMock()]
    announce.setup(bot)

    await announce._on_version_detected(
        version="54.0",
        previous_version="53.0",
        title="Bloons TD 6 - Update 54.0",
        url="https://store.steampowered.com/news/app/960090/view/2",
    )

    channel.send.assert_awaited_once()
    embed = channel.send.await_args.kwargs["embed"]
    assert "54.0" in embed.title
    # Both versions surfaced in the embed fields.
    field_values = [f.value for f in embed.fields]
    assert any("53.0" in v for v in field_values)
    assert any("54.0" in v for v in field_values)


async def test_skips_guild_without_configured_channel(monkeypatch):
    monkeypatch.setattr(
        "services.btd6_version_announce._resolve_channel",
        AsyncMock(return_value=None),
    )
    bot = MagicMock()
    bot.guilds = [MagicMock(), MagicMock()]
    announce.setup(bot)

    # Must not raise even though no channel resolves anywhere.
    await announce._on_version_detected(version="54.0")


async def test_noop_when_bot_unset():
    # setup() never called -> _BOT is None -> handler returns quietly.
    await announce._on_version_detected(version="54.0")


async def test_blank_version_is_ignored(monkeypatch):
    resolve = AsyncMock()
    monkeypatch.setattr("services.btd6_version_announce._resolve_channel", resolve)
    bot = MagicMock()
    bot.guilds = [MagicMock()]
    announce.setup(bot)

    await announce._on_version_detected(version="   ")

    resolve.assert_not_called()


async def test_resolve_channel_filters_non_text(monkeypatch):
    # resolve_settings_channel returns something that isn't a TextChannel/Thread
    # (e.g. a category) -> _resolve_channel rejects it.
    _patch_binding(monkeypatch, target_id=None)  # unbound → KV path
    monkeypatch.setattr(
        "core.runtime.guild_resources.resolve_settings_channel",
        AsyncMock(return_value=MagicMock()),
    )
    assert await announce._resolve_channel(MagicMock()) is None


# ---------------------------------------------------------------------------
# Subscription
# ---------------------------------------------------------------------------


def test_setup_is_idempotent(monkeypatch):
    from core.events import bus

    on = MagicMock()
    monkeypatch.setattr(bus, "on", on)
    announce.setup(MagicMock())
    announce.setup(MagicMock())  # second call must not re-subscribe

    on.assert_called_once()
