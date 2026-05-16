"""Per-session breadcrumb navigation stack.

State is persisted via state_store so navigation survives bot restarts.
Each entry is a (screen_id, data_dict) pair.

Concurrency
-----------
Push/pop/root are read-modify-write against state_store.  A pair of
concurrent interactions for the same session (two double-clicks, a
modal submit racing a button click) would otherwise both read the same
stack, both mutate their local copy, and the second write would silently
lose the first mutation.

To prevent this we hold a per-session ``asyncio.Lock`` for the duration
of every push/pop/root.  Locks are created lazily on first use and may
be released with :func:`forget` when the session ends (callers that
manage session lifecycle should invoke this for cleanup; otherwise the
locks expire with the process).

Public surface:
    push(session_id, screen_id, data)  → None
    pop(session_id)                    → ScreenState | None
    current(session_id)                → ScreenState | None  (read-only)
    root(session_id)                   → None  (clear stack)
    depth(session_id)                  → int  (read-only)
    forget(session_id)                 → None (drop the lock)
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from core.runtime import state_store

logger = logging.getLogger("bot.runtime.nav")

_STACK_KEY = "nav_stack"

# Per-session locks for push/pop/root.  Created lazily; freed via forget().
_locks: dict[str, asyncio.Lock] = {}


def _lock_for(session_id: str) -> asyncio.Lock:
    """Return the lock for *session_id*, creating it on first use."""
    lock = _locks.get(session_id)
    if lock is None:
        lock = asyncio.Lock()
        _locks[session_id] = lock
    return lock


def forget(session_id: str) -> None:
    """Drop the in-process lock for *session_id*.

    Safe to call when the lock is held (the holding coroutine still
    completes); subsequent accesses will create a fresh lock.  Intended
    for session-end cleanup so the lock dict cannot grow unbounded.
    """
    _locks.pop(session_id, None)


@dataclass
class ScreenState:
    """One entry in the navigation stack."""

    screen_id: str
    data: dict = field(default_factory=dict)


async def push(session_id: str, screen_id: str, data: dict | None = None) -> None:
    """Push a new screen onto the stack for *session_id*."""
    async with _lock_for(session_id):
        stack = await _get_stack(session_id)
        stack.append({"screen_id": screen_id, "data": data or {}})
        await state_store.set(session_id, _STACK_KEY, stack)
        logger.debug(
            "Nav push | session=%s | screen=%s | depth=%d",
            session_id,
            screen_id,
            len(stack),
        )


async def pop(session_id: str) -> ScreenState | None:
    """Pop and return the top screen, or ``None`` if the stack is empty."""
    async with _lock_for(session_id):
        stack = await _get_stack(session_id)
        if not stack:
            return None
        item = stack.pop()
        await state_store.set(session_id, _STACK_KEY, stack)
        logger.debug(
            "Nav pop | session=%s | screen=%s | remaining=%d",
            session_id,
            item["screen_id"],
            len(stack),
        )
        return ScreenState(screen_id=item["screen_id"], data=item.get("data", {}))


async def current(session_id: str) -> ScreenState | None:
    """Return the top screen without modifying the stack, or ``None``."""
    # Read-only — no lock needed (state_store.get is a single SELECT).
    stack = await _get_stack(session_id)
    if not stack:
        return None
    item = stack[-1]
    return ScreenState(screen_id=item["screen_id"], data=item.get("data", {}))


async def root(session_id: str) -> None:
    """Clear the navigation stack — user returns to the root screen."""
    async with _lock_for(session_id):
        await state_store.delete(session_id, _STACK_KEY)
        logger.debug("Nav root | session=%s", session_id)


async def depth(session_id: str) -> int:
    """Return the current stack depth (0 = at root)."""
    # Read-only — no lock needed.
    stack = await _get_stack(session_id)
    return len(stack)


async def _get_stack(session_id: str) -> list:
    value = await state_store.get(session_id, _STACK_KEY)
    if not isinstance(value, list):
        return []
    return value
