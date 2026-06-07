"""Tests for the author-sweep + apply helpers in services.history_cleanup.

``build_author_cleanup_plan`` plans a post-moderation sweep of one member's
recent messages; ``apply_history_cleanup_plan`` is the single deletion path
shared by ``!cleanuphistory`` and the moderation post-action sweep
(server-management PR10).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from services.history_cleanup import (
    CleanupApplyResult,
    HistoryCleanupPlan,
    apply_history_cleanup_plan,
    build_author_cleanup_plan,
)


def _make_msg(msg_id: int, author_id: int) -> MagicMock:
    msg = MagicMock()
    msg.id = msg_id
    msg.author = MagicMock()
    msg.author.id = author_id
    msg.delete = AsyncMock()
    return msg


def _make_channel(messages: list) -> MagicMock:
    channel = MagicMock()

    async def _history(*, limit):
        for m in messages[:limit]:
            yield m

    channel.history = _history
    return channel


# ---------------------------------------------------------------------------
# build_author_cleanup_plan
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_build_author_plan_matches_only_target():
    target = 100
    messages = [
        _make_msg(1, target),
        _make_msg(2, 999),
        _make_msg(3, target),
        _make_msg(4, 999),
    ]
    plan = await build_author_cleanup_plan(
        _make_channel(messages),
        author_id=target,
        limit=50,
    )
    assert plan.scanned == 4
    assert [m.id for m in plan.matched] == [1, 3]


@pytest.mark.asyncio
async def test_build_author_plan_respects_scan_limit():
    target = 7
    messages = [_make_msg(i, target) for i in range(10)]
    plan = await build_author_cleanup_plan(
        _make_channel(messages),
        author_id=target,
        limit=3,
    )
    assert plan.scanned == 3
    assert len(plan.matched) == 3


@pytest.mark.asyncio
async def test_build_author_plan_excludes_ids():
    target = 5
    messages = [_make_msg(1, target), _make_msg(2, target)]
    plan = await build_author_cleanup_plan(
        _make_channel(messages),
        author_id=target,
        limit=50,
        exclude_message_ids={1},
    )
    assert [m.id for m in plan.matched] == [2]


@pytest.mark.asyncio
async def test_build_author_plan_no_match_returns_empty():
    plan = await build_author_cleanup_plan(
        _make_channel([_make_msg(1, 1), _make_msg(2, 2)]),
        author_id=999,
        limit=50,
    )
    assert plan.scanned == 2
    assert plan.matched == []


# ---------------------------------------------------------------------------
# apply_history_cleanup_plan
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_deletes_all_matched():
    msgs = [_make_msg(1, 1), _make_msg(2, 1)]
    result = await apply_history_cleanup_plan(
        HistoryCleanupPlan(scanned=2, matched=msgs),
    )
    assert result == CleanupApplyResult(deleted=2, failed=0)
    for m in msgs:
        m.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_counts_forbidden_and_gone_as_failures():
    ok = _make_msg(1, 1)
    forbidden = _make_msg(2, 1)
    forbidden.delete.side_effect = discord.Forbidden(MagicMock(), "no perms")
    gone = _make_msg(3, 1)
    # NotFound is an HTTPException subclass — counted as failed (mirrors the
    # pre-extraction !cleanuphistory loop, which only deleted/failed-counted).
    gone.delete.side_effect = discord.NotFound(MagicMock(), "already gone")
    result = await apply_history_cleanup_plan(
        HistoryCleanupPlan(scanned=3, matched=[ok, forbidden, gone]),
    )
    assert result.deleted == 1
    assert result.failed == 2


@pytest.mark.asyncio
async def test_apply_empty_plan_is_noop():
    result = await apply_history_cleanup_plan(
        HistoryCleanupPlan(scanned=10, matched=[]),
    )
    assert result == CleanupApplyResult(deleted=0, failed=0)
