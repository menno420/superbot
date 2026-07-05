#!/usr/bin/env python3.10
"""Guard: merge-relevant workflows must NEVER cancel an in-progress head run.

PROVENANCE / RELIABILITY (2026-07-05, CI-setup redesign PR #1737 — decision G4 /
``docs/planning/ci-setup-redesign-2026-07-05.md`` §C.3 Mode 3):
    The cancellation race (#1275 / #1195): under the born-red flow's rapid event burst
    (open → push → push within ~2 min), a ``concurrency`` group with
    ``cancel-in-progress: true`` RACES and drops the run for the *head* commit, leaving
    the PR with no passing required check → native auto-merge stalls forever. ``code-quality.yml``
    was fixed to ``cancel-in-progress: false`` for exactly this. But that invariant lives only
    in a comment: a *future* merge-relevant workflow (or a Dependabot/edit regression) can ship
    ``cancel: true`` — or the expression form ``${{ github.ref != 'refs/heads/main' }}`` that
    ``codeql.yml`` carries today, which cancels on PR refs — and silently re-open the race. A
    warn-only note can't PREVENT that; this checker enforces it.

    THE RULE: for every workflow whose runs feed a required merge check (the ``MERGE_RELEVANT``
    set below), ``concurrency.cancel-in-progress`` must be **absent** (GitHub defaults it to
    ``false``) or the literal ``false``. Any ``true`` or ``${{ ... }}`` expression is a finding,
    because on a PR ref it can cancel the head run the required check depends on. ``cancel:false``
    guarantees the *head* run completes (a third rapid push may still cancel the *pending middle*
    run — that is safe only because ``ci-gate`` keys on the final head SHA and treats ``cancelled``
    as failure; §C.3 Mode 3 documents the pairing).

    UNVERIFIED (Q-0105) — ``MERGE_RELEVANT`` is a hardcoded list, not inferred from triggers
    ("is a workflow merge-relevant?" is not readable from YAML alone). It is drift-prone by design
    (update it when the required-check topology changes) but honest. Deterministic regex parse,
    ~0 false positives. **Delete this script if it ever misfires.** It intentionally FLAGS
    ``codeql.yml`` today (its ``cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}`` is the
    A1 tell — flip it to ``false`` before CodeQL becomes a required gate; see the redesign doc).

Stdlib-only. Exit 0 = all merge-relevant workflows safe; exit 1 = a finding.

Run:  python3.10 scripts/check_workflow_concurrency.py
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"

# Workflow file *stems* whose runs feed a required merge check now or in the target design
# (docs/planning/ci-setup-redesign-2026-07-05.md). Kill-switch list per Q-0105 — keep it in sync
# with the required-check topology; do not infer from triggers.
MERGE_RELEVANT: frozenset[str] = frozenset(
    {
        "code-quality",  # today's required gate
        "ci",  # target aggregate required context (ci-gate lives here)
        "_python-quality",  # target reusable python leg (feeds ci-gate)
        "web-ci",  # target reusable web leg (feeds ci-gate)
        "codeql",  # becomes gating via the merge-protection ruleset (needs the A1 flip first)
    },
)

# ``cancel-in-progress:`` appears only inside a ``concurrency:`` block, so a line match is safe.
# Capture the value up to an optional trailing comment.
_CANCEL = re.compile(r"^\s*cancel-in-progress:\s*(.+?)\s*(?:#.*)?$", re.MULTILINE)


def _cancel_values(text: str) -> list[str]:
    """Every ``cancel-in-progress:`` value in a workflow file (raw, comment-stripped)."""
    return [m.group(1).strip() for m in _CANCEL.finditer(text)]


def _is_safe(value: str) -> bool:
    """Safe iff the value is the literal ``false`` (case-insensitive).

    ``true`` or any ``${{ ... }}`` expression can cancel the head run on a PR ref → unsafe.
    """
    return value.strip().strip("'\"").lower() == "false"


def check(workflows: dict[str, str]) -> list[str]:
    """Return human-readable findings (empty == all merge-relevant workflows safe).

    ``workflows`` maps a workflow filename (e.g. ``"codeql.yml"``) to its text — injected so the
    logic is unit-testable without touching disk. A merge-relevant workflow is a finding when it
    declares a ``cancel-in-progress`` value that is not the literal ``false``.
    """
    problems: list[str] = []
    for filename in sorted(workflows):
        stem = filename.rsplit(".", 1)[0]
        if stem not in MERGE_RELEVANT:
            continue
        for value in _cancel_values(workflows[filename]):
            if not _is_safe(value):
                problems.append(
                    f"{filename}: merge-relevant workflow has "
                    f"cancel-in-progress: {value!r} — must be `false` (or absent). On a PR ref this "
                    f"can cancel the head run the required check depends on (the #1275 race).",
                )
    return problems


def load_workflows(directory: Path = WORKFLOWS_DIR) -> dict[str, str]:
    """Read every ``*.yml`` / ``*.yaml`` in *directory* → {filename: text}."""
    out: dict[str, str] = {}
    for path in sorted(directory.glob("*.y*ml")):
        out[path.name] = path.read_text(encoding="utf-8")
    return out


def main() -> int:
    if not WORKFLOWS_DIR.is_dir():
        print(f"check_workflow_concurrency: SKIP — no {WORKFLOWS_DIR} directory.")
        return 0
    problems = check(load_workflows())
    if problems:
        print(
            "Merge-relevant workflow(s) can cancel a head run (the #1275 cancellation race):",
        )
        for p in problems:
            print(f"  ✗ {p}")
        print(
            "\nFix: set `cancel-in-progress: false` (or remove the key — GitHub defaults it to "
            "false) on every merge-relevant workflow. See docs/planning/ci-setup-redesign-2026-07-05.md "
            "§C.3 Mode 3.",
        )
        return 1
    print(
        "✓ all merge-relevant workflows use cancel-in-progress: false (no head-run cancellation)",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
