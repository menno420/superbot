"""Tests for the rewritten ``!btd6 why-no-response`` (Issue D).

After PR #310 retired the BTD6 passive stage, the original command
read ``self._passive_stage`` which was always ``None`` and produced
"Passive stage is not loaded" on every invocation. The audit table
held the actual data but was never queried.

These tests pin the post-hardening behaviour:

* The command queries ``ai_decision_audit_service.query``.
* Rows are filtered to ``task='btd6.answer'``.
* Only ``decided / skipped / errored / degraded`` rows are surfaced.
* The ``BTD6Cog`` instance has no remaining ``_passive_stage``
  attribute (regression pin for the surgical cleanup).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from cogs.btd6_cog import BTD6Cog

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ctx(*, guild_id: int | None, channel_id: int = 1):
    ctx = MagicMock()
    if guild_id is None:
        ctx.guild = None
    else:
        ctx.guild = SimpleNamespace(id=guild_id)
    ctx.channel = SimpleNamespace(id=channel_id)
    ctx.send = AsyncMock()
    return ctx


def _row(*, decision: str, task: str, reason: str = "below_min_level"):
    return {
        "decision": decision,
        "task": task,
        "route": task,
        "reason_code": reason,
        "channel_id": 1,
        "user_id": 9,
        "policy_snapshot_hash": "abc123",
        "instruction_profile_ids": [101, 202],
        "provider": "openai",
        "model": "gpt-4",
    }


# ---------------------------------------------------------------------------
# Surgical cleanup pin
# ---------------------------------------------------------------------------


def test_btd6_cog_has_no_passive_stage_attribute():
    """The cog should no longer carry the retired ``_passive_stage``
    attribute. If this fails, the surgical cleanup regressed."""
    cog = BTD6Cog(bot=MagicMock())
    assert not hasattr(cog, "_passive_stage")


# ---------------------------------------------------------------------------
# Audit-table read pin
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_btd6_why_no_response_reads_audit_table(monkeypatch):
    from services import ai_decision_audit_service

    captured: list[dict] = []

    async def _query(guild_id, *, limit=50, **_kw):
        captured.append({"guild_id": guild_id, "limit": limit})
        return [
            _row(decision="denied", task="btd6.answer", reason="below_min_level"),
            _row(decision="skipped", task="btd6.answer", reason="no_route_matched"),
        ]

    monkeypatch.setattr(ai_decision_audit_service, "query", _query)

    cog = BTD6Cog(bot=MagicMock())
    ctx = _ctx(guild_id=42)
    await cog.btd6_why_no_response.callback(cog, ctx)

    assert captured == [{"guild_id": 42, "limit": 10}]
    ctx.send.assert_awaited_once()
    embed = ctx.send.await_args.kwargs.get("embed")
    assert embed is not None
    field_text = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
    assert "denied" in field_text
    assert "below_min_level" in field_text
    assert "no_route_matched" in field_text
    # New PR-A fields surface the audit-quality diagnostics.
    assert "abc123" in field_text  # policy_snapshot_hash
    assert "101" in field_text and "202" in field_text  # profile ids
    assert "openai" in field_text  # provider
    assert "gpt-4" in field_text  # model


@pytest.mark.asyncio
async def test_btd6_why_no_response_filters_to_btd6_task(monkeypatch):
    """Audit rows from other tasks (general.nl_answer, etc.) must be
    filtered out so the BTD6 diagnostic only surfaces BTD6 decisions."""
    from services import ai_decision_audit_service

    async def _query(_guild_id, **_kw):
        return [
            _row(decision="denied", task="general.nl_answer", reason="role_denied"),
            _row(decision="denied", task="btd6.answer", reason="below_min_level"),
            _row(decision="replied", task="btd6.answer"),  # not a denial → excluded
        ]

    monkeypatch.setattr(ai_decision_audit_service, "query", _query)

    cog = BTD6Cog(bot=MagicMock())
    ctx = _ctx(guild_id=42)
    await cog.btd6_why_no_response.callback(cog, ctx)

    embed = ctx.send.await_args.kwargs.get("embed")
    assert embed is not None
    field_text = "\n".join(f"{f.name}\n{f.value}" for f in embed.fields)
    assert "below_min_level" in field_text
    # The general.nl_answer denial must NOT bleed through.
    assert "role_denied" not in field_text


@pytest.mark.asyncio
async def test_btd6_why_no_response_no_rows_message(monkeypatch):
    from services import ai_decision_audit_service

    async def _query(_guild_id, **_kw):
        # Only non-BTD6 rows.
        return [_row(decision="denied", task="general.nl_answer")]

    monkeypatch.setattr(ai_decision_audit_service, "query", _query)

    cog = BTD6Cog(bot=MagicMock())
    ctx = _ctx(guild_id=42)
    await cog.btd6_why_no_response.callback(cog, ctx)

    msg = ctx.send.await_args.args[0]
    assert "No recent BTD6" in msg


@pytest.mark.asyncio
async def test_btd6_why_no_response_requires_guild_context():
    cog = BTD6Cog(bot=MagicMock())
    ctx = _ctx(guild_id=None)
    await cog.btd6_why_no_response.callback(cog, ctx)

    msg = ctx.send.await_args.args[0]
    assert "guild context" in msg


@pytest.mark.asyncio
async def test_btd6_why_no_response_clamps_limit(monkeypatch):
    """The ``limit`` argument must be clamped to [1, 50] to keep the
    query bounded regardless of operator input."""
    from services import ai_decision_audit_service

    seen_limits: list[int] = []

    async def _query(_guild_id, *, limit=50, **_kw):
        seen_limits.append(limit)
        return []

    monkeypatch.setattr(ai_decision_audit_service, "query", _query)

    cog = BTD6Cog(bot=MagicMock())
    await cog.btd6_why_no_response.callback(cog, _ctx(guild_id=42), limit=0)
    await cog.btd6_why_no_response.callback(cog, _ctx(guild_id=42), limit=9999)

    assert seen_limits == [1, 50]
