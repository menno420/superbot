"""Explore — the federated open-world hub package.

The top-level "town square" the player walks out into, routing them into each
registered game's own world (Mine · Fish · …). The world list is driven by
``services.world_registry`` so a new world docks in by registering an entry,
never by editing the hub.

Plan: ``docs/planning/explore-hub-federated-world-plan-2026-06-19.md`` (PR 1).
"""

from __future__ import annotations

from views.explore.world_hub import (
    ExploreWorldHubView,
    build_world_hub_embed,
    ensure_default_world_entries,
)

__all__ = [
    "ExploreWorldHubView",
    "build_world_hub_embed",
    "ensure_default_world_entries",
]
