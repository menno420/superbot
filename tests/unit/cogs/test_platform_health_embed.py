"""Tests for the deterministic !platform health surface — PR2.

Covers the embed renderer (``build_health_embed``) and that the Platform
panel routes its ``health`` selection through the same builder (so the
typed command and the panel render identical facts).
"""

from __future__ import annotations

import datetime
from unittest.mock import AsyncMock, MagicMock

import discord

import views.diagnostic.platform_panel as panel
from cogs.diagnostic._platform_embeds import build_health_embed
from services.health_contracts import (
    FindingSeverity,
    HealthAudience,
    HealthSnapshot,
    OperationalHealthFinding,
    SnapshotStatus,
    SubsystemHealth,
)


def _snapshot(
    *,
    status: SnapshotStatus = SnapshotStatus.DEGRADED,
    partial: bool = False,
    n_subs: int = 3,
    n_findings: int = 2,
    audience: HealthAudience = HealthAudience.GUILD_ADMIN,
) -> HealthSnapshot:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    subs = tuple(
        SubsystemHealth(
            name=f"sub{i}",
            status=SnapshotStatus.HEALTHY,
            summary=f"subsystem {i} ok",
            generated_at=now,
        )
        for i in range(n_subs)
    )
    findings = tuple(
        OperationalHealthFinding(
            fingerprint=f"f{i}",
            severity=FindingSeverity.WARNING,
            category="c",
            message=f"finding {i}",
            related_subsystem="sub0",
        )
        for i in range(n_findings)
    )
    return HealthSnapshot(
        snapshot_id="abc123",
        generated_at=now,
        purpose="summary",
        status=status,
        summary="Overall status: degraded — attention: sub0.",
        subsystems=subs,
        findings=findings,
        partial=partial,
        redaction_audience=audience,
    )


def test_build_health_embed_basic() -> None:
    embed = build_health_embed(_snapshot())
    assert embed.title == "🩺 Bot health"
    assert embed.color == discord.Color.gold()  # degraded
    field_names = [f.name for f in embed.fields]
    assert "Subsystems" in field_names
    assert any(f.name.startswith("Findings") for f in embed.fields)
    assert "guild_admin" in (embed.footer.text or "")
    assert "deterministic" in (embed.footer.text or "")


def test_build_health_embed_status_colors() -> None:
    assert build_health_embed(
        _snapshot(status=SnapshotStatus.HEALTHY, n_findings=0)
    ).color == discord.Color.green()
    assert build_health_embed(
        _snapshot(status=SnapshotStatus.CRITICAL)
    ).color == discord.Color.red()
    assert build_health_embed(
        _snapshot(status=SnapshotStatus.UNKNOWN, n_findings=0)
    ).color == discord.Color.light_grey()


def test_build_health_embed_partial_note() -> None:
    embed = build_health_embed(_snapshot(partial=True))
    assert "partial" in (embed.description or "")


def test_build_health_embed_no_findings_field_when_empty() -> None:
    embed = build_health_embed(_snapshot(n_findings=0))
    assert not any(f.name.startswith("Findings") for f in embed.fields)


def test_build_health_embed_stays_within_discord_limits() -> None:
    # Pathological snapshot: many subsystems + findings with long messages.
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    subs = tuple(
        SubsystemHealth(
            name=f"subsystem_{i}",
            status=SnapshotStatus.DEGRADED,
            summary="x" * 300,
            generated_at=now,
        )
        for i in range(20)
    )
    findings = tuple(
        OperationalHealthFinding(
            fingerprint=f"f{i}",
            severity=FindingSeverity.ERROR,
            category="c",
            message="y" * 300,
            related_subsystem="subsystem_0",
        )
        for i in range(20)
    )
    snap = HealthSnapshot(
        snapshot_id="z" * 12,
        generated_at=now,
        purpose="summary",
        status=SnapshotStatus.CRITICAL,
        summary="z" * 300,
        subsystems=subs,
        findings=findings,
    )
    embed = build_health_embed(snap)
    assert len(embed) <= 6000
    for field in embed.fields:
        assert len(field.value) <= 1024


async def test_panel_health_routes_through_same_builder(monkeypatch) -> None:
    """The panel's ``health`` dispatch must reuse build_health_embed."""
    snap = _snapshot(audience=HealthAudience.PLATFORM_OWNER)

    monkeypatch.setattr(
        "services.health_snapshot_service.resolve_audience",
        AsyncMock(return_value=HealthAudience.PLATFORM_OWNER),
    )
    monkeypatch.setattr(
        "services.health_snapshot_service.collect_snapshot",
        AsyncMock(return_value=snap),
    )

    interaction = MagicMock()
    interaction.client = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 42
    interaction.user = MagicMock()

    embed = await panel._dispatch("health", interaction)
    assert embed.title == "🩺 Bot health"
    assert "platform_owner" in (embed.footer.text or "")


def test_health_is_a_runtime_panel_option() -> None:
    keys = {opt[0] for opt in panel._RUNTIME_OPTIONS}
    assert "health" in keys
