"""Tests for core.runtime.navigation_stack — R4 concurrency hardening.

The critical property under test: concurrent push() / pop() calls for
the same session do not corrupt the stack (no lost updates from
read-modify-write races).

We back state_store with an in-memory dict and introduce an explicit
await point inside both ``get`` and ``set`` so a deliberately scheduled
context switch will surface the race if the lock were missing.
"""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from core.runtime import navigation_stack


class _MemoryStore:
    """In-memory state_store substitute with an awaitable on every op."""

    def __init__(self) -> None:
        self.data: dict[tuple[str, str], object] = {}

    async def get(self, session_id: str, key: str) -> object | None:
        # await point to allow another coroutine to interleave
        await asyncio.sleep(0)
        return self.data.get((session_id, key))

    async def set(self, session_id: str, key: str, value: object) -> None:
        await asyncio.sleep(0)
        self.data[(session_id, key)] = value

    async def delete(self, session_id: str, key: str) -> None:
        await asyncio.sleep(0)
        self.data.pop((session_id, key), None)


@pytest.fixture
def _mem_store():
    store = _MemoryStore()
    with (
        patch("core.runtime.state_store.get", new=store.get),
        patch("core.runtime.state_store.set", new=store.set),
        patch("core.runtime.state_store.delete", new=store.delete),
    ):
        # Also wipe any leftover locks from earlier tests.
        navigation_stack._locks.clear()
        yield store
        navigation_stack._locks.clear()


@pytest.mark.asyncio
async def test_push_pop_basic(_mem_store):
    await navigation_stack.push("s1", "home", {"a": 1})
    await navigation_stack.push("s1", "details", {"b": 2})

    top = await navigation_stack.current("s1")
    assert top.screen_id == "details"
    assert top.data == {"b": 2}

    popped = await navigation_stack.pop("s1")
    assert popped.screen_id == "details"
    assert await navigation_stack.depth("s1") == 1


@pytest.mark.asyncio
async def test_concurrent_pushes_do_not_lose_updates(_mem_store):
    """Without the per-session lock, the two pushes would race on the
    read-modify-write of the stack and one would silently overwrite the
    other.  With the lock, both must land.
    """
    await asyncio.gather(
        navigation_stack.push("s1", "a"),
        navigation_stack.push("s1", "b"),
    )
    depth = await navigation_stack.depth("s1")
    assert depth == 2, "concurrent pushes lost an entry (lock missing?)"


@pytest.mark.asyncio
async def test_concurrent_pops_do_not_double_decrement(_mem_store):
    await navigation_stack.push("s1", "a")
    await navigation_stack.push("s1", "b")

    results = await asyncio.gather(
        navigation_stack.pop("s1"),
        navigation_stack.pop("s1"),
    )
    # Both pops returned something different (no double-pop of the same entry).
    screens = {r.screen_id for r in results if r is not None}
    assert screens == {"a", "b"}
    assert await navigation_stack.depth("s1") == 0


@pytest.mark.asyncio
async def test_root_clears_stack(_mem_store):
    await navigation_stack.push("s1", "a")
    await navigation_stack.push("s1", "b")
    await navigation_stack.root("s1")
    assert await navigation_stack.depth("s1") == 0


@pytest.mark.asyncio
async def test_forget_drops_lock(_mem_store):
    await navigation_stack.push("s1", "a")
    assert "s1" in navigation_stack._locks
    navigation_stack.forget("s1")
    assert "s1" not in navigation_stack._locks
    # Subsequent ops create a fresh lock and still work.
    await navigation_stack.push("s1", "b")
    assert "s1" in navigation_stack._locks
