r"""Config-driven seam-authority fences (Lane B6).

A *seam* is a boundary the host declares in ``config.seams`` — "all writes go
through the mutation service", "no direct pool access outside the db layer" —
generalising superbot's hardcoded architecture fences into pure data. Each
seam is a dict::

    {"name": "db-seam",
     "paths": ["src/**/*.py"],        # globs to scan, relative to root
     "forbidden": "pool\\.execute",   # regex; a hit is a violation
     "allowed": ["src/db/**"],        # exempt globs (the seam's own home)
     "message": "call db.* helpers, never the pool directly"}

The scan is plain line-by-line text matching (no AST, no imports) so it works
on any language the host points it at. A regex hit in a non-exempt file
becomes a ``Finding(kind="seam")`` whose message carries the seam name, the
configured message, and the line number. Findings reuse the ``Finding``
record from ``engine.checks.check_docs``; unreadable/binary files are skipped.
"""

from __future__ import annotations

import re
from pathlib import Path

from engine.checks.check_docs import Finding


def _seam_files(root: Path, globs: list[str]) -> list[Path]:
    """Return the de-duplicated files matched by ``globs`` under ``root``."""
    matched: set[Path] = set()
    for pattern in globs:
        for candidate in root.glob(pattern):
            if candidate.is_file():
                matched.add(candidate)
    return sorted(matched)


def _seam_exempt_files(root: Path, allowed: list[str]) -> set[Path]:
    """Resolve the exempt set with the SAME glob semantics as ``paths``.

    fnmatch let ``*`` cross ``/`` — an ``allowed`` pattern like ``src/*``
    silently exempted ``src/sub/hack.py`` and opened a fence gap. Re-globbing
    with ``root.glob`` keeps both sides of the seam on pathlib semantics.

    A glob hit that is a *directory* is expanded to the files under it — a
    trailing ``**`` (the documented ``src/db/**`` "own home" form) matches only
    directories in ``Path.glob``, so exempting by raw glob hits compared the
    file being scanned against a set of dirs and exempted **nothing**: a seam
    flagged its own home. Directory hits now contribute their whole file
    subtree (the ``economy`` reference-scan idiom), so ``src/db/**``,
    ``src/db/*`` and ``src/db/**/*`` all exempt the subtree as documented.
    """
    exempt: set[Path] = set()
    for pattern in allowed:
        for hit in root.glob(pattern):
            if hit.is_file():
                exempt.add(hit)
            elif hit.is_dir():
                exempt.update(p for p in hit.rglob("*") if p.is_file())
    return exempt


def check_seam_authority(root: Path, seams: list[dict]) -> list[Finding]:
    """Scan the configured seams under ``root``; return the violations.

    Each seam dict supplies ``name``, ``paths`` (globs to scan), ``forbidden``
    (a regex), optional ``allowed`` (exempt globs), and ``message``. A seam
    with an invalid regex is itself reported as a finding rather than raising
    (a broken fence should fail loud in the report, not crash the check).
    """
    findings: list[Finding] = []
    for seam in seams:
        name = seam.get("name", "unnamed")
        message = seam.get("message", "forbidden pattern")
        pattern = seam.get("forbidden", "")
        if not pattern:
            # An empty pattern's ``.search`` matches every line — a seam with no
            # ``forbidden`` would flag every line of every in-scope file. That is
            # a misconfiguration; report it loud instead of drowning the report.
            msg = f"seam `{name}`: no `forbidden` regex configured — seam skipped"
            findings.append(Finding("", "seam", msg))
            continue
        try:
            forbidden = re.compile(pattern)
        except re.error as exc:
            msg = f"seam `{name}`: invalid forbidden regex: {exc}"
            findings.append(Finding("", "seam", msg))
            continue
        exempt = _seam_exempt_files(root, list(seam.get("allowed", [])))
        for path in _seam_files(root, list(seam.get("paths", []))):
            rel = path.relative_to(root).as_posix()
            if path in exempt:
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                if forbidden.search(line):
                    msg = f"L{lineno}: seam `{name}`: {message}"
                    findings.append(Finding(rel, "seam", msg))
    return findings
