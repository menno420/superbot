#!/usr/bin/env python3.10
"""new_subsystem.py — scaffold + verify the ~8 subsystem registration touch-points.

Provenance: custom repo tooling (CLAUDE.md tooling rule), built 2026-06-09 for
owner decision **Q-0025** (first consumer: registering Community Spotlight,
Q-0044). It encodes the verified touch-point list from
``docs/planning/multi-lane-execution-plan-2026-06-09.md`` Lane 1; if the
integration standard grows a touch-point, extend ``build_checks`` here and
``docs/building-roadmap/command-integration-standard.md`` together.

Adding a hub child/subsystem requires ~8 coordinated edits with no automation.
This tool makes the list executable:

* ``check``    — verify every touch-point for a subsystem key; exit 1 on gaps.
* ``scaffold`` — print ready-to-paste snippets for each *missing* touch-point
  (registry entry, panel-command tuple, help hook, doc rows). It deliberately
  edits nothing: the snippets are pasted by a human/agent, then ``check`` is
  re-run until green — generation is guessable, verification is not.

Usage::

    python3.10 scripts/new_subsystem.py check    --key community_spotlight \
        --cog CommunitySpotlightCog --panel-command spotlight
    python3.10 scripts/new_subsystem.py scaffold --key community_spotlight \
        --cog CommunitySpotlightCog --panel-command spotlight --parent-hub community

The four enumeration test files printed at the end are the post-edit verify
step — run them (or the full CI mirror) after applying snippets.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DISBOT = REPO_ROOT / "disbot"

SURFACE_MAP = REPO_ROOT / "docs" / "help-command-surface-map.md"
COMMAND_MAP = (
    REPO_ROOT / "docs" / "setup-platform" / "settings-customization-command-map.md"
)
NAV_MAP = REPO_ROOT / "docs" / "repo-navigation-map.md"

# The post-edit verification set (touch-point 8): the enumeration tests that
# pin registry ↔ docs ↔ source agreement.
ENUMERATION_TESTS = (
    "tests/unit/utils/test_subsystem_registry.py",
    "tests/unit/docs/test_help_surface_map_doc.py",
    "tests/unit/docs/test_settings_customization_doc.py",
    "tests/unit/services/test_customization_catalogue.py",
)


@dataclass(frozen=True)
class Check:
    """One touch-point verdict."""

    name: str
    ok: bool
    detail: str
    snippet: str = ""  # paste-ready fix, shown by `scaffold` when not ok


def _import_registry():
    """Import the live registry (strong check — no duplicated key math)."""
    sys.path.insert(0, str(DISBOT))
    from utils import hub_registry, subsystem_registry  # noqa: PLC0415

    return subsystem_registry, hub_registry


def _derive_key(cog_class: str) -> str:
    """CamelCaseCog → snake_case key, using the ledger's own regexes.

    ``cog_name_to_subsystem`` returns None for *unregistered* keys, so the
    pre-registration check needs the raw derivation; reusing the ledger's
    compiled patterns keeps the math from drifting.
    """
    from core.runtime import command_surface_ledger as ledger  # noqa: PLC0415

    stripped = ledger._COG_SUFFIX_RE.sub("", cog_class)
    snaked = ledger._CAMEL_HEAD_RE.sub(r"\1_\2", stripped)
    return ledger._CAMEL_TAIL_RE.sub(r"\1_\2", snaked).lower()


def _find_cog_file(cog_class: str) -> Path | None:
    for path in sorted((DISBOT / "cogs").rglob("*.py")):
        try:
            if f"class {cog_class}(" in path.read_text(encoding="utf-8"):
                return path
        except (OSError, UnicodeDecodeError):
            continue
    return None


def _registry_snippet(key: str, panel_command: str, parent_hub: str | None) -> str:
    parent = f'\n        "parent_hub": "{parent_hub}",' if parent_hub else ""
    return f"""    "{key}": {{
        "display_name": "<Display Name>",
        "description": "<one line>",
        "emoji": "🌟",
        "color": GENERAL_COLOR.value,
        "visibility_tier": "user",
        "visibility_mode": "normal",
        "category": "community",
        "tags": ["<tag>"],
        "entry_points": ["{panel_command}"],
        "default_channels": ["general", "bot-commands"],
        "related_subsystems": [],
        "dependencies": [],
        "soft_dependencies": [],
        "supports_dm": False,
        "has_cleanup_rules": False,
        "ui_priority": 30,{parent}
        "capabilities": [
            "{key}.<resource>.<action>",
        ],
    }},"""


def _hook_snippet(view_hint: str) -> str:
    return f'''    async def build_help_menu_view(
        self,
        interaction: discord.Interaction,
    ) -> tuple[discord.Embed, discord.ui.View]:
        """Help/hub direct-navigation hook (returns this subsystem's panel)."""
        if interaction.guild is None:
            return (
                discord.Embed(description="Only available inside a server."),
                discord.ui.View(),
            )
        embed = await <build_embed>(interaction.guild)
        view = {view_hint}(interaction.guild, interaction.user)
        return embed, view'''


def build_checks(
    key: str,
    cog_class: str,
    panel_command: str,
    parent_hub: str | None,
) -> list[Check]:
    """Evaluate every registration touch-point for *key*."""
    subsystem_registry, hub_registry = _import_registry()
    subsystems = subsystem_registry.SUBSYSTEMS
    checks: list[Check] = []

    # 1. SUBSYSTEMS entry, with the Q-0026 key↔cog identity law.
    expected_key = _derive_key(cog_class)
    if key != expected_key:
        checks.append(
            Check(
                "key-identity",
                False,
                f"key {key!r} != cog_name_to_subsystem({cog_class!r}) = "
                f"{expected_key!r} — pick the derived key (Q-0026)",
            ),
        )
    else:
        checks.append(Check("key-identity", True, f"{cog_class} → {key}"))
    entry = subsystems.get(key)
    checks.append(
        Check(
            "registry-entry",
            entry is not None,
            (
                "SUBSYSTEMS has the entry"
                if entry
                else f"no SUBSYSTEMS[{key!r}] in utils/subsystem_registry.py"
            ),
            _registry_snippet(key, panel_command, parent_hub),
        ),
    )

    # 2. Hub linkage: parent_hub points at a real hub (child path), or the
    #    key itself is a registered hub (new-hub path).
    if parent_hub:
        hub = hub_registry.get_hub(parent_hub)
        declared = (entry or {}).get("parent_hub") == parent_hub
        checks.append(
            Check(
                "hub-linkage",
                hub is not None and (entry is None or declared),
                (
                    f"parent_hub={parent_hub!r} "
                    f"({'known hub' if hub else 'NOT a registered hub'}; "
                    f"{'declared on entry' if declared else 'entry missing/undeclared'})"
                ),
                f'    "parent_hub": "{parent_hub}",  # inside SUBSYSTEMS["{key}"]',
            ),
        )
        # 2b. The hub's HubEntry must ALSO declare the child in
        #     primary_children — test_every_hub_primary_children_match_
        #     parent_hub_filter pins the two lists equal. (Touch-point
        #     discovered registering Community Spotlight, 2026-06-09.)
        in_primary = hub is not None and key in hub.primary_children
        checks.append(
            Check(
                "hub-primary-children",
                entry is None or in_primary,
                (
                    f"HUBS[{parent_hub!r}].primary_children "
                    f"{'includes' if in_primary else 'missing'} {key!r}"
                ),
                f'    "{key}",  # inside HUBS {parent_hub!r} primary_children',
            ),
        )

    # 3. KNOWN_PANEL_COMMANDS row.
    catalogue = (DISBOT / "services" / "customization_catalogue.py").read_text(
        encoding="utf-8",
    )
    pair = f'("{key}", "{panel_command}")'
    checks.append(
        Check(
            "panel-command",
            pair in catalogue,
            f"KNOWN_PANEL_COMMANDS {'has' if pair in catalogue else 'missing'} {pair}",
            f"    {pair},  # keep the tuple alphabetical by subsystem",
        ),
    )

    # 4. Cog: class exists, setup() present, help hook adopted.
    cog_file = _find_cog_file(cog_class)
    if cog_file is None:
        checks.append(Check("cog-file", False, f"no cogs/*.py defines {cog_class}"))
        cog_src = ""
    else:
        cog_src = cog_file.read_text(encoding="utf-8")
        checks.append(Check("cog-file", True, str(cog_file.relative_to(REPO_ROOT))))
        checks.append(
            Check(
                "cog-setup",
                "async def setup(" in cog_src,
                "extension setup() hook",
            ),
        )
    view_hint = "<PanelView>"
    match = re.search(r"class (\w+View)\(", cog_src)
    if match:
        view_hint = match.group(1)
    checks.append(
        Check(
            "help-hook",
            "def build_help_menu_view(" in cog_src,
            "build_help_menu_view (Help dropdown + hub child routing call it)",
            _hook_snippet(view_hint),
        ),
    )

    # 5–7. Doc rows.
    surface = SURFACE_MAP.read_text(encoding="utf-8")
    checks.append(
        Check(
            "surface-map-row",
            f"| `{key}` |" in surface,
            "docs/help-command-surface-map.md §2 row",
            f"| `{key}` | `<cog file>` | `{panel_command}` | <other commands> | "
            f"`<PanelView>` | `!help <name>` → opens panel (shared resolver) | "
            f'reached via <hub> (`parent_hub="{parent_hub}"`) | hub child |',
        ),
    )
    command_map = COMMAND_MAP.read_text(encoding="utf-8")
    checks.append(
        Check(
            "command-map-section",
            f"### {key}" in command_map,
            "settings-customization-command-map.md ### section",
            f"### {key}\n\n<fill the 24-field template>",
        ),
    )
    nav = NAV_MAP.read_text(encoding="utf-8")
    checks.append(
        Check(
            "navigation-map-row",
            key in nav,
            "docs/repo-navigation-map.md mention",
            f"| {key} | `cogs/...` | `views/...` | <data path> | <db owner> |",
        ),
    )
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("mode", choices=("check", "scaffold"))
    parser.add_argument("--key", required=True, help="subsystem key (snake_case)")
    parser.add_argument("--cog", required=True, help="cog class name")
    parser.add_argument("--panel-command", required=True, help="panel entry command")
    parser.add_argument("--parent-hub", default=None, help="hub this child belongs to")
    args = parser.parse_args(argv)

    checks = build_checks(args.key, args.cog, args.panel_command, args.parent_hub)
    missing = [c for c in checks if not c.ok]

    for c in checks:
        print(f"  [{'OK' if c.ok else 'MISSING'}] {c.name:<20} {c.detail}")

    if args.mode == "scaffold" and missing:
        # Extend-before-mint reminder (family-plan §3.7 rubric, surfaced 2026-06-13).
        # The cascade below is the cost of a NEW subsystem; the cheaper move is often
        # to extend an existing one. Ask this BEFORE pasting any boilerplate.
        print(
            "\n⚠ extend-before-mint: does this feature EXTEND an existing subsystem's\n"
            "  domain? If so, add settings/bindings to that subsystem's schema (no\n"
            "  pinned-surface cascade) instead of minting a new one. Mint only when the\n"
            "  feature has its own identity/pipeline/lifecycle. (server-logging extended\n"
            "  `logging` = 0 cascade; automod/welcome/counters genuinely needed new ones.)",
        )
        print("\n── paste-ready snippets for the missing touch-points ──")
        for c in missing:
            if c.snippet:
                print(f"\n# {c.name}\n{c.snippet}")

    print("\nVerify after edits (the enumeration tests):")
    print(f"  python3.10 -m pytest {' '.join(ENUMERATION_TESTS)} -q")
    if missing:
        print(f"\n{len(missing)} touch-point(s) missing.")
        return 1
    print("\nAll touch-points present ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
