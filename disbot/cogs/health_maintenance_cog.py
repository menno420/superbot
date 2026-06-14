"""Health maintenance cog — owns periodic operational-health findings retention.

P1-2: ``health_findings_service.run_retention()`` rolls resolved/ignored finding
detail older than the 30-day TTL into the aggregates table and prunes it. That
sweep previously ran **only once at startup** (``bot1._report_startup_health``),
so a long-lived replica — the production posture — never re-swept and
resolved/ignored rows accumulated for the lifetime of the process.

This glue cog is the lifecycle owner the health readiness map asked for: a slow
``tasks.loop`` that re-runs retention on a daily cadence, mirroring
``MediaMaintenanceCog`` (the YouTube-cache retention owner). The startup sweep
stays — it covers the just-recorded boot snapshot — and this loop keeps it
operational thereafter.

It is deliberately **content-free**: it logs only a pruned row count, never any
finding content (which is already scrubbed at record time anyway). The cog holds
no state and adds no command; it exists purely to own the retention task.
"""

from __future__ import annotations

import logging

from discord.ext import commands, tasks

from services import health_findings_service

logger = logging.getLogger("bot.cogs.health_maintenance")

# A 24-hour cadence is ample for a 30-day TTL: it bounds the post-TTL retention
# overhang to <=1 day while keeping DB churn negligible (the findings tables are
# tiny and bounded by the per-fingerprint dedupe key).
_RETENTION_LOOP_HOURS = 24


class HealthMaintenanceCog(commands.Cog):
    """Owns the periodic operational-health findings retention sweep."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self._retention_loop.start()

    async def cog_unload(self) -> None:
        self._retention_loop.cancel()

    @tasks.loop(hours=_RETENTION_LOOP_HOURS)
    async def _retention_loop(self) -> None:
        # run_retention is itself best-effort (swallows DB errors and returns 0),
        # but guard the call too so nothing can kill the loop task.
        try:
            pruned = await health_findings_service.run_retention()
        except Exception:  # noqa: BLE001 — a transient blip must not kill the loop
            logger.exception("health: findings retention sweep failed")
            return
        if pruned:
            logger.info("health: pruned %d expired finding row(s)", pruned)

    @_retention_loop.before_loop
    async def _before_retention_loop(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HealthMaintenanceCog(bot))
