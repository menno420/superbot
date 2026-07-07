#!/usr/bin/env python3.10
"""Amendment-registry integrity checker — the enforcer `rebuild-amendments.yml` names.

Provenance / reliability header (per CLAUDE.md Q-0105 adopt-with-kill-switch):
- Why: the registry (`docs/planning/rebuild-amendments.yml`) is THE sole amendment-ID minting
  authority (spec 01 §3.7) and its own header says its rules are "enforced by
  tools/check_amendments.py" — but the checker was never built (Gate-V P-9 / Arm-A Blocker #2:
  "Gate-0 docs complete ≠ build prerequisites in place"). Canonical-plan §5 step 3 builds it.
- What it enforces (the header's own rules, stateless forms):
  1. next-free-number / append-only — per family (G-/R-/P-) the IDs form a contiguous 1..N
     sequence with no duplicates (a deletion or out-of-order mint breaks contiguity);
  2. a refuted name is never reused — no amendment/provisional name collides with a `refuted:`
     key, and names are unique across the registry;
  3. status discipline — amendment status ∈ {in-spec, pending-gate-0}; `in-spec` requires a
     non-null spec_ref; `pending-gate-0` requires spec_ref: null;
  4. every in-spec spec_ref resolves in the declared spec_corpus — named `.md` files exist under
     a corpus root, and bare `§X.Y` refs match a numbered heading somewhere in the corpus.
- Stdlib-only, line-based parse (the registry's entries are one flow-mapping per line by
  convention) — runs in the pre-pip CI stage like its sibling doc checkers.
- Added: 2026-07-07 (session `claude/superbot-rebuild-phase-2.5-qk07s7`, PR #1775).
  **Unverified** — confirm its output against ground truth a few times across sessions before
  trusting it. **Delete this checker if it proves unreliable over multiple sessions.**

Usage::

    python3.10 tools/check_amendments.py           # check the live registry
    python3.10 tools/check_amendments.py --quiet   # exit code only
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "docs" / "planning" / "rebuild-amendments.yml"

_SECTION_RE = re.compile(
    r"^(amendments|riders|provisional|refuted|spec_corpus|version):"
)
_ENTRY_RE = re.compile(r"^ {2}([A-Za-z][\w./-]*(?:-\d+)?):\s*\{(.*)\}\s*$")
_CORPUS_ITEM_RE = re.compile(r"^ {2}-\s*(\S+)")
_FAMILY_ID_RE = re.compile(r"^([GRP])-(\d+)$")
_MD_REF_RE = re.compile(r"([\w./-]+\.md)")
_SECT_REF_RE = re.compile(r"§(\d+(?:\.\d+)*)")
_ALLOWED_STATUS = {"in-spec", "pending-gate-0"}


def _field(body: str, key: str) -> str | None:
    """Extract a flow-mapping field's value (quoted or bare, up to the next comma)."""
    m = re.search(rf"(?:^|[,{{])\s*{key}:\s*(\"[^\"]*\"|'[^']*'|[^,}}]+)", body)
    if not m:
        return None
    return m.group(1).strip().strip("\"'").strip()


def parse_registry(text: str) -> dict:
    """Parse the registry into sections; each entry keeps (id, fields-body, line no)."""
    sections: dict[str, list[tuple[str, str, int]]] = {}
    corpus: list[str] = []
    current = ""
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        sect = _SECTION_RE.match(line)
        if sect:
            current = sect.group(1)
            continue
        if current == "spec_corpus":
            item = _CORPUS_ITEM_RE.match(line)
            if item:
                corpus.append(item.group(1).rstrip("/"))
            continue
        entry = _ENTRY_RE.match(line)
        if entry and current in ("amendments", "riders", "provisional", "refuted"):
            sections.setdefault(current, []).append(
                (entry.group(1), entry.group(2), lineno),
            )
    return {"sections": sections, "corpus": corpus}


def _corpus_texts(corpus: list[str]) -> list[str]:
    texts: list[str] = []
    for root in corpus:
        path = REPO_ROOT / root
        if path.is_file():
            texts.append(path.read_text(encoding="utf-8"))
        elif path.is_dir():
            texts.extend(
                p.read_text(encoding="utf-8") for p in sorted(path.glob("*.md"))
            )
    return texts


def check(text: str) -> list[str]:
    """Return all integrity violations found in the registry text."""
    parsed = parse_registry(text)
    sections = parsed["sections"]
    problems: list[str] = []

    # Rule 4 precondition: corpus roots exist.
    for root in parsed["corpus"]:
        if not (REPO_ROOT / root).exists():
            problems.append(f"spec_corpus entry does not exist on disk: {root}")

    # Rule 1 — per-family contiguous 1..N, no duplicates (next-free + append-only).
    families: dict[str, list[int]] = {"G": [], "R": [], "P": []}
    for sect in ("amendments", "riders", "provisional"):
        for entry_id, _body, lineno in sections.get(sect, []):
            m = _FAMILY_ID_RE.match(entry_id)
            if not m:
                problems.append(f"line {lineno}: id {entry_id!r} is not <G|R|P>-<n>")
                continue
            families[m.group(1)].append(int(m.group(2)))
    for fam, nums in families.items():
        dupes = sorted({n for n in nums if nums.count(n) > 1})
        for n in dupes:
            problems.append(f"family {fam}: duplicate id {fam}-{n}")
        if nums and sorted(set(nums)) != list(range(1, max(nums) + 1)):
            missing = sorted(set(range(1, max(nums) + 1)) - set(nums))
            problems.append(
                f"family {fam}: ids are not contiguous 1..{max(nums)} "
                f"(missing {', '.join(f'{fam}-{n}' for n in missing)}) — "
                "mint next-free only; never renumber or delete"
            )

    # Rule 2 — refuted names never reused; names unique.
    refuted = {entry_id for entry_id, _b, _n in sections.get("refuted", [])}
    seen: dict[str, str] = {}
    for sect in ("amendments", "provisional"):
        for entry_id, body, lineno in sections.get(sect, []):
            name = _field(body, "name")
            if not name:
                problems.append(f"line {lineno}: {entry_id} has no name field")
                continue
            if name in refuted:
                problems.append(
                    f"line {lineno}: {entry_id} reuses REFUTED name {name!r} "
                    "(do-not-re-propose)"
                )
            if name in seen:
                problems.append(
                    f"line {lineno}: {entry_id} duplicates name {name!r} "
                    f"(already used by {seen[name]})"
                )
            seen[name] = entry_id

    # Rules 3 + 4 — status discipline and in-spec ref resolution.
    corpus_texts = _corpus_texts(parsed["corpus"])
    for entry_id, body, lineno in sections.get("amendments", []):
        status = _field(body, "status")
        spec_ref = _field(body, "spec_ref")
        if status not in _ALLOWED_STATUS:
            problems.append(
                f"line {lineno}: {entry_id} has unknown status {status!r} "
                f"(allowed: {sorted(_ALLOWED_STATUS)})"
            )
            continue
        if status == "pending-gate-0" and spec_ref not in (None, "null", "~"):
            problems.append(
                f"line {lineno}: {entry_id} is pending-gate-0 but carries "
                f"spec_ref {spec_ref!r} (must be null until its fold ships)"
            )
        if status == "in-spec":
            if spec_ref in (None, "null", "~", ""):
                problems.append(
                    f"line {lineno}: {entry_id} is in-spec with no spec_ref"
                )
                continue
            for md in _MD_REF_RE.findall(spec_ref):
                basename = Path(md).name
                if not any(
                    p.name == basename
                    for root in parsed["corpus"]
                    for p in (REPO_ROOT / root).glob("**/*.md")
                    if (REPO_ROOT / root).is_dir()
                ) and not any(root.endswith(md) for root in parsed["corpus"]):
                    problems.append(
                        f"line {lineno}: {entry_id} spec_ref names {md!r} "
                        "which is not in the spec_corpus"
                    )
            for num in _SECT_REF_RE.findall(spec_ref):
                heading = re.compile(rf"^#{{1,6}}\s+{re.escape(num)}\b", re.MULTILINE)
                if not any(heading.search(t) for t in corpus_texts):
                    problems.append(
                        f"line {lineno}: {entry_id} spec_ref §{num} matches no "
                        "numbered heading in the spec_corpus"
                    )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="SuperBot rebuild amendment-registry integrity checker.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress output; return exit code only",
    )
    args = parser.parse_args(argv)

    if not REGISTRY.exists():
        if not args.quiet:
            print(f"check_amendments: registry missing: {REGISTRY}")
        return 1
    problems = check(REGISTRY.read_text(encoding="utf-8"))
    if not problems:
        if not args.quiet:
            print("check_amendments: registry integrity OK ✓")
        return 0
    if not args.quiet:
        print(f"check_amendments — {len(problems)} violation(s):")
        for p in problems:
            print(f"  - {p}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
