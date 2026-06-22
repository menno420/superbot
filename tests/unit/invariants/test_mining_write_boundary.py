"""RS02 ratchet — every mining write flows through services/mining_workflow.

After the stage-1/stage-2 convergence, no file under ``disbot/views/`` or
``disbot/cogs/`` may call a mining write primitive directly; the workflow
service owns every mutation (one transaction per operation, Q-0071).
Reads (``get_*``) stay free — panels and embeds compose them directly.

AST scan modeled on ``test_inv_f_economy_service.py``: attribute calls
named like a write primitive are flagged regardless of receiver (the
names are unique to the mining DB layer).
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCANNED_DIRS = (
    _REPO_ROOT / "disbot" / "views",
    _REPO_ROOT / "disbot" / "cogs",
)

# Names unique to the mining DB layer — forbidden on ANY receiver.
_FORBIDDEN_ANY_RECEIVER = {
    "update_mining_item",
    "apply_inventory_deltas",
    "set_mining_inventory",
    "update_vault_item",
    "set_gear_wear",
    "clear_gear_wear",
    "set_last_broken",
    "set_vault_level",
    # mining-adjacent progression writers (depth records, shared game-XP,
    # skill tree) — names unique to utils/db/games/, same one-owner rule as
    # above (skill writes flow through services/skill_service.py).
    "record_depth",
    "add_game_xp",
    "set_skill_points",
    "set_structure_level",
    # title selection (Slice F) — written only through services/title_service.py.
    "set_equipped_title",
    # grid Mine (hub-redesign PR 3) — lateral position, the per-guild world seed,
    # and fog-of-war discovery, all written only through services/mining_workflow.
    "set_position",
    "set_world_seed",
    "mark_discovered",
    # energy fuel (2026-06-22) — dig spend / food restore written only through
    # services/mining_workflow (one transaction per op).
    "set_energy",
}

# Names that collide with other subsystems (``setup_session.set_depth`` is the
# setup wizard's, not mining's) — forbidden only on a DB-ish receiver.
_FORBIDDEN_DB_RECEIVER = {"set_depth", "equip_item", "unequip_slot"}

_DB_RECEIVERS = {
    "db",
    "pool",
    "mining",
    "mining_equipment",
    "mining_gear_wear",
    "mining_player_state",
}


def _receiver_leaf(node: ast.Attribute) -> str:
    rcv: ast.expr = node.value
    while isinstance(rcv, ast.Attribute):
        rcv = rcv.value if not isinstance(rcv.value, ast.Name) else rcv.value
        if isinstance(rcv, ast.Name):
            break
    # leaf = the attribute closest to the call, e.g. ``db`` in utils.db.set_depth
    leaf = node.value
    if isinstance(leaf, ast.Attribute):
        return leaf.attr
    if isinstance(leaf, ast.Name):
        return leaf.id
    return ""


def _write_calls(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(), filename=str(path))
    found: list[str] = []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        name = n.func.attr
        if name in _FORBIDDEN_ANY_RECEIVER:
            found.append(f"{name} (line {n.lineno})")
        elif name in _FORBIDDEN_DB_RECEIVER:
            if _receiver_leaf(n.func) in _DB_RECEIVERS:
                found.append(f"{name} (line {n.lineno})")
    return found


def test_no_direct_mining_writes_from_cogs_or_views():
    violations: list[tuple[str, list[str]]] = []
    for base in _SCANNED_DIRS:
        for path in sorted(base.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            calls = _write_calls(path)
            if calls:
                violations.append((str(path.relative_to(_REPO_ROOT)), calls))
    assert not violations, (
        "RS02 violation: direct mining writes outside services/mining_workflow.py "
        "(route through the workflow service — Q-0071/Q-0072):\n"
        + "\n".join(f"  {p}: {calls}" for p, calls in violations)
    )
