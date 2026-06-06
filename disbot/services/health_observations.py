"""Pure classification + grouping primitives for operational health.

PR4 of the bot-awareness programme.  Deliberately **stdlib-only** (plus the
dependency-light :mod:`services.health_contracts`) so it is import-safe and
cycle-free: ``services.health_snapshot_service`` imports *this* module — never
the reverse.

It owns three things:

* the free-text redaction regexes + :func:`normalize_text` — the single source
  of truth used both by the aggregator's ``_scrub`` and by fingerprinting, so a
  secret / ID / traceback is stripped the same way everywhere;
* :func:`fingerprint` — a deterministic, ID-free grouping key
  (``<category>:<subsystem>:<operation>:<exc-type>[:<code>]``);
* :func:`group_log_errors` — collapse a bounded stream of recent log records
  into a few counted :class:`~services.health_contracts.OperationalHealthFinding`
  objects so a flood of identical errors reads as one finding with a count.

Nothing here performs I/O or mutation.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from services.health_contracts import FindingSeverity, OperationalHealthFinding

# Default bound for a single normalized free-text span.  Kept in sync with
# ``health_snapshot_service.MAX_MESSAGE_CHARS`` (which passes its own limit
# explicitly); this default only applies to direct callers.
_DEFAULT_LIMIT = 180

# ---------------------------------------------------------------------------
# Redaction — strips secrets, JWTs/hashes, snowflake IDs, and flattens
# multi-line tracebacks from ANY free text before it can enter a finding,
# a fingerprint, an embed, or AI context.  (``project_for_audience`` then
# removes owner-only *fields* on top of this.)
# ---------------------------------------------------------------------------

_SECRET_RE = re.compile(
    r"(?i)\b(token|secret|password|passwd|api[_-]?key|authorization|bearer)\b"
    r"\s*[=:]\s*\S+",
)
_JWT_RE = re.compile(
    r"\b[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{6,}\.[A-Za-z0-9_\-]{10,}\b",
)
_LONG_HEX_RE = re.compile(r"\b[A-Fa-f0-9]{24,}\b")
_LONG_DIGITS_RE = re.compile(r"\d{7,}")


def normalize_text(text: str | None, *, limit: int = _DEFAULT_LIMIT) -> str:
    """Collapse, redact, and bound free text.

    Removes ``key=value`` secrets, JWT-like and long-hex blobs, and long
    digit runs (Discord snowflake IDs), flattens newlines so multi-line
    tracebacks cannot survive, and truncates to ``limit`` chars.
    """
    if not text:
        return ""
    flattened = " ".join(str(text).split())
    flattened = _SECRET_RE.sub("<secret>", flattened)
    flattened = _JWT_RE.sub("<token>", flattened)
    flattened = _LONG_HEX_RE.sub("<hash>", flattened)
    flattened = _LONG_DIGITS_RE.sub("<id>", flattened)
    if len(flattened) > limit:
        flattened = flattened[: limit - 1].rstrip() + "…"
    return flattened


# ---------------------------------------------------------------------------
# Fingerprinting — a deterministic grouping key with no volatile parts.
# ---------------------------------------------------------------------------

_TOKEN_CLEAN_RE = re.compile(r"[^a-z0-9]+")
_SEGMENT_CHARS = 48
# An exception class name embedded in a free-text log message.
_EXC_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Warning))\b")


def _segment(value: str | None, *, default: str = "unknown") -> str:
    """Normalize one fingerprint segment.

    Redacts (so IDs/secrets never enter a key), lowercases, collapses any
    run of non-alphanumerics to a single ``_``, and bounds the length.
    """
    text = normalize_text(value, limit=_SEGMENT_CHARS)
    token = _TOKEN_CLEAN_RE.sub("_", text.lower()).strip("_")
    return token or default


def fingerprint(
    *,
    category: str,
    subsystem: str,
    operation: str,
    exc_type: str,
    code: str | None = None,
) -> str:
    """Deterministic, ID-free grouping key.

    ``<category>:<subsystem>:<operation>:<exc-type>[:<code>]`` — every
    segment normalized, so the same problem groups across occurrences while
    distinct problems stay distinct, and no raw ID / secret survives.
    """
    parts = [
        _segment(category),
        _segment(subsystem),
        _segment(operation),
        _segment(exc_type, default="error"),
    ]
    if code:
        parts.append(_segment(code))
    return ":".join(parts)


def classify_log_message(message: str) -> tuple[str, str]:
    """Return ``(exc_type, stem)`` for a raw log message.

    ``exc_type`` is the first ``*Error`` / ``*Exception`` / ``*Warning``
    token (or ``"LogError"`` when none is present); ``stem`` is a normalized,
    ID-free summary used to keep genuinely-different messages in different
    groups.  Neither carries a raw ID, secret, or traceback.
    """
    raw = message or ""
    match = _EXC_RE.search(raw)
    exc_type = match.group(1) if match else "LogError"
    stem = normalize_text(raw, limit=80)
    return exc_type, stem


# ---------------------------------------------------------------------------
# Grouping — collapse a bounded recent-error stream into counted findings.
# ---------------------------------------------------------------------------

_MAX_GROUPS = 5


def group_log_errors(
    entries: Iterable[Mapping[str, Any]],
    *,
    subsystem: str = "errors",
    max_findings: int = _MAX_GROUPS,
) -> list[OperationalHealthFinding]:
    """Collapse recent log records into a few counted findings.

    Records sharing a :func:`fingerprint` (exception type + normalized
    message stem) are grouped; ``occurrence_count`` is how many collapsed.
    The displayed ``message`` is normalized (IDs/secrets/traces stripped) and
    never enters the fingerprint verbatim.  Returns at most ``max_findings``
    findings, busiest first.
    """
    groups: dict[str, dict[str, Any]] = {}
    for entry in entries:
        message = (
            str(entry.get("message", "")) if isinstance(entry, Mapping) else str(entry)
        )
        if not message.strip():
            continue
        exc_type, stem = classify_log_message(message)
        key = fingerprint(
            category="runtime.log_error",
            subsystem=subsystem,
            operation=stem,
            exc_type=exc_type,
        )
        group = groups.get(key)
        if group is None:
            groups[key] = {"sample": message, "count": 1}
        else:
            group["count"] += 1
    findings = [
        OperationalHealthFinding(
            fingerprint=key,
            severity=FindingSeverity.ERROR,
            category="runtime.log_error",
            message=normalize_text(group["sample"]),
            occurrence_count=group["count"],
            related_subsystem=subsystem,
            source="log_buffer",
        )
        for key, group in groups.items()
    ]
    findings.sort(key=lambda f: (-f.occurrence_count, f.fingerprint))
    return findings[:max_findings]
