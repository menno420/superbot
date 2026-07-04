"""Tests for the author-sweep + apply helpers in services.history_cleanup.

``build_author_cleanup_plan`` plans a post-moderation sweep of one member's
recent messages; ``apply_history_cleanup_plan`` is the single deletion path
shared by ``!cleanuphistory`` and the moderation post-action sweep
(server-management PR10).
"""

from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest

from services.history_cleanup import (
    CleanupApplyResult,
    HistoryCleanupPlan,
    apply_history_cleanup_plan,
    build_author_cleanup_plan,
    build_history_cleanup_plan,
)


def _make_msg(msg_id: int, author_id: int) -> MagicMock:
    msg = MagicMock()
    msg.id = msg_id
    msg.author = MagicMock()
    msg.author.id = author_id
    msg.delete = AsyncMock()
    return msg


def _content_msg(
    msg_id: int,
    *,
    content: str = "",
    embeds: list | None = None,
    attachments: list | None = None,
    bot: bool = False,
    created_at: dt.datetime | None = None,
) -> MagicMock:
    """A message for content-type/age tests (`build_history_cleanup_plan`)."""
    msg = MagicMock()
    msg.id = msg_id
    msg.content = content
    msg.embeds = embeds or []
    msg.attachments = attachments or []
    msg.author = MagicMock()
    msg.author.bot = bot
    msg.created_at = created_at or dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
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


# ---------------------------------------------------------------------------
# build_history_cleanup_plan — content-type modes (punch-list #2)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_embeds_mode_matches_only_messages_with_embeds():
    with_embed = _content_msg(1, embeds=[MagicMock()])
    plain = _content_msg(2, content="hi")
    plan = await build_history_cleanup_plan(
        _make_channel([with_embed, plain]),
        limit=50,
        mode="embeds",
    )
    assert [m.id for m in plan.matched] == [1]


@pytest.mark.asyncio
async def test_links_mode_matches_only_messages_with_urls():
    link = _content_msg(1, content="see https://example.com/x for more")
    no_link = _content_msg(2, content="no url here")
    plan = await build_history_cleanup_plan(
        _make_channel([link, no_link]),
        limit=50,
        mode="links",
    )
    assert [m.id for m in plan.matched] == [1]


@pytest.mark.asyncio
async def test_attachments_mode_matches_only_messages_with_attachments():
    with_file = _content_msg(1, attachments=[MagicMock()])
    plain = _content_msg(2, content="text")
    plan = await build_history_cleanup_plan(
        _make_channel([with_file, plain]),
        limit=50,
        mode="attachments",
    )
    assert [m.id for m in plan.matched] == [1]


@pytest.mark.asyncio
async def test_content_modes_skip_bot_messages():
    bot_embed = _content_msg(1, embeds=[MagicMock()], bot=True)
    user_embed = _content_msg(2, embeds=[MagicMock()])
    plan = await build_history_cleanup_plan(
        _make_channel([bot_embed, user_embed]),
        limit=50,
        mode="embeds",
    )
    assert [m.id for m in plan.matched] == [2]


@pytest.mark.asyncio
async def test_unsupported_mode_raises():
    with pytest.raises(ValueError, match="Unsupported cleanuphistory mode"):
        await build_history_cleanup_plan(
            _make_channel([]),
            limit=10,
            mode="nope",  # type: ignore[arg-type]
        )


# ---------------------------------------------------------------------------
# build_history_cleanup_plan — age gate (punch-list #3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_older_than_gate_keeps_only_old_messages():
    cutoff = dt.datetime(2026, 6, 1, tzinfo=dt.timezone.utc)
    old = _content_msg(
        1,
        content="https://x.test",
        created_at=dt.datetime(2026, 5, 1, tzinfo=dt.timezone.utc),
    )
    recent = _content_msg(
        2,
        content="https://y.test",
        created_at=dt.datetime(2026, 6, 15, tzinfo=dt.timezone.utc),
    )
    plan = await build_history_cleanup_plan(
        _make_channel([recent, old]),
        limit=50,
        mode="links",
        older_than=cutoff,
    )
    assert [m.id for m in plan.matched] == [1]


@pytest.mark.asyncio
async def test_older_than_gate_composes_with_spam_mode():
    cutoff = dt.datetime(2026, 6, 10, tzinfo=dt.timezone.utc)
    # Two duplicate-content pairs; only the old pair's later message should
    # match once the age gate is applied.
    base_old = dt.datetime(2026, 5, 1, tzinfo=dt.timezone.utc)
    base_new = dt.datetime(2026, 6, 20, tzinfo=dt.timezone.utc)
    old_a = _content_msg(1, content="spam", created_at=base_old)
    old_b = _content_msg(2, content="spam", created_at=base_old + dt.timedelta(seconds=3))
    new_a = _content_msg(3, content="ping", created_at=base_new)
    new_b = _content_msg(4, content="ping", created_at=base_new + dt.timedelta(seconds=3))
    # history() yields newest→oldest
    plan = await build_history_cleanup_plan(
        _make_channel([new_b, new_a, old_b, old_a]),
        limit=50,
        mode="spam",
        spam_duplicate_window_seconds=15,
        older_than=cutoff,
    )
    assert [m.id for m in plan.matched] == [2]
