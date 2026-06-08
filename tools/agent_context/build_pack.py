#!/usr/bin/env python3
"""SuperBot Context Compiler — generate task-specific context packs.

Reads docs/agent/index.yml and writes one markdown file per subsystem into
docs/agent/generated/.  Generated packs are read-only orientation aids for
Claude sessions; they are NOT source of truth.  Canonical docs listed in
each subsystem's binding_docs always win.

Usage:
    python3.10 tools/agent_context/build_pack.py
    python3.10 tools/agent_context/build_pack.py --subsystem ai
    python3.10 tools/agent_context/build_pack.py --dry-run

Provenance: added 2026-06-08 as part of the SuperBot Context Compiler.
Unverified against a long track record — spot-check generated output against
the source index.yml a few times before relying on it for high-stakes sessions.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = REPO_ROOT / "docs" / "agent" / "index.yml"
OUTPUT_DIR = REPO_ROOT / "docs" / "agent" / "generated"

_NOT_SOURCE_OF_TRUTH = (
    "> **NOT SOURCE OF TRUTH.** This file is generated from `docs/agent/index.yml`.\n"
    "> Canonical docs listed under *Binding docs* always win over this pack.\n"
    "> Edit the index, then re-run `python3.10 tools/agent_context/build_pack.py`."
)


def _load_index() -> dict[str, Any]:
    with INDEX_PATH.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or "subsystems" not in data:
        raise ValueError(f"Invalid index format in {INDEX_PATH}")
    return data


def _bullet_list(items: list[str], indent: int = 0) -> str:
    pad = " " * indent
    return "\n".join(f"{pad}- {item}" for item in items)


def _code_block(lines: list[str]) -> str:
    body = "\n".join(lines)
    return f"```\n{body}\n```"


def _render_pack(name: str, sub: dict[str, Any]) -> str:
    display = sub.get("display_name", name)
    today = date.today().isoformat()

    sections: list[str] = []

    # Header — status badge must appear in first 12 lines for check_docs.py
    sections.append(
        f"# Agent Context Pack — {display}\n\n"
        f"> **Status:** `reference` — generated orientation aid (NOT source of truth).\n"
        f"> Generated: {today} · Subsystem key: `{name}`",
    )
    sections.append(_NOT_SOURCE_OF_TRUTH)

    # Folio
    folio = sub.get("folio", "")
    # Use a repo-root-relative path for the link so it works in GitHub and editors.
    sections.append(
        f"## Folio (start here)\n\n"
        f"[`{folio}`](../../../{folio}) — canonical area index, debug router, "
        f"current state, next candidates.",
    )

    # Binding docs
    binding = sub.get("binding_docs", [])
    if binding:
        sections.append(
            "## Binding docs (read before editing)\n\n" + _bullet_list(binding),
        )

    # Reference docs
    reference = sub.get("reference_docs", [])
    if reference:
        sections.append(
            "## Reference docs (consult on demand)\n\n" + _bullet_list(reference),
        )

    # Source roots
    roots = sub.get("source_roots", [])
    if roots:
        sections.append("## Likely source areas\n\n" + _bullet_list(roots))

    # Related subsystems
    related = sub.get("related_subsystems", [])
    if related:
        links = [f"`docs/agent/generated/{r}.context.md`" for r in related]
        sections.append("## Related subsystems\n\n" + _bullet_list(links))

    # Do-not-create warnings
    dnc = sub.get("do_not_create", [])
    if dnc:
        items = "\n".join(f"- {d}" for d in dnc)
        sections.append(
            "## Do NOT create\n\n"
            "These systems already exist — duplicating them is the main source of\n"
            "architectural drift in this repo.\n\n" + items,
        )

    # Gates
    gates = sub.get("gates", [])
    if gates:
        items = "\n".join(f"- {g}" for g in gates)
        sections.append("## Active gates\n\n" + items)

    # Verification
    cmds = sub.get("verification", [])
    if cmds:
        sections.append(
            "## Verification commands\n\n"
            "Run these before pushing any change to this subsystem:\n\n"
            + _code_block(cmds),
        )

    # Footer reminder
    sections.append(
        "---\n\n"
        "*This pack is orientation only.  When this file and a canonical doc\n"
        "disagree, the canonical doc wins.  When this file and source code\n"
        "disagree, source code wins.*",
    )

    return "\n\n".join(sections) + "\n"


def build(subsystems: dict[str, Any], target: str | None, dry_run: bool) -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    errors = 0

    for name, sub in subsystems.items():
        if target and name != target:
            continue

        try:
            content = _render_pack(name, sub)
        except Exception as exc:
            print(f"ERROR: could not render pack for '{name}': {exc}", file=sys.stderr)
            errors += 1
            continue

        out_path = OUTPUT_DIR / f"{name}.context.md"
        if dry_run:
            print(f"[dry-run] would write {out_path.relative_to(REPO_ROOT)}")
        else:
            out_path.write_text(content, encoding="utf-8")
            print(f"  wrote {out_path.relative_to(REPO_ROOT)}")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--subsystem",
        metavar="KEY",
        help="Generate only this subsystem (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without writing",
    )
    args = parser.parse_args()

    data = _load_index()
    subsystems: dict[str, Any] = data["subsystems"]

    if args.subsystem and args.subsystem not in subsystems:
        print(
            f"ERROR: subsystem '{args.subsystem}' not in index. "
            f"Valid keys: {', '.join(subsystems)}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Building context packs from {INDEX_PATH.relative_to(REPO_ROOT)} …")
    errors = build(subsystems, args.subsystem, args.dry_run)
    if errors:
        print(f"\n{errors} error(s) — see above.", file=sys.stderr)
        sys.exit(1)
    print("Done.")


if __name__ == "__main__":
    main()
