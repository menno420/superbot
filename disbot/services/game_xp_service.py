"""Game-XP service — the shared cross-game progression track (§7.4).

The second XP track the owner taste table (brainstorm §7.2) calls for:
**chat XP** keeps driving the auto-role tiers untouched; **game XP** is a
separate, guild-scoped track shared by *all* game cogs, whose function is
**prestige + leaderboard** (and, later, capped skill points) — never
content gates.

Mirrors :mod:`services.xp_service`: this service is the only path through
which production code grants game XP, so every grant goes through one
central award policy (XP ≈ effort/risk; money moves award nothing, so
sell/buy can't farm it) and emits the catalogued events.

Central award policy (v1 — tunable constants, not per-game code):

==============  ======================  =====================================
action          XP                      attribution
==============  ======================  =====================================
mine            3 + depth               ``GAME_MINING``
harvest         2                       ``GAME_MINING``
explore         4 + depth               ``GAME_MINING``
depth_record    25 (one-time per band)  ``GAME_MINING``
craft           8                       ``GAME_CRAFTING``
quick_craft     8                       ``GAME_CRAFTING``
repair          3                       ``GAME_CRAFTING``
sell / buy      0                       (money moves never award XP)
==============  ======================  =====================================

**Daily soft cap** (per game, per UTC day): the first
:data:`DAILY_SOFT_CAP` XP award at full rate; beyond it awards are scaled
by :data:`CAPPED_RATE` (floor 1 — soft, never zero), so no single game is
the optimal infinite farm.  The day counter is read-compute-write inside
the caller's transaction; the rare concurrent overshoot is acceptable
game-state slack (ADR-002 spirit).

**Levels are shared and derived**: ``level = level_progress(SUM(xp))``
using the existing chat-XP curve (``5·lvl² + 50·lvl + 100``) — one curve
bot-wide, no second formula, no stored level column.

Transaction contract (Q-0071): :func:`award` takes the workflow's open
``conn`` so the XP write commits atomically with the action that earned
it; the **caller emits the events after commit** via
:func:`emit_award_events` (the ``economy_service.transfer`` precedent).
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from core.events import bus
from utils import db

if TYPE_CHECKING:
    import asyncpg

logger = logging.getLogger("bot.game_xp_service")

# Event names — also listed in core/events_catalogue.KNOWN_EVENTS.
EVT_GAME_XP_AWARDED = "game_xp.awarded"
EVT_GAME_LEVEL_UP = "game_xp.level_up"

# Game identifiers (the `game` column). New games add a constant here and
# call award() — no schema or service change needed.
GAME_MINING = "mining"
GAME_CRAFTING = "crafting"
GAME_FISHING = "fishing"

# Per-game, per-UTC-day full-rate budget; beyond it, awards scale by
# CAPPED_RATE (floor 1). One constant to retune or disable (set to 0 to
# cap nothing... set very high to disable the cap).
DAILY_SOFT_CAP = 400
CAPPED_RATE = 0.25

# The central award table — action name → base XP (depth-scaled actions
# add the player's current band).
_AWARDS: dict[str, int] = {
    "mine": 3,
    "harvest": 2,
    "explore": 4,
    "fish": 3,
    "depth_record": 25,
    "craft": 8,
    "quick_craft": 8,
    "repair": 3,
}
_DEPTH_SCALED = {"mine", "explore"}


@dataclass(frozen=True)
class GameXpAward:
    """Result of one award — carries everything the caller needs to render
    an inline note and to emit the post-commit events.
    """

    guild_id: int
    user_id: int
    game: str
    action: str
    amount: int
    game_total: int
    shared_total: int
    level: int
    leveled_up: bool

    @property
    def note(self) -> str:
        """The inline level-up notice (render only when ``leveled_up``)."""
        return f"🎉 Game level up — you reached **Level {self.level}**!"


def xp_for_action(action: str, *, depth: int = 0) -> int:
    """The award table, pure: base XP (+ depth for depth-scaled actions)."""
    base = _AWARDS.get(action, 0)
    if base and action in _DEPTH_SCALED:
        return base + max(0, depth)
    return base


async def award(
    guild_id: int,
    user_id: int,
    *,
    game: str,
    action: str,
    depth: int = 0,
    conn: asyncpg.Connection | None = None,
) -> GameXpAward | None:
    """Grant the action's XP; return the award, or None for 0-XP actions.

    Pass the owning workflow's *conn* so the grant commits atomically with
    the action that earned it.  **No events are emitted here** — call
    :func:`emit_award_events` after the transaction commits.
    """
    amount = xp_for_action(action, depth=depth)
    if amount <= 0:
        return None
    today = datetime.datetime.now(datetime.timezone.utc).date()
    row = await db.get_game_xp_row(user_id, guild_id, game, conn=conn)
    day_xp_today = row["day_xp"] if row["day"] == today else 0
    if day_xp_today >= DAILY_SOFT_CAP:
        amount = max(1, int(amount * CAPPED_RATE))
    shared_before = await db.get_total_xp(user_id, guild_id, conn=conn)
    game_total = await db.add_game_xp(
        user_id,
        guild_id,
        game,
        amount,
        day=today,
        conn=conn,
    )
    shared_after = shared_before + amount
    level_before, _, _ = db.level_progress(shared_before)
    level_after, _, _ = db.level_progress(shared_after)
    return GameXpAward(
        guild_id=guild_id,
        user_id=user_id,
        game=game,
        action=action,
        amount=amount,
        game_total=game_total,
        shared_total=shared_after,
        level=level_after,
        leveled_up=level_after > level_before,
    )


async def emit_award_events(award_result: GameXpAward) -> None:
    """Emit the catalogued events for one award — AFTER the owning
    transaction has committed (never inside it).
    """
    await bus.emit(
        EVT_GAME_XP_AWARDED,
        guild_id=award_result.guild_id,
        user_id=award_result.user_id,
        game=award_result.game,
        action=award_result.action,
        amount=award_result.amount,
        total=award_result.shared_total,
    )
    if award_result.leveled_up:
        await bus.emit(
            EVT_GAME_LEVEL_UP,
            guild_id=award_result.guild_id,
            user_id=award_result.user_id,
            level=award_result.level,
            total=award_result.shared_total,
        )


async def level_info(guild_id: int, user_id: int) -> tuple[int, int, int]:
    """``(level, into_level, needed_for_next)`` from the shared total."""
    total = await db.get_total_xp(user_id, guild_id)
    return db.level_progress(total)


__all__ = [
    "EVT_GAME_XP_AWARDED",
    "EVT_GAME_LEVEL_UP",
    "GAME_MINING",
    "GAME_CRAFTING",
    "DAILY_SOFT_CAP",
    "CAPPED_RATE",
    "GameXpAward",
    "xp_for_action",
    "award",
    "emit_award_events",
    "level_info",
]
