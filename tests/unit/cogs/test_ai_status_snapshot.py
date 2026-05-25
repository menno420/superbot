"""Snapshot-driven consistency: !ai status + !ai support-report.

PR-4A pin:

* ``build_status_embed`` sources every provider/counter field from the
  snapshot when one is supplied; falls back to the legacy diagnostics
  call when ``snapshot=None`` (panel-header callsite).
* ``build_support_report_draft`` adds operator-readable header lines
  (provider / model / memory / projection drift) sourced from the
  snapshot. Audit-row body is unchanged.
* Both surfaces produce the same provider/model fields for the same
  snapshot input — no parallel re-derivation.
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from cogs.ai_cog import build_status_embed
from services import ai_config_projection_service, ai_diagnostics_service
from views.ai.support_report import build_support_report_draft


def _snapshot(
    *,
    provider_name: str = "openai",
    model: str = "gpt-4o-mini",
    requests: int = 17,
    failures: int = 2,
    enabled: bool = True,
    window_minutes: int = 30,
    scan_enabled: bool = True,
    degraded: bool = False,
    last_error: str | None = None,
    drift_count: int = 0,
):
    """Build a fully-populated snapshot for the consistency checks."""
    return ai_config_projection_service.AIConfigSnapshot(
        guild_id=1,
        policy=ai_config_projection_service.PolicySnapshot(
            guild_id=1,
            enabled=enabled,
            natural_language_enabled=True,
            default_provider=provider_name,
            default_model=model,
        ),
        memory=ai_config_projection_service.MemorySnapshot(
            window_minutes=window_minutes,
            scan_enabled=scan_enabled,
            cached_channel_count=0,
            cached_total_turns=0,
            per_channel_cap=200,
            channel_lru_cap=50,
            min_floor_turns=3,
        ),
        provider=ai_config_projection_service.ProviderSnapshot(
            enabled=enabled,
            default_provider=provider_name,
            setup_advisor_provider=provider_name,
            provider_active=provider_name,
            degraded=degraded,
            last_error_type=last_error,
            last_fallback_reason=None,
            requests_observed=requests,
            failures_observed=failures,
            redaction_enabled=True,
        ),
        projection=ai_config_projection_service.ProjectionSnapshot(
            drift_count=drift_count,
        ),
        instruction=ai_config_projection_service.InstructionSnapshot(),
        audit=ai_config_projection_service.AuditSnapshot(),
    )


# ---------------------------------------------------------------------------
# build_status_embed
# ---------------------------------------------------------------------------


def test_status_embed_with_snapshot_sources_provider_fields():
    snap = _snapshot(provider_name="openai", requests=42, failures=3)
    embed = build_status_embed(snap)
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Default provider"] == "openai"
    assert fields["Active provider"] == "openai"
    assert fields["Requests"] == "42"
    assert fields["Failures"] == "3"
    assert fields["Enabled"] == "yes"


def test_status_embed_without_snapshot_falls_back_to_diagnostics(monkeypatch):
    """Panel-header callsite has no guild context — the builder still
    works by reading directly from ``ai_diagnostics_service``."""
    monkeypatch.setattr(
        ai_diagnostics_service,
        "snapshot_for_cog",
        lambda: {
            "enabled": True,
            "default_provider": "deterministic",
            "setup_advisor_provider": "deterministic",
            "provider_active": "deterministic",
            "requests_observed": 5,
            "failures_observed": 0,
        },
    )
    embed = build_status_embed(None)
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Default provider"] == "deterministic"
    assert fields["Requests"] == "5"


def test_status_embed_handles_none_provider_gracefully():
    """A guild with no provider configured renders ``—`` rather than
    raising. Snapshot fields are typed as ``str | None``."""
    snap = _snapshot(provider_name="")
    # Replace default_provider with None to exercise the dash branch.
    snap = ai_config_projection_service.AIConfigSnapshot(
        guild_id=snap.guild_id,
        policy=snap.policy,
        memory=snap.memory,
        provider=ai_config_projection_service.ProviderSnapshot(
            enabled=False,
            default_provider=None,
            setup_advisor_provider=None,
            provider_active=None,
            degraded=False,
            last_error_type=None,
            last_fallback_reason=None,
            requests_observed=0,
            failures_observed=0,
            redaction_enabled=True,
        ),
        projection=snap.projection,
        instruction=snap.instruction,
        audit=snap.audit,
    )
    embed = build_status_embed(snap)
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Default provider"] == "—"
    assert fields["Active provider"] == "—"
    assert fields["Enabled"] == "no"


# ---------------------------------------------------------------------------
# build_support_report_draft with snapshot
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_support_report_draft_includes_snapshot_header(monkeypatch):
    from services import ai_decision_audit_service

    monkeypatch.setattr(
        ai_decision_audit_service, "query", AsyncMock(return_value=[]),
    )

    snap = _snapshot(window_minutes=30, scan_enabled=True)
    draft = await build_support_report_draft(
        guild_id=1, bot_user_id=42, snapshot=snap,
    )
    assert "# provider: openai" in draft
    assert "# model: gpt-4o-mini" in draft
    assert "# memory: 30 min" in draft
    assert "scan=on" in draft


@pytest.mark.asyncio
async def test_support_report_draft_without_snapshot_skips_header(monkeypatch):
    """When no snapshot is supplied, the draft has no provider/memory
    header lines — backwards compatible with the original output."""
    from services import ai_decision_audit_service

    monkeypatch.setattr(
        ai_decision_audit_service, "query", AsyncMock(return_value=[]),
    )

    draft = await build_support_report_draft(guild_id=1, bot_user_id=42)
    assert "# provider:" not in draft
    assert "# memory:" not in draft


@pytest.mark.asyncio
async def test_support_report_draft_renders_memory_minimal(monkeypatch):
    """``window_minutes=0`` renders 'minimal (N-turn floor)'."""
    from services import ai_decision_audit_service

    monkeypatch.setattr(
        ai_decision_audit_service, "query", AsyncMock(return_value=[]),
    )

    snap = _snapshot(window_minutes=0)
    draft = await build_support_report_draft(
        guild_id=1, bot_user_id=42, snapshot=snap,
    )
    assert "# memory: minimal (3-turn floor)" in draft


@pytest.mark.asyncio
async def test_support_report_draft_renders_degraded_gateway(monkeypatch):
    from services import ai_decision_audit_service

    monkeypatch.setattr(
        ai_decision_audit_service, "query", AsyncMock(return_value=[]),
    )

    snap = _snapshot(degraded=True, last_error="HTTPTimeout")
    draft = await build_support_report_draft(
        guild_id=1, bot_user_id=42, snapshot=snap,
    )
    assert "# gateway: degraded" in draft
    assert "HTTPTimeout" in draft


@pytest.mark.asyncio
async def test_support_report_draft_renders_projection_drift(monkeypatch):
    from services import ai_decision_audit_service

    monkeypatch.setattr(
        ai_decision_audit_service, "query", AsyncMock(return_value=[]),
    )

    snap = _snapshot(drift_count=2)
    draft = await build_support_report_draft(
        guild_id=1, bot_user_id=42, snapshot=snap,
    )
    assert "projection_drift: 2 field(s)" in draft


@pytest.mark.asyncio
async def test_support_report_audit_body_unchanged_by_snapshot(monkeypatch):
    """Stop-condition pin: PR-4A is a read-source replacement. The
    audit-row body lines look the same whether a snapshot is supplied
    or not."""
    from services import ai_decision_audit_service

    monkeypatch.setattr(
        ai_decision_audit_service,
        "query",
        AsyncMock(
            return_value=[
                {
                    "decision": "denied",
                    "reason_code": "below_min_level",
                    "task": "general.nl_answer",
                    "route": "openai",
                    "provider": "openai",
                    "model": "gpt-4",
                },
            ],
        ),
    )

    snap = _snapshot()
    draft_with = await build_support_report_draft(
        guild_id=1, bot_user_id=42, snapshot=snap,
    )
    draft_without = await build_support_report_draft(guild_id=1, bot_user_id=42)
    # The audit-row body line is identical in both drafts (string match).
    audit_line = (
        "- decision=denied reason=below_min_level "
        "task=general.nl_answer route=openai "
        "provider=openai model=gpt-4"
    )
    assert audit_line in draft_with
    assert audit_line in draft_without


# ---------------------------------------------------------------------------
# Consistency: same snapshot produces same provider fields across surfaces
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_status_and_support_report_agree_on_provider(monkeypatch):
    from services import ai_decision_audit_service

    monkeypatch.setattr(
        ai_decision_audit_service, "query", AsyncMock(return_value=[]),
    )

    snap = _snapshot(provider_name="openai", model="gpt-4o-mini")
    status = build_status_embed(snap)
    draft = await build_support_report_draft(
        guild_id=1, bot_user_id=42, snapshot=snap,
    )
    status_fields = {f.name: f.value for f in status.fields}
    assert status_fields["Default provider"] == "openai"
    assert "# provider: openai" in draft
    assert "# model: gpt-4o-mini" in draft
