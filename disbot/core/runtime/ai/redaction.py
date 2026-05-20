"""Redaction helpers for future AI request preparation.

Inert scaffold: not imported by production runtime yet.

The future AI gateway should run payloads through these helpers before
provider calls.  Keep the helpers deterministic and conservative: they
should reduce risk without requiring network access or external state.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


_TOKEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "discord_token_like",
        re.compile(
            r"[A-Za-z0-9_-]{23,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,}"
        ),
    ),
    (
        "api_key_like",
        re.compile(r"\b(?:sk|pk|rk|xoxb|ghp)_[A-Za-z0-9_\-]{12,}\b"),
    ),
    (
        "database_url",
        re.compile(r"\b(?:postgres|postgresql)://[^\s]+", re.IGNORECASE),
    ),
    (
        "bearer_token",
        re.compile(r"\bBearer\s+[A-Za-z0-9._\-]+", re.IGNORECASE),
    ),
)

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_URL_QUERY_RE = re.compile(
    r"([?&](?:token|key|secret|password|signature)=)[^&\s]+", re.IGNORECASE
)


@dataclass(frozen=True)
class RedactionResult:
    """Result of redacting one value."""

    value: Any
    replacements: dict[str, int]


def _count(replacements: dict[str, int], key: str) -> None:
    replacements[key] = replacements.get(key, 0) + 1


def redact_text(text: str) -> RedactionResult:
    """Redact sensitive-looking substrings from plain text."""

    replacements: dict[str, int] = {}
    value = text

    for label, pattern in _TOKEN_PATTERNS:

        def _replace_token(_: re.Match[str], *, redaction_label: str = label) -> str:
            _count(replacements, redaction_label)
            return f"[{redaction_label}:redacted]"

        value = pattern.sub(_replace_token, value)

    def _replace_email(_: re.Match[str]) -> str:
        _count(replacements, "email")
        return "[email:redacted]"

    value = _EMAIL_RE.sub(_replace_email, value)

    def _replace_query(match: re.Match[str]) -> str:
        _count(replacements, "url_secret_query")
        return f"{match.group(1)}[redacted]"

    value = _URL_QUERY_RE.sub(_replace_query, value)
    return RedactionResult(value=value, replacements=replacements)


def redact_payload(payload: Any) -> RedactionResult:
    """Recursively redact strings in common JSON-like payloads."""

    replacements: dict[str, int] = {}

    def merge(child: RedactionResult) -> Any:
        for key, count in child.replacements.items():
            replacements[key] = replacements.get(key, 0) + count
        return child.value

    def walk(value: Any) -> Any:
        if isinstance(value, str):
            return merge(redact_text(value))
        if isinstance(value, dict):
            return {str(k): walk(v) for k, v in value.items()}
        if isinstance(value, list):
            return [walk(v) for v in value]
        if isinstance(value, tuple):
            return tuple(walk(v) for v in value)
        return value

    return RedactionResult(value=walk(payload), replacements=replacements)


__all__ = ["RedactionResult", "redact_payload", "redact_text"]
