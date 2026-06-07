#!/usr/bin/env python3
"""Doc-hygiene checker for SuperBot ``docs/``.

Hard rules (CI gate — see ``--strict``):

  1. **badge**  — every ``docs/**/*.md`` carries a machine-readable
     ``> **Status:** `<token>``` line in its first 12 lines, with ``<token>`` from
     the allowed taxonomy. ADRs (``docs/decisions/NNN-*.md``) are exempt: they use
     their own ``**Status:** Accepted/Superseded`` convention and are inherently
     binding.
  2. **link**   — every *relative* markdown link ``[text](path)`` inside ``docs/``
     resolves to an existing file/dir (external/anchor-only links are skipped).
  3. **pinned** — every concrete repo path referenced in backticks inside the
     read-path docs (``AGENT_ORIENTATION`` / ``current-state`` / ``repo-navigation-map``)
     exists, so the canonical read path never points at a moved/renamed file.

Pure stdlib (no third-party imports) so CI can run it on every PR — including
docs-only PRs — without installing anything.

Usage:
    python scripts/check_docs.py            # report mode (always exit 0)
    python scripts/check_docs.py --strict   # exit 1 if any violation
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / "docs"

# Keep in sync with the "Status badges" list in docs/AGENT_ORIENTATION.md.
ALLOWED_BADGES = frozenset(
    {
        "binding",
        "living-ledger",
        "reference",
        "plan",
        "historical",
        "audit",
        "owner-guidance",
        "ideas",
        "archive",
    },
)

# The machine-readable badge: `> **Status:** `<token>`` (rich text may follow).
_BADGE_RE = re.compile(r"\*\*Status:\*\*\s*`([a-z-]+)`")
# ADR filename: NNN-something.md
_ADR_RE = re.compile(r"^\d+-.*\.md$")
# Markdown link target: [text](target)
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# Concrete repo path inside backticks, e.g. `docs/foo.md`, `disbot/x.py`.
_PATH_REF_RE = re.compile(
    r"`((?:docs|disbot|tests|scripts|architecture_rules|\.claude|\.github)"
    r"/[\w./-]+\.(?:py|md|sql|ya?ml|txt|sh|json|toml|cfg|ini))`",
)
_READPATH_DOCS = ("AGENT_ORIENTATION.md", "current-state.md", "repo-navigation-map.md")


def _docs_files() -> list[Path]:
    return sorted(DOCS_ROOT.rglob("*.md"))


def _is_adr(path: Path) -> bool:
    return path.parent.name == "decisions" and bool(_ADR_RE.match(path.name))


def check_badges() -> list[tuple[Path, str, str]]:
    """Every doc (non-ADR) must declare a valid Status badge."""
    violations: list[tuple[Path, str, str]] = []
    for f in _docs_files():
        if _is_adr(f):
            continue
        rel = f.relative_to(REPO_ROOT)
        head = "\n".join(f.read_text(encoding="utf-8").splitlines()[:12])
        match = _BADGE_RE.search(head)
        if match is None:
            violations.append(
                (rel, "badge", "missing `> **Status:** `<token>`` in first 12 lines"),
            )
        elif match.group(1) not in ALLOWED_BADGES:
            violations.append(
                (
                    rel,
                    "badge",
                    f"invalid badge token `{match.group(1)}` "
                    f"(allowed: {', '.join(sorted(ALLOWED_BADGES))})",
                ),
            )
    return violations


def _link_target(raw: str) -> str:
    """Normalise a markdown link target to a bare path (drop title, <>, anchor)."""
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1:].split(">", 1)[0]
    target = target.split()[0] if target.split() else target  # drop "title"
    return target.split("#", 1)[0]  # drop anchor


def check_links() -> list[tuple[Path, str, str]]:
    """Relative markdown links inside docs/ must resolve."""
    violations: list[tuple[Path, str, str]] = []
    for f in _docs_files():
        rel = f.relative_to(REPO_ROOT)
        for lineno, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for raw in _MD_LINK_RE.findall(line):
                if raw.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = _link_target(raw)
                if not target or target.startswith(("http", "mailto:")):
                    continue
                if not (f.parent / target).resolve().exists():
                    violations.append((rel, "link", f"L{lineno}: dead link -> {raw}"))
    return violations


def check_pinned() -> list[tuple[Path, str, str]]:
    """Concrete repo paths cited in the read-path docs must exist."""
    violations: list[tuple[Path, str, str]] = []
    for name in _READPATH_DOCS:
        f = DOCS_ROOT / name
        if not f.exists():
            continue
        rel = f.relative_to(REPO_ROOT)
        text = f.read_text(encoding="utf-8")
        for ref in sorted(set(_PATH_REF_RE.findall(text))):
            if any(ch in ref for ch in "<>*"):
                continue  # placeholder / glob, not a concrete path
            if not (REPO_ROOT / ref).exists():
                violations.append((rel, "pinned", f"references missing path `{ref}`"))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SuperBot doc-hygiene checker.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any violation (CI gate); default reports and exits 0",
    )
    args = parser.parse_args(argv)

    violations = check_badges() + check_links() + check_pinned()
    if not violations:
        print("check_docs: all checks passed ✓")
        return 0

    by_kind: dict[str, list[tuple[Path, str]]] = {}
    for rel, kind, msg in violations:
        by_kind.setdefault(kind, []).append((rel, msg))

    print(f"\ncheck_docs — {len(violations)} issue(s)\n")
    print("  by check: " + ", ".join(f"{k}={len(by_kind[k])}" for k in sorted(by_kind)))
    print()
    for kind in sorted(by_kind):
        print(f"[{kind}]")
        for rel, msg in sorted(by_kind[kind], key=lambda x: str(x[0])):
            print(f"  {rel}: {msg}")
        print()

    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
