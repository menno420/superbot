#!/usr/bin/env python3.10
"""Warn-first guard: the supersede-banner handshake across ``docs/``.

Why this exists (idea ``docs/ideas/supersede-banner-integrity-checker-2026-07-06.md``,
implemented 2026-07-08, PR #1846): consolidation passes create supersede webs **by
hand** — a "⚠ SUPERSEDED (by X)" banner on the losing doc, a disposition table in the
winning doc — and nothing enforced any of it. The observed drift classes this
mechanizes (all real, from this repo's history):

* a banner names a successor that **doesn't exist / was renamed** (the "phantom
  handoff §F" class);
* the successor **never links back**, so the disposition handshake is one-sided and
  the superseded doc is unreachable from the winner;
* a superseded doc **keeps its live ``plan`` badge**, so ``docs/planning/README.md``'s
  "Active" promise and the doc's own header disagree and agents act from a dead plan;
* (reverse pass) a "Superseded / disposition" table row names a loser that **never
  got its banner** (the "design-spec header stayed stale 4 days" class).

Scope: only banners in a doc's **header block** (the blockquote run at the top of the
file) count as "this doc is superseded". Mid-doc ``SUPERSEDED`` markers are
section-level supersedes (e.g. ``docs/btd6/``) and are intentionally out of scope.
``SUPERSEDED-IN-PART`` is a partial supersede: the handshake checks apply, the
badge-must-not-be-``plan`` check does **not** (a partially-superseded plan may stay live).

Provenance / reliability (Q-0105): added 2026-07-08 because reconciliation passes kept
re-finding this drift by hand (Q-0194 "enforce, don't exhort"). **Unverified: confirm
its output against ground truth a few times across sessions before trusting it.**
Warn-first — the default run always exits 0; ``--strict`` (exit 1 on findings) is the
promotion path once proven. **Delete this if it proves unreliable over multiple
sessions** (noisy, or green while visible banner drift exists — the Q-0120 rule).

Stdlib-only.  Run:  python3.10 scripts/check_supersede_integrity.py [--strict]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = REPO_ROOT / "docs"

# A supersede marker: uppercase on purpose — prose like "supersedes the open
# backlogs" (a doc describing what *it* replaces) must not mark the doc itself.
_MARKER = re.compile(r"\bSUPERSEDED(-IN-PART)?\b")

# ``**Status:** `plan`  `` — the badge convention used across docs/ headers.
_STATUS_BADGE = re.compile(r"\*\*Status:\*\*\s*`([a-z][a-z-]*)`")

# Markdown links to .md files (anchor stripped): ``[text](path.md)`` / ``(path.md#sec)``.
_MD_LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+\.md)(?:#[^)]*)?\)")

# Plain-text .md path mentions (``docs/audits/foo.md`` in prose or inline code).
_PLAIN_MD = re.compile(r"(?<![\w(\[])((?:[\w.-]+/)*[\w.-]+\.md)\b")

# Headings that open a disposition section for the reverse pass.
_SUPERSEDE_HEADING = re.compile(r"^#{1,6}\s.*supersed", re.IGNORECASE)
_HEADING = re.compile(r"^#{1,6}\s")


def _header_blocks(text: str) -> list[list[str]]:
    """Blockquote blocks in the doc's header region.

    The header region: leading blank lines, an optional ``#`` title run, then any
    mix of blockquote (``>``) and blank lines. It ends at the first other content
    line (usually a ``##`` section or prose) — so mid-doc blockquotes never count.
    Returns each contiguous ``>`` run as its own block.
    """
    blocks: list[list[str]] = []
    current: list[str] = []
    seen_title = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                blocks.append(current)
                current = []
            continue
        if stripped.startswith(">"):
            current.append(stripped)
            continue
        if stripped.startswith("#") and not seen_title and not blocks and not current:
            seen_title = True
            continue
        break  # first real content line — header region over
    if current:
        blocks.append(current)
    return blocks


def _banner_block(text: str) -> list[str] | None:
    """The header blockquote block carrying a SUPERSEDED marker, if any."""
    for block in _header_blocks(text):
        if any(_MARKER.search(line) for line in block):
            return block
    return None


def _is_partial(block: list[str]) -> bool:
    """True when every marker in the block is SUPERSEDED-IN-PART (no full marker)."""
    full = any(m.group(1) is None for line in block for m in _MARKER.finditer(line))
    return not full


def _status_badge(text: str) -> str | None:
    for block in _header_blocks(text):
        for line in block:
            m = _STATUS_BADGE.search(line)
            if m:
                return m.group(1)
    return None


def _resolve(raw: str, doc: Path, repo_root: Path) -> Path | None:
    """Resolve a referenced .md path: doc-relative first, then repo-root-relative."""
    for base in (doc.parent, repo_root):
        candidate = (base / raw).resolve()
        if candidate.is_file():
            return candidate
    return None


def _successor_candidates(
    block: list[str], doc: Path, repo_root: Path
) -> tuple[list[Path], list[str]]:
    """(resolved successor paths, unresolvable md-link targets) named by a banner.

    Markdown-link targets that fail to resolve are *findings* (phantom successor).
    Plain-text path mentions are extra handshake candidates only — unresolvable
    ones are dropped silently (prose mentions are too loose to hard-flag).
    """
    resolved: list[Path] = []
    phantoms: list[str] = []
    text = "\n".join(block)
    seen: set[str] = set()
    for raw in _MD_LINK.findall(text):
        seen.add(raw)
        target = _resolve(raw, doc, repo_root)
        if target is None:
            phantoms.append(raw)
        elif target != doc.resolve():
            resolved.append(target)
    stripped_links = _MD_LINK.sub("", text)
    for raw in _PLAIN_MD.findall(stripped_links):
        if raw in seen:
            continue
        target = _resolve(raw, doc, repo_root)
        if target is not None and target != doc.resolve():
            resolved.append(target)
    # De-dup, order-preserving.
    unique: list[Path] = []
    for p in resolved:
        if p not in unique:
            unique.append(p)
    return unique, phantoms


def _check_banner(doc: Path, text: str, repo_root: Path) -> list[str]:
    """Findings for one superseded doc's banner (empty == handshake intact)."""
    block = _banner_block(text)
    if block is None:
        return []
    findings: list[str] = []
    rel = doc.relative_to(repo_root)

    successors, phantoms = _successor_candidates(block, doc, repo_root)
    for raw in phantoms:
        findings.append(
            f"{rel}: banner links successor `{raw}` which does not resolve "
            f"(phantom successor — fix the path or the banner)"
        )
    if not successors and not phantoms:
        findings.append(
            f"{rel}: SUPERSEDED banner names no successor doc "
            f"(link the doc that replaces it)"
        )
    elif successors:
        stem = doc.stem
        if not any(stem in s.read_text(encoding="utf-8") for s in successors):
            findings.append(
                f"{rel}: no named successor references `{stem}` back "
                f"(one-sided handshake — add it to the successor's disposition table)"
            )

    if not _is_partial(block) and _status_badge(text) == "plan":
        findings.append(
            f"{rel}: fully SUPERSEDED but still badged `plan` "
            f"(re-badge `historical`/`reference` so the planning index stays honest)"
        )
    return findings


def _check_disposition_tables(doc: Path, text: str, repo_root: Path) -> list[str]:
    """Reverse pass: disposition-table rows must point at docs that carry a banner.

    Under any heading matching /supersed/i, every table row whose text itself says
    "supersed" and links a .md doc is a supersede claim: the linked doc must exist
    and carry a header banner. Rows without that word (kept-live dispositions) and
    rows without links are skipped.
    """
    findings: list[str] = []
    rel = doc.relative_to(repo_root)
    lines = text.splitlines()
    in_section = False
    for line in lines:
        if _HEADING.match(line):
            in_section = bool(_SUPERSEDE_HEADING.match(line))
            continue
        if not in_section:
            continue
        stripped = line.strip()
        if not stripped.startswith("|") or "supersed" not in stripped.lower():
            continue
        for raw in _MD_LINK.findall(stripped):
            target = _resolve(raw, doc, repo_root)
            if target is None:
                findings.append(
                    f"{rel}: disposition row links `{raw}` which does not resolve"
                )
                continue
            if target == doc.resolve():
                continue
            if _banner_block(target.read_text(encoding="utf-8")) is None:
                findings.append(
                    f"{rel}: disposition row marks "
                    f"`{target.relative_to(repo_root)}` superseded, but that doc "
                    f"has no SUPERSEDED banner in its header (stamp it)"
                )
    return findings


def check(docs_root: Path = DOCS_ROOT, repo_root: Path = REPO_ROOT) -> list[str]:
    """All findings across the docs tree (empty == supersede web intact)."""
    findings: list[str] = []
    for doc in sorted(docs_root.rglob("*.md")):
        text = doc.read_text(encoding="utf-8")
        findings.extend(_check_banner(doc, text, repo_root))
        findings.extend(_check_disposition_tables(doc, text, repo_root))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 on findings (promotion path; default is warn-only, exit 0)",
    )
    args = parser.parse_args()

    findings = check()
    if findings:
        print("Supersede-banner integrity — the hand-maintained web has drift:")
        for f in findings:
            print(f"  ⚠ {f}")
        print(
            f"\n{len(findings)} finding(s). Handshake rule: banner → successor "
            f"resolves → successor links back → badge is not `plan`."
        )
        return 1 if args.strict else 0
    print(
        "✓ supersede web intact — every banner resolves, links back, and no dead plan"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
