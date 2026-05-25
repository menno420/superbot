"""Short-term per-channel conversation memory.

In-process only — :doc:`docs/decisions/001-no-redis-backed-state`
forbids Redis-backed state. Each channel keeps the last N message
turns so the gateway has a tiny rolling context.

Memory is cleared on bot restart and on guild leave (via
:func:`forget_guild`, called from ``disbot/guild_lifecycle.py``).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

# Tunable defaults. We deliberately keep this small to stay well
# below provider context windows and to avoid retaining old data.
_MAX_TURNS_PER_CHANNEL = 6
_BUFFERS: dict[tuple[int, int], deque[ConversationTurn]] = {}


@dataclass(frozen=True)
class ConversationTurn:
    user_id: int
    role: str  # 'user' | 'assistant'
    text: str


def append(
    guild_id: int,
    channel_id: int,
    *,
    user_id: int,
    role: str,
    text: str,
) -> None:
    buf = _BUFFERS.setdefault(
        (guild_id, channel_id),
        deque(maxlen=_MAX_TURNS_PER_CHANNEL),
    )
    buf.append(ConversationTurn(user_id=user_id, role=role, text=text))


def recent_turns(guild_id: int, channel_id: int) -> list[ConversationTurn]:
    buf = _BUFFERS.get((guild_id, channel_id))
    return list(buf) if buf else []


def forget_guild(guild_id: int) -> int:
    """Drop every buffer scoped to ``guild_id``; returns the count."""
    drop = [key for key in _BUFFERS if key[0] == guild_id]
    for key in drop:
        del _BUFFERS[key]
    return len(drop)


def _reset_for_tests() -> None:
    _BUFFERS.clear()


__all__ = [
    "ConversationTurn",
    "append",
    "forget_guild",
    "recent_turns",
]
