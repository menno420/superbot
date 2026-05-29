"""Read-only AI tools the model may call during a natural-language turn.

Handlers live in the services layer (not ``core/runtime``) because they
read from other services. For a given request the gateway is handed the
``{name: handler}`` map; the matching :class:`AIToolSpec` objects travel
on the request as pure data. Every tool here is **read-only** and returns
a small, JSON-serialisable dict.

Adding a write-capable tool is deliberately out of scope: mutations must
continue to flow through the deterministic mutation services after
explicit confirmation (see ``docs/ai-service-integration-map.md`` and
``docs/ai-config-ownership.md`` § "Mutation seam"). Tools added here must
stay read-only.

Scope gating: ``build_registry`` only includes a tool when the caller's
:class:`AIScope` satisfies the tool's ``min_scope``. A tool above the
caller's privilege is never offered to the model at all, so the model
cannot even attempt to call it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from core.runtime.ai.contracts import AIScope, AIToolSpec
from core.runtime.ai.providers.base import ToolHandler
from services import ai_permission_service

# Least-privilege ordering for AIScope. A caller may be offered a tool
# when their rank is >= the tool's ``min_scope`` rank.
_SCOPE_RANK: dict[AIScope, int] = {
    AIScope.USER: 0,
    AIScope.MODERATOR: 1,
    AIScope.ADMIN: 2,
    AIScope.SERVER_OWNER: 3,
    AIScope.PLATFORM_OWNER: 4,
    AIScope.SYSTEM: 5,
}

_NO_ARGS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}


def _scope_allows(caller: AIScope, required: AIScope) -> bool:
    """True if ``caller`` is privileged enough to be offered ``required``."""
    return _SCOPE_RANK.get(caller, 0) >= _SCOPE_RANK.get(required, 0)


# --- get_user_standing -------------------------------------------------

_USER_STANDING_SPEC = AIToolSpec(
    name="get_user_standing",
    description=(
        "Return the current user's standing in this server: their XP "
        "level and whether they are a brand-new user. Call this when the "
        "answer depends on who is asking or on their level/permissions."
    ),
    parameters=_NO_ARGS_SCHEMA,
    min_scope=AIScope.USER,
)


def _make_user_standing(guild_id: int, actor_id: int) -> ToolHandler:
    async def handler(_arguments: dict[str, Any]) -> dict[str, Any]:
        snap = await ai_permission_service.snapshot(guild_id, actor_id)
        return {"level": snap.level, "is_new_user": snap.is_fresh_user}

    return handler


# --- get_server_time ---------------------------------------------------

_SERVER_TIME_SPEC = AIToolSpec(
    name="get_server_time",
    description=(
        "Return the bot's current UTC date and time. Call this before "
        "stating or computing anything time-relative (today's date, how "
        "long ago something happened) so the answer is grounded, not "
        "guessed."
    ),
    parameters=_NO_ARGS_SCHEMA,
    min_scope=AIScope.USER,
)


async def _server_time(_arguments: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        "utc": now.isoformat(timespec="seconds"),
        "note": "Authoritative server clock; use instead of guessing dates.",
    }


@dataclass(frozen=True)
class ToolRegistry:
    """The tools offered for one request: specs (data) + live handlers."""

    specs: tuple[AIToolSpec, ...]
    handlers: Mapping[str, ToolHandler]


def build_registry(
    *,
    scope: AIScope,
    guild_id: int,
    actor_id: int,
) -> ToolRegistry:
    """Build the read-only tool set the caller's ``scope`` may be offered.

    ``specs`` are attached to the :class:`AIRequest` (the model sees
    them); ``handlers`` are passed to ``ai_gateway.execute`` as
    ``tool_handlers``. Only tools whose ``min_scope`` the caller
    satisfies are included.
    """
    catalog: list[tuple[AIToolSpec, ToolHandler]] = [
        (_USER_STANDING_SPEC, _make_user_standing(guild_id, actor_id)),
        (_SERVER_TIME_SPEC, _server_time),
    ]
    specs: list[AIToolSpec] = []
    handlers: dict[str, ToolHandler] = {}
    for spec, handler in catalog:
        if _scope_allows(scope, spec.min_scope):
            specs.append(spec)
            handlers[spec.name] = handler
    return ToolRegistry(specs=tuple(specs), handlers=handlers)


__all__ = ["ToolRegistry", "build_registry"]
