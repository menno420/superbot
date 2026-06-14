"""``!list`` channel-inventory pagination (PR F; extracted from the cog in P0-4).

Discord limits an embed to 25 fields and 6000 characters total, and each
field value to 1024 characters.  This module renders the guild's categories +
uncategorized bucket into paginated embeds and provides the tiny inline
paginator view.

Lives under ``views/channels/`` (the F-3 convention: view/rendering code is a
``views/<sub>/`` sibling, not inlined in the cog).  ``cogs.channel_cog``
re-exports these names for backward compatibility.
"""

from __future__ import annotations

import discord

from utils.ui_constants import INFO_COLOR

# Conservative chunk to stay under both caps: 12 categories per page leaves
# headroom for the uncategorized bucket on the last page and respects the
# 6000-char total.
_CHANNELS_PER_PAGE_CATEGORIES = 12
_MAX_FIELD_VALUE = 1024


def _channel_block_for_category(
    category: discord.CategoryChannel,
) -> str:
    """Render one category's channels as a newline-separated block.

    Truncates the block at ``_MAX_FIELD_VALUE`` characters with an
    ellipsis so a category with hundreds of channels does not push
    the embed over Discord's per-field 1024-char cap.
    """
    if not category.channels:
        return "No channels"
    lines = [f" - {ch.name}" for ch in category.channels]
    block = "\n".join(lines)
    if len(block) > _MAX_FIELD_VALUE:
        # Reserve room for the truncation marker.
        return block[: _MAX_FIELD_VALUE - 4] + "\n..."
    return block


def _uncategorized_block(guild: discord.Guild) -> str | None:
    uncategorized = [
        ch
        for ch in guild.channels
        if ch.category is None and not isinstance(ch, discord.CategoryChannel)
    ]
    if not uncategorized:
        return None
    lines = [f" - {ch.name}" for ch in sorted(uncategorized, key=lambda c: c.position)]
    block = "\n".join(lines)
    if len(block) > _MAX_FIELD_VALUE:
        return block[: _MAX_FIELD_VALUE - 4] + "\n..."
    return block


def _build_channel_list_pages(
    guild: discord.Guild,
) -> list[discord.Embed]:
    """Split the categories + uncategorized bucket into paginated embeds.

    Pagination math:

    * Each page renders up to ``_CHANNELS_PER_PAGE_CATEGORIES`` (12)
      category fields. With a guild's 25-field embed cap this leaves
      13 fields of slack — plenty for the uncategorized field on
      the final page and any future per-page metadata.
    * The uncategorized bucket lands as the last field on the LAST
      page; it does not occupy its own page.
    * If the guild has no categories AND no uncategorized channels,
      ``ChannelCog.list_channels`` short-circuits to an empty-state embed.
    """
    categories = list(guild.categories)
    pages: list[discord.Embed] = []

    chunks = [
        categories[i : i + _CHANNELS_PER_PAGE_CATEGORIES]
        for i in range(0, len(categories), _CHANNELS_PER_PAGE_CATEGORIES)
    ] or [[]]

    uncat_block = _uncategorized_block(guild)
    last_chunk_idx = len(chunks) - 1

    for idx, chunk in enumerate(chunks):
        embed = discord.Embed(title="Categories and Channels", color=INFO_COLOR)
        for category in chunk:
            embed.add_field(
                name=category.name,
                value=_channel_block_for_category(category),
                inline=False,
            )
        # Attach the uncategorized bucket to the last page so the
        # operator sees it without paging past empty content.
        if idx == last_chunk_idx and uncat_block is not None:
            embed.add_field(
                name="— Uncategorized —",
                value=uncat_block,
                inline=False,
            )
        if not embed.fields:
            # Empty guild — the caller short-circuits before reaching
            # this branch, but defend against a future refactor.
            continue
        if len(chunks) > 1:
            embed.set_footer(text=f"Page {idx + 1} / {len(chunks)}")
        pages.append(embed)

    return pages


class _ChannelListPaginatorView(discord.ui.View):
    """Tiny inline paginator for ``!list`` output (PR F).

    Mirrors the leaderboard pagination style — ``◀``, ``▶``, and a
    ``↩ Close`` button on a single row. No new framework; this view
    only exists so guilds with many categories don't hit Discord's
    embed-field cap.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        pages: list[discord.Embed],
    ) -> None:
        super().__init__(timeout=180)
        self._author = author
        self._pages = pages
        self._idx = 0
        self.message: discord.Message | None = None
        self._rebuild()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self._author.id:
            await interaction.response.send_message(
                "This list isn't yours.",
                ephemeral=True,
            )
            return False
        return True

    def _rebuild(self) -> None:
        self.clear_items()
        prev_btn = discord.ui.Button(  # type: ignore[var-annotated]
            label="◀ Prev",
            style=discord.ButtonStyle.grey,
            disabled=self._idx == 0,
            row=0,
        )
        prev_btn.callback = self._on_prev  # type: ignore[method-assign]
        self.add_item(prev_btn)

        next_btn = discord.ui.Button(  # type: ignore[var-annotated]
            label="Next ▶",
            style=discord.ButtonStyle.grey,
            disabled=self._idx >= len(self._pages) - 1,
            row=0,
        )
        next_btn.callback = self._on_next  # type: ignore[method-assign]
        self.add_item(next_btn)

        close_btn = discord.ui.Button(  # type: ignore[var-annotated]
            label="↩ Close",
            style=discord.ButtonStyle.secondary,
            row=0,
        )
        close_btn.callback = self._on_close  # type: ignore[method-assign]
        self.add_item(close_btn)

    async def _on_prev(self, interaction: discord.Interaction) -> None:
        self._idx = max(0, self._idx - 1)
        self._rebuild()
        await interaction.response.edit_message(
            embed=self._pages[self._idx],
            view=self,
        )

    async def _on_next(self, interaction: discord.Interaction) -> None:
        self._idx = min(len(self._pages) - 1, self._idx + 1)
        self._rebuild()
        await interaction.response.edit_message(
            embed=self._pages[self._idx],
            view=self,
        )

    async def _on_close(self, interaction: discord.Interaction) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(view=self)
        self.stop()

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass


__all__ = [
    "_ChannelListPaginatorView",
    "_build_channel_list_pages",
]
