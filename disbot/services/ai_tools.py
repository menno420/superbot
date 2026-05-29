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
from services import (
    ai_config_projection_service,
    ai_decision_audit_service,
    ai_permission_service,
)

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


# --- get_guild_ai_config (admin) ---------------------------------------

_GUILD_AI_CONFIG_SPEC = AIToolSpec(
    name="get_guild_ai_config",
    description=(
        "Return this server's AI configuration: whether AI and natural-"
        "language replies are enabled, the active provider and model, the "
        "minimum level and cooldown, and the memory window. Admin only. "
        "Use this to answer questions about how the bot is set up here."
    ),
    parameters=_NO_ARGS_SCHEMA,
    min_scope=AIScope.ADMIN,
)


def _make_guild_ai_config(guild_id: int) -> ToolHandler:
    async def handler(_arguments: dict[str, Any]) -> dict[str, Any]:
        snap = await ai_config_projection_service.build_snapshot(guild_id)
        return {
            "ai_enabled": snap.policy.enabled,
            "natural_language_enabled": snap.policy.natural_language_enabled,
            "provider": snap.policy.default_provider or snap.provider.provider_active,
            "model": snap.policy.default_model,
            "minimum_level": snap.policy.minimum_level_default,
            "cooldown_seconds": snap.policy.cooldown_seconds,
            "memory_window_minutes": snap.memory.window_minutes,
        }

    return handler


# --- recent_audit (admin) ----------------------------------------------

_RECENT_AUDIT_SPEC = AIToolSpec(
    name="recent_audit",
    description=(
        "Return the most recent AI decision-audit rows for this server — "
        "what the bot decided to do with recent messages and why. Admin "
        "only. Use to explain recent AI behaviour, e.g. why the bot did or "
        "did not reply."
    ),
    parameters={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "description": "How many recent rows to return (default 5).",
            },
        },
        "additionalProperties": False,
    },
    min_scope=AIScope.ADMIN,
)


def _make_recent_audit(guild_id: int) -> ToolHandler:
    async def handler(arguments: dict[str, Any]) -> dict[str, Any]:
        limit = _coerce_limit(arguments.get("limit"), default=5, lo=1, hi=20)
        rows = await ai_decision_audit_service.query(guild_id, limit=limit)
        return {"rows": [_audit_row_summary(row) for row in rows]}

    return handler


def _coerce_limit(value: Any, *, default: int, lo: int, hi: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, parsed))


def _audit_row_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": row.get("decision"),
        "reason": row.get("reason_code"),
        "task": row.get("task"),
        "at": _ts(row.get("created_at")),
    }


def _ts(value: Any) -> str | None:
    if value is None:
        return None
    iso = getattr(value, "isoformat", None)
    return iso() if callable(iso) else str(value)


# --- btd6_lookup -------------------------------------------------------

_BTD6_LOOKUP_SPEC = AIToolSpec(
    name="btd6_lookup",
    description=(
        "Look up verified Bloons TD 6 (BTD6) data: tower and hero stats and "
        "costs, bloon properties and immunities (camo, lead, ceramic, "
        "MOAB-class), maps, modes, rounds, and current live events. Call this "
        "for ANY question about BTD6 before answering — even when no specific "
        "tower, hero, or bloon is named — so the answer is grounded in real "
        "data instead of memory. Returns found=false when nothing matched; "
        "treat that as 'no verified data available'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "The BTD6 question, or a focused sub-query naming the "
                    "tower / hero / bloon / topic to look up."
                ),
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)

# Cap returned grounding lines so one chatty entity can't blow the token budget.
_BTD6_LOOKUP_FACT_CAP = 25


async def _btd6_lookup(arguments: dict[str, Any]) -> dict[str, Any]:
    query = str(arguments.get("query") or "").strip()
    if not query:
        return {"found": False, "facts": [], "note": "empty query"}
    # Lazy import: btd6_context_service pulls the BTD6 data layer, which we do
    # not want to load unless the model actually asks for a lookup.
    from services import btd6_context_service

    ctx = await btd6_context_service.build(query)
    facts = list(ctx.facts[:_BTD6_LOOKUP_FACT_CAP])
    return {"found": bool(facts), "facts": facts, "source": ctx.source_summary}


# --- btd6_capability_lookup --------------------------------------------

_BTD6_CAPABILITY_SPEC = AIToolSpec(
    name="btd6_capability_lookup",
    description=(
        "List which BTD6 towers have a capability — use for 'which tower …' "
        "discovery questions that do NOT name a specific tower. Supported "
        "capabilities: 'camo_detection' (can target Camo bloons) and "
        "'lead_popping' (can damage Lead bloons). Set unupgraded=true (the "
        "default) for base 0-0-0 only — the usual 'without upgrades' question "
        "— or false to also include towers that gain it from an upgrade. "
        "Returns the matching towers and where each gets the capability."
    ),
    parameters={
        "type": "object",
        "properties": {
            "capability": {
                "type": "string",
                "description": "One of: camo_detection, lead_popping.",
            },
            "unupgraded": {
                "type": "boolean",
                "description": (
                    "Base (0-0-0) only when true (default); include "
                    "upgrade-granted towers when false."
                ),
            },
        },
        "required": ["capability"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


async def _btd6_capability_lookup(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_capability_service

    capability = str(arguments.get("capability") or "").strip().lower()
    if capability not in btd6_capability_service.CAPABILITIES:
        return {
            "found": False,
            "note": (
                "unsupported capability; supported: "
                + ", ".join(btd6_capability_service.CAPABILITIES)
            ),
        }
    raw = arguments.get("unupgraded", True)
    unupgraded = True if raw is None else bool(raw)
    hits = btd6_capability_service.towers_with_capability(
        capability,
        unupgraded=unupgraded,
    )
    return {
        "found": bool(hits),
        "capability": capability,
        "unupgraded": unupgraded,
        "towers": [
            {"id": h.tower_id, "name": h.canonical, "detail": h.detail} for h in hits
        ],
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
        (_BTD6_LOOKUP_SPEC, _btd6_lookup),
        (_BTD6_CAPABILITY_SPEC, _btd6_capability_lookup),
        (_GUILD_AI_CONFIG_SPEC, _make_guild_ai_config(guild_id)),
        (_RECENT_AUDIT_SPEC, _make_recent_audit(guild_id)),
    ]
    specs: list[AIToolSpec] = []
    handlers: dict[str, ToolHandler] = {}
    for spec, handler in catalog:
        if _scope_allows(scope, spec.min_scope):
            specs.append(spec)
            handlers[spec.name] = handler
    return ToolRegistry(specs=tuple(specs), handlers=handlers)


__all__ = ["ToolRegistry", "build_registry"]
