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


async def test_get_channel_id_reads_setting(monkeypatch):
    monkeypatch.setattr("utils.db.get_setting", AsyncMock(return_value="789"))

    assert await announce.get_channel_id(guild_id=123) == "789"


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
