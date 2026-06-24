"""ticket_service — open-eligibility decisions + transcript rendering.

The eligibility gate is the single source of truth every open path (command /
panel / AI) shares, so its reason codes are pinned here.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from services import ticket_service as ts


def _cfg(**over):
    base = dict(
        guild_id=1,
        enabled=True,
        staff_role_id=99,
        category_id=None,
        log_channel_id=None,
        panel_channel_id=None,
        panel_message_id=None,
        max_open_per_user=1,
        ping_staff_on_open=True,
    )
    base.update(over)
    return ts.TicketConfig(**base)


@pytest.mark.asyncio
async def test_eligibility_disabled_when_no_config(monkeypatch):
    monkeypatch.setattr(ts.db, "ticket_get_config", AsyncMock(return_value=None))
    out = await ts.check_open_eligibility(1, 2)
    assert not out.allowed
    assert out.reason == ts.REASON_DISABLED


@pytest.mark.asyncio
async def test_eligibility_not_configured_when_no_staff_role(monkeypatch):
    row = _cfg(staff_role_id=None).__dict__
    monkeypatch.setattr(ts.db, "ticket_get_config", AsyncMock(return_value=row))
    out = await ts.check_open_eligibility(1, 2)
    assert not out.allowed
    assert out.reason == ts.REASON_NOT_CONFIGURED


@pytest.mark.asyncio
async def test_eligibility_blacklisted(monkeypatch):
    monkeypatch.setattr(ts.db, "ticket_get_config", AsyncMock(return_value=_cfg().__dict__))
    monkeypatch.setattr(ts.db, "ticket_is_blacklisted", AsyncMock(return_value=True))
    out = await ts.check_open_eligibility(1, 2)
    assert not out.allowed
    assert out.reason == ts.REASON_BLACKLISTED


@pytest.mark.asyncio
async def test_eligibility_limit_reached(monkeypatch):
    monkeypatch.setattr(ts.db, "ticket_get_config", AsyncMock(return_value=_cfg().__dict__))
    monkeypatch.setattr(ts.db, "ticket_is_blacklisted", AsyncMock(return_value=False))
    monkeypatch.setattr(ts.db, "ticket_count_open_for_user", AsyncMock(return_value=1))
    out = await ts.check_open_eligibility(1, 2)
    assert not out.allowed
    assert out.reason == ts.REASON_LIMIT_REACHED
    assert "limit 1" in out.message


@pytest.mark.asyncio
async def test_eligibility_allowed_under_limit(monkeypatch):
    monkeypatch.setattr(
        ts.db, "ticket_get_config", AsyncMock(return_value=_cfg(max_open_per_user=3).__dict__)
    )
    monkeypatch.setattr(ts.db, "ticket_is_blacklisted", AsyncMock(return_value=False))
    monkeypatch.setattr(ts.db, "ticket_count_open_for_user", AsyncMock(return_value=2))
    out = await ts.check_open_eligibility(1, 2)
    assert out.allowed
    assert out.reason == ts.REASON_OK


def test_config_is_set_up_requires_enabled_and_role():
    assert _cfg().is_set_up
    assert not _cfg(enabled=False).is_set_up
    assert not _cfg(staff_role_id=None).is_set_up


@pytest.mark.asyncio
async def test_build_transcript_renders_messages():
    class _Msg:
        def __init__(self, author_name, content):
            self.created_at = __import__("datetime").datetime(2026, 6, 24, 12, 0)
            self.author = type("A", (), {"display_name": author_name})()
            self.content = content
            self.attachments = []
            self.embeds = []

    class _Channel:
        name = "ticket-bob"
        id = 5

        def history(self, *, limit, oldest_first):  # noqa: ARG002
            async def _gen():
                for m in (_Msg("bob", "hello"), _Msg("staff", "hi there")):
                    yield m

            return _gen()

    out = await ts.build_transcript(_Channel())
    assert "bob: hello" in out
    assert "staff: hi there" in out
    assert "2 message(s)" in out
