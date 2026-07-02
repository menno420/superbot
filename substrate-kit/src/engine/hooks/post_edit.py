"""PostToolUse edit advisor (plan section 5.B, Lane B7).

Runs after every Edit/Write tool call: the CLI's ``hook postedit`` entry point
extracts the edited file path from the PostToolUse stdin payload and asks
``evaluate_edit`` whether the edit deserves an advisory —

- **generated artifact** — the file lives under ``<state_dir>/rendered`` or
  ``<state_dir>/contextpacks``, or its head carries the ``NOT SOURCE OF
  TRUTH`` marker: edit the template/index and re-render, not the artifact.
- **missing Status badge** — a ``*.md`` under the docs root without a
  ``> **Status:** `<token>``` badge in its first 12 lines (the same badge scan
  ``check_docs`` runs, via the shared ``badge_token`` reader).

Like every hook evaluator this **fails open**: absolute or root-relative paths
both resolve, and an unreadable / missing file yields ``None`` — the advisor
never gets in the way when it is unsure.
"""

from __future__ import annotations

from pathlib import Path

from engine.checks.check_docs import badge_token
from engine.lib.config import Config

# The HTML-comment form only: planted (hand-editable) docs carry the bare
# phrase "NOT SOURCE OF TRUTH" in their badge prose, and the guard must not
# warn on every legitimate edit of a planted binding doc — only generated
# artifacts (contextpacks etc.) open with this comment marker.
_PE_MARKER = "<!-- NOT SOURCE OF TRUTH"
_PE_HEAD_LINES = 12
# <state_dir> subdirectories that hold build artifacts, never source.
_PE_GENERATED_DIRS = ("rendered", "contextpacks")
_PE_GENERATED_MSG = (
    "generated artifact — edit the template/index and re-render, not this file"
)
_PE_BADGE_MSG = (
    "missing Status badge — add `> **Status:** `<token>`` to its first 12 lines"
)


def _pe_resolve(root: Path, file_path: str) -> tuple[Path, Path | None]:
    """Return ``(absolute path, root-relative path or None)`` for an edit path.

    Accepts absolute and root-relative inputs; the relative half is ``None``
    when the file lives outside ``root`` (nothing to classify against config
    paths there).
    """
    path = Path(file_path)
    if not path.is_absolute():
        path = root / path
    try:
        rel = path.resolve().relative_to(root.resolve())
    except (OSError, ValueError):
        rel = None
    return path, rel


def _pe_head(path: Path) -> str:
    """Return the file's first 12 lines ('' when unreadable — fail open)."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return ""
    return "\n".join(lines[:_PE_HEAD_LINES])


def _pe_is_generated(config: Config, rel: Path | None, head: str) -> bool:
    """True when the edited file is a build artifact (by path or by marker)."""
    if _PE_MARKER in head:
        return True
    if rel is None:
        return False
    state_dir = Path(config.state_dir)
    return any(rel.is_relative_to(state_dir / sub) for sub in _PE_GENERATED_DIRS)


def evaluate_edit(root: Path, config: Config, file_path: str) -> str | None:
    """Return the advisory warning for one edited file, or None.

    Warns on a generated artifact (path under ``<state_dir>/rendered`` /
    ``<state_dir>/contextpacks``, or the generated-artifact HTML-comment marker)
    and on a docs-root ``*.md`` lacking a Status badge. Tolerant of absolute
    or root-relative ``file_path`` and of unreadable / missing files (None).
    """
    try:
        path, rel = _pe_resolve(root, file_path)
        if not path.is_file():
            return None
        name = rel.as_posix() if rel is not None else path.as_posix()
        if _pe_is_generated(config, rel, _pe_head(path)):
            return f"{name}: {_PE_GENERATED_MSG}"
        if (
            rel is not None
            and path.suffix == ".md"
            and rel.is_relative_to(Path(config.docs_root))
            and badge_token(path) is None
        ):
            return f"{name}: {_PE_BADGE_MSG}"
        return None
    except Exception:  # fail open — the advisor never blocks an edit
        return None
