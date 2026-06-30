from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.cleanup_cog import MAX_CLEANUP_HISTORY_LIMIT, Cleanup

# ruff: noqa: S101


def _msg(content: str):
    m = MagicMock()
    m.content = content
    m.author = SimpleNamespace(bot=False)
    m.delete = AsyncMock()
    return m


def _ctx(messages):
    ctx = MagicMock()
    me = SimpleNamespace()
    ctx.guild = SimpleNamespace(id=1, me=me)
    ctx.channel = MagicMock()

    async def _history(limit=100):
        for m in messages[:limit]:
            yield m

    ctx.channel.history = _history
    ctx.channel.permissions_for = MagicMock(
        return_value=SimpleNamespace(manage_messages=True),
    )
    ctx.channel.name = "general"
    ctx.channel.id = 9
    ctx.author = SimpleNamespace(id=42)
    ctx.message = MagicMock()
    ctx.message.id = 999
    ctx.message.delete = AsyncMock()
    ctx.send = AsyncMock()
    return ctx


def _reply():
    m = MagicMock()
    m.delete = AsyncMock()
    return m


def _confirmed_reaction():
    return SimpleNamespace(emoji="✅", message=SimpleNamespace(id=100))


@pytest.mark.asyncio
async def test_cleanuphistory_keyword_mode_deletes_only_matching_message():
    cog = Cleanup(MagicMock())
    match = _msg("hello bad")
    other = _msg("clean")
    ctx = _ctx([match, other])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, _reply()]
    with (
        patch(
            "cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[]),
        ),
        patch.object(
            cog.bot,
            "wait_for",
            new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author)),
        ),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="keyword bad")
    match.delete.assert_awaited_once()
    other.delete.assert_not_called()
    ctx.message.delete.assert_awaited()


@pytest.mark.asyncio
async def test_cleanuphistory_backward_compat_keyword():
    cog = Cleanup(MagicMock())
    match = _msg("contains legacyword")
    ctx = _ctx([match])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, _reply()]
    with (
        patch(
            "cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[]),
        ),
        patch.object(
            cog.bot,
            "wait_for",
            new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author)),
        ),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="legacyword")
    match.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_cleanuphistory_commands_mode_deletes_prefixed_messages():
    cog = Cleanup(MagicMock())
    cmd = _msg("   !help me")
    normal = _msg("hello world")
    invocation = _msg("!cleanuphistory 10 commands")
    invocation.id = 999
    ctx = _ctx([invocation, cmd, normal])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, _reply()]
    with (
        patch(
            "cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[]),
        ),
        patch.object(
            cog.bot,
            "wait_for",
            new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author)),
        ),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="commands")
    cmd.delete.assert_awaited_once()
    normal.delete.assert_not_called()
    invocation.delete.assert_not_called()


@pytest.mark.asyncio
async def test_cleanuphistory_prohibited_mode_uses_word_boundary():
    cog = Cleanup(MagicMock())
    exact = _msg("this has badword here")
    partial = _msg("this has badwording")
    ctx = _ctx([exact, partial])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, _reply()]
    with (
        patch(
            "cogs.cleanup_cog.db.get_prohibited_words",
            new=AsyncMock(return_value=["badword"]),
        ),
        patch.object(
            cog.bot,
            "wait_for",
            new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author)),
        ),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="prohibited")
    exact.delete.assert_awaited_once()
    partial.delete.assert_not_called()


@pytest.mark.asyncio
async def test_cleanuphistory_zero_match_skips_confirmation():
    cog = Cleanup(MagicMock())
    ctx = _ctx([_msg("hello world")])
    with patch(
        "cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[]),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="keyword missing")
    first_msg = ctx.send.await_args_list[0].args[0]
    assert "Matched 0" in first_msg


@pytest.mark.asyncio
async def test_cleanuphistory_no_filter_defaults_to_prohibited():
    cog = Cleanup(MagicMock())
    exact = _msg("contains badword")
    ctx = _ctx([exact])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, _reply()]
    with (
        patch(
            "cogs.cleanup_cog.db.get_prohibited_words",
            new=AsyncMock(return_value=["badword"]),
        ),
        patch.object(
            cog.bot,
            "wait_for",
            new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author)),
        ),
    ):
        await cog.cleanup_history.callback(cog, ctx, 100, keyword=None)
    exact.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_cleanuphistory_cancel_confirmation_deletes_nothing():
    cog = Cleanup(MagicMock())
    match = _msg("keyword hit")
    ctx = _ctx([match])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, _reply()]
    reaction = SimpleNamespace(emoji="❌", message=SimpleNamespace(id=100))
    with (
        patch(
            "cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[]),
        ),
        patch.object(
            cog.bot, "wait_for", new=AsyncMock(return_value=(reaction, ctx.author)),
        ),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="keyword keyword")
    match.delete.assert_not_called()


@pytest.mark.asyncio
async def test_cleanuphistory_delete_failure_is_counted():
    cog = Cleanup(MagicMock())
    match = _msg("keyword hit")
    resp = MagicMock(status=500)
    resp.reason = "oops"
    match.delete.side_effect = discord.HTTPException(resp, "boom")
    ctx = _ctx([match])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    status_msg = _reply()
    ctx.send.side_effect = [confirm, status_msg]
    with (
        patch(
            "cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[]),
        ),
        patch.object(
            cog.bot,
            "wait_for",
            new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author)),
        ),
    ):
        await cog.cleanup_history.callback(cog, ctx, 10, keyword="keyword keyword")
    completion = ctx.send.await_args_list[-1].args[0]
    assert "failed 1" in completion


@pytest.mark.asyncio
async def test_cleanuphistory_limit_above_max_is_clamped():
    cog = Cleanup(MagicMock())
    ctx = _ctx([_msg("badword")])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [_reply(), confirm, _reply()]
    with (
        patch(
            "cogs.cleanup_cog.db.get_prohibited_words",
            new=AsyncMock(return_value=["badword"]),
        ),
        patch(
            "cogs.cleanup_cog.build_history_cleanup_plan",
            new=AsyncMock(
                return_value=SimpleNamespace(scanned=1, matched=[_msg("badword")]),
            ),
        ) as planner,
        patch.object(
            cog.bot,
            "wait_for",
            new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author)),
        ),
    ):
        await cog.cleanup_history.callback(
            cog, ctx, MAX_CLEANUP_HISTORY_LIMIT + 1, keyword="prohibited",
        )
    assert planner.await_args.kwargs["limit"] == MAX_CLEANUP_HISTORY_LIMIT
    warning = ctx.send.await_args_list[0].args[0]
    final = ctx.send.await_args_list[-1].args[0]
    assert "Requested" in warning
    assert "Maximum" in warning
    assert "effective" in final
    assert "Scanned" in final


@pytest.mark.asyncio
async def test_cleanuphistory_missing_manage_messages_stops_early():
    cog = Cleanup(MagicMock())
    ctx = _ctx([_msg("badword")])
    ctx.channel.permissions_for.return_value = SimpleNamespace(manage_messages=False)
    with patch(
        "cogs.cleanup_cog.build_history_cleanup_plan", new=AsyncMock(),
    ) as planner:
        await cog.cleanup_history.callback(cog, ctx, 100, keyword="prohibited")
    planner.assert_not_awaited()


@pytest.mark.asyncio
async def test_cleanuphistory_spam_mode_duplicate_window():
    now = discord.utils.utcnow()
    newest = _msg("hello there")
    newest.created_at = now
    middle = _msg("Hello   there")
    middle.created_at = now - timedelta(seconds=5)
    oldest = _msg("hello there")
    oldest.created_at = now - timedelta(seconds=30)
    cog = Cleanup(MagicMock())
    # history() is newest-first; spam logic must still preserve oldest in a burst.
    ctx = _ctx([newest, middle, oldest])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, _reply()]
    with (
        patch(
            "cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[]),
        ),
        patch.object(
            cog.bot,
            "wait_for",
            new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author)),
        ),
    ):
        await cog.cleanup_history.callback(cog, ctx, 100, keyword="spam")
    oldest.delete.assert_not_called()
    middle.delete.assert_not_called()
    newest.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_cleanuphistory_embeds_mode_routes_to_builder():
    cog = Cleanup(MagicMock())
    ctx = _ctx([_msg("x")])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, _reply()]
    with (
        patch(
            "cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[]),
        ),
        patch(
            "cogs.cleanup_cog.build_history_cleanup_plan",
            new=AsyncMock(
                return_value=SimpleNamespace(scanned=1, matched=[_msg("x")]),
            ),
        ) as planner,
        patch.object(
            cog.bot,
            "wait_for",
            new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author)),
        ),
    ):
        await cog.cleanup_history.callback(cog, ctx, 100, keyword="embeds")
    assert planner.await_args.kwargs["mode"] == "embeds"
    assert planner.await_args.kwargs["older_than"] is None


@pytest.mark.asyncio
async def test_cleanuphistory_older_than_token_sets_cutoff_and_strips_from_query():
    cog = Cleanup(MagicMock())
    ctx = _ctx([_msg("x")])
    confirm = MagicMock(id=100)
    confirm.add_reaction = AsyncMock()
    confirm.delete = AsyncMock()
    ctx.send.side_effect = [confirm, _reply()]
    before = discord.utils.utcnow()
    with (
        patch(
            "cogs.cleanup_cog.db.get_prohibited_words", new=AsyncMock(return_value=[]),
        ),
        patch(
            "cogs.cleanup_cog.build_history_cleanup_plan",
            new=AsyncMock(
                return_value=SimpleNamespace(scanned=1, matched=[_msg("x")]),
            ),
        ) as planner,
        patch.object(
            cog.bot,
            "wait_for",
            new=AsyncMock(return_value=(_confirmed_reaction(), ctx.author)),
        ),
    ):
        await cog.cleanup_history.callback(cog, ctx, 100, keyword="links older:7d")
    kwargs = planner.await_args.kwargs
    assert kwargs["mode"] == "links"
    # older:7d → a cutoff ~7 days before now (the `older:` token never leaks
    # into the keyword query).
    assert kwargs["keyword"] is None
    cutoff = kwargs["older_than"]
    assert cutoff is not None
    delta = (before - cutoff).total_seconds()
    assert 7 * 86400 - 60 <= delta <= 7 * 86400 + 60


@pytest.mark.asyncio
async def test_cleanuphistory_invalid_older_than_stops_early():
    cog = Cleanup(MagicMock())
    ctx = _ctx([_msg("x")])
    with patch(
        "cogs.cleanup_cog.build_history_cleanup_plan", new=AsyncMock(),
    ) as planner:
        await cog.cleanup_history.callback(cog, ctx, 100, keyword="links older:soon")
    planner.assert_not_awaited()
    assert "older:" in ctx.send.await_args_list[-1].args[0]
