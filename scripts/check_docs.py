#!/usr/bin/env python3
"""Doc-hygiene checker for SuperBot ``docs/``.

[session-close-gate] Invoked from ``/session-close`` Step 4 (``check_session_close_gate.py`` enforces that this stays wired in).

Hard rules (CI gate — see ``--strict``):

  1. **badge**  — every ``docs/**/*.md`` carries a machine-readable
     ``> **Status:** `<token>``` line in its first 12 lines, with ``<token>`` from
     the allowed taxonomy. ADRs (``docs/decisions/NNN-*.md``) are exempt: they use
     their own ``**Status:** Accepted/Superseded`` convention and are inherently
     binding.
  2. **link**   — every *relative* markdown link ``[text](path)`` inside ``docs/``
     resolves to an existing file/dir (external/anchor-only links are skipped).
  3. **pinned** — every concrete repo path referenced in backticks inside the
     read-path docs (``AGENT_ORIENTATION`` / ``current-state`` / ``repo-navigation-map``),
     **the always-loaded instruction core** (``.claude/CLAUDE.md`` +
     ``.claude/rules/*.md``), and **the routine prompts** (the
     ``docs/operations/*.md`` saved procedures the thin pointers target) exists, so
     neither the canonical read path, a CLAUDE.md *thin pointer*, nor the procedure
     a routine actually runs (the procedures→skills convention) ever points at a
     moved/renamed file — the "stale pointer" drift class (Q-0166).
  4. **reachable** — every live doc is reachable by following links from a read-path
     root (the read-path docs + subsystem folios + every ``README.md`` + ``CLAUDE.md``).
     Orphans fail unless badged ``historical`` / ``archive``, an ADR, or allowlisted —
     so a doc nobody links to can't accumulate silently.
  5. **freshness** — ``current-state.md`` must not hard-code the in-flight PR in prose.
     Markers like ``(this PR, pending)`` / ``(pending PR)`` rot the moment that PR
     merges (they were left stale twice in one session). The living ledger names only
     MERGED work + the single ``▶ Next action`` pointer; in-flight status comes from
     live GitHub. This gate forbids reintroducing the rotting markers.

Soft checks (printed as warnings — never change the exit code, like the census
ratchets):

  - **inventory-count** — a bare hand-maintained count (``N migrations`` /
    ``workflows`` / ``extensions`` / ``cogs`` / ``subsystems``) in a ``binding``
    doc, unless it cites a regen command, is marked generated, or carries
    ``<!-- count-ok -->``. The drift class the 2026-06-16 architecture review
    found; a nudge to cite/de-number, not a CI failure.
  - **supersede-integrity** — delegates to ``scripts/check_supersede_integrity.py``
    (warn-first, Q-0105, added 2026-07-08): every header ``SUPERSEDED`` banner's
    successor must resolve and link back, a fully-superseded doc may not keep its
    ``plan`` badge, and supersede-marked disposition-table rows must point at
    stamped docs. Once proven across sessions, promote its findings into the
    strict list (or delete the sibling script per its own header if unreliable).

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

# --- Inventory-count drift guard (soft) ------------------------------------
# A bare integer followed by one of these nouns in a BINDING doc is almost always
# a hand-maintained inventory count that rots the moment the repo grows — the
# exact drift class the 2026-06-16 architecture review found ("51 migrations" when
# live was 74; "×28 cogs" when live was 43). This is a **soft** forcing function
# (warn, never fail CI): binding contracts should cite the source of a count or
# drop the number, not pin a value that silently goes stale. (Q-0151 / folds in
# the readiness-maps-cite-regen-command idea.)
_COUNT_NOUNS = ("migrations", "workflows", "extensions", "cogs", "subsystems")
_INVENTORY_COUNT_RE = re.compile(
    r"\b\d+\s+(?:" + "|".join(_COUNT_NOUNS) + r")\b",
    re.IGNORECASE,
)
# A count is acceptable when, on its line or an adjacent one, it cites a regen
# command (a scripts/*.py), is marked generated, or carries the explicit
# `<!-- count-ok -->` escape hatch (declare an intentionally-maintained count).
_COUNT_CITED_RE = re.compile(
    r"scripts/[\w./-]+\.py|\bgenerated\b|<!--\s*count-ok\s*-->",
    re.IGNORECASE,
)
# Pinned-to-code docs already have a dedicated doc-test verifying their counts
# against live source, so a stronger guard than this heuristic covers them.
_COUNT_GUARD_EXEMPT_DOCS = frozenset(
    {
        "smoke-test-checklist.md",
        "help-command-surface-map.md",
        "ai-config-ownership.md",
    },
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
# 2026-06-08: 41 -> 16 after the Q-0010 consolidation moved plans / audits /
# inventories / historical snapshots into clustered subdirs (docs/ai/,
# docs/setup-platform/, docs/health/) and the type buckets, behind their folios.
# 2026-06-14: 18 -> 19 — the one sanctioned *raise*: repo-sector-map.md is a genuine
# top-level navigation peer to repo-navigation-map.md / repo-review-map.md (the 3-tap nav
# top layer, owner-directed Q-0137). Keep raising reserved for true top-level nav docs only.
# 2026-06-19: 19 -> 20 — sanctioned raise: bot-changelog.md is a genuine top-level content
# peer (the curated user-facing changelog the public bot site renders), pinned to this path
# by the website two-site-split plan (§1/§5, owner-directed Q-0178/Q-0179). Not a
# plan/audit/historical snapshot (those still belong in subdirs) — a durable, frequently
# updated ledger alongside current-state.md / roadmap.md.
# 2026-07-12: 20 -> 21 — sanctioned raise: fleet-reading-path.md is a true top-level nav
# doc (the cross-repo sibling of repo-navigation-map.md / repo-sector-map.md, boot-visible
# per owner directive Q-0272). The relocation alternative (current-state-archive.md) is
# load-bearing in trim_recently_shipped.py / check_current_state_ledger.py — not movable.
_TOP_LEVEL_DOCS_BUDGET = 21

# Soft cap on `current-state.md` § Recently shipped (newest-first merged-PR bullets).
# Keeps the 2nd-most-read doc lean — overflow is archived to current-state-archive.md.
# Headroom over the ~15 target so a busy week doesn't nag immediately. Warn-only.
_RECENTLY_SHIPPED_BUDGET = 20

# Soft cap (chars) on the live `▶ Next action` callout in current-state.md — the most-read
# pointer in the repo. It bloated to a ~40 KB single-paragraph wall before the band-#1230 pass
# pruned it by hand, because the bloat was prose (a standing Q-0102 finding) not a number a
# checker could name. This is the *gauge* (idea: reconcile-callout-line-budget-guard, Q-0089):
# the same warn-only role the Recently-shipped ratchet plays, but for the callout's length — it
# names the regression the moment the line crosses the budget. Warn-only (Q-0105 disposable dev
# tooling) — never changes the exit code. 6 KB ≈ a generously-sized live queue + next-startables
# + gated list; consumed band-history belongs in the per-band planning/reconciliation-pass-* records.
# unverified: confirm a few times that this tracks the real callout before trusting it; delete
# this sub-check if it proves noisy/unreliable across sessions.
_NEXT_ACTION_CALLOUT_BUDGET = 6000


# Per-claim files (Q-0195) are transient coordination state — one file per active
# session, created at start and deleted at close (the same lifecycle as `.sessions/`
# logs, which also live outside the docs census). They are not docs, so they carry no
# Status badge and need no reachability link; only their README.md is a real doc.
_CLAIMS_DIR = DOCS_ROOT / "owner" / "claims"


def _is_transient_claim(path: Path) -> bool:
    return path.parent == _CLAIMS_DIR and path.name.lower() != "readme.md"


def _docs_files() -> list[Path]:
    return sorted(f for f in DOCS_ROOT.rglob("*.md") if not _is_transient_claim(f))


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


def _instruction_files() -> list[Path]:
    """The always-loaded agent instruction core — ``.claude/CLAUDE.md`` plus the
    glob-triggered ``.claude/rules/*.md``.

    These are read at the start of (or during) *every* session, and the
    procedures→skills conversion (#1028 / #1029) deliberately turned their big
    runbooks into **thin pointers** ("full procedure: ``docs/...``"). A pointer
    here going stale is the "stale pointer" drift class (Q-0166), so their
    concrete backtick repo-paths are pin-checked the same as the read-path docs.
    Glob ``rules/*.md`` so a new rules file is auto-covered.
    """
    claude_dir = REPO_ROOT / ".claude"
    files = [claude_dir / "CLAUDE.md", *sorted((claude_dir / "rules").glob("*.md"))]
    return [f for f in files if f.exists()]


def _routine_prompt_files() -> list[Path]:
    """The canonical routine-prompt / saved-procedure docs the thin pointers target.

    The procedures→skills convention (#1028 / #1029) moves the *HOW* out of the
    always-loaded core and into these "fat" homes — ``autonomous-routines.md`` (the
    reconciliation routine's saved procedure) and ``hermes-dispatch-bridge.md`` (the
    dispatch routine's prompt). They are read in full on every routine run, so their
    own backtick repo-paths are pin-checked too: a pointer in the *destination* going
    stale is the same drift class a pointer in the *source* is. Scoped to these two
    actively-maintained prompts, not all of ``docs/operations/`` (which also holds
    dated investigation/review snapshots that may cite moved files).
    """
    ops = DOCS_ROOT / "operations"
    files = [ops / "autonomous-routines.md", ops / "hermes-dispatch-bridge.md"]
    return [f for f in files if f.exists()]


def _pinned_refs_in(f: Path) -> list[tuple[Path, str, str]]:
    """Flag every concrete backtick repo-path in ``f`` that doesn't resolve."""
    rel = f.relative_to(REPO_ROOT)
    text = f.read_text(encoding="utf-8")
    out: list[tuple[Path, str, str]] = []
    for ref in sorted(set(_PATH_REF_RE.findall(text))):
        if any(ch in ref for ch in "<>*"):
            continue  # placeholder / glob, not a concrete path
        if not (REPO_ROOT / ref).exists():
            out.append((rel, "pinned", f"references missing path `{ref}`"))
    return out


def check_pinned() -> list[tuple[Path, str, str]]:
    """Concrete repo paths cited in the read-path docs, the always-loaded
    instruction core (``.claude/CLAUDE.md`` / ``.claude/rules/*.md``), and the
    routine prompts (``docs/operations/*`` saved procedures) must exist.
    """
    violations: list[tuple[Path, str, str]] = []
    targets = (
        [DOCS_ROOT / name for name in _READPATH_DOCS]
        + _instruction_files()
        + _routine_prompt_files()
    )
    for f in targets:
        if not f.exists():
            continue
        violations += _pinned_refs_in(f)
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


def inventory_count_flags() -> list[tuple[Path, str, str]]:
    """Soft: bare hand-maintained inventory counts in BINDING docs (drift-prone).

    Flags ``N migrations`` / ``N workflows`` / ``N extensions`` / ``N cogs`` /
    ``N subsystems`` in a ``binding``-badged doc unless the count cites a regen
    command, is marked generated, or carries ``<!-- count-ok -->``. **Soft** — the
    caller prints these as a warning and never changes the exit code (a binding
    doc may legitimately state a number; this is a nudge to cite or de-number it,
    not a CI failure). Pinned-to-code docs are exempt (their doc-test guards them).
    """
    flags: list[tuple[Path, str, str]] = []
    for f in _docs_files():
        if _is_adr(f) or f.name in _COUNT_GUARD_EXEMPT_DOCS:
            continue
        if _doc_badge(f) != "binding":
            continue
        rel = f.relative_to(REPO_ROOT)
        lines = f.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines):
            for m in _INVENTORY_COUNT_RE.finditer(line):
                window = "\n".join(lines[max(0, i - 1) : i + 2])
                if _COUNT_CITED_RE.search(window):
                    continue
                flags.append(
                    (
                        rel,
                        "inventory-count",
                        f"L{i + 1}: hand-maintained count `{m.group(0)}` in a binding "
                        "doc rots when the repo grows — cite its regen command "
                        "(e.g. `scripts/extension_crosswalk.py`), drop the number, or "
                        "mark it `<!-- count-ok -->`.",
                    ),
                )
    return flags


def print_inventory_count_report() -> None:
    """Soft report of drift-prone inventory counts in binding docs (never fails CI)."""
    flags = inventory_count_flags()
    if not flags:
        return
    print(
        f"  ⚠ {len(flags)} hand-maintained inventory count(s) in binding docs — "
        "cite a regen command, drop the number, or mark `<!-- count-ok -->`. "
        "(soft — not a CI failure)",
    )
    for rel, _kind, msg in sorted(flags, key=lambda x: str(x[0])):
        print(f"      {rel}: {msg}")
    print()


def print_supersede_integrity_report() -> None:
    """Soft report of supersede-banner drift (never fails CI, never raises).

    Delegates to the sibling ``scripts/check_supersede_integrity.py`` (warn-first
    guard, Q-0105, added 2026-07-08 — see its header for the delete-if-unreliable
    clause). Failure-tolerant on purpose: a bug in the young checker must never
    redden this load-bearing gate. Promotion path once proven: fold its findings
    into the strict violations list in ``main()``.
    """
    try:
        import importlib.util

        script = Path(__file__).resolve().parent / "check_supersede_integrity.py"
        spec = importlib.util.spec_from_file_location(
            "check_supersede_integrity", script
        )
        if spec is None or spec.loader is None:
            return
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        findings = mod.check()
    except Exception as exc:  # noqa: BLE001 — soft check must never fail the gate
        print(f"  ⚠ supersede-integrity soft check skipped ({exc})\n")
        return
    if not findings:
        return
    print(
        f"  ⚠ {len(findings)} supersede-banner drift finding(s) — "
        "banner → successor resolves → successor links back → badge not `plan`. "
        "(soft — not a CI failure; details: scripts/check_supersede_integrity.py)",
    )
    for f in findings:
        print(f"      {f}")
    print()


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
    shipped = _recently_shipped_count()
    print(
        f"  current-state Recently-shipped: {shipped} (ratchet {_RECENTLY_SHIPPED_BUDGET})",
    )
    if shipped > _RECENTLY_SHIPPED_BUDGET:
        print(
            f"  ⚠ Recently-shipped grew by {shipped - _RECENTLY_SHIPPED_BUDGET} over the "
            "ratchet — move the oldest entries into docs/current-state-archive.md to keep "
            "the living ledger lean. (soft — not a CI failure)",
        )
    callout = _next_action_callout_chars()
    print(
        f"  current-state ▶ Next action callout: {callout} chars "
        f"(budget {_NEXT_ACTION_CALLOUT_BUDGET})",
    )
    if callout > _NEXT_ACTION_CALLOUT_BUDGET:
        print(
            f"  ⚠ ▶ Next action callout is {callout - _NEXT_ACTION_CALLOUT_BUDGET} chars over "
            "the budget — prune consumed band-history into the per-band "
            "planning/reconciliation-pass-* records (Q-0102). (soft — not a CI failure)",
        )
    print()


def _next_action_callout_chars() -> int:
    """Measure the live ``▶ Next action`` callout paragraph in ``current-state.md``.

    The callout is the contiguous run of non-empty blockquote (``>``) lines that begins
    with the ``▶ Next action`` marker, stopping at the first blockquote separator (a bare
    ``>``) or the end of the leading blockquote. Returns its character length (the ``> ``
    prefixes stripped). 0 if the marker is absent.
    """
    f = DOCS_ROOT / "current-state.md"
    if not f.exists():
        return 0
    lines = f.read_text(encoding="utf-8").splitlines()
    try:
        start = next(
            i
            for i, ln in enumerate(lines)
            if ln.lstrip("> ").startswith("**▶ Next action")
        )
    except StopIteration:
        return 0
    chars = 0
    for ln in lines[start:]:
        if not ln.startswith(">"):
            break
        body = ln[1:].strip()
        if not body:  # bare ``>`` separator ends the callout paragraph
            break
        chars += len(body)
    return chars


def _recently_shipped_count() -> int:
    """Count newest-first merged-PR bullets in ``current-state.md`` § Recently shipped."""
    f = DOCS_ROOT / "current-state.md"
    if not f.exists():
        return 0
    lines = f.read_text(encoding="utf-8").splitlines()
    try:
        hdr = next(
            i for i, ln in enumerate(lines) if ln.startswith("## Recently shipped")
        )
    except StopIteration:
        return 0
    count = 0
    for ln in lines[hdr + 1 :]:
        if ln.startswith("## "):
            break
        if ln.startswith("- **#"):
            count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SuperBot doc-hygiene checker.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="exit 1 if any violation (CI gate); default reports and exits 0",
    )
    args = parser.parse_args(argv)

    print_census()
    print_inventory_count_report()
    print_supersede_integrity_report()

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
