"""HTTP chokepoint for BTD6 source fetches (M3B real client).

M3A shipped this as a refusing seam; M3B replaces the seam with a
real ``aiohttp`` client. Calls still refuse any source that is not
registered / enabled / has a ``base_url``, so the M3A registry seed
(all rows ``enabled=FALSE``) means nothing actually fires until a
human flips a row via :func:`services.btd6_source_mutation.set_enabled`.

The pin test ``tests/unit/runtime/test_no_untrusted_fetches.py``
ensures this is the only BTD6 service module that imports an HTTP
client; the registry is the only allowlist source.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from services import btd6_source_registry

logger = logging.getLogger("bot.services.btd6_fetch")


# ---------------------------------------------------------------------------
# Errors / result types
# ---------------------------------------------------------------------------


class BTD6FetchRefusedError(Exception):
    """Raised when the registry says the source can't be fetched."""

    def __init__(self, source_key: str, reason: str) -> None:
        super().__init__(f"refused fetch for {source_key!r}: {reason}")
        self.source_key = source_key
        self.reason = reason


class BTD6FetchHTTPError(Exception):
    """Raised when the upstream HTTP request fails."""

    def __init__(self, source_key: str, status_code: int, message: str) -> None:
        super().__init__(
            f"{source_key!r} fetch failed: status={status_code} {message}",
        )
        self.source_key = source_key
        self.status_code = status_code


@dataclass(frozen=True)
class FetchResult:
    source_key: str
    status_code: int
    raw_body: str

    @property
    def raw_body_hash(self) -> str:
        return hashlib.sha256(self.raw_body.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Rate limiting + circuit breaker (per source_key)
# ---------------------------------------------------------------------------


_DEFAULT_REQUEST_TIMEOUT = 15.0
_DEFAULT_MIN_INTERVAL = 1.0  # seconds between back-to-back fetches per source
_DEFAULT_BREAKER_THRESHOLD = 5

_LAST_REQUEST_AT: dict[str, float] = defaultdict(float)
_FAILURES: dict[str, int] = defaultdict(int)
_BREAKER_OPEN_UNTIL: dict[str, float] = defaultdict(float)


def _reset_for_tests() -> None:
    _LAST_REQUEST_AT.clear()
    _FAILURES.clear()
    _BREAKER_OPEN_UNTIL.clear()


async def fetch(
    source_key: str,
    *,
    path_params: dict[str, Any] | None = None,
    timeout: float = _DEFAULT_REQUEST_TIMEOUT,
) -> FetchResult:
    """Fetch ``source_key`` from its registered URL.

    Raises :class:`BTD6FetchRefusedError` for any allowlist failure
    (including the circuit breaker being open) and
    :class:`BTD6FetchHTTPError` for an upstream non-2xx response.
    """
    usable, reason = await btd6_source_registry.is_source_usable(source_key)
    if not usable:
        raise BTD6FetchRefusedError(source_key, reason)

    if _BREAKER_OPEN_UNTIL[source_key] > time.time():
        raise BTD6FetchRefusedError(source_key, "circuit_breaker_open")

    # Per-source pacing.
    last = _LAST_REQUEST_AT[source_key]
    wait = max(0.0, _DEFAULT_MIN_INTERVAL - (time.time() - last))
    if wait > 0:
        await asyncio.sleep(wait)

    row = await btd6_source_registry.get_by_key(source_key)
    if row is None:
        raise BTD6FetchRefusedError(source_key, "source_not_registered")
    url = _resolve_url(row, path_params or {})

    try:
        body, status = await _http_get(url, timeout=timeout)
    except BTD6FetchHTTPError:
        _FAILURES[source_key] += 1
        if _FAILURES[source_key] >= _DEFAULT_BREAKER_THRESHOLD:
            _BREAKER_OPEN_UNTIL[source_key] = time.time() + 60.0
        raise
    finally:
        _LAST_REQUEST_AT[source_key] = time.time()

    _FAILURES[source_key] = 0
    _BREAKER_OPEN_UNTIL[source_key] = 0
    return FetchResult(source_key=source_key, status_code=status, raw_body=body)


def _resolve_url(row: dict[str, Any], path_params: dict[str, Any]) -> str:
    template = row.get("full_url") or (
        f"{(row.get('base_url') or '').rstrip('/')}{row.get('path_template') or ''}"
    )
    for key, value in path_params.items():
        template = template.replace(f":{key}", str(value))
    return template


async def _http_get(url: str, *, timeout: float) -> tuple[str, int]:
    """Issue one GET request through ``aiohttp``. Imported lazily so
    test environments that mock the fetcher never need the dep.
    """
    try:
        import aiohttp
    except Exception as exc:  # pragma: no cover - dependency present in prod
        raise BTD6FetchHTTPError(
            "(no_source)",
            0,
            f"aiohttp unavailable: {exc}",
        ) from exc
    async with (
        aiohttp.ClientSession() as session,
        session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=timeout),
        ) as resp,
    ):
        text = await resp.text()
        if resp.status >= 400:
            raise BTD6FetchHTTPError("(http)", resp.status, text[:200])
        return text, resp.status


__all__ = [
    "BTD6FetchHTTPError",
    "BTD6FetchRefusedError",
    "FetchResult",
    "fetch",
]
