"""Unit tests for the paginated ``!list`` channel-cog command (PR F).

Pins:

* ``_build_channel_list_pages`` chunks categories at the configured
  per-page cap.
* The uncategorized bucket lands as the LAST field on the LAST page
  (operators must not page past empty content to find it).
* Each field value is truncated to Discord's 1024-character per-field
  cap when the category has too many channels.
* No embed exceeds Discord's 25-field cap.
* ``!list`` on an empty guild surfaces a non-empty empty-state embed
  rather than sending an unrenderable empty embed.
* When ≥ 2 pages exist the view ships with a prev/next/close trio
  and the message gets the paginator view attached.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import discord
import pytest
from discord.ext import commands

from cogs.channel_cog import (
    _CHANNELS_PER_PAGE_CATEGORIES,
    _MAX_FIELD_VALUE,
    ChannelCog,
    _build_channel_list_pages,
    _ChannelListPaginatorView,
)


def _make_channel(name: str, position: int = 0) -> MagicMock:
    ch = MagicMock(spec=discord.TextChannel)
    ch.name = name
    ch.position = position
    ch.category = None
    # Spec-bound mocks default-pass isinstance for the spec type, so this
    # also returns False for ``isinstance(ch, discord.CategoryChannel)``.
    return ch


def _make_category(name: str, channel_count: int = 3) -> MagicMock:
    cat = MagicMock(spec=discord.CategoryChannel)
    cat.name = name
    cat.channels = [_make_channel(f"{name}-ch{i}") for i in range(channel_count)]
    return cat


def _make_guild(
    *,
    categories: list[MagicMock] | None = None,
    uncategorized: list[MagicMock] | None = None,
) -> MagicMock:
    guild = MagicMock(spec=discord.Guild)
    guild.categories = categories or []
    uncat = uncategorized or []
    for ch in uncat:
        ch.category = None
    guild.channels = list(uncat) + list(guild.categories)
    return guild


# ---------------------------------------------------------------------------
# _build_channel_list_pages — pagination math
# ---------------------------------------------------------------------------


def test_empty_guild_returns_no_pages():
    guild = _make_guild()
    assert _build_channel_list_pages(guild) == []


def test_single_category_fits_on_one_page():
    guild = _make_guild(categories=[_make_category("General")])
    pages = _build_channel_list_pages(guild)
    assert len(pages) == 1
    # The single page has the category field and no footer (single-page
    # output omits page indicator).
    assert pages[0].fields[0].name == "General"
    assert pages[0].footer.text in (None, "")


def test_chunks_at_configured_page_size():
    cats = [_make_category(f"Cat{i}") for i in range(_CHANNELS_PER_PAGE_CATEGORIES + 5)]
    guild = _make_guild(categories=cats)
    pages = _build_channel_list_pages(guild)
    assert len(pages) == 2
    assert len(pages[0].fields) == _CHANNELS_PER_PAGE_CATEGORIES
    # Second page holds the remaining 5 categories.
    assert len(pages[1].fields) == 5


def test_multi_page_attaches_page_indicator_footer():
    cats = [_make_category(f"Cat{i}") for i in range(_CHANNELS_PER_PAGE_CATEGORIES + 1)]
    guild = _make_guild(categories=cats)
    pages = _build_channel_list_pages(guild)
    assert len(pages) == 2
    for idx, page in enumerate(pages, start=1):
        assert f"Page {idx}" in (page.footer.text or "")


def test_no_page_exceeds_field_cap():
    cats = [_make_category(f"Cat{i}") for i in range(50)]
    uncat = [_make_channel(f"U{i}") for i in range(3)]
    guild = _make_guild(categories=cats, uncategorized=uncat)
    pages = _build_channel_list_pages(guild)
    for page in pages:
        assert len(page.fields) <= 25, (
            f"Embed exceeded Discord's 25-field cap: {len(page.fields)}"
        )


# ---------------------------------------------------------------------------
# Uncategorized bucket — placement and content
# ---------------------------------------------------------------------------


def test_uncategorized_lands_on_last_page_only():
    cats = [_make_category(f"Cat{i}") for i in range(_CHANNELS_PER_PAGE_CATEGORIES + 1)]
    uncat = [_make_channel("loose")]
    guild = _make_guild(categories=cats, uncategorized=uncat)
    pages = _build_channel_list_pages(guild)
    assert len(pages) == 2
    # First page must NOT carry the uncategorized field — operators
    # should not see an empty bucket before navigating.
    first_field_names = {f.name for f in pages[0].fields}
    assert "— Uncategorized —" not in first_field_names
    # Last page carries it as the LAST field.
    last_page = pages[-1]
    assert last_page.fields[-1].name == "— Uncategorized —"
    assert "loose" in (last_page.fields[-1].value or "")


def test_uncategorized_only_no_categories():
    """Empty categories list but loose channels — paginator must still
    emit one page with the uncategorized bucket.
    """
    uncat = [_make_channel("loose-1"), _make_channel("loose-2")]
    guild = _make_guild(uncategorized=uncat)
    pages = _build_channel_list_pages(guild)
    assert len(pages) == 1
    assert pages[0].fields[0].name == "— Uncategorized —"


# ---------------------------------------------------------------------------
# Field-value truncation
# ---------------------------------------------------------------------------


def test_category_field_value_truncated_at_1024_chars():
    """A category with many channels must not push its field value
    over Discord's per-field 1024-char cap.
    """
    big = _make_category("Massive", channel_count=0)
    # Build channels whose names sum to ~3000 chars in the rendered
    # block.
    big.channels = [_make_channel("x" * 60) for _ in range(50)]
    guild = _make_guild(categories=[big])
    pages = _build_channel_list_pages(guild)
    field_value = pages[0].fields[0].value or ""
    assert len(field_value) <= _MAX_FIELD_VALUE


def test_uncategorized_field_value_truncated_at_1024_chars():
    uncat = [_make_channel("u" * 60, position=i) for i in range(50)]
    guild = _make_guild(uncategorized=uncat)
    pages = _build_channel_list_pages(guild)
    field_value = pages[0].fields[0].value or ""
    assert len(field_value) <= _MAX_FIELD_VALUE


# ---------------------------------------------------------------------------
# !list command behavior
# ---------------------------------------------------------------------------


def _ctx_with_guild(guild: MagicMock) -> MagicMock:
    ctx = MagicMock(spec=commands.Context)
    ctx.guild = guild
    ctx.author = MagicMock(spec=discord.Member)
    ctx.author.id = 1
    ctx.send = AsyncMock(return_value=MagicMock(spec=discord.Message))
    return ctx


@pytest.mark.asyncio
async def test_list_empty_guild_sends_empty_state_embed():
    cog = ChannelCog(MagicMock())
    ctx = _ctx_with_guild(_make_guild())

    await cog.list_channels.callback(cog, ctx)

    ctx.send.assert_awaited_once()
    _args, kwargs = ctx.send.call_args
    embed = kwargs["embed"]
    assert "No channels found" in (embed.description or "")
    # No view on empty state.
    assert kwargs.get("view") is None


@pytest.mark.asyncio
async def test_list_single_page_sends_no_view():
    cog = ChannelCog(MagicMock())
    guild = _make_guild(categories=[_make_category("General")])
    ctx = _ctx_with_guild(guild)

    await cog.list_channels.callback(cog, ctx)

    _args, kwargs = ctx.send.call_args
    # Single page must not ship the paginator view (no navigation needed).
    assert kwargs.get("view") is None


@pytest.mark.asyncio
async def test_list_multi_page_attaches_paginator_view():
    cog = ChannelCog(MagicMock())
    cats = [_make_category(f"Cat{i}") for i in range(_CHANNELS_PER_PAGE_CATEGORIES + 1)]
    guild = _make_guild(categories=cats)
    ctx = _ctx_with_guild(guild)

    await cog.list_channels.callback(cog, ctx)

    _args, kwargs = ctx.send.call_args
    view = kwargs.get("view")
    assert isinstance(view, _ChannelListPaginatorView)
    # The paginator ships with three controls: prev, next, close.
    labels = {
        c.label
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    assert labels == {"◀ Prev", "Next ▶", "↩ Close"}


# ---------------------------------------------------------------------------
# Paginator view — navigation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_paginator_prev_disabled_on_first_page():
    pages = [discord.Embed(title="A"), discord.Embed(title="B")]
    view = _ChannelListPaginatorView(MagicMock(id=1), pages)
    prev_btn = next(
        c for c in view.children if isinstance(c, discord.ui.Button) and "Prev" in (c.label or "")
    )
    assert prev_btn.disabled is True


@pytest.mark.asyncio
async def test_paginator_next_disabled_on_last_page():
    pages = [discord.Embed(title="A"), discord.Embed(title="B")]
    author = MagicMock(spec=discord.Member)
    author.id = 1
    view = _ChannelListPaginatorView(author, pages)
    view._idx = 1
    view._rebuild()
    next_btn = next(
        c for c in view.children if isinstance(c, discord.ui.Button) and "Next" in (c.label or "")
    )
    assert next_btn.disabled is True


@pytest.mark.asyncio
async def test_paginator_next_advances_page():
    pages = [discord.Embed(title="A"), discord.Embed(title="B"), discord.Embed(title="C")]
    author = MagicMock(spec=discord.Member)
    author.id = 1
    view = _ChannelListPaginatorView(author, pages)

    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = author
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()

    next_btn = next(
        c for c in view.children if isinstance(c, discord.ui.Button) and "Next" in (c.label or "")
    )
    await next_btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.edit_message.assert_awaited_once()
    _args, kwargs = interaction.response.edit_message.call_args
    assert kwargs["embed"] is pages[1]


@pytest.mark.asyncio
async def test_paginator_rejects_non_author():
    pages = [discord.Embed(title="A"), discord.Embed(title="B")]
    author = MagicMock(spec=discord.Member)
    author.id = 1
    view = _ChannelListPaginatorView(author, pages)

    stranger = MagicMock(spec=discord.Member)
    stranger.id = 999
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = stranger
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()

    allowed = await view.interaction_check(interaction)

    assert allowed is False
    interaction.response.send_message.assert_awaited_once()
