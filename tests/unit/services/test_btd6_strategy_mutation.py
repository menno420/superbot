"""M4 — strategy mutation tests (audit + publish gating + retention)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_strategy_mutation as mut  # noqa: E402
from utils.db import btd6_strategies as db  # noqa: E402


@pytest.fixture(autouse=True)
def _stub_db(monkeypatch):
    state = {"rows": {}, "audit": [], "next_id": 0}

    async def _insert_strategy(**kw):
        state["next_id"] += 1
        sid = state["next_id"]
        state["rows"][sid] = {**kw, "id": sid, "version": 1}
        return sid

    async def _get_strategy(sid):
        return state["rows"].get(sid)

    async def _update_state(sid, **kw):
        if sid not in state["rows"]:
            return
        for k, v in kw.items():
            if k == "bump_version":
                if v:
                    state["rows"][sid]["version"] = state["rows"][sid].get(
                        "version", 1) + 1
                continue
            state["rows"][sid][k] = v

    async def _anon(sid, *, new_state):
        if sid in state["rows"]:
            state["rows"][sid]["submitted_by"] = None
            state["rows"][sid]["submitter_display_snapshot"] = None
            state["rows"][sid]["submitter_identity_state"] = new_state

    async def _record_audit(sid, **kw):
        state["audit"].append({"strategy_id": sid, **kw})
        return len(state["audit"])

    async def _list_audit(sid, *, limit=50):
        return [a for a in state["audit"] if a["strategy_id"] == sid]

    monkeypatch.setattr(db, "insert_strategy", _insert_strategy)
    monkeypatch.setattr(db, "get_strategy", _get_strategy)
    monkeypatch.setattr(db, "update_strategy_state", _update_state)
    monkeypatch.setattr(db, "anonymize_submitter", _anon)
    monkeypatch.setattr(db, "record_strategy_audit", _record_audit)
    monkeypatch.setattr(db, "list_strategy_audit", _list_audit)
    yield state


def _user(id_=42, display="alice"):
    m = MagicMock()
    m.id = id_
    m.display_name = display
    m.guild_permissions = MagicMock(administrator=False, manage_guild=False)
    return m


def _staff(id_=99):
    m = MagicMock()
    m.id = id_
    m.display_name = "moderator"
    m.guild_permissions = MagicMock(administrator=True)
    return m


async def test_submit_writes_audit_row(_stub_db):
    result = await mut.submit_strategy(
        origin_guild_id=1, submitter=_user(),
        title="ZTOM", summary="Zero tower opener",
    )
    assert result.action == "submitted"
    assert any(a["action"] == "submitted" for a in _stub_db["audit"])


async def test_ai_approve_is_guild_local_only(_stub_db):
    submit = await mut.submit_strategy(
        origin_guild_id=1, submitter=_user(),
        title="A", summary="S",
    )
    await mut.ai_approve_guild(
        submit.strategy_id, provider="deterministic", model="",
    )
    row = _stub_db["rows"][submit.strategy_id]
    assert row["approval_status"] == "approved"
    assert row["approved_by"] == "ai"
    assert row["visibility"] == "guild"  # AI never publishes


async def test_ai_approve_refuses_published_row(_stub_db):
    submit = await mut.submit_strategy(
        origin_guild_id=1, submitter=_user(),
        title="A", summary="S",
    )
    await mut.staff_publish(submit.strategy_id, staff_actor=_staff())
    with pytest.raises(mut.InvalidStrategyValueError):
        await mut.ai_approve_guild(
            submit.strategy_id, provider="deterministic", model="",
        )


async def test_staff_publish_requires_staff(_stub_db):
    submit = await mut.submit_strategy(
        origin_guild_id=1, submitter=_user(),
        title="A", summary="S",
    )
    with pytest.raises(mut.UnauthorizedStrategyMutationError):
        await mut.staff_publish(submit.strategy_id, staff_actor=_user())


async def test_publish_writes_audit_and_marks_published(_stub_db):
    submit = await mut.submit_strategy(
        origin_guild_id=1, submitter=_user(),
        title="A", summary="S",
    )
    result = await mut.staff_publish(
        submit.strategy_id, staff_actor=_staff(),
    )
    assert result.action == "published"
    row = _stub_db["rows"][submit.strategy_id]
    assert row["visibility"] == "published"
    assert any(a["action"] == "published" for a in _stub_db["audit"])


async def test_unpublish_reverts_visibility_and_audits(_stub_db):
    submit = await mut.submit_strategy(
        origin_guild_id=1, submitter=_user(),
        title="A", summary="S",
    )
    await mut.staff_publish(submit.strategy_id, staff_actor=_staff())
    result = await mut.unpublish(
        submit.strategy_id, staff_actor=_staff(), reason="cleanup",
    )
    assert result.action == "unpublished"
    row = _stub_db["rows"][submit.strategy_id]
    assert row["visibility"] == "guild"


async def test_anonymise_submitter_clears_identity_and_audits(_stub_db):
    submit = await mut.submit_strategy(
        origin_guild_id=1, submitter=_user(),
        title="A", summary="S",
    )
    await mut.anonymise_submitter(
        submit.strategy_id, actor=_staff(), state="anonymized",
    )
    row = _stub_db["rows"][submit.strategy_id]
    assert row["submitted_by"] is None
    assert row["submitter_display_snapshot"] is None
    assert row["submitter_identity_state"] == "anonymized"
    assert any(
        a["action"] == "submitter_anonymized" for a in _stub_db["audit"]
    )


async def test_anonymise_rejects_invalid_state(_stub_db):
    submit = await mut.submit_strategy(
        origin_guild_id=1, submitter=_user(),
        title="A", summary="S",
    )
    with pytest.raises(mut.InvalidStrategyValueError):
        await mut.anonymise_submitter(
            submit.strategy_id, actor=_staff(), state="bogus",
        )
