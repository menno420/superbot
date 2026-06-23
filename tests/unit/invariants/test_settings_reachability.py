"""Settings-reachability invariant (consolidation audit — settings half).

The *settings* companion to ``test_command_reachability.py``.  Where that guards
that every member command is reachable through ``!help``, this guards the audit's
§3.4 goal — **every cog's configurable settings are reachable from the
``!settings`` hub** — and makes it un-regressable.

It drives ``scripts/check_settings_reachability.py`` (the static checker) and
**ratchets against a recorded baseline** (Q-0105 warn-first): the baseline is the
set of accepted pre-existing gaps, and any *new* gap fails.  The baseline is
currently **empty** — every config-declaring subsystem either surfaces in the
Settings hub (declares a ``SubsystemSchema``, non-internal) or is an explicit,
reasoned allowlist entry (the intentional domain-panel cases: counting/chain
per-channel game setup, the channel-visibility admin action).

Full write-up + exemption disposition:
  docs/audits/settings-reachability-2026-06-23.md

Sibling invariants: ``test_command_reachability.py`` (per-command help),
``test_discoverability.py`` (subsystem-level homing).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_settings_reachability.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "check_settings_reachability_ut", _SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_CHECK = _load_checker()


# ---------------------------------------------------------------------------
# Baseline — accepted pre-existing settings-reachability gaps (none).
#
# Each entry would be a subsystem that declares configurable settings but is not
# reachable from the !settings hub and is not (yet) allowlisted.  There are none:
# the 3 configure-capability-without-schema subsystems (counting/chain/channel)
# are *intentional* domain-panel cases, recorded as reasoned allowlist entries in
# architecture_rules/settings_reachability_exceptions.yml — not gaps.  REMOVE an
# entry here only when its subsystem becomes reachable; never add one to mute a
# real gap that should be fixed by adding a SubsystemSchema.
# ---------------------------------------------------------------------------
_BASELINE: frozenset[str] = frozenset()


def _current_gap_keys() -> set[str]:
    return {f.key for f in _CHECK.gaps(_CHECK.collect_findings())}


# ---------------------------------------------------------------------------
# The ratchet
# ---------------------------------------------------------------------------


def test_no_new_settings_reachability_gaps():
    """No config-declaring subsystem is unreachable from !settings beyond the
    accepted baseline. A *new* gap (a schema marked internal, or a new
    ``*.configure`` capability with neither a schema nor an allowlist entry)
    fails here — that is what keeps settings centralized.
    """
    new = _current_gap_keys() - _BASELINE
    assert not new, (
        "New settings-reachability gap(s): "
        f"{sorted(new)}. Centralize the config (add a SubsystemSchema so it "
        "surfaces in !settings) or allowlist it with a reason in "
        "architecture_rules/settings_reachability_exceptions.yml."
    )


def test_baseline_has_no_stale_entries():
    """The baseline only ever shrinks: an entry that is no longer a gap must be
    removed so the ledger can never go stale.
    """
    stale = _BASELINE - _current_gap_keys()
    assert (
        not stale
    ), f"Baseline entries that are no longer gaps — remove them: {sorted(stale)}"


def test_known_schema_subsystems_are_reachable():
    """A spot-check that real schema-bearing subsystems classify as reachable."""
    by_sub = {f.subsystem: f for f in _CHECK.collect_findings()}
    for sub in ("economy", "moderation", "ai", "xp", "karma"):
        assert sub in by_sub, f"{sub!r} should appear in the findings"
        assert (
            by_sub[sub].status == "reachable"
        ), f"{sub!r} should be reachable: {by_sub[sub].reason}"


def test_allowlisted_domain_panel_subsystems_are_exempt_not_gaps():
    """counting/chain/channel are intentional domain-panel cases — exempt, never gaps."""
    by_sub = {f.subsystem: f for f in _CHECK.collect_findings()}
    for sub in ("counting", "chain", "channel"):
        assert sub in by_sub, f"{sub!r} should appear in the findings"
        assert (
            by_sub[sub].status == "exempt"
        ), f"{sub!r} should be exempt: {by_sub[sub].reason}"


def test_strict_mode_is_clean():
    """With the baseline empty and all gaps allowlisted, the guard is strict-clean —
    so it can graduate to ``--mode strict`` failing CI on any future gap.
    """
    assert _current_gap_keys() == set()
