"""End-to-end integration of the counters chain (completion punch #5).

Where ``test_counter_service`` mocks ``load_policy`` with a hand-built
``CounterPolicy``, this exercises the *real* chain:

    stored settings  →  counter_config.load_policy (real)
                     →  counter_service.sync_guild (real)
                     →  counters.updated event

The stored-settings dict stands in for the legacy KV table; applying a preset's
``preset_setting_writes`` into it is the offline analogue of the
``SettingsMutationPipeline`` write the ``!counterpreset`` command performs, so
this covers "settings-mutation → loop sync → event" with a real policy object.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from services import counter_config, counter_service


def _guild(member_count: int, members: list) -> MagicMock:
    g = MagicMock(spec=discord.Guild)
    g.id = 1
    g.member_count = member_count
    g.members = members
    g.get_channel.return_value = None
    return g


def _voice(name: str) -> MagicMock:
    ch = MagicMock(spec=discord.VoiceChannel)
    ch.name = name
    ch.edit = AsyncMock()
    return ch


@pytest.mark.asyncio
async def test_preset_apply_then_sync_renames_and_emits(monkeypatch):
    members = [MagicMock(bot=False), MagicMock(bot=False), MagicMock(bot=True)]
    guild = _guild(member_count=3, members=members)

    total_ch = _voice("voice-total")
    humans_ch = _voice("voice-humans")
    bots_ch = _voice("voice-bots")
    channels = {100: total_ch, 200: humans_ch, 300: bots_ch}
    guild.get_channel.side_effect = lambda cid: channels.get(cid)

    # Stored settings = the legacy KV table.  Master on + three bound channels.
    stored: dict[str, object] = {
        "enabled": True,
        "total_channel": "100",
        "humans_channel": "200",
        "bots_channel": "300",
    }

    # Apply the "minimal" preset the same way !counterpreset does — through the
    # template SettingSpec names — but into the stored dict (offline analogue).
    preset = counter_config.get_preset("minimal")
    assert preset is not None
    for setting_name, template in counter_config.preset_setting_writes(preset):
        # SettingSpec name is e.g. "total_template"; load_policy resolves the
        # same name, so write under it directly.
        stored[setting_name] = template

    async def fake_resolve(guild_id, subsystem, name, fallback):
        assert subsystem == counter_config.SUBSYSTEM
        return stored.get(name, fallback)

    import services.settings_resolution as sr

    monkeypatch.setattr(sr, "resolve_value", fake_resolve)

    import core.events

    emit = AsyncMock()
    monkeypatch.setattr(core.events.bus, "emit", emit)

    # Real load_policy + real sync_guild.
    renamed = await counter_service.sync_guild(guild)

    assert renamed == 3
    assert total_ch.edit.await_args.kwargs["name"] == "Members: 3"
    assert humans_ch.edit.await_args.kwargs["name"] == "Humans: 2"
    assert bots_ch.edit.await_args.kwargs["name"] == "Bots: 1"

    emit.assert_awaited_once()
    assert emit.await_args.args[0] == counter_service.EVT_COUNTERS_UPDATED
    assert emit.await_args.kwargs["renamed"] == 3


@pytest.mark.asyncio
async def test_master_off_syncs_nothing_end_to_end(monkeypatch):
    guild = _guild(member_count=3, members=[])
    channel = _voice("voice-total")
    guild.get_channel.side_effect = lambda cid: channel

    stored = {"enabled": False, "total_channel": "100"}

    async def fake_resolve(guild_id, subsystem, name, fallback):
        return stored.get(name, fallback)

    import services.settings_resolution as sr

    monkeypatch.setattr(sr, "resolve_value", fake_resolve)
    import core.events

    emit = AsyncMock()
    monkeypatch.setattr(core.events.bus, "emit", emit)

    renamed = await counter_service.sync_guild(guild)
    assert renamed == 0
    channel.edit.assert_not_called()
    emit.assert_not_called()
