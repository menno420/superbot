"""Mining workflow service — the audited write boundary for mining (RS02).

Q-0071: every mining operation that mutates more than one row — and every
one that spans **coins + mining inventory** — runs inside ONE
``db.transaction()`` here, composed from the conn-aware ``utils/db``
primitives.  Neither leg is ever committed separately from a cog/view
(the FIND-RS01/RS02 anti-pattern this service closes).  EventBus
emission happens **after commit**, never inside the transaction (the
``economy_service.transfer`` precedent).

Stage 1 (this module's birth) owns the **workshop** operations — the
densest multi-write invariants (Q-0072=C): the wear tick (break =
clear wear + consume + unequip + remember-for-quick-craft, atomically),
repair (coin debit + wear clear in one transaction), craft (materials +
product in one transaction), and quick-craft (craft + auto-equip +
marker clear in one transaction).  Stage 2 converges the market
(sell/buy) and the remaining single writers behind this seam.

User-visible messages are pinned byte-identical by
``tests/unit/cogs/test_mining_workflow_characterization.py`` — the
extraction changed transaction boundaries, never copy.
"""

from __future__ import annotations

import logging

from core.events import bus
from services import economy_service
from utils import db, equipment
from utils.mining import workshop
from utils.mining.market import TradeResult
from utils.mining.recipes import load_recipes
from utils.mining.workshop import WearReport

logger = logging.getLogger("bot.mining_workflow")


async def wear_tick(
    user_id: int,
    guild_id: int,
    *,
    action: str,
    depth: int,
    equipped: dict[str, str],
) -> WearReport:
    """Tick 1 durability off each equipped item *action* uses; break at 0.

    Breaking consumes one unit from the inventory (the actual sink), clears
    the equipment slot, deletes the wear row, and records the item as
    ``last_broken_item`` so quick-craft can offer it back — all four writes
    in ONE transaction (pre-RS02 these were four separate commits; a
    mid-break failure could consume the item but leave it equipped).
    """
    plan = workshop.WEAR_PLAN.get(action, ())
    suid = str(user_id)
    candidates = [
        (slot, item)
        for slot, underground_only in plan
        if (item := equipped.get(slot))
        and (not underground_only or depth > 0)
        and equipment.max_durability(item) is not None
    ]
    if not candidates:
        return WearReport()

    wear = await db.get_gear_wear(suid, guild_id)
    broke: list[str] = []
    notes: list[str] = []
    async with db.transaction() as conn:
        for slot, item in candidates:
            maximum = equipment.max_durability(item)
            if maximum is None:  # filtered above; guard keeps the type narrow
                continue
            remaining = wear.get(item, maximum) - 1
            if remaining <= 0:
                await db.clear_gear_wear(suid, guild_id, item, conn=conn)
                await db.update_mining_item(suid, guild_id, item, -1, conn=conn)
                await db.unequip_slot(suid, guild_id, slot, conn=conn)
                await db.set_last_broken(suid, guild_id, item, conn=conn)
                broke.append(item)
                notes.append(
                    f"💥 Your **{item}** broke! Re-craft or repair gear at the "
                    f"🔧 Workshop.",
                )
            else:
                await db.set_gear_wear(suid, guild_id, item, remaining, conn=conn)
                if remaining <= workshop.LOW_DURABILITY_WARN:
                    notes.append(
                        f"⚠️ Your **{item}** is nearly worn out "
                        f"({remaining}/{maximum}) — repair it at the 🔧 Workshop.",
                    )
    return WearReport(broke=tuple(broke), notes=tuple(notes))


async def repair(user_id: int, guild_id: int, item: str) -> TradeResult:
    """Repair *item* to full durability for coins — debit + wear clear atomically.

    Pre-RS02 the debit committed before the wear clear (a mid-op failure
    cost coins without repairing); both legs now commit or roll back
    together, and the balance event emits after commit.
    """
    item = item.strip().lower()
    suid = str(user_id)
    if equipment.max_durability(item) is None:
        return TradeResult(False, f"**{item}** doesn't wear out.")
    inventory = await db.get_mining_inventory(suid, guild_id)
    if inventory.get(item, 0) < 1:
        return TradeResult(False, f"You don't own a **{item}** to repair.")
    wear = await db.get_gear_wear(suid, guild_id)
    if item not in wear:
        return TradeResult(
            False,
            f"Your **{item}** is already at full durability.",
        )
    cost = workshop.repair_cost(item, wear[item])
    if cost is None:
        return TradeResult(False, f"**{item}** can't be repaired here.")
    try:
        async with db.transaction() as conn:
            new_balance = await economy_service.debit_in_txn(
                conn,
                guild_id,
                user_id,
                cost,
                reason=workshop.REPAIR_REASON,
                actor_id=user_id,
            )
            await db.clear_gear_wear(suid, guild_id, item, conn=conn)
    except economy_service.InsufficientFundsError:
        balance = await db.get_coins(user_id, guild_id)
        return TradeResult(
            False,
            f"Repairing **{item}** costs **{cost}** 🪙 — you only have "
            f"**{balance}** 🪙.",
        )
    await bus.emit(
        economy_service.EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=-cost,
        new_balance=new_balance,
        reason=workshop.REPAIR_REASON,
    )
    return TradeResult(
        True,
        f"Repaired **{item}** to full durability for **{cost}** 🪙. "
        f"Balance: **{new_balance}** 🪙.",
        -cost,
        new_balance,
    )


def _resolve_recipe(item: str) -> dict[str, int] | TradeResult:
    """Look up *item*'s recipe — the recipe dict, or the no-recipe result.

    Runs before any DB read so an unknown recipe costs no I/O (the
    pre-RS02 ordering, pinned by the existing craft tests).
    """
    from utils.mining import market

    recipe = load_recipes().get(item)
    if not recipe:
        hint = (
            " You can buy one at the 🛒 Market instead."
            if market.buy_price(item) is not None
            else " Use `!buildlist` to see available recipes."
        )
        return TradeResult(False, f"No recipe for **{item}**.{hint}")
    return recipe


def _check_materials(
    item: str,
    recipe: dict[str, int],
    inventory: dict[str, int],
) -> TradeResult | None:
    """The missing-materials failure result, or None when craftable."""
    for mat, qty in recipe.items():
        if inventory.get(mat, 0) < qty:
            return TradeResult(
                False,
                f"You don't have enough **{mat}** to craft **{item}** "
                f"(needs {workshop.describe_materials(recipe)}).",
            )
    return None


async def craft(user_id: int, guild_id: int, item: str) -> TradeResult:
    """Craft *item* from its recipe — materials + product in one transaction."""
    item = item.strip().lower()
    recipe = _resolve_recipe(item)
    if isinstance(recipe, TradeResult):
        return recipe
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    missing = _check_materials(item, recipe, inventory)
    if missing is not None:
        return missing
    deltas = {mat: -qty for mat, qty in recipe.items()}
    deltas[item] = deltas.get(item, 0) + 1
    async with db.transaction() as conn:
        await db.apply_inventory_deltas(suid, guild_id, deltas, conn=conn)
    return TradeResult(True, f"Crafted **{item}**!")


async def quick_craft(user_id: int, guild_id: int) -> TradeResult:
    """Re-craft the last item that broke; auto-equip it if its slot is free.

    Craft deltas + equip + marker clear commit in ONE transaction — pre-RS02
    these were three separate commits and a mid-op failure could craft the
    item but keep offering the quick-craft.
    """
    suid = str(user_id)
    last = await db.get_last_broken(suid, guild_id)
    if not last:
        return TradeResult(
            False,
            "Nothing has broken recently — craft or repair gear below.",
        )
    recipe = _resolve_recipe(last)
    if isinstance(recipe, TradeResult):
        return recipe
    inventory = await db.get_mining_inventory(suid, guild_id)
    missing = _check_materials(last, recipe, inventory)
    if missing is not None:
        return missing
    deltas = {mat: -qty for mat, qty in recipe.items()}
    deltas[last] = deltas.get(last, 0) + 1
    message = f"Crafted **{last}**!"
    async with db.transaction() as conn:
        await db.apply_inventory_deltas(suid, guild_id, deltas, conn=conn)
        slot = equipment.slot_for(last)
        if slot is not None:
            equipped = await db.get_equipment(suid, guild_id, conn=conn)
            if slot not in equipped:
                await db.equip_item(suid, guild_id, slot, last, conn=conn)
                message = f"Crafted **{last}** and equipped it in the **{slot}** slot!"
        await db.set_last_broken(suid, guild_id, None, conn=conn)
    return TradeResult(True, message)


__all__ = [
    "wear_tick",
    "repair",
    "craft",
    "quick_craft",
]
