"""Unit tests for services/ai_preset_service.py.

Pins: lookup normalizes + is fail-safe (never raises into the reply path),
set_preset upserts + emits an audit action + validates empty input, and
remove_preset audits only on a real delete.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import ai_preset_service as svc  # noqa: E402
from services import audit_events as audit_mod  # noqa: E402
from utils.db import ai_presets as presets_db  # noqa: E402


@pytest.fixture(autouse=True)
def _stub(monkeypatch):
    rows: list[dict] = []
    audits: list[dict] = []

    async def _lookup(guild_id, key):
        for r in rows:
            if r["guild_id"] == guild_id and r["question_key"] == key and r["enabled"]:
                return r["answer"]
        return None

    async def _get_by_key(guild_id, key):
        for r in rows:
            if r["guild_id"] == guild_id and r["question_key"] == key:
                return dict(r)
        return None

    async def _get_by_id(guild_id, preset_id):
        for r in rows:
            if r["guild_id"] == guild_id and r["id"] == preset_id:
                return dict(r)
        return None

    async def _upsert(*, guild_id, question_key, question, answer, task, source, created_by):
        for r in rows:
            if r["guild_id"] == guild_id and r["question_key"] == question_key:
                r.update(question=question, answer=answer, task=task, enabled=True)
                return r["id"]
        new_id = len(rows) + 1
        rows.append(
            {
                "id": new_id,
                "guild_id": guild_id,
                "question_key": question_key,
                "question": question,
                "answer": answer,
                "task": task,
                "source": source,
                "enabled": True,
                "created_by": created_by,
            },
        )
        return new_id

    async def _list_for_guild(guild_id, *, limit=50):
        return [dict(r) for r in rows if r["guild_id"] == guild_id]

    async def _delete(guild_id, preset_id):
        before = len(rows)
        rows[:] = [r for r in rows if not (r["guild_id"] == guild_id and r["id"] == preset_id)]
        return len(rows) < before

    async def _emit_audit_action(**kwargs):
        audits.append(kwargs)
        return True

    monkeypatch.setattr(presets_db, "lookup", _lookup)
    monkeypatch.setattr(presets_db, "get_by_key", _get_by_key)
    monkeypatch.setattr(presets_db, "get_by_id", _get_by_id)
    monkeypatch.setattr(presets_db, "upsert", _upsert)
    monkeypatch.setattr(presets_db, "list_for_guild", _list_for_guild)
    monkeypatch.setattr(presets_db, "delete", _delete)
    monkeypatch.setattr(audit_mod, "emit_audit_action", _emit_audit_action)
    return type("S", (), {"rows": rows, "audits": audits})


async def test_set_then_lookup_roundtrips_normalized(_stub) -> None:
    pid = await svc.set_preset(
        1,
        "How much cash on round 10?",
        "About $130.",
        actor_id=42,
    )
    assert pid == 1
    # lookup matches case/punct/mention-insensitively (same normalizer).
    assert await svc.lookup(1, "<@99> how much cash on round 10") == "About $130."
    assert await svc.lookup(1, "totally different") is None
    # other guilds don't see it.
    assert await svc.lookup(2, "how much cash on round 10") is None


async def test_set_preset_emits_create_then_update_audit(_stub) -> None:
    await svc.set_preset(1, "q one", "first", actor_id=7)
    assert _stub.audits[-1]["mutation_type"] == "preset_created"
    assert _stub.audits[-1]["new_value"] == "first"
    # re-authoring the same question updates in place + audits as an update.
    await svc.set_preset(1, "q one", "second", actor_id=7)
    assert _stub.audits[-1]["mutation_type"] == "preset_updated"
    assert _stub.audits[-1]["prev_value"] == "first"
    assert _stub.audits[-1]["new_value"] == "second"
    assert len(_stub.rows) == 1  # upsert, not a second row


@pytest.mark.parametrize(
    ("question", "answer"),
    [("   ", "valid"), ("???", "valid"), ("valid q", "   ")],
)
async def test_set_preset_rejects_empty(_stub, question, answer) -> None:
    with pytest.raises(ValueError):
        await svc.set_preset(1, question, answer, actor_id=1)
    assert _stub.rows == []
    assert _stub.audits == []


async def test_remove_preset_audits_only_on_real_delete(_stub) -> None:
    pid = await svc.set_preset(1, "q", "a", actor_id=1)
    _stub.audits.clear()
    # missing id → no delete, no audit.
    assert await svc.remove_preset(1, 999, actor_id=1) is False
    assert _stub.audits == []
    # real delete → audited.
    assert await svc.remove_preset(1, pid, actor_id=1) is True
    assert _stub.audits[-1]["mutation_type"] == "preset_removed"
    assert _stub.audits[-1]["prev_value"] == "a"
    assert _stub.rows == []


async def test_lookup_is_fail_safe(monkeypatch, _stub) -> None:
    async def _boom(guild_id, key):
        raise RuntimeError("db down")

    monkeypatch.setattr(presets_db, "lookup", _boom)
    # Must swallow and return None — never raise into the AI reply path.
    assert await svc.lookup(1, "anything") is None


async def test_lookup_empty_question_returns_none(_stub) -> None:
    assert await svc.lookup(1, "") is None
    assert await svc.lookup(1, None) is None
