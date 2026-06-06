"""Redaction tests for the health snapshot — PR1 (bot awareness).

The redaction boundary is a pure transform tested for *omission* (not
masking) with **per-adapter planted leaks**: every source that can carry
free text or an identifier is seeded with a secret/ID and we assert it
never survives into the projected snapshot at the relevant audience.

Two layers are under test:

1. ``_scrub`` — strips secrets / long IDs / hashes / multi-line traces
   from all free text at adapter time (every audience).
2. ``project_for_audience`` — removes owner-only *fields* (``file_hint``,
   ``related_provider``) for ``GUILD_ADMIN`` and drops all detail for
   ``PUBLIC``.
"""

from __future__ import annotations

import datetime

import pytest

from core.runtime import startup_outcome
from services import (
    ai_diagnostics_service,
    diagnostics_service,
)
from services import health_snapshot_service as hss
from services import (
    resource_health,
)
from services.health_contracts import (
    FindingSeverity,
    HealthAudience,
    HealthSnapshot,
    OperationalHealthFinding,
    SnapshotStatus,
    SubsystemHealth,
)

_SECRET = "S3CR3TTOKENvalue"
_SNOWFLAKE = "1234567890123456789"  # 19-digit Discord ID


def _all_text(snapshot: HealthSnapshot) -> str:
    """Concatenate every operator-visible string in a snapshot."""
    parts: list[str] = [snapshot.summary]
    findings = list(snapshot.findings)
    for sub in snapshot.subsystems:
        parts.append(sub.summary)
        parts.extend(f"{k}={v}" for k, v in sub.facts.items())
        findings.extend(sub.findings)
    for f in findings:
        parts.extend(
            str(x)
            for x in (
                f.message,
                f.file_hint,
                f.related_provider,
                f.related_command,
                f.suggested_next_step,
            )
            if x is not None
        )
    return " ".join(parts)


# --- _scrub primitive ------------------------------------------------------


def test_scrub_removes_keyed_secret() -> None:
    out = hss._scrub(f"RuntimeError: token={_SECRET} at boot")
    assert _SECRET not in out
    assert "<secret>" in out


def test_scrub_collapses_snowflake_ids() -> None:
    out = hss._scrub(f"role {_SNOWFLAKE} is missing")
    assert _SNOWFLAKE not in out
    assert "<id>" in out


def test_scrub_flattens_multiline_traceback() -> None:
    trace = "Traceback (most recent call last):\n  File x\n  line y\nBoom"
    out = hss._scrub(trace)
    assert "\n" not in out


def test_scrub_bounds_length() -> None:
    out = hss._scrub("x" * 5000)
    assert len(out) <= hss.MAX_MESSAGE_CHARS


def test_scrub_strips_jwt_and_hash() -> None:
    jwt = "aaaaaaaaaa.bbbbbbbb.cccccccccccccccc"
    assert "<token>" in hss._scrub(f"auth {jwt}")
    assert "<hash>" in hss._scrub("digest deadbeefdeadbeefdeadbeefdeadbeef")


# --- project_for_audience field omission -----------------------------------


def _finding_with_owner_detail() -> OperationalHealthFinding:
    return OperationalHealthFinding(
        fingerprint="x",
        severity=FindingSeverity.ERROR,
        category="diagnostics.provider_failed",
        message="A provider failed.",
        related_provider="secret_provider_name",
        file_hint="owner-only error detail",
        related_subsystem="diagnostics",
    )


def _snapshot_with(finding: OperationalHealthFinding) -> HealthSnapshot:
    sub = SubsystemHealth(
        name="diagnostics",
        status=SnapshotStatus.DEGRADED,
        summary="1 provider failing",
        generated_at=datetime.datetime.now(tz=datetime.timezone.utc),
        findings=(finding,),
        facts={"failed_count": 1},
    )
    return hss._finalize([sub], purpose="summary", partial=False)


def test_admin_projection_strips_owner_fields() -> None:
    snap = _snapshot_with(_finding_with_owner_detail())
    admin = hss.project_for_audience(snap, HealthAudience.GUILD_ADMIN)
    for f in admin.findings:
        assert f.file_hint is None
        assert f.related_provider is None
    assert admin.redaction_audience is HealthAudience.GUILD_ADMIN


def test_owner_projection_keeps_owner_fields() -> None:
    snap = _snapshot_with(_finding_with_owner_detail())
    owner = hss.project_for_audience(snap, HealthAudience.PLATFORM_OWNER)
    assert any(f.file_hint == "owner-only error detail" for f in owner.findings)


def test_public_projection_drops_findings_and_facts() -> None:
    snap = _snapshot_with(_finding_with_owner_detail())
    public = hss.project_for_audience(snap, HealthAudience.PUBLIC)
    assert public.findings == ()
    for sub in public.subsystems:
        assert sub.findings == ()
        assert dict(sub.facts) == {}


# --- per-adapter planted leaks --------------------------------------------


def test_diagnostics_provider_error_leak_is_contained() -> None:
    """A provider error containing a secret must not reach an admin."""
    name = "test_health_leak_provider"

    def _raiser() -> dict:
        raise RuntimeError(f"token={_SECRET} failed at /home/user/secret.py:9")

    diagnostics_service.register(name, _raiser)
    try:
        sub = hss._diagnostics_subsystem()
    finally:
        diagnostics_service.unregister(name)

    raw = hss._finalize([sub], purpose="summary", partial=False)
    admin = hss.project_for_audience(raw, HealthAudience.GUILD_ADMIN)
    owner = hss.project_for_audience(raw, HealthAudience.PLATFORM_OWNER)

    # Secret never appears at any audience (scrubbed at adapter time)...
    assert _SECRET not in _all_text(admin)
    assert _SECRET not in _all_text(owner)
    # ...and the admin never even sees the provider name / hint field.
    assert name not in _all_text(admin)


async def test_resource_finding_id_leak_is_scrubbed(monkeypatch) -> None:
    fake = resource_health.ResourceHealthFinding(
        subsystem="roles",
        binding_name="mod_role",
        kind="role",  # adapter ignores .kind; plain test double
        status="stale_binding",
        severity="error",
        message=f"role {_SNOWFLAKE} no longer resolves",
        target_id=int(_SNOWFLAKE),
    )

    async def _fake_inspect(_guild):
        return (fake,)

    monkeypatch.setattr(resource_health, "inspect", _fake_inspect)

    class _Bot:
        def get_guild(self, _gid):
            return object()

    sub = await hss._resources_subsystem(_Bot(), 42)
    raw = hss._finalize([sub], purpose="guild", partial=False)
    for audience in (HealthAudience.GUILD_ADMIN, HealthAudience.PLATFORM_OWNER):
        text = _all_text(hss.project_for_audience(raw, audience))
        assert _SNOWFLAKE not in text


def test_ai_error_leak_is_contained(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_diagnostics_service,
        "snapshot_for_cog",
        lambda: {
            "enabled": True,
            "degraded": True,
            "last_error_type": f"AuthError token={_SECRET}",
            "last_fallback_reason": "deterministic",
            "requests_observed": 1,
            "failures_observed": 1,
        },
    )
    sub = hss._ai_subsystem()
    raw = hss._finalize([sub], purpose="summary", partial=False)
    assert _SECRET not in _all_text(hss.project_for_audience(raw, HealthAudience.PLATFORM_OWNER))
    assert _SECRET not in _all_text(hss.project_for_audience(raw, HealthAudience.GUILD_ADMIN))


def test_startup_error_leak_is_contained() -> None:
    startup_outcome.reset_for_tests()
    try:
        startup_outcome.record_failure(
            "test_phase",
            RuntimeError(f"token={_SECRET} /home/user/secret.py:42"),
        )
        sub = hss._startup_subsystem()
    finally:
        startup_outcome.reset_for_tests()

    raw = hss._finalize([sub], purpose="summary", partial=False)
    admin = hss.project_for_audience(raw, HealthAudience.GUILD_ADMIN)
    owner = hss.project_for_audience(raw, HealthAudience.PLATFORM_OWNER)
    assert _SECRET not in _all_text(admin)
    assert _SECRET not in _all_text(owner)
    # owner keeps the (scrubbed) file_hint; admin does not.
    assert all(f.file_hint is None for s in admin.subsystems for f in s.findings)
