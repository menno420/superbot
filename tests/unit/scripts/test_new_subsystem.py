"""Tests for ``scripts/new_subsystem.py`` (the Q-0025 registration scaffold).

The checker is exercised against the real repo state: a fully registered
subsystem reports all touch-points OK; a bogus key reports the missing ones
with paste-ready snippets. This doubles as a regression net — if a future
refactor moves a touch-point (registry, panel-command table, doc row), the
scaffold's checks must move with it or these tests redden.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "new_subsystem.py"


@pytest.fixture(scope="module")
def ns():
    spec = importlib.util.spec_from_file_location("new_subsystem_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _by_name(checks):
    return {c.name: c for c in checks}


def test_derive_key_matches_q0026_snake_case_law(ns):
    assert ns._derive_key("CommunitySpotlightCog") == "community_spotlight"
    assert ns._derive_key("ServerManagementCog") == "server_management"
    assert ns._derive_key("XpCog") == "xp"


def test_registered_subsystem_passes_every_touch_point(ns):
    # Community Spotlight is the scaffold's first consumer — fully wired.
    checks = ns.build_checks(
        "community_spotlight",
        "CommunitySpotlightCog",
        "spotlight",
        "community",
    )
    failed = [c for c in checks if not c.ok]
    assert not failed, f"touch-points regressed: {[(c.name, c.detail) for c in failed]}"


def test_unregistered_key_reports_missing_with_snippets(ns):
    checks = _by_name(ns.build_checks("warp_drive", "WarpDriveCog", "warpmenu", None))
    assert not checks["registry-entry"].ok
    assert "warp_drive" in checks["registry-entry"].snippet
    assert not checks["panel-command"].ok
    assert '("warp_drive", "warpmenu")' in checks["panel-command"].snippet
    assert not checks["cog-file"].ok
    assert not checks["surface-map-row"].ok


def test_key_identity_mismatch_is_flagged(ns):
    checks = _by_name(
        ns.build_checks(
            "communityspotlight", "CommunitySpotlightCog", "spotlight", None,
        ),
    )
    assert not checks["key-identity"].ok
    assert "community_spotlight" in checks["key-identity"].detail


def test_unknown_parent_hub_fails_hub_linkage(ns):
    checks = _by_name(
        ns.build_checks(
            "community_spotlight",
            "CommunitySpotlightCog",
            "spotlight",
            "not_a_hub",
        ),
    )
    assert not checks["hub-linkage"].ok


def test_enumeration_test_files_exist(ns):
    for rel in ns.ENUMERATION_TESTS:
        assert (_REPO_ROOT / rel).exists(), rel


# ---------------------------------------------------------------------------
# Loader / extension-role / sector-folio touch-points (added 2026-06-23 after
# the Karma build, #1332, hit all three as uncaught CI failures).
# ---------------------------------------------------------------------------


def test_new_touch_points_pass_for_fully_wired_subsystem(ns):
    """Karma is wired through every touch-point including the three the
    checker gained 2026-06-23 — they must all report OK.
    """
    checks = _by_name(
        ns.build_checks("karma", "KarmaCog", "karma", "community", has_panel=False),
    )
    for name in ("extension-loaded", "extension-role", "sector-folio"):
        assert name in checks, f"{name} check missing from build_checks"
        assert checks[name].ok, f"{name} regressed: {checks[name].detail}"


def test_extension_loaded_and_role_checks_present_for_any_cog(ns):
    """The loader + extension-role checks attach whenever the cog file is
    found — community_spotlight is a config-only subsystem with no folio, so
    sector-folio is correctly absent while the other two are present.
    """
    checks = _by_name(
        ns.build_checks(
            "community_spotlight",
            "CommunitySpotlightCog",
            "spotlight",
            "community",
        ),
    )
    assert checks["extension-loaded"].ok
    assert checks["extension-role"].ok
    # No docs/subsystems/community_spotlight.md folio → the conditional
    # sector-folio check is skipped, not failed.
    assert "sector-folio" not in checks


def test_sector_folio_helper_reads_the_machine_readable_block(ns):
    # ``karma`` is homed to S1 in the sector-folio-map block.
    assert ns._folio_homed_to_sector("karma") is True
    # A name absent from every S<n>: line is not homed.
    assert ns._folio_homed_to_sector("definitely_not_a_homed_folio") is False


def test_cli_check_exits_zero_for_registered_subsystem(ns, capsys):
    rc = ns.main(
        [
            "check",
            "--key",
            "community_spotlight",
            "--cog",
            "CommunitySpotlightCog",
            "--panel-command",
            "spotlight",
            "--parent-hub",
            "community",
        ],
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "All touch-points present" in out


def test_cli_scaffold_prints_snippets_and_exits_one(ns, capsys):
    rc = ns.main(
        [
            "scaffold",
            "--key",
            "warp_drive",
            "--cog",
            "WarpDriveCog",
            "--panel-command",
            "warpmenu",
        ],
    )
    assert rc == 1
    out = capsys.readouterr().out
    assert "paste-ready snippets" in out
    assert '"warp_drive": {' in out


def test_no_panel_skips_panel_command_check(ns):
    # Config-only subsystems (ai/welcome/counters/automod) carry NO
    # KNOWN_PANEL_COMMANDS entry; without --no-panel the check is a false MISSING.
    with_panel = _by_name(ns.build_checks("welcome", "WelcomeCog", "welcome", None))
    assert not with_panel["panel-command"].ok  # the false positive the flag fixes

    checks = ns.build_checks("welcome", "WelcomeCog", "welcome", None, has_panel=False)
    assert "panel-command" not in _by_name(checks)
    failed = [c for c in checks if not c.ok]
    assert not failed, f"config-only welcome should pass: {[(c.name, c.detail) for c in failed]}"


def test_cli_no_panel_exits_zero_for_config_only_subsystem(ns, capsys):
    rc = ns.main(
        [
            "check",
            "--key",
            "welcome",
            "--cog",
            "WelcomeCog",
            "--panel-command",
            "welcome",
            "--no-panel",
        ],
    )
    assert rc == 0
    assert "All touch-points present" in capsys.readouterr().out
