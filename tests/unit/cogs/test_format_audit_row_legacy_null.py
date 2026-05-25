"""PR-5 — _format_audit_row renders ``—`` for legacy-NULL columns.

Pin per ``docs/ai-config-ownership.md`` § "Audit fields" (the I-4
legacy-NULL rendering rule): the cog's audit-row formatter and the
support-report draft renderer must tolerate rows missing the
migration-045 ``effective_source`` / ``effective_mode`` columns,
producing ``—`` placeholders without raising.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from cogs.ai_cog import _format_audit_row
from views.ai.support_report import build_support_report_draft


def _legacy_row(**overrides) -> dict:
    """Pre-migration-045 audit row — none of the new columns present."""
    base = {
        "id": 1,
        "guild_id": 1,
        "channel_id": 100,
        "user_id": 42,
        "task": "general.nl_answer",
        "route": "openai",
        "decision": "denied",
        "reason_code": "below_min_level",
        "provider": "openai",
        "model": "gpt-4o-mini",
        "created_at": datetime(2026, 5, 25, 12, 0, tzinfo=timezone.utc),
    }
    base.update(overrides)
    return base


def _post_migration_row_with_nulls(**overrides) -> dict:
    """Post-migration row where the new columns exist but are NULL —
    most commonly a denial row that did not produce a reply."""
    base = _legacy_row(
        effective_source=None,
        effective_mode=None,
        memory_turns_used=None,
        memory_window_minutes=None,
        memory_scan_attempted=None,
        memory_scan_added_turns=None,
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# _format_audit_row
# ---------------------------------------------------------------------------


def test_format_audit_row_does_not_raise_on_legacy_row():
    """A pre-migration row has no ``effective_source`` key at all.
    The formatter must tolerate this without KeyError."""
    line = _format_audit_row(_legacy_row())
    assert "—" in line  # the missing effective_*/* fields render as dash


def test_format_audit_row_renders_dash_for_null_effective_fields():
    line = _format_audit_row(_post_migration_row_with_nulls())
    assert "effective=—/—" in line


def test_format_audit_row_renders_populated_effective_fields():
    line = _format_audit_row(
        _post_migration_row_with_nulls(
            effective_source="channel",
            effective_mode="always_reply",
        ),
    )
    assert "effective=channel/always_reply" in line


# ---------------------------------------------------------------------------
# build_support_report_draft
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_support_report_draft_tolerates_legacy_rows(monkeypatch):
    from services import ai_decision_audit_service

    monkeypatch.setattr(
        ai_decision_audit_service,
        "query",
        AsyncMock(return_value=[_legacy_row()]),
    )

    draft = await build_support_report_draft(guild_id=1, bot_user_id=42)
    # Audit-row body line renders ``effective=—/—`` for the legacy row.
    assert "effective=—/—" in draft


@pytest.mark.asyncio
async def test_support_report_draft_renders_post_migration_fields(monkeypatch):
    from services import ai_decision_audit_service

    monkeypatch.setattr(
        ai_decision_audit_service,
        "query",
        AsyncMock(
            return_value=[
                _post_migration_row_with_nulls(
                    effective_source="channel",
                    effective_mode="mention_only",
                ),
            ],
        ),
    )

    draft = await build_support_report_draft(guild_id=1, bot_user_id=42)
    assert "effective=channel/mention_only" in draft
