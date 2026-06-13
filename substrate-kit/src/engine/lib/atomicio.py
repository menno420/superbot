"""Atomic file writes for crash-safe state.

A write goes to a sibling ``*.tmp`` file and is renamed into place with
``os.replace`` — an atomic rename on POSIX and Windows — so a process that dies
mid-write can never leave a half-written, unparseable file behind. This is the
robustness floor the whole engine builds on (plan: Gemini round).
"""

from __future__ import annotations

import os
from pathlib import Path


def atomic_write_text(path: Path, text: str) -> None:
    """Write ``text`` to ``path`` atomically via a temp file + ``os.replace``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)
