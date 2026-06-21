"""BTD6 Assistant — mother cog.

Owns the BTD6 subsystem identity (the ``btd6`` / ``btd6menu`` entry points,
the ``BTD6PanelView`` main menu, and the schema + ingestion-supervisor
lifecycle). The bulk of the command surface lives in sibling cogs to keep
this file under the 800-LOC ceiling
(``tests/unit/invariants/test_cog_size.py``):

* :mod:`cogs.btd6_reference_cog` — ``!btd6ref`` tower/hero/round/relic/ct.
* :mod:`cogs.btd6_events_cog` — ``!btd6events`` live events, leaderboards,
  source diagnostics, grounding.
* :mod:`cogs.btd6_strategy_cog` — ``!btd6strat`` strategy browse/submit/review
  and ``why-no-response``.
* :mod:`cogs.btd6_ops_cog` — ``!btd6ops`` ingestion operations.

This cog keeps the panel (bare ``!btd6`` / ``/btd6menu``), the core
diagnostics (``status`` / ``diagnostics`` / ``ask`` / ``test-intent``), and
``ctteam`` (a prefix-only admin utility — pasting a long bracket URL is the
natural prefix surface, so it intentionally has no slash twin).

Architecture:

* The cog never writes to the AI Platform's policy / instruction tables.
  Natural-language reply eligibility is owned by
  :mod:`services.ai_natural_language_policy`; BTD6 reads from
  :mod:`services.ai_decision_audit_service` only.
* All BTD6 facts come from the BTD6 service layer; nothing in the cog
  invents BTD6 data.
* Commands match the SuperBot convention (prefix + slash side by side via
  :mod:`cogs.btd6._builders`; both forms gated as user-tier per the
  SUBSYSTEMS entry).
"""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs.btd6 import _builders
from cogs.btd6._embeds import (
    build_diagnostics_embed,
    build_status_embed,
    build_test_intent_embed,
)
from cogs.btd6._embeds import response_to_embed as _response_to_embed
from cogs.btd6._reply import reply_ephemeral
from cogs.btd6.stage import STAGE_NAME as BTD6_STAGE_NAME
from core.runtime import message_pipeline, tasks
from core.runtime.interaction_helpers import safe_defer, safe_followup
from services import (
    btd6_ai_service,
    btd6_data_service,
    btd6_ingestion_supervisor,
    btd6_version_announce,
)
from views.btd6.panel import BTD6PanelView, build_btd6_panel_embed

logger = logging.getLogger("bot")


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------


class BTD6Cog(commands.Cog):
    """Deterministic BTD6 assistant — panel, core diagnostics, lifecycle."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        """Register the BTD6 SubsystemSchema; do NOT register a passive stage.

        M2 introduced the central natural-language stage (order=70).
        M5 retired the short-lived ``AI_BTD6_VIA_ROUTER`` env var: the
        BTD6 passive stage stays unregistered unconditionally so the
        central stage is the only passive replier. ``!btd6strat
        why-no-response`` reads the AI decision audit table directly,
        filtered to ``task='btd6.answer'``.
        """
        from cogs.btd6.schemas import register_schemas

        register_schemas()
        message_pipeline.unregister(BTD6_STAGE_NAME)

        # Subscribe the version-announcement service to btd6.version_detected.
        # Subscribe-once (idempotent across reloads), and wired regardless of
        # data availability so an enabled patch-notes source can still notify.
        btd6_version_announce.setup(self.bot)

        # Warm the deterministic-data cache before starting ingestion. This is
        # a no-op for the local file provider; for the cloud provider it
        # fetches fixtures into the local cache. If required data is
        # unreachable with no cache, degrade gracefully — log, skip the
        # ingestion supervisor (so it doesn't error-loop), and leave the cogs
        # loaded so the panel still works — rather than crashing the bot.
        if not await btd6_data_service.warm_provider():
            logger.warning(
                "BTD6 data unavailable (%s) — skipping ingestion supervisor; "
                "BTD6 lookups will be unavailable until data is reachable.",
                btd6_data_service.data_source_label(),
            )
            return

        # Auto-seed (Q-0077(b), 2026-06-19 owner decision): when the deployed
        # files carry a strictly NEWER game version than the postgres store
        # serves, re-seed the store from them so a version bump goes live on
        # deploy with no manual `!btd6ops seed-data`. Never fires for the file
        # backend, an equal/newer store (never clobbers a deliberately-newer
        # one), or a same-version data edit (those still need manual seed-data).
        # Defensive: a failure logs and serves the existing store.
        if btd6_data_service.auto_seed_enabled() and (
            btd6_data_service.bundled_newer_than_served()
        ):
            try:
                count = await btd6_data_service.seed_postgres_from_files()
                logger.info(
                    "BTD6 auto-seed: deployed files are a newer game version than "
                    "the store — synced %d blobs (no manual seed-data needed).",
                    count,
                )
            except Exception:
                logger.warning(
                    "BTD6 auto-seed failed; serving the existing store. Run "
                    "`!btd6ops seed-data` to update.",
                    exc_info=True,
                )

        # Data PRs update the bundled files only — a postgres/cloud store
        # keeps serving its old copy until re-seeded, invisibly (live,
        # 2026-06-10: code auto-deployed at 55.1 while the blob store served
        # 55.0). Surface the drift loudly at every boot; `!btd6 status`
        # shows the same warning.
        drift = btd6_data_service.served_data_drift()
        if drift is not None:
            served, bundled = drift
            logger.warning(
                "BTD6 data drift: the deployed files carry %s but the active "
                "store serves %s — run `!btd6ops seed-data` to update "
                "(applies immediately, no restart needed).",
                bundled,
                served,
            )

        await btd6_ingestion_supervisor.start_supervisor()

    async def cog_unload(self) -> None:
        """Defensive unregister so reload/test cycles stay clean."""
        message_pipeline.unregister(BTD6_STAGE_NAME)
        await btd6_ingestion_supervisor.stop_supervisor()
        tasks.cancel_by_prefix("btd6_ingestion:")

    # ------------------------------------------------------------------
    # Prefix commands
    # ------------------------------------------------------------------

    @commands.group(name="btd6", invoke_without_command=True)
    async def btd6_group(self, ctx: commands.Context) -> None:
        """Open the BTD6 panel."""
        await ctx.send(embed=await build_btd6_panel_embed(), view=BTD6PanelView())

    @btd6_group.command(name="status")  # type: ignore[arg-type]
    async def btd6_status(self, ctx: commands.Context) -> None:
        await ctx.send(embed=await build_status_embed())

    @btd6_group.command(name="diagnostics")  # type: ignore[arg-type]
    async def btd6_diagnostics(self, ctx: commands.Context) -> None:
        await ctx.send(embed=build_diagnostics_embed())

    @btd6_group.command(name="ask")  # type: ignore[arg-type]
    async def btd6_ask(self, ctx: commands.Context, *, question: str) -> None:
        """Deterministic Q&A. Module 5 adds optional AI augmentation."""
        response = await btd6_ai_service.answer_question(question)
        await ctx.send(embed=_response_to_embed(response))

    @btd6_group.command(name="test-intent")  # type: ignore[arg-type]
    async def btd6_test_intent(self, ctx: commands.Context, *, text: str) -> None:
        await ctx.send(embed=build_test_intent_embed(text))

    @btd6_group.command(name="ctteam")  # type: ignore[arg-type]
    async def btd6_ctteam(self, ctx: commands.Context, *, arg: str = "") -> None:
        """View or set this server's CT team (paste the bracket group id / URL)."""
        embed, view = await _builders.handle_ctteam(ctx, arg)
        if view is None:
            await ctx.send(embed=embed)
            return
        message = await ctx.send(embed=embed, view=view)
        view.message = message  # disable-on-timeout edits the right message

    @commands.command(name="btd6menu")
    async def btd6menu(self, ctx: commands.Context) -> None:
        """Open the BTD6 panel (alias for ``!btd6``)."""
        await ctx.send(embed=await build_btd6_panel_embed(), view=BTD6PanelView())

    # ------------------------------------------------------------------
    # App commands — mirror the prefix surface.
    # ------------------------------------------------------------------

    btd6_app_group = app_commands.Group(
        name="btd6",
        description="BTD6 Assistant — panel, status, ask, diagnostics.",
    )

    @btd6_app_group.command(name="status", description="BTD6 assistant status.")
    async def btd6_status_slash(self, interaction: discord.Interaction) -> None:
        await reply_ephemeral(interaction, build_status_embed())

    @btd6_app_group.command(
        name="diagnostics",
        description="BTD6 dataset diagnostics.",
    )
    async def btd6_diagnostics_slash(self, interaction: discord.Interaction) -> None:
        # Sync builder — safe to respond directly without defer.
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
        if not await safe_defer(interaction, ephemeral=True):
            return
        response = await btd6_ai_service.answer_question(question)
        await safe_followup(
            interaction,
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
        # Sync resolver work — safe to respond directly without defer.
        await interaction.response.send_message(
            embed=build_test_intent_embed(text),
            ephemeral=True,
        )

    @app_commands.command(name="btd6menu", description="Open the BTD6 panel.")
    async def btd6menu_slash(self, interaction: discord.Interaction) -> None:
        if not await safe_defer(interaction, ephemeral=True):
            return
        embed = await build_btd6_panel_embed()
        await safe_followup(
            interaction,
            embed=embed,
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
        return await build_btd6_panel_embed(), BTD6PanelView()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BTD6Cog(bot))
