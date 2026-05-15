"""core/runtime — Platform orchestration layer.

Provides the infrastructure that separates concern between:
  - cogs   (subsystem business logic, action handlers)
  - runtime (session lifecycle, interaction routing, governance gating)

Public aliases:
    router     — interaction_router module
    sessions   — session_manager module
    store      — state_store module
    perms      — ui_permissions module
    components — component_registry module
    nav        — navigation_stack module
    surfaces   — ephemeral_surface_manager module
    scheduler  — live_update_scheduler module

EventBus subscriptions are established in setup(), called once from bot1.py
after the DB is initialised.
"""

from __future__ import annotations

import logging

from core.runtime import component_registry as components  # noqa: F401 — re-exported
from core.runtime import (  # noqa: F401 — re-exported
    ephemeral_surface_manager as surfaces,
)
from core.runtime import interaction_router as router  # noqa: F401 — re-exported
from core.runtime import live_update_scheduler as scheduler  # noqa: F401 — re-exported
from core.runtime import message_anchor_manager as anchors  # noqa: F401 — re-exported
from core.runtime import navigation_stack as nav  # noqa: F401 — re-exported
from core.runtime import panel_manager as panels  # noqa: F401 — re-exported
from core.runtime import persistent_views  # noqa: F401 — re-exported
from core.runtime import session_gc as gc  # noqa: F401 — re-exported
from core.runtime import session_manager as sessions  # noqa: F401 — re-exported
from core.runtime import state_store as store  # noqa: F401 — re-exported
from core.runtime import ui_permissions as perms  # noqa: F401 — re-exported

logger = logging.getLogger("bot.runtime")


async def setup() -> None:
    """Wire EventBus subscriptions for the runtime layer.

    Must be called once during bot startup, after db.init() has run.
    Idempotent — safe to call more than once (handlers accumulate but are
    scoped to this module's functions, not lambdas, so duplication is benign).
    """
    from core.events import bus
    from services.governance_service import (
        EVT_CACHE_INVALIDATED,
        EVT_VISIBILITY_CHANGED,
    )

    async def _on_visibility_changed(
        guild_id: int, subsystem: str, **_: object
    ) -> None:
        await sessions.invalidate_subsystem_sessions(guild_id, subsystem)

    async def _on_cache_invalidated(guild_id: int, **_: object) -> None:
        await store.invalidate_guild_state(guild_id)

    bus.on(EVT_VISIBILITY_CHANGED, _on_visibility_changed)
    bus.on(EVT_CACHE_INVALIDATED, _on_cache_invalidated)

    logger.info("Runtime layer initialised — EventBus subscriptions active.")
