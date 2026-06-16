#!/usr/bin/env python3.10
"""Scan the subsystem registry into a tier→visibility access map (stdlib, read-only).

The developer dashboard (``docs/planning/developer-dashboard-plan.md``) wants to
show **who can see what**: the bot's visibility-tier ladder and, for each tier,
the subsystems that first become discoverable there. That is exactly what
``disbot/utils/visibility_rules.py`` computes at runtime
(``get_subsystems_for_tier``) over ``disbot/utils/subsystem_registry.py``.

This scanner is a **faithful static mirror** of that rule, so the dashboard can
render the access map without importing ``disbot`` (the decoupling contract):

* The tier ladder + each tier's Discord-permission gate mirror
  ``visibility_rules.VISIBILITY_TIERS`` / ``TIER_DISCORD_PERMISSION``.
* A subsystem is user-facing iff ``visibility_mode != "internal"`` and not
  ``hidden`` (the two exclusions ``get_subsystems_for_tier`` applies).
* A subsystem first appears at the tier named by its ``visibility_tier``
  (default ``user``); a member at a higher tier sees everything at or below
  their tier (cumulative) — the page states this.

**Visibility is not execution** (the same caveat the bot module carries): this
map is UI/Help discoverability, never permission to run a command.

Emits::

    {
        "tiers": [
            {"tier": "user", "discord_permission": null, "subsystems": [
                {"key": "...", "display_name": "...", "category": "...",
                 "emoji": "..."}, ...]},
            ...
        ],
        "total_visible": 42,
        "internal_count": 7,
    }

Pure stdlib so it runs in CI, mirroring ``scripts/scan_env_usage.py`` /
``scripts/scan_commands.py`` (which ``scripts/export_dashboard_data.py`` embeds
in ``dashboard/data/dashboard.json``).

Run standalone::

    python3.10 scripts/scan_access.py            # human-readable summary
    python3.10 scripts/scan_access.py --json     # the raw JSON payload

Reliability (Q-0105): **unverified** — confirm the map against
``utils/visibility_rules.get_subsystems_for_tier`` a few times across sessions
before trusting it (it mirrors that rule by hand), and delete this seam if it
proves unreliable. Convenience generator, not load-bearing runtime code.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REGISTRY = REPO_ROOT / "disbot" / "utils" / "subsystem_registry.py"

# Mirrors disbot/utils/visibility_rules.py — keep in sync if the ladder changes.
VISIBILITY_TIERS: list[str] = [
    "user",
    "trusted",
    "staff",
    "moderator",
    "administrator",
    "owner",
]
TIER_DISCORD_PERMISSION: dict[str, str | None] = {
    "user": None,
    "trusted": None,
    "staff": "manage_guild",
    "moderator": "moderate_members",
    "administrator": "administrator",
    "owner": None,
}


def _literal(node: ast.AST) -> object:
    """Best-effort literal value of an AST node, or None for non-literals."""
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        return None


def _find_subsystems_dict(tree: ast.AST) -> ast.Dict | None:
    """Locate the ``SUBSYSTEMS = {...}`` dict node (Assign or AnnAssign)."""
    for node in ast.walk(tree):
        target = None
        if isinstance(node, ast.Assign):
            target = next((t for t in node.targets if isinstance(t, ast.Name)), None)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            target = node.target
        if target is not None and target.id == "SUBSYSTEMS":
            if isinstance(node.value, ast.Dict):
                return node.value
    return None


def _subsystem_field(value: ast.Dict, field: str) -> object:
    """Read one literal field from a subsystem's AST dict node, or None."""
    for key_node, val_node in zip(value.keys, value.values, strict=False):
        if key_node is not None and _literal(key_node) == field:
            return _literal(val_node)
    return None


def _tier_or_user(tier: object) -> str:
    """Normalise a registry ``visibility_tier`` onto the known ladder.

    Mirrors ``visibility_rules._TIER_INDEX.get(tier, 0)``: an unknown/missing
    tier sorts as the floor (``user``) so it is never accidentally hidden.
    """
    return tier if isinstance(tier, str) and tier in VISIBILITY_TIERS else "user"


def scan_access(registry: Path = DEFAULT_REGISTRY) -> dict:
    """Build the tier→visibility access map from the subsystem registry."""
    by_tier: dict[str, list[dict]] = {tier: [] for tier in VISIBILITY_TIERS}
    total_visible = 0
    internal_count = 0

    try:
        tree = ast.parse(registry.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        tree = None
    subsystems = _find_subsystems_dict(tree) if tree is not None else None

    if subsystems is not None:
        for key_node, val_node in zip(subsystems.keys, subsystems.values, strict=False):
            key = _literal(key_node) if key_node is not None else None
            if not isinstance(key, str) or not isinstance(val_node, ast.Dict):
                continue
            mode = _subsystem_field(val_node, "visibility_mode") or "normal"
            hidden = bool(_subsystem_field(val_node, "hidden"))
            # The two exclusions get_subsystems_for_tier applies.
            if mode == "internal" or hidden:
                internal_count += 1
                continue
            tier = _tier_or_user(_subsystem_field(val_node, "visibility_tier"))
            by_tier[tier].append(
                {
                    "key": key,
                    "display_name": _subsystem_field(val_node, "display_name") or key,
                    "category": _subsystem_field(val_node, "category") or "other",
                    "emoji": _subsystem_field(val_node, "emoji") or "",
                },
            )
            total_visible += 1

    for entries in by_tier.values():
        entries.sort(key=lambda e: (e["category"], e["display_name"]))

    return {
        "tiers": [
            {
                "tier": tier,
                "discord_permission": TIER_DISCORD_PERMISSION.get(tier),
                "subsystems": by_tier[tier],
            }
            for tier in VISIBILITY_TIERS
        ],
        "total_visible": total_visible,
        "internal_count": internal_count,
    }


def _format_summary(access: dict) -> str:
    """Render a short human-readable access map for the CLI."""
    lines = [
        f"{access['total_visible']} user-facing subsystem(s) across "
        f"{len(access['tiers'])} tiers "
        f"({access['internal_count']} internal/hidden excluded):\n",
    ]
    cumulative = 0
    for entry in access["tiers"]:
        cumulative += len(entry["subsystems"])
        perm = entry["discord_permission"] or "—"
        lines.append(
            f"  {entry['tier']:<14} (needs: {perm}) "
            f"+{len(entry['subsystems'])} new · {cumulative} visible",
        )
        for sub in entry["subsystems"]:
            lines.append(
                f"      {sub['emoji']} {sub['display_name']} ({sub['category']})",
            )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: print the access map (summary / JSON)."""
    parser = argparse.ArgumentParser(
        description="Mirror visibility_rules into a tier->subsystem access map.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the raw JSON payload instead of the human summary",
    )
    args = parser.parse_args(argv)

    access = scan_access()
    if args.json:
        print(json.dumps(access, indent=2, ensure_ascii=False))
    else:
        print(_format_summary(access))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
