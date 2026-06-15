"""RS02 characterization net — exact user-visible contract of mining writes.

Pinned BEFORE the workflow-service extraction (consolidated plan Batch 7:
"characterize → extract the workshop workflow first → market/exploration
follow"), so the refactor that moves these operations behind
``services/mining_workflow.py`` must keep every message, reason tag, and
call shape byte-identical.  When an operation moves, ONLY the import /
patch-path constants below change — never an expected string.

The patch-path constants point at the module that currently OWNS each
operation:  ``_WS`` (workshop ops) and ``_MK`` (market ops).
"""

from __future__ import annotations

from unittest.mock import ANY, AsyncMock, patch

import pytest

from services import mining_workflow
from services.economy_service import InsufficientFundsError
from utils.mining import market as market_mod
from utils.mining import workshop as workshop_mod

# Current owners — the RS02 extraction updates these (and only these).
_WS = "services.mining_workflow"
_MK = "services.mining_workflow"

craft = mining_workflow.craft
repair = mining_workflow.repair
quick_craft = mining_workflow.quick_craft
wear_tick = mining_workflow.wear_tick
buy = mining_workflow.buy
sell = mining_workflow.sell
sell_all = mining_workflow.sell_all


ACTION_MINE = workshop_mod.ACTION_MINE


@pytest.fixture(autouse=True)
def _null_workflow_transaction():
    """Replace db.transaction() with a no-op context manager.

    The workflow service wraps its writes in ONE db.transaction(); these
    characterization tests patch the write primitives themselves, so the
    transaction becomes a pass-through yielding a sentinel connection.
    The conn= kwarg the primitives receive is asserted with mock.ANY.
    """
    from contextlib import asynccontextmanager
    from unittest.mock import MagicMock

    @asynccontextmanager
    async def _txn():
        yield MagicMock(name="characterization_conn")

    with (
        patch("services.mining_workflow.db.transaction", _txn),
        patch(
            "services.mining_workflow.game_xp_service.award",
            AsyncMock(return_value=None),
        ),
        patch(
            "services.mining_workflow.game_xp_service.emit_award_events",
            AsyncMock(),
        ),
    ):
        yield


# ---------------------------------------------------------------------------
# Reason tags — economy_audit_log filter keys, byte-identical forever.
# ---------------------------------------------------------------------------


def test_audit_reason_tags_are_pinned():
    assert workshop_mod.REPAIR_REASON == "mining:repair_gear"
    assert market_mod.SELL_REASON == "mining:sell_ore"
    assert market_mod.BUY_REASON == "mining:buy_gear"


# ---------------------------------------------------------------------------
# Craft
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_craft_success_message():
    with (
        patch(
            f"{_WS}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"wood": 10, "stone": 10},
        ),
        patch(f"{_WS}.db.apply_inventory_deltas", new_callable=AsyncMock) as deltas,
    ):
        result = await craft(1, 99, "pickaxe")
    assert result.ok is True
    assert result.message == "Crafted **pickaxe**!"
    # Materials + product move in ONE call (the atomicity seam).
    applied = deltas.await_args.args[2]
    assert applied == {"wood": -2, "stone": -3, "pickaxe": 1}


@pytest.mark.asyncio
async def test_craft_unknown_recipe_buyable_hint():
    with patch(
        f"{_WS}.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={},
    ):
        result = await craft(1, 99, "dynamite")  # in GEAR_SHOP, no recipe
    assert result.ok is False
    assert result.message == (
        "No recipe for **dynamite**. You can buy one at the 🛒 Market instead."
    )


@pytest.mark.asyncio
async def test_craft_unknown_recipe_buildlist_hint():
    with patch(
        f"{_WS}.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={},
    ):
        result = await craft(1, 99, "spaceship")
    assert result.ok is False
    assert result.message == (
        "No recipe for **spaceship**. Use `!buildlist` to see available recipes."
    )


@pytest.mark.asyncio
async def test_craft_missing_materials_message():
    with patch(
        f"{_WS}.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"wood": 1},
    ):
        result = await craft(1, 99, "pickaxe")  # needs wood 2, stone 3
    assert result.ok is False
    assert result.message == (
        "You don't have enough **wood** to craft **pickaxe** "
        "(needs 3× stone, 2× wood)."
    )


# ---------------------------------------------------------------------------
# Repair
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_repair_not_wearable_message():
    result = await repair(1, 99, "stone hut")
    assert result.message == "**stone hut** doesn't wear out."


@pytest.mark.asyncio
async def test_repair_not_owned_message():
    with patch(
        f"{_WS}.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={},
    ):
        result = await repair(1, 99, "pickaxe")
    assert result.message == "You don't own a **pickaxe** to repair."


@pytest.mark.asyncio
async def test_repair_full_durability_message():
    with (
        patch(
            f"{_WS}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"pickaxe": 1},
        ),
        patch(f"{_WS}.db.get_gear_wear", new_callable=AsyncMock, return_value={}),
    ):
        result = await repair(1, 99, "pickaxe")
    assert result.message == "Your **pickaxe** is already at full durability."


@pytest.mark.asyncio
async def test_repair_insufficient_funds_message_and_no_wear_clear():
    with (
        patch(
            f"{_WS}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"pickaxe": 1},
        ),
        patch(
            f"{_WS}.db.get_gear_wear",
            new_callable=AsyncMock,
            return_value={"pickaxe": 30},  # cost: ceil(13 * 30/60) = 7
        ),
        patch(
            f"{_WS}.economy_service.debit_in_txn",
            new_callable=AsyncMock,
            side_effect=InsufficientFundsError("no"),
        ),
        patch(f"{_WS}.db.get_coins", new_callable=AsyncMock, return_value=3),
        patch(f"{_WS}.db.clear_gear_wear", new_callable=AsyncMock) as clear,
    ):
        result = await repair(1, 99, "pickaxe")
    assert result.ok is False
    assert result.message == (
        "Repairing **pickaxe** costs **7** 🪙 — you only have **3** 🪙."
    )
    clear.assert_not_called()


@pytest.mark.asyncio
async def test_repair_success_message_costs_and_reason():
    with (
        patch(
            f"{_WS}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"pickaxe": 1},
        ),
        patch(
            f"{_WS}.db.get_gear_wear",
            new_callable=AsyncMock,
            return_value={"pickaxe": 30},
        ),
        patch(
            f"{_WS}.economy_service.debit_in_txn",
            new_callable=AsyncMock,
            return_value=93,
        ) as debit,
        patch(f"{_WS}.db.clear_gear_wear", new_callable=AsyncMock) as clear,
    ):
        result = await repair(1, 99, "pickaxe")
    assert result.ok is True
    assert result.message == (
        "Repaired **pickaxe** to full durability for **7** 🪙. " "Balance: **93** 🪙."
    )
    assert result.coins_delta == -7
    assert result.new_balance == 93
    assert debit.await_args.kwargs["reason"] == "mining:repair_gear"
    clear.assert_awaited_once()


# ---------------------------------------------------------------------------
# Quick-craft
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_quick_craft_nothing_broken_message():
    with patch(
        f"{_WS}.db.get_last_broken",
        new_callable=AsyncMock,
        return_value=None,
    ):
        result = await quick_craft(1, 99)
    assert result.message == (
        "Nothing has broken recently — craft or repair gear below."
    )


@pytest.mark.asyncio
async def test_quick_craft_crafts_equips_and_clears_marker():
    with (
        patch(
            f"{_WS}.db.get_last_broken",
            new_callable=AsyncMock,
            return_value="torch",
        ),
        patch(
            f"{_WS}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"wood": 5},
        ),
        patch(f"{_WS}.db.apply_inventory_deltas", new_callable=AsyncMock),
        patch(f"{_WS}.db.get_equipment", new_callable=AsyncMock, return_value={}),
        patch(f"{_WS}.db.equip_item", new_callable=AsyncMock) as equip,
        patch(f"{_WS}.db.set_last_broken", new_callable=AsyncMock) as clear_last,
    ):
        result = await quick_craft(1, 99)
    assert result.ok is True
    assert result.message == (
        "Crafted **torch** and equipped it in the **light** slot!"
    )
    equip.assert_awaited_once_with("1", 99, "light", "torch", conn=ANY)
    clear_last.assert_awaited_once_with("1", 99, None, conn=ANY)


@pytest.mark.asyncio
async def test_quick_craft_slot_occupied_keeps_plain_message():
    with (
        patch(
            f"{_WS}.db.get_last_broken",
            new_callable=AsyncMock,
            return_value="torch",
        ),
        patch(
            f"{_WS}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"wood": 5},
        ),
        patch(f"{_WS}.db.apply_inventory_deltas", new_callable=AsyncMock),
        patch(
            f"{_WS}.db.get_equipment",
            new_callable=AsyncMock,
            return_value={"light": "lantern"},
        ),
        patch(f"{_WS}.db.equip_item", new_callable=AsyncMock) as equip,
        patch(f"{_WS}.db.set_last_broken", new_callable=AsyncMock),
    ):
        result = await quick_craft(1, 99)
    assert result.message == "Crafted **torch**!"
    equip.assert_not_called()


# ---------------------------------------------------------------------------
# Wear tick (break + low-durability notes)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_wear_break_consumes_unequips_and_notes():
    with (
        patch(
            f"{_WS}.db.get_gear_wear",
            new_callable=AsyncMock,
            return_value={"pickaxe": 1},  # next tick → 0 → break
        ),
        patch(f"{_WS}.db.clear_gear_wear", new_callable=AsyncMock) as clear,
        patch(f"{_WS}.db.update_mining_item", new_callable=AsyncMock) as consume,
        patch(f"{_WS}.db.unequip_slot", new_callable=AsyncMock) as unequip,
        patch(f"{_WS}.db.set_last_broken", new_callable=AsyncMock) as last,
        patch(f"{_WS}.db.set_gear_wear", new_callable=AsyncMock),
    ):
        report = await wear_tick(
            1,
            99,
            action=ACTION_MINE,
            depth=0,
            equipped={"tool": "pickaxe"},
        )
    assert report.broke == ("pickaxe",)
    assert report.notes == (
        "💥 Your **pickaxe** broke! Re-craft or repair gear at the 🔧 Workshop.",
    )
    clear.assert_awaited_once_with("1", 99, "pickaxe", conn=ANY)
    consume.assert_awaited_once_with("1", 99, "pickaxe", -1, conn=ANY)
    unequip.assert_awaited_once_with("1", 99, "tool", conn=ANY)
    last.assert_awaited_once_with("1", 99, "pickaxe", conn=ANY)


@pytest.mark.asyncio
async def test_wear_low_durability_warning_note():
    with (
        patch(
            f"{_WS}.db.get_gear_wear",
            new_callable=AsyncMock,
            return_value={"pickaxe": 6},  # 6 → 5 = LOW_DURABILITY_WARN
        ),
        patch(f"{_WS}.db.set_gear_wear", new_callable=AsyncMock) as set_wear,
    ):
        report = await wear_tick(
            1,
            99,
            action=ACTION_MINE,
            depth=0,
            equipped={"tool": "pickaxe"},
        )
    assert report.broke == ()
    assert report.notes == (
        "⚠️ Your **pickaxe** is nearly worn out (5/60) — repair it at the "
        "🔧 Workshop.",
    )
    set_wear.assert_awaited_once_with("1", 99, "pickaxe", 5, conn=ANY)


@pytest.mark.asyncio
async def test_wear_light_spared_on_surface():
    """Underground-only slots don't wear at depth 0."""
    with (
        patch(
            f"{_WS}.db.get_gear_wear",
            new_callable=AsyncMock,
            return_value={},
        ),
        patch(f"{_WS}.db.set_gear_wear", new_callable=AsyncMock) as set_wear,
    ):
        report = await wear_tick(
            1,
            99,
            action=ACTION_MINE,
            depth=0,
            equipped={"light": "torch"},
        )
    assert report.notes == ()
    set_wear.assert_not_called()


# ---------------------------------------------------------------------------
# Market (sell / sell-all / buy) — extracted in RS02 stage 2; pinned now.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sell_messages_and_reason():
    result = await sell(1, 99, "pickaxe", 1)  # tools never sell
    assert result.message == "You can't sell **pickaxe** — only raw resources sell."

    with patch(
        f"{_MK}.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={"iron": 2},
    ):
        result = await sell(1, 99, "iron", 5)
    assert result.message == "You only have **2× iron** to sell."

    with (
        patch(
            f"{_MK}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"iron": 5},
        ),
        patch(f"{_MK}.db.update_mining_item", new_callable=AsyncMock),
        patch(
            f"{_MK}.economy_service.credit_in_txn",
            new_callable=AsyncMock,
            return_value=115,
        ) as credit,
    ):
        result = await sell(1, 99, "iron", 5)
    assert result.ok is True
    assert result.message == ("Sold **5× iron** for **15** 🪙. Balance: **115** 🪙.")
    assert credit.await_args.kwargs["reason"] == "mining:sell_ore"


@pytest.mark.asyncio
async def test_sell_all_messages():
    with patch(
        f"{_MK}.db.get_mining_inventory",
        new_callable=AsyncMock,
        return_value={},
    ):
        result = await sell_all(1, 99)
    assert result.message == "You have no resources to sell — go mine some!"

    with (
        patch(
            f"{_MK}.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"iron": 2, "wood": 3},
        ),
        patch(f"{_MK}.db.update_mining_item", new_callable=AsyncMock) as remove,
        patch(
            f"{_MK}.economy_service.credit_in_txn",
            new_callable=AsyncMock,
            return_value=109,
        ),
    ):
        result = await sell_all(1, 99)
    assert result.ok is True
    # sellable_inventory orders by unit price desc then name: iron(3), wood(1)
    assert result.message == (
        "Sold 2× iron, 3× wood for **9** 🪙. Balance: **109** 🪙."
    )
    assert remove.await_count == 2


@pytest.mark.asyncio
async def test_buy_messages_and_reason():
    result = await buy(1, 99, "spaceship")
    assert result.message == "**spaceship** isn't for sale. Check `!market` for stock."

    with (
        patch(
            f"{_MK}.economy_service.debit_in_txn",
            new_callable=AsyncMock,
            side_effect=InsufficientFundsError("no"),
        ),
        patch(f"{_MK}.db.get_coins", new_callable=AsyncMock, return_value=4),
    ):
        result = await buy(1, 99, "torch")
    assert result.message == "**torch** costs **10** 🪙 — you only have **4** 🪙."

    with (
        patch(
            f"{_MK}.economy_service.debit_in_txn",
            new_callable=AsyncMock,
            return_value=90,
        ) as debit,
        patch(f"{_MK}.db.update_mining_item", new_callable=AsyncMock) as grant,
    ):
        result = await buy(1, 99, "torch")
    assert result.ok is True
    assert result.message == (
        "Bought **torch** for **10** 🪙. Balance: **90** 🪙. "
        "Use `!equip torch` to wear it."
    )
    assert debit.await_args.kwargs["reason"] == "mining:buy_gear"
    grant.assert_awaited_once_with("1", 99, "torch", 1, conn=ANY)


# ---------------------------------------------------------------------------
# Command ↔ panel parity — both surfaces call the SAME implementation.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_repair_command_and_panel_share_one_implementation():
    """`!repair x` and the workshop panel's repair select call the same
    function object, so behavior can never drift between surfaces."""
    import cogs.mining_cog as cog_mod
    from views.mining import workshop_panel

    calls: list[tuple] = []

    async def _spy(user_id, guild_id, item):
        calls.append((user_id, guild_id, item))
        from utils.mining.market import TradeResult

        return TradeResult(True, "ok")

    with patch("services.mining_workflow.repair", AsyncMock(side_effect=_spy)):
        # Command path
        cog = cog_mod.MiningCog.__new__(cog_mod.MiningCog)
        ctx = AsyncMock()
        ctx.author.id = 1
        ctx.guild.id = 99
        await cog_mod.MiningCog.repair.callback(cog, ctx, item="pickaxe")
        # Panel path
        select = _make_select(workshop_panel._RepairSelect, "pickaxe")
        interaction = AsyncMock()
        with (
            patch(
                "views.mining.workshop_panel.safe_defer",
                AsyncMock(return_value=True),
            ),
            patch(
                "views.mining.workshop_panel._rerender",
                AsyncMock(),
            ),
        ):
            await workshop_panel._RepairSelect.callback(select, interaction)

    assert calls == [(1, 99, "pickaxe"), (1, 99, "pickaxe")]


@pytest.mark.asyncio
async def test_craft_command_modal_and_panel_share_one_implementation():
    import cogs.mining_cog as cog_mod
    from views.mining import workshop_panel
    from views.mining.main_panel import _BuildModal

    calls: list[tuple] = []

    async def _spy(user_id, guild_id, item):
        calls.append((user_id, guild_id, item))
        from utils.mining.market import TradeResult

        return TradeResult(True, "ok")

    with patch("services.mining_workflow.craft", AsyncMock(side_effect=_spy)):
        cog = cog_mod.MiningCog.__new__(cog_mod.MiningCog)
        cog.bot = AsyncMock()
        ctx = AsyncMock()
        ctx.author.id = 1
        ctx.guild.id = 99
        await cog_mod.MiningCog.build.callback(cog, ctx, structure="torch")

        modal = _BuildModal.__new__(_BuildModal)
        structure_input = AsyncMock()
        structure_input.value = "torch"
        object.__setattr__(modal, "_children", [])
        modal.__dict__["structure"] = structure_input
        interaction = AsyncMock()
        interaction.guild_id = 99
        interaction.user.id = 1
        await _BuildModal.on_submit(modal, interaction)

        select = _make_select(workshop_panel._CraftSelect, "torch")
        interaction2 = AsyncMock()
        with (
            patch(
                "views.mining.workshop_panel.safe_defer",
                AsyncMock(return_value=True),
            ),
            patch("views.mining.workshop_panel._rerender", AsyncMock()),
        ):
            await workshop_panel._CraftSelect.callback(select, interaction2)

    assert calls == [(1, 99, "torch"), (1, 99, "torch"), (1, 99, "torch")]


def _make_select(cls, value):
    """Mock select carrying the attributes the callback reads (repo idiom:
    drive the class-level callback with a MagicMock instance —
    ``cls.callback(select, interaction)``)."""
    from unittest.mock import MagicMock

    select = MagicMock(spec_set=None)
    select._user_id = 1
    select._guild_id = 99
    select.values = [value]
    return select
