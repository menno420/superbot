"""Invariant — every registered Explore world maps to a real subsystem.

The federated Explore world hub (spine PR 1, `services/world_registry.py` +
`views/explore/world_hub.py`) is **registry-driven**: each subsystem registers a
`WorldEntry`, and the hub renders one button per entry. A world whose `key`
doesn't correspond to a real `SUBSYSTEMS` entry would render a button that looks
valid but is backed by nothing — a silent dead end. This invariant catches that
at CI time, the same way `test_command_synonyms_resolve_to_real_commands` guards
the synonym map.

Why a test and not a `check_*.py` script: the registry is **code** (openers are
callables), not a generated JSON artifact, so a pytest invariant — which already
has `disbot` importable and runs in CI — is the right home (the `check_*.py`
scripts validate generated artifacts).
"""

from __future__ import annotations

from types import SimpleNamespace

import discord
import pytest

from services.world_registry import (
    clear_world_entries,
    get_world_entries,
)
from utils.subsystem_registry import SUBSYSTEMS
from views.explore.world_hub import (
    ExploreWorldHubView,
    ensure_default_world_entries,
)


@pytest.fixture(autouse=True)
def _clean_registry():
    clear_world_entries()
    ensure_default_world_entries()
    yield
    clear_world_entries()


def test_every_registered_world_key_is_a_real_subsystem():
    """A registered world's key must resolve to a SUBSYSTEMS entry.

    Otherwise the hub renders a button for a game that doesn't exist — the
    silent dead-end this invariant exists to prevent.
    """
    orphans = [e.key for e in get_world_entries() if e.key not in SUBSYSTEMS]
    assert not orphans, (
        f"Explore world entries reference unknown subsystem key(s): {orphans}. "
        f"Register the world under a real SUBSYSTEMS key, or add the subsystem."
    )


def test_every_world_entry_has_display_fields():
    """Each entry needs a non-empty label/emoji/description for the button + embed."""
    for entry in get_world_entries():
        assert entry.label.strip(), f"world {entry.key!r} has a blank label"
        assert entry.emoji.strip(), f"world {entry.key!r} has a blank emoji"
        assert entry.description.strip(), f"world {entry.key!r} has a blank description"


def test_hub_buttons_have_unique_custom_ids():
    """No two world buttons may collide on custom_id (Discord rejects dupes)."""
    author = SimpleNamespace(id=1, name="A", display_name="A")
    view = ExploreWorldHubView(author, 123)
    ids = [
        c.custom_id
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id
    ]
    assert len(ids) == len(set(ids)), f"duplicate world button custom_ids: {ids}"


def test_builtin_worlds_present():
    """The two built-in worlds (mining · fishing) are registered by default."""
    keys = {e.key for e in get_world_entries()}
    assert {"mining", "fishing"} <= keys
