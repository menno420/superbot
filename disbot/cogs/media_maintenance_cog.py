"""Media maintenance cog — the shared-platform owner of YouTube cache retention.

P0-2 / Q-0099: the video-reference cache (``youtube_video_cache``) gives each
row a *logical* TTL, but reads only **ignore** expired rows — nothing ever
physically removed them (``purge_expired_video_cache`` had no caller), so
transcript excerpts and cached metadata lingered in storage indefinitely.  This
cog is the lifecycle owner the media readiness map asked for: a slow
``tasks.loop`` that physically purges expired rows.

It is deliberately **content-free** — it logs only a row count, never any video
content.  Media has no public cog/command (it is a service consumed by the AI
pipeline), so this glue-only cog exists purely to own the retention task; it is
registered in the shared platform layer per ADR-007, not under AI or BTD6.
"""

from __future__ import annotations

import logging

from discord.ext import commands, tasks

from services import video_reference_cache_service, youtube_diagnostics

logger = logging.getLogger("bot.cogs.media_maintenance")

# Expired rows already stop serving (reads filter ``expires_at > now()``); this
# loop only reclaims storage.  A 6-hour cadence bounds the post-expiry retention
# window to <=6h while keeping DB churn negligible (the table is tiny + bounded
# by the 2-video-per-message cap).
_PURGE_LOOP_HOURS = 6


class MediaMaintenanceCog(commands.Cog):
    """Owns physical retention/purge of the YouTube reference cache."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        self._purge_loop.start()

    async def cog_unload(self) -> None:
        self._purge_loop.cancel()

    @tasks.loop(hours=_PURGE_LOOP_HOURS)
    async def _purge_loop(self) -> None:
        try:
            purged = await video_reference_cache_service.purge_expired()
        except Exception:  # noqa: BLE001 — a transient DB blip must not kill the loop
            logger.exception("media: expired video-cache purge failed")
            youtube_diagnostics.record_purge(0, ok=False)
            return
        youtube_diagnostics.record_purge(purged, ok=True)
        if purged:
            logger.info("media: purged %d expired video-cache row(s)", purged)

    @_purge_loop.before_loop
    async def _before_purge_loop(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    from services import diagnostics_service

    # Register the content-free media diagnostics provider so the
    # process-local provider-outcome counters + last-purge status show in
    # ``!platform runtime`` and back the ``!platform media`` surface.
    diagnostics_service.register("media", youtube_diagnostics.snapshot)
    await bot.add_cog(MediaMaintenanceCog(bot))
