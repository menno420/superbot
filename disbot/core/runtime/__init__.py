"""core/runtime — Platform orchestration layer.

Provides the infrastructure that separates concern between:
  - cogs   (subsystem business logic, action handlers)
  - runtime (session lifecycle, interaction routing, governance gating)

Public aliases:
    router   — interaction_router module
    sessions — session_manager module
    store    — state_store module
    perms    — ui_permissions module

EventBus subscriptions are established in setup(), called once from bot1.py
after the DB is initialised.
"""

from __future__ import annotations

import logging

from core.runtime import interaction_router as router  # noqa: F401 — re-exported
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
