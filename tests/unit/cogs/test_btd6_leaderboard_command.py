"""``/btd6 leaderboard`` builder + prefix/slash plumbing.

Covers happy paths, empty-state hints (must point at parent chains,
never child sources), invalid kinds, and the newest-active-event
fallback when ``event_id`` is omitted.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from cogs.btd6._builders import build_leaderboard_embed
from services.btd6_live_query_service import (
    ActiveEventHeadline,
    LeaderboardRow,
)


def _row(rank: int, name: str = "alice", score: int = 100) -> LeaderboardRow:
    return LeaderboardRow(
        rank=rank,
        display_name=name,
        score=score,
        score_parts=None,
        submission_time_ms=1700000000000,
        profile_url=None,
    )


def _active(entity_key: str, name: str = "Reversed Loop") -> ActiveEventHeadline:
    return ActiveEventHeadline(
        entity_kind="btd6_race",
        entity_key=entity_key,
        name=name,
        start_ms=None,
        end_ms=None,
        fetched_at=datetime.now(tz=timezone.utc),
    )


@pytest.mark.asyncio
async def test_invalid_kind_returns_error_embed():
    embed = await build_leaderboard_embed("not-a-kind", None)
    assert isinstance(embed, discord.Embed)
    assert embed.color == discord.Color.red()
    assert "Unknown kind" in (embed.description or "")


@pytest.mark.asyncio
async def test_race_no_active_event_shows_refresh_hint(monkeypatch):
    from services import btd6_live_query_service as live

    async def _none():
        return None

    monkeypatch.setattr(live, "get_newest_active_race", _none)

    embed = await build_leaderboard_embed("race", None)
    desc = embed.description or ""
    assert "No active race" in desc
    # Hint MUST point at the parent chain, not the leaderboard child.
    assert "refresh-source nk_btd6_races" in desc
    assert "nk_btd6_races_leaderboard" not in desc


@pytest.mark.asyncio
async def test_boss_no_active_event_shows_refresh_hint(monkeypatch):
    from services import btd6_live_query_service as live

    async def _none():
        return None

    monkeypatch.setattr(live, "get_newest_active_boss", _none)

    embed = await build_leaderboard_embed("boss", None)
    desc = embed.description or ""
    assert "No active boss" in desc
    assert "refresh-source nk_btd6_bosses" in desc
    assert "nk_btd6_bosses_leaderboard" not in desc


@pytest.mark.asyncio
async def test_empty_race_leaderboard_hints_at_parent_chain(monkeypatch):
    from services import btd6_live_query_service as live

    async def _active_race():
        return _active("RaceA_abc")

    async def _empty(*args, **kwargs):
        return ()

    monkeypatch.setattr(live, "get_newest_active_race", _active_race)
    monkeypatch.setattr(live, "get_race_leaderboard", _empty)

    embed = await build_leaderboard_embed("race", None)
    desc = embed.description or ""
    assert "refresh-source nk_btd6_races" in desc
    assert "nk_btd6_races_leaderboard" not in desc


@pytest.mark.asyncio
async def test_empty_boss_leaderboard_hints_at_parent_chain(monkeypatch):
    from services import btd6_live_query_service as live

    async def _active_boss():
        return ActiveEventHeadline(
            entity_kind="btd6_boss",
            entity_key="Boss1",
            name="Diamondback",
            start_ms=None,
            end_ms=None,
            fetched_at=datetime.now(tz=timezone.utc),
        )

    async def _empty(*args, **kwargs):
        return ()

    monkeypatch.setattr(live, "get_newest_active_boss", _active_boss)
    monkeypatch.setattr(live, "get_boss_leaderboard", _empty)

    embed = await build_leaderboard_embed("boss", None)
    desc = embed.description or ""
    assert "refresh-source nk_btd6_bosses" in desc
    assert "nk_btd6_bosses_leaderboard" not in desc


@pytest.mark.asyncio
async def test_race_happy_path_renders_ranks_in_order(monkeypatch):
    from services import btd6_live_query_service as live

    async def _active_race():
        return _active("R1", name="Cool Race")

    async def _lb(race_id, *, limit=10):
        # Facade contract: rows already sorted by rank ASC.
        return (_row(1, "alice"), _row(2, "bob"), _row(3, "carol"))

    monkeypatch.setattr(live, "get_newest_active_race", _active_race)
    monkeypatch.setattr(live, "get_race_leaderboard", _lb)

    embed = await build_leaderboard_embed("race", None)
    assert "Cool Race" in (embed.title or "")
    desc = embed.description or ""
    assert "alice" in desc
    assert "bob" in desc
    # Renders in rank order
    assert desc.index("alice") < desc.index("bob") < desc.index("carol")


@pytest.mark.asyncio
async def test_boss_happy_path_shows_standard_solo_hint(monkeypatch):
    from services import btd6_live_query_service as live

    async def _active_boss():
        return ActiveEventHeadline(
            entity_kind="btd6_boss",
            entity_key="Boss1",
            name="Diamondback",
            start_ms=None,
            end_ms=None,
            fetched_at=datetime.now(tz=timezone.utc),
        )

    async def _lb(boss_id, *, score_type="standard", team_size=1, limit=10):
        return (_row(1, "alice"),)

    monkeypatch.setattr(live, "get_newest_active_boss", _active_boss)
    monkeypatch.setattr(live, "get_boss_leaderboard", _lb)

    embed = await build_leaderboard_embed("boss", None)
    footer_text = embed.footer.text or "" if embed.footer else ""
    assert "standard solo" in footer_text
    assert "Elite" in footer_text
    # Page-1 leaderboard coverage caveat is always surfaced on populated boards.
    assert "top page only" in footer_text


@pytest.mark.asyncio
async def test_explicit_event_id_skips_active_resolution(monkeypatch):
    from services import btd6_live_query_service as live

    async def _active_race():
        raise AssertionError("must not be called when event_id given")

    async def _lb(race_id, *, limit=10):
        assert race_id == "explicit_race_id"
        return (_row(1, "alice"),)

    monkeypatch.setattr(live, "get_newest_active_race", _active_race)
    monkeypatch.setattr(live, "get_race_leaderboard", _lb)

    embed = await build_leaderboard_embed("race", "explicit_race_id")
    assert "explicit_race_id" in (embed.title or "")


@pytest.mark.asyncio
async def test_race_leaderboard_footer_shows_page1_coverage(monkeypatch):
    from services import btd6_live_query_service as live

    async def _active_race():
        return _active("R9", name="Edge Loop")

    async def _lb(race_id, *, limit=10):
        return (_row(1, "alice"),)

    monkeypatch.setattr(live, "get_newest_active_race", _active_race)
    monkeypatch.setattr(live, "get_race_leaderboard", _lb)

    embed = await build_leaderboard_embed("race", None)
    footer_text = embed.footer.text or "" if embed.footer else ""
    # Race leaderboards have no boss hint, but still surface page-1 coverage.
    assert "top page only" in footer_text
