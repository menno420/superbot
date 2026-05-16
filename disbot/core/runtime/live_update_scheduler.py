"""EventBus-driven panel refresh scheduler.

Cogs register (subsystem, event, refresh_fn) triples.  When an event fires on
the EventBus, the scheduler finds all matching panel anchors and calls
refresh_fn to produce a new embed/view, then edits the Discord message.

Edits are rate-limited to one per channel per _MIN_EDIT_INTERVAL seconds to
avoid hitting Discord's 5-edits-per-5-seconds bucket.

Public surface:
    register_refresh(subsystem, event, refresh_fn) → None
    setup(bot)                                     → None

refresh_fn signature:
    async (bot, user_id, guild_id, channel_id) -> tuple[discord.Embed, discord.ui.View] | None

Returning None from refresh_fn skips the edit for that anchor.

Events must include at least ``user_id: int`` and ``guild_id: int`` in their
payload for the scheduler to route them to the right anchor.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any

import discord

from core.events import bus
from core.runtime import tasks
from services import metrics as _metrics
from utils import db

if TYPE_CHECKING:
    from discord.ext import commands

logger = logging.getLogger("bot.runtime.scheduler")

# Minimum seconds between edits to the same Discord channel.
_MIN_EDIT_INTERVAL: float = 1.0

# (guild_id, channel_id) → monotonic timestamp of last edit.
# Keyed by (guild_id, channel_id) so guild_lifecycle.teardown() can drop entries
# deterministically for a departed guild without touching other guilds' state.
_last_edit: dict[tuple[int, int], float] = {}

# subsystem → [(event_name, refresh_fn), ...]
_REGISTRATIONS: dict[str, list[tuple[str, Callable]]] = {}

# event_name → [subsystem, ...]
_EVENT_SUBSYSTEMS: dict[str, list[str]] = {}

# Events already subscribed on the bus (avoid double-subscription)
_SUBSCRIBED_EVENTS: set[str] = set()

_bot: commands.Bot | None = None

RefreshFn = Callable[
    ["commands.Bot", int, int, int],
    Coroutine[Any, Any, tuple[discord.Embed, discord.ui.View] | None],
]


def register_refresh(subsystem: str, event: str, refresh_fn: RefreshFn) -> None:
    """Register *refresh_fn* to run when *event* fires for *subsystem* panels.

    May be called before ``setup()`` — subscriptions are queued and take
    effect once the bus is active.
    """
    _REGISTRATIONS.setdefault(subsystem, []).append((event, refresh_fn))
    _EVENT_SUBSYSTEMS.setdefault(event, [])
    if subsystem not in _EVENT_SUBSYSTEMS[event]:
        _EVENT_SUBSYSTEMS[event].append(subsystem)

    if event not in _SUBSCRIBED_EVENTS:
        _SUBSCRIBED_EVENTS.add(event)
        # Capture event in closure to avoid late-binding issues.
        _event = event

        async def _handler(**payload: Any) -> None:
            await _on_event(_event, **payload)

        bus.on(event, _handler)
        logger.debug("Scheduler subscribed to EventBus event %r", event)


async def _on_event(event: str, **payload: Any) -> None:
    """Dispatch a fired event to all matching subsystem anchors."""
    if _bot is None:
        return

    user_id: int | None = payload.get("user_id")
    guild_id: int | None = payload.get("guild_id")

    if not user_id or not guild_id:
        logger.debug(
            "Scheduler skipping event %r — missing user_id or guild_id in payload",
            event,
        )
        return

    for subsystem in _EVENT_SUBSYSTEMS.get(event, []):
        refresh_fns = [
            fn for ev, fn in _REGISTRATIONS.get(subsystem, []) if ev == event
        ]
        if not refresh_fns:
            continue

        try:
            anchors = await db.get_user_subsystem_anchors(user_id, guild_id, subsystem)
        except Exception as exc:
            logger.error(
                "Scheduler failed to fetch anchors for user=%d subsystem=%r: %s",
                user_id,
                subsystem,
                exc,
            )
            continue

        for anchor in anchors:
            for refresh_fn in refresh_fns:
                tasks.spawn(
                    f"panel_refresh:{subsystem}:{anchor['message_id']}",
                    _refresh_panel(
                        _bot,
                        refresh_fn,
                        user_id,
                        guild_id,
                        anchor["channel_id"],
                        anchor["message_id"],
                        subsystem,
                    ),
                )


async def _refresh_panel(
    bot: commands.Bot,
    refresh_fn: RefreshFn,
    user_id: int,
    guild_id: int,
    channel_id: int,
    message_id: int,
    subsystem: str = "unknown",
) -> None:
    """Fetch a new embed/view and edit the panel message, respecting rate limits."""
    now = time.monotonic()
    wait = _MIN_EDIT_INTERVAL - (now - _last_edit.get((guild_id, channel_id), 0.0))
    if wait > 0:
        await asyncio.sleep(wait)

    try:
        result = await refresh_fn(bot, user_id, guild_id, channel_id)
    except Exception as exc:
        _metrics.panel_refresh_total.labels(
            subsystem=subsystem,
            result="refresh_fn_error",
        ).inc()
        logger.error(
            "refresh_fn failed for user=%d channel=%d: %s",
            user_id,
            channel_id,
            exc,
        )
        return

    if result is None:
        _metrics.panel_refresh_total.labels(
            subsystem=subsystem,
            result="skipped",
        ).inc()
        return

    embed, view = result
    channel = bot.get_channel(channel_id)
    if channel is None or not isinstance(channel, discord.abc.Messageable):
        _metrics.panel_refresh_total.labels(
            subsystem=subsystem,
            result="channel_missing",
        ).inc()
        return

    try:
        message = await channel.fetch_message(message_id)
        await message.edit(embed=embed, view=view)
        _last_edit[(guild_id, channel_id)] = time.monotonic()
        _metrics.panel_refresh_total.labels(subsystem=subsystem, result="ok").inc()
        logger.debug(
            "Panel refreshed | user=%d | channel=%d | message=%d",
            user_id,
            channel_id,
            message_id,
        )
    except discord.NotFound as exc:
        _metrics.panel_refresh_total.labels(
            subsystem=subsystem,
            result="message_not_found",
        ).inc()
        logger.debug("Panel refresh skipped — message gone: %s", exc)
    except discord.Forbidden as exc:
        _metrics.panel_refresh_total.labels(
            subsystem=subsystem,
            result="forbidden",
        ).inc()
        logger.debug("Panel refresh skipped — forbidden: %s", exc)
    except discord.HTTPException as exc:
        _metrics.panel_refresh_total.labels(
            subsystem=subsystem,
            result="http_error",
        ).inc()
        logger.warning("Panel refresh HTTP error for message %d: %s", message_id, exc)


def setup(bot: commands.Bot) -> None:
    """Wire the scheduler to the bot instance.  Call once after bot is ready."""
    global _bot
    _bot = bot
    logger.info(
        "Live update scheduler ready — %d registration(s) across %d event(s)",
        sum(len(v) for v in _REGISTRATIONS.values()),
        len(_SUBSCRIBED_EVENTS),
    )


def forget_guild(guild_id: int) -> int:
    """Drop _last_edit throttle entries owned by a departed guild.

    Cleanup is deterministic and always occurs regardless of dict size — there
    is no size-gated bypass.  The (guild_id, channel_id) keying makes this O(n)
    over _last_edit but bounded by the number of channels the guild ever
    refreshed.  Returns the number of entries removed.
    """
    stale = [k for k in _last_edit if k[0] == guild_id]
    for k in stale:
        _last_edit.pop(k, None)
    return len(stale)
