"""Project Moon (Limbus) knowledge — Discord plumbing only.

The first user surface of the Project Moon knowledge domain
(``docs/planning/project-moon-knowledge-domain-plan-2026-06-21.md``, owner
decision Q-0192). A read-only, deterministic **browse + lookup** surface over
the committed Limbus structural facts — the 12 Sinners, the 7 Sins, the 3 damage
types, the 5 E.G.O grades, and common status keywords.

Domain data + the typed accessors live in their own modules; this file hosts
only commands, the cog lifecycle, and the Help-menu hook:

    services/projmoon_data_service.py  — typed data loader + resolver
    utils/projmoon/keywords.py         — the ``has_limbus_context`` detector
    disbot/data/projmoon/limbus/       — the committed structural facts
    views/projmoon/                    — the browse panel + embed builders

No writes, no DB, no AI gateway — like ``btd6_reference``. Wiring the AI
natural-language grounding path (``AITask.PROJMOON_ANSWER``) is a later PR,
flagged for a runtime walk. Project Moon is **hub-less** for PR 1 (surfaced via
its Help hook + the typed ``!pm`` commands, like ``fishing``/``creature``);
an Explore/Games-hub panel can follow.
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from core.runtime.interaction_helpers import help_ctx_shim
from services import projmoon_data_service as data
from views.base import send_panel
from views.projmoon import (
    LimbusBrowseView,
    build_entry_embed,
    build_kind_embed,
    build_origins_embed,
    build_overview_embed,
)

logger = logging.getLogger("bot.cogs.project_moon")

# Subcommand name -> entity kind, for the per-category lookups.
_KIND_ALIASES: dict[str, str] = {
    "sinner": "sinner",
    "sinners": "sinner",
    "sin": "sin",
    "sins": "sin",
    "damage": "damage_type",
    "damagetype": "damage_type",
    "ego": "ego_grade",
    "grade": "ego_grade",
    "status": "status",
    "statuses": "status",
    "keyword": "status",
}


class ProjectMoonCog(commands.Cog):
    """Read-only Limbus reference lookups. User-tier; no provider calls."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # ------------------------------------------------------------------
    # Prefix surface — !pm ...
    # ------------------------------------------------------------------

    @commands.group(
        name="pm",
        aliases=["limbus", "projectmoon"],
        invoke_without_command=True,
    )
    async def pm_group(self, ctx: commands.Context) -> None:
        """Open the Project Moon (Limbus) browse panel."""
        view = LimbusBrowseView(ctx.author)
        await send_panel(ctx, embed=build_overview_embed(), view=view)

    @pm_group.command(name="lookup", aliases=["search", "what"])  # type: ignore[arg-type]
    async def pm_lookup(self, ctx: commands.Context, *, query: str = "") -> None:
        """Resolve any Limbus name/term across every category."""
        entry = data.resolve(query) if query.strip() else None
        if entry is None:
            await ctx.send(
                embed=discord.Embed(
                    title="🌑 Limbus lookup",
                    description=(
                        f"I don't have a Limbus entry matching **{query.strip() or '—'}**. "
                        "Try `!pm` to browse what I know."
                    ),
                    color=discord.Color.greyple(),
                ),
            )
            return
        await ctx.send(embed=build_entry_embed(entry))

    @pm_group.command(name="list")  # type: ignore[arg-type]
    async def pm_list(self, ctx: commands.Context, *, category: str = "") -> None:
        """List a whole category (sinners / sins / damage / ego / statuses)."""
        kind = _KIND_ALIASES.get(category.strip().lower())
        if kind is None:
            view = LimbusBrowseView(ctx.author)
            await send_panel(ctx, embed=build_overview_embed(), view=view)
            return
        await ctx.send(embed=build_kind_embed(kind))

    async def _category_lookup(
        self,
        ctx: commands.Context,
        kind: str,
        name: str,
    ) -> None:
        if not name.strip():
            await ctx.send(embed=build_kind_embed(kind))
            return
        entry = data.resolve(name, kind=kind)
        if entry is None:
            await ctx.send(
                embed=discord.Embed(
                    title=f"🌑 Limbus — {data.KIND_LABELS[kind]}",
                    description=(
                        f"No {data.KIND_LABELS[kind].rstrip('s').lower()} matches "
                        f"**{name.strip()}**. Try `!pm list {kind}` to see them all."
                    ),
                    color=discord.Color.greyple(),
                ),
            )
            return
        await ctx.send(embed=build_entry_embed(entry))

    @pm_group.command(name="origins", aliases=["origin", "literary"])  # type: ignore[arg-type]
    async def pm_origins(self, ctx: commands.Context) -> None:
        """Show every Sinner ↔ the literary work it is drawn from."""
        await ctx.send(embed=build_origins_embed())

    @pm_group.command(name="sinner", aliases=["sinners"])  # type: ignore[arg-type]
    async def pm_sinner(self, ctx: commands.Context, *, name: str = "") -> None:
        """Look up one of the 12 Sinners (or list them all)."""
        await self._category_lookup(ctx, "sinner", name)

    @pm_group.command(name="sin", aliases=["sins", "affinity"])  # type: ignore[arg-type]
    async def pm_sin(self, ctx: commands.Context, *, name: str = "") -> None:
        """Look up one of the 7 Sin affinities (or list them all)."""
        await self._category_lookup(ctx, "sin", name)

    @pm_group.command(name="status", aliases=["statuses", "keyword"])  # type: ignore[arg-type]
    async def pm_status(self, ctx: commands.Context, *, name: str = "") -> None:
        """Look up a status keyword like Burn / Bleed / Sinking (or list them all)."""
        await self._category_lookup(ctx, "status", name)

    @pm_group.command(name="ego", aliases=["grade"])  # type: ignore[arg-type]
    async def pm_ego(self, ctx: commands.Context, *, name: str = "") -> None:
        """Look up an E.G.O grade (ZAYIN…ALEPH) (or list them all)."""
        await self._category_lookup(ctx, "ego_grade", name)

    @pm_group.command(name="damage", aliases=["damagetype"])  # type: ignore[arg-type]
    async def pm_damage(self, ctx: commands.Context, *, name: str = "") -> None:
        """Look up a damage type (Slash / Pierce / Blunt) (or list them all)."""
        await self._category_lookup(ctx, "damage_type", name)

    # ------------------------------------------------------------------
    # Slash front door — /pm (ephemeral browse panel)
    # ------------------------------------------------------------------

    @app_commands.command(
        name="pm",
        description="Browse Project Moon (Limbus) knowledge — Sinners, Sins, statuses, E.G.O.",
    )
    async def pm_slash(self, interaction: discord.Interaction) -> None:
        """Ephemeral Limbus browse panel."""
        embed, view = await self.build_help_menu_view(interaction)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # ------------------------------------------------------------------
    # Help-menu direct-navigation hook
    # ------------------------------------------------------------------

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help/hub direct-navigation hook — the interactive Limbus browse panel."""
        ctx = help_ctx_shim(interaction)
        return build_overview_embed(), LimbusBrowseView(ctx.author)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ProjectMoonCog(bot))
