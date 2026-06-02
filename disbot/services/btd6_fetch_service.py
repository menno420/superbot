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
import re
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


@dataclass(frozen=True)
class BreakerState:
    """Immutable snapshot of one open circuit breaker."""

    source_key: str
    failures: int
    open_until: float
    seconds_remaining: float


# ---------------------------------------------------------------------------
# Rate limiting + circuit breaker (per source_key)
# ---------------------------------------------------------------------------


_DEFAULT_REQUEST_TIMEOUT = 15.0
_DEFAULT_MIN_INTERVAL = 1.0  # seconds between back-to-back fetches per source
_DEFAULT_BREAKER_THRESHOLD = 5

# PR2 is page-1-only by design. Bounded explicit pagination is deferred
# to a follow-up — this guard fires before any registry lookup or HTTP
# call so leaderboard / list endpoints cannot crawl pages.
_ONLY_ALLOWED_PAGE = 1

# Matches an unresolved ``:varName`` placeholder remaining in a path
# after substitution. Anchored on a leading slash so it does not match
# the ``://`` in ``https://``. Word characters keep camelCase intact.
_UNRESOLVED_PATH_PARAM = re.compile(r"/:([A-Za-z][A-Za-z0-9_]*)")

_LAST_REQUEST_AT: dict[str, float] = defaultdict(float)
_FAILURES: dict[str, int] = defaultdict(int)
_BREAKER_OPEN_UNTIL: dict[str, float] = defaultdict(float)


def _reset_for_tests() -> None:
    _LAST_REQUEST_AT.clear()
    _FAILURES.clear()
    _BREAKER_OPEN_UNTIL.clear()


def breaker_status() -> tuple[BreakerState, ...]:
    """Immutable snapshot of currently-open circuit breakers.

    Reads the in-memory breaker maps **without mutating them**: iterates
    ``.items()`` and uses ``.get()`` rather than ``_FAILURES[key]`` /
    ``_BREAKER_OPEN_UNTIL[key]``, which (being ``defaultdict``s) would
    materialise phantom zero entries on read. Only breakers open *now*
    are returned, sorted by source_key, so the operator readiness reader
    can never perturb fetcher state.
    """
    now = time.time()
    out: list[BreakerState] = []
    for source_key, open_until in _BREAKER_OPEN_UNTIL.items():
        if open_until > now:
            out.append(
                BreakerState(
                    source_key=source_key,
                    failures=_FAILURES.get(source_key, 0),
                    open_until=open_until,
                    seconds_remaining=open_until - now,
                ),
            )
    return tuple(sorted(out, key=lambda b: b.source_key))


async def fetch(
    source_key: str,
    *,
    path_params: dict[str, str] | None = None,
    page: int = 1,
    timeout: float = _DEFAULT_REQUEST_TIMEOUT,
) -> FetchResult:
    """Fetch ``source_key`` from its registered URL.

    ``page`` must be ``1``; PR2 supports page-1-only fetches. Any
    other value raises :class:`BTD6FetchRefusedError` with reason
    ``paging_cap`` before any registry lookup or HTTP call. Bounded
    explicit pagination is deferred to a follow-up.

    Raises :class:`BTD6FetchRefusedError` for any allowlist failure
    (including the circuit breaker being open, paging cap, or
    unresolved path placeholders) and :class:`BTD6FetchHTTPError` for
    an upstream non-2xx response.
    """
    if page != _ONLY_ALLOWED_PAGE:
        raise BTD6FetchRefusedError(source_key, "paging_cap")

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
    # After substitution any remaining ``/:varName`` placeholder is a
    # caller bug (forgot a path_param); never let it reach the wire.
    if _UNRESOLVED_PATH_PARAM.search(url):
        raise BTD6FetchRefusedError(source_key, "missing_path_param")

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


async def fetch_url_bytes(url: str, *, timeout: float = 10.0) -> bytes:
    """Fetch raw bytes from an operator-configured URL (BTD6 cloud data).

    A narrow second chokepoint so the *only* module issuing outbound HTTP stays
    ``btd6_fetch_service`` (pinned by ``test_no_untrusted_fetches``). Unlike
    :func:`fetch`, this does **not** consult the source registry — the URL is
    operator-configured (``BTD6_DATA_BASE_URL``), not user- or registry-driven —
    so it is used solely by ``CloudRawProvider`` to pull our own fixtures.
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
        session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp,
    ):
        data = await resp.read()
        if resp.status >= 400:
            detail = data[:200].decode("utf-8", "replace")
            raise BTD6FetchHTTPError("(http)", resp.status, detail)
        return data


__all__ = [
    "BTD6FetchHTTPError",
    "BTD6FetchRefusedError",
    "BreakerState",
    "FetchResult",
    "breaker_status",
    "fetch",
    "fetch_url_bytes",
]
