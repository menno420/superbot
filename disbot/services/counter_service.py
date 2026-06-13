"""Counter service — count computation + the channel-rename orchestration.

Server counters (owner decision Q-0110).  Where welcome *greets* members, this
keeps designated channel names showing a live server stat (total / humans /
bots).  The cog (:mod:`cogs.counters_cog`) drives :func:`sync_guild` from a
periodic ``tasks.loop`` — **never** per join — because Discord rate-limits
channel renames to ~2 per 10 minutes per channel; a lazy loop + change-detection
(rename only when the name actually differs) keeps every guild comfortably under
that cap (see ``docs/operations/discord-platform-limits.md`` and the
``mock_counters`` exhibit note).

Design (family-plan §3): off by default, fail-open (a count or rename fault on
one guild/channel never stops the loop), one advisory ``counters.updated`` event.
The counts are computed from the live member cache — no DB writes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import discord

from core.runtime import resources
from services import counter_config

logger = logging.getLogger("bot.services.counters")

EVT_COUNTERS_UPDATED = "counters.updated"


@dataclass(frozen=True)
class CounterCounts:
    """The three live server stats for one guild."""

    total: int
    humans: int
    bots: int

    def for_kind(self, kind: str) -> int:
        """Return the count for a counter ``kind`` (0 for an unknown kind)."""
        return {
            counter_config.KIND_TOTAL: self.total,
            counter_config.KIND_HUMANS: self.humans,
            counter_config.KIND_BOTS: self.bots,
        }.get(kind, 0)


def compute_counts(guild: Any) -> CounterCounts:
    """Compute the live member stats for ``guild`` from the member cache.

    ``total`` prefers ``guild.member_count`` (always populated); ``bots`` is
    counted from the member cache and ``humans`` is the remainder, so the three
    stay internally consistent even when the cache is partially chunked.
    """
    members = list(getattr(guild, "members", ()) or ())
    bots = sum(1 for m in members if getattr(m, "bot", False))
    total = int(getattr(guild, "member_count", 0) or len(members))
    humans = max(total - bots, 0)
    return CounterCounts(total=total, humans=humans, bots=bots)


def _resolve_guild_channel(guild: discord.Guild, channel_id: int) -> Any | None:
    """Return the bound channel when it exists and is renamable, else None."""
    channel = resources.resolve_channel(guild, channel_id=channel_id)
    if isinstance(channel, discord.abc.GuildChannel):
        return channel
    return None


async def _rename_if_changed(channel: Any, desired: str) -> bool:
    """Rename ``channel`` to ``desired`` when it differs — fail-safe + counted.

    Returns True only when an actual rename was issued (change-detection skips a
    no-op, which is what keeps the loop under Discord's rename rate limit).
    """
    if getattr(channel, "name", None) == desired:
        return False
    try:
        await channel.edit(name=desired, reason="Server counter update")
    except discord.Forbidden:
        logger.warning("counters: missing Manage Channels permission for a counter")
        return False
    except discord.HTTPException as exc:
        logger.warning("counters: HTTP error renaming counter channel: %s", exc)
        return False
    except Exception:  # noqa: BLE001 — fail-safe wrapper
        logger.exception("counters: unexpected error renaming counter channel")
        return False
    return True


async def sync_guild(guild: discord.Guild) -> int:
    """Update every bound counter channel for ``guild``; return renames issued.

    Fully fail-safe: a config-read fault returns 0 (the loop continues to the
    next guild), and each channel is renamed in isolation.  Emits the advisory
    ``counters.updated`` event when at least one channel changed.
    """
    try:
        policy = await counter_config.load_policy(guild.id)
    except Exception:  # noqa: BLE001 — fail open on any config-read fault
        logger.exception("counters: load_policy failed for guild=%s", guild.id)
        return 0

    if not policy.any_bound:
        return 0

    counts = compute_counts(guild)
    renamed = 0
    for kind, channel_id, template in policy.active:
        channel = _resolve_guild_channel(guild, channel_id)
        if channel is None:
            continue
        desired = counter_config.render_counter_name(template, counts.for_kind(kind))
        if await _rename_if_changed(channel, desired):
            renamed += 1

    if renamed:
        await _emit_updated(guild, renamed)
    return renamed


async def _emit_updated(guild: discord.Guild, renamed: int) -> None:
    """Emit the advisory ``counters.updated`` event (best-effort)."""
    from core.events import bus

    try:
        await bus.emit(EVT_COUNTERS_UPDATED, guild_id=guild.id, renamed=renamed)
    except Exception:  # noqa: BLE001 — advisory event; never fail the loop
        logger.exception("counters: updated emit failed")
