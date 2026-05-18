"""Phase 2c PR-9 — utils.db.user_participation write primitives.

The PR-8 read primitives are covered in
``test_user_participation_db.py``.  This file adds the four new
PR-9 atomic write+audit primitives:

* ``upsert_participation_with_audit``
* ``upsert_subscription_with_audit``
* ``upsert_preference_with_audit``
* ``upsert_visibility_with_audit``
* ``get_audit_count``

Each must issue both statements (target table UPSERT + audit row
INSERT) inside the SAME transaction so partial failures roll back.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.db import user_participation as up_db


@pytest.fixture
def _mock_pool_with_transaction():
    """Pool fixture providing both autocommit AND transactional contexts.

    Returns ``(pool_mock, conn_mock)``.  ``conn_mock.execute`` records
    every statement issued inside the transaction in the order it ran;
    tests assert against ``conn_mock.execute.await_args_list``.
    """
    conn = MagicMock()
    conn.execute = AsyncMock()

    txn_cm = MagicMock()
    txn_cm.__aenter__ = AsyncMock(return_value=None)
    txn_cm.__aexit__ = AsyncMock(return_value=False)
    conn.transaction = MagicMock(return_value=txn_cm)

    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=False)

    pool_mock = MagicMock()
    pool_mock.acquire = MagicMock(return_value=acquire_cm)
    pool_mock.fetchrow = AsyncMock()
    with patch.object(up_db, "pool") as pool_module:
        pool_module.get = MagicMock(return_value=pool_mock)
        yield pool_mock, conn


# ---------------------------------------------------------------------------
# upsert_participation_with_audit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_participation_issues_two_statements_in_transaction(
    _mock_pool_with_transaction,
):
    _pool, conn = _mock_pool_with_transaction
    await up_db.upsert_participation_with_audit(
        user_id=1,
        guild_id=2,
        subsystem="xp",
        state="opted_out",
        actor_id=1,
        actor_type="user",
        mutation_id="abc-mutation",
        prev_state=None,
    )
    # Two statements: UPSERT + audit INSERT
    assert conn.execute.await_count == 2
    upsert_sql = conn.execute.await_args_list[0].args[0]
    audit_sql = conn.execute.await_args_list[1].args[0]
    assert "INSERT INTO user_participation" in upsert_sql
    assert "ON CONFLICT (user_id, guild_id, subsystem)" in upsert_sql
    assert "INSERT INTO user_participation_audit" in audit_sql
    assert "'set_participation'" in audit_sql
    # Transaction was opened
    conn.transaction.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_participation_records_prev_state_in_audit(
    _mock_pool_with_transaction,
):
    _pool, conn = _mock_pool_with_transaction
    await up_db.upsert_participation_with_audit(
        user_id=1,
        guild_id=2,
        subsystem="xp",
        state="opted_in",
        actor_id=1,
        actor_type="user",
        mutation_id="abc",
        prev_state="opted_out",
    )
    audit_call = conn.execute.await_args_list[1]
    # Args: $1=mutation_id $2=user_id $3=guild_id $4=subsystem
    #       $5=prev_state $6=new_state $7=actor_id $8=actor_type
    args = audit_call.args[1:]
    assert args[0] == "abc"
    assert args[1] == 1
    assert args[2] == 2
    assert args[3] == "xp"
    assert args[4] == "opted_out"  # prev_state
    assert args[5] == "opted_in"  # new_state


# ---------------------------------------------------------------------------
# upsert_subscription_with_audit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_subscription_issues_two_statements(
    _mock_pool_with_transaction,
):
    _pool, conn = _mock_pool_with_transaction
    await up_db.upsert_subscription_with_audit(
        user_id=1,
        guild_id=2,
        subsystem="economy",
        topic="daily",
        enabled=False,
        actor_id=1,
        actor_type="user",
        mutation_id="abc",
        prev_enabled=True,
    )
    assert conn.execute.await_count == 2
    upsert_sql = conn.execute.await_args_list[0].args[0]
    audit_sql = conn.execute.await_args_list[1].args[0]
    assert "INSERT INTO user_subscriptions" in upsert_sql
    assert "INSERT INTO user_participation_audit" in audit_sql
    assert "'set_subscription'" in audit_sql


# ---------------------------------------------------------------------------
# upsert_preference_with_audit — JSON encoding of value
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_preference_json_encodes_value(_mock_pool_with_transaction):
    _pool, conn = _mock_pool_with_transaction
    payload = {"unit": "hours", "interval": 6}
    await up_db.upsert_preference_with_audit(
        user_id=1,
        guild_id=2,
        key="digest_freq",
        value=payload,
        actor_id=1,
        actor_type="user",
        mutation_id="abc",
        prev_value=None,
    )
    upsert_call = conn.execute.await_args_list[0]
    # value is positional arg index 4 in the upsert statement
    serialised_value = upsert_call.args[4]
    assert json.loads(serialised_value) == payload


@pytest.mark.asyncio
async def test_upsert_preference_none_prev_passed_as_null(_mock_pool_with_transaction):
    _pool, conn = _mock_pool_with_transaction
    await up_db.upsert_preference_with_audit(
        user_id=1,
        guild_id=2,
        key="digest_freq",
        value={"x": 1},
        actor_id=1,
        actor_type="user",
        mutation_id="abc",
        prev_value=None,
    )
    audit_call = conn.execute.await_args_list[1]
    # prev_value is the 6th positional arg (index 5 after sql)
    assert audit_call.args[5] is None


# ---------------------------------------------------------------------------
# upsert_visibility_with_audit
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_upsert_visibility_issues_two_statements(_mock_pool_with_transaction):
    _pool, conn = _mock_pool_with_transaction
    await up_db.upsert_visibility_with_audit(
        user_id=1,
        guild_id=2,
        subsystem="xp",
        visibility="hidden",
        actor_id=1,
        actor_type="user",
        mutation_id="abc",
        prev_visibility="public",
    )
    assert conn.execute.await_count == 2
    upsert_sql = conn.execute.await_args_list[0].args[0]
    audit_sql = conn.execute.await_args_list[1].args[0]
    assert "INSERT INTO user_visibility_overrides" in upsert_sql
    assert "INSERT INTO user_participation_audit" in audit_sql
    assert "'set_visibility'" in audit_sql


# ---------------------------------------------------------------------------
# get_audit_count
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_audit_count_no_filter(_mock_pool_with_transaction):
    pool_mock, _ = _mock_pool_with_transaction
    pool_mock.fetchrow.return_value = {"n": 7}
    assert await up_db.get_audit_count() == 7
    sql, *args = pool_mock.fetchrow.await_args.args
    assert "FROM user_participation_audit" in sql
    assert "WHERE" not in sql
    assert args == []


@pytest.mark.asyncio
async def test_get_audit_count_filtered(_mock_pool_with_transaction):
    pool_mock, _ = _mock_pool_with_transaction
    pool_mock.fetchrow.return_value = {"n": 3}
    n = await up_db.get_audit_count(
        user_id=42,
        guild_id=99,
        mutation_type="set_participation",
    )
    assert n == 3
    sql, *args = pool_mock.fetchrow.await_args.args
    assert "user_id = $1" in sql
    assert "guild_id = $2" in sql
    assert "mutation_type = $3" in sql
    assert args == [42, 99, "set_participation"]
