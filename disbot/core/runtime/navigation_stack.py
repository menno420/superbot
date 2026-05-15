"""Per-session breadcrumb navigation stack.

State is persisted via state_store so navigation survives bot restarts.
Each entry is a (screen_id, data_dict) pair.

Public surface:
    push(session_id, screen_id, data)  → None
    pop(session_id)                    → ScreenState | None
    current(session_id)                → ScreenState | None
    root(session_id)                   → None  (clear stack)
    depth(session_id)                  → int
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from core.runtime import state_store

logger = logging.getLogger("bot.runtime.nav")

_STACK_KEY = "nav_stack"


@dataclass
class ScreenState:
    """One entry in the navigation stack."""

    screen_id: str
    data: dict = field(default_factory=dict)


async def push(session_id: str, screen_id: str, data: dict | None = None) -> None:
    """Push a new screen onto the stack for *session_id*."""
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
    stack = await _get_stack(session_id)
    if not stack:
        return None
    item = stack[-1]
    return ScreenState(screen_id=item["screen_id"], data=item.get("data", {}))


async def root(session_id: str) -> None:
    """Clear the navigation stack — user returns to the root screen."""
    await state_store.delete(session_id, _STACK_KEY)
    logger.debug("Nav root | session=%s", session_id)


async def depth(session_id: str) -> int:
    """Return the current stack depth (0 = at root)."""
    stack = await _get_stack(session_id)
    return len(stack)


async def _get_stack(session_id: str) -> list:
    value = await state_store.get(session_id, _STACK_KEY)
    if not isinstance(value, list):
        return []
    return value
