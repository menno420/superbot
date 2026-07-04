"""Mining workflow service — the audited write boundary for mining (RS02).

Q-0071: every mining operation that mutates more than one row — and every
one that spans **coins + mining inventory** — runs inside ONE
``db.transaction()`` here, composed from the conn-aware ``utils/db``
primitives.  Neither leg is ever committed separately from a cog/view
(the FIND-RS01/RS02 anti-pattern this service closes).  EventBus
emission happens **after commit**, never inside the transaction (the
``economy_service.transfer`` precedent).

Stage 1 owned the **workshop** operations — the densest multi-write
invariants (Q-0072=C): the wear tick (break = clear wear + consume +
unequip + remember-for-quick-craft, atomically), repair (coin debit +
wear clear in one transaction), craft (materials + product in one
transaction), and quick-craft (craft + auto-equip + marker clear in one
transaction).  Stage 2 (this revision) converges everything else: the
market (sell / sell-all / buy — inventory leg + coin leg atomically),
the action writers (mine / harvest / explore — loot grant + wear tick
in one transaction), equip / unequip / use, descent, and the admin
writes.  ``cogs/mining/`` is gone; views and the cog call only this
service, and the AST ratchet
(``tests/unit/invariants/test_mining_write_boundary.py``) keeps any new
direct write out of cogs/views.

User-visible messages are pinned byte-identical by
``tests/unit/cogs/test_mining_workflow_characterization.py`` — the
extraction changed transaction boundaries, never copy.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from core.events import bus
from services import economy_service, game_xp_service
from utils import db, equipment
from utils.mining import (
    capacity,
    character,
    energy,
    grid,
    items,
    market,
    rewards,
    structures,
    workshop,
    world,
)
from utils.mining.exploration import explore_from_state
from utils.mining.market import TradeResult
from utils.mining.recipes import load_recipes
from utils.mining.workshop import WearReport

logger = logging.getLogger("bot.mining_workflow")


@dataclass(frozen=True)
class MineResult:
    """One mining swing — the rolled loot plus the wear it caused."""

    found: str
    amount: int
    depth: int
    wear: WearReport
    #: Inline level-up notice (set only when the award crossed a level).
    xp_note: str | None = None
    #: Gentle "pack full — stash at the vault" nudge (Slice A; never blocks).
    pack_warning: str | None = None


@dataclass(frozen=True)
class HarvestResult:
    """One harvest — the rolled wood amount."""

    amount: int
    xp_note: str | None = None
    #: Gentle "pack full — stash at the vault" nudge (Slice A; never blocks).
    pack_warning: str | None = None


@dataclass(frozen=True)
class ExploreActionResult:
    """One exploration roll — outcome text/loot plus the wear it caused."""

    text: str
    item: str | None
    amount: int
    depth: int
    wear: WearReport
    xp_note: str | None = None
    #: Gentle "pack full — stash at the vault" nudge (Slice A; never blocks).
    pack_warning: str | None = None


@dataclass(frozen=True)
class DescentResult:
    """A descend/ascend attempt — call sites own the copy (cog ≠ panel)."""

    moved: bool
    depth: int
    hint: str | None = None
    xp_note: str | None = None


@dataclass(frozen=True)
class DigResult:
    """One directional dig (PR 3): move into the adjacent cell AND mine it.

    The owner's grid model (in-chat, post-#1281): every dig is locomotion — N/S/E/W
    tunnel laterally, Down descends a band (light-gated), Up ascends one — and mines
    the cell you move *into*.  A blocked vertical dig leaves ``moved`` False with a
    ``hint`` and no loot (``found`` None).  ``x``/``y`` are the new lateral position;
    ``depth`` is the new band (z).
    """

    moved: bool
    x: int
    y: int
    depth: int
    found: str | None
    amount: int
    wear: WearReport
    hint: str | None = None
    cell_note: str | None = None
    xp_note: str | None = None
    pack_warning: str | None = None


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
    candidates = _wear_candidates(action, depth, equipped)
    if not candidates:
        return WearReport()

    suid = str(user_id)
    wear = await db.get_gear_wear(suid, guild_id)
    async with db.transaction() as conn:
        return await _apply_wear_writes(conn, suid, guild_id, candidates, wear)


def _wear_candidates(
    action: str,
    depth: int,
    equipped: dict[str, str],
) -> list[tuple[str, str]]:
    """The (slot, item) pairs that wear for *action* at *depth* (pure)."""
    plan = workshop.WEAR_PLAN.get(action, ())
    return [
        (slot, item)
        for slot, underground_only in plan
        if (item := equipped.get(slot))
        and (not underground_only or depth > 0)
        and equipment.max_durability(item) is not None
    ]


async def _apply_wear_writes(
    conn,
    suid: str,
    guild_id: int,
    candidates: list[tuple[str, str]],
    wear: dict[str, int],
) -> WearReport:
    """The wear writes, on a caller-owned connection (shared by wear_tick /
    mine / explore so an action's loot grant and its wear commit together).
    """
    broke: list[str] = []
    notes: list[str] = []
    for slot, item in candidates:
        maximum = equipment.max_durability(item)
        if maximum is None:  # filtered by _wear_candidates; narrows the type
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
            xp = await game_xp_service.award(
                guild_id,
                user_id,
                game=game_xp_service.GAME_CRAFTING,
                action="repair",
                conn=conn,
            )
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
    message = (
        f"Repaired **{item}** to full durability for **{cost}** 🪙. "
        f"Balance: **{new_balance}** 🪙."
    )
    if xp is not None:
        await game_xp_service.emit_award_events(xp)
        if xp.leveled_up:
            message += "\n" + xp.note
    return TradeResult(True, message, -cost, new_balance)


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


async def _forge_gate(user_id: int, guild_id: int, item: str) -> TradeResult | None:
    """The forge-requirement failure for *item*, or None when craftable (Slice B).

    Forge-free recipes (every tool, structure, and bronze/iron/silver gear)
    return immediately with **no DB read** — so existing craft paths are
    unchanged in I/O and behaviour; only gold/diamond gear ever reads the
    structures table.
    """
    required = structures.forge_level_required(item)
    if required == 0:
        return None
    built = await db.get_structures(user_id, guild_id)
    level = built.get(structures.FORGE, 0)
    if level >= required:
        return None
    tier = equipment.gear_tier(item)
    needed = structures.forge_level_name(required)
    return TradeResult(
        False,
        f"Crafting **{item}** needs a **{needed}** 🔥 — "
        f"build the Forge with `!forge` to unlock {tier}-tier gear.",
    )


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
    gated = await _forge_gate(user_id, guild_id, item)
    if gated is not None:
        return gated
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    missing = _check_materials(item, recipe, inventory)
    if missing is not None:
        return missing
    deltas = {mat: -qty for mat, qty in recipe.items()}
    deltas[item] = deltas.get(item, 0) + 1
    async with db.transaction() as conn:
        await db.apply_inventory_deltas(suid, guild_id, deltas, conn=conn)
        xp = await game_xp_service.award(
            guild_id,
            user_id,
            game=game_xp_service.GAME_CRAFTING,
            action="craft",
            conn=conn,
        )
    message = f"Crafted **{item}**!"
    if xp is not None:
        await game_xp_service.emit_award_events(xp)
        if xp.leveled_up:
            message += "\n" + xp.note
    return TradeResult(True, message)


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
    gated = await _forge_gate(user_id, guild_id, last)
    if gated is not None:
        return gated
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
        xp = await game_xp_service.award(
            guild_id,
            user_id,
            game=game_xp_service.GAME_CRAFTING,
            action="quick_craft",
            conn=conn,
        )
    if xp is not None:
        await game_xp_service.emit_award_events(xp)
        if xp.leveled_up:
            message += "\n" + xp.note
    return TradeResult(True, message)


# ---------------------------------------------------------------------------
# Market — sell / sell-all / buy (coin leg + inventory leg, one transaction)
# ---------------------------------------------------------------------------


async def sell(user_id: int, guild_id: int, item: str, qty: int) -> TradeResult:
    """Sell *qty* of *item* (a resource) for coins — both legs atomic."""
    item = item.strip().lower()
    price = market.sell_price(item)
    if price is None:
        return TradeResult(
            False,
            f"You can't sell **{item}** — only raw resources sell.",
        )
    if qty <= 0:
        return TradeResult(False, "Amount to sell must be a positive number.")
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    have = inventory.get(item, 0)
    if have < qty:
        return TradeResult(False, f"You only have **{have}× {item}** to sell.")
    coins = price * qty
    async with db.transaction() as conn:
        await db.update_mining_item(suid, guild_id, item, -qty, conn=conn)
        new_balance = await economy_service.credit_in_txn(
            conn,
            guild_id,
            user_id,
            coins,
            reason=market.SELL_REASON,
            actor_id=user_id,
        )
    await _emit_balance(guild_id, user_id, coins, new_balance, market.SELL_REASON)
    return TradeResult(
        True,
        f"Sold **{qty}× {item}** for **{coins}** 🪙. Balance: **{new_balance}** 🪙.",
        coins,
        new_balance,
    )


async def sell_all(user_id: int, guild_id: int) -> TradeResult:
    """Sell every sellable resource — all removals + one credit, atomic."""
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    sellables = market.sellable_inventory(inventory)
    if not sellables:
        return TradeResult(False, "You have no resources to sell — go mine some!")
    total = sum(qty * price for _, qty, price in sellables)
    async with db.transaction() as conn:
        for name, qty, _ in sellables:
            await db.update_mining_item(suid, guild_id, name, -qty, conn=conn)
        new_balance = await economy_service.credit_in_txn(
            conn,
            guild_id,
            user_id,
            total,
            reason=market.SELL_REASON,
            actor_id=user_id,
        )
    await _emit_balance(guild_id, user_id, total, new_balance, market.SELL_REASON)
    sold = ", ".join(f"{qty}× {name}" for name, qty, _ in sellables)
    return TradeResult(
        True,
        f"Sold {sold} for **{total}** 🪙. Balance: **{new_balance}** 🪙.",
        total,
        new_balance,
    )


async def buy(user_id: int, guild_id: int, item: str) -> TradeResult:
    """Buy one *item* from the gear shop — debit + grant atomic."""
    item = item.strip().lower()
    price = market.buy_price(item)
    if price is None:
        return TradeResult(
            False,
            f"**{item}** isn't for sale. Check `!market` for stock.",
        )
    try:
        async with db.transaction() as conn:
            new_balance = await economy_service.debit_in_txn(
                conn,
                guild_id,
                user_id,
                price,
                reason=market.BUY_REASON,
                actor_id=user_id,
            )
            await db.update_mining_item(str(user_id), guild_id, item, 1, conn=conn)
    except economy_service.InsufficientFundsError:
        balance = await db.get_coins(user_id, guild_id)
        return TradeResult(
            False,
            f"**{item}** costs **{price}** 🪙 — you only have **{balance}** 🪙.",
        )
    await _emit_balance(guild_id, user_id, -price, new_balance, market.BUY_REASON)
    return TradeResult(
        True,
        f"Bought **{item}** for **{price}** 🪙. Balance: **{new_balance}** 🪙. "
        f"Use `!equip {item}` to wear it.",
        -price,
        new_balance,
    )


async def _emit_balance(
    guild_id: int,
    user_id: int,
    delta: int,
    new_balance: int,
    reason: str,
) -> None:
    """EVT_BALANCE_CHANGED, after the owning transaction committed."""
    await bus.emit(
        economy_service.EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=delta,
        new_balance=new_balance,
        reason=reason,
    )


# ---------------------------------------------------------------------------
# Vault — safe stash (move items between the active inventory and the vault)
# ---------------------------------------------------------------------------


async def vault_deposit(
    user_id: int,
    guild_id: int,
    item: str,
    qty: int,
) -> TradeResult:
    """Move *qty* of *item* from the active inventory into the safe vault.

    Both legs (inventory debit + vault credit) commit in ONE transaction so a
    mid-move failure can never duplicate the items or lose them between stores
    (the §7.5 Vault is item-state, direct-lane — no coins move, so no
    economy_service / audit leg; the atomicity is the whole contract).
    """
    item = item.strip().lower()
    if qty <= 0:
        return TradeResult(False, "Amount to deposit must be a positive number.")
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    have = inventory.get(item, 0)
    if have < qty:
        owned = f"only **{have}× {item}**" if have else f"no **{item}**"
        return TradeResult(False, f"You have {owned} to deposit.")
    async with db.transaction() as conn:
        await db.update_mining_item(suid, guild_id, item, -qty, conn=conn)
        await db.update_vault_item(suid, guild_id, item, qty, conn=conn)
    return TradeResult(
        True,
        f"Deposited **{qty}× {item}** into your vault — safe and out of your pack.",
    )


async def vault_withdraw(
    user_id: int,
    guild_id: int,
    item: str,
    qty: int,
) -> TradeResult:
    """Move *qty* of *item* from the safe vault back into the active inventory."""
    item = item.strip().lower()
    if qty <= 0:
        return TradeResult(False, "Amount to withdraw must be a positive number.")
    suid = str(user_id)
    vault = await db.get_vault(suid, guild_id)
    have = vault.get(item, 0)
    if have < qty:
        owned = f"only **{have}× {item}**" if have else f"no **{item}**"
        return TradeResult(False, f"Your vault holds {owned}.")
    async with db.transaction() as conn:
        await db.update_vault_item(suid, guild_id, item, -qty, conn=conn)
        await db.update_mining_item(suid, guild_id, item, qty, conn=conn)
    return TradeResult(
        True,
        f"Withdrew **{qty}× {item}** from your vault back into your pack.",
    )


async def vault_deposit_all_resources(user_id: int, guild_id: int) -> TradeResult:
    """Stash every raw resource into the vault in ONE transaction.

    The one-click "tuck away my ore" convenience (gear / tools / treasure stay
    in the active pack — only sellable resources move).  All the moves commit
    together so a mid-sweep failure leaves the pack and the vault consistent.
    """
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    resources = market.sellable_inventory(inventory)  # [(name, qty, price), …]
    if not resources:
        return TradeResult(False, "You have no raw resources to stash — go mine some!")
    async with db.transaction() as conn:
        for name, qty, _ in resources:
            await db.update_mining_item(suid, guild_id, name, -qty, conn=conn)
            await db.update_vault_item(suid, guild_id, name, qty, conn=conn)
    moved = ", ".join(f"{qty}× {name}" for name, qty, _ in resources)
    return TradeResult(True, f"Stashed {moved} into your vault.")


async def vault_upgrade(user_id: int, guild_id: int) -> TradeResult:
    """Buy one vault-capacity tier — the §7.5 coin sink (Slice A).

    Debits the rising upgrade cost and raises ``vault_level`` by one in ONE
    transaction (the ``buy`` / ``skill_service.respec`` precedent: the coin
    debit is economy-audited, the balance event emits after commit).  At the
    top tier nothing is charged — the upgrade is a *capacity* feature, never a
    block on storing or mining (owner: no hard cap).
    """
    suid = str(user_id)
    level = await db.get_vault_level(suid, guild_id)
    cost = capacity.vault_upgrade_cost(level)
    if cost is None:
        cap = capacity.vault_capacity(level)
        return TradeResult(
            False,
            f"Your vault is already at its maximum capacity (**{cap}** item types).",
        )
    try:
        async with db.transaction() as conn:
            new_balance = await economy_service.debit_in_txn(
                conn,
                guild_id,
                user_id,
                cost,
                reason=market.VAULT_UPGRADE_REASON,
                actor_id=user_id,
            )
            await db.set_vault_level(suid, guild_id, level + 1, conn=conn)
    except economy_service.InsufficientFundsError:
        balance = await db.get_coins(user_id, guild_id)
        return TradeResult(
            False,
            f"A vault upgrade costs **{cost}** 🪙 — you only have **{balance}** 🪙.",
        )
    await _emit_balance(
        guild_id,
        user_id,
        -cost,
        new_balance,
        market.VAULT_UPGRADE_REASON,
    )
    new_cap = capacity.vault_capacity(level + 1)
    return TradeResult(
        True,
        f"Vault upgraded to capacity **{new_cap}** item types for **{cost}** 🪙. "
        f"Balance: **{new_balance}** 🪙.",
        -cost,
        new_balance,
    )


def _build_success_suffix(structure: str, new_level: int) -> str:
    """The structure-specific reward line appended to a successful build.

    Forge advertises the gear tier it just unlocked; Home advertises the
    Character-card backdrop it just unlocked.  Generic structures get nothing.
    """
    if structure == structures.FORGE:
        unlocked = structures.tiers_unlocked_at(new_level)
        return f" Now crafts **{unlocked[-1]}-tier** gear." if unlocked else ""
    if structure == structures.HOME:
        return " It now frames your Character card."
    if structure == structures.TIDE_POOL:
        mult = structures.tide_pool_pull_mult(new_level)
        pct = round((mult - 1.0) * 100)
        return f" Your casts now pull **+{pct}%** toward rarer fish."
    if structure == structures.DOCK:
        mult = structures.dock_bite_speed_mult(new_level)
        pct = round((1.0 - mult) * 100)
        return f" Fish now bite **{pct}%** faster."
    if structure == structures.BOATHOUSE:
        mult = structures.boathouse_regen_mult(new_level)
        pct = round((1.0 - mult) * 100)
        return f" Your fishing energy now refills **{pct}%** faster."
    if structure == structures.FISHERY:
        pct = round(structures.fishery_bonus_chance(new_level) * 100)
        return f" Your reels now have **+{pct}%** chance of a double catch."
    return ""


async def build_structure(
    user_id: int,
    guild_id: int,
    structure: str = structures.FORGE,
) -> TradeResult:
    """Build/upgrade *structure* one level — the §7.5 coin + material sink.

    Debits coins, consumes the build materials, and raises the structure level by
    one in ONE transaction (the ``vault_upgrade`` precedent extended with a
    material leg — every part commits together or not at all).  Building is never
    required to play: the Forge (Slice B) gates only gold/diamond gear crafting,
    and the Home (Slice C) is a purely cosmetic Character-card backdrop.
    """
    structure = structure.strip().lower()
    if not structures.is_structure(structure):
        return TradeResult(
            False,
            f"**{structure or '(blank)'}** isn't a buildable structure — "
            "try `!forge` or `!home`.",
        )
    display = structures.display_name(structure)
    suid = str(user_id)
    built = await db.get_structures(user_id, guild_id)
    level = built.get(structure, 0)
    cost = structures.build_cost(structure, level)
    if cost is None:
        name = structures.level_name(structure, level)
        return TradeResult(
            False,
            f"Your {display} is already at its maximum level (**{name}**).",
        )
    # Material check first, for a clean message (the craft precedent) — the coin
    # debit inside the txn handles the affordability failure.
    inventory = await db.get_mining_inventory(suid, guild_id)
    missing = _check_materials(structure, cost.materials, inventory)
    if missing is not None:
        return TradeResult(
            False,
            f"Building the {display} needs "
            f"{workshop.describe_materials(cost.materials)} "
            f"plus {cost.coins} 🪙 — you're short on materials.",
        )
    deltas = {mat: -qty for mat, qty in cost.materials.items()}
    reason = market.structure_build_reason(structure)
    try:
        async with db.transaction() as conn:
            new_balance = await economy_service.debit_in_txn(
                conn,
                guild_id,
                user_id,
                cost.coins,
                reason=reason,
                actor_id=user_id,
            )
            await db.apply_inventory_deltas(suid, guild_id, deltas, conn=conn)
            await db.set_structure_level(
                user_id,
                guild_id,
                structure,
                level + 1,
                conn=conn,
            )
    except economy_service.InsufficientFundsError:
        balance = await db.get_coins(user_id, guild_id)
        return TradeResult(
            False,
            f"Building the {display} costs **{cost.coins}** 🪙 — you only have "
            f"**{balance}** 🪙.",
        )
    await _emit_balance(guild_id, user_id, -cost.coins, new_balance, reason)
    new_name = structures.level_name(structure, level + 1)
    suffix = _build_success_suffix(structure, level + 1)
    return TradeResult(
        True,
        f"{display} built to **{new_name}** for "
        f"{workshop.describe_materials(cost.materials)} "
        f"+ {cost.coins} 🪙.{suffix} Balance: **{new_balance}** 🪙.",
        -cost.coins,
        new_balance,
    )


# ---------------------------------------------------------------------------
# Actions — mine / harvest / explore (loot grant + wear in one transaction)
# ---------------------------------------------------------------------------


def _pack_warning_after(inventory: dict[str, int], granted: str | None) -> str | None:
    """The pack soft-cap nudge once *granted* lands in *inventory* (Slice A).

    Computed from the pre-action read + the granted item (no extra query): a
    gentle "stash at the vault" hint when the pack is at/over its distinct-type
    soft cap.  Returns ``None`` below the cap — mining is never blocked.
    """
    projected = capacity.projected_distinct_types(inventory, granted)
    return capacity.pack_warning(capacity.CapStatus(projected, capacity.PACK_SOFT_CAP))


async def mine(user_id: int, guild_id: int) -> MineResult:
    """One mining swing: roll loot, grant it, and tick wear — atomically."""
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    equipped = await db.get_equipment(suid, guild_id)
    depth = await db.get_depth(suid, guild_id)
    found, amount = rewards.roll_mine_loot(
        has_pickaxe=inventory.get("pickaxe", 0) > 0,
        depth=depth,
        multiplier=rewards.mine_multiplier(equipped, inventory),
    )
    candidates = _wear_candidates(workshop.ACTION_MINE, depth, equipped)
    wear = await db.get_gear_wear(suid, guild_id) if candidates else {}
    async with db.transaction() as conn:
        await db.update_mining_item(suid, guild_id, found, amount, conn=conn)
        report = (
            await _apply_wear_writes(conn, suid, guild_id, candidates, wear)
            if candidates
            else WearReport()
        )
        xp = await game_xp_service.award(
            guild_id,
            user_id,
            game=game_xp_service.GAME_MINING,
            action="mine",
            depth=depth,
            conn=conn,
        )
    if xp is not None:
        await game_xp_service.emit_award_events(xp)
    return MineResult(
        found=found,
        amount=amount,
        depth=depth,
        wear=report,
        xp_note=xp.note if xp is not None and xp.leveled_up else None,
        pack_warning=_pack_warning_after(inventory, found),
    )


async def harvest(user_id: int, guild_id: int) -> HarvestResult:
    """Chop wood (doubled with an axe in the inventory) and grant it."""
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    amount = rewards.roll_harvest_amount(has_axe=inventory.get("axe", 0) > 0)
    async with db.transaction() as conn:
        await db.update_mining_item(suid, guild_id, "wood", amount, conn=conn)
        xp = await game_xp_service.award(
            guild_id,
            user_id,
            game=game_xp_service.GAME_MINING,
            action="harvest",
            conn=conn,
        )
    if xp is not None:
        await game_xp_service.emit_award_events(xp)
    return HarvestResult(
        amount=amount,
        xp_note=xp.note if xp is not None and xp.leveled_up else None,
        pack_warning=_pack_warning_after(inventory, "wood"),
    )


async def explore(user_id: int, guild_id: int) -> ExploreActionResult:
    """One exploration roll: outcome + loot grant + wear — atomically."""
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    equipped = await db.get_equipment(suid, guild_id)
    depth = await db.get_depth(suid, guild_id)
    text, item, amount = explore_from_state(
        equipped,
        inventory,
        biome=world.biome_for_depth(depth),
    )
    candidates = _wear_candidates(workshop.ACTION_EXPLORE, depth, equipped)
    wear = await db.get_gear_wear(suid, guild_id) if candidates else {}
    async with db.transaction() as conn:
        if item:
            await db.update_mining_item(suid, guild_id, item, amount, conn=conn)
        report = (
            await _apply_wear_writes(conn, suid, guild_id, candidates, wear)
            if candidates
            else WearReport()
        )
        xp = await game_xp_service.award(
            guild_id,
            user_id,
            game=game_xp_service.GAME_MINING,
            action="explore",
            depth=depth,
            conn=conn,
        )
    if xp is not None:
        await game_xp_service.emit_award_events(xp)
    return ExploreActionResult(
        text=text,
        item=item,
        amount=amount,
        depth=depth,
        wear=report,
        xp_note=xp.note if xp is not None and xp.leveled_up else None,
        pack_warning=_pack_warning_after(inventory, item),
    )


# ---------------------------------------------------------------------------
# Loadout — use / equip / unequip
# ---------------------------------------------------------------------------


async def use_item(user_id: int, guild_id: int, item: str) -> TradeResult:
    """Consume one *item* from the inventory.

    Food / boosters (``ration``, ``energy drink`` — :data:`energy.RESTORE_VALUES`)
    restore mining energy: the item consume and the energy raise commit in ONE
    transaction (Q-0071) so a mid-op failure can't eat the item without the
    refill.  Other consumables stay flavour-only.
    """
    item = item.strip().lower()
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    if inventory.get(item, 0) < 1:
        return TradeResult(False, f"You don't have **{item}** to use.")

    restore = energy.restore_value(item)
    if restore is not None:
        now = int(time.time())
        e_state = energy.EnergyState(*await db.get_energy(suid, guild_id))
        if energy.settle(e_state, now).current >= energy.MAX_ENERGY:
            return TradeResult(
                False,
                "Your energy is already full — save it for later.",
            )
        restored = energy.restore(e_state, now, restore)
        async with db.transaction() as conn:
            await db.update_mining_item(suid, guild_id, item, -1, conn=conn)
            await db.set_energy(
                suid,
                guild_id,
                restored.current,
                restored.updated_at,
                conn=conn,
            )
        return TradeResult(
            True,
            f"You consume **{item}** and recover energy "
            f"({energy.bar(restored.current)}).",
        )

    if item == "torch":
        message = "You light a torch and peer into the darkness..."
    elif item == "dynamite":
        message = "You ignite dynamite and blow a new path in the mine!"
    else:
        message = f"You used **{item}**, but nothing special happened."
    await db.update_mining_item(suid, guild_id, item, -1)
    return TradeResult(True, message)


#: The food produced by cooking a fish (eaten via use_item for energy).
COOKED_FISH = "cooked fish"


async def cook(user_id: int, guild_id: int, fish: str, qty: int = 1) -> TradeResult:
    """Cook *qty* caught *fish* into ``cooked fish`` food at a built campfire.

    Owner decision (2026-06-22): cooking is gated on a built **Campfire**
    structure.  Consumes the raw fish and grants the same number of generic
    ``cooked fish`` (eaten via :func:`use_item` to refill mining energy) in ONE
    transaction (Q-0071).  Raw fish are sold for coins through the normal market
    instead; cooking trades a fish for a meal.
    """
    fish = fish.strip().lower()
    suid = str(user_id)
    qty = max(1, qty)

    built = await db.get_structures(user_id, guild_id)
    if not structures.cooking_unlocked(built.get(structures.CAMPFIRE, 0)):
        return TradeResult(
            False,
            "You need a 🔥 **Campfire** to cook — build one with `!build campfire`.",
        )
    if not items.is_fish(fish):
        return TradeResult(
            False,
            f"**{fish}** isn't a fish you can cook — catch fish with `!fish`.",
        )
    inventory = await db.get_mining_inventory(suid, guild_id)
    have = inventory.get(fish, 0)
    if have < qty:
        return TradeResult(
            False,
            f"You only have **{have}× {fish}** to cook (wanted {qty}).",
        )

    async with db.transaction() as conn:
        await db.update_mining_item(suid, guild_id, fish, -qty, conn=conn)
        await db.update_mining_item(suid, guild_id, COOKED_FISH, qty, conn=conn)

    gain = energy.RESTORE_VALUES.get(COOKED_FISH, 0)
    return TradeResult(
        True,
        f"🔥 You cook **{qty}× {fish}** into **{qty}× cooked fish** "
        f"(+{gain} ⚡ each when eaten — `!use cooked fish`).",
    )


async def equip(user_id: int, guild_id: int, item: str) -> TradeResult:
    """Equip *item* into its slot (ownership + slot validation centralized)."""
    item = item.strip().lower()
    slot = equipment.slot_for(item)
    if slot is None:
        return TradeResult(False, f"**{item.title()}** can't be equipped.")
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    if inventory.get(item, 0) < 1:
        return TradeResult(False, f"You don't own a **{item.title()}** to equip.")
    await db.equip_item(suid, guild_id, slot, item)
    return TradeResult(
        True,
        f"equipped **{item.title()}** in the **{slot}** slot.",
    )


async def unequip(user_id: int, guild_id: int, slot: str) -> TradeResult:
    """Clear an equipment *slot*."""
    slot = slot.strip().lower()
    if slot not in equipment.SLOTS:
        return TradeResult(
            False,
            f"Unknown slot **{slot}**. Slots: {', '.join(equipment.SLOTS)}.",
        )
    await db.unequip_slot(str(user_id), guild_id, slot)
    return TradeResult(True, f"cleared the **{slot}** slot.")


# ---------------------------------------------------------------------------
# Loadout presets — save / apply / list / delete (V-14, Q-0175 unified loadout)
# ---------------------------------------------------------------------------
#
# A *preset* is a named snapshot of which item sits in which slot.  Saving
# captures your current equipped gear; applying restores that exact loadout —
# equipping every saved item you still own and clearing any other currently
# filled slot, so a preset behaves like a gear set ("put on your fishing
# gear").  Equip/unequip never consume the item (gear stays in your inventory),
# so applying is fully reversible.  Same direct-lane seam as equip/unequip
# (RC-8A); additive — a player with no preset sees byte-identical behaviour.

#: A small, generous cap on saved presets — keeps storage bounded and the
#: manage select inside Discord's 25-option limit.
MAX_LOADOUT_PRESETS = 10
#: Cap on a preset name's length (keeps embeds + selects tidy).
MAX_LOADOUT_NAME_LEN = 24


def _clean_loadout_name(name: str) -> str:
    """Normalise a user-supplied preset name (lowercase, collapse whitespace)."""
    return " ".join(name.strip().lower().split())[:MAX_LOADOUT_NAME_LEN]


async def save_loadout(user_id: int, guild_id: int, name: str) -> TradeResult:
    """Snapshot the player's current equipped gear as the preset *name*."""
    name = _clean_loadout_name(name)
    if not name:
        return TradeResult(
            False,
            "Give the loadout a name, e.g. `!loadout save mining`.",
        )
    suid = str(user_id)
    equipped = await db.get_equipment(suid, guild_id)
    if not equipped:
        return TradeResult(
            False,
            "You have no gear equipped to save — equip something first.",
        )
    existing = await db.list_loadouts(suid, guild_id)
    if name not in existing and len(existing) >= MAX_LOADOUT_PRESETS:
        return TradeResult(
            False,
            f"You already have {MAX_LOADOUT_PRESETS} loadouts — delete one "
            "first with `!loadout delete <name>`.",
        )
    await db.save_loadout(suid, guild_id, name, equipped)
    n = len(equipped)
    return TradeResult(
        True,
        f"saved your current gear as the **{name}** loadout "
        f"({n} slot{'s' if n != 1 else ''}).",
    )


async def apply_loadout(user_id: int, guild_id: int, name: str) -> TradeResult:
    """Restore the saved preset *name*: equip every still-owned item, clear the rest."""
    name = _clean_loadout_name(name)
    suid = str(user_id)
    preset = await db.get_loadout(suid, guild_id, name)
    if not preset:
        return TradeResult(
            False,
            f"No loadout named **{name}**. See your loadouts with `!loadout list`.",
        )
    inventory = await db.get_mining_inventory(suid, guild_id)
    to_equip = {
        slot: item for slot, item in preset.items() if inventory.get(item, 0) >= 1
    }
    missing = sorted({i for i in preset.values() if inventory.get(i, 0) < 1})
    if not to_equip:
        msg = f"You no longer own any gear from the **{name}** loadout"
        if missing:
            msg += f" (missing: {', '.join(i.title() for i in missing)})"
        return TradeResult(False, msg + ".")
    current = await db.get_equipment(suid, guild_id)
    cleared = 0
    async with db.transaction() as conn:
        for slot in equipment.SLOTS:
            if slot in to_equip:
                await db.equip_item(suid, guild_id, slot, to_equip[slot], conn=conn)
            elif slot in current:
                await db.unequip_slot(suid, guild_id, slot, conn=conn)
                cleared += 1
    n = len(to_equip)
    parts = [f"equipped the **{name}** loadout ({n} slot{'s' if n != 1 else ''})"]
    if cleared:
        parts.append(f"cleared {cleared} other slot{'s' if cleared != 1 else ''}")
    if missing:
        parts.append(
            f"skipped {len(missing)} you no longer own "
            f"({', '.join(i.title() for i in missing)})",
        )
    return TradeResult(True, " — ".join(parts) + ".")


async def list_loadouts(user_id: int, guild_id: int) -> list[str]:
    """Return the player's saved preset names, alphabetically."""
    return await db.list_loadouts(str(user_id), guild_id)


async def delete_loadout(user_id: int, guild_id: int, name: str) -> TradeResult:
    """Delete the saved preset *name*."""
    name = _clean_loadout_name(name)
    removed = await db.delete_loadout(str(user_id), guild_id, name)
    if removed == 0:
        return TradeResult(False, f"No loadout named **{name}** to delete.")
    return TradeResult(True, f"deleted the **{name}** loadout.")


# ---------------------------------------------------------------------------
# Descent — depth moves (gating stays in utils.mining.world)
# ---------------------------------------------------------------------------


async def descend(user_id: int, guild_id: int) -> DescentResult:
    """Move one band deeper if the equipped light allows it."""
    suid = str(user_id)
    depth = await db.get_depth(suid, guild_id)
    # Gear + allocated skill points (§7.4).  An unspent player reads {} ⇒
    # byte-identical to the old gear-only stats (the additive safety property).
    equipped = await db.get_equipment(suid, guild_id)
    alloc = await db.get_skills(user_id, guild_id)
    stats = character.character_stats(equipped, alloc)
    new_depth = world.descend(depth, stats)
    if new_depth == depth:
        return DescentResult(moved=False, depth=depth, hint=world.descend_hint(stats))
    xp = None
    async with db.transaction() as conn:
        await db.set_depth(suid, guild_id, new_depth, conn=conn)
        if await db.record_depth(suid, guild_id, new_depth, conn=conn):
            xp = await game_xp_service.award(
                guild_id,
                user_id,
                game=game_xp_service.GAME_MINING,
                action="depth_record",
                conn=conn,
            )
    if xp is not None:
        await game_xp_service.emit_award_events(xp)
    return DescentResult(
        moved=True,
        depth=new_depth,
        xp_note=xp.note if xp is not None and xp.leveled_up else None,
    )


async def ascend(user_id: int, guild_id: int) -> DescentResult:
    """Climb one band toward the surface."""
    suid = str(user_id)
    depth = await db.get_depth(suid, guild_id)
    new_depth = world.ascend(depth)
    if new_depth == depth:
        return DescentResult(moved=False, depth=depth)
    await db.set_depth(suid, guild_id, new_depth)
    return DescentResult(moved=True, depth=new_depth)


# ---------------------------------------------------------------------------
# Grid — dig the (x, y, z) world (PR 3): every dig moves you AND mines the cell
# ---------------------------------------------------------------------------


def _resolve_dig_target(
    direction: str,
    x: int,
    y: int,
    depth: int,
    stats: equipment.EffectiveStats,
) -> tuple[int, int, int] | DigResult:
    """The cell a *direction* dig moves into — or a blocked :class:`DigResult`.

    Lateral digs always resolve to an adjacent cell; ``Down`` is light-gated
    (the :func:`descend` rule) and ``Up`` stops at the Surface; an unknown token
    is a no-op.  Pure: it decides the destination, the caller does the I/O.
    """
    if direction in grid.LATERAL:
        nx, ny = grid.step(x, y, direction)
        return nx, ny, depth
    if direction == grid.DOWN:
        new_depth = world.descend(depth, stats)
        if new_depth == depth:
            return DigResult(
                moved=False,
                x=x,
                y=y,
                depth=depth,
                found=None,
                amount=0,
                wear=WearReport(),
                hint=world.descend_hint(stats),
            )
        return x, y, new_depth
    if direction == grid.UP:
        new_depth = world.ascend(depth)
        if new_depth == depth:
            return DigResult(
                moved=False,
                x=x,
                y=y,
                depth=depth,
                found=None,
                amount=0,
                wear=WearReport(),
                hint="You're already at the Surface — nowhere up to dig.",
            )
        return x, y, new_depth
    return DigResult(
        moved=False,
        x=x,
        y=y,
        depth=depth,
        found=None,
        amount=0,
        wear=WearReport(),
        hint=f"Unknown direction: {direction}.",
    )


async def dig(user_id: int, guild_id: int, direction: str) -> DigResult:
    """Dig one cell in *direction* — move into it AND mine it (PR 3, owner model).

    The owner's grid model (post-#1281): mining *is* locomotion.  N/S/E/W tunnel
    laterally; ``Down`` descends a band (gated by the equipped light — the
    :func:`descend` rule); ``Up`` ascends one.  The player moves into the adjacent
    cell and mines **that** cell — its seed-deterministic content (richness +
    featured ore, depth-weighted) drives the loot.  The move, the loot grant, the
    fog-of-war mark, and the wear tick all commit in ONE transaction; a down-dig
    that reaches a new deepest band also awards the depth-record XP (the
    :func:`descend` precedent).  A blocked vertical dig returns ``moved=False`` with
    a hint and no loot.
    """
    suid = str(user_id)
    direction = direction.strip().lower()
    x, y = await db.get_position(suid, guild_id)
    depth = await db.get_depth(suid, guild_id)

    # Energy is the frequency brake (owner's choice over a cooldown, 2026-06-22):
    # no energy → can't dig (no move, no loot, no energy spent) until it refills
    # over time or you eat a ration / energy drink.
    now = int(time.time())
    e_state = energy.EnergyState(*await db.get_energy(suid, guild_id))
    if not energy.can_dig(e_state, now):
        wait = energy.seconds_until(e_state, now, energy.DIG_COST)
        return DigResult(
            moved=False,
            x=x,
            y=y,
            depth=depth,
            found=None,
            amount=0,
            wear=WearReport(),
            hint=(
                "⚡ You're out of energy — rest a moment "
                f"(~{wait}s until your next dig) or eat a **ration** / "
                "**energy drink** (`!use ration`)."
            ),
        )

    equipped = await db.get_equipment(suid, guild_id)
    # Gear + allocated skill points gate Down (byte-identical to gear-only when
    # nothing is allocated — the additive safety property, as in descend()).
    alloc = await db.get_skills(user_id, guild_id)
    stats = character.character_stats(equipped, alloc)

    target = _resolve_dig_target(direction, x, y, depth, stats)
    if isinstance(target, DigResult):
        return target  # blocked / unknown — no move, no loot
    nx, ny, nz = target

    inventory = await db.get_mining_inventory(suid, guild_id)
    seed = await db.get_world_seed(guild_id)
    cell = grid.cell_at(seed, nx, ny, nz)
    found, amount = rewards.roll_mine_loot(
        has_pickaxe=inventory.get("pickaxe", 0) > 0,
        depth=nz,
        multiplier=rewards.mine_multiplier(equipped, inventory),
    )
    found, amount, cell_note = grid.apply_cell_to_loot(cell, found, amount)
    candidates = _wear_candidates(workshop.ACTION_MINE, nz, equipped)
    wear = await db.get_gear_wear(suid, guild_id) if candidates else {}

    awards: list[game_xp_service.GameXpAward] = []
    descended = direction == grid.DOWN
    spent = energy.spend(e_state, now)
    async with db.transaction() as conn:
        await db.set_energy(suid, guild_id, spent.current, spent.updated_at, conn=conn)
        if direction in grid.LATERAL:
            await db.set_position(suid, guild_id, nx, ny, conn=conn)
        else:
            await db.set_depth(suid, guild_id, nz, conn=conn)
        await db.update_mining_item(suid, guild_id, found, amount, conn=conn)
        await db.mark_discovered(suid, guild_id, nz, nx, ny, conn=conn)
        report = (
            await _apply_wear_writes(conn, suid, guild_id, candidates, wear)
            if candidates
            else WearReport()
        )
        if descended and await db.record_depth(suid, guild_id, nz, conn=conn):
            record = await game_xp_service.award(
                guild_id,
                user_id,
                game=game_xp_service.GAME_MINING,
                action="depth_record",
                conn=conn,
            )
            if record is not None:
                awards.append(record)
        mined = await game_xp_service.award(
            guild_id,
            user_id,
            game=game_xp_service.GAME_MINING,
            action="mine",
            depth=nz,
            conn=conn,
        )
        if mined is not None:
            awards.append(mined)
    for award in awards:
        await game_xp_service.emit_award_events(award)
    xp_note = next((a.note for a in awards if a.leveled_up), None)
    return DigResult(
        moved=True,
        x=nx,
        y=ny,
        depth=nz,
        found=found,
        amount=amount,
        wear=report,
        cell_note=cell_note,
        xp_note=xp_note,
        pack_warning=_pack_warning_after(inventory, found),
    )


async def reseed_world(guild_id: int, seed: int) -> int:
    """Set the guild's shared world *seed* (PR 3) — the owner re-seed.

    Returns the seed stored.  Re-seeding changes the procedural world everyone in
    the guild roams (Q-0173: one shared, shareable grid per seed); player
    positions and fog-of-war are coordinates, so they are unaffected.
    """
    await db.set_world_seed(guild_id, seed)
    return seed


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------


async def admin_reset(user_id: int, guild_id: int, *, actor_id: int) -> None:
    """Admin reset of a user's mining inventory in ONE guild (logged)."""
    logger.info(
        "mining admin_reset: actor=%s -> user=%s guild=%s",
        actor_id,
        user_id,
        guild_id,
    )
    await db.set_mining_inventory(str(user_id), guild_id, {})


__all__ = [
    "MineResult",
    "HarvestResult",
    "ExploreActionResult",
    "DescentResult",
    "DigResult",
    "wear_tick",
    "repair",
    "craft",
    "quick_craft",
    "sell",
    "sell_all",
    "buy",
    "vault_deposit",
    "vault_withdraw",
    "vault_deposit_all_resources",
    "vault_upgrade",
    "build_structure",
    "mine",
    "harvest",
    "explore",
    "use_item",
    "equip",
    "unequip",
    "descend",
    "ascend",
    "dig",
    "reseed_world",
    "admin_reset",
]
