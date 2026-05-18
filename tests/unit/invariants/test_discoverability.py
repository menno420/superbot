"""Discoverability audit invariant (PR 5).

Every entry in :data:`utils.subsystem_registry.SUBSYSTEMS` must have
at least one discoverability path: a Help route (cog implements
``build_help_menu_view``), a panel command (listed in
``KNOWN_PANEL_COMMANDS`` or matches the ``.+menu$`` regex), or an
explicit internal classification (``visibility_mode == "internal"``).

This is a static audit — it does not load the Discord bot or
instantiate cogs.  It uses:

* :data:`utils.subsystem_registry.SUBSYSTEMS` for declared metadata;
* :data:`services.customization_catalogue.KNOWN_PANEL_COMMANDS` for
  the curated panel-command floor (the same source the customization
  catalogue uses);
* :mod:`ast` to scan each cog file for a ``build_help_menu_view``
  method definition.

When a subsystem has no discoverability path the invariant fails
with a punch list of offenders so the operator can decide between
(a) adding a help hook, (b) marking it internal, or (c) adding it
to ``KNOWN_PANEL_COMMANDS``.

The test also produces a categorized report (``HUB_REPORT``) that
counts each discovery mechanism — useful as documentation, not a
gate.

Sibling read-only invariants:

- ``test_identity_contract_strict.py`` — entry_points alignment.
- ``test_settings_cog_read_only.py`` — settings UI mutation discipline.
- ``test_cog_size.py`` — per-cog LOC ceiling.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from services.customization_catalogue import KNOWN_PANEL_COMMANDS
from utils.subsystem_registry import SUBSYSTEMS

_REPO_ROOT = Path(__file__).resolve().parents[3]
_COG_DIR = _REPO_ROOT / "disbot" / "cogs"
_MENU_REGEX = re.compile(r".+menu$")


def _cog_has_help_hook(subsystem: str) -> bool:
    """Return True if ``{subsystem}_cog.py`` declares ``build_help_menu_view``.

    Static check via :mod:`ast` — does not load the cog.  Returns
    False when the cog file doesn't exist (subsystems that don't
    correspond to a single cog file fall through to other
    discoverability paths).
    """
    cog_path = _COG_DIR / f"{subsystem}_cog.py"
    if not cog_path.exists():
        return False
    try:
        tree = ast.parse(cog_path.read_text())
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef | ast.FunctionDef):
            if node.name == "build_help_menu_view":
                return True
    return False


def _discoverability(subsystem: str) -> tuple[bool, str]:
    """Return ``(is_discoverable, mechanism)`` for the named subsystem.

    Mechanism keys:
        ``internal``       — visibility_mode == "internal"
        ``help_root``      — subsystem == "help" with "help" entry_point
                             (the help system is its own discovery path)
        ``panel_command``  — entry_point listed in KNOWN_PANEL_COMMANDS
        ``menu_regex``     — entry_point matches ``.+menu$``
        ``help_hook``      — cog file declares build_help_menu_view
        ``none``           — no discoverability path
    """
    meta = SUBSYSTEMS.get(subsystem) or {}
    if meta.get("visibility_mode") == "internal":
        return True, "internal"

    entry_points = set(meta.get("entry_points") or ())

    # The help system is the root discovery surface — by definition it
    # cannot be reached *through* itself, so the canonical mechanisms
    # below don't apply.  Recognised explicitly so the invariant
    # doesn't flag a tautological orphan.
    if subsystem == "help" and "help" in entry_points:
        return True, "help_root"

    panel_cmds = {cmd for sub, cmd in KNOWN_PANEL_COMMANDS if sub == subsystem}
    if panel_cmds & entry_points:
        return True, "panel_command"

    if any(_MENU_REGEX.match(ep) for ep in entry_points):
        return True, "menu_regex"

    if _cog_has_help_hook(subsystem):
        return True, "help_hook"

    return False, "none"


# ---------------------------------------------------------------------------
# Invariant
# ---------------------------------------------------------------------------


def test_every_subsystem_has_a_discoverability_path():
    """No subsystem may exist without at least one discovery route.

    Failure mode: emits a punch list of subsystems missing every
    mechanism.  Each offender can be fixed by adding (a) a
    ``build_help_menu_view`` method to its cog, (b) a panel command
    entry in :data:`KNOWN_PANEL_COMMANDS`, (c) an entry_point ending
    in ``menu``, or (d) ``visibility_mode = "internal"`` in
    :data:`SUBSYSTEMS`.
    """
    offenders: list[str] = []
    for subsystem in SUBSYSTEMS:
        ok, _mechanism = _discoverability(subsystem)
        if not ok:
            offenders.append(subsystem)

    assert not offenders, (
        "These subsystems have no discoverability path "
        "(help hook / panel command / internal classification): "
        f"{sorted(offenders)}.  Add one of: build_help_menu_view, "
        "KNOWN_PANEL_COMMANDS entry, .+menu entry_point, or set "
        "visibility_mode='internal'."
    )


# ---------------------------------------------------------------------------
# Report — counts each mechanism + per-mechanism subsystem list
# ---------------------------------------------------------------------------


def build_discoverability_report() -> dict[str, list[str]]:
    """Return a ``{mechanism: [subsystem, ...]}`` map for tooling.

    Public helper — useful from REPL or future docs generators.
    """
    report: dict[str, list[str]] = {
        "internal": [],
        "help_root": [],
        "panel_command": [],
        "menu_regex": [],
        "help_hook": [],
        "none": [],
    }
    for subsystem in sorted(SUBSYSTEMS):
        _ok, mechanism = _discoverability(subsystem)
        report[mechanism].append(subsystem)
    return report


def test_report_covers_every_subsystem_exactly_once():
    """Sanity: every subsystem appears in exactly one report bucket."""
    report = build_discoverability_report()
    seen: list[str] = []
    for entries in report.values():
        seen.extend(entries)
    assert sorted(seen) == sorted(SUBSYSTEMS.keys())


def test_report_has_no_orphans_in_none_bucket():
    """The ``none`` bucket must be empty — mirror of the main invariant.

    Kept as a separate test so the per-mechanism counts surface in
    pytest output alongside the punch list.
    """
    report = build_discoverability_report()
    assert report["none"] == [], (
        f"Discoverability orphans: {report['none']}. "
        "See test_every_subsystem_has_a_discoverability_path for the fix."
    )


# ---------------------------------------------------------------------------
# Help-hook coverage — informational
# ---------------------------------------------------------------------------


def test_majority_of_visible_subsystems_have_a_help_hook():
    """Soft check: most visibility_mode='normal' subsystems should
    expose a ``build_help_menu_view`` hook, because the help menu's
    direct-navigation path consumes that hook.

    Not a hard failure — subsystems may legitimately rely on panel
    commands without a hook (e.g. game cogs whose menu is the panel
    itself).  The threshold is intentionally loose (≥60%) so this
    test serves as a regression alarm rather than a forced pattern.
    """
    visible = [
        s for s, m in SUBSYSTEMS.items() if m.get("visibility_mode") != "internal"
    ]
    with_hook = [s for s in visible if _cog_has_help_hook(s)]
    if not visible:
        pytest.skip("No visible subsystems registered.")
    ratio = len(with_hook) / len(visible)
    assert ratio >= 0.6, (
        f"Only {len(with_hook)}/{len(visible)} visible subsystems "
        f"({ratio:.0%}) have build_help_menu_view hooks.  Help-menu "
        "direct-navigation requires the hook; subsystems below this "
        "threshold may be unreachable from !help."
    )


# ---------------------------------------------------------------------------
# Test for the discoverability helpers themselves
# ---------------------------------------------------------------------------


def test_cog_has_help_hook_detects_known_cog():
    """Sanity check: admin_cog declares build_help_menu_view."""
    assert _cog_has_help_hook("admin") is True


def test_cog_has_help_hook_returns_false_for_nonexistent_file():
    assert _cog_has_help_hook("not_a_real_subsystem") is False


def test_discoverability_recognises_internal_classification():
    """If a subsystem is marked internal, it's discoverable regardless
    of panel/hook presence."""
    saved = SUBSYSTEMS.copy()
    try:
        SUBSYSTEMS["__test_internal__"] = {
            "display_name": "Test Internal",
            "description": "fixture",
            "emoji": "🔒",
            "color": 0,
            "visibility_tier": "owner",
            "visibility_mode": "internal",
            "category": "test",
            "tags": [],
            "entry_points": [],
            "default_channels": [],
            "related_subsystems": [],
            "dependencies": [],
            "soft_dependencies": [],
            "supports_dm": False,
            "has_cleanup_rules": False,
            "ui_priority": 0,
            "capabilities": [],
        }
        ok, mechanism = _discoverability("__test_internal__")
        assert ok is True
        assert mechanism == "internal"
    finally:
        SUBSYSTEMS.clear()
        SUBSYSTEMS.update(saved)


def test_discoverability_recognises_panel_command():
    """A subsystem with an entry_point in KNOWN_PANEL_COMMANDS is
    discoverable via panel_command (admin has 'adminmenu')."""
    ok, mechanism = _discoverability("admin")
    assert ok is True
    # admin maps to panel_command (KNOWN_PANEL_COMMANDS includes admin/adminmenu).
    assert mechanism in ("panel_command", "menu_regex", "help_hook")


def test_discoverability_returns_none_for_missing_subsystem():
    """Unknown subsystem with no metadata falls to 'none'."""
    ok, mechanism = _discoverability("not_a_subsystem")
    assert ok is False
    assert mechanism == "none"
