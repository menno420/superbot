"""core/runtime — Platform orchestration layer.

Provides the infrastructure that separates concern between:
  - cogs   (subsystem business logic, action handlers)
  - runtime (session lifecycle, interaction routing, governance gating)

Public aliases:
    router       — interaction_router module
    sessions     — session_manager module
    store        — state_store module
    perms        — ui_permissions module
    components   — component_registry module
    nav          — navigation_stack module
    surfaces     — ephemeral_surface_manager module
    scheduler    — live_update_scheduler module
    tasks        — managed background-task helper (see CRIT-1 fix)
    interaction  — safe_defer / safe_followup / safe_edit (see CRIT-2 fix)
    guild_config — F-1 cached-config primitive (Phase S1.1) — use the
                   typed accessors in utils.guild_config_accessors
    scope_locks  — F-2 per-scope asyncio.Lock primitive (Phase S1.2) —
                   pair with the V/M/A pattern in §"Realtime / event-
                   driven systems"

EventBus subscriptions are established in setup(), called once from bot1.py
after the DB is initialised.
"""

from __future__ import annotations

import logging

from core.runtime import component_registry as components  # noqa: F401 — re-exported
from core.runtime import (  # noqa: F401 — re-exported
    ephemeral_surface_manager as surfaces,
)
from core.runtime import guild_config  # noqa: F401 — re-exported
from core.runtime import persistent_views  # noqa: F401 — re-exported
from core.runtime import scope_locks  # noqa: F401 — re-exported
from core.runtime import tasks  # noqa: F401 — re-exported
from core.runtime import guild_resources as resources  # noqa: F401 — re-exported
from core.runtime import interaction_helpers as interaction  # noqa: F401 — re-exported
from core.runtime import interaction_router as router  # noqa: F401 — re-exported
from core.runtime import live_update_scheduler as scheduler  # noqa: F401 — re-exported
from core.runtime import message_anchor_manager as anchors  # noqa: F401 — re-exported
from core.runtime import navigation_stack as nav  # noqa: F401 — re-exported
from core.runtime import panel_manager as panels  # noqa: F401 — re-exported
from core.runtime import session_gc as gc  # noqa: F401 — re-exported
from core.runtime import session_manager as sessions  # noqa: F401 — re-exported
from core.runtime import state_store as store  # noqa: F401 — re-exported
from core.runtime import ui_permissions as perms  # noqa: F401 — re-exported

logger = logging.getLogger("bot.runtime")

# Guard: setup() must be idempotent.  A second call (e.g. hot-reload or test
# re-entry) must not register duplicate EventBus handlers — inner functions are
# closures and have distinct object identities on every call, so bus.on() would
# append them as separate handlers, causing double-execution.
_SETUP_DONE: bool = False


async def setup() -> None:
    """Wire EventBus subscriptions for the runtime layer.

    Must be called once during bot startup, after db.init() has run.
    Subsequent calls are no-ops (idempotency guard prevents double registration).
    """
    global _SETUP_DONE
    if _SETUP_DONE:
        logger.debug("runtime.setup() called again — skipping (already initialised).")
        return
    _SETUP_DONE = True

    from core.events import bus
    from services.governance_service import (
        EVT_CACHE_INVALIDATED,
        EVT_CLEANUP_CHANGED,
        EVT_VISIBILITY_CHANGED,
    )

    async def _on_visibility_changed(
        guild_id: int,
        subsystem: str,
        scope_type: str = "guild",
        scope_id: int | None = None,
        **_: object,
    ) -> None:
        """Scope-aware session invalidation (Phase 2.3).

        For channel-scoped changes we only invalidate sessions in the affected
        channel.  For guild-scoped (or unknown scope) we fall back to full
        guild-subsystem invalidation to be safe.
        """
        channel_id: int | None = None
        if (
            scope_type == "channel"
            and scope_id is not None
            or scope_type == "thread"
            and scope_id is not None
        ):
            channel_id = scope_id

        await sessions.invalidate_subsystem_sessions(
            guild_id,
            subsystem,
            channel_id=channel_id,
        )

    async def _on_cache_invalidated(guild_id: int, **_: object) -> None:
        await store.invalidate_guild_state(guild_id)

    async def _on_cleanup_changed(
        guild_id: int,
        scope_type: str = "guild",
        scope_id: int | None = None,
        **_: object,
    ) -> None:
        """Subscription hook for EVT_CLEANUP_CHANGED (DEBT-003).

        Cleanup policy is currently resolved uncached (governance/cleanup.py
        queries the DB on every call).  This handler exists so any future
        cleanup-policy cache MUST register its invalidation here rather than
        introducing a parallel invalidation path.

        The GovernanceMutationPipeline already calls invalidate_guild_cache()
        and emits EVT_CACHE_INVALIDATED inside set_cleanup_policy, so the
        in-process visibility cache is already coherent — this hook covers
        only future cleanup-specific caching.
        """
        logger.debug(
            "EVT_CLEANUP_CHANGED received | guild=%d scope=%s/%s — "
            "no cleanup cache present, hook reserved for future use",
            guild_id,
            scope_type,
            scope_id,
        )

    bus.on(EVT_VISIBILITY_CHANGED, _on_visibility_changed)
    bus.on(EVT_CACHE_INVALIDATED, _on_cache_invalidated)
    bus.on(EVT_CLEANUP_CHANGED, _on_cleanup_changed)

    logger.info("Runtime layer initialised — EventBus subscriptions active.")
