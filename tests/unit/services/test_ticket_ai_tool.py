"""open_support_ticket — the AI action tool's offering gate + delegation.

Pins: the tool is offered only with a live guild + member; the handler refuses
an empty subject without touching the mutation seam; otherwise it delegates to
the audited ``ticket_mutation.open_ticket`` and maps the result for the model.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from core.runtime.ai.contracts import AIScope
from services import ticket_mutation
from services.ai_tools import build_registry


def test_tool_offered_only_with_guild_and_member():
    with_ctx = build_registry(
        scope=AIScope.USER, guild_id=1, actor_id=2, guild=object(), member=object()
    )
    assert "open_support_ticket" in with_ctx.handlers

    without = build_registry(scope=AIScope.USER, guild_id=1, actor_id=2)
    assert "open_support_ticket" not in without.handlers


@pytest.mark.asyncio
async def test_handler_refuses_empty_subject(monkeypatch):
    open_mock = AsyncMock()
    monkeypatch.setattr(ticket_mutation, "open_ticket", open_mock)
    reg = build_registry(
        scope=AIScope.USER, guild_id=1, actor_id=2, guild=object(), member=object()
    )
    out = await reg.handlers["open_support_ticket"]({"subject": "   "})
    assert out["opened"] is False
    assert out["reason"] == "missing_subject"
    open_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_handler_delegates_and_maps_success(monkeypatch):
    open_mock = AsyncMock(
        return_value=ticket_mutation.TicketOpenResult(
            success=True,
            ticket_id=7,
            channel_id=555,
            message="🎫 Opened your ticket: <#555>",
            reason="ok",
        )
    )
    monkeypatch.setattr(ticket_mutation, "open_ticket", open_mock)
    reg = build_registry(
        scope=AIScope.USER, guild_id=1, actor_id=2, guild=object(), member=object()
    )
    out = await reg.handlers["open_support_ticket"]({"subject": "need help"})
    assert out["opened"] is True
    assert out["ticket_id"] == 7
    assert out["channel_mention"] == "<#555>"
    open_mock.assert_awaited_once()
    # the AI path is tagged source="ai"
    assert open_mock.await_args.kwargs.get("source") == "ai"


@pytest.mark.asyncio
async def test_handler_maps_failure_reason(monkeypatch):
    open_mock = AsyncMock(
        return_value=ticket_mutation.TicketOpenResult(
            success=False, message="You can't open tickets here.", reason="blacklisted"
        )
    )
    monkeypatch.setattr(ticket_mutation, "open_ticket", open_mock)
    reg = build_registry(
        scope=AIScope.USER, guild_id=1, actor_id=2, guild=object(), member=object()
    )
    out = await reg.handlers["open_support_ticket"]({"subject": "let me in"})
    assert out["opened"] is False
    assert out["reason"] == "blacklisted"
