"""M3A — mutation owner tests (writes + audit in same transaction)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_source_mutation as svc  # noqa: E402
from utils.db import btd6_sources as btd6_db  # noqa: E402


@pytest.fixture(autouse=True)
def _stub_db(monkeypatch):
    state: dict = {"rows": {}, "audit": []}

    async def _get_by_key(key):
        return state["rows"].get(key)

    async def _upsert(**kwargs):
        key = kwargs["source_key"]
        state["rows"][key] = {**kwargs, "id": len(state["rows"]) + 1}
        return state["rows"][key]["id"]

    async def _record_audit(**kwargs):
        state["audit"].append(kwargs)
        return len(state["audit"])

    monkeypatch.setattr(btd6_db, "get_source_by_key", _get_by_key)
    monkeypatch.setattr(btd6_db, "upsert_source", _upsert)
    monkeypatch.setattr(btd6_db, "record_source_audit", _record_audit)
    yield state


def _admin_actor():
    m = MagicMock()
    m.id = 42
    m.guild_permissions = MagicMock(administrator=True)
    return m


def _non_admin_actor():
    m = MagicMock()
    m.id = 7
    m.guild_permissions = MagicMock(administrator=False)
    return m


async def test_upsert_creates_row_plus_audit(_stub_db):
    result = await svc.upsert_source(
        source_key="nk_btd6_test",
        source_name="Test",
        source_owner="Ninja Kiwi",
        source_kind="official_api",
        trust_tier=1,
        base_url=None,
        path_template="/btd6/test",
        actor=_admin_actor(),
    )
    assert result.action == "created"
    assert result.source_id == 1
    assert len(_stub_db["audit"]) == 1
    assert _stub_db["audit"][0]["action"] == "created"


async def test_upsert_update_records_updated_action(_stub_db):
    await svc.upsert_source(
        source_key="nk_btd6_test",
        source_name="Test", source_owner="Ninja Kiwi",
        source_kind="official_api", trust_tier=1,
        base_url=None, path_template="/btd6/test",
        actor=_admin_actor(),
    )
    await svc.upsert_source(
        source_key="nk_btd6_test",
        source_name="Test v2", source_owner="Ninja Kiwi",
        source_kind="official_api", trust_tier=1,
        base_url=None, path_template="/btd6/test",
        actor=_admin_actor(),
    )
    assert _stub_db["audit"][-1]["action"] == "updated"


async def test_upsert_enable_change_records_enabled_action(_stub_db):
    await svc.upsert_source(
        source_key="nk_btd6_test",
        source_name="Test", source_owner="Ninja Kiwi",
        source_kind="official_api", trust_tier=1,
        base_url="https://x", path_template="/btd6/test",
        enabled=False, actor=_admin_actor(),
    )
    await svc.upsert_source(
        source_key="nk_btd6_test",
        source_name="Test", source_owner="Ninja Kiwi",
        source_kind="official_api", trust_tier=1,
        base_url="https://x", path_template="/btd6/test",
        enabled=True, actor=_admin_actor(),
    )
    assert _stub_db["audit"][-1]["action"] == "enabled"


async def test_tier_change_records_tier_changed_action(_stub_db):
    await svc.upsert_source(
        source_key="nk_btd6_test",
        source_name="Test", source_owner="Ninja Kiwi",
        source_kind="official_api", trust_tier=1,
        base_url=None, path_template="/btd6/test",
        actor=_admin_actor(),
    )
    await svc.upsert_source(
        source_key="nk_btd6_test",
        source_name="Test", source_owner="Community",
        source_kind="webpage", trust_tier=2,
        base_url=None, path_template="/btd6/test",
        actor=_admin_actor(),
    )
    assert _stub_db["audit"][-1]["action"] == "tier_changed"


async def test_set_enabled_requires_base_url(_stub_db):
    await svc.upsert_source(
        source_key="nk_btd6_test",
        source_name="Test", source_owner="Ninja Kiwi",
        source_kind="official_api", trust_tier=1,
        base_url=None, path_template="/btd6/test",
        actor=_admin_actor(),
    )
    with pytest.raises(svc.InvalidSourceValueError):
        await svc.set_enabled("nk_btd6_test", enabled=True, actor=_admin_actor())


async def test_set_enabled_writes_audit_on_disable(_stub_db):
    await svc.upsert_source(
        source_key="nk_btd6_test",
        source_name="Test", source_owner="Ninja Kiwi",
        source_kind="official_api", trust_tier=1,
        base_url="https://x", path_template="/btd6/test",
        enabled=True, actor=_admin_actor(),
    )
    audit_before = len(_stub_db["audit"])
    await svc.set_enabled("nk_btd6_test", enabled=False, actor=_admin_actor())
    assert len(_stub_db["audit"]) == audit_before + 1
    assert _stub_db["audit"][-1]["action"] == "disabled"


async def test_non_admin_actor_rejected(_stub_db):
    with pytest.raises(svc.UnauthorizedSourceMutationError):
        await svc.upsert_source(
            source_key="nk_btd6_test",
            source_name="Test", source_owner="Ninja Kiwi",
            source_kind="official_api", trust_tier=1,
            base_url=None, path_template="/btd6/test",
            actor=_non_admin_actor(),
        )


async def test_invalid_kind_rejected(_stub_db):
    with pytest.raises(svc.InvalidSourceValueError):
        await svc.upsert_source(
            source_key="nk_btd6_test",
            source_name="Test", source_owner="Ninja Kiwi",
            source_kind="rss",  # not in allowed set
            trust_tier=1,
            base_url=None, path_template="/btd6/test",
            actor=_admin_actor(),
        )


async def test_invalid_tier_rejected(_stub_db):
    with pytest.raises(svc.InvalidSourceValueError):
        await svc.upsert_source(
            source_key="nk_btd6_test",
            source_name="Test", source_owner="Ninja Kiwi",
            source_kind="official_api", trust_tier=3,
            base_url=None, path_template="/btd6/test",
            actor=_admin_actor(),
        )
