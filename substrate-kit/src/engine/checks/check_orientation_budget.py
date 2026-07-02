"""Orientation-budget gate — the K0 <=7,000-word boot-read cap (Lane B6).

Orientation cost is the tax every session pays before real work starts, so
the kit meters it: the *boot set* (``config.orientation["boot_docs"]``,
falling back to ``config.readpath_docs`` when empty) must total no more than
``config.orientation["budget_words"]`` words. Boot-doc entries name files
under ``docs_root``; an entry containing ``/`` resolves from the project root
instead, so hosts can meter root-level docs (a journal, a CLAUDE.md) too.

Per-doc self-caps ride on top: a doc whose first 12 lines declare
``substrate-budget: N words`` is individually capped at N — a living doc can
pin its own growth ceiling without touching config.

Finding kinds: ``orientation-missing`` (a boot doc is absent),
``orientation-budget`` (the total blows the budget), ``orientation-doc-cap``
(a self-capped doc outgrew its declared cap). Findings reuse the ``Finding``
record from ``engine.checks.check_docs``.
"""

from __future__ import annotations

import re
from pathlib import Path

from engine.checks.check_docs import Finding
from engine.lib.config import Config

# `substrate-budget: 500 words` — the per-doc self-cap declaration.
_OB_SELF_CAP_RE = re.compile(r"substrate-budget:\s*(\d+)\s*words", re.IGNORECASE)
_OB_HEAD_LINES = 12
_OB_TOTAL_KEY = "_total"


def _ob_word_count(path: Path) -> int | None:
    """Return the doc's word count, or ``None`` when it cannot be read."""
    try:
        return len(path.read_text(encoding="utf-8").split())
    except (OSError, UnicodeDecodeError):
        return None


def _ob_self_cap(path: Path) -> int | None:
    """Return the doc's declared self-cap from its first 12 lines, if any."""
    try:
        head = path.read_text(encoding="utf-8").splitlines()[:_OB_HEAD_LINES]
    except (OSError, UnicodeDecodeError):
        return None
    match = _OB_SELF_CAP_RE.search("\n".join(head))
    return int(match.group(1)) if match else None


def _ob_rel(path: Path, root: Path) -> str:
    """Return ``path`` relative to ``root`` (posix) when possible, else str."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def orientation_word_count(root: Path, boot_docs: list[Path]) -> dict[str, int]:
    """Return per-doc word counts plus a ``_total`` for the boot set.

    Keys are paths relative to ``root`` where possible. A missing or
    unreadable doc counts 0 here — ``check_orientation_budget`` is the layer
    that reports it.
    """
    counts: dict[str, int] = {}
    total = 0
    for doc in boot_docs:
        words = _ob_word_count(doc) or 0
        counts[_ob_rel(doc, root)] = words
        total += words
    counts[_OB_TOTAL_KEY] = total
    return counts


def _ob_boot_paths(root: Path, config: Config) -> list[Path]:
    """Resolve the configured boot set to concrete paths.

    Explicit ``orientation["boot_docs"]`` entries: a bare name resolves under
    ``docs_root``, an entry with ``/`` resolves from the project root. The
    ``readpath_docs`` fallback resolves under ``docs_root`` unconditionally —
    matching ``check_reachable``, which reads the same key.
    """
    orientation = config.orientation or {}
    docs_root = root / config.docs_root
    explicit = list(orientation.get("boot_docs") or [])
    if explicit:
        # Explicit boot docs: a bare name resolves under docs_root, an entry
        # with "/" resolves from the project root (CONSTITUTION.md etc.).
        return [root / e if "/" in e else docs_root / e for e in explicit]
    # readpath_docs fallback: resolve under docs_root unconditionally, matching
    # check_reachable — the two consumers of that key must agree.
    return [docs_root / e for e in config.readpath_docs]


def check_orientation_budget(root: Path, config: Config) -> list[Finding]:
    """Meter the boot-read set against the orientation budget.

    Reports missing boot docs (``orientation-missing``), a total word count
    over ``orientation["budget_words"]`` (``orientation-budget``), and any doc
    that outgrew its own ``substrate-budget: N words`` self-cap
    (``orientation-doc-cap``).
    """
    findings: list[Finding] = []
    boot_paths = _ob_boot_paths(root, config)
    for doc in boot_paths:
        if not doc.is_file():
            msg = "boot doc missing — fix the path or the orientation config"
            findings.append(Finding(_ob_rel(doc, root), "orientation-missing", msg))

    counts = orientation_word_count(root, boot_paths)
    budget = int((config.orientation or {}).get("budget_words", 7000))
    total = counts[_OB_TOTAL_KEY]
    if total > budget:
        msg = (
            f"boot-read set totals {total} words, over the "
            f"{budget}-word orientation budget — trim or demote a boot doc"
        )
        findings.append(Finding(_OB_TOTAL_KEY, "orientation-budget", msg))

    for doc in boot_paths:
        cap = _ob_self_cap(doc)
        if cap is None:
            continue
        words = counts.get(_ob_rel(doc, root), 0)
        if words > cap:
            msg = f"doc is {words} words, over its {cap}-word self-cap"
            findings.append(Finding(_ob_rel(doc, root), "orientation-doc-cap", msg))
    return findings
