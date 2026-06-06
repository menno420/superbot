"""Role DiagnosticsPanel — the operator's window into role-automation health.

Pins the pure ``_format_preflight`` summary so the panel surfaces the exact
blockers ``role_automation.apply`` enforces before mutating (missing Manage
Roles / role above the bot / configured role gone) — the live diagnostic for
the "role_automation.apply failed for member" degradation.
"""

from __future__ import annotations

from services.role_automation import PreflightResult
from views.roles.diagnostics_panel import _format_preflight


def test_format_preflight_flags_missing_manage_roles():
    out = _format_preflight(PreflightResult(bot_has_manage_roles=False))
    assert "Manage Roles" in out
    assert out.startswith("🔴")


def test_format_preflight_all_clear():
    out = _format_preflight(PreflightResult(bot_has_manage_roles=True))
    assert out.startswith("🟢")


def test_format_preflight_reports_hierarchy_and_missing():
    out = _format_preflight(
        PreflightResult(
            bot_has_manage_roles=True,
            hierarchy_blockers=("Veteran",),
            missing_roles=("Ghost",),
        ),
    )
    assert out.startswith("⚠️")
    assert "above my top role: Veteran" in out
    assert "missing: Ghost" in out
