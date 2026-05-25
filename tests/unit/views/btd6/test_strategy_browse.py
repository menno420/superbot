"""PR-F tests for the strategy memory UX renderers + service layer."""

from __future__ import annotations

from datetime import datetime, timezone

import discord
import pytest

from services import btd6_strategy_service
from views.btd6.strategy_browse import (
    build_audit_embed,
    build_browse_embed,
    build_detail_embed,
    build_mine_embed,
)


def _row(
    sid: int,
    *,
    title: str,
    visibility: str = "guild",
    approval_status: str = "draft",
    approved_by: str | None = None,
    origin_guild_id: int = 100,
    current_guild_id: int = 100,
    submitted_by: int = 555,
    summary: str = "summary text",
    version: int = 1,
):
    return {
        "id": sid,
        "title": title,
        "summary": summary,
        "visibility": visibility,
        "approval_status": approval_status,
        "approved_by": approved_by,
        "origin_guild_id": origin_guild_id,
        "current_guild_id": current_guild_id,
        "submitted_by": submitted_by,
        "version": version,
        "map": "Bloody Puddles",
        "mode": "CHIMPS",
        "difficulty": None,
        "hero": None,
        "towers": ["Super Monkey"],
        "steps": ["Step 1"],
    }


# ---------------------------------------------------------------------------
# Service layer
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_mine_filters_to_submitter(monkeypatch):
    async def _search(*, guild_id, limit):
        return [
            _row(1, title="mine", submitted_by=555),
            _row(2, title="others", submitted_by=999),
            _row(3, title="mine2", submitted_by=555),
        ]

    monkeypatch.setattr(
        "utils.db.btd6_strategies.search_strategies",
        _search,
    )

    out = await btd6_strategy_service.list_mine(100, submitter_id=555, limit=10)
    assert {r["title"] for r in out} == {"mine", "mine2"}


@pytest.mark.asyncio
async def test_list_clamp_caps_huge_limit(monkeypatch):
    captured = {}

    async def _search(*, guild_id=None, visibility=None, limit, **_kw):
        captured["limit"] = limit
        return []

    monkeypatch.setattr(
        "utils.db.btd6_strategies.search_strategies",
        _search,
    )

    await btd6_strategy_service.list_for_guild(1, limit=999_999)
    assert captured["limit"] == btd6_strategy_service._MAX_LIMIT


# ---------------------------------------------------------------------------
# Browse / mine
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_browse_embed_lists_published_only(monkeypatch):
    async def _list(*, limit):
        return [
            _row(1, title="published one", visibility="published"),
            _row(2, title="published two", visibility="published"),
        ]

    monkeypatch.setattr(btd6_strategy_service, "list_published", _list)

    embed = await build_browse_embed()
    blob = "\n".join(f.name + " " + f.value for f in embed.fields)
    assert "published one" in blob
    assert "published two" in blob


@pytest.mark.asyncio
async def test_browse_embed_empty_message(monkeypatch):
    async def _list(*, limit):
        return []

    monkeypatch.setattr(btd6_strategy_service, "list_published", _list)

    embed = await build_browse_embed()
    assert "No published" in (embed.description or "")


@pytest.mark.asyncio
async def test_mine_embed(monkeypatch):
    async def _mine(guild_id, submitter_id, *, limit):
        return [_row(7, title="my draft", submitted_by=submitter_id)]

    monkeypatch.setattr(btd6_strategy_service, "list_mine", _mine)

    embed = await build_mine_embed(100, 555)
    blob = "\n".join(f.value for f in embed.fields)
    assert "my draft" in blob


# ---------------------------------------------------------------------------
# Detail: cross-guild visibility
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_detail_published_visible_anywhere(monkeypatch):
    async def _get(_sid):
        return _row(5, title="public", visibility="published", origin_guild_id=10)

    monkeypatch.setattr(btd6_strategy_service, "get", _get)

    embed = await build_detail_embed(5, viewer_guild_id=999)
    assert isinstance(embed, discord.Embed)
    assert "public" in (embed.title or "")


@pytest.mark.asyncio
async def test_detail_guild_local_hidden_from_other_guild(monkeypatch):
    async def _get(_sid):
        return _row(
            5,
            title="secret",
            visibility="guild",
            origin_guild_id=10,
            current_guild_id=10,
        )

    monkeypatch.setattr(btd6_strategy_service, "get", _get)

    out = await build_detail_embed(5, viewer_guild_id=999)
    assert isinstance(out, str)
    assert "not visible" in out


@pytest.mark.asyncio
async def test_detail_guild_local_visible_to_origin(monkeypatch):
    async def _get(_sid):
        return _row(
            5,
            title="secret",
            visibility="guild",
            origin_guild_id=10,
            current_guild_id=10,
        )

    monkeypatch.setattr(btd6_strategy_service, "get", _get)

    embed = await build_detail_embed(5, viewer_guild_id=10)
    assert isinstance(embed, discord.Embed)


@pytest.mark.asyncio
async def test_detail_missing_strategy(monkeypatch):
    async def _get(_sid):
        return None

    monkeypatch.setattr(btd6_strategy_service, "get", _get)

    out = await build_detail_embed(404, viewer_guild_id=1)
    assert isinstance(out, str)
    assert "not found" in out


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_audit_embed_renders_each_row(monkeypatch):
    async def _audit(_sid):
        now = datetime.now(tz=timezone.utc)
        return [
            {
                "action": "submitted",
                "actor_kind": "user",
                "actor_id": 555,
                "created_at": now,
            },
            {
                "action": "ai_approved",
                "actor_kind": "ai",
                "actor_id": None,
                "created_at": now,
            },
        ]

    monkeypatch.setattr(btd6_strategy_service, "audit_for", _audit)

    embed = await build_audit_embed(7)
    names = {f.name for f in embed.fields}
    assert any("submitted" in n for n in names)
    assert any("ai_approved" in n for n in names)


@pytest.mark.asyncio
async def test_audit_embed_empty(monkeypatch):
    async def _audit(_sid):
        return []

    monkeypatch.setattr(btd6_strategy_service, "audit_for", _audit)

    embed = await build_audit_embed(7)
    assert "No audit rows" in (embed.description or "")
