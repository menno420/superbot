"""Tests for the server_scan setup section.

Covers:

* The section calls ``services.guild_snapshot.collect`` and caches
  the result on the hub view for sibling sections.
* It surfaces an error message (and does not crash) when collect()
  raises.
* It rejects DM context.
* The hub-cache helpers round-trip.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from services.guild_snapshot import GuildSnapshot
from views.setup.sections import server_scan


class _FakeGuild:
    def __init__(self, guild_id: int = 1):
        self.id = guild_id
        self.name = "Test Guild"
        self.owner_id = 99


class _FakeMember:
    def __init__(self, guild: _FakeGuild | None = None):
        self.id = 7
        self.guild = guild or _FakeGuild()


class _FakeResponse:
    def __init__(self):
        self.sent: list[dict] = []

    async def send_message(self, *args, embed=None, ephemeral=False, **kwargs):
        content = args[0] if args else kwargs.get("content")
        self.sent.append({"content": content, "embed": embed, "ephemeral": ephemeral})


class _FakeInteraction:
    def __init__(self, guild: _FakeGuild | None = None):
        self.guild = guild
        self.user = _FakeMember(guild=guild)
        self.response = _FakeResponse()


class _FakeHubView:
    """Bare cache target — server_scan.set_cached_snapshot uses setattr."""

    pass


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def test_cache_round_trip():
    hub = _FakeHubView()
    snap = GuildSnapshot(guild_id=1, guild_name="x", owner_id=0)
    assert server_scan.get_cached_snapshot(hub) is None
    server_scan.set_cached_snapshot(hub, snap)
    assert server_scan.get_cached_snapshot(hub) is snap


def test_cache_returns_none_when_unset():
    hub = _FakeHubView()
    assert server_scan.get_cached_snapshot(hub) is None


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_collects_snapshot_caches_and_sends_embed():
    guild = _FakeGuild()
    interaction = _FakeInteraction(guild=guild)
    hub = _FakeHubView()
    snap = GuildSnapshot(guild_id=guild.id, guild_name=guild.name, owner_id=99)

    with (
        patch(
            "views.setup.sections.server_scan.collect",
            new=AsyncMock(return_value=snap),
        ) as collect_mock,
        patch(
            "services.setup_session.mark_in_progress",
            new=AsyncMock(),
        ),
    ):
        await server_scan.run(interaction, hub)

    collect_mock.assert_awaited_once_with(guild)
    assert server_scan.get_cached_snapshot(hub) is snap
    sent = interaction.response.sent[0]
    assert sent["ephemeral"] is True
    assert sent["embed"] is not None
    assert "Test Guild" in sent["embed"].title


@pytest.mark.asyncio
async def test_run_rejects_dm_context():
    interaction = _FakeInteraction(guild=None)
    hub = _FakeHubView()

    with patch(
        "views.setup.sections.server_scan.collect",
        new=AsyncMock(),
    ) as collect_mock:
        await server_scan.run(interaction, hub)

    collect_mock.assert_not_awaited()
    assert any(
        "guild" in (s["content"] or "").lower()
        for s in interaction.response.sent
    )


@pytest.mark.asyncio
async def test_run_surfaces_collect_failure_gracefully():
    guild = _FakeGuild()
    interaction = _FakeInteraction(guild=guild)
    hub = _FakeHubView()

    with (
        patch(
            "views.setup.sections.server_scan.collect",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new=AsyncMock(),
        ),
    ):
        await server_scan.run(interaction, hub)

    # No snapshot cached on failure.
    assert server_scan.get_cached_snapshot(hub) is None
    # Operator gets an ephemeral failure message.
    last = interaction.response.sent[-1]
    assert "fail" in (last["content"] or "").lower()


@pytest.mark.asyncio
async def test_run_marks_setup_session_in_progress():
    guild = _FakeGuild()
    interaction = _FakeInteraction(guild=guild)
    hub = _FakeHubView()
    snap = GuildSnapshot(guild_id=guild.id, guild_name=guild.name, owner_id=99)

    with (
        patch(
            "views.setup.sections.server_scan.collect",
            new=AsyncMock(return_value=snap),
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new=AsyncMock(),
        ) as mark_mock,
    ):
        await server_scan.run(interaction, hub)

    mark_mock.assert_awaited_once_with(guild.id, step="server_scan")


@pytest.mark.asyncio
async def test_run_tolerates_mark_in_progress_failure():
    """A logging-only failure to record progress must not propagate."""
    guild = _FakeGuild()
    interaction = _FakeInteraction(guild=guild)
    hub = _FakeHubView()
    snap = GuildSnapshot(guild_id=guild.id, guild_name=guild.name, owner_id=99)

    with (
        patch(
            "views.setup.sections.server_scan.collect",
            new=AsyncMock(return_value=snap),
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new=AsyncMock(side_effect=RuntimeError("session DB down")),
        ),
    ):
        await server_scan.run(interaction, hub)

    # Snapshot still cached; embed still sent.
    assert server_scan.get_cached_snapshot(hub) is snap
    assert any(s["embed"] is not None for s in interaction.response.sent)


def test_section_is_registered_with_expected_slug_and_order():
    from services.setup_sections import REGISTRY

    section = REGISTRY.get("server_scan")
    assert section is not None
    assert section.label == "Scan server"
    assert section.order == 5  # before readiness (order=10)
    assert section.emoji == "🛰"
