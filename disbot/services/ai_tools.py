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
        "Return the asking user's standing in THIS server: their Discord "
        "permission role (server_owner / administrator / moderator / regular "
        "member) with owner/admin flags, plus their XP level and whether they "
        "are a brand-new user. This is the authoritative live answer for "
        "'what are my permissions / am I an admin / am I the owner'. It also "
        "reports is_bot_owner — whether the asker is THIS bot's verified "
        "owner/operator. Call it when the answer depends on who is asking, "
        "their permissions, or their level."
    ),
    parameters=_NO_ARGS_SCHEMA,
    min_scope=AIScope.USER,
)


def _make_user_standing(
    guild_id: int,
    actor_id: int,
    member: Any = None,
) -> ToolHandler:
    async def handler(_arguments: dict[str, Any]) -> dict[str, Any]:
        snap = await ai_permission_service.snapshot(guild_id, actor_id)
        result: dict[str, Any] = {
            "level": snap.level,
            "is_new_user": snap.is_fresh_user,
        }
        # Resolve the Discord permission standing from the live member using
        # the SAME resolver the bot_user_identity span uses, so the tool can
        # never contradict the span. Without this the tool returned only XP
        # data and the model inferred "no admin status" from its silence —
        # telling a server owner they were a regular member.
        if member is not None:
            from services.bot_knowledge_service import resolve_user_tier

            tier = resolve_user_tier(member)
            result["server_role"] = tier
            result["is_server_owner"] = tier == "server_owner"
            result["has_admin_access"] = tier in ("server_owner", "administrator")
        # Bot-owner recognition, keyed to the authoritative actor id (the live
        # Discord user id), consistent with the bot_user_identity span.
        from config import BOT_OWNER_USER_ID

        result["is_bot_owner"] = (
            BOT_OWNER_USER_ID is not None and actor_id == BOT_OWNER_USER_ID
        )
        return result

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


# --- get_server_overview ----------------------------------------------

_SERVER_OVERVIEW_SPEC = AIToolSpec(
    name="get_server_overview",
    description=(
        "Return a high-level overview of THIS Discord server: its name, "
        "description, owner, creation date, boost status, and how many "
        "text/voice channels, categories, and roles it has. Call this to "
        "answer general 'tell me about this server' questions. (Member "
        "count is included only when member lookups are enabled.)"
    ),
    parameters=_NO_ARGS_SCHEMA,
    min_scope=AIScope.USER,
)


def _make_server_overview(guild: Any, *, include_members: bool) -> ToolHandler:
    async def handler(_arguments: dict[str, Any]) -> dict[str, Any]:
        from services import guild_introspection_service

        return guild_introspection_service.server_overview(
            guild,
            include_members=include_members,
        )

    return handler


# --- list_server_roles -------------------------------------------------

_SERVER_ROLES_SPEC = AIToolSpec(
    name="list_server_roles",
    description=(
        "List the roles in THIS server, highest first, with a short "
        "privilege summary (administrator / which manage-permissions / "
        "none) and whether each is hoisted or mentionable. Call this to "
        "answer questions about the server's roles or permission "
        "structure. (Per-role member counts appear only when member "
        "lookups are enabled.)"
    ),
    parameters=_NO_ARGS_SCHEMA,
    min_scope=AIScope.USER,
)


def _make_list_roles(guild: Any, *, include_member_counts: bool) -> ToolHandler:
    async def handler(_arguments: dict[str, Any]) -> dict[str, Any]:
        from services import guild_introspection_service

        return guild_introspection_service.list_roles(
            guild,
            include_member_counts=include_member_counts,
        )

    return handler


# --- list_server_channels ----------------------------------------------

_SERVER_CHANNELS_SPEC = AIToolSpec(
    name="list_server_channels",
    description=(
        "List the text and voice channels in THIS server that the asking "
        "user can see, grouped by category, with each channel's topic when "
        "set. Channels the asker cannot view are omitted. Call this to "
        "answer questions about the server's channels or layout."
    ),
    parameters=_NO_ARGS_SCHEMA,
    min_scope=AIScope.USER,
)


def _make_list_channels(guild: Any, member: Any) -> ToolHandler:
    async def handler(_arguments: dict[str, Any]) -> dict[str, Any]:
        from services import guild_introspection_service

        return guild_introspection_service.list_channels(guild, member)

    return handler


# --- lookup_member (opt-in) --------------------------------------------

_MEMBER_LOOKUP_SPEC = AIToolSpec(
    name="lookup_member",
    description=(
        "Find members of THIS server whose display name or username "
        "matches a query, returning each match's display name, join date, "
        "whether they are a bot or the owner, and their roles. Use for "
        "'who is X' / 'what roles does X have' questions. Returns "
        "found=false when nothing matches."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Name or partial name of the member to look up.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


def _make_lookup_member(guild: Any, member: Any) -> ToolHandler:
    async def handler(arguments: dict[str, Any]) -> dict[str, Any]:
        from services import guild_introspection_service

        return guild_introspection_service.lookup_member(
            guild,
            str(arguments.get("query") or ""),
            requester=member,
        )

    return handler


# --- list_all_members (opt-in) -----------------------------------------

_MEMBER_LIST_SPEC = AIToolSpec(
    name="list_all_members",
    description=(
        "List ALL members of THIS server at once, each with their permission "
        "tier (owner / administrator / moderator / member), whether they are a "
        "bot, and their roles. Use this for 'list everyone', 'who are all the "
        "members', or 'show every member and their permissions' — it is the "
        "full-roster companion to lookup_member's by-name search. Results are "
        "sorted most-privileged first and capped; the response includes total "
        "and truncated so you can say 'showing N of M' when the server is large."
    ),
    parameters=_NO_ARGS_SCHEMA,
    min_scope=AIScope.USER,
)


def _make_list_members(guild: Any) -> ToolHandler:
    async def handler(_arguments: dict[str, Any]) -> dict[str, Any]:
        from services import guild_introspection_service

        return guild_introspection_service.list_members(guild)

    return handler


# --- btd6_lookup -------------------------------------------------------

_BTD6_LOOKUP_SPEC = AIToolSpec(
    name="btd6_lookup",
    description=(
        "Look up verified Bloons TD 6 (BTD6) data: tower and hero stats and "
        "costs; bloon properties, immunities, health, what each bloon spawns "
        "into (the full Red->Blue->Green->Yellow->Pink->...->MOAB-class chain), "
        "and RBE (Red Bloon Equivalent); maps, modes, rounds, current live "
        "events; and Contested Territory (CT) relics and tiles — what each "
        "relic does and which tile it sits on in the active CT event(s). Call "
        "this for ANY question about BTD6 before answering — including 'what "
        "does X pop into', 'how much health/RBE does X have', questions about "
        "the basic bloon tiers, AND any CT relic / tile question ('tell me "
        "about the relics', 'what relics are in the current CT', 'where is "
        "Camo Trap') — even when no specific tower, hero, bloon, or relic is "
        "named, so the answer is grounded in real data instead of memory. "
        "Returns found=false when nothing matched; treat that as 'no verified "
        "data available'."
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
        "capabilities: 'camo_detection' (can target Camo bloons), "
        "'lead_popping', 'black_popping', 'white_popping', and "
        "'purple_popping' (can damage Lead / Black / White / Purple bloons). "
        "Set unupgraded=true (the default) for base 0-0-0 only — the usual "
        "'without upgrades' question — or false to also include towers that "
        "gain it from an upgrade. Returns the matching towers and where each "
        "gets the capability."
    ),
    parameters={
        "type": "object",
        "properties": {
            "capability": {
                "type": "string",
                "description": (
                    "One of: camo_detection, lead_popping, black_popping, "
                    "white_popping, purple_popping."
                ),
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
    from utils.btd6.coverage import AREA_CAPABILITIES, get_coverage

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
        "note": get_coverage(AREA_CAPABILITIES).user_label,
        "towers": [
            {"id": h.tower_id, "name": h.canonical, "detail": h.detail} for h in hits
        ],
    }


# --- btd6_superlative_lookup -------------------------------------------

_BTD6_SUPERLATIVE_SPEC = AIToolSpec(
    name="btd6_superlative_lookup",
    description=(
        "Rank BTD6 costs across the whole roster — use for "
        "'most/least/cheapest/most expensive …' questions. metric: "
        "'upgrade_cost' (set tier 1-5 to scope it, e.g. 'most expensive tier "
        "4 upgrade'), 'tower_cost' (base placement cost), or 'paragon_cost'. "
        "Set cheapest=true for least expensive (default is most expensive). "
        "Returns the top matches with their cost."
    ),
    parameters={
        "type": "object",
        "properties": {
            "metric": {
                "type": "string",
                "description": "upgrade_cost, tower_cost, or paragon_cost.",
            },
            "tier": {
                "type": "integer",
                "description": "1-5; only meaningful for upgrade_cost.",
            },
            "cheapest": {
                "type": "boolean",
                "description": "Least expensive when true (default false).",
            },
            "limit": {
                "type": "integer",
                "description": (
                    "How many to return (default 3). Use a large value to "
                    "list them all, e.g. every paragon (max 25)."
                ),
            },
        },
        "required": ["metric"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


async def _btd6_superlative_lookup(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_superlative_service as sup

    metric = str(arguments.get("metric") or "").strip().lower()
    if metric not in sup.METRICS:
        return {
            "found": False,
            "note": "unsupported metric; supported: " + ", ".join(sup.METRICS),
        }
    raw_tier = arguments.get("tier")
    try:
        tier = int(raw_tier) if raw_tier is not None else None
    except (TypeError, ValueError):
        tier = None
    cheapest = bool(arguments.get("cheapest", False))
    limit = _coerce_limit(arguments.get("limit"), default=3, lo=1, hi=25)
    hits = sup.rank(metric, tier=tier, cheapest=cheapest, limit=limit)
    return {
        "found": bool(hits),
        "metric": metric,
        "tier": tier,
        "cheapest": cheapest,
        "results": [
            {"cost": h.cost, "what": h.what, "tower_id": h.tower_id} for h in hits
        ],
    }


# --- btd6_difficulty_cost ----------------------------------------------

_BTD6_DIFFICULTY_COST_SPEC = AIToolSpec(
    name="btd6_difficulty_cost",
    description=(
        "Convert a BTD6 Medium-difficulty cost into all four difficulties. "
        "BTD6 prices scale with difficulty (Easy is cheaper, Hard/Impoppable "
        "are pricier), and every other lookup tool returns the MEDIUM figure. "
        "When the user asks about Easy / Hard / Impoppable pricing, pass the "
        "Medium cost here to get the exact Easy/Medium/Hard/Impoppable prices "
        "— do not do the multiplication yourself, and never claim costs are "
        "the same across difficulties."
    ),
    parameters={
        "type": "object",
        "properties": {
            "medium_cost": {
                "type": "integer",
                "description": "The Medium-difficulty cost to convert.",
            },
        },
        "required": ["medium_cost"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


async def _btd6_difficulty_cost(arguments: dict[str, Any]) -> dict[str, Any]:
    from utils.btd6 import difficulty_costs

    try:
        medium = int(arguments.get("medium_cost"))
    except (TypeError, ValueError):
        return {"found": False, "note": "medium_cost must be an integer"}
    if medium <= 0:
        return {"found": False, "note": "medium_cost must be > 0"}
    return {
        "found": True,
        "medium_cost": medium,
        "costs_by_difficulty": difficulty_costs.all_difficulty_costs(medium),
    }


# --- btd6_paragon_calculate --------------------------------------------------

_PARAGON_CALCULATE_SPEC = AIToolSpec(
    name="btd6_paragon_calculate",
    description=(
        "Calculate the BTD6 Paragon DEGREE a set of sacrifices would produce — "
        "use for 'what degree will I get with ...' questions. Give the tower or "
        "paragon plus any of: pops (total pops/damage), income, cash_spent (cash "
        "used building the non-T5 sacrifices), slider_cash, upgrade_count (non-T5 "
        "upgrade tiers, e.g. a 0-2-4 tower = 6), tier5_count (extra T5s beyond the "
        "3 required — solo allows 1 and only on Dart Monkey, co-op allows up to 9), "
        "geraldo_totems, player_count (1 = solo, 2-4 = co-op), and difficulty. "
        "Returns degree (1-100), total power, a per-source power breakdown, and "
        "warnings. If the result has estimated=true the live calculator was "
        "unreachable and the numbers are a local estimate — tell the user."
    ),
    parameters={
        "type": "object",
        "properties": {
            "tower": {
                "type": "string",
                "description": "Tower name, paragon name, or paragon id (e.g. 'Dart Monkey').",
            },
            "pops": {
                "type": "integer",
                "description": "Total pops/damage across sacrifices.",
            },
            "income": {
                "type": "integer",
                "description": "Cash generated by sacrifices ($1 = 4 pops).",
            },
            "cash_spent": {
                "type": "integer",
                "description": "Cash spent building non-T5 sacrifices.",
            },
            "slider_cash": {
                "type": "integer",
                "description": "Cash injected via the in-game slider.",
            },
            "upgrade_count": {
                "type": "integer",
                "description": "Total non-T5 upgrade tiers (cap 100).",
            },
            "tier5_count": {
                "type": "integer",
                "description": "Extra T5s beyond the 3 required.",
            },
            "geraldo_totems": {
                "type": "integer",
                "description": "Geraldo Paragon Power Totems.",
            },
            "player_count": {
                "type": "integer",
                "minimum": 1,
                "maximum": 4,
                "description": "1 solo, 2-4 co-op.",
            },
            "difficulty": {
                "type": "string",
                "enum": ["easy", "medium", "hard", "impoppable"],
                "description": "Game difficulty (default medium).",
            },
        },
        "required": ["tower"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


# --- btd6_paragon_requirements -----------------------------------------------

_PARAGON_REQUIREMENTS_SPEC = AIToolSpec(
    name="btd6_paragon_requirements",
    description=(
        "Work out what it takes to REACH a target BTD6 Paragon degree — use for "
        "'what do I need for Degree X' and 'least money / least tiers / least pops "
        "to hit Degree X' questions. Give the tower/paragon, target_degree (1-100), "
        "and a strategy: 'least_cash', 'least_tiers', or 'least_pops' (minimise that "
        "one input while maxing the others), or 'balanced' (spread evenly across "
        "pops/tiers/cash). Optional player_count (1 solo, 2-4 co-op) and difficulty. "
        "Returns a concrete recommended build (pops, upgrade tiers, cash, extra T5s, "
        "Geraldo totems) that reaches the degree. Geraldo totems are only used as a "
        "final topper for very high degrees that capped inputs alone cannot reach."
    ),
    parameters={
        "type": "object",
        "properties": {
            "tower": {
                "type": "string",
                "description": "Tower name, paragon name, or paragon id.",
            },
            "target_degree": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "description": "The Paragon degree to reach (1-100).",
            },
            "strategy": {
                "type": "string",
                "enum": ["balanced", "least_cash", "least_tiers", "least_pops"],
                "description": "Which input to minimise, or 'balanced' (default).",
            },
            "player_count": {
                "type": "integer",
                "minimum": 1,
                "maximum": 4,
                "description": "1 solo, 2-4 co-op.",
            },
            "difficulty": {
                "type": "string",
                "enum": ["easy", "medium", "hard", "impoppable"],
                "description": "Game difficulty (default medium).",
            },
        },
        "required": ["tower", "target_degree"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


def _paragon_error(
    code: str,
    message: str,
    *,
    valid_towers: list[str] | None = None,
    retry_after: int | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if valid_towers is not None:
        error["valid_towers"] = valid_towers
    if retry_after is not None:
        error["retry_after"] = retry_after
    return {"success": False, "result": None, "error": error, "estimated": False}


def _paragon_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _paragon_attribution() -> dict[str, str]:
    """Credit + click-through data the model must append to paragon answers.

    The link/author live in ``paragon_service`` (it owns the live-API URL); the
    ``note`` tells the model to end its reply with this credit so attribution
    travels with every AI-delivered paragon result, mirroring the ``!paragon``
    panel's link button + credit field.
    """
    from services import paragon_service

    return {
        "calculator_url": paragon_service.CALCULATOR_PUBLIC_URL,
        "author": paragon_service.CALCULATOR_AUTHOR_NAME,
        "note": (
            "End your reply with a credit line linking to calculator_url and "
            "naming the author."
        ),
    }


def _paragon_breakdown_summary(breakdown: Any) -> dict[str, Any]:
    return {
        axis.key: {
            "power": axis.power,
            "max_power": axis.max_power,
            "capped": axis.capped,
            "fill_pct": axis.fill_pct,
        }
        for axis in breakdown.axes
    }


async def _paragon_calculate(arguments: dict[str, Any]) -> dict[str, Any]:
    tower = str(arguments.get("tower") or "").strip()
    if not tower:
        return _paragon_error("missing_field", "A tower or paragon name is required.")
    from services import paragon_service
    from utils.btd6.paragon_math import ParagonInputs

    inputs = ParagonInputs(
        tower=tower,
        pops=_paragon_int(arguments.get("pops")),
        income=_paragon_int(arguments.get("income")),
        cash_spent=_paragon_int(arguments.get("cash_spent")),
        slider_cash=_paragon_int(arguments.get("slider_cash")),
        upgrade_count=_paragon_int(arguments.get("upgrade_count")),
        tier5_count=_paragon_int(arguments.get("tier5_count")),
        geraldo_totems=_paragon_int(arguments.get("geraldo_totems")),
        player_count=_paragon_int(arguments.get("player_count"), 1) or 1,
        difficulty=str(arguments.get("difficulty") or "medium").strip().lower(),
    )
    try:
        result = await paragon_service.calculate(inputs)
    except paragon_service.ParagonUnknownTowerError as exc:
        return _paragon_error(
            "unknown_tower",
            str(exc),
            valid_towers=list(exc.valid_towers),
        )
    except paragon_service.ParagonRateLimitError as exc:
        return _paragon_error("rate_limited", str(exc), retry_after=exc.retry_after)
    except paragon_service.ParagonServiceError as exc:
        return _paragon_error("error", str(exc))

    breakdown = result.breakdown
    return {
        "success": True,
        "result": {
            "degree": breakdown.degree,
            "total_power": breakdown.total_power,
            "power_for_next_degree": breakdown.power_for_next_degree,
            "next_degree": breakdown.next_degree,
            "breakdown": _paragon_breakdown_summary(breakdown),
            "wasted_cash": breakdown.wasted_cash,
            "warnings": [w.message for w in result.warnings],
            "paragon": {
                "id": result.paragon_id,
                "name": result.paragon_name,
                "tower": result.tower,
                "base_price": result.base_price,
                "difficulty": result.difficulty,
                "game_mode": result.game_mode,
            },
        },
        "attribution": _paragon_attribution(),
        "error": None,
        "estimated": result.estimated,
    }


async def _paragon_requirements(arguments: dict[str, Any]) -> dict[str, Any]:
    tower = str(arguments.get("tower") or "").strip()
    if not tower:
        return _paragon_error("missing_field", "A tower or paragon name is required.")
    target = _paragon_int(arguments.get("target_degree"))
    if target < 1 or target > 100:
        return _paragon_error(
            "invalid_target",
            "target_degree must be between 1 and 100.",
        )
    from services import paragon_service

    try:
        requirement = await paragon_service.requirements(
            target,
            tower,
            strategy=arguments.get("strategy", "balanced"),
            player_count=_paragon_int(arguments.get("player_count"), 1) or 1,
            difficulty=str(arguments.get("difficulty") or "medium").strip().lower(),
        )
    except paragon_service.ParagonUnknownTowerError as exc:
        return _paragon_error(
            "unknown_tower",
            str(exc),
            valid_towers=list(exc.valid_towers),
        )
    except paragon_service.ParagonServiceError as exc:
        return _paragon_error("error", str(exc))

    solution = requirement.solution
    chosen = solution.inputs
    return {
        "success": True,
        "result": {
            "target_degree": solution.target_degree,
            "strategy": solution.strategy.value,
            "paragon": {
                "id": requirement.paragon_id,
                "name": requirement.paragon_name,
                "tower": requirement.tower,
            },
            "recommended_inputs": {
                "pops": chosen.pops,
                "cash_spent": chosen.cash_spent,
                "upgrade_count": chosen.upgrade_count,
                "tier5_count": chosen.tier5_count,
                "geraldo_totems": chosen.geraldo_totems,
                "player_count": chosen.player_count,
                "difficulty": chosen.difficulty,
            },
            "resulting_degree": requirement.confirmed_degree,
            "requires_totems": solution.requires_totems,
            "verified": requirement.verified,
        },
        "attribution": _paragon_attribution(),
        "error": None,
        "estimated": requirement.estimated,
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
    guild: Any = None,
    member: Any = None,
) -> ToolRegistry:
    """Build the read-only tool set the caller's ``scope`` may be offered.

    ``specs`` are attached to the :class:`AIRequest` (the model sees
    them); ``handlers`` are passed to ``ai_gateway.execute`` as
    ``tool_handlers``. Only tools whose ``min_scope`` the caller
    satisfies are included.

    ``guild`` (the live ``discord.Guild``) and ``member`` (the asking
    ``discord.Member``) enable the server-introspection tools. When
    ``guild`` is ``None`` those tools are omitted, so existing callers
    that do not have a live guild keep the prior toolset. Member-level
    data (the ``lookup_member`` and ``list_all_members`` tools, plus member
    counts) is gated behind
    :func:`feature_flags.ai_server_member_lookup_enabled` — default off.
    """
    from core.runtime.ai.feature_flags import ai_server_member_lookup_enabled

    include_members = ai_server_member_lookup_enabled()
    catalog: list[tuple[AIToolSpec, ToolHandler]] = [
        (_USER_STANDING_SPEC, _make_user_standing(guild_id, actor_id, member)),
        (_SERVER_TIME_SPEC, _server_time),
        (_BTD6_LOOKUP_SPEC, _btd6_lookup),
        (_BTD6_CAPABILITY_SPEC, _btd6_capability_lookup),
        (_BTD6_SUPERLATIVE_SPEC, _btd6_superlative_lookup),
        (_BTD6_DIFFICULTY_COST_SPEC, _btd6_difficulty_cost),
        (_PARAGON_CALCULATE_SPEC, _paragon_calculate),
        (_PARAGON_REQUIREMENTS_SPEC, _paragon_requirements),
        (_GUILD_AI_CONFIG_SPEC, _make_guild_ai_config(guild_id)),
        (_RECENT_AUDIT_SPEC, _make_recent_audit(guild_id)),
    ]
    if guild is not None:
        catalog.extend(
            [
                (
                    _SERVER_OVERVIEW_SPEC,
                    _make_server_overview(guild, include_members=include_members),
                ),
                (
                    _SERVER_ROLES_SPEC,
                    _make_list_roles(guild, include_member_counts=include_members),
                ),
                (_SERVER_CHANNELS_SPEC, _make_list_channels(guild, member)),
            ],
        )
        if include_members:
            catalog.extend(
                [
                    (_MEMBER_LOOKUP_SPEC, _make_lookup_member(guild, member)),
                    (_MEMBER_LIST_SPEC, _make_list_members(guild)),
                ],
            )
    specs: list[AIToolSpec] = []
    handlers: dict[str, ToolHandler] = {}
    for spec, handler in catalog:
        if _scope_allows(scope, spec.min_scope):
            specs.append(spec)
            handlers[spec.name] = handler
    return ToolRegistry(specs=tuple(specs), handlers=handlers)


__all__ = ["ToolRegistry", "build_registry"]
