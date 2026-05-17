"""Per-scope asyncio.Lock manager (F-2).

State class: **process-local runtime** — see ``docs/architecture.md``
§"State classification".

Generalizes the proven shape of ``navigation_stack._locks`` so any future
realtime / event-driven cog (counting, tournaments, matchmaking,
reaction games, limited-quantity drops) can serialize its hot-path
mutation under a narrow, per-scope lock without growing yet another
bespoke lock dictionary.

Used in combination with the **Validate / Mutate / Apply** pattern
documented in ``docs/architecture.md`` §"Realtime / event-driven systems":
the lock guards the validate + mutate + persist phase; Discord I/O
happens outside the lock in the apply phase.

``scope_id`` is a caller-defined string with a subsystem prefix so
``!platform locks <prefix>`` (Phase S2.5) can filter:

    counting:channel:{channel_id}
    tournament:{tournament_id}
    matchmaking:{mode}:{guild_id}

Cleanup contract — three paths, only the first is the primary one:

  1. **Explicit ``forget(scope_id)``** on natural scope end (the cog
     contract — e.g. ``end_match``, ``tournament_complete``).
  2. **Per-guild bulk teardown** via registered hooks invoked from
     ``guild_lifecycle.teardown`` on ``on_guild_remove`` — each cog
     that uses scope_locks calls ``register_guild_teardown_hook`` at
     ``cog_load`` to translate its own scope IDs to guild membership.
  3. **Idle eviction** via ``sweep_idle`` from ``session_gc`` —
     unused locks are reclaimed after ``SCOPE_LOCK_IDLE_TTL`` as a
     safety net for missed ``forget`` calls.

Substitution boundary: **stays process-local**.  Distributed locks
(etcd, Postgres advisory locks beyond migration use) are deliberately
out of scope per ADR-001; SuperBot runs as one process by design and
same-process serialisation is exactly what ``asyncio.Lock`` provides.

Public surface:
    lock_for(scope_id)              → _TimedScopeLock (async context manager)
    forget(scope_id)                → None
    register_guild_teardown_hook(h) → None
    teardown_guild(guild_id)        → int
    active_count()                  → int
    stats()                         → ScopeLockStats
    sweep_idle(max_idle_seconds)    → int
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import Counter as _Counter
from collections.abc import Callable
from dataclasses import dataclass
from types import TracebackType

from services import metrics as _metrics

logger = logging.getLogger("bot.runtime.scope_locks")

# Default idle TTL matches session TTL — abandoned locks are reclaimed on
# roughly the same cadence as abandoned sessions.  Tunable via session_gc.
SCOPE_LOCK_IDLE_TTL: float = 7200.0  # 2 h, in seconds

# ---------------------------------------------------------------------------
# Module-level state
# ---------------------------------------------------------------------------

# scope_id → (lock, last_used_monotonic_ts)
_LOCKS: dict[str, tuple[asyncio.Lock, float]] = {}

# Per-cog teardown hooks invoked from guild_lifecycle.teardown.
# Each hook receives a guild_id and returns the count of locks it dropped.
_GUILD_TEARDOWN_HOOKS: list[Callable[[int], int]] = []


@dataclass(frozen=True)
class ScopeLockStats:
    """Snapshot of scope-lock state for ``!platform locks``."""

    total: int
    by_prefix: dict[str, int]
    held_count: int


# ---------------------------------------------------------------------------
# Context manager — instruments wait time as a Prometheus histogram
# ---------------------------------------------------------------------------


class _TimedScopeLock:
    """asyncio.Lock-wrapping context manager that records acquire-wait time."""

    __slots__ = ("_lock", "_prefix")

    def __init__(self, lock: asyncio.Lock, prefix: str) -> None:
        self._lock = lock
        self._prefix = prefix

    async def __aenter__(self) -> _TimedScopeLock:
        start = time.monotonic()
        await self._lock.acquire()
        wait = time.monotonic() - start
        _metrics.scope_locks_wait_seconds.labels(prefix=self._prefix).observe(wait)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._lock.release()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _prefix_of(scope_id: str) -> str:
    """Return the ``:``-delimited prefix or ``'<unprefixed>'`` for ``scope_id``."""
    return scope_id.split(":", 1)[0] if ":" in scope_id else "<unprefixed>"


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


def lock_for(scope_id: str) -> _TimedScopeLock:
    """Return an async context manager for ``scope_id``'s lock, lazily created.

    The returned object acquires the underlying ``asyncio.Lock`` on
    ``__aenter__`` (observing wait time as a Prometheus histogram) and
    releases on ``__aexit__``.

    Usage::

        async with scope_locks.lock_for("counting:channel:123"):
            ...  # validate + mutate + persist
        await ...  # apply (Discord I/O) outside the lock

    The last-used timestamp is refreshed on every call so idle GC will
    not reclaim a scope that is still receiving traffic.
    """
    entry = _LOCKS.get(scope_id)
    if entry is None:
        lock = asyncio.Lock()
        _LOCKS[scope_id] = (lock, time.monotonic())
        _metrics.scope_locks_total.set(len(_LOCKS))
    else:
        lock, _ = entry
        _LOCKS[scope_id] = (lock, time.monotonic())
    return _TimedScopeLock(lock, _prefix_of(scope_id))


def forget(scope_id: str) -> None:
    """Drop the lock for ``scope_id``.

    Safe to call when the lock is held — the holding coroutine still
    completes; subsequent ``lock_for(...)`` calls create a fresh lock.
    Idempotent — no-op when the scope is unknown.

    Cogs MUST call this on natural scope end (end_match,
    tournament_complete, channel deletion, etc.).
    """
    if _LOCKS.pop(scope_id, None) is not None:
        _metrics.scope_locks_total.set(len(_LOCKS))


def register_guild_teardown_hook(hook: Callable[[int], int]) -> None:
    """Register a hook called from ``guild_lifecycle.teardown``.

    The hook receives ``guild_id`` and returns the count of locks it
    dropped.  Cogs that use scope_locks register one hook each at
    ``cog_load`` time so the (scope_id → guild_id) mapping stays with
    the cog that knows it (counting knows ``counting:channel:{cid}`` is
    in the guild that owns channel ``cid``; scope_locks itself does
    not).
    """
    _GUILD_TEARDOWN_HOOKS.append(hook)


def teardown_guild(guild_id: int) -> int:
    """Invoke every registered guild-teardown hook for ``guild_id``.

    Returns the total count of locks removed across all hooks.  Hook
    failures are logged but do not abort sibling hooks (consistent
    with ``guild_lifecycle``'s best-effort discipline).
    """
    total = 0
    for hook in _GUILD_TEARDOWN_HOOKS:
        try:
            total += hook(guild_id)
        except Exception as exc:
            logger.warning(
                "scope_locks teardown hook failed for guild=%d: %s",
                guild_id,
                exc,
            )
    return total


def active_count() -> int:
    """Return the number of scope locks currently tracked."""
    return len(_LOCKS)


def stats() -> ScopeLockStats:
    """Point-in-time snapshot for ``!platform locks``."""
    by_prefix: _Counter[str] = _Counter()
    held = 0
    for scope_id, (lock, _ts) in _LOCKS.items():
        by_prefix[_prefix_of(scope_id)] += 1
        if lock.locked():
            held += 1
    return ScopeLockStats(
        total=len(_LOCKS),
        by_prefix=dict(by_prefix),
        held_count=held,
    )


def sweep_idle(max_idle_seconds: float = SCOPE_LOCK_IDLE_TTL) -> int:
    """Drop unused locks last touched more than ``max_idle_seconds`` ago.

    Called from ``session_gc._run_gc_loop`` as a safety net for cogs
    that missed a ``forget`` call on edge paths (channel deleted via
    mod, bot kicked from channel, etc.).

    Held locks are never reclaimed — only locks whose holder has
    finished AND whose last_used timestamp is past the cutoff.

    Returns the count removed.
    """
    cutoff = time.monotonic() - max_idle_seconds
    drop = [
        scope_id
        for scope_id, (lock, ts) in _LOCKS.items()
        if not lock.locked() and ts < cutoff
    ]
    for k in drop:
        _LOCKS.pop(k, None)
    if drop:
        _metrics.scope_locks_total.set(len(_LOCKS))
        _metrics.scope_locks_idle_swept_total.inc(len(drop))
        logger.debug("scope_locks.sweep_idle: removed %d idle lock(s)", len(drop))
    return len(drop)


# ---------------------------------------------------------------------------
# Test surface — module-state reset.  Not used in production.
# ---------------------------------------------------------------------------


def _reset_for_tests() -> None:
    """Wipe module state.  Tests call this in their setup/teardown fixture."""
    _LOCKS.clear()
    _GUILD_TEARDOWN_HOOKS.clear()
