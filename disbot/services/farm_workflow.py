"""Farm workflow service — the audited write boundary for the idle chicken farm.

Owner-directed task "Idle egg/chicken farm": the bot's first idle activity. Hens
lay eggs over time (pure accrual in :mod:`utils.farm`), you **collect** them for
coins + game XP, and you spend coins on more **chickens** (faster lay rate) and a
bigger **coop** (larger egg cap).

Mirrors :mod:`services.fishing_workflow` / :mod:`services.mining_workflow`
(RS02 / Q-0071): every coin-moving op runs the farm-row write + the coin leg
inside ONE ``db.transaction()`` connection via the conn-aware ``utils/db`` and
``economy_service.*_in_txn`` primitives; the EventBus emission happens **after**
commit. The accrual/pricing math is pure (:mod:`utils.farm`); this service
sequences read → settle → atomic writes → post-commit events.

A subtlety the settle math forces: **buying a chicken settles eggs at the OLD
flock size first**, persisting ``(eggs, now)`` before the new count applies — so
the faster rate only counts going forward, never retroactively.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from core.events import bus
from services import economy_service, game_xp_service
from utils import db
from utils import farm as farm_mod

logger = logging.getLogger("bot.farm_workflow")

#: Audit/event reason tags (mirrors "<game>:<action>").
COLLECT_REASON = "farm:collect"
BUY_CHICKEN_REASON = "farm:buy_chicken"
UPGRADE_COOP_REASON = "farm:upgrade_coop"


async def get_state(user_id: int, guild_id: int) -> farm_mod.FarmState:
    """The player's *settled* farm state (read-only — writes nothing).

    Accrual is pure (a stored value + a timestamp), so showing the panel never
    needs to persist; only the coin-moving ops below settle-and-write.
    """
    chickens, eggs, ts, coop = await db.get_chicken_farm(user_id, guild_id)
    return farm_mod.settle(
        farm_mod.FarmState(chickens, eggs, ts, coop),
        int(time.time()),
    )


@dataclass(frozen=True)
class CollectResult:
    """The outcome of a collect — a flag, a message, and the new balance."""

    success: bool
    message: str
    eggs_collected: int = 0
    coins_earned: int = 0
    new_balance: int | None = None
    #: Inline shared-game level-up notice (set only when collecting crossed one).
    xp_note: str | None = None


async def collect(user_id: int, guild_id: int) -> CollectResult:
    """Collect all settled eggs → coins (the faucet) + game XP.

    Reads + settles the farm, then inside ONE transaction: credits the egg value
    (the credit audits itself via ``credit_in_txn``), resets the coop to empty as
    of *now*, and awards the ``collect_eggs`` game XP. Nothing to collect writes
    nothing. Events emit after commit.
    """
    now = int(time.time())
    chickens, eggs, ts, coop = await db.get_chicken_farm(user_id, guild_id)
    settled = farm_mod.settle(farm_mod.FarmState(chickens, eggs, ts, coop), now)
    if settled.eggs <= 0:
        return CollectResult(
            False,
            "🥚 The coop is empty — your hens need time to lay. Check back soon!",
        )

    payout = farm_mod.collect_value(settled.eggs)
    async with db.transaction() as conn:
        new_balance = await economy_service.credit_in_txn(
            conn,
            guild_id,
            user_id,
            payout,
            reason=COLLECT_REASON,
            actor_id=user_id,
        )
        await db.set_chicken_farm(
            user_id,
            guild_id,
            settled.chickens,
            0,  # coop emptied
            now,
            settled.coop_level,
            conn=conn,
        )
        award = await game_xp_service.award(
            guild_id,
            user_id,
            game=game_xp_service.GAME_FARM,
            action="collect_eggs",
            conn=conn,
        )

    await bus.emit(
        economy_service.EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=payout,
        new_balance=new_balance,
        reason=COLLECT_REASON,
    )
    xp_note = None
    if award is not None:
        await game_xp_service.emit_award_events(award)
        xp_note = award.note if award.leveled_up else None

    return CollectResult(
        True,
        f"🥚 Collected **{settled.eggs}** egg(s) for **{payout}** 🪙! "
        f"Balance: **{new_balance}** 🪙.",
        eggs_collected=settled.eggs,
        coins_earned=payout,
        new_balance=new_balance,
        xp_note=xp_note,
    )


@dataclass(frozen=True)
class PurchaseResult:
    """The outcome of a buy/upgrade — a flag, a message, and the new balance."""

    success: bool
    message: str
    new_balance: int | None = None


async def buy_chicken(user_id: int, guild_id: int) -> PurchaseResult:
    """Buy one more hen — an audited coin sink that speeds up egg laying.

    Settles eggs at the OLD flock size first (so the faster rate only applies
    going forward), then debits the scaling price and raises the flock by one
    inside ONE transaction. Insufficient funds rolls everything back.
    """
    now = int(time.time())
    chickens, eggs, ts, coop = await db.get_chicken_farm(user_id, guild_id)
    if not farm_mod.can_buy_chicken(chickens):
        return PurchaseResult(
            False,
            f"🐔 Your flock is at the cap of **{farm_mod.MAX_CHICKENS}** hens — "
            "that's a lot of clucking!",
        )
    settled = farm_mod.settle(farm_mod.FarmState(chickens, eggs, ts, coop), now)
    price = farm_mod.chicken_price(chickens)

    try:
        async with db.transaction() as conn:
            new_balance = await economy_service.debit_in_txn(
                conn,
                guild_id,
                user_id,
                price,
                reason=BUY_CHICKEN_REASON,
                actor_id=user_id,
            )
            await db.set_chicken_farm(
                user_id,
                guild_id,
                settled.chickens + 1,
                settled.eggs,
                now,
                settled.coop_level,
                conn=conn,
            )
    except economy_service.InsufficientFundsError:
        balance = await db.get_coins(user_id, guild_id)
        return PurchaseResult(
            False,
            f"🐔 A new hen costs **{price}** 🪙 — you only have **{balance}** 🪙.",
        )

    await bus.emit(
        economy_service.EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=-price,
        new_balance=new_balance,
        reason=BUY_CHICKEN_REASON,
    )
    return PurchaseResult(
        True,
        f"🐔 Bought a hen for **{price}** 🪙! Your flock is now "
        f"**{settled.chickens + 1}** strong. Balance: **{new_balance}** 🪙.",
        new_balance=new_balance,
    )


async def upgrade_coop(user_id: int, guild_id: int) -> PurchaseResult:
    """Upgrade the coop one level — an audited coin sink that raises the egg cap.

    Settles eggs first (keeping the timestamp fresh), then debits the scaling
    price and raises the coop level by one inside ONE transaction.
    """
    now = int(time.time())
    chickens, eggs, ts, coop = await db.get_chicken_farm(user_id, guild_id)
    if not farm_mod.can_upgrade_coop(coop):
        return PurchaseResult(
            False,
            f"🏠 Your coop is already maxed at level **{farm_mod.MAX_COOP_LEVEL}** "
            f"(holds **{farm_mod.coop_capacity(coop)}** eggs).",
        )
    settled = farm_mod.settle(farm_mod.FarmState(chickens, eggs, ts, coop), now)
    price = farm_mod.coop_upgrade_price(coop)
    new_capacity = farm_mod.coop_capacity(coop + 1)

    try:
        async with db.transaction() as conn:
            new_balance = await economy_service.debit_in_txn(
                conn,
                guild_id,
                user_id,
                price,
                reason=UPGRADE_COOP_REASON,
                actor_id=user_id,
            )
            await db.set_chicken_farm(
                user_id,
                guild_id,
                settled.chickens,
                settled.eggs,
                now,
                settled.coop_level + 1,
                conn=conn,
            )
    except economy_service.InsufficientFundsError:
        balance = await db.get_coins(user_id, guild_id)
        return PurchaseResult(
            False,
            f"🏠 The next coop upgrade costs **{price}** 🪙 — you only have "
            f"**{balance}** 🪙.",
        )

    await bus.emit(
        economy_service.EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=-price,
        new_balance=new_balance,
        reason=UPGRADE_COOP_REASON,
    )
    return PurchaseResult(
        True,
        f"🏠 Upgraded your coop to level **{settled.coop_level + 1}** for "
        f"**{price}** 🪙 — it now holds **{new_capacity}** eggs! "
        f"Balance: **{new_balance}** 🪙.",
        new_balance=new_balance,
    )
