"""Creature workflow service — the audited write boundary for catching.

The runtime side of ``docs/planning/creature-game-design-and-sim-2026-06-20.md``
(Q-0186/Q-0187): a player goes out, a wild creature appears (rarity-weighted),
and a catch roll (``rarity base × a small player-level bonus``) decides whether it
joins their collection. **Leveling reuses the shared ``game_xp`` track** (the
plan's directive) — the player's creature level is derived from their per-game
``GAME_CREATURE`` xp; level only nudges catch odds (there is no level gate).

Mirrors ``services/fishing_workflow.py`` (RS02 / Q-0071): on a successful catch
the collection-log write + the xp award commit inside ONE ``db.transaction()``
from conn-aware ``utils/db`` primitives; EventBus emission happens **after**
commit. A *failed* catch (the creature flees) writes nothing and awards no xp.
The encounter/catch math is pure (``utils/creatures``); this service sequences the
read → roll → atomic writes → post-commit events.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from services import game_xp_service
from utils import db
from utils.creatures import Creature, attempt_catch, roll_encounter

logger = logging.getLogger("bot.creature_workflow")


def creature_level_from_xp(creature_xp: int) -> int:
    """The player's creature level (1-based) from their ``GAME_CREATURE`` xp.

    Reuses the shared game-xp level curve (``db.level_progress``) rather than
    inventing a parallel system. Unlike fishing there is no MAX cap — creature
    level is open-ended (it feeds PvE/collection prestige and, later, the
    level-normalized PvP seed).
    """
    level_index, _, _ = db.level_progress(max(0, creature_xp))
    return 1 + level_index


@dataclass(frozen=True)
class CatchResult:
    """One ``!catch`` attempt — the wild creature and the outcome."""

    #: The creature that appeared (``None`` only if the catalog failed to load).
    creature: Creature | None
    #: True when the catch succeeded and the creature joined the collection.
    caught: bool = False
    #: True when this was the player's first-ever catch of this creature.
    is_new: bool = False
    #: The player's creature level after the attempt (1-based).
    creature_level: int = 1
    #: True when a successful catch crossed a shared game level.
    leveled_up: bool = False
    #: Inline shared-game level-up notice (set only when that crossed a level).
    xp_note: str | None = None


async def catch(user_id: int, guild_id: int) -> CatchResult:
    """One outing: spawn a wild creature, roll the catch, log + award atomically."""
    xp_map = await db.get_game_xp(user_id, guild_id)
    creature_xp_before = xp_map.get(game_xp_service.GAME_CREATURE, 0)
    level = creature_level_from_xp(creature_xp_before)

    encounter = roll_encounter()
    if encounter is None:
        # Catalog failed to load — never write, surface an honest empty result.
        logger.error("creatures: no encounterable creature (catalog empty?)")
        return CatchResult(creature=None, creature_level=level)

    creature = encounter.creature
    if not attempt_catch(creature, level):
        # The creature fled — no write, no xp, but report the sighting.
        return CatchResult(creature=creature, caught=False, creature_level=level)

    # A first-ever catch of this creature is a "new dex entry" — read the prior
    # collection before the write so the cog can celebrate it.
    collection_before = await db.get_creature_collection(user_id, guild_id)
    is_new = creature.name not in collection_before

    async with db.transaction() as conn:
        await db.record_creature_catch(user_id, guild_id, creature.name, conn=conn)
        award = await game_xp_service.award(
            guild_id,
            user_id,
            game=game_xp_service.GAME_CREATURE,
            action="catch",
            conn=conn,
        )
    if award is not None:
        await game_xp_service.emit_award_events(award)

    creature_xp_after = award.game_total if award is not None else creature_xp_before
    return CatchResult(
        creature=creature,
        caught=True,
        is_new=is_new,
        creature_level=creature_level_from_xp(creature_xp_after),
        leveled_up=award.leveled_up if award is not None else False,
        xp_note=award.note if award is not None and award.leveled_up else None,
    )
