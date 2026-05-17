"""Tests for core.runtime.scope_locks — F-2 per-scope lock primitive."""

from __future__ import annotations

import asyncio

import pytest

from core.runtime import scope_locks


@pytest.fixture(autouse=True)
def _reset():
    scope_locks._reset_for_tests()
    yield
    scope_locks._reset_for_tests()


# ---------------------------------------------------------------------------
# lock_for + forget
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lock_for_creates_lock_on_first_use():
    assert scope_locks.active_count() == 0
    async with scope_locks.lock_for("counting:channel:1"):
        assert scope_locks.active_count() == 1


@pytest.mark.asyncio
async def test_lock_for_returns_same_lock_on_repeat():
    cm1 = scope_locks.lock_for("counting:channel:1")
    cm2 = scope_locks.lock_for("counting:channel:1")
    # Same underlying asyncio.Lock instance (the wrapper is fresh per call).
    assert cm1._lock is cm2._lock


@pytest.mark.asyncio
async def test_lock_for_different_scopes_are_independent():
    async with scope_locks.lock_for("counting:channel:1"):
        async with scope_locks.lock_for("counting:channel:2"):
            assert scope_locks.active_count() == 2


@pytest.mark.asyncio
async def test_concurrent_lock_acquires_for_same_scope_serialize():
    events: list[str] = []

    async def worker(label: str) -> None:
        async with scope_locks.lock_for("counting:channel:1"):
            events.append(f"{label}:enter")
            await asyncio.sleep(0.01)
            events.append(f"{label}:exit")

    await asyncio.gather(worker("A"), worker("B"), worker("C"))
    # Each worker's enter is immediately followed by its exit — no interleave.
    pairs = [(events[i], events[i + 1]) for i in range(0, len(events), 2)]
    for enter, exit_ in pairs:
        assert enter.endswith(":enter")
        assert exit_.endswith(":exit")
        assert enter.split(":")[0] == exit_.split(":")[0]


@pytest.mark.asyncio
async def test_concurrent_lock_acquires_for_different_scopes_overlap():
    events: list[str] = []

    async def worker(scope: str, label: str) -> None:
        async with scope_locks.lock_for(scope):
            events.append(f"{label}:enter")
            await asyncio.sleep(0.02)
            events.append(f"{label}:exit")

    await asyncio.gather(
        worker("counting:channel:1", "A"),
        worker("counting:channel:2", "B"),
    )
    # Both enter before either exits — independent scopes do not serialize.
    assert events.index("A:enter") < events.index("A:exit")
    assert events.index("B:enter") < events.index("B:exit")
    assert events.index("A:enter") < events.index("B:exit")
    assert events.index("B:enter") < events.index("A:exit")


def test_forget_drops_lock():
    scope_locks.lock_for("counting:channel:1")
    assert scope_locks.active_count() == 1
    scope_locks.forget("counting:channel:1")
    assert scope_locks.active_count() == 0


def test_forget_unknown_scope_is_noop():
    scope_locks.forget("nothing:here")
    assert scope_locks.active_count() == 0


@pytest.mark.asyncio
async def test_forget_while_held_is_safe():
    """The holding coroutine still completes; subsequent lock_for creates fresh."""
    held = asyncio.Event()
    can_release = asyncio.Event()

    async def holder() -> None:
        async with scope_locks.lock_for("counting:channel:1"):
            held.set()
            await can_release.wait()

    task = asyncio.create_task(holder())
    await held.wait()
    # Forget while the lock is held.
    scope_locks.forget("counting:channel:1")
    assert scope_locks.active_count() == 0
    can_release.set()
    await task  # must complete cleanly
    # A subsequent lock_for re-creates the entry.
    scope_locks.lock_for("counting:channel:1")
    assert scope_locks.active_count() == 1


# ---------------------------------------------------------------------------
# stats / by-prefix grouping
# ---------------------------------------------------------------------------


def test_stats_groups_by_prefix():
    scope_locks.lock_for("counting:channel:1")
    scope_locks.lock_for("counting:channel:2")
    scope_locks.lock_for("tournament:42")
    scope_locks.lock_for("unprefixed_scope")
    s = scope_locks.stats()
    assert s.total == 4
    assert s.by_prefix == {
        "counting": 2,
        "tournament": 1,
        "<unprefixed>": 1,
    }
    assert s.held_count == 0


@pytest.mark.asyncio
async def test_stats_held_count_reflects_held_locks():
    held = asyncio.Event()
    can_release = asyncio.Event()

    async def holder() -> None:
        async with scope_locks.lock_for("counting:channel:1"):
            held.set()
            await can_release.wait()

    task = asyncio.create_task(holder())
    await held.wait()
    assert scope_locks.stats().held_count == 1
    can_release.set()
    await task


# ---------------------------------------------------------------------------
# sweep_idle
# ---------------------------------------------------------------------------


def test_sweep_idle_drops_unused_locks_past_cutoff():
    scope_locks.lock_for("counting:channel:1")
    scope_locks.lock_for("counting:channel:2")
    # Backdate both entries past the cutoff.
    import time as _t

    backdate_by = 10_000.0
    for k, (lock, ts) in list(scope_locks._LOCKS.items()):
        scope_locks._LOCKS[k] = (lock, ts - backdate_by)
    removed = scope_locks.sweep_idle(max_idle_seconds=1.0)
    assert removed == 2
    assert scope_locks.active_count() == 0


def test_sweep_idle_preserves_recently_used_locks():
    scope_locks.lock_for("counting:channel:1")
    removed = scope_locks.sweep_idle(max_idle_seconds=1.0)
    assert removed == 0
    assert scope_locks.active_count() == 1


@pytest.mark.asyncio
async def test_sweep_idle_never_drops_held_locks():
    held = asyncio.Event()
    can_release = asyncio.Event()

    async def holder() -> None:
        async with scope_locks.lock_for("counting:channel:1"):
            held.set()
            await can_release.wait()

    task = asyncio.create_task(holder())
    await held.wait()
    # Backdate the entry so it WOULD be swept if it weren't held.
    for k, (lock, ts) in list(scope_locks._LOCKS.items()):
        scope_locks._LOCKS[k] = (lock, ts - 10_000.0)
    removed = scope_locks.sweep_idle(max_idle_seconds=1.0)
    assert removed == 0  # held lock is never reclaimed
    can_release.set()
    await task


def test_lock_for_refreshes_last_used_timestamp():
    scope_locks.lock_for("counting:channel:1")
    # Backdate.
    for k, (lock, ts) in list(scope_locks._LOCKS.items()):
        scope_locks._LOCKS[k] = (lock, ts - 10_000.0)
    # Touching the scope again refreshes the timestamp.
    scope_locks.lock_for("counting:channel:1")
    removed = scope_locks.sweep_idle(max_idle_seconds=1.0)
    assert removed == 0


# ---------------------------------------------------------------------------
# guild teardown hooks
# ---------------------------------------------------------------------------


def test_register_and_invoke_guild_teardown_hook():
    invocations: list[int] = []

    def hook(guild_id: int) -> int:
        invocations.append(guild_id)
        return 3  # pretend we dropped 3 locks

    scope_locks.register_guild_teardown_hook(hook)
    removed = scope_locks.teardown_guild(123)
    assert invocations == [123]
    assert removed == 3


def test_teardown_guild_fans_out_to_multiple_hooks():
    def hook_a(_: int) -> int:
        return 1

    def hook_b(_: int) -> int:
        return 2

    scope_locks.register_guild_teardown_hook(hook_a)
    scope_locks.register_guild_teardown_hook(hook_b)
    assert scope_locks.teardown_guild(99) == 3


def test_teardown_guild_continues_on_hook_failure():
    def bad_hook(_: int) -> int:
        raise RuntimeError("teardown crashed")

    def good_hook(_: int) -> int:
        return 5

    scope_locks.register_guild_teardown_hook(bad_hook)
    scope_locks.register_guild_teardown_hook(good_hook)
    # Sibling hook must still run despite the bad one raising.
    assert scope_locks.teardown_guild(7) == 5


def test_teardown_guild_with_no_hooks_returns_zero():
    assert scope_locks.teardown_guild(1) == 0
