"""User-level permission glue for the AI natural-language stage.

There is no per-user AI policy table in this initiative — "user-level
checks" means XP-level lookup, cooldown identity, fresh-user
mention allowance, and audit actor identity. This service is the
thin layer that fetches those facts so the resolver and the stage
do not import ``services.xp_service`` directly.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger("bot.services.ai_permission")


@dataclass(frozen=True)
class UserPermissionSnapshot:
    user_id: int
    guild_id: int
    level: int
    is_fresh_user: bool


# Process-local cooldown tracker: per (guild_id, user_id) → last reply
# epoch seconds. Respect ADR-001 (no Redis-backed state) — this is
# in-memory only and resets on restart, which is acceptable for
# cooldown enforcement.
_LAST_REPLY_AT: dict[tuple[int, int], float] = defaultdict(float)
_FRESH_ALLOWANCE_USED: dict[tuple[int, int], int] = defaultdict(int)


async def snapshot(guild_id: int, user_id: int) -> UserPermissionSnapshot:
    """Return the XP level + fresh-user marker for ``user_id``.

    The XP service is the canonical source for level lookups. A
    user with no XP row yet is treated as level 0 and ``is_fresh_user
    = True``; the cooldown / mention-allowance rules in the resolver
    decide whether that prevents a reply.
    """
    level = 0
    is_fresh = True
    try:
        from services import xp_service

        record = await xp_service.get_user_record(guild_id, user_id)
        if record is not None:
            level = int(getattr(record, "level", 0) or 0)
            is_fresh = level == 0 and int(getattr(record, "xp", 0) or 0) == 0
    except Exception as exc:  # noqa: BLE001 — defensive
        logger.debug(
            "ai_permission_service: xp lookup failed (%s); treating "
            "guild=%s user=%s as fresh",
            exc,
            guild_id,
            user_id,
        )
    return UserPermissionSnapshot(
        user_id=user_id,
        guild_id=guild_id,
        level=level,
        is_fresh_user=is_fresh,
    )


def is_on_cooldown(guild_id: int, user_id: int, cooldown_seconds: int) -> bool:
    if cooldown_seconds <= 0:
        return False
    last = _LAST_REPLY_AT[(guild_id, user_id)]
    return (time.time() - last) < cooldown_seconds


def mark_reply_sent(guild_id: int, user_id: int) -> None:
    _LAST_REPLY_AT[(guild_id, user_id)] = time.time()


def fresh_allowance_remaining(
    guild_id: int,
    user_id: int,
    allowance: int,
) -> int:
    used = _FRESH_ALLOWANCE_USED[(guild_id, user_id)]
    return max(0, int(allowance) - used)


def consume_fresh_allowance(guild_id: int, user_id: int) -> None:
    _FRESH_ALLOWANCE_USED[(guild_id, user_id)] += 1


def _reset_for_tests() -> None:
    _LAST_REPLY_AT.clear()
    _FRESH_ALLOWANCE_USED.clear()


__all__ = [
    "UserPermissionSnapshot",
    "consume_fresh_allowance",
    "fresh_allowance_remaining",
    "is_on_cooldown",
    "mark_reply_sent",
    "snapshot",
]
