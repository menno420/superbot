"""BTD6 Assistant — mother cog.

Owns the BTD6 subsystem identity (the ``btd6`` / ``btd6menu`` entry points,
the ``BTD6PanelView`` main menu, and the schema + ingestion-supervisor
lifecycle), and **registers the unified command tree**.

The whole BTD6 command surface lives under one ``/btd6`` (``!btd6``) tree
(owner request, 2026-06-24): everyday lookups flat (``/btd6 income`` …) and the
bigger buckets nested (``/btd6 strat`` / ``/btd6 ops`` / ``/btd6 events``). That
tree is module-level in :mod:`cogs.btd6._unified` — discord.py can't share one
``app_commands.Group`` across cogs, and one mega-cog would blow the 800-LOC
ceiling (``tests/unit/invariants/test_cog_size.py``) — and this cog registers it
in :func:`setup`. The old per-group cogs remain only as *hidden* prefix aliases
so existing muscle-memory keeps working:

* :mod:`cogs.btd6_reference_cog` — hidden ``!btd6ref`` alias (tower/hero/round/…).
* :mod:`cogs.btd6_events_cog` — hidden ``!btd6events`` alias (live events, …).
* :mod:`cogs.btd6_strategy_cog` — hidden ``!btd6strat`` alias (strategy memory).
* :mod:`cogs.btd6_ops_cog` — hidden ``!btd6ops`` alias (ingestion operations).

This cog itself keeps only the panel opener (``!btd6menu`` / ``/btd6menu``) and
the lifecycle; the ``btd6`` group and every subcommand are the unified tree.

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

from cogs.btd6 import _unified
from cogs.btd6.stage import STAGE_NAME as BTD6_STAGE_NAME
from core.runtime import message_pipeline, tasks
from core.runtime.interaction_helpers import safe_defer, safe_followup
from services import (
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
        # deploy with no manual `!btd6 ops seed-data`. Never fires for the file
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
                    "`!btd6 ops seed-data` to update.",
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
                "store serves %s — run `!btd6 ops seed-data` to update "
                "(applies immediately, no restart needed).",
                bundled,
                served,
            )
        else:
            # Same-version drift (no game_version bump): strict-(b) auto-seed
            # won't fire and the version-based check above can't see it, so a
            # buff/stat edit would stay stale silently. Surface it (warn only).
            changed = btd6_data_service.content_drift()
            if changed:
                logger.warning(
                    "BTD6 data drift: %d committed data file(s) differ from the "
                    "served store at the same version — run `!btd6 ops seed-data` "
                    "to apply (e.g. %s).",
                    len(changed),
                    ", ".join(changed[:3]) + ("…" if len(changed) > 3 else ""),
                )

        await btd6_ingestion_supervisor.start_supervisor()

    async def cog_unload(self) -> None:
        """Defensive unregister so reload/test cycles stay clean."""
        message_pipeline.unregister(BTD6_STAGE_NAME)
        await btd6_ingestion_supervisor.stop_supervisor()
        tasks.cancel_by_prefix("btd6_ingestion:")

    # ------------------------------------------------------------------
    # Prefix command — the panel opener. The rest of the !btd6 surface
    # (income/round/strat/ops/events/…) is the module-level unified tree
    # in cogs.btd6._unified, registered in setup().
    # ------------------------------------------------------------------

    @commands.command(name="btd6menu")
    async def btd6menu(self, ctx: commands.Context) -> None:
        """Open the BTD6 panel (alias for ``!btd6``)."""
        await ctx.send(embed=await build_btd6_panel_embed(), view=BTD6PanelView())

    # ------------------------------------------------------------------
    # App command — the panel opener. A slash group can't be invoked
    # directly, so /btd6menu opens the panel; the /btd6 <action> tree
    # lives in cogs.btd6._unified (registered in setup()).
    # ------------------------------------------------------------------

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
    # The unified /btd6 + !btd6 tree (income/round/strat/ops/events/…) is
    # module-level — discord.py can't cleanly share one app_commands.Group
    # across cogs — so the mother cog registers it once here.
    _unified.register(bot)


async def teardown(bot: commands.Bot) -> None:
    _unified.teardown(bot)
