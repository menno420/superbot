"""Mining titles panel — earn + equip identity titles (brainstorm §7.6).

An ephemeral child of the mining hub: shows the player's earned titles (with a
select to display one or clear it) and the locked titles with how to earn them.
Every mutation runs through :mod:`services.title_service` (the audited write
boundary — cogs/views never write ``equipped_title`` directly); this view is only
the select that calls it.
"""

from __future__ import annotations

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import title_service
from utils.mining import titles
from utils.ui_constants import ERROR_COLOR, MINING_COLOR, SUCCESS_COLOR
from views.base import HubView

_NONE_VALUE = "__none__"


async def build_titles_embed(
    user_id: int,
    guild_id: int,
    *,
    note: str = "",
) -> discord.Embed:
    """The titles embed: equipped title, earned list, and locked list."""
    ctx = await title_service.build_context(guild_id, user_id)
    earned = titles.earned_titles(ctx)
    equipped = await title_service.equipped_title(guild_id, user_id)

    embed = discord.Embed(title="🏆 Titles", color=MINING_COLOR)
    if note:
        embed.description = note
    embed.add_field(
        name="Equipped",
        value=titles.display(equipped) if equipped else "— none —",
        inline=False,
    )
    if earned:
        embed.add_field(
            name=f"Earned ({len(earned)})",
            value="\n".join(titles.display(t) for t in earned),
            inline=False,
        )
    locked = tuple(t for t in titles.ALL_TITLES if not titles.is_earned(t.id, ctx))
    if locked:
        embed.add_field(
            name=f"🔒 Locked ({len(locked)})",
            value="\n".join(f"{t.emoji} {t.label} — {t.requirement}" for t in locked),
            inline=False,
        )
    embed.set_footer(
        text="Earn titles by mastering skill branches, descending, and levelling up.",
    )
    return embed


class _TitleSelect(discord.ui.Select):
    """Pick an earned title to display, or clear it."""

    def __init__(self, earned: tuple[titles.Title, ...], equipped_id: str | None):
        options = [
            discord.SelectOption(
                label="(none)",
                value=_NONE_VALUE,
                description="Display no title",
                default=equipped_id is None,
            ),
        ]
        for t in earned:
            options.append(
                discord.SelectOption(
                    label=t.label,
                    value=t.id,
                    emoji=t.emoji,
                    default=t.id == equipped_id,
                ),
            )
        super().__init__(
            placeholder="Choose a title to display…",
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction):
            return
        view: MiningTitlesView = self.view  # type: ignore[assignment]
        choice = self.values[0]
        if choice == _NONE_VALUE:
            result = await title_service.unequip(view.guild_id, view._author.id)
        else:
            result = await title_service.equip(view.guild_id, view._author.id, choice)
        new_view = await MiningTitlesView.create(view._author, view.guild_id)
        embed = await build_titles_embed(
            view._author.id,
            view.guild_id,
            note=("✅ " if result.ok else "❌ ") + result.message,
        )
        embed.color = SUCCESS_COLOR if result.ok else ERROR_COLOR
        await safe_edit(interaction, embed=embed, view=new_view)
        view.stop()


class MiningTitlesView(HubView):
    """Earned-title display picker; a child of the mining hub."""

    SUBSYSTEM = "mining"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @classmethod
    async def create(
        cls,
        author: discord.Member | discord.User,
        guild_id: int,
    ) -> MiningTitlesView:
        """Build the view with the player's earned titles as select options."""
        view = cls(author, guild_id)
        ctx = await title_service.build_context(guild_id, author.id)
        earned = titles.earned_titles(ctx)
        equipped = await title_service.equipped_title(guild_id, author.id)
        if earned:
            view.add_item(_TitleSelect(earned, equipped.id if equipped else None))
        return view

    @discord.ui.button(label="↩ Mining Hub", style=discord.ButtonStyle.secondary, row=1)
    async def back_btn(self, interaction: discord.Interaction, _: discord.ui.Button):
        # Late import keeps the module-load graph acyclic (the hub imports this).
        from views.mining.main_panel import MiningHubView, build_overview_embed

        embed = await build_overview_embed(
            self._author.id,
            self.guild_id,
            name=getattr(self._author, "display_name", None),
        )
        view = MiningHubView()
        await interaction.response.edit_message(embed=embed, view=view)
        self.stop()


__all__ = ["MiningTitlesView", "build_titles_embed"]
