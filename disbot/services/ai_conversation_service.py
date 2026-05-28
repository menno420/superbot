"""Short-term per-channel conversation memory.

In-process only — :doc:`docs/decisions/001-no-redis-backed-state`
forbids Redis-backed state. Each channel keeps a rolling buffer of
recent ``ConversationTurn`` rows so the AI gateway can ground replies
in the channel's prior context.

The natural-language stage (and the operator-facing
``ai_conversation_service``-aware diagnostic commands) consume this
through :func:`recent_turns` with an explicit window. Cache writes
flow through :func:`append`; cache flushes flow through
:func:`forget_guild` (called from ``disbot/guild_lifecycle.py``) and
:func:`forget_channel` (called from ``!ai forget``).

The cache always retains at least :data:`MIN_FLOOR_TURNS` per channel
regardless of the configured window so the bot has a basic
conversational handle even when an operator leaves memory "off".

Memory bounds:

* per-channel deque cap: :data:`_PER_CHANNEL_CAP`
* tracked-channel cap: :data:`_CHANNEL_LRU_CAP`

The channel-level LRU evicts the least-recently-used channel buffer
when a new (guild, channel) pair pushes us past the cap. This keeps
total in-process retention bounded even on a very busy host.
"""

from __future__ import annotations

import time
from collections import OrderedDict, deque
from dataclasses import dataclass, field

# Always-on minimum: even when an operator sets the memory window to
# 0 (off) the bot still retains the last N messages per channel so a
# basic "what did the previous person ask?" handle works out-of-box.
MIN_FLOOR_TURNS: int = 3

# Cap per channel — large enough for a 2-hour window of moderate
# chatter without bloating, small enough that even ``_CHANNEL_LRU_CAP``
# busy channels stay well below 20 000 stored turns process-wide.
_PER_CHANNEL_CAP: int = 200

# Cap on how many distinct (guild, channel) buffers we track.
_CHANNEL_LRU_CAP: int = 50


@dataclass(frozen=True)
class ConversationTurn:
    user_id: int
    role: str  # 'user' | 'assistant'
    text: str
    # Wall-clock timestamp (epoch seconds). Defaulted so existing
    # callers that don't pass it still work; the natural-language
    # stage always passes time.time().
    ts: float = field(default_factory=time.time)
    # Discord display name as the user appeared at message time
    # (per-guild nickname if set, else global name, else username).
    # ``ai_instruction_service`` sanitizes and uses this as the
    # bracketed speaker label so the model can refer to people by
    # name instead of opaque ``user_A`` pseudonyms. Defaults to None
    # for backwards compat with callers that don't yet pass it; in
    # that case the assembler falls back to a pseudonym.
    display_name: str | None = None


# OrderedDict so we can do channel-level LRU eviction cheaply.
_BUFFERS: OrderedDict[tuple[int, int], deque[ConversationTurn]] = OrderedDict()


def _buffer_for(guild_id: int, channel_id: int) -> deque[ConversationTurn]:
    key = (guild_id, channel_id)
    if key in _BUFFERS:
        # Touch — mark as most-recently used.
        _BUFFERS.move_to_end(key)
        return _BUFFERS[key]
    # New buffer; evict oldest if we are at the cap.
    if len(_BUFFERS) >= _CHANNEL_LRU_CAP:
        _BUFFERS.popitem(last=False)
    buf: deque[ConversationTurn] = deque(maxlen=_PER_CHANNEL_CAP)
    _BUFFERS[key] = buf
    return buf


def append(
    guild_id: int,
    channel_id: int,
    *,
    user_id: int,
    role: str,
    text: str,
    ts: float | None = None,
    display_name: str | None = None,
) -> None:
    """Append one turn to the channel's rolling buffer.

    Empty ``text`` and non-``str`` values are dropped silently so the
    central NL stage can call this unconditionally without per-message
    pre-validation. ``ts`` defaults to ``time.time()``. ``display_name``
    is the Discord-side speaker name and is preserved verbatim here;
    sanitization happens later in ``ai_instruction_service.assemble``
    so the buffer carries raw data and rendering decisions stay in one
    place.
    """
    if not isinstance(text, str):
        return
    text = text.strip()
    if not text:
        return
    buf = _buffer_for(guild_id, channel_id)
    buf.append(
        ConversationTurn(
            user_id=user_id,
            role=role,
            text=text,
            ts=ts if ts is not None else time.time(),
            display_name=display_name,
        ),
    )


def recent_turns(
    guild_id: int,
    channel_id: int,
    *,
    window_minutes: int = 0,
    min_floor: int = MIN_FLOOR_TURNS,
    limit: int = _PER_CHANNEL_CAP,
) -> list[ConversationTurn]:
    """Return recent turns for the channel, applying window + floor.

    Semantics:

    * ``window_minutes == 0`` → return up to ``min_floor`` most recent
      turns (the always-on minimum).
    * ``window_minutes > 0`` → return turns whose ``ts`` is within
      ``window_minutes`` of now, but never fewer than ``min_floor``
      (so short windows on a quiet channel still surface the same
      handle the "off" mode would).
    * ``limit`` caps the returned list size regardless.
    """
    key = (guild_id, channel_id)
    buf = _BUFFERS.get(key)
    if not buf:
        return []
    # Touch on read so heavily-trafficked channels stay warm in the LRU.
    _BUFFERS.move_to_end(key)

    all_turns = list(buf)
    if window_minutes <= 0:
        out = all_turns[-min_floor:]
        return out[-limit:]

    cutoff = time.time() - (window_minutes * 60)
    windowed = [t for t in all_turns if t.ts >= cutoff]
    if len(windowed) < min_floor:
        windowed = all_turns[-min_floor:]
    return windowed[-limit:]


def forget_guild(guild_id: int) -> int:
    """Drop every buffer scoped to ``guild_id``; returns the count."""
    drop = [key for key in _BUFFERS if key[0] == guild_id]
    for key in drop:
        del _BUFFERS[key]
    return len(drop)


def forget_channel(guild_id: int, channel_id: int) -> int:
    """Drop the buffer for one (guild, channel); returns 1 or 0."""
    key = (guild_id, channel_id)
    if key in _BUFFERS:
        del _BUFFERS[key]
        return 1
    return 0


@dataclass(frozen=True)
class CacheStats:
    """Body-free snapshot of cache occupancy for operator diagnostics."""

    channel_count: int
    total_turns: int
    per_channel_cap: int = _PER_CHANNEL_CAP
    channel_lru_cap: int = _CHANNEL_LRU_CAP


def stats() -> CacheStats:
    """Return a body-free snapshot of cache occupancy.

    Never returns message text — only counts. Safe to render in
    public-facing diagnostics.
    """
    total = sum(len(buf) for buf in _BUFFERS.values())
    return CacheStats(
        channel_count=len(_BUFFERS),
        total_turns=total,
    )


def channel_stats(guild_id: int) -> dict[int, int]:
    """Per-channel turn counts for a guild. No bodies."""
    return {
        channel_id: len(buf)
        for (gid, channel_id), buf in _BUFFERS.items()
        if gid == guild_id
    }


def _reset_for_tests() -> None:
    _BUFFERS.clear()


__all__ = [
    "CacheStats",
    "ConversationTurn",
    "MIN_FLOOR_TURNS",
    "append",
    "channel_stats",
    "forget_channel",
    "forget_guild",
    "recent_turns",
    "stats",
]
