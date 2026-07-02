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
from fnmatch import fnmatch
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


def _seam_is_exempt(rel: str, allowed: list[str]) -> bool:
    """True when the relpath matches any exempt glob (fnmatch semantics)."""
    return any(fnmatch(rel, pattern) for pattern in allowed)


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
        try:
            forbidden = re.compile(seam.get("forbidden", ""))
        except re.error as exc:
            msg = f"seam `{name}`: invalid forbidden regex: {exc}"
            findings.append(Finding("", "seam", msg))
            continue
        allowed = list(seam.get("allowed", []))
        for path in _seam_files(root, list(seam.get("paths", []))):
            rel = path.relative_to(root).as_posix()
            if _seam_is_exempt(rel, allowed):
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
