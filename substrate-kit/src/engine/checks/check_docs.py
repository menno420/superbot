"""Generic doc-hygiene checker (config-driven port of ``check_docs``).

Three portable checks, every input supplied by the caller (from config) rather
than hardcoded:

  1. **badge**      — every ``*.md`` under ``docs_root`` (non-ADR) carries a
     ``> **Status:** `<token>``` line in its first 12 lines, ``<token>`` drawn
     from the project's allowed taxonomy.
  2. **link**       — every relative markdown link ``[text](path)`` resolves to
     an existing file (external / anchor-only links are skipped).
  3. **reachable**  — every live doc is reachable by following links + backtick
     ``<docs>/*.md`` refs from a read-path root (the read-path docs + any
     ``README.md``). Orphans fail unless badged ``historical`` / ``archive`` or
     an ADR.

The host's soft ratchets (top-level pile, recently-shipped) and the
superbot-specific freshness rule are intentionally left behind — they are
project policy, not portable mechanism. Pure stdlib; returns findings rather
than printing so the CLI owns all output.
"""

from __future__ import annotations

import re
from collections import deque
from collections.abc import Collection, Sequence
from pathlib import Path
from typing import NamedTuple


class Finding(NamedTuple):
    """One doc-hygiene violation: ``path`` is relative to ``docs_root``."""

    path: str
    kind: str
    message: str


# `> **Status:** `<token>`` — the machine-readable badge (rich text may follow).
_BADGE_RE = re.compile(r"\*\*Status:\*\*\s*`([a-z-]+)`")
# ADR filename: NNN-something.md (exempt — ADRs use their own Accepted/Superseded).
_ADR_RE = re.compile(r"^\d+-.*\.md$")
# Markdown link target: [text](target).
_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
# Badges whose docs are retired content and need no inbound link.
_EXEMPT_BADGES = frozenset({"historical", "archive"})

_BADGE_MISSING = "missing `> **Status:** `<token>`` in first 12 lines"
_ORPHAN_MSG = (
    "orphan: not reachable from any read-path doc / README "
    "(link it from one, or badge it historical/archive)"
)


def _md_files(docs_root: Path) -> list[Path]:
    """Return every ``*.md`` under ``docs_root`` (sorted, empty if absent)."""
    if not docs_root.exists():
        return []
    return sorted(docs_root.rglob("*.md"))


def _is_adr(path: Path) -> bool:
    """True for ``decisions/NNN-*.md`` ADR files (badge-exempt)."""
    return path.parent.name == "decisions" and bool(_ADR_RE.match(path.name))


def badge_token(path: Path) -> str | None:
    """Return the doc's Status-badge token from its first 12 lines, or None.

    Public: the trigger detector (and any host tooling) classifies docs by this
    same badge scan — one badge reader, not per-module copies.
    """
    head = "\n".join(path.read_text(encoding="utf-8").splitlines()[:12])
    match = _BADGE_RE.search(head)
    return match.group(1) if match else None


# Backward-compatible alias for the original private name.
_badge_token = badge_token


def _link_target(raw: str) -> str:
    """Normalise a markdown link target (drop ``<>``, title, ``#anchor``)."""
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        target = target[1:].split(">", 1)[0]
    parts = target.split()
    target = parts[0] if parts else target
    return target.split("#", 1)[0]


def _backtick_docs_re(docs_root: Path) -> re.Pattern[str]:
    """Compile the ``<docs>/*.md`` backtick-ref pattern for this doc root."""
    name = re.escape(docs_root.name)
    return re.compile(rf"`({name}/[\w./-]+\.md)`")


def check_badges(docs_root: Path, badge_tokens: Collection[str]) -> list[Finding]:
    """Every non-ADR doc must declare a Status badge from the taxonomy."""
    allowed = set(badge_tokens)
    findings: list[Finding] = []
    for f in _md_files(docs_root):
        if _is_adr(f):
            continue
        rel = f.relative_to(docs_root).as_posix()
        token = badge_token(f)
        if token is None:
            findings.append(Finding(rel, "badge", _BADGE_MISSING))
        elif token not in allowed:
            allowed_list = ", ".join(sorted(allowed))
            findings.append(
                Finding(
                    rel,
                    "badge",
                    f"invalid badge token `{token}` (allowed: {allowed_list})",
                ),
            )
    return findings


def check_links(docs_root: Path) -> list[Finding]:
    """Relative markdown links inside ``docs_root`` must resolve."""
    findings: list[Finding] = []
    for f in _md_files(docs_root):
        rel = f.relative_to(docs_root).as_posix()
        for lineno, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for raw in _MD_LINK_RE.findall(line):
                if raw.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = _link_target(raw)
                if not target or target.startswith(("http", "mailto:")):
                    continue
                if not (f.parent / target).resolve().exists():
                    msg = f"L{lineno}: dead link -> {raw}"
                    findings.append(Finding(rel, "link", msg))
    return findings


def _outgoing_links(path: Path, docs_root: Path) -> set[Path]:
    """Resolve every relative markdown link + backtick ``<docs>/*.md`` ref."""
    out: set[Path] = set()
    backtick = _backtick_docs_re(docs_root)
    root = docs_root.parent
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
        for ref in backtick.findall(line):
            out.add((root / ref).resolve())
    return out


def check_reachable(docs_root: Path, readpath_docs: Sequence[str]) -> list[Finding]:
    """Every live doc must be reachable from a read-path root / README.

    Walks the doc graph (markdown links + backtick ``<docs>/*.md`` refs) from the
    roots; any doc not reached — and not ``historical`` / ``archive`` badged or an
    ADR — is an orphan.
    """
    roots = [docs_root / name for name in readpath_docs]
    roots += sorted(docs_root.rglob("README.md"))
    seen: set[Path] = set()
    queue: deque[Path] = deque()
    for root in roots:
        resolved = root.resolve()
        if root.exists() and resolved not in seen:
            seen.add(resolved)
            queue.append(resolved)
    while queue:
        cur = queue.popleft()
        if cur.suffix != ".md" or not cur.exists():
            continue
        for nxt in _outgoing_links(cur, docs_root):
            if nxt not in seen and nxt.suffix == ".md" and nxt.exists():
                seen.add(nxt)
                queue.append(nxt)

    findings: list[Finding] = []
    for f in _md_files(docs_root):
        if f.resolve() in seen or _is_adr(f):
            continue
        if badge_token(f) in _EXEMPT_BADGES:
            continue
        rel = f.relative_to(docs_root).as_posix()
        findings.append(Finding(rel, "reachable", _ORPHAN_MSG))
    return findings


def run_doc_checks(
    docs_root: Path,
    badge_tokens: Collection[str],
    readpath_docs: Sequence[str],
) -> list[Finding]:
    """Run every doc check and return the combined findings."""
    return (
        check_badges(docs_root, badge_tokens)
        + check_links(docs_root)
        + check_reachable(docs_root, readpath_docs)
    )
