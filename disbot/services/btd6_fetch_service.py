"""Single HTTP chokepoint for BTD6 source fetches.

M3A ships the seam: a fetch request is refused unless the source is
registered in ``btd6_source_registry``, has ``enabled=TRUE``, and
carries a non-null ``base_url``. M3A does not actually issue an HTTP
request — the real client lands in M3B after base URL + per-endpoint
response formats are confirmed.

The pin test ``tests/unit/runtime/test_no_untrusted_fetches.py``
ensures every BTD6 service module that needs HTTP routes through
this file; if you find yourself reaching for ``httpx`` / ``aiohttp``
elsewhere in ``disbot/services/btd6_*.py`` you are bypassing the
allowlist.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from services import btd6_source_registry

logger = logging.getLogger("bot.services.btd6_fetch")


class BTD6FetchRefused(Exception):
    """Raised when the registry says the source can't be fetched."""

    def __init__(self, source_key: str, reason: str) -> None:
        super().__init__(f"refused fetch for {source_key!r}: {reason}")
        self.source_key = source_key
        self.reason = reason


@dataclass(frozen=True)
class FetchResult:
    source_key: str
    status_code: int
    raw_body: str


async def fetch(
    source_key: str,
    *,
    path_params: dict[str, Any] | None = None,
) -> FetchResult:
    """Validate the source then perform the HTTP request.

    M3A intentionally raises ``BTD6FetchRefused`` for every call —
    the seam exists so callers can be written today; real HTTP work
    lands in M3B with rate-limiting, backoff, and circuit-breaker
    metrics.
    """
    usable, reason = await btd6_source_registry.is_source_usable(source_key)
    if not usable:
        raise BTD6FetchRefused(source_key, reason)

    logger.warning(
        "btd6_fetch_service: M3A seam refusing live fetch for %s — "
        "M3B will wire the real HTTP client",
        source_key,
    )
    raise BTD6FetchRefused(source_key, "fetcher_unwired_in_m3a")


__all__ = ["BTD6FetchRefused", "FetchResult", "fetch"]
