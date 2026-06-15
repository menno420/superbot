"""Tests for the mining Vault seam (services.mining_workflow vault ops).

The vault is a safe stash separate from the active pack: deposit moves items
out of ``mining_inventory`` into ``mining_vault``, withdraw moves them back.
These tests pin the *contract* — both legs of a move run on the workflow's
transaction conn (atomic), a move you can't afford writes nothing, and
"stash all" touches only raw resources — without a real DB (the CRUD
primitives are mocked).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from services import mining_workflow


@pytest.fixture(autouse=True)
def _null_workflow_transaction():
    """db.transaction() becomes a pass-through — primitives are mocked here."""

    @asynccontextmanager
    async def _txn():
        yield MagicMock(name="test_conn")

    with patch("services.mining_workflow.db.transaction", _txn):
        yield


# ---------------------------------------------------------------------------
# Deposit (inventory → vault)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_deposit_debits_inventory_and_credits_vault_atomically():
    with (
        patch(
            "services.mining_workflow.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"diamond": 5},
        ),
        patch(
            "services.mining_workflow.db.update_mining_item",
            new_callable=AsyncMock,
        ) as mock_inv,
        patch(
            "services.mining_workflow.db.update_vault_item",
            new_callable=AsyncMock,
        ) as mock_vault,
    ):
        result = await mining_workflow.vault_deposit(123, 7, "diamond", 3)
    assert result.ok
    # Both legs run on the workflow's transaction conn (atomic move).
    mock_inv.assert_awaited_once_with("123", 7, "diamond", -3, conn=ANY)
    mock_vault.assert_awaited_once_with("123", 7, "diamond", 3, conn=ANY)


@pytest.mark.asyncio
async def test_deposit_rejects_more_than_owned_without_writing():
    with (
        patch(
            "services.mining_workflow.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"iron": 2},
        ),
        patch(
            "services.mining_workflow.db.update_mining_item",
            new_callable=AsyncMock,
        ) as mock_inv,
        patch(
            "services.mining_workflow.db.update_vault_item",
            new_callable=AsyncMock,
        ) as mock_vault,
    ):
        result = await mining_workflow.vault_deposit(1, 1, "iron", 5)
    assert not result.ok
    mock_inv.assert_not_awaited()  # never move items you don't have
    mock_vault.assert_not_awaited()


@pytest.mark.asyncio
async def test_deposit_rejects_nonpositive_before_any_io():
    with patch(
        "services.mining_workflow.db.get_mining_inventory",
        new_callable=AsyncMock,
    ) as mock_read:
        result = await mining_workflow.vault_deposit(1, 1, "diamond", 0)
    assert not result.ok
    assert "positive" in result.message.lower()
    mock_read.assert_not_awaited()


# ---------------------------------------------------------------------------
# Withdraw (vault → inventory)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_withdraw_debits_vault_and_credits_inventory_atomically():
    with (
        patch(
            "services.mining_workflow.db.get_vault",
            new_callable=AsyncMock,
            return_value={"diamond": 5},
        ),
        patch(
            "services.mining_workflow.db.update_vault_item",
            new_callable=AsyncMock,
        ) as mock_vault,
        patch(
            "services.mining_workflow.db.update_mining_item",
            new_callable=AsyncMock,
        ) as mock_inv,
    ):
        result = await mining_workflow.vault_withdraw(123, 7, "diamond", 2)
    assert result.ok
    mock_vault.assert_awaited_once_with("123", 7, "diamond", -2, conn=ANY)
    mock_inv.assert_awaited_once_with("123", 7, "diamond", 2, conn=ANY)


@pytest.mark.asyncio
async def test_withdraw_rejects_more_than_stored_without_writing():
    with (
        patch(
            "services.mining_workflow.db.get_vault",
            new_callable=AsyncMock,
            return_value={"diamond": 1},
        ),
        patch(
            "services.mining_workflow.db.update_vault_item",
            new_callable=AsyncMock,
        ) as mock_vault,
        patch(
            "services.mining_workflow.db.update_mining_item",
            new_callable=AsyncMock,
        ) as mock_inv,
    ):
        result = await mining_workflow.vault_withdraw(1, 1, "diamond", 9)
    assert not result.ok
    mock_vault.assert_not_awaited()
    mock_inv.assert_not_awaited()


# ---------------------------------------------------------------------------
# Stash all ore (one-click convenience)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stash_all_moves_only_resources_in_one_transaction():
    with (
        patch(
            "services.mining_workflow.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"stone": 4, "diamond": 1, "pickaxe": 1, "iron sword": 1},
        ),
        patch(
            "services.mining_workflow.db.update_mining_item",
            new_callable=AsyncMock,
        ) as mock_inv,
        patch(
            "services.mining_workflow.db.update_vault_item",
            new_callable=AsyncMock,
        ) as mock_vault,
    ):
        result = await mining_workflow.vault_deposit_all_resources(1, 1)
    assert result.ok
    moved = {call.args[2] for call in mock_inv.await_args_list}
    assert {"stone", "diamond"} <= moved
    assert "pickaxe" not in moved  # tools stay in the pack
    assert "iron sword" not in moved  # gear stays in the pack
    # every resource is mirrored into the vault
    assert {call.args[2] for call in mock_vault.await_args_list} == moved


@pytest.mark.asyncio
async def test_stash_all_with_no_resources_writes_nothing():
    with (
        patch(
            "services.mining_workflow.db.get_mining_inventory",
            new_callable=AsyncMock,
            return_value={"pickaxe": 1},  # only non-resource items
        ),
        patch(
            "services.mining_workflow.db.update_mining_item",
            new_callable=AsyncMock,
        ) as mock_inv,
        patch(
            "services.mining_workflow.db.update_vault_item",
            new_callable=AsyncMock,
        ) as mock_vault,
    ):
        result = await mining_workflow.vault_deposit_all_resources(1, 1)
    assert not result.ok
    mock_inv.assert_not_awaited()
    mock_vault.assert_not_awaited()


# ---------------------------------------------------------------------------
# Pack soft-cap nudge on mining actions (Slice A — warns, never blocks)
# ---------------------------------------------------------------------------


def test_pack_warning_after_fires_only_when_a_new_type_reaches_the_cap():
    from utils.mining import capacity

    # One slot below the cap, granting a NEW type tips it over → nudge.
    near_full = {f"item{i}": 1 for i in range(capacity.PACK_SOFT_CAP - 1)}
    assert mining_workflow._pack_warning_after(near_full, "diamond") is not None
    # Same pack, but the grant tops up an existing type → still below cap → quiet.
    assert mining_workflow._pack_warning_after(near_full, "item0") is None
    # A roomy pack never nags.
    assert mining_workflow._pack_warning_after({"stone": 5}, "iron") is None


# ---------------------------------------------------------------------------
# Vault upgrade (Slice A — the coin sink)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_vault_upgrade_debits_coins_and_raises_level_atomically():
    with (
        patch(
            "services.mining_workflow.db.get_vault_level",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "services.mining_workflow.economy_service.debit_in_txn",
            new_callable=AsyncMock,
            return_value=12345,
        ) as mock_debit,
        patch(
            "services.mining_workflow.db.set_vault_level",
            new_callable=AsyncMock,
        ) as mock_level,
        patch(
            "services.mining_workflow._emit_balance",
            new_callable=AsyncMock,
        ) as mock_emit,
    ):
        result = await mining_workflow.vault_upgrade(123, 7)
    assert result.ok
    # Coin debit + level raise both run on the workflow's transaction conn.
    mock_debit.assert_awaited_once()
    mock_level.assert_awaited_once_with("123", 7, 1, conn=ANY)
    # Balance event emits only after commit.
    mock_emit.assert_awaited_once()


@pytest.mark.asyncio
async def test_vault_upgrade_at_max_level_charges_nothing():
    from utils.mining import capacity

    with (
        patch(
            "services.mining_workflow.db.get_vault_level",
            new_callable=AsyncMock,
            return_value=capacity.MAX_VAULT_LEVEL,
        ),
        patch(
            "services.mining_workflow.economy_service.debit_in_txn",
            new_callable=AsyncMock,
        ) as mock_debit,
        patch(
            "services.mining_workflow.db.set_vault_level",
            new_callable=AsyncMock,
        ) as mock_level,
    ):
        result = await mining_workflow.vault_upgrade(1, 1)
    assert not result.ok
    assert "maximum" in result.message.lower()
    mock_debit.assert_not_awaited()  # nothing charged at the ceiling
    mock_level.assert_not_awaited()


@pytest.mark.asyncio
async def test_vault_upgrade_insufficient_funds_writes_nothing():
    with (
        patch(
            "services.mining_workflow.db.get_vault_level",
            new_callable=AsyncMock,
            return_value=0,
        ),
        patch(
            "services.mining_workflow.economy_service.debit_in_txn",
            new_callable=AsyncMock,
            side_effect=mining_workflow.economy_service.InsufficientFundsError(),
        ),
        patch(
            "services.mining_workflow.db.set_vault_level",
            new_callable=AsyncMock,
        ) as mock_level,
        patch(
            "services.mining_workflow.db.get_coins",
            new_callable=AsyncMock,
            return_value=5,
        ),
    ):
        result = await mining_workflow.vault_upgrade(1, 1)
    assert not result.ok
    assert "🪙" in result.message
    mock_level.assert_not_awaited()  # no level change without payment
