"""BTD6 Assistant cog — Module 4 of the AI/BTD6 plan.

Provides deterministic Bloons Tower Defense 6 lookups and a
provider-free ``ask`` command. The cog is intentionally
deterministic-only; Module 5 wires optional AI augmentation.

Architecture:

* The cog never imports the AI cog. When AI augmentation lands in
  Module 5 it will go through ``services.ai_gateway``.
* All facts come from :mod:`services.btd6_data_service` via the
  knowledge / response-builder services. Nothing in the cog
  invents BTD6 data.
* Commands match the SuperBot convention (prefix + slash side by
  side; both forms gated as user-tier per the SUBSYSTEMS entry).
"""

from __future__ import annotations

import logging
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from cogs.btd6.stage import STAGE_NAME as BTD6_STAGE_NAME
from cogs.btd6.stage import BTD6AssistantMessageStage
from core.runtime import message_pipeline
from services import btd6_ai_service, btd6_knowledge_service
from services.btd6_resolver_service import resolve
from views.btd6.panel import BTD6PanelView, build_btd6_panel_embed

logger = logging.getLogger("bot")


# ---------------------------------------------------------------------------
# Embed builders — shared by panel buttons and explicit commands.
# ---------------------------------------------------------------------------


def _response_to_embed(response: Any) -> discord.Embed:
    """Convert a :class:`BTD6Response` into a Discord embed."""
    color = {
        "high": discord.Color.green(),
        "medium": discord.Color.gold(),
        "low": discord.Color.light_grey(),
    }.get(response.confidence, discord.Color.light_grey())
    embed = discord.Embed(
        title=response.title,
        description=response.short_answer,
        color=color,
    )
    if response.why_it_matters:
        embed.add_field(
            name="Why it matters",
            value=response.why_it_matters,
            inline=False,
        )
    if response.recommended_options:
        embed.add_field(
            name="Recommended options",
            value="\n".join(f"• {opt}" for opt in response.recommended_options),
            inline=False,
        )
    if response.common_mistakes:
        embed.add_field(
            name="Common mistakes",
            value="\n".join(f"• {m}" for m in response.common_mistakes),
            inline=False,
        )
    if response.version_sensitivity:
        embed.add_field(
            name="Version sensitivity",
            value=response.version_sensitivity,
            inline=False,
        )
    if response.follow_up:
        embed.add_field(name="Follow-up", value=response.follow_up, inline=False)
    if response.sources:
        embed.set_footer(text="Sources: " + " · ".join(response.sources))
    return embed


def build_status_embed() -> discord.Embed:
    """BTD6 status: data version + entity counts."""
    embed = discord.Embed(
        title="🐵 BTD6 Assistant — Status",
        description="Deterministic-only mode (Module 4). AI augmentation off.",
        color=discord.Color.green(),
    )
    embed.add_field(
        name="Data version",
        value=btd6_knowledge_service.data_version(),
        inline=True,
    )
    embed.add_field(
        name="Game version",
        value=btd6_knowledge_service.game_version(),
        inline=True,
    )
    embed.add_field(
        name="Towers",
        value=str(len(btd6_knowledge_service.list_towers())),
        inline=True,
    )
    embed.add_field(
        name="Heroes",
        value=str(len(btd6_knowledge_service.list_heroes())),
        inline=True,
    )
    embed.add_field(
        name="Maps",
        value=str(len(btd6_knowledge_service.list_maps())),
        inline=True,
    )
    embed.add_field(
        name="Rounds",
        value=str(len(btd6_knowledge_service.list_rounds())),
        inline=True,
    )
    return embed


def build_diagnostics_embed() -> discord.Embed:
    """Detailed diagnostics: source labels and entry catalogues."""
    embed = discord.Embed(
        title="🐵 BTD6 Assistant — Diagnostics",
        color=discord.Color.green(),
    )
    embed.add_field(
        name="Towers",
        value=", ".join(t.canonical for t in btd6_knowledge_service.list_towers()),
        inline=False,
    )
    embed.add_field(
        name="Heroes",
        value=", ".join(h.canonical for h in btd6_knowledge_service.list_heroes()),
        inline=False,
    )
    embed.add_field(
        name="Maps",
        value=", ".join(m.canonical for m in btd6_knowledge_service.list_maps()),
        inline=False,
    )
    embed.add_field(
        name="Modes",
        value=", ".join(m.canonical for m in btd6_knowledge_service.list_modes()),
        inline=False,
    )
    rounds = ", ".join(
        str(r.round_number) for r in btd6_knowledge_service.list_rounds()
    )
    embed.add_field(name="Rounds tracked", value=rounds, inline=False)
    return embed


def build_towers_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🐵 BTD6 — Towers",
        color=discord.Color.green(),
    )
    for tower in btd6_knowledge_service.list_towers():
        embed.add_field(
            name=tower.canonical,
            value=f"Cost: {tower.base_cost} • Category: {tower.category}",
            inline=True,
        )
    return embed


def build_modes_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🐵 BTD6 — Modes",
        color=discord.Color.green(),
    )
    for mode in btd6_knowledge_service.list_modes():
        embed.add_field(
            name=mode.canonical,
            value=(
                f"Starting cash: {mode.starting_cash} • "
                f"Lives: {mode.starting_lives}"
            ),
            inline=False,
        )
    return embed


def build_why_no_response_embed(
    stage: BTD6AssistantMessageStage | None,
    channel_id: int,
) -> discord.Embed:
    """Render the latest passive-stage skip reasons for a channel.

    The buffer carries only skip-reason codes + confidence scores —
    never message content — so this command is safe to run in
    public channels.
    """
    embed = discord.Embed(
        title="🐵 BTD6 — Why no response?",
        color=discord.Color.light_grey(),
    )
    if stage is None:
        embed.description = (
            "Passive stage is not loaded. Reload the BTD6 cog and try again."
        )
        return embed
    skips = stage.latest_skips(channel_id)
    if not skips:
        embed.description = (
            "No recent skip records for this channel. Either the passive "
            "stage has not seen a message here yet, or it replied to the "
            "last eligible one."
        )
        return embed
    lines: list[str] = []
    for record in reversed(skips):  # newest first
        lines.append(
            f"`{record.reason}` • confidence={record.confidence:.2f} "
            f"• <t:{int(record.timestamp)}:R>",
        )
    embed.description = "\n".join(lines)
    embed.set_footer(text="No message content is stored — only skip reasons.")
    return embed


def build_test_intent_embed(text: str) -> discord.Embed:
    """Resolver introspection — useful for operators tuning the cog."""
    intent = resolve(text)
    embed = discord.Embed(
        title="🐵 BTD6 — test-intent",
        description=f"Resolved intent for: ``{text[:200]}``",
        color=discord.Color.green(),
    )
    embed.add_field(name="Confidence", value=f"{intent.confidence:.2f}")
    embed.add_field(
        name="Towers",
        value=", ".join(t.canonical for t in intent.towers) or "—",
        inline=False,
    )
    embed.add_field(
        name="Heroes",
        value=", ".join(h.canonical for h in intent.heroes) or "—",
        inline=False,
    )
    embed.add_field(
        name="Maps",
        value=", ".join(m.canonical for m in intent.maps) or "—",
        inline=False,
    )
    embed.add_field(
        name="Modes",
        value=", ".join(m.canonical for m in intent.modes) or "—",
        inline=False,
    )
    embed.add_field(
        name="Rounds",
        value=", ".join(str(n) for n in intent.candidate_round_numbers) or "—",
        inline=False,
    )
    return embed


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class BTD6Cog(commands.Cog):
    """Deterministic BTD6 assistant. User-tier; no provider calls."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._passive_stage: BTD6AssistantMessageStage | None = None

    async def cog_load(self) -> None:
        """Register the BTD6 SubsystemSchema; do NOT register a passive stage.

        M2 introduced the central natural-language stage (order=70).
        M5 retires the short-lived ``AI_BTD6_VIA_ROUTER`` env var: the
        BTD6 passive stage stays unregistered unconditionally so the
        central stage is the only passive replier. ``!btd6
        why-no-response`` reads the AI decision audit table directly,
        not the in-memory skip buffer of the (now unregistered)
        legacy stage.
        """
        from cogs.btd6.schemas import register_schemas

        register_schemas()
        self._passive_stage = None
        message_pipeline.unregister(BTD6_STAGE_NAME)

    async def cog_unload(self) -> None:
        """Remove the passive stage so reload/test cycles stay clean."""
        message_pipeline.unregister(BTD6_STAGE_NAME)
        self._passive_stage = None

    # ------------------------------------------------------------------
    # Prefix commands
    # ------------------------------------------------------------------

    @commands.group(name="btd6", invoke_without_command=True)
    async def btd6_group(self, ctx: commands.Context) -> None:
        """Open the BTD6 panel."""
        await ctx.send(embed=build_btd6_panel_embed(), view=BTD6PanelView())

    @btd6_group.command(name="status")  # type: ignore[arg-type]
    async def btd6_status(self, ctx: commands.Context) -> None:
        await ctx.send(embed=build_status_embed())

    @btd6_group.command(name="diagnostics")  # type: ignore[arg-type]
    async def btd6_diagnostics(self, ctx: commands.Context) -> None:
        await ctx.send(embed=build_diagnostics_embed())

    @btd6_group.command(name="ask")  # type: ignore[arg-type]
    async def btd6_ask(self, ctx: commands.Context, *, question: str) -> None:
        """Deterministic Q&A. Module 5 adds optional AI augmentation."""
        response = await btd6_ai_service.answer_question(question)
        await ctx.send(embed=_response_to_embed(response))

    @btd6_group.command(name="tower")  # type: ignore[arg-type]
    async def btd6_tower(self, ctx: commands.Context, *, name: str) -> None:
        intent = resolve(name)
        if not intent.towers:
            await ctx.send(
                embed=_response_to_embed(
                    btd6_ai_service.deterministic_answer(intent),
                ),
            )
            return
        from services.btd6_knowledge_service import tower_fact
        from services.btd6_response_builder import for_tower

        fact = tower_fact(intent.towers[0].id)
        if fact is None:
            await ctx.send(content=f"No deterministic data for {name!r}.")
            return
        await ctx.send(embed=_response_to_embed(for_tower(fact)))

    @btd6_group.command(name="hero")  # type: ignore[arg-type]
    async def btd6_hero(self, ctx: commands.Context, *, name: str) -> None:
        intent = resolve(name)
        if not intent.heroes:
            await ctx.send(
                embed=_response_to_embed(
                    btd6_ai_service.deterministic_answer(intent),
                ),
            )
            return
        from services.btd6_response_builder import for_hero

        await ctx.send(embed=_response_to_embed(for_hero(intent.heroes[0])))

    @btd6_group.command(name="round")  # type: ignore[arg-type]
    async def btd6_round(self, ctx: commands.Context, number: int) -> None:
        from services.btd6_knowledge_service import round_fact
        from services.btd6_response_builder import for_round, for_unresolved

        fact = round_fact(number)
        if fact is None:
            intent = resolve(f"round {number}")
            await ctx.send(embed=_response_to_embed(for_unresolved(intent)))
            return
        await ctx.send(embed=_response_to_embed(for_round(fact)))

    @btd6_group.command(name="test-intent")  # type: ignore[arg-type]
    async def btd6_test_intent(self, ctx: commands.Context, *, text: str) -> None:
        await ctx.send(embed=build_test_intent_embed(text))

    @btd6_group.command(name="why-no-response")  # type: ignore[arg-type]
    async def btd6_why_no_response(self, ctx: commands.Context) -> None:
        """Show the latest passive-stage skip reasons for this channel."""
        await ctx.send(
            embed=build_why_no_response_embed(
                self._passive_stage,
                ctx.channel.id if ctx.channel else 0,
            ),
        )

    @btd6_group.command(name="sources")  # type: ignore[arg-type]
    async def btd6_sources(self, ctx: commands.Context) -> None:
        """List BTD6 source registry rows (M3A: read-only)."""
        from services import btd6_source_registry

        rows = await btd6_source_registry.list_all()
        if not rows:
            await ctx.send("No BTD6 sources registered yet.")
            return
        lines = []
        for row in rows[:25]:
            state = "ON" if row["enabled"] else "off"
            url = row.get("full_url") or row.get("path_template") or "—"
            lines.append(
                f"`{row['source_key']:<26}` tier {row['trust_tier']} · "
                f"{state} · {url}",
            )
        await ctx.send("\n".join(lines))

    @btd6_group.command(name="strategies")  # type: ignore[arg-type]
    async def btd6_strategies(self, ctx: commands.Context) -> None:
        """List strategy memory entries available in this guild."""
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return
        from services import btd6_strategy_service

        rows = await btd6_strategy_service.list_for_guild(ctx.guild.id, limit=10)
        if not rows:
            await ctx.send("No BTD6 strategies recorded for this guild yet.")
            return
        lines = []
        for row in rows:
            tag = (
                "📦 published" if row["visibility"] == "published"
                else "🛡️ guild"
            )
            lines.append(
                f"{tag} · `{row['approval_status']}` · **{row['title']}** "
                f"— {row['summary'][:80]}",
            )
        await ctx.send("\n".join(lines))

    @commands.command(name="btd6menu")
    async def btd6menu(self, ctx: commands.Context) -> None:
        """Open the BTD6 panel (alias for ``!btd6``)."""
        await ctx.send(embed=build_btd6_panel_embed(), view=BTD6PanelView())

    # ------------------------------------------------------------------
    # App commands — mirror the prefix surface.
    # ------------------------------------------------------------------

    btd6_app_group = app_commands.Group(
        name="btd6",
        description="BTD6 Assistant — deterministic tower/round/mode lookups.",
    )

    @btd6_app_group.command(name="status", description="BTD6 assistant status.")
    async def btd6_status_slash(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=build_status_embed(),
            ephemeral=True,
        )

    @btd6_app_group.command(
        name="diagnostics",
        description="BTD6 dataset diagnostics.",
    )
    async def btd6_diagnostics_slash(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=build_diagnostics_embed(),
            ephemeral=True,
        )

    @btd6_app_group.command(name="ask", description="Ask a BTD6 question.")
    async def btd6_ask_slash(
        self,
        interaction: discord.Interaction,
        question: str,
    ) -> None:
        response = await btd6_ai_service.answer_question(question)
        await interaction.response.send_message(
            embed=_response_to_embed(response),
            ephemeral=True,
        )

    @btd6_app_group.command(name="tower", description="Look up a tower.")
    async def btd6_tower_slash(
        self,
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        intent = resolve(name)
        from services.btd6_knowledge_service import tower_fact
        from services.btd6_response_builder import for_tower, for_unresolved

        if not intent.towers:
            response = for_unresolved(intent)
        else:
            fact = tower_fact(intent.towers[0].id)
            response = for_tower(fact) if fact is not None else for_unresolved(intent)
        await interaction.response.send_message(
            embed=_response_to_embed(response),
            ephemeral=True,
        )

    @btd6_app_group.command(name="round", description="Look up a round.")
    async def btd6_round_slash(
        self,
        interaction: discord.Interaction,
        number: int,
    ) -> None:
        from services.btd6_knowledge_service import round_fact
        from services.btd6_response_builder import for_round, for_unresolved

        fact = round_fact(number)
        if fact is None:
            intent = resolve(f"round {number}")
            response = for_unresolved(intent)
        else:
            response = for_round(fact)
        await interaction.response.send_message(
            embed=_response_to_embed(response),
            ephemeral=True,
        )

    @btd6_app_group.command(
        name="test-intent",
        description="Show what the resolver extracted from a message.",
    )
    async def btd6_test_intent_slash(
        self,
        interaction: discord.Interaction,
        text: str,
    ) -> None:
        await interaction.response.send_message(
            embed=build_test_intent_embed(text),
            ephemeral=True,
        )

    @app_commands.command(name="btd6menu", description="Open the BTD6 panel.")
    async def btd6menu_slash(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=build_btd6_panel_embed(),
            view=BTD6PanelView(),
            ephemeral=True,
        )

    # ------------------------------------------------------------------
    # Help-menu hook
    # ------------------------------------------------------------------

    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        return build_btd6_panel_embed(), BTD6PanelView()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BTD6Cog(bot))
