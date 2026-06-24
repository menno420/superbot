"""open_support_ticket — the AI tool's offering gate + confirmation request.

The AI tool does NOT open tickets; it validates eligibility and emits
``ticket.open_requested`` so the cog posts a one-click confirm (Q-0201). Pins:
offered only with a live guild + member; refuses an empty subject; refuses (no
event) when ineligible; on success emits the event and never calls the mutation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from core.runtime.ai.contracts import AIScope
from services import ticket_mutation, ticket_service
from services.ai_tools import build_registry


def _channel(cid: int = 42):
    class _C:
        id = cid

    return _C()


def _handler(monkeypatch, *, eligible: bool, reason: str = "ok"):
    """Build the open_support_ticket handler with eligibility stubbed."""
    monkeypatch.setattr(
        ticket_service,
        "check_open_eligibility",
        AsyncMock(
            return_value=ticket_service.OpenEligibility(eligible, reason, 0, 1)
        ),
    )
    reg = build_registry(
        scope=AIScope.USER,
        guild_id=1,
        actor_id=2,
        guild=type("G", (), {"id": 1})(),
        member=type("M", (), {"id": 2})(),
        channel=_channel(),
    )
    return reg.handlers["open_support_ticket"]


def test_tool_offered_only_with_guild_and_member():
    with_ctx = build_registry(
        scope=AIScope.USER,
        guild_id=1,
        actor_id=2,
        guild=object(),
        member=object(),
        channel=_channel(),
    )
    assert "open_support_ticket" in with_ctx.handlers

    without = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    assert "open_support_ticket" not in without.handlers


@pytest.mark.asyncio
async def test_handler_refuses_empty_subject(monkeypatch):
    emit = AsyncMock()
    monkeypatch.setattr("core.events.bus.emit", emit)
    handler = _handler(monkeypatch, eligible=True)
    out = await handler({"subject": "   "})
    assert out["requested"] is False
    assert out["reason"] == "missing_subject"
    emit.assert_not_awaited()


@pytest.mark.asyncio
async def test_handler_refuses_when_ineligible_without_emitting(monkeypatch):
    emit = AsyncMock()
    monkeypatch.setattr("core.events.bus.emit", emit)
    open_mock = AsyncMock()
    monkeypatch.setattr(ticket_mutation, "open_ticket", open_mock)
    handler = _handler(monkeypatch, eligible=False, reason="limit_reached")
    out = await handler({"subject": "need help"})
    assert out["requested"] is False
    assert out["reason"] == "limit_reached"
    emit.assert_not_awaited()
    open_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_handler_requests_confirmation_without_opening(monkeypatch):
    emitted: list[tuple] = []

    async def _emit(event, **payload):
        emitted.append((event, payload))

    monkeypatch.setattr("core.events.bus.emit", _emit)
    open_mock = AsyncMock()
    monkeypatch.setattr(ticket_mutation, "open_ticket", open_mock)

    handler = _handler(monkeypatch, eligible=True)
    out = await handler({"subject": "my printer is broken"})

    assert out["requested"] is True
    assert out["subject"] == "my printer is broken"
    # the tool requests confirmation — it must NOT open the ticket itself
    open_mock.assert_not_awaited()
    assert any(e == "ticket.open_requested" for e, _ in emitted)
    _, payload = next(p for p in emitted if p[0] == "ticket.open_requested")
    assert payload["channel_id"] == 42
    assert payload["user_id"] == 2
    assert payload["subject"] == "my printer is broken"
