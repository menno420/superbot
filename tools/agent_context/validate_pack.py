#!/usr/bin/env python3
"""Validate docs/agent/index.yml and generated context packs.

Checks:
  1. Index YAML is well-formed and has the required structure.
  2. Every subsystem lists a folio, at least one binding doc, source roots,
     do_not_create warnings, and verification commands.
  3. Every path listed in folio + binding_docs + reference_docs exists on disk.
  4. Every path listed in source_roots exists on disk (files or directories).
  5. Every generated context pack exists in docs/agent/generated/ and carries
     the NOT-SOURCE-OF-TRUTH marker.

Usage:
    python3.10 tools/agent_context/validate_pack.py
    python3.10 tools/agent_context/validate_pack.py --fix  # re-generates stale packs

Exit code 0 = all checks pass.  Non-zero = at least one failure (details printed).

Provenance: added 2026-06-08 as part of the SuperBot Context Compiler.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = REPO_ROOT / "docs" / "agent" / "index.yml"
GENERATED_DIR = REPO_ROOT / "docs" / "agent" / "generated"
BUILD_SCRIPT = REPO_ROOT / "tools" / "agent_context" / "build_pack.py"

_REQUIRED_FIELDS = (
    "folio",
    "binding_docs",
    "source_roots",
    "do_not_create",
    "verification",
)
_NOT_SOURCE_MARKER = "NOT SOURCE OF TRUTH"


def _fail(errors: list[str], msg: str) -> None:
    errors.append(msg)
    print(f"  FAIL  {msg}")


def _ok(msg: str) -> None:
    print(f"  ok    {msg}")


def check_index_structure(subsystems: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    print("\n[1] Index structure")
    for name, sub in subsystems.items():
        for field in _REQUIRED_FIELDS:
            if not sub.get(field):
                _fail(errors, f"'{name}' is missing or empty: {field}")
        _ok(f"'{name}' has required fields")
    return errors


def check_paths(subsystems: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    print("\n[2] Path existence")
    for name, sub in subsystems.items():
        # Folio
        folio = REPO_ROOT / sub.get("folio", "")
        if not folio.exists():
            _fail(errors, f"'{name}' folio not found: {sub.get('folio')}")
        else:
            _ok(f"'{name}' folio exists")

        # Binding docs
        for doc in sub.get("binding_docs", []):
            p = REPO_ROOT / doc
            if not p.exists():
                _fail(errors, f"'{name}' binding_doc not found: {doc}")

        # Reference docs
        for doc in sub.get("reference_docs", []):
            p = REPO_ROOT / doc
            if not p.exists():
                _fail(errors, f"'{name}' reference_doc not found: {doc}")

        # Source roots
        for root in sub.get("source_roots", []):
            p = REPO_ROOT / root
            if not p.exists():
                _fail(errors, f"'{name}' source_root not found: {root}")

    return errors


def check_generated_packs(subsystems: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    print("\n[3] Generated packs")
    for name in subsystems:
        pack = GENERATED_DIR / f"{name}.context.md"
        if not pack.exists():
            _fail(
                errors,
                f"Generated pack missing: docs/agent/generated/{name}.context.md",
            )
            continue
        text = pack.read_text(encoding="utf-8")
        if _NOT_SOURCE_MARKER not in text:
            _fail(
                errors,
                f"'{name}' pack is missing the NOT-SOURCE-OF-TRUTH marker "
                f"(must contain: '{_NOT_SOURCE_MARKER}')",
            )
        else:
            _ok(f"'{name}' pack exists and is marked")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Re-run build_pack.py to regenerate missing or stale packs before validating",
    )
    args = parser.parse_args()

    if not INDEX_PATH.exists():
        print(f"ERROR: index not found at {INDEX_PATH}", file=sys.stderr)
        sys.exit(1)

    with INDEX_PATH.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict) or "subsystems" not in data:
        print(
            "ERROR: index.yml has unexpected format (missing 'subsystems' key)",
            file=sys.stderr,
        )
        sys.exit(1)

    subsystems: dict[str, Any] = data["subsystems"]
    print(
        f"Validating {len(subsystems)} subsystems in {INDEX_PATH.relative_to(REPO_ROOT)} …",
    )

    if args.fix:
        print("\n[0] Regenerating packs (--fix)")
        result = subprocess.run(
            [sys.executable, str(BUILD_SCRIPT)],
            cwd=REPO_ROOT,
        )
        if result.returncode != 0:
            print("ERROR: build_pack.py failed", file=sys.stderr)
            sys.exit(1)

    all_errors: list[str] = []
    all_errors += check_index_structure(subsystems)
    all_errors += check_paths(subsystems)
    all_errors += check_generated_packs(subsystems)

    print()
    if all_errors:
        print(f"FAILED — {len(all_errors)} error(s):")
        for e in all_errors:
            print(f"  • {e}")
        sys.exit(1)
    else:
        print("All checks passed.")


if __name__ == "__main__":
    main()
