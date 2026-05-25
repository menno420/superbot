"""BTD6 Assistant cog.

Provides Bloons Tower Defense 6 lookups, strategy memory, and
audit-quality diagnostics. Deterministic facts (towers, heroes,
maps, modes, rounds) come from :mod:`services.btd6_knowledge_service`;
live entity grounding flows through :mod:`services.btd6_context_service`
once the resolver matches a live intent.

Architecture:

* The cog never writes to the AI Platform's policy / instruction
  tables. Natural-language reply eligibility is owned by
  :mod:`services.ai_natural_language_policy`; this cog reads from
  :mod:`services.ai_decision_audit_service` only.
* All BTD6 facts come from the BTD6 service layer; nothing in the
  cog invents BTD6 data.
* Commands match the SuperBot convention (prefix + slash side by
  side via :mod:`cogs.btd6._builders`; both forms gated as user-tier
  per the SUBSYSTEMS entry).
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs.btd6._embeds import (
    build_diagnostics_embed,
    build_status_embed,
    build_test_intent_embed,
)
from cogs.btd6._embeds import response_to_embed as _response_to_embed
from cogs.btd6.stage import STAGE_NAME as BTD6_STAGE_NAME
from core.runtime import message_pipeline
from services import btd6_ai_service
from services.btd6_resolver_service import resolve
from views.btd6.panel import BTD6PanelView, build_btd6_panel_embed

logger = logging.getLogger("bot")


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class BTD6Cog(commands.Cog):
    """Deterministic BTD6 assistant. User-tier; no provider calls."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        """Register the BTD6 SubsystemSchema; do NOT register a passive stage.

        M2 introduced the central natural-language stage (order=70).
        M5 retired the short-lived ``AI_BTD6_VIA_ROUTER`` env var: the
        BTD6 passive stage stays unregistered unconditionally so the
        central stage is the only passive replier. ``!btd6
        why-no-response`` reads the AI decision audit table directly,
        filtered to ``task='btd6.answer'``.
        """
        from cogs.btd6.schemas import register_schemas

        register_schemas()
        message_pipeline.unregister(BTD6_STAGE_NAME)

    async def cog_unload(self) -> None:
        """Defensive unregister so reload/test cycles stay clean."""
        message_pipeline.unregister(BTD6_STAGE_NAME)

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
        from cogs.btd6._builders import build_hero_embed

        await ctx.send(embed=await build_hero_embed(name))

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
    async def btd6_why_no_response(
        self,
        ctx: commands.Context,
        limit: int = 10,
    ) -> None:
        """Show the most recent BTD6 denials / skips for this guild.

        Reads the canonical ``ai_decision_audit`` table filtered to
        ``task='btd6.answer'`` — the legacy in-memory skip buffer of
        the retired passive stage is no longer consulted. The embed
        surfaces ``policy_snapshot_hash``, ``instruction_profile_ids``,
        ``route``, ``provider``, ``model`` and ``reason_code`` so
        operators can correlate a denial with the policy/profile state
        that produced it.
        """
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return
        from cogs.btd6._builders import build_why_no_response_payload

        payload = await build_why_no_response_payload(ctx.guild.id, limit=limit)
        if isinstance(payload, str):
            await ctx.send(payload)
        else:
            await ctx.send(embed=payload)

    @btd6_group.command(name="sources")  # type: ignore[arg-type]
    async def btd6_sources(self, ctx: commands.Context) -> None:
        """List BTD6 source registry rows."""
        from cogs.btd6._builders import build_sources_payload

        await ctx.send(await build_sources_payload())

    @btd6_group.command(name="strategies")  # type: ignore[arg-type]
    async def btd6_strategies(self, ctx: commands.Context) -> None:
        """List strategy memory entries available in this guild."""
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return
        from cogs.btd6._builders import build_strategies_payload

        await ctx.send(await build_strategies_payload(ctx.guild.id))

    @btd6_group.command(name="source-health")  # type: ignore[arg-type]
    async def btd6_source_health(
        self,
        ctx: commands.Context,
        limit: int = 25,
    ) -> None:
        """Show source registry freshness (PR-D)."""
        from cogs.btd6._builders import build_source_health_embed

        await ctx.send(embed=await build_source_health_embed(limit=limit))

    @btd6_group.command(name="latest-data")  # type: ignore[arg-type]
    async def btd6_latest_data(self, ctx: commands.Context) -> None:
        """Show newest fact envelope per entity_kind (PR-D)."""
        from cogs.btd6._builders import build_latest_data_embed

        await ctx.send(embed=await build_latest_data_embed())

    @btd6_group.command(name="grounding")  # type: ignore[arg-type]
    async def btd6_grounding(
        self,
        ctx: commands.Context,
        message_id: int,
    ) -> None:
        """Show the grounding facts that fed an AI response (PR-D)."""
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return
        from cogs.btd6._builders import build_grounding_embed

        payload = await build_grounding_embed(ctx.guild.id, message_id)
        if isinstance(payload, str):
            await ctx.send(payload)
        else:
            await ctx.send(embed=payload)

    @btd6_group.command(name="browse")  # type: ignore[arg-type]
    async def btd6_browse(
        self,
        ctx: commands.Context,
        limit: int = 10,
    ) -> None:
        """Browse published BTD6 strategies (PR-F)."""
        from views.btd6.strategy_browse import build_browse_embed

        await ctx.send(embed=await build_browse_embed(limit=limit))

    @btd6_group.command(name="mine")  # type: ignore[arg-type]
    async def btd6_mine(self, ctx: commands.Context, limit: int = 10) -> None:
        """List my own strategy submissions in this guild (PR-F)."""
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return
        from views.btd6.strategy_browse import build_mine_embed

        await ctx.send(
            embed=await build_mine_embed(ctx.guild.id, ctx.author.id, limit=limit),
        )

    @btd6_group.command(name="strategy")  # type: ignore[arg-type]
    async def btd6_strategy_detail(
        self,
        ctx: commands.Context,
        strategy_id: int,
    ) -> None:
        """Show one strategy in detail (PR-F)."""
        from views.btd6.strategy_browse import build_detail_embed

        viewer_guild = ctx.guild.id if ctx.guild else None
        payload = await build_detail_embed(strategy_id, viewer_guild_id=viewer_guild)
        if isinstance(payload, str):
            await ctx.send(payload)
        else:
            await ctx.send(embed=payload)

    @btd6_group.command(name="strategy-audit")  # type: ignore[arg-type]
    async def btd6_strategy_audit(
        self,
        ctx: commands.Context,
        strategy_id: int,
    ) -> None:
        """Show the per-strategy audit log (PR-F)."""
        from views.btd6.strategy_browse import build_audit_embed

        await ctx.send(embed=await build_audit_embed(strategy_id))

    @btd6_group.command(name="submit")  # type: ignore[arg-type]
    async def btd6_submit(self, ctx: commands.Context) -> None:
        """Open a strategy submission modal (slash-only on Discord).

        Discord modals are slash-only; the prefix command surfaces a
        friendly message redirecting to /btd6 submit.
        """
        await ctx.send(
            "Strategy submission opens a Discord modal — use `/btd6 submit` "
            "to fill it in.",
        )

    @btd6_group.command(name="pending")  # type: ignore[arg-type]
    @commands.has_guild_permissions(manage_guild=True)
    async def btd6_pending(self, ctx: commands.Context, limit: int = 5) -> None:
        """List pending strategy submissions with review buttons.

        Staff-only (manage_guild). Each pending strategy gets its own
        review embed + button row (Approve guild / Publish / Reject /
        Unpublish). All actions funnel through
        ``services.btd6_strategy_mutation``.
        """
        if not ctx.guild:
            await ctx.send("This command requires a guild context.")
            return
        from cogs.btd6._builders import build_pending_review_payload

        payload = await build_pending_review_payload(ctx.guild.id, limit=limit)
        if isinstance(payload, str):
            await ctx.send(payload)
            return
        for embed, view in payload:
            await ctx.send(embed=embed, view=view)

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

    @btd6_app_group.command(name="hero", description="Look up a hero.")
    async def btd6_hero_slash(
        self,
        interaction: discord.Interaction,
        name: str,
    ) -> None:
        from cogs.btd6._builders import build_hero_embed

        await interaction.response.send_message(
            embed=await build_hero_embed(name),
            ephemeral=True,
        )

    @btd6_app_group.command(
        name="why-no-response",
        description="Recent BTD6 denials/skips for this guild.",
    )
    async def btd6_why_no_response_slash(
        self,
        interaction: discord.Interaction,
        limit: int = 10,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command requires a guild context.",
                ephemeral=True,
            )
            return
        from cogs.btd6._builders import build_why_no_response_payload

        payload = await build_why_no_response_payload(
            interaction.guild.id,
            limit=limit,
        )
        if isinstance(payload, str):
            await interaction.response.send_message(payload, ephemeral=True)
        else:
            await interaction.response.send_message(embed=payload, ephemeral=True)

    @btd6_app_group.command(
        name="sources",
        description="List BTD6 source registry rows.",
    )
    async def btd6_sources_slash(self, interaction: discord.Interaction) -> None:
        from cogs.btd6._builders import build_sources_payload

        await interaction.response.send_message(
            await build_sources_payload(),
            ephemeral=True,
        )

    @btd6_app_group.command(
        name="strategies",
        description="List strategy memory entries available in this guild.",
    )
    async def btd6_strategies_slash(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command requires a guild context.",
                ephemeral=True,
            )
            return
        from cogs.btd6._builders import build_strategies_payload

        await interaction.response.send_message(
            await build_strategies_payload(interaction.guild.id),
            ephemeral=True,
        )

    @btd6_app_group.command(
        name="source-health",
        description="BTD6 source registry freshness overview.",
    )
    async def btd6_source_health_slash(
        self,
        interaction: discord.Interaction,
        limit: int = 25,
    ) -> None:
        from cogs.btd6._builders import build_source_health_embed

        await interaction.response.send_message(
            embed=await build_source_health_embed(limit=limit),
            ephemeral=True,
        )

    @btd6_app_group.command(
        name="latest-data",
        description="Newest fact envelope per entity_kind.",
    )
    async def btd6_latest_data_slash(
        self,
        interaction: discord.Interaction,
    ) -> None:
        from cogs.btd6._builders import build_latest_data_embed

        await interaction.response.send_message(
            embed=await build_latest_data_embed(),
            ephemeral=True,
        )

    @btd6_app_group.command(
        name="grounding",
        description="Grounding facts that fed an AI response.",
    )
    async def btd6_grounding_slash(
        self,
        interaction: discord.Interaction,
        message_id: str,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command requires a guild context.",
                ephemeral=True,
            )
            return
        try:
            mid = int(message_id)
        except ValueError:
            await interaction.response.send_message(
                f"❌ Invalid message_id: {message_id!r}",
                ephemeral=True,
            )
            return
        from cogs.btd6._builders import build_grounding_embed

        payload = await build_grounding_embed(interaction.guild.id, mid)
        if isinstance(payload, str):
            await interaction.response.send_message(payload, ephemeral=True)
        else:
            await interaction.response.send_message(embed=payload, ephemeral=True)

    @btd6_app_group.command(
        name="browse",
        description="Browse published BTD6 strategies.",
    )
    async def btd6_browse_slash(
        self,
        interaction: discord.Interaction,
        limit: int = 10,
    ) -> None:
        from views.btd6.strategy_browse import build_browse_embed

        await interaction.response.send_message(
            embed=await build_browse_embed(limit=limit),
            ephemeral=True,
        )

    @btd6_app_group.command(
        name="mine",
        description="List my own strategy submissions in this guild.",
    )
    async def btd6_mine_slash(
        self,
        interaction: discord.Interaction,
        limit: int = 10,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command requires a guild context.",
                ephemeral=True,
            )
            return
        from views.btd6.strategy_browse import build_mine_embed

        await interaction.response.send_message(
            embed=await build_mine_embed(
                interaction.guild.id,
                interaction.user.id,
                limit=limit,
            ),
            ephemeral=True,
        )

    @btd6_app_group.command(
        name="strategy",
        description="Show one strategy in detail.",
    )
    async def btd6_strategy_slash(
        self,
        interaction: discord.Interaction,
        strategy_id: int,
    ) -> None:
        from views.btd6.strategy_browse import build_detail_embed

        viewer_guild = interaction.guild.id if interaction.guild else None
        payload = await build_detail_embed(strategy_id, viewer_guild_id=viewer_guild)
        if isinstance(payload, str):
            await interaction.response.send_message(payload, ephemeral=True)
        else:
            await interaction.response.send_message(embed=payload, ephemeral=True)

    @btd6_app_group.command(
        name="strategy-audit",
        description="Per-strategy audit log.",
    )
    async def btd6_strategy_audit_slash(
        self,
        interaction: discord.Interaction,
        strategy_id: int,
    ) -> None:
        from views.btd6.strategy_browse import build_audit_embed

        await interaction.response.send_message(
            embed=await build_audit_embed(strategy_id),
            ephemeral=True,
        )

    @btd6_app_group.command(
        name="submit",
        description="Submit a BTD6 strategy.",
    )
    async def btd6_submit_slash(self, interaction: discord.Interaction) -> None:
        from views.btd6.strategy_submit import StrategySubmitModal

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Submitting a strategy requires a guild context.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(StrategySubmitModal())

    @btd6_app_group.command(
        name="pending",
        description="List pending strategy submissions (staff-only).",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def btd6_pending_slash(
        self,
        interaction: discord.Interaction,
        limit: int = 5,
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command requires a guild context.",
                ephemeral=True,
            )
            return
        from cogs.btd6._builders import build_pending_review_payload

        payload = await build_pending_review_payload(
            interaction.guild.id,
            limit=limit,
        )
        if isinstance(payload, str):
            await interaction.response.send_message(payload, ephemeral=True)
            return
        # First embed responds; remaining embeds go as followups.
        first_embed, first_view = payload[0]
        await interaction.response.send_message(
            embed=first_embed,
            view=first_view,
            ephemeral=True,
        )
        for embed, view in payload[1:]:
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)

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
