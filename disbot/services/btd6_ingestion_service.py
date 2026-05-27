"""BTD6 ingestion orchestration service.

Drives the fetch → snapshot → parse → store cycle for registered
BTD6 data sources.  DB writes go through utils.db.btd6_sources;
this module contains no raw SQL.

Each source fetch is protected by a per-(source_key, path_params_hash)
asyncio Lock.  The lock check is best-effort: if the lock is already
held when checked, the call is recorded as 'skipped' and returns
immediately.  The async with block below the check guarantees the
lock is always released on every exit path.

Dependency chains (e.g. CT index → CT tiles) are driven by
refresh_with_dependencies().  Child fetches use entity_key values
from the current index run's written_entity_keys — not stale DB rows.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from services import (
    btd6_fact_store,
    btd6_fetch_service,
    btd6_source_parser,
    btd6_source_registry,
)
from services import (  # noqa: F401  — triggers registration side-effects
    parsers as _parsers_pkg,
)
from utils.db import btd6_sources as btd6_sources_db

logger = logging.getLogger("bot.services.btd6_ingestion")


# ---------------------------------------------------------------------------
# Shared types
# ---------------------------------------------------------------------------


IngestionReason = Literal["scheduled", "manual", "dependency"]


@dataclass(frozen=True)
class IngestionResult:
    source_key: str
    status: Literal[
        "ok",
        "fetch_error",
        "parse_error",
        "store_error",
        "skipped",
        "disabled",
        "interrupted",
    ]
    fact_count: int
    duration_ms: int
    error_code: str | None
    run_id: int | None
    written_entity_keys: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Per-(source_key, path_params_hash) lock registry
# ---------------------------------------------------------------------------

_locks: dict[tuple[str, str], asyncio.Lock] = {}
_locks_mutex = asyncio.Lock()


async def _lock_for(source_key: str, path_params_hash: str) -> asyncio.Lock:
    key = (source_key, path_params_hash)
    async with _locks_mutex:
        if key not in _locks:
            _locks[key] = asyncio.Lock()
        return _locks[key]


# ---------------------------------------------------------------------------
# Core refresh
# ---------------------------------------------------------------------------


async def refresh_source(
    source_key: str,
    *,
    path_params: dict[str, str] | None = None,
    reason: IngestionReason = "scheduled",
    started_by_user_id: int | None = None,
) -> IngestionResult:
    start_ms = time.monotonic()

    # 1. Resolve source row.
    source_row = await btd6_source_registry.get_by_key(source_key)
    if source_row is None:
        return IngestionResult(
            source_key=source_key,
            status="disabled",
            fact_count=0,
            duration_ms=0,
            error_code="source_not_registered",
            run_id=None,
        )

    # 2. Compute path_params_hash.
    if path_params is not None:
        path_params_hash = hashlib.sha256(
            json.dumps(path_params, sort_keys=True).encode(),
        ).hexdigest()
    else:
        path_params_hash = ""

    # 3. Best-effort lock check — not atomic; skipping is optimistic.
    lock = await _lock_for(source_key, path_params_hash)
    if lock.locked():
        run_id = await btd6_sources_db.insert_ingestion_run(
            source_key=source_key,
            status="skipped",
            triggered_by=reason,
            path_params_json=path_params,
            started_by_user_id=started_by_user_id,
        )
        return IngestionResult(
            source_key=source_key,
            status="skipped",
            fact_count=0,
            duration_ms=int((time.monotonic() - start_ms) * 1000),
            error_code=None,
            run_id=run_id,
        )

    async with lock:
        run_id = await btd6_sources_db.insert_ingestion_run(
            source_key=source_key,
            status="running",
            triggered_by=reason,
            path_params_json=path_params,
            started_by_user_id=started_by_user_id,
        )
        try:
            return await _run_ingestion(
                source_key=source_key,
                source_row=source_row,
                path_params=path_params,
                path_params_hash=path_params_hash,
                run_id=run_id,
                reason=reason,
                started_by_user_id=started_by_user_id,
                start_ms=start_ms,
            )
        except asyncio.CancelledError:
            duration_ms = int((time.monotonic() - start_ms) * 1000)
            await btd6_sources_db.update_ingestion_run(
                run_id,
                status="interrupted",
                finished_at=datetime.now(timezone.utc),
                duration_ms=duration_ms,
                error_code="task_cancelled",
            )
            raise


async def _run_ingestion(
    *,
    source_key: str,
    source_row: dict[str, Any],
    path_params: dict[str, str] | None,
    path_params_hash: str,
    run_id: int,
    reason: str,
    started_by_user_id: int | None,
    start_ms: float,
) -> IngestionResult:
    source_id = int(source_row["id"])

    def _elapsed() -> int:
        return int((time.monotonic() - start_ms) * 1000)

    async def _fail(
        status: str,
        error_code: str,
        error_message: str | None = None,
        status_code: int | None = None,
    ) -> IngestionResult:
        await btd6_sources_db.update_ingestion_run(
            run_id,
            status=status,
            finished_at=datetime.now(timezone.utc),
            duration_ms=_elapsed(),
            error_code=error_code,
            error_message=error_message,
            status_code=status_code,
        )
        return IngestionResult(
            source_key=source_key,
            status=status,  # type: ignore[arg-type]
            fact_count=0,
            duration_ms=_elapsed(),
            error_code=error_code,
            run_id=run_id,
        )

    # 5. Fetch.
    try:
        fetch_result = await btd6_fetch_service.fetch(
            source_key,
            path_params=path_params,
        )
    except btd6_fetch_service.BTD6FetchRefusedError as err:
        return await _fail("disabled", err.reason)
    except btd6_fetch_service.BTD6FetchHTTPError as err:
        return await _fail(
            "fetch_error",
            str(err.status_code),
            status_code=err.status_code,
        )
    except Exception as err:
        return await _fail("fetch_error", "unexpected_fetch_error", str(err))

    # 6. Write snapshot.
    try:
        await btd6_sources_db.insert_source_snapshot(
            source_id=source_id,
            status_code=fetch_result.status_code,
            raw_body_hash=fetch_result.raw_body_hash,
            raw_body=fetch_result.raw_body,
        )
    except Exception:
        logger.warning(
            "snapshot write failed for %s run %d",
            source_key,
            run_id,
            exc_info=True,
        )

    # 7. Look up parser.
    parser = btd6_source_parser.get(source_key)
    if parser is None:
        return await _fail("parse_error", "no_parser")

    # 8. JSON-decode body.
    try:
        payload = json.loads(fetch_result.raw_body)
    except json.JSONDecodeError:
        return await _fail("parse_error", "invalid_json")

    # 9. Parse.
    try:
        facts = parser.parse(payload, game_version=None, path_params=path_params)
    except Exception as err:
        return await _fail("parse_error", "parse_exception", str(err))

    # 10. Store.
    try:
        results = await btd6_fact_store.store_facts(facts, default_source_id=source_id)
    except Exception as err:
        return await _fail("store_error", "store_exception", str(err))

    # 11. Update run to ok.
    duration_ms = _elapsed()
    await btd6_sources_db.update_ingestion_run(
        run_id,
        status="ok",
        finished_at=datetime.now(timezone.utc),
        duration_ms=duration_ms,
        fact_count=len(results),
        raw_body_hash=fetch_result.raw_body_hash,
        status_code=fetch_result.status_code,
        path_params_hash=path_params_hash or None,
    )

    # 12. Return result.
    return IngestionResult(
        source_key=source_key,
        status="ok",
        fact_count=len(results),
        duration_ms=duration_ms,
        error_code=None,
        run_id=run_id,
        written_entity_keys=tuple(r.entity_key for r in results),
    )


# ---------------------------------------------------------------------------
# Dependency chains (PR 3)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _DependencySpec:
    child_source: str
    path_param_builder: Callable[[str], dict[str, str]]


_DEPENDENCY_CHAINS: dict[str, list[_DependencySpec]] = {
    "nk_btd6_ct": [
        _DependencySpec(
            child_source="nk_btd6_ct_tiles",
            path_param_builder=lambda ct_id: {"ctID": ct_id},
        ),
    ],
    # nk_btd6_races: added in next PR
    # nk_btd6_bosses, nk_btd6_odyssey: deferred (multi-param path builders needed)
}


async def refresh_with_dependencies(
    source_key: str,
    *,
    reason: IngestionReason = "scheduled",
    started_by_user_id: int | None = None,
) -> list[IngestionResult]:
    """Refresh a source and any declared child sources.

    Child fetches use entity_key values from the current index run —
    not stale DB rows — so only IDs present in the latest fetch are expanded.

    Children inherit the parent's ``reason`` and ``started_by_user_id`` so
    audit queries against ``btd6_ingestion_runs`` see the whole chain as a
    single operator-triggered (or scheduled) operation.
    """
    results: list[IngestionResult] = []
    index_result = await refresh_source(
        source_key,
        reason=reason,
        started_by_user_id=started_by_user_id,
    )
    results.append(index_result)
    if index_result.status != "ok":
        return results
    specs = _DEPENDENCY_CHAINS.get(source_key, [])
    for spec in specs:
        for entity_key in index_result.written_entity_keys:
            path_params = spec.path_param_builder(entity_key)
            child = await refresh_source(
                spec.child_source,
                path_params=path_params,
                reason=reason,
                started_by_user_id=started_by_user_id,
            )
            results.append(child)
    return results


async def refresh_source_or_dependencies(
    source_key: str,
    *,
    reason: IngestionReason = "scheduled",
    started_by_user_id: int | None = None,
) -> list[IngestionResult]:
    """Single public entry point for command surfaces.

    Sources with a declared dependency chain go through
    :func:`refresh_with_dependencies` (returning parent + children);
    others return a one-item list with the direct refresh result. Unknown
    source keys yield a structured ``status="disabled"`` /
    ``error_code="source_not_registered"`` result rather than raising.
    """
    if source_key in _DEPENDENCY_CHAINS:
        return await refresh_with_dependencies(
            source_key,
            reason=reason,
            started_by_user_id=started_by_user_id,
        )
    return [
        await refresh_source(
            source_key,
            reason=reason,
            started_by_user_id=started_by_user_id,
        ),
    ]


__all__ = [
    "IngestionReason",
    "IngestionResult",
    "refresh_source",
    "refresh_source_or_dependencies",
    "refresh_with_dependencies",
]
