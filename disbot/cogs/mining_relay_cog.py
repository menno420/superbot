"""Mining relay cog — the ~60 s mineverse snapshot push loop (glue only).

Owns the delivery cadence of the mineverse READ relay (FLAG 1): every
:data:`_RELAY_INTERVAL_SECONDS` it projects the configured guild's mining
state through :mod:`services.mining_snapshot_service` and POSTs it to the
relay URL.  Content-free and command-free (the ``media_maintenance_cog``
pattern) — the projection and transport live in the service; this cog only
schedules them.

**Dormant by default**: with ``MINING_SNAPSHOT_RELAY_URL`` /
``MINING_SNAPSHOT_RELAY_GUILD_ID`` unset (every current deploy) the loop
never starts and the bot's behaviour is byte-identical — one startup log
line states which mode the relay is in, so an operator can confirm the
armed/off state from the boot log alone.  On-demand refreshes go through
:meth:`MiningRelayCog.push_now` (the same seam the loop uses), ready for a
future owner surface without a second code path.
"""

from __future__ import annotations

import logging

from discord.ext import commands, tasks

from core.runtime.guild_resources import resolve_member
from services import mining_snapshot_service

logger = logging.getLogger("bot.cogs.mining_relay")

# The contract's suggested cadence ("target every 60 s",
# docs/mining-data-contract.md § Delivery expectations).
_RELAY_INTERVAL_SECONDS = 60


class MiningRelayCog(commands.Cog):
    """Schedules the bot→web mining snapshot push (mineverse FLAG 1)."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        config = mining_snapshot_service.relay_config()
        if config is None:
            logger.info(
                "mining relay: OFF (set %s + %s to enable)",
                mining_snapshot_service.ENV_RELAY_URL,
                mining_snapshot_service.ENV_RELAY_GUILD_ID,
            )
            return
        logger.info(
            "mining relay: ENABLED — guild %s → %s every %ds",
            config.guild_id,
            config.url,
            _RELAY_INTERVAL_SECONDS,
        )
        self._push_loop.start()

    async def cog_unload(self) -> None:
        self._push_loop.cancel()

    def _display_name(self, guild_id: int, suid: str) -> str | None:
        """Guild display name for *suid* from the member cache, or None."""
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return None
        member = resolve_member(guild, suid)
        return member.display_name if member else None

    async def push_now(self) -> bool:
        """Build + push one snapshot now; False when off or the push failed.

        The single seam both the loop and any future on-demand surface use.
        Never raises — a failed projection or push is logged and absorbed
        (the relay degrades the website, never the bot).
        """
        config = mining_snapshot_service.relay_config()
        if config is None:
            return False
        try:
            snapshot = await mining_snapshot_service.build_snapshot(
                config.guild_id,
                resolve_display_name=lambda suid: self._display_name(
                    config.guild_id,
                    suid,
                ),
            )
        except Exception:  # noqa: BLE001 — a projection bug must not kill the loop
            logger.exception("mining relay: snapshot build failed")
            return False
        return await mining_snapshot_service.push_snapshot(snapshot, config.url)

    @tasks.loop(seconds=_RELAY_INTERVAL_SECONDS)
    async def _push_loop(self) -> None:
        await self.push_now()

    @_push_loop.before_loop
    async def _before_push_loop(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MiningRelayCog(bot))
