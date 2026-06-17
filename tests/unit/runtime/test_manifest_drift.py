"""AST-vs-runtime drift guard — manifest spine slice 3 (Q-0162).

The manifest spine demotes the AST scanner (``scripts/scan_commands.py``) to a
**drift-detection layer** and makes the runtime manifests the source of truth.
This guard is the cheap, CI-runnable cross-check that keeps the two honest:

    every subsystem the AST scanner sees a ``panel_action`` command in
    must own at least one registered persistent panel (PanelManifest).

It is the structural half of the ``dangling_panel_action`` reconciliation
(``manifest_reconciliation``): a ``panel_action`` command whose subsystem owns no
panel has nowhere to live. Both the AST scan and the panel manifest are cheap
(arg-free view instantiation), so this runs in unit-test CI without a live bot —
unlike the full command ledger, which needs a loaded bot.

If this fails: either a new ``panel_action`` command landed in a subsystem with no
panel (the drift the spine exists to catch), or the AST scanner / panel registry
drifted — triage against the live registry before trusting the verdict (Q-0120).
"""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

from core.runtime import panel_manifest

REPO_ROOT = Path(__file__).resolve().parents[3]

# The persistent-view modules whose import registers panels (mirrors
# test_panel_manifest._real_manifest so collection order can't hide a panel).
_PANEL_MODULES = (
    "views.ai.panel",
    "views.moderation.main_panel",
    "views.economy.main_panel",
    "views.btd6.panel",
    "views.mining.main_panel",
    "views.ux_lab.persistent_demo",
    "views.server_management.hub",
    "cogs.help.panels",
    "cogs.role_cog",
)


def _load_scan_commands():
    script = REPO_ROOT / "scripts" / "scan_commands.py"
    spec = importlib.util.spec_from_file_location("_scan_commands_drift", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.scan_commands


def _ast_panel_action_subsystems() -> dict[str, list[str]]:
    """``subsystem -> [command names]`` for every AST ``panel_action`` command."""
    scan_commands = _load_scan_commands()
    out: dict[str, list[str]] = {}
    for cog in scan_commands(repo_root=REPO_ROOT):
        for cmd in cog["commands"]:
            if cmd["classification"] == "panel_action":
                out.setdefault(cog["subsystem"], []).append(cmd["name"])
    return out


def _panel_subsystems() -> set[str]:
    for mod in _PANEL_MODULES:
        importlib.import_module(mod)
    return {p.subsystem for p in panel_manifest.build_panel_manifest().panels}


def test_every_panel_action_subsystem_owns_a_panel():
    pa = _ast_panel_action_subsystems()
    panels = _panel_subsystems()
    dangling = {sub: cmds for sub, cmds in pa.items() if sub not in panels}
    assert not dangling, (
        "panel_action commands in subsystem(s) with no registered panel "
        f"(dangling): {dangling}. Register a panel, fix the cog->subsystem join, "
        "or reclassify the command."
    )


def test_drift_guard_actually_sees_panel_actions():
    # Guards the guard: if the scanner ever stops finding any panel_action
    # command, the subset check above would pass vacuously — so assert it has
    # real data to check (Q-0120: a green that contradicts evidence is a bug).
    assert _ast_panel_action_subsystems(), "scan_commands found no panel_action commands"
