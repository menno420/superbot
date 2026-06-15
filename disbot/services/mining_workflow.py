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
from dataclasses import dataclass

from core.events import bus
from services import economy_service, game_xp_service
from utils import db, equipment
from utils.mining import capacity, character, market, rewards, workshop, world
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
    """Consume one *item* from the inventory (flavor only, for now)."""
    item = item.strip().lower()
    suid = str(user_id)
    inventory = await db.get_mining_inventory(suid, guild_id)
    if inventory.get(item, 0) < 1:
        return TradeResult(False, f"You don't have **{item}** to use.")
    if item == "torch":
        message = "You light a torch and peer into the darkness..."
    elif item == "dynamite":
        message = "You ignite dynamite and blow a new path in the mine!"
    else:
        message = f"You used **{item}**, but nothing special happened."
    await db.update_mining_item(suid, guild_id, item, -1)
    return TradeResult(True, message)


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
# Admin
# ---------------------------------------------------------------------------


async def admin_grant(
    user_id: int,
    guild_id: int,
    item: str,
    amount: int,
    *,
    actor_id: int,
) -> None:
    """Admin grant of *amount*× *item* (logged for traceability)."""
    logger.info(
        "mining admin_grant: actor=%s -> user=%s guild=%s %sx %s",
        actor_id,
        user_id,
        guild_id,
        amount,
        item,
    )
    await db.update_mining_item(str(user_id), guild_id, item.lower(), amount)


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
    "mine",
    "harvest",
    "explore",
    "use_item",
    "equip",
    "unequip",
    "descend",
    "ascend",
    "admin_grant",
    "admin_reset",
]
