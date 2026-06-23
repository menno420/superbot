"""Per-command help-reachability invariant (discoverability audit, Session 1).

The command-level companion to ``test_discoverability.py`` (which guards that
every *subsystem* is homed).  This guards the next level down — the gap the owner
reported ("the general cog is completely unfindable from the help menu"): **every
member-tier command must live in a cog that is reachable by clicking through
``!help``.**

It drives ``scripts/check_command_reachability.py`` (the static checker) and
**ratchets against a recorded baseline** (Q-0105 warn-first): the pre-existing
orphan-cog gaps are tolerated, but any *new* unreachable member command fails —
which is what makes "every command findable" un-regressable while the per-cog
audit follow-on sessions clear the baseline.

The baseline is the per-cog gap list recorded in
``docs/audits/command-reachability-gaps-2026-06-23.md``.  When a follow-on session
homes one of these cogs (or surfaces its commands via a panel button), it removes
the matching baseline entry here — :func:`test_baseline_has_no_stale_entries`
fails until it does, so the baseline can never go stale.

Sibling invariants: ``test_discoverability.py`` (subsystem-level homing),
``test_command_synonyms_resolve_to_real_commands.py``.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "check_command_reachability.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location(
        "check_command_reachability_ut", _SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_CHECK = _load_checker()


# ---------------------------------------------------------------------------
# Baseline — the accepted pre-existing per-cog gaps (audit follow-on work).
#
# Each is a member-tier command whose cog maps to no homed + help-discoverable
# subsystem, so it is not auto-listed under any hub.  They are recorded (not
# allowlisted) on purpose: they are real findings a later per-cog audit session
# clears.  REMOVE an entry here when its cog is homed / its command buttonized —
# `test_baseline_has_no_stale_entries` enforces that the baseline shrinks.
#
# Full per-cog write-up + disposition:
#   docs/audits/command-reachability-gaps-2026-06-23.md
# ---------------------------------------------------------------------------
_BASELINE: frozenset[tuple[str, str]] = frozenset(
    {
        # !temproles — member view of one's temp roles; not surfaced in any roles panel.
        # Routed to fleet unit U2 (roles) — see the consolidation-fleet-plan.
        ("disbot/cogs/role_grants_cog.py", "temproles"),
    },
)


# ---------------------------------------------------------------------------
# The ratchet
# ---------------------------------------------------------------------------


def test_no_new_command_reachability_gaps():
    """No member-tier command may become unreachable beyond the recorded baseline.

    This is the un-regressable guarantee: a newly-added member command whose cog
    is not homed under a help-discoverable subsystem (and is not operator/internal/
    allowlisted) fails here, with a punch list of the offending commands.
    """
    report = _CHECK.run_check()
    gaps = _CHECK.gap_keys(report)
    new = sorted(gaps - _BASELINE)
    assert not new, (
        "New command-reachability gap(s) — member-tier commands not reachable from "
        f"the !help tree: {new}. Fix by one of: home the cog's subsystem (parent_hub "
        "+ a build_help_menu_view hook or a *menu entry-point), surface the command "
        "via a panel button, mark it operator/internal, or — if it is genuinely a "
        "non-member command the static scan misclassified — add it to "
        "architecture_rules/command_reachability_exceptions.yml with a reason. "
        "See scripts/check_command_reachability.py."
    )


def test_baseline_has_no_stale_entries():
    """Every baseline entry must still be a real gap — the baseline can't go stale.

    When a per-cog audit session homes one of these cogs (or buttonizes its
    commands), the gap disappears and this test fails until the now-fixed entry is
    removed from ``_BASELINE`` — so the recorded debt only ever shrinks.
    """
    report = _CHECK.run_check()
    gaps = _CHECK.gap_keys(report)
    fixed = sorted(_BASELINE - gaps)
    assert not fixed, (
        "These baseline command-reachability gaps are no longer gaps (the cog was "
        f"homed / the command buttonized): {fixed}. Remove them from _BASELINE in "
        "this test so the recorded debt stays accurate."
    )


# ---------------------------------------------------------------------------
# Classification sanity — the guard's exemptions behave as intended
# ---------------------------------------------------------------------------


def test_operator_gated_commands_are_exempt():
    """``!setup`` / ``!btd6ops`` are operator-gated → exempt, never a gap.

    They gate at runtime (inside the command / its subcommands), so they are
    allowlisted in ``command_reachability_exceptions.yml``.
    """
    report = _CHECK.run_check()
    gaps = _CHECK.gap_keys(report)
    assert ("disbot/cogs/setup_cog.py", "setup") not in gaps
    assert ("disbot/cogs/btd6_ops_cog.py", "btd6ops") not in gaps


def test_help_command_is_exempt():
    """``!help`` is the root discovery surface — it cannot be reached through itself."""
    report = _CHECK.run_check()
    gaps = _CHECK.gap_keys(report)
    assert ("disbot/cogs/help_cog.py", "help") not in gaps


def test_general_subsystem_commands_are_reachable():
    """The General cog's commands resolve to a homed + discoverable subsystem.

    The owner-reported "general unfindable" gap was a *view*-rendering bug (the
    Utility hub did not surface its General child — fixed separately and guarded by
    ``tests/unit/cogs/test_utility_hub_children.py``).  At the registry level the
    `general` subsystem has always been homed, so none of its commands are flagged
    here — this pins that they stay classified reachable.
    """
    report = _CHECK.run_check()
    gaps = _CHECK.gap_keys(report)
    for cmd in ("joke", "fact", "quote", "trivia", "motivate", "greet"):
        assert ("disbot/cogs/general_cog.py", cmd) not in gaps


def test_reachability_helpers_classify_known_subsystems():
    """The reachability primitives agree with the registry for known subsystems."""
    # economy is a top-level hub child with a help hook → homed + discoverable.
    assert _CHECK._subsystem_homed("economy") is True
    assert _CHECK._subsystem_discoverable("economy") is True
    # general is a Utility child with a help hook.
    assert _CHECK._subsystem_homed("general") is True
    assert _CHECK._subsystem_discoverable("general") is True
    # a nonexistent subsystem is neither.
    assert _CHECK._subsystem_homed("not_a_subsystem") is False
    assert _CHECK._subsystem_discoverable("not_a_subsystem") is False


def test_every_cog_command_is_classified_once():
    """Sanity: reachable + exempt + gaps accounts for every scanned prefix command."""
    report = _CHECK.run_check()
    total = report.reachable + report.exempt + len(report.gaps)
    # The repo has well over 100 prefix commands; guard against an empty scan
    # (a path/import regression) silently passing the ratchet.
    assert total > 100, f"Only {total} prefix commands scanned — scan likely broke."
