"""Unit tests for services/ai_review_log_service.py.

Pins: the two writers (record_unknown / record_correction) persist + emit, text
is redacted + capped, the answer registry remembers / looks up / dedups
flaggers, and every public call is fail-safe (a DB failure returns None / 0,
never raises into the AI path).
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core import events as events_mod  # noqa: E402
from core.runtime.ai import redaction as redaction_mod  # noqa: E402
from services import ai_review_log_service as svc  # noqa: E402
from utils.db import ai_review as ai_review_db  # noqa: E402


@pytest.fixture(autouse=True)
def _stub(monkeypatch):
    rows: list[dict] = []
    emitted: list[dict] = []

    async def _record_review_entry(**kwargs):
        rows.append(kwargs)
        return len(rows)

    async def _query_review_entries(guild_id, **kwargs):
        return [r for r in rows if r.get("guild_id") == guild_id]

    async def _mark_reviewed(guild_id, entry_id):
        return 0 < entry_id <= len(rows)

    async def _count_unreviewed(guild_id, *, kind=None):
        return len(rows)

    async def _export_review_entries(guild_id, *, kind=None, include_reviewed=True, limit=1000):
        return [r for r in rows if r.get("guild_id") == guild_id]

    async def _emit(event, **payload):
        emitted.append({"event": event, **payload})

    monkeypatch.setattr(ai_review_db, "record_review_entry", _record_review_entry)
    monkeypatch.setattr(ai_review_db, "query_review_entries", _query_review_entries)
    monkeypatch.setattr(ai_review_db, "export_review_entries", _export_review_entries)
    monkeypatch.setattr(ai_review_db, "mark_reviewed", _mark_reviewed)
    monkeypatch.setattr(ai_review_db, "count_unreviewed", _count_unreviewed)
    monkeypatch.setattr(events_mod.bus, "emit", _emit)
    svc._reset_for_tests()
    yield SimpleNamespace(rows=rows, emitted=emitted)


async def test_record_unknown_writes_and_emits(_stub) -> None:
    entry_id = await svc.record_unknown(
        guild_id=1,
        channel_id=2,
        user_id=3,
        message_id=4,
        task="btd6.answer",
        route="r",
        reason_code="grounding_failed",
        question="how much cash on round 10",
        answer="blocked ungrounded text",
    )
    assert entry_id == 1
    row = _stub.rows[0]
    assert row["kind"] == svc.KIND_UNKNOWN
    assert row["reason_code"] == "grounding_failed"
    assert row["question"] == "how much cash on round 10"
    assert row["answer"] == "blocked ungrounded text"
    assert _stub.emitted and _stub.emitted[0]["event"] == svc.EVT_AI_REVIEW_LOGGED
    assert _stub.emitted[0]["kind"] == svc.KIND_UNKNOWN


async def test_record_correction_writes_and_notes_flagger(_stub) -> None:
    svc.remember_answer(
        50,
        guild_id=1,
        channel_id=2,
        user_id=3,
        message_id=4,
        question="q",
        answer="a",
        task=None,
        route=None,
        provider=None,
        model=None,
    )
    assert svc.already_flagged(50, 7) is False
    entry_id = await svc.record_correction(
        guild_id=1,
        channel_id=2,
        user_id=3,
        message_id=4,
        reply_message_id=50,
        corrected_by=7,
        signal=svc.SIGNAL_REPLY,
        question="q",
        answer="a",
        correction="no it's 5",
    )
    assert entry_id == 1
    assert _stub.rows[0]["kind"] == svc.KIND_CORRECTION
    assert _stub.rows[0]["correction"] == "no it's 5"
    assert _stub.rows[0]["corrected_by"] == 7
    # The flagger is now remembered so a second 👎 from the same user dedups.
    assert svc.already_flagged(50, 7) is True


async def test_text_is_redacted_and_capped(_stub, monkeypatch) -> None:
    monkeypatch.setattr(
        redaction_mod,
        "redact_text",
        lambda t: SimpleNamespace(value=t.upper()),
    )
    await svc.record_unknown(
        guild_id=1,
        channel_id=2,
        user_id=3,
        message_id=4,
        task=None,
        route=None,
        reason_code="no_route_matched",
        question="hello " * 1000,
        answer="world",
    )
    assert _stub.rows[0]["question"] == ("HELLO " * 1000).strip()[:2000]
    assert _stub.rows[0]["answer"] == "WORLD"


async def test_record_unknown_is_fail_safe(monkeypatch, _stub) -> None:
    async def _boom(**kwargs):
        raise RuntimeError("db down")

    monkeypatch.setattr(ai_review_db, "record_review_entry", _boom)
    out = await svc.record_unknown(
        guild_id=1,
        channel_id=2,
        user_id=3,
        message_id=4,
        task=None,
        route=None,
        reason_code="errored",
        question="q",
        answer=None,
    )
    assert out is None
    assert _stub.emitted == []  # no emit when the write failed


def test_registry_remember_lookup_and_miss(_stub) -> None:
    svc.remember_answer(
        10,
        guild_id=1,
        channel_id=2,
        user_id=3,
        message_id=4,
        question="q",
        answer="a",
        task=None,
        route=None,
        provider=None,
        model=None,
    )
    ctx = svc.lookup_answer(10)
    assert ctx is not None and ctx.guild_id == 1 and ctx.question == "q"
    assert svc.lookup_answer(11) is None


async def test_export_normalizes_datetime_to_iso(_stub) -> None:
    from datetime import datetime, timezone

    _stub.rows.append(
        {
            "guild_id": 7,
            "id": 1,
            "kind": svc.KIND_UNKNOWN,
            "question": "q",
            "created_at": datetime(2026, 6, 30, 12, 0, tzinfo=timezone.utc),
        },
    )
    out = await svc.export(7)
    assert len(out) == 1
    # created_at is JSON-serializable (ISO string, not a datetime).
    assert out[0]["created_at"] == "2026-06-30T12:00:00+00:00"
    import json

    json.dumps(out)  # must not raise


async def test_query_and_mark_reviewed_passthrough(_stub) -> None:
    await svc.record_unknown(
        guild_id=99,
        channel_id=2,
        user_id=3,
        message_id=4,
        task=None,
        route=None,
        reason_code="no_route_matched",
        question="q",
        answer=None,
    )
    rows = await svc.query(99)
    assert len(rows) == 1
    assert await svc.mark_reviewed(99, 1) is True
    assert await svc.count_unreviewed(99) == 1
