"""Tests for the chat-memory hook in ai_instruction_service.assemble()."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from services import ai_instruction_service
from utils.db import ai as ai_db


@pytest.mark.asyncio
async def test_assemble_with_no_recent_turns_unchanged(monkeypatch):
    """Without ``recent_turns``, the data layer holds only retrieved
    facts (regression: existing callers stay correct)."""

    async def _get(_pid):
        return None

    monkeypatch.setattr(ai_db, "get_instruction_profile", _get)

    stack = await ai_instruction_service.assemble(
        guild_id=1,
        user_message="hi",
        profile_ids=(),
        retrieved_facts=["fact one"],
    )
    # Exactly one data block (the retrieved fact), no recent-turns block.
    assert len(stack.data) == 1
    assert "fact one" in stack.data[0]
    assert "recent_channel_turns" not in stack.data[0]


@pytest.mark.asyncio
async def test_assemble_renders_recent_turns_as_untrusted_data(monkeypatch):
    async def _get(_pid):
        return None

    monkeypatch.setattr(ai_db, "get_instruction_profile", _get)

    turns = [
        SimpleNamespace(user_id=10, role="user", text="prior question"),
        SimpleNamespace(user_id=999, role="assistant", text="prior reply"),
        SimpleNamespace(user_id=20, role="user", text="bystander comment"),
    ]
    stack = await ai_instruction_service.assemble(
        guild_id=1,
        user_message="follow-up",
        profile_ids=(),
        recent_turns=turns,
    )
    # The recent-turns block is the FIRST data entry.
    recent_block = stack.data[0]
    # Untrusted wrapper present.
    assert "UNTRUSTED_DATA__recent_channel_turns__BEGIN" in recent_block
    # All three rendered.
    assert "prior question" in recent_block
    assert "prior reply" in recent_block
    assert "bystander comment" in recent_block
    # Role + user_id appears in each line.
    assert "[user user=10]" in recent_block
    assert "[assistant user=999]" in recent_block


@pytest.mark.asyncio
async def test_assemble_recent_turns_then_facts_order(monkeypatch):
    async def _get(_pid):
        return None

    monkeypatch.setattr(ai_db, "get_instruction_profile", _get)

    turns = [SimpleNamespace(user_id=1, role="user", text="t")]
    stack = await ai_instruction_service.assemble(
        guild_id=1,
        user_message="x",
        profile_ids=(),
        recent_turns=turns,
        retrieved_facts=["F"],
    )
    # Order: recent_turns first, then facts.
    assert "recent_channel_turns" in stack.data[0]
    assert "retrieved_fact" in stack.data[1]


@pytest.mark.asyncio
async def test_assemble_empty_recent_turns_skipped(monkeypatch):
    async def _get(_pid):
        return None

    monkeypatch.setattr(ai_db, "get_instruction_profile", _get)

    stack = await ai_instruction_service.assemble(
        guild_id=1,
        user_message="x",
        profile_ids=(),
        recent_turns=[],
    )
    assert all(
        "recent_channel_turns" not in block for block in stack.data
    )


@pytest.mark.asyncio
async def test_assemble_recent_turns_propagate_into_payload(monkeypatch):
    """The recent-turns block must reach the payload that is sent to
    the gateway, not just sit in the data tuple."""

    async def _get(_pid):
        return None

    monkeypatch.setattr(ai_db, "get_instruction_profile", _get)

    turns = [SimpleNamespace(user_id=42, role="user", text="LOOK_FOR_ME")]
    stack = await ai_instruction_service.assemble(
        guild_id=1,
        user_message="now",
        profile_ids=(),
        recent_turns=turns,
    )
    payload = stack.render_payload_text()
    assert "LOOK_FOR_ME" in payload
    assert "now" in payload  # user message still appended at the end.
