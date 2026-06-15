"""M2 — ai_decision_audit_service tests.

Pins the sentinel-reason-code rule (success rows carry
``reason_code='none'``) and the rejection of unknown decision
strings.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from core.runtime.ai.contracts import PolicyDenialReason  # noqa: E402
from services import ai_decision_audit_service as svc  # noqa: E402
from utils.db import ai as ai_db  # noqa: E402


@pytest.fixture(autouse=True)
def _stub_db(monkeypatch):
    rows: list[dict] = []

    async def _record_decision(**kwargs):
        rows.append(kwargs)
        return len(rows)

    async def _query_decisions(guild_id, **kwargs):
        return [r for r in rows if r["guild_id"] == guild_id]

    monkeypatch.setattr(ai_db, "record_decision", _record_decision)
    monkeypatch.setattr(ai_db, "query_decisions", _query_decisions)
    yield rows


async def test_record_writes_a_row(_stub_db):
    new_id = await svc.record(
        guild_id=1,
        channel_id=2,
        category_id=None,
        user_id=3,
        message_id=4,
        task="btd6.answer",
        route="btd6.answer",
        decision="denied",
        reason_code=PolicyDenialReason.BELOW_MIN_LEVEL,
    )
    assert new_id == 1
    assert _stub_db[0]["reason_code"] == "below_min_level"


async def test_success_row_forces_sentinel_reason(_stub_db):
    """A 'replied' or 'allowed' decision must always carry 'none'."""
    await svc.record(
        guild_id=1, channel_id=2, category_id=None, user_id=3,
        message_id=4, task=None, route=None,
        decision="replied",
        reason_code=PolicyDenialReason.BELOW_MIN_LEVEL,  # would be a bug
    )
    assert _stub_db[0]["reason_code"] == "none"

    await svc.record(
        guild_id=1, channel_id=2, category_id=None, user_id=3,
        message_id=4, task=None, route=None,
        decision="allowed",
        reason_code="something_invalid",
    )
    assert _stub_db[1]["reason_code"] == "none"


async def test_unknown_decision_raises(_stub_db):
    with pytest.raises(ValueError):
        await svc.record(
            guild_id=1, channel_id=2, category_id=None, user_id=3,
            message_id=4, task=None, route=None,
            decision="bogus",
            reason_code=PolicyDenialReason.NONE,
        )


async def test_query_filters_by_guild(_stub_db):
    await svc.record(
        guild_id=1, channel_id=2, category_id=None, user_id=3,
        message_id=4, task=None, route=None,
        decision="denied", reason_code=PolicyDenialReason.COOLDOWN_ACTIVE,
    )
    await svc.record(
        guild_id=999, channel_id=2, category_id=None, user_id=3,
        message_id=5, task=None, route=None,
        decision="denied", reason_code=PolicyDenialReason.COOLDOWN_ACTIVE,
    )
    rows = await svc.query(1)
    assert len(rows) == 1
    assert rows[0]["guild_id"] == 1


async def test_no_raw_message_content_is_stored(_stub_db):
    """The audit row must NEVER carry the user's raw message text.

    Pinned by inspection: ``record`` exposes no ``text`` / ``content``
    parameter. If a future change adds one, this test will need to
    be updated AND the redaction policy noted in the migration
    comment must be defined first.
    """
    import inspect

    sig = inspect.signature(svc.record)
    assert "text" not in sig.parameters
    assert "content" not in sig.parameters
    assert "message_text" not in sig.parameters
