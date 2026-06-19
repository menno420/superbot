"""INSERT-only submissions store for the public bot site.

The public marketing bot site's **only** write is the ``/submit`` intake: a
validated form INSERTs one ``pending`` row into the **dashboard-owned** submissions
Postgres (plan §2.3 / §4.4). This module is that single write path — it can
``insert_pending`` and **nothing else**. It deliberately cannot read, list, update,
or delete: a full compromise of the public site cannot exfiltrate submissions,
reach GitHub, or touch the bot. Least privilege is enforced *twice* — by this
module's surface (INSERT-only) and by the DB role the owner grants its DSN.

The schema is the single contract in ``botsite/migrations/001_submissions.sql``;
this module shares **only that contract** with ``dashboard/submissions_db.py`` (the
read/moderate side) — never code (plan §2.2 / §5).

**Dormant by default.** When ``SUBMISSIONS_DB_DSN`` is not set, :func:`is_configured`
is ``False`` and :func:`insert_pending` raises :class:`SubmissionsNotConfiguredError`; the
``/submit`` route shows a "submissions are temporarily unavailable" state rather than
erroring. Nothing here connects to anything until the owner sets the DSN on the
public Railway service at rollout (plan §6).

Decoupling: this module is part of the web tier and never imports ``disbot``. It
uses ``asyncpg`` directly against its own DSN — it is NOT the bot's ``utils.db``
seam (that rule is scoped to the bot's Postgres + ``disbot/``). ``asyncpg`` is
lazy-imported so the module (and the bot-site app that imports it) loads even where
the driver is absent.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any

# The two intake kinds (must match the DDL CHECK + the GitHub issue-template shapes).
KIND_BUG = "bug"
KIND_SUGGESTION = "suggestion"
VALID_KINDS: frozenset[str] = frozenset({KIND_BUG, KIND_SUGGESTION})

# Server-side length caps (plan §4.2 — validation + sanitation). Mirrored by the
# form, but enforced here so a hand-crafted POST can never store an oversized blob.
MAX_TITLE_LEN = 200
MAX_BODY_LEN = 8_000
MAX_SURFACE_LEN = 80
MAX_CONTACT_LEN = 200

_DSN_ENV = "SUBMISSIONS_DB_DSN"
# Salt for the source-IP hash. A dedicated env keeps the salt out of the codebase;
# a per-process fallback still yields a usable within-run dedup key when unset
# (the hash is for abuse forensics, not identity — plan §2.3 / §4.2).
_IP_SALT_ENV = "SUBMISSIONS_IP_SALT"
_FALLBACK_SALT = os.urandom(16).hex()


class SubmissionsNotConfiguredError(RuntimeError):
    """Raised by :func:`insert_pending` when ``SUBMISSIONS_DB_DSN`` is unset."""


class SubmissionValidationError(ValueError):
    """Raised when a submission fails server-side validation (bad kind / empty)."""


def dsn() -> str | None:
    """Return the submissions DB DSN, or ``None`` when the store is dormant."""
    value = os.environ.get(_DSN_ENV, "").strip()
    return value or None


def is_configured() -> bool:
    """``True`` when the submissions DB DSN is set (the store is live)."""
    return dsn() is not None


def hash_ip(raw_ip: str | None) -> str | None:
    """Return a **salted** hash of ``raw_ip`` for abuse forensics — never the raw IP.

    Plan §2.3 / §4.2: we store ``source_ip_hash`` only, so the moderation view and
    any forensic dedup work on a pseudonymous token, not a real address. Returns
    ``None`` for an empty/unknown IP so the column stays NULL rather than hashing "".
    """
    if not raw_ip:
        return None
    salt = (os.environ.get(_IP_SALT_ENV, "").strip() or _FALLBACK_SALT).encode()
    return hmac.new(salt, raw_ip.encode("utf-8"), hashlib.sha256).hexdigest()


def _clean(text: str | None, limit: int) -> str | None:
    r"""Trim, drop control characters, and length-cap a free-text field.

    Returns ``None`` for an empty/whitespace-only result so optional columns stay
    NULL. Control characters (other than ``\n`` / ``\t``) are stripped so a crafted
    payload can't smuggle terminal escapes into the owner's moderation view.
    """
    if text is None:
        return None
    # Keep newlines + tabs; drop other C0/C1 control chars.
    cleaned = "".join(
        ch for ch in text if ch in ("\n", "\t") or (ch >= " " and ch != "\x7f")
    ).strip()
    if not cleaned:
        return None
    return cleaned[:limit]


def build_insert(
    *,
    kind: str,
    title: str,
    body: str,
    surface: str | None = None,
    contact: str | None = None,
    source_ip: str | None = None,
) -> tuple[str, tuple[Any, ...]]:
    """Validate + sanitise a submission and build its parametrised INSERT.

    Pure (no I/O), so the whole validation contract is unit-testable without a DB:
    returns ``(sql, params)`` where ``params`` is positional for asyncpg's ``$1..``.
    Raises :class:`SubmissionValidationError` on a bad ``kind`` or a missing
    required field (``title`` / ``body``). ``surface`` / ``contact`` are optional
    and stored NULL when blank. The row is always inserted ``status='pending'`` —
    this module physically cannot insert any other status (plan §2.3).
    """
    if kind not in VALID_KINDS:
        raise SubmissionValidationError(
            f"kind must be one of {sorted(VALID_KINDS)}, got {kind!r}",
        )
    clean_title = _clean(title, MAX_TITLE_LEN)
    clean_body = _clean(body, MAX_BODY_LEN)
    if not clean_title:
        raise SubmissionValidationError("title is required")
    if not clean_body:
        raise SubmissionValidationError("body is required")

    sql = (
        "INSERT INTO submissions "
        "(kind, title, body, surface, contact, status, source_ip_hash) "
        "VALUES ($1, $2, $3, $4, $5, 'pending', $6) "
        "RETURNING id"
    )
    params = (
        kind,
        clean_title,
        clean_body,
        _clean(surface, MAX_SURFACE_LEN),
        _clean(contact, MAX_CONTACT_LEN),
        hash_ip(source_ip),
    )
    return sql, params


async def insert_pending(
    *,
    kind: str,
    title: str,
    body: str,
    surface: str | None = None,
    contact: str | None = None,
    source_ip: str | None = None,
) -> int:
    """INSERT one ``pending`` submission and return its new ``id``.

    The single write path of the public site. Validates + sanitises via
    :func:`build_insert`, then opens a short-lived asyncpg connection to the
    submissions DSN and executes the INSERT. Raises :class:`SubmissionsNotConfiguredError`
    when the store is dormant and :class:`SubmissionValidationError` on bad input.
    """
    target = dsn()
    if target is None:
        raise SubmissionsNotConfiguredError(
            f"{_DSN_ENV} is not set — the submissions store is dormant",
        )
    sql, params = build_insert(
        kind=kind,
        title=title,
        body=body,
        surface=surface,
        contact=contact,
        source_ip=source_ip,
    )
    import asyncpg  # lazy — keeps module import-safe where the driver is absent

    conn = await asyncpg.connect(target)
    try:
        new_id = await conn.fetchval(sql, *params)
    finally:
        await conn.close()
    return int(new_id)
