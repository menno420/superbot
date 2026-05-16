"""XP service — the single authority for XP awards and level-up events.

Mirrors :mod:`services.economy_service`: the service is the only path
through which production code should grant XP, so every grant goes
through one place that emits the catalogued ``EVT_XP_AWARDED`` and
(when applicable) ``EVT_LEVEL_UP`` events.

Subscribers — panel-refresh, future analytics, possible XP-audit log —
react to these events instead of polling the DB.

Public API
----------
- ``award(guild_id, user_id, amount, *, source, now=None)``
  Atomic XP increment via the existing ``db.add_xp`` upsert + level
  recalculation.  Returns ``XpAward`` (new_xp, new_level, leveled_up).
  Emits ``EVT_XP_AWARDED`` always and ``EVT_LEVEL_UP`` on level boundary
  crossings.

The existing ``db.add_xp`` remains the implementation primitive — the
service wraps it.  ``db.add_xp`` is kept callable directly only for
unit tests and the legacy on_message path in xp_cog; new code should
go through this module.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from core.events import bus
from utils import db

logger = logging.getLogger("bot.xp_service")

EVT_XP_AWARDED = "xp.awarded"
EVT_LEVEL_UP = "xp.level_up"


@dataclass(frozen=True)
class XpAward:
    """Result of an XP grant."""

    new_xp: int
    new_level: int
    leveled_up: bool
    delta: int
    source: str


async def award(
    guild_id: int,
    user_id: int,
    amount: int,
    *,
    source: str,
    now: int | None = None,
) -> XpAward:
    """Grant *amount* XP to *user_id* in *guild_id* and emit events.

    Args:
        guild_id: discord guild.
        user_id: target member.
        amount: XP to grant.  Must be > 0.
        source: short label for the grant ("message", "work:carpenter",
            "daily", …).  Surfaces in the event payload and aids
            downstream attribution.
        now: optional Unix timestamp for the cooldown column.  Defaults
            to ``int(time.time())``.

    Returns:
        :class:`XpAward` describing the post-award state.

    Raises:
        ValueError: if ``amount <= 0``.
    """
    if amount <= 0:
        msg = f"award amount must be positive, got {amount}"
        raise ValueError(msg)
    ts = now if now is not None else int(time.time())
    new_xp, new_level, leveled_up = await db.add_xp(user_id, guild_id, amount, ts)

    await bus.emit(
        EVT_XP_AWARDED,
        guild_id=guild_id,
        user_id=user_id,
        delta=amount,
        new_xp=new_xp,
        new_level=new_level,
        source=source,
    )
    if leveled_up:
        await bus.emit(
            EVT_LEVEL_UP,
            guild_id=guild_id,
            user_id=user_id,
            new_level=new_level,
            source=source,
        )

    return XpAward(
        new_xp=new_xp,
        new_level=new_level,
        leveled_up=leveled_up,
        delta=amount,
        source=source,
    )
