"""Unit tests for :mod:`services.world_registry` — the federated world seam.

Pins the registry contract the Explore hub (and future pets/survival worlds)
depend on: idempotent registration, de-dup by key, deterministic ordering, and
the test-only reset helper.
"""

from __future__ import annotations

import pytest

from services.world_registry import (
    WorldEntry,
    clear_world_entries,
    get_world_entries,
    get_world_entry,
    register_world_entry,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    """Isolate every test — the registry is module-level global state."""
    clear_world_entries()
    yield
    clear_world_entries()


def _entry(key: str, *, order: int = 100, label: str | None = None) -> WorldEntry:
    return WorldEntry(
        key=key,
        label=label or key.title(),
        emoji="🎮",
        description=f"the {key} world",
        order=order,
    )


def test_register_and_get_roundtrip():
    assert register_world_entry(_entry("mining")) is True
    fetched = get_world_entry("mining")
    assert fetched is not None
    assert fetched.key == "mining"


def test_register_is_idempotent_by_key():
    first = _entry("mining", label="Mine")
    second = _entry("mining", label="Different")
    assert register_world_entry(first) is True
    # Re-registering the same key is a no-op (returns False), keeps the first.
    assert register_world_entry(second) is False
    assert get_world_entry("mining").label == "Mine"


def test_replace_overwrites_when_asked():
    register_world_entry(_entry("mining", label="Mine"))
    assert register_world_entry(_entry("mining", label="New"), replace=True) is True
    assert get_world_entry("mining").label == "New"


def test_entries_sorted_by_order_then_label():
    register_world_entry(_entry("fishing", order=20, label="Fish"))
    register_world_entry(_entry("mining", order=10, label="Mine"))
    register_world_entry(_entry("pets", order=10, label="Adopt"))
    keys = [e.key for e in get_world_entries()]
    # order 10 before 20; within order 10, "Adopt" sorts before "Mine".
    assert keys == ["pets", "mining", "fishing"]


def test_get_missing_returns_none():
    assert get_world_entry("nope") is None


def test_clear_empties_the_registry():
    register_world_entry(_entry("mining"))
    clear_world_entries()
    assert get_world_entries() == []


def test_opener_defaults_to_none():
    entry = _entry("mining")
    assert entry.opener is None
