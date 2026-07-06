#!/usr/bin/env python3
"""Extension-type taxonomy crosswalk for SuperBot.

Joins three sources of truth into one browsable crosswalk that answers, for every
loaded Discord extension: what *role* it plays, whether it is a registered
subsystem, and (if not) which subsystem it backs.

Sources
-------
1. ``disbot/config.py``                  — ``INITIAL_EXTENSIONS`` (the live manifest)
2. ``disbot/utils/subsystem_registry.py``— ``SUBSYSTEMS`` (registered identities)
3. ``architecture_rules/extension_roles.yaml`` — the curated editorial role overlay

The first two are read by **AST** (no import, no env, no bot startup) so this runs
identically in CI and locally. The overlay is the only hand-edited input.

Why a crosswalk: SuperBot loads 43 extensions but registers 33 subsystems; the 10
non-1:1 extensions (bootstrap / maintenance loops / BTD6 sub-surfaces / the Hermes
adapter) are a *classification*, not a gap. See
``docs/ideas/architecture-atlas-and-structure-review-2026-06-16.md`` (Q-0151c).

Modes
-----
    python3.10 scripts/extension_crosswalk.py            # print the crosswalk (preview)
    python3.10 scripts/extension_crosswalk.py --write    # (re)generate the doc
    python3.10 scripts/extension_crosswalk.py --check     # CI guard (exit 1 on drift)

``--check`` fails when: an extension is unclassified, the overlay names a stranger,
a role/backs value is invalid, a registered subsystem has no backing extension, or
the committed doc is stale. ``tests/unit/scripts/test_extension_crosswalk.py`` runs
``--check`` so the suite enforces it (no workflow edit needed).

RELIABILITY / PROVENANCE (Q-0105): added 2026-06-16. Read-only, stdlib + yaml,
disposable. If it proves more nuisance than help across a few sessions, delete this
script, ``architecture_rules/extension_roles.yaml``, the generated doc, and the test
together — nothing in the bot runtime depends on it.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PY = REPO_ROOT / "disbot" / "config.py"
REGISTRY_PY = REPO_ROOT / "disbot" / "utils" / "subsystem_registry.py"
OVERLAY_YAML = REPO_ROOT / "architecture_rules" / "extension_roles.yaml"
GENERATED_DOC = REPO_ROOT / "docs" / "architecture" / "extension-taxonomy-crosswalk.md"

# Bump when the rendered layout changes (so a stale committed doc is detected).
GENERATOR_VERSION = "v1"

_NOT_SOURCE_OF_TRUTH = (
    "> **Status:** `living-ledger` — **GENERATED — NOT SOURCE OF TRUTH.** Do not edit "
    "by hand.\n"
    "> Regenerate with `python3.10 scripts/extension_crosswalk.py --write` after editing\n"
    "> `architecture_rules/extension_roles.yaml`. Sources: `disbot/config.py` "
    "(`INITIAL_EXTENSIONS`),\n"
    "> `disbot/utils/subsystem_registry.py` (`SUBSYSTEMS`), and that overlay. "
    "`--check` guards staleness."
)


# ---------------------------------------------------------------------------
# AST extraction (no imports — safe in CI, no env / bot startup)
# ---------------------------------------------------------------------------


def _find_assignment(tree: ast.Module, name: str) -> ast.expr:
    """Return the value node assigned to ``name`` at module level (Assign/AnnAssign)."""
    for node in tree.body:
        targets = (
            node.targets
            if isinstance(node, ast.Assign)
            else [node.target]
            if isinstance(node, ast.AnnAssign)
            else []
        )
        for tgt in targets:
            if isinstance(tgt, ast.Name) and tgt.id == name and node.value is not None:
                return node.value
    raise ValueError(f"could not find module-level assignment to {name!r}")


def _str_constants(node: ast.expr) -> list[str]:
    return [el.value for el in node.elts if isinstance(el, ast.Constant)]  # type: ignore[attr-defined]


def initial_extensions() -> list[str]:
    """Short names (``cogs.x_cog`` -> ``x``) in load order, from config.py."""
    tree = ast.parse(CONFIG_PY.read_text(encoding="utf-8"))
    raw = _str_constants(_find_assignment(tree, "INITIAL_EXTENSIONS"))
    return [m.split(".")[-1].removesuffix("_cog") for m in raw]


def subsystem_keys() -> set[str]:
    """The registered subsystem identities, from subsystem_registry.py."""
    tree = ast.parse(REGISTRY_PY.read_text(encoding="utf-8"))
    node = _find_assignment(tree, "SUBSYSTEMS")
    if not isinstance(node, ast.Dict):
        raise ValueError("SUBSYSTEMS is not a dict literal")
    return {k.value for k in node.keys if isinstance(k, ast.Constant)}


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Row:
    extension: str
    role: str
    registered: bool
    backs: str | None
    note: str


def _load_overlay() -> dict:
    return yaml.safe_load(OVERLAY_YAML.read_text(encoding="utf-8"))


def build_rows() -> tuple[list[Row], list[str]]:
    """Return (rows in load order, validation errors)."""
    overlay = _load_overlay()
    roles = overlay.get("roles", {})
    entries = overlay.get("extensions", {})
    exts = initial_extensions()
    keys = subsystem_keys()
    errors: list[str] = []

    ext_set = set(exts)
    # 1. every extension classified · 2. no stranger overlay entries
    for missing in sorted(ext_set - set(entries)):
        errors.append(
            f"extension {missing!r} is in INITIAL_EXTENSIONS but not classified in the overlay",
        )
    for stranger in sorted(set(entries) - ext_set):
        errors.append(f"overlay entry {stranger!r} does not match any loaded extension")
    # 4. every registered subsystem has a backing extension
    for orphan in sorted(keys - ext_set):
        errors.append(
            f"registered subsystem {orphan!r} has no backing extension in INITIAL_EXTENSIONS",
        )

    rows: list[Row] = []
    for ext in exts:
        meta = entries.get(ext, {}) or {}
        role = meta.get("role", "?")
        backs = meta.get("backs") or None
        note = (meta.get("note") or "").strip()
        if ext in entries:
            # 3. role + backs validity
            if role not in roles:
                errors.append(f"extension {ext!r} has unknown role {role!r}")
            if backs is not None and backs not in keys:
                errors.append(f"extension {ext!r} backs unknown subsystem {backs!r}")
        rows.append(Row(ext, role, ext in keys, backs, note))
    return rows, errors


# ---------------------------------------------------------------------------
# Rendering (deterministic — no timestamp/SHA so the committed doc is stable)
# ---------------------------------------------------------------------------


def _cell(text: str) -> str:
    return text.replace("|", r"\|").replace("\n", " ").strip()


def render(rows: list[Row], keys: set[str]) -> str:
    by_role: dict[str, int] = {}
    for r in rows:
        by_role[r.role] = by_role.get(r.role, 0) + 1
    non_1to1 = [r.extension for r in rows if not r.registered]
    overlay = _load_overlay()
    role_desc = overlay.get("roles", {})

    out: list[str] = []
    out.append("# Extension-type taxonomy crosswalk")
    out.append("")
    out.append(_NOT_SOURCE_OF_TRUTH)
    out.append("")
    out.append(
        f"_Generator:_ `scripts/extension_crosswalk.py` `{GENERATOR_VERSION}`  ·  "
        f"**{len(rows)}** extensions  ·  **{len(keys)}** registered subsystems  ·  "
        f"**{len(non_1to1)}** non-1:1 extensions.",
    )
    out.append("")
    out.append(
        "Every loaded extension classified by **role** (editorial — in "
        "`architecture_rules/extension_roles.yaml`) and joined to the registry. A "
        "✓ in *Registered* means the extension is a 1:1 subsystem identity; the "
        "non-1:1 rows are surfaces/maintenance/adapters that **back** a subsystem or "
        "the platform.",
    )
    out.append("")

    # Role legend + counts
    out.append("## Roles")
    out.append("")
    out.append("| Role | Count | Meaning |")
    out.append("|---|---:|---|")
    for role in sorted(role_desc):
        desc = _cell(str(role_desc[role].get("description", "")))
        out.append(f"| `{role}` | {by_role.get(role, 0)} | {desc} |")
    out.append("")

    # The crosswalk, in load order
    out.append("## Crosswalk (load order)")
    out.append("")
    out.append("| # | Extension | Role | Registered | Backs | Note |")
    out.append("|---:|---|---|:--:|---|---|")
    for i, r in enumerate(rows, 1):
        reg = "✓" if r.registered else "—"
        backs = f"`{r.backs}`" if r.backs else ""
        out.append(
            f"| {i} | `{r.extension}` | `{r.role}` | {reg} | {backs} | {_cell(r.note)} |",
        )
    out.append("")

    # The non-1:1 callout (the review's "10 unclassified" — now classified)
    out.append("## Non-1:1 extensions (no registry identity)")
    out.append("")
    out.append(
        "These load as extensions but are **not** registered subsystems — they are "
        "classified by role instead of being product verticals:",
    )
    out.append("")
    for r in rows:
        if not r.registered:
            backs = f" → backs `{r.backs}`" if r.backs else ""
            note = f" — {r.note}" if r.note else ""
            out.append(f"- `{r.extension}` (`{r.role}`{backs}){note}")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def check() -> list[str]:
    """Return a list of drift/validation errors (empty == clean)."""
    rows, errors = build_rows()
    keys = subsystem_keys()
    rendered = render(rows, keys).rstrip("\n") + "\n"
    if not GENERATED_DOC.exists():
        errors.append(
            f"{GENERATED_DOC.relative_to(REPO_ROOT)} does not exist — run --write",
        )
    elif GENERATED_DOC.read_text(encoding="utf-8") != rendered:
        errors.append(
            f"{GENERATED_DOC.relative_to(REPO_ROOT)} is stale — run "
            "`python3.10 scripts/extension_crosswalk.py --write`",
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extension-type taxonomy crosswalk.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--write", action="store_true", help="(re)generate the doc.")
    group.add_argument(
        "--check",
        action="store_true",
        help="CI guard: exit 1 on drift.",
    )
    args = parser.parse_args(argv)

    if args.check:
        errors = check()
        if errors:
            print("extension_crosswalk: FAIL")
            for e in errors:
                print(f"  - {e}")
            return 1
        print("extension_crosswalk: all checks passed ✓")
        return 0

    rows, errors = build_rows()
    keys = subsystem_keys()
    rendered = render(rows, keys).rstrip("\n") + "\n"
    if args.write:
        GENERATED_DOC.write_text(rendered, encoding="utf-8")
        print(f"wrote {GENERATED_DOC.relative_to(REPO_ROOT)} ({len(rows)} extensions)")
        if errors:
            print("WARNING — overlay validation errors (fix the overlay):")
            for e in errors:
                print(f"  - {e}")
            return 1
        return 0

    # default: preview to stdout
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
