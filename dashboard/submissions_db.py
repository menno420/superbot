"""Read + moderate side of the submissions store (dev-site / dashboard).

The owner-gated dev site reads the ``pending`` queue and moderates it (plan §2.3):
``list_pending`` shows what the public submitted, ``set_status`` approves/rejects a
row, and ``attach_issue_url`` records the GitHub issue created on approval. This
module holds the **full** (read/write) role on the submissions DB — the counterpart
to the public site's INSERT-only :mod:`botsite.submissions_db`.

The two modules share **only** the table contract in
``botsite/migrations/001_submissions.sql`` — never code (plan §2.2 / §5). Keeping
them as independent, single-purpose modules is what lets the two services hold
different DB roles (INSERT-only vs. full) without a shared package re-coupling them.

**Dormant by default.** When ``SUBMISSIONS_DB_DSN`` is not set, :func:`is_configured`
is ``False`` and the moderation page shows a "set this up" state instead of querying
anything (same discipline as the control API). The owner sets the DSN on the dev-site
Railway service at rollout (plan §6).

Decoupling: part of the web tier, never imports ``disbot``; uses ``asyncpg`` directly
against its own DSN (NOT the bot's ``utils.db`` seam). ``asyncpg`` is lazy-imported so
the module loads where the driver is absent.
"""

from __future__ import annotations

import os
from typing import Any

# Terminal moderation statuses an owner decision can set (the DDL also allows the
# default 'pending', which only the public INSERT path writes — never a moderator).
STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"
MODERATION_STATUSES: frozenset[str] = frozenset({STATUS_APPROVED, STATUS_REJECTED})

# Columns the moderation view reads. Explicit (never SELECT *) so a future schema
# addition can't silently surface an unexpected column in the owner's UI.
_ROW_COLUMNS = (
    "id",
    "kind",
    "title",
    "body",
    "surface",
    "contact",
    "status",
    "submitted_at",
    "github_issue_url",
)

_DSN_ENV = "SUBMISSIONS_DB_DSN"


class SubmissionsNotConfiguredError(RuntimeError):
    """Raised by the query helpers when ``SUBMISSIONS_DB_DSN`` is unset."""


def dsn() -> str | None:
    """Return the submissions DB DSN, or ``None`` when the store is dormant."""
    value = os.environ.get(_DSN_ENV, "").strip()
    return value or None


def is_configured() -> bool:
    """``True`` when the submissions DB DSN is set."""
    return dsn() is not None


def _require_dsn() -> str:
    target = dsn()
    if target is None:
        raise SubmissionsNotConfiguredError(
            f"{_DSN_ENV} is not set — the submissions store is dormant",
        )
    return target


async def _connect() -> Any:
    """Open a short-lived asyncpg connection to the submissions DSN."""
    import asyncpg  # lazy — keeps module import-safe where the driver is absent

    return await asyncpg.connect(_require_dsn())


async def list_pending(limit: int = 200) -> list[dict[str, Any]]:
    """Return the ``pending`` submissions, oldest first (the moderation queue).

    Oldest-first so the owner works through the backlog in arrival order. Each row
    is a plain dict of :data:`_ROW_COLUMNS`; the body is returned verbatim (plain
    text) — the moderation template renders it **escaped** (plan §4.2), this layer
    never renders. Raises :class:`SubmissionsNotConfiguredError` when dormant.
    """
    sql = (
        f"SELECT {', '.join(_ROW_COLUMNS)} FROM submissions "
        f"WHERE status = 'pending' ORDER BY submitted_at ASC LIMIT $1"
    )
    conn = await _connect()
    try:
        rows = await conn.fetch(sql, limit)
    finally:
        await conn.close()
    return [dict(row) for row in rows]


async def set_status(
    submission_id: int,
    status: str,
    *,
    moderated_by: str | None = None,
) -> bool:
    """Approve or reject a **pending** submission; return ``True`` if a row changed.

    Only flips a row that is still ``pending`` (the ``WHERE status='pending'`` guard
    makes a double-click idempotent — a second decision on an already-moderated row
    is a no-op and returns ``False``). ``status`` must be ``approved`` or
    ``rejected``; ``moderated_by`` records the owner's Discord id at decision time.
    Raises :class:`ValueError` on a bad status, :class:`SubmissionsNotConfiguredError`
    when dormant.
    """
    if status not in MODERATION_STATUSES:
        raise ValueError(
            f"status must be one of {sorted(MODERATION_STATUSES)}, got {status!r}",
        )
    sql = (
        "UPDATE submissions SET status = $2, moderated_by = $3 "
        "WHERE id = $1 AND status = 'pending'"
    )
    conn = await _connect()
    try:
        result = await conn.execute(sql, submission_id, status, moderated_by)
    finally:
        await conn.close()
    return _rows_affected(result) > 0


async def attach_issue_url(submission_id: int, issue_url: str) -> bool:
    """Record the GitHub issue URL on an approved submission; return ``True`` on change.

    Called after the GitHub mirror creates the issue (plan §2.3). Idempotent: only
    sets the URL when it is still NULL, so a retried mirror cannot overwrite a prior
    link (the double-file guard, plan §4.2). Raises :class:`SubmissionsNotConfiguredError`
    when dormant.
    """
    sql = (
        "UPDATE submissions SET github_issue_url = $2 "
        "WHERE id = $1 AND github_issue_url IS NULL"
    )
    conn = await _connect()
    try:
        result = await conn.execute(sql, submission_id, issue_url)
    finally:
        await conn.close()
    return _rows_affected(result) > 0


def _rows_affected(command_tag: str) -> int:
    """Parse asyncpg's command tag (e.g. ``"UPDATE 1"``) into a row count."""
    try:
        return int(str(command_tag).split()[-1])
    except (ValueError, IndexError):
        return 0
