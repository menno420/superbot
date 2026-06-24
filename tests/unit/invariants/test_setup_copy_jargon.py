"""Setup-copy jargon ratchet (setup-wizard restructure plan — Law 2).

Drives ``scripts/check_setup_copy.py`` (the static plain-language guard) and
**ratchets against a recorded baseline** (Q-0105 warn-first): the current
jargon-heavy setup copy is tolerated, but the count may only ever go *down* and
no *new* setup file may introduce jargon.  As the spine rewrite (plan PR 1)
cleans each section's copy, lower ``_BASELINE_TOTAL`` to lock in the gain; when
it reaches zero the guard graduates to ``--mode strict`` in CI.

Why two assertions rather than a frozen 207-line baseline: line numbers shift
constantly, so a per-line baseline is noise.  The two real regressions we must
catch are (a) an existing file growing *more* jargon and (b) a brand-new setup
section shipping with jargon — a count ceiling catches (a), the file-set guard
catches (b).

Baseline measured 2026-06-24 against the pre-restructure wizard:
  207 operator-facing jargon strings across 33 files (``check_setup_copy --json``).

Sibling invariants: ``test_settings_reachability.py``, ``test_command_reachability.py``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_setup_copy.py"

# Ratchet ceiling — lower this as the spine rewrite cleans copy; never raise it.
_BASELINE_TOTAL = 207

# The setup files that carry jargon debt today. A finding in any file NOT in
# this set is new jargon and fails — new sections must ship plain-language.
_BASELINE_FILES = frozenset(
    {
        "disbot/views/setup/ai_review/main_panel.py",
        "disbot/views/setup/ai_review/per_recommendation.py",
        "disbot/views/setup/depth_panel.py",
        "disbot/views/setup/draft_render.py",
        "disbot/views/setup/final_review.py",
        "disbot/views/setup/hub.py",
        "disbot/views/setup/launcher.py",
        "disbot/views/setup/provisioning/confirm_panel.py",
        "disbot/views/setup/provisioning/preview_panel.py",
        "disbot/views/setup/recovery.py",
        "disbot/views/setup/scan_panel.py",
        "disbot/views/setup/section_card.py",
        "disbot/views/setup/sections/ai_setup.py",
        "disbot/views/setup/sections/btd6.py",
        "disbot/views/setup/sections/channels.py",
        "disbot/views/setup/sections/cleanup.py",
        "disbot/views/setup/sections/cog_routing.py",
        "disbot/views/setup/sections/diagnostics.py",
        "disbot/views/setup/sections/final_review.py",
        "disbot/views/setup/sections/identity.py",
        "disbot/views/setup/sections/logging_presets.py",
        "disbot/views/setup/sections/moderation.py",
        "disbot/views/setup/sections/preset_select.py",
        "disbot/views/setup/sections/purpose.py",
        "disbot/views/setup/sections/readiness.py",
        "disbot/views/setup/sections/role_templates.py",
        "disbot/views/setup/sections/roles.py",
        "disbot/views/setup/sections/server_scan.py",
        "disbot/views/setup/sections/suggestions.py",
        "disbot/views/setup/sections/ticket.py",
        "disbot/views/setup/summary.py",
        "disbot/views/setup/template_picker.py",
        "disbot/views/setup/wizard.py",
    },
)


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_setup_copy_ut", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_jargon_count_does_not_regress() -> None:
    checker = _load_checker()
    findings = checker.scan_setup_copy()
    assert len(findings) <= _BASELINE_TOTAL, (
        f"Setup-copy jargon rose to {len(findings)} (baseline {_BASELINE_TOTAL}). "
        "New operator-facing jargon was added — see plan §4 for plain-language "
        "replacements, or run `python3.10 scripts/check_setup_copy.py`."
    )


def test_no_new_setup_file_introduces_jargon() -> None:
    checker = _load_checker()
    dirty_files = {f.file for f in checker.scan_setup_copy()}
    new_dirty = dirty_files - _BASELINE_FILES
    assert not new_dirty, (
        "New setup file(s) shipped with operator-facing jargon: "
        f"{sorted(new_dirty)}. New sections must use plain language (plan Law 2)."
    )


def test_clean_string_is_not_flagged() -> None:
    """A plain-language label produces no finding; a jargon one does (guard sanity)."""
    checker = _load_checker()
    assert checker._terms_in("Greet new members when they join") == ()
    assert "stage" in checker._terms_in("Each pick stages an operation in the draft")
