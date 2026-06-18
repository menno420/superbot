"""Stdlib signed-cookie session for the dashboard — no third-party deps.

Deliberately avoids ``itsdangerous`` / a session middleware so the whole app is
verifiable with only ``fastapi`` + ``jinja2`` installed (the dashboard test suite
must run locally to catch template bugs — the #979 lesson). It is the same idea a
signing library uses: an HMAC-SHA256 signature over a base64url JSON payload. A
tampered, unsigned, or malformed cookie reads back as an **empty** session, so a
forged cookie can never inject identity — and the bot re-checks every write anyway.

The signing key is ``DASHBOARD_SESSION_SECRET`` in production; a per-process random
fallback keeps local/dormant runs working (sessions simply don't survive a restart
without the real secret).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from typing import Any

COOKIE_NAME = "sb_session"
_MAX_AGE = 60 * 60 * 24 * 7  # one week
_FALLBACK_SECRET = secrets.token_hex(32)


def _secret() -> bytes:
    return (os.environ.get("DASHBOARD_SESSION_SECRET") or _FALLBACK_SECRET).encode()


def _sign(payload: bytes) -> str:
    return hmac.new(_secret(), payload, hashlib.sha256).hexdigest()


def encode(data: dict[str, Any]) -> str:
    """Serialise ``data`` to a signed cookie value."""
    raw = base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode())
    return f"{raw.decode()}.{_sign(raw)}"


def decode(cookie: str | None) -> dict[str, Any]:
    """Read a signed cookie back to a dict; ``{}`` if absent/tampered/malformed."""
    if not cookie or "." not in cookie:
        return {}
    raw_str, _, signature = cookie.rpartition(".")
    raw = raw_str.encode()
    if not hmac.compare_digest(signature, _sign(raw)):
        return {}
    try:
        data = json.loads(base64.urlsafe_b64decode(raw))
    except (ValueError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def read(request: Any) -> dict[str, Any]:
    """The session dict carried by the request cookie (empty if none)."""
    return decode(request.cookies.get(COOKIE_NAME))


def write(response: Any, data: dict[str, Any]) -> None:
    """Persist ``data`` onto ``response`` as the signed session cookie."""
    response.set_cookie(
        COOKIE_NAME,
        encode(data),
        max_age=_MAX_AGE,
        httponly=True,
        samesite="lax",
        path="/",
    )


def clear(response: Any) -> None:
    """Delete the session cookie (sign-out)."""
    response.delete_cookie(COOKIE_NAME, path="/")
