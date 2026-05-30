"""Discord-aware chat-memory orchestration.

Sits between :mod:`services.ai_conversation_service` (pure in-process
buffer) and the central natural-language stage. Owns:

* Reading the per-guild memory settings (window minutes, channel-scan
  enabled).
* The fallback path that scans recent Discord history via
  ``TextChannel.history()`` and seeds the buffer when the cache holds
  fewer turns than the configured window requires.

The conversation service stays Discord-free; this module is the only
seam that talks to ``discord.TextChannel``. Keeping the split means
unit tests for the buffer never need a mocked Discord client.

Privacy: the scan reads message bodies that the bot has the
``read_message_history`` permission for, but it never persists them.
Everything goes into the in-process buffer, which is dropped on
restart and on ``forget_guild`` / ``forget_channel``.
"""

from __future__ import annotations

import logging
from typing import Any

from services import ai_conversation_service
from utils.db.settings import get_setting
from utils.settings_keys import (
    AI_MEMORY_CHANNEL_SCAN_ENABLED,
    AI_MEMORY_WINDOW_MINUTES,
)

logger = logging.getLogger("bot.services.ai_memory")


# Hard ceiling on a single channel-scan fetch. The Discord history
# call is rate-limited; we cap so a single chatty channel can't
# bloat one reply path. 30 covers ~ 2h of moderate activity.
_SCAN_LIMIT: int = 30

# Upper bound on how many recent turns we hand the prompt assembler,
# independent of the configured window. The per-channel buffer holds up
# to 200 turns; on a busy channel a wide window would otherwise dump all
# of them into a single request, inflating cost and risking truncation
# of the actual question. The most recent N turns carry the conversational
# context that matters; older turns add noise.
_MAX_PROMPT_TURNS: int = 40

# Validated window choices — mirrors the SettingSpec in
# ``cogs/ai/schemas.py``. Anything else from the DB is treated as
# disabled.
_ALLOWED_WINDOWS: frozenset[int] = frozenset({0, 15, 30, 60, 120})


async def read_memory_settings(guild_id: int) -> tuple[int, bool]:
    """Read ``(window_minutes, channel_scan_enabled)`` for a guild.

    Returns the safe defaults ``(0, False)`` for unknown / unset rows
    and clamps the window to :data:`_ALLOWED_WINDOWS`.
    """
    raw_window = await get_setting(guild_id, AI_MEMORY_WINDOW_MINUTES, default="0")
    raw_scan = await get_setting(
        guild_id,
        AI_MEMORY_CHANNEL_SCAN_ENABLED,
        default="False",
    )
    try:
        window = int(raw_window)
    except (TypeError, ValueError):
        window = 0
    if window not in _ALLOWED_WINDOWS:
        window = 0
    scan_enabled = str(raw_scan).strip().lower() in {"true", "1", "yes", "on"}
    return window, scan_enabled


async def gather_recent_turns(
    *,
    guild_id: int,
    channel_id: int,
    channel: Any = None,
    bot_user_id: int | None = None,
) -> list[ai_conversation_service.ConversationTurn]:
    """Get the recent turns the AI stage should see, with fallback scan.

    1. Reads the per-guild settings.
    2. Asks the conversation service for turns within the window
       (always retains :data:`MIN_FLOOR_TURNS` regardless).
    3. If the buffer is short and ``channel_scan_enabled=True`` and a
       ``channel`` is provided, scans Discord history and re-asks.

    The scan is best-effort — if the channel object lacks history()
    or raises (missing permission, network error), the helper logs at
    debug level and returns whatever the buffer already had.
    """
    window, scan_enabled = await read_memory_settings(guild_id)
    turns = ai_conversation_service.recent_turns(
        guild_id,
        channel_id,
        window_minutes=window,
        limit=_MAX_PROMPT_TURNS,
    )
    # Decide whether the buffer is short enough to warrant a scan.
    # We only scan when the operator has opted in AND the buffer
    # really does hold fewer than the floor. (Empty buffers are the
    # obvious case; the "buffer < min_floor on a non-trivial window"
    # case also qualifies because the floor's purpose is exactly to
    # not return zero context.)
    if (
        scan_enabled
        and channel is not None
        and len(turns) < ai_conversation_service.MIN_FLOOR_TURNS
    ):
        try:
            await _seed_from_history(
                guild_id=guild_id,
                channel_id=channel_id,
                channel=channel,
                bot_user_id=bot_user_id,
            )
        except Exception as exc:  # noqa: BLE001 — best-effort fallback
            logger.debug(
                "ai_memory: channel scan failed for guild=%s channel=%s: %s",
                guild_id,
                channel_id,
                exc,
            )
        # Re-read after the seed.
        turns = ai_conversation_service.recent_turns(
            guild_id,
            channel_id,
            window_minutes=window,
        )
    return turns


async def _seed_from_history(
    *,
    guild_id: int,
    channel_id: int,
    channel: Any,
    bot_user_id: int | None,
) -> int:
    """Scan recent channel history and populate the in-process buffer.

    Returns the count of turns appended. Skips system messages and
    empty bodies; classifies the bot's own messages as ``role='assistant'``
    when ``bot_user_id`` is known.
    """
    history_fn = getattr(channel, "history", None)
    if history_fn is None:
        return 0
    appended = 0
    # ``oldest_first=True`` so the buffer ends up chronologically
    # ordered after the seed (the buffer is a FIFO deque under the
    # hood).
    async for msg in history_fn(limit=_SCAN_LIMIT, oldest_first=True):
        author_id = getattr(getattr(msg, "author", None), "id", None)
        body = getattr(msg, "content", "") or ""
        if not body or author_id is None:
            continue
        # Discard messages that look like commands so the cache doesn't
        # treat operator prefixes as conversation context.
        if body.startswith("!") or body.startswith("/"):
            continue
        role = "assistant" if (bot_user_id and author_id == bot_user_id) else "user"
        ts = getattr(getattr(msg, "created_at", None), "timestamp", None)
        try:
            ts_value = float(ts()) if callable(ts) else None
        except Exception:  # noqa: BLE001 — defensive
            ts_value = None
        # Only carry display_name for non-bot turns; assistant turns
        # always render as ``[assistant]`` in the assembled prompt.
        display_name = (
            None
            if role == "assistant"
            else getattr(getattr(msg, "author", None), "display_name", None)
        )
        ai_conversation_service.append(
            guild_id,
            channel_id,
            user_id=author_id,
            role=role,
            text=body,
            ts=ts_value,
            display_name=display_name,
        )
        appended += 1
    return appended


__all__ = [
    "gather_recent_turns",
    "read_memory_settings",
]
