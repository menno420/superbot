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
  4. **reachable** — every live doc is reachable by following links from a read-path
     root (the read-path docs + subsystem folios + every ``README.md`` + ``CLAUDE.md``).
     Orphans fail unless badged ``historical`` / ``archive``, an ADR, or allowlisted —
     so a doc nobody links to can't accumulate silently.
  5. **freshness** — ``current-state.md`` must not hard-code the in-flight PR in prose.
     Markers like ``(this PR, pending)`` / ``(pending PR)`` rot the moment that PR
     merges (they were left stale twice in one session). The living ledger names only
     MERGED work + the single ``▶ Next action`` pointer; in-flight status comes from
     live GitHub. This gate forbids reintroducing the rotting markers.

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
from collections import deque
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

# Rot-prone "in-flight PR named in prose" markers. current-state.md must name only
# MERGED work + the ▶ Next action line; these forms assert a transient PR status
# that becomes a false claim the instant the PR merges.
_STALE_PENDING_RE = re.compile(
    r"\(\s*pending pr\s*\)|\(\s*this pr,?\s*pending\s*\)|\bthis pr \(pending\)",
    re.IGNORECASE,
)

# A backtick-wrapped docs path, e.g. `docs/foo.md` — used to walk the doc graph
# (backtick refs are how most SuperBot docs cross-link, alongside markdown links).
_DOCS_PATH_RE = re.compile(r"`(docs/[\w./-]+\.md)`")
# Badges whose docs are retired content and need no inbound link.
_REACHABILITY_EXEMPT_BADGES = frozenset({"historical", "archive"})
# Docs intentionally islanded (repo-relative paths). Keep empty unless a doc is
# deliberately unlinked; prefer linking it from a folio/README/read-path doc.
_REACHABILITY_ALLOWLIST: frozenset[str] = frozenset()

# Soft ratchet on the *top-level* docs/ pile (docs/*.md, not subdirs). The
# friction a new session feels is the count, not any one doc — so freeze the
# top-level count at today's value and only ever lower it as plans / audits /
# historical snapshots move into a subdir (docs/archive/, docs/planning/, …).
# This is a **soft** forcing function: the census prints every run and warns on
# a breach, but it never changes the exit code (adding a genuinely top-level doc
# must not break CI). Lower this number when you trim; never raise it.
_TOP_LEVEL_DOCS_BUDGET = 41


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


def _doc_badge(path: Path) -> str | None:
    """Return the doc's Status badge token, or None."""
    head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:12])
    match = _BADGE_RE.search(head)
    return match.group(1) if match else None


def _reachability_roots() -> list[Path]:
    """Entry points a new session actually reads — the doc graph must connect here."""
    roots = [DOCS_ROOT / name for name in _READPATH_DOCS]
    roots.append(REPO_ROOT / ".claude" / "CLAUDE.md")
    roots += sorted(DOCS_ROOT.glob("subsystems/*.md"))
    roots += sorted(DOCS_ROOT.rglob("README.md"))
    return [r for r in roots if r.exists()]


def _outgoing_doc_links(path: Path) -> set[Path]:
    """Resolve every relative markdown link + backtick ``docs/*.md`` ref in a file."""
    out: set[Path] = set()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return out
    for line in text.splitlines():
        for raw in _MD_LINK_RE.findall(line):
            if raw.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = _link_target(raw)
            if target:
                out.add((path.parent / target).resolve())
        for ref in _DOCS_PATH_RE.findall(line):
            out.add((REPO_ROOT / ref).resolve())
    return out


def check_reachable() -> list[tuple[Path, str, str]]:
    """Every live doc must be reachable from a read-path root / folio / README.

    Walks the doc graph (markdown links + backtick ``docs/*.md`` refs) from the
    roots; any doc not reached — and not ``historical`` / ``archive`` badged, an
    ADR, or allowlisted — is an orphan. Turns "can a session find this?" into a gate.
    """
    seen: set[Path] = set()
    queue: deque[Path] = deque()
    for root in _reachability_roots():
        resolved = root.resolve()
        if resolved not in seen:
            seen.add(resolved)
            queue.append(resolved)
    while queue:
        cur = queue.popleft()
        if cur.suffix != ".md" or not cur.exists():
            continue
        for nxt in _outgoing_doc_links(cur):
            if nxt not in seen and nxt.suffix == ".md" and nxt.exists():
                seen.add(nxt)
                queue.append(nxt)

    violations: list[tuple[Path, str, str]] = []
    for f in _docs_files():
        if f.resolve() in seen or _is_adr(f):
            continue
        rel = f.relative_to(REPO_ROOT)
        if str(rel) in _REACHABILITY_ALLOWLIST:
            continue
        if _doc_badge(f) in _REACHABILITY_EXEMPT_BADGES:
            continue
        violations.append(
            (
                rel,
                "reachable",
                "orphan: not reachable from any read-path doc / folio / README "
                "(link it from one, or badge it historical/archive)",
            ),
        )
    return violations


def check_freshness() -> list[tuple[Path, str, str]]:
    """``current-state.md`` must not hard-code the in-flight PR in prose.

    A ``(this PR, pending)`` / ``(pending PR)`` marker is a transient claim that
    rots on merge — the recurring drift this gate exists to stop. The living
    ledger names only merged PRs + the ``▶ Next action`` line; in-flight status is
    fetched from live GitHub at session start.
    """
    violations: list[tuple[Path, str, str]] = []
    f = DOCS_ROOT / "current-state.md"
    if not f.exists():
        return violations
    rel = f.relative_to(REPO_ROOT)
    for lineno, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        if _STALE_PENDING_RE.search(line):
            violations.append(
                (
                    rel,
                    "freshness",
                    f"L{lineno}: in-flight-PR marker in prose rots on merge — name "
                    "only merged work + the ▶ Next action line; get in-flight status "
                    "from live GitHub (`list_pull_requests`).",
                ),
            )
    return violations


def census() -> tuple[int, int, dict[str, int]]:
    """Return ``(total_docs, top_level_count, counts_by_badge)``.

    Pure (no printing) so it is unit-testable. ADRs are counted under a
    synthetic ``decision (ADR)`` key since they carry no Status badge.
    """
    files = _docs_files()
    by_badge: dict[str, int] = {}
    for f in files:
        key = "decision (ADR)" if _is_adr(f) else (_doc_badge(f) or "(unbadged)")
        by_badge[key] = by_badge.get(key, 0) + 1
    top_level = sum(1 for f in files if f.parent == DOCS_ROOT)
    return len(files), top_level, by_badge


def print_census() -> None:
    """Print the doc census + the top-level-pile ratchet status.

    Informational and **soft** — never changes the exit code. The point is
    to keep the doc surface visible every run so the top-level pile can't
    silently regrow past :data:`_TOP_LEVEL_DOCS_BUDGET`.
    """
    total, top_level, by_badge = census()
    print("check_docs census:")
    print(
        f"  total docs: {total}  ·  top-level docs/*.md: {top_level} "
        f"(ratchet {_TOP_LEVEL_DOCS_BUDGET})",
    )
    ordered = sorted(by_badge.items(), key=lambda kv: (-kv[1], kv[0]))
    print("  by badge: " + ", ".join(f"{k}={n}" for k, n in ordered))
    if top_level > _TOP_LEVEL_DOCS_BUDGET:
        print(
            f"  ⚠ top-level pile grew by {top_level - _TOP_LEVEL_DOCS_BUDGET} over "
            "the ratchet — move plans/audits/historical snapshots into a docs/ "
            "subdir (folio-linked), or lower the ratchet if you intentionally "
            "trimmed. (soft — not a CI failure)",
        )
    print()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SuperBot doc-hygiene checker.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any violation (CI gate); default reports and exits 0",
    )
    args = parser.parse_args(argv)

    print_census()

    violations = (
        check_badges()
        + check_links()
        + check_pinned()
        + check_reachable()
        + check_freshness()
    )
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
