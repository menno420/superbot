"""PR-H tests for the support-report draft surface.

Pin:

* The draft contains ONLY fields already in ai_decision_audit.
* The draft is a markdown code block.
* The view path makes NO network calls — it only calls
  ai_decision_audit_service.query.
* The embed format clearly labels itself as "draft".
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest

from views.ai.support_report import (
    build_support_report_draft,
    build_support_report_embed,
)


@pytest.mark.asyncio
async def test_draft_is_code_block(monkeypatch):
    from services import ai_decision_audit_service

    async def _q(_gid, **_kw):
        return []

    monkeypatch.setattr(ai_decision_audit_service, "query", _q)

    draft = await build_support_report_draft(guild_id=1, bot_user_id=42)
    assert draft.startswith("```")
    assert draft.rstrip().endswith("```")
    assert "guild_id: 1" in draft
    assert "bot_user_id: 42" in draft


@pytest.mark.asyncio
async def test_draft_renders_audit_fields_only(monkeypatch):
    from services import ai_decision_audit_service

    async def _q(_gid, **_kw):
        return [
            {
                "decision": "denied",
                "reason_code": "below_min_level",
                "task": "btd6.answer",
                "route": "btd6.answer",
                "provider": "openai",
                "model": "gpt-4",
            },
        ]

    monkeypatch.setattr(ai_decision_audit_service, "query", _q)

    draft = await build_support_report_draft(guild_id=1, bot_user_id=42)
    assert "decision=denied" in draft
    assert "reason=below_min_level" in draft
    assert "provider=openai" in draft
    assert "model=gpt-4" in draft


@pytest.mark.asyncio
async def test_draft_never_includes_message_text(monkeypatch):
    """The audit table does not store message bodies — the draft path
    must never invent or include any. We assert that no key from a
    fake "message body" leaks even if it appeared in the audit row.
    """
    from services import ai_decision_audit_service

    async def _q(_gid, **_kw):
        return [
            {
                "decision": "replied",
                "reason_code": "none",
                "task": "general.nl_answer",
                "route": "openai",
                "provider": "openai",
                "model": "gpt-4",
                # Pretend an out-of-spec extra field leaked through:
                "content": "SECRET MESSAGE BODY DO NOT LEAK",
            },
        ]

    monkeypatch.setattr(ai_decision_audit_service, "query", _q)

    draft = await build_support_report_draft(guild_id=1, bot_user_id=42)
    assert "SECRET MESSAGE BODY" not in draft


@pytest.mark.asyncio
async def test_embed_labels_itself_as_draft(monkeypatch):
    from services import ai_decision_audit_service

    async def _q(_gid, **_kw):
        return []

    monkeypatch.setattr(ai_decision_audit_service, "query", _q)

    embed = await build_support_report_embed(guild_id=1, bot_user_id=42)
    blob = (embed.title or "") + " " + (embed.description or "")
    assert "draft" in blob.lower()
    assert "does NOT send" in blob or "no outbound" in blob.lower()


def test_module_makes_no_network_calls():
    """The view module must not import aiohttp / requests / urllib /
    httpx as HTTP clients."""
    src = inspect.getsource(
        __import__("views.ai.support_report", fromlist=["support_report"]),
    )
    # Use import-statement patterns so common English words ("support
    # requests are handled") don't false-match.
    forbidden_patterns = (
        r"\bimport\s+aiohttp\b",
        r"\bfrom\s+aiohttp\b",
        r"\bimport\s+requests\b",
        r"\bfrom\s+requests\b",
        r"\bimport\s+httpx\b",
        r"\bfrom\s+httpx\b",
        r"\bimport\s+urllib\b",
        r"\bfrom\s+urllib\b",
    )
    for pattern in forbidden_patterns:
        assert not re.search(pattern, src), (
            f"support report must not import: {pattern}"
        )


def test_no_outbound_call_strings_in_file():
    path = (
        Path(__file__).resolve().parents[4]
        / "disbot"
        / "views"
        / "ai"
        / "support_report.py"
    )
    src = path.read_text()
    # Pattern guard against accidental email / webhook code.
    assert not re.search(r"\bsmtplib\b", src)
    assert not re.search(r"\bsend_email\b", src)
    assert not re.search(r"webhook", src, re.IGNORECASE)
