"""Pin that BTD6 JSONB writers don't pre-encode their dict args.

The asyncpg pool registers a JSONB codec at init
(``utils.db.codec.init_connection``) which calls ``json.dumps`` on the
wire. Pre-encoding via ``json.dumps`` in the writer caused the codec to
re-encode the resulting string, so rows round-tripped through the
``body_json`` column as a JSON string instead of a dict — silently
breaking every reader that did ``isinstance(body, dict) else {}``.

These tests assert the writer passes the dict through as-is.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from utils.db import btd6_sources as btd6_db


@pytest.mark.asyncio
async def test_upsert_fact_passes_body_json_as_dict(monkeypatch):
    seen: dict = {}

    async def _fetchrow(_sql, *args):
        seen["args"] = args
        return {"id": 1}

    fake_pool = MagicMock()
    fake_pool.fetchrow = _fetchrow
    monkeypatch.setattr(btd6_db.pool, "get", lambda: fake_pool)

    body = {"id": "x", "start_ms": 1779019200000, "name": "Reversed Loop"}
    await btd6_db.upsert_fact(
        source_id=1,
        fact_type="btd6.test",
        entity_kind="btd6_test",
        entity_key="x",
        body_json=body,
        game_version=None,
    )

    # The 5th positional arg ($5) is body_json. It must be the dict
    # itself — pre-encoding to a string was the historical bug.
    assert (
        seen["args"][4] is body
    ), f"upsert_fact pre-encoded body_json (got {type(seen['args'][4]).__name__})"


@pytest.mark.asyncio
async def test_insert_ingestion_run_passes_path_params_as_dict(monkeypatch):
    seen: dict = {}

    async def _fetchrow(_sql, *args):
        seen["args"] = args
        return {"id": 1}

    fake_pool = MagicMock()
    fake_pool.fetchrow = _fetchrow
    monkeypatch.setattr(btd6_db.pool, "get", lambda: fake_pool)

    params = {"raceID": "Reversed_Loop_mpbd7tcu"}
    await btd6_db.insert_ingestion_run(
        source_key="nk_btd6_races_metadata",
        status="ok",
        triggered_by="manual",
        path_params_json=params,
        started_by_user_id=None,
    )

    # The 4th positional arg ($4) is path_params_json. Must be the
    # dict, not a JSON string.
    assert seen["args"][3] is params, (
        f"insert_ingestion_run pre-encoded path_params_json "
        f"(got {type(seen['args'][3]).__name__})"
    )


@pytest.mark.asyncio
async def test_insert_ingestion_run_passes_none_when_no_params(monkeypatch):
    """``path_params_json=None`` must propagate as None (not as 'null')."""
    seen: dict = {}

    async def _fetchrow(_sql, *args):
        seen["args"] = args
        return {"id": 1}

    fake_pool = MagicMock()
    fake_pool.fetchrow = _fetchrow
    monkeypatch.setattr(btd6_db.pool, "get", lambda: fake_pool)

    await btd6_db.insert_ingestion_run(
        source_key="nk_btd6_maps",
        status="ok",
        triggered_by="scheduled",
        path_params_json=None,
        started_by_user_id=None,
    )

    assert seen["args"][3] is None


@pytest.mark.asyncio
async def test_record_source_audit_passes_values_as_dicts(monkeypatch):
    seen: dict = {}

    async def _fetchrow(_sql, *args):
        seen["args"] = args
        return {"id": 1}

    fake_pool = MagicMock()
    fake_pool.fetchrow = _fetchrow
    monkeypatch.setattr(btd6_db.pool, "get", lambda: fake_pool)

    old_value = {"enabled": True}
    new_value = {"enabled": False}
    await btd6_db.record_source_audit(
        action="disable",
        source_key="nk_btd6_test",
        old_value=old_value,
        new_value=new_value,
        actor_id=1,
        guild_id=None,
        reason=None,
    )

    # Args order: actor_id, guild_id, source_key, action, old_value, new_value, reason
    args = seen["args"]
    assert args[4] is old_value
    assert args[5] is new_value
