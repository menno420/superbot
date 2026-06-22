"""Fishing workflow service — the audited write boundary for fishing.

Owner design Q-0175 (``docs/planning/fishing-open-world-expansion-plan-2026-06-18.md``):
fishing v1 is a **level-gated catch** — the player's fishing level (derived from
their per-game ``GAME_FISHING`` xp, reusing the shared ``game_xp`` system) gates
which size band of fish they can catch; each level unlocks +3 bigger fish.
**Fish value/use is an explicitly OPEN owner question, so v1 pays no coins** —
the reward is progression (level up → unlock bigger fish) + the collection log.

Mirrors ``services/mining_workflow.py`` (RS02 / Q-0071): the catch-log write +
the xp award commit inside ONE ``db.transaction()`` from conn-aware ``utils/db``
primitives; EventBus emission happens **after** commit. The catch math is pure
(``utils/fishing``); this service sequences the read → roll → atomic writes →
post-commit events.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from services import game_xp_service
from utils import db
from utils.fishing import MAX_LEVEL, Catch, roll_catch

logger = logging.getLogger("bot.fishing_workflow")


def fishing_level_from_xp(fishing_xp: int) -> int:
    """The player's fishing level (1…MAX_LEVEL) from their fishing xp total.

    Reuses the shared game-xp level curve (``db.level_progress``) rather than
    inventing a parallel system (the owner's "reuse game_xp" directive), capped
    at MAX_LEVEL (= 7 size bands). The *shape* of leveling — a dedicated rod-tier
    ladder vs. this skill-xp derivation — is an OPEN owner question (Q-0175); this
    is the deferrable v1 choice.
    """
    level_index, _, _ = db.level_progress(max(0, fishing_xp))
    return min(MAX_LEVEL, 1 + level_index)


@dataclass(frozen=True)
class FishResult:
    """One cast — the rolled catch plus the progression it produced."""

    catch: Catch | None
    #: The player's fishing level after this cast (1…MAX_LEVEL).
    fishing_level: int
    #: True when this cast crossed a fishing level → bigger fish just unlocked.
    unlocked_bigger: bool = False
    #: Inline shared-game level-up notice (set only when that crossed a level).
    xp_note: str | None = None


@dataclass(frozen=True)
class Cast:
    """A cast in progress — the fish on the line, *before* it is committed.

    The minigame (``views/fishing``) rolls the catch at cast time so it knows
    what is biting, then commits it only if the player successfully reels in
    (owner decision 2026-06-22: a missed reel = the fish gets away, no write).
    The instant ``fish()`` below rolls + commits in one go for the legacy path.
    """

    catch: Catch | None
    #: The player's fishing level at cast time (gates the roll + the catch math).
    level_before: int


async def roll_cast(user_id: int, guild_id: int) -> Cast:
    """Read the player's level and roll a catch **without writing anything**.

    The read-only half of a cast: the minigame calls this when the line goes
    out, holds the rolled :class:`Cast`, and only calls :func:`commit_catch`
    once the reel succeeds. Returns ``Cast(catch=None, …)`` if the catalog
    failed to load (no species) — the caller surfaces an honest empty result.
    """
    xp_map = await db.get_game_xp(user_id, guild_id)
    fishing_xp_before = xp_map.get(game_xp_service.GAME_FISHING, 0)
    level_before = fishing_level_from_xp(fishing_xp_before)
    catch = roll_catch(level_before)
    if catch is None:
        logger.error("fishing: no catchable species (catalog empty?)")
    return Cast(catch=catch, level_before=level_before)


async def commit_catch(user_id: int, guild_id: int, cast: Cast) -> FishResult:
    """Commit a successfully-reeled cast: log it + grant the item + award xp.

    The audited write boundary (RS02 / Q-0071): the catch-log write, the
    inventory grant, and the xp award all run on ONE workflow-owned
    ``db.transaction()`` connection; the xp event emits only after commit. A
    ``cast`` with no ``catch`` (empty catalog) writes nothing.
    """
    catch = cast.catch
    level_before = cast.level_before
    if catch is None:
        return FishResult(catch=None, fishing_level=level_before)

    async with db.transaction() as conn:
        await db.record_catch(user_id, guild_id, catch.species.name, conn=conn)
        # The caught fish is now a tangible inventory item (owner decision
        # 2026-06-22): sellable for coins via the market, and cookable into food
        # at a campfire (mining_workflow.cook). The catch-log row above stays the
        # dex/leaderboard record; this grant makes the fish usable — same atomic
        # catch transaction, conn-composed (RS02).
        await db.update_mining_item(
            str(user_id),
            guild_id,
            catch.species.name,
            1,
            conn=conn,
        )
        award = await game_xp_service.award(
            guild_id,
            user_id,
            game=game_xp_service.GAME_FISHING,
            action="fish",
            conn=conn,
        )
    if award is not None:
        await game_xp_service.emit_award_events(award)
        level_after = fishing_level_from_xp(award.game_total)
    else:
        level_after = level_before
    return FishResult(
        catch=catch,
        fishing_level=level_after,
        unlocked_bigger=level_after > level_before,
        xp_note=award.note if award is not None and award.leveled_up else None,
    )


async def fish(user_id: int, guild_id: int) -> FishResult:
    """One instant cast: roll a catch from the unlocked band + commit it.

    The legacy / non-interactive path (kept for the shared-game seam and tests).
    The interactive minigame instead calls :func:`roll_cast` then
    :func:`commit_catch` so the write happens only on a successful reel.
    """
    cast = await roll_cast(user_id, guild_id)
    return await commit_catch(user_id, guild_id, cast)
