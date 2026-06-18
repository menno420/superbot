"""Fishing workflow service — the audited write boundary for fishing.

Mirrors ``services/mining_workflow.py`` (RS02 / Q-0071): every fishing
mutation that touches more than one row — here the catch log + the coin
balance + the game-XP track — runs inside ONE ``db.transaction()`` composed
from the conn-aware ``utils/db`` primitives.  Coins move through the audited
``economy_service.credit_in_txn`` seam (never a raw balance write), and
EventBus emission happens **after** commit, never inside the transaction (the
``economy_service.transfer`` precedent).

The catch math is pure (``utils/fishing``); this service only sequences the
roll → the atomic writes → the post-commit events.

Plan: ``docs/planning/fishing-ecosystem-plan-2026-06-18.md`` (PR 1).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from core.events import bus
from services import economy_service, game_xp_service
from utils import db
from utils.fishing import Catch, roll_catch

logger = logging.getLogger("bot.fishing_workflow")

#: The economy-audit reason stamped on a fishing coin reward.
FISH_REASON = "fishing_catch"


@dataclass(frozen=True)
class FishResult:
    """One cast — the rolled catch plus the coins + XP it earned."""

    catch: Catch
    coins: int
    new_balance: int
    #: Inline level-up notice (set only when the award crossed a level).
    xp_note: str | None = None


async def fish(user_id: int, guild_id: int) -> FishResult:
    """One cast: roll a catch, then log it + pay coins + award XP — atomically."""
    catch = roll_catch()
    async with db.transaction() as conn:
        await db.record_catch(
            user_id,
            guild_id,
            catch.species.name,
            catch.weight,
            catch.value,
            conn=conn,
        )
        new_balance = await economy_service.credit_in_txn(
            conn,
            guild_id,
            user_id,
            catch.value,
            reason=FISH_REASON,
            actor_id=user_id,
        )
        xp = await game_xp_service.award(
            guild_id,
            user_id,
            game=game_xp_service.GAME_FISHING,
            action="fish",
            conn=conn,
        )
    await bus.emit(
        economy_service.EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=catch.value,
        new_balance=new_balance,
        reason=FISH_REASON,
    )
    if xp is not None:
        await game_xp_service.emit_award_events(xp)
    return FishResult(
        catch=catch,
        coins=catch.value,
        new_balance=new_balance,
        xp_note=xp.note if xp is not None and xp.leveled_up else None,
    )
