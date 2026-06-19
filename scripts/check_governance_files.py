#!/usr/bin/env python3.10
"""Governance-files presence + path-freshness guard for SuperBot's root docs.

Why this exists (provenance + reliability header — Q-0105)
----------------------------------------------------------
Added 2026-06-19 from the idea
``docs/ideas/governance-files-presence-guard-2026-06-19.md`` (Fleet B1). The
2026-06-19 governance/supply-chain baseline session added the standard
outward-facing governance files (``LICENSE``, ``SECURITY.md``, ``CONTRIBUTING.md``,
``CITATION.cff``) and a human contributor on-ramp. They are *prose*, so nothing
stops a later refactor from silently deleting one, or letting ``CONTRIBUTING.md``'s
instructions rot — it cites ``scripts/check_quality.py --full``,
``scripts/setup_dev_env.sh``, and the binding-contract paths; if any of those move,
the onboarding doc lies and the *first thing a new contributor runs* fails. These
root files sit **outside** ``check_docs.py``'s ``docs/**`` scope, so its existing
link/pinned-path resolution never covers them. This guard closes that gap with the
repo's "executable verification over prose" ethos.

What it checks
--------------
  1. **presence** — ``LICENSE``, ``SECURITY.md``, ``CONTRIBUTING.md``,
     ``CITATION.cff`` all exist at the repo root and are non-empty.
  2. **freshness** — every concrete repo path cited in backticks inside
     ``CONTRIBUTING.md`` + ``SECURITY.md`` resolves on disk (the same link
     resolution ``check_docs`` does for ``docs/**``, applied to these root files).
  3. **citation** — ``CITATION.cff`` carries the minimal CFF keys
     (``cff-version``, ``title``, ``authors``) so the citation metadata stays valid.

Pure stdlib (no third-party imports) so CI can run it on every PR — including
docs-only PRs — without installing anything. Advisory by default (exit 0);
``--strict`` for an explicit gate (e.g. ``/session-close`` or CI).

Reliability (Q-0105): **unverified** — confirm its output against ground truth a
few times across sessions before trusting it. **Delete this script if it proves
unreliable over multiple sessions** (false positives on legitimate path moves, CFF
false negatives): it is a disposable convenience guard for the governance layer,
not a load-bearing contract.

Usage:
    python3.10 scripts/check_governance_files.py            # report (always exit 0)
    python3.10 scripts/check_governance_files.py --strict   # exit 1 on any violation
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The standard outward-facing governance files this guard protects. Each must
# exist at the repo root and be non-empty.
REQUIRED_FILES = ("LICENSE", "SECURITY.md", "CONTRIBUTING.md", "CITATION.cff")

# The prose docs whose backtick path references must stay fresh (resolve on disk).
# These are *outside* check_docs.py's docs/** scope, so this is the only guard.
FRESHNESS_DOCS = ("CONTRIBUTING.md", "SECURITY.md")

# Concrete repo path inside backticks, e.g. `docs/foo.md`, `scripts/x.py`,
# `disbot/control_api.py`. Mirrors check_docs.py's `_PATH_REF_RE` but anchored on
# the directories the root governance docs actually reference. A trailing-slash
# directory reference (e.g. `disbot/`) is matched separately below.
_PATH_REF_RE = re.compile(
    r"`((?:docs|disbot|tests|scripts|architecture_rules|dashboard|\.claude|\.github)"
    r"/[\w./-]+\.(?:py|md|sql|ya?ml|txt|sh|json|toml|cfg|ini))`",
)
# A directory reference in backticks, e.g. `disbot/`, `scripts/`, `docs/`. Must
# end in a slash so we don't mistake a bare word for a path.
_DIR_REF_RE = re.compile(
    r"`((?:docs|disbot|tests|scripts|architecture_rules|dashboard|\.claude|\.github)"
    r"/[\w./-]*?/?)`",
)

# Minimal CFF keys whose absence makes the citation metadata invalid/unusable.
_REQUIRED_CFF_KEYS = ("cff-version", "title", "authors")


def check_presence() -> list[tuple[str, str]]:
    """Each required governance file must exist at the root and be non-empty."""
    violations: list[tuple[str, str]] = []
    for name in REQUIRED_FILES:
        path = REPO_ROOT / name
        if not path.exists():
            violations.append(
                (name, "missing — required governance file does not exist"),
            )
            continue
        try:
            if not path.read_text(encoding="utf-8").strip():
                violations.append(
                    (name, "empty — required governance file has no content"),
                )
        except OSError as exc:  # pragma: no cover - unreadable file is rare
            violations.append((name, f"unreadable ({exc})"))
    return violations


def _referenced_paths(text: str) -> set[str]:
    """All concrete file + directory repo-paths cited in backticks in ``text``."""
    refs: set[str] = set()
    for ref in _PATH_REF_RE.findall(text):
        if not any(ch in ref for ch in "<>*"):  # skip placeholders / globs
            refs.add(ref)
    for ref in _DIR_REF_RE.findall(text):
        # Only treat slash-terminated tokens as directory references; a path that
        # the file regex already matched (ends in a known extension) is skipped.
        if ref.endswith("/") and not any(ch in ref for ch in "<>*"):
            refs.add(ref)
    return refs


def check_freshness() -> list[tuple[str, str]]:
    """Every backtick repo-path in the freshness docs must resolve on disk."""
    violations: list[tuple[str, str]] = []
    for name in FRESHNESS_DOCS:
        path = REPO_ROOT / name
        if not path.exists():
            continue  # presence check already reports a missing doc
        text = path.read_text(encoding="utf-8")
        for ref in sorted(_referenced_paths(text)):
            if not (REPO_ROOT / ref).exists():
                violations.append((name, f"references missing path `{ref}`"))
    return violations


def check_citation() -> list[tuple[str, str]]:
    """``CITATION.cff`` must carry the minimal CFF keys (no YAML dep — stdlib only)."""
    violations: list[tuple[str, str]] = []
    path = REPO_ROOT / "CITATION.cff"
    if not path.exists():
        return violations  # presence check already reports it
    text = path.read_text(encoding="utf-8")
    # A top-level CFF key starts a line as `key:` (allowing no leading whitespace).
    present = {
        m.group(1)
        for line in text.splitlines()
        if (m := re.match(r"([A-Za-z][A-Za-z0-9_-]*):", line))
    }
    for key in _REQUIRED_CFF_KEYS:
        if key not in present:
            violations.append(("CITATION.cff", f"missing required CFF key `{key}`"))
    return violations


def collect_violations() -> list[tuple[str, str]]:
    """All governance-file violations across presence, freshness, and citation."""
    return check_presence() + check_freshness() + check_citation()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Governance-files presence + path-freshness guard.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any governance file is missing/empty or a cited path is stale",
    )
    args = parser.parse_args(argv)

    violations = collect_violations()
    if not violations:
        files = ", ".join(REQUIRED_FILES)
        print(
            f"check_governance_files: all present, cited paths fresh, CFF valid ✓ "
            f"({files})",
        )
        return 0

    print("check_governance_files: governance-file issues found:")
    for where, problem in violations:
        print(f"  - {where}: {problem}")
    print(
        "\nFix: restore the missing/empty file, or update the stale backtick path so "
        "the contributor on-ramp does not lie. (Q-0105 unverified guard — delete this "
        "script if it proves unreliable over multiple sessions.)",
    )
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
