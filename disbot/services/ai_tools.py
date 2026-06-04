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
        "costs; a single upgrade by name or community abbreviation ('PMFC', "
        "'POD', 'Prince of Darkness'); paragon stats and their named abilities "
        "and cooldowns ('Carpet Bomb', 'Spikeageddon'); bloon properties, "
        "immunities, health, what each bloon spawns "
        "into (the full Red->Blue->Green->Yellow->Pink->...->MOAB-class chain), "
        "and RBE (Red Bloon Equivalent); maps, modes, rounds, current live "
        "events; and Contested Territory (CT) relics and tiles — what each "
        "relic does and which tile it sits on, the active CT event's full tile "
        "inventory (the true total and counts by tile type and battle mode), "
        "and what sits on a specific tile named by its 3-letter code ('DEC', "
        "'MRX'). Call "
        "this for ANY question about BTD6 before answering — including 'what "
        "does X pop into', 'how much health/RBE does X have', questions about "
        "the basic bloon tiers, any upgrade or paragon-ability question, AND "
        "any CT relic / tile question ('tell me "
        "about the relics', 'what relics are in the current CT', 'where is "
        "Camo Trap', 'list all tiles', 'how many tiles', 'what's on tile DEC') "
        "— even when no specific tower, hero, bloon, or relic is "
        "named, so the answer is grounded in real data instead of memory. Call "
        "it even if an earlier reply implied the data wasn't available — the "
        "tool's data is updated independently and can change between messages. "
        "Returns found=false when nothing matched; treat that as 'no verified "
        "data available' only after you have actually called it."
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

# Cap returned grounding lines so a runaway query can't blow the token budget.
# Must clear the grounding's own largest single-query payload, or the tool
# silently re-truncates what build() already bounded. The biggest legitimate
# case is a full Contested Territory relic map: btd6_context_service caps it at
# _CT_TILE_LINE_CAP (48 tile lines) + _CT_RELIC_EFFECT_CAP (24 effect lines),
# and Pass-2 live-event rows are emitted *before* those tiles — so a cap of 25
# dropped a 24-relic listing to ~19 once a handful of live events ate the
# budget. Sit above 48+24 plus live-event preamble; each line is itself capped
# at 240 chars, so even the maximum payload stays within a sane token budget.
_BTD6_LOOKUP_FACT_CAP = 80


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


# --- btd6_list_roster --------------------------------------------------

_BTD6_LIST_ROSTER_SPEC = AIToolSpec(
    name="btd6_list_roster",
    description=(
        "List the COMPLETE verified roster of a BTD6 entity kind — every hero, "
        "tower, or paragon by name, with the exact count. Use for 'list all "
        "heroes', 'which heroes are in the game', 'how many towers are there', "
        "'name every paragon'. Returns the full canonical list so you never "
        "guess a count or miss an entry — state the names from this list "
        "verbatim. ``kind`` must be one of: heroes, towers, paragons."
    ),
    parameters={
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": ["heroes", "towers", "paragons"],
                "description": "Which roster to list.",
            },
        },
        "required": ["kind"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


async def _btd6_list_roster(arguments: dict[str, Any]) -> dict[str, Any]:
    kind = str(arguments.get("kind") or "").strip().lower()
    # Lazy import: keep the BTD6 data layer off the import path until used.
    from services import btd6_data_service

    if kind == "heroes":
        names = [hero.canonical for hero in btd6_data_service.get_dataset().heroes]
    elif kind == "towers":
        names = [tower.canonical for tower in btd6_data_service.get_dataset().towers]
    elif kind == "paragons":
        from utils.btd6.paragon_math import PARAGONS

        names = [paragon.name for paragon in PARAGONS]
    else:
        return {
            "found": False,
            "kind": kind,
            "note": "kind must be one of: heroes, towers, paragons",
        }
    return {"found": True, "kind": kind, "count": len(names), "names": names}


# --- btd6_capability_lookup --------------------------------------------

_BTD6_CAPABILITY_SPEC = AIToolSpec(
    name="btd6_capability_lookup",
    description=(
        "List which BTD6 TOWERS — or PARAGONS — have a capability. Use for "
        "'which tower …' / 'which paragon …' / 'which paragons can(not) see "
        "camo' discovery questions that don't name a specific entity. Supported "
        "capabilities: 'camo_detection' (can target Camo bloons), "
        "'lead_popping', 'black_popping', 'white_popping', 'purple_popping'. "
        "Set entity='paragon' for paragon questions (camo_detection only — "
        "returns BOTH the paragons that CAN and CANNOT see camo; only the 13 "
        "tower paragons exist, heroes have none); default entity='tower'. For "
        "towers, set unupgraded=true (default) for base 0-0-0 only, or false to "
        "include upgrade-granted towers. Returns the matching entities."
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
            "entity": {
                "type": "string",
                "description": (
                    "'tower' (default) or 'paragon'. Use 'paragon' for "
                    "'which paragon(s) …' questions (camo_detection only)."
                ),
            },
            "unupgraded": {
                "type": "boolean",
                "description": (
                    "Towers only: base (0-0-0) when true (default); include "
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

    entity = str(arguments.get("entity") or "tower").strip().lower()
    if entity == "paragon":
        hits = btd6_capability_service.paragons_with_capability(capability)
        if not hits:
            return {
                "found": False,
                "entity": "paragon",
                "note": (
                    f"per-paragon {capability} is not verified; only "
                    "camo_detection is supported for paragons"
                ),
            }
        return {
            "found": True,
            "entity": "paragon",
            "capability": capability,
            "with_capability": [
                {"paragon": h.paragon, "tower": h.tower}
                for h in hits
                if h.has_capability
            ],
            "without_capability": [
                {"paragon": h.paragon, "tower": h.tower}
                for h in hits
                if not h.has_capability
            ],
            "note": (
                "The 13 tier-6 tower paragons. Heroes do NOT have paragons — "
                "do not list heroes."
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
        "Rank BTD6 entities across the whole roster in ONE call — use for "
        "'most/least/highest/lowest/cheapest/most expensive …' questions (e.g. "
        "'which paragon has the highest DPS', 'longest-range tower') instead of "
        "looking entities up one by one. COST metrics: 'upgrade_cost' (set tier "
        "1-5 to scope, e.g. 'priciest tier-4 upgrade'), 'tower_cost' (base "
        "placement), 'paragon_cost'. COMBAT metrics: 'paragon_dps', "
        "'paragon_damage', 'paragon_pierce' (paragons at degree 1) and "
        "'tower_dps', 'tower_damage', 'tower_pierce', 'tower_range' (base 0-0-0 "
        "towers). DPS is a ROUGH estimate only (sums all projectile damage / "
        "cooldown; ignores targeting/pierce/AoE) — present it as approximate and "
        "use 'btd6_paragon_stats_at_degree' for the exact per-attack breakdown; "
        "rank by '*_pierce' for crowd-clear. Set cheapest=true for the "
        "lowest/least (default is highest/most). Each result has value, unit, "
        "what, and a detail string."
    ),
    parameters={
        "type": "object",
        "properties": {
            "metric": {
                "type": "string",
                "description": (
                    "Cost: upgrade_cost, tower_cost, paragon_cost. Combat: "
                    "paragon_dps, paragon_damage, paragon_pierce, tower_dps, "
                    "tower_damage, tower_pierce, tower_range."
                ),
            },
            "tier": {
                "type": "integer",
                "description": "1-5; only meaningful for upgrade_cost.",
            },
            "cheapest": {
                "type": "boolean",
                "description": (
                    "Lowest/least when true (cheapest cost, lowest DPS, …); "
                    "default false = highest/most."
                ),
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
    results: list[dict[str, Any]] = []
    for h in hits:
        row: dict[str, Any] = {
            "value": h.value,
            "unit": h.unit,
            "what": h.what,
            "detail": h.detail,
            "tower_id": h.tower_id,
        }
        if h.unit == "$":  # back-compat for cost-ranking callers
            row["cost"] = h.cost
        results.append(row)
    return {
        "found": bool(hits),
        "metric": metric,
        "tier": tier,
        "cheapest": cheapest,
        "results": results,
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


# --- btd6_round_composition --------------------------------------------------

_BTD6_ROUND_COMPOSITION_SPEC = AIToolSpec(
    name="btd6_round_composition",
    description=(
        "Exact BTD6 bloon composition for a round or a round RANGE (standard "
        "rounds 1-140). Use for 'how many purples in rounds 35-70', 'what spawns "
        "in round 63', 'which rounds have MOABs', 'RBE of round 80'. Pass "
        "round_start (and round_end for a range). Pass a bloon (e.g. 'purple', "
        "'ceramic', 'MOAB') to get its TOTAL across the range plus the per-round "
        "counts; omit it for each round's full spawn list + RBE. Do not count or "
        "sum yourself — this returns the exact totals."
    ),
    parameters={
        "type": "object",
        "properties": {
            "round_start": {
                "type": "integer",
                "description": "First round (1-140). For a single round, set only this.",
            },
            "round_end": {
                "type": "integer",
                "description": "Last round of the range (inclusive); omit for one round.",
            },
            "bloon": {
                "type": "string",
                "description": "Bloon to count, e.g. 'purple', 'ceramic', 'MOAB'. Omit for full composition.",
            },
        },
        "required": ["round_start"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


async def _btd6_round_composition(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_data_service

    try:
        start = int(arguments.get("round_start"))
    except (TypeError, ValueError):
        return {"found": False, "note": "round_start must be an integer (1-140)"}
    raw_end = arguments.get("round_end")
    try:
        end = int(raw_end) if raw_end is not None else None
    except (TypeError, ValueError):
        end = None
    bloon = str(arguments.get("bloon") or "").strip() or None
    return btd6_data_service.round_composition(start, end, bloon)


# --- btd6_map_lookup ---------------------------------------------------------

_BTD6_MAP_LOOKUP_SPEC = AIToolSpec(
    name="btd6_map_lookup",
    description=(
        "BTD6 map info: difficulty (Beginner / Intermediate / Advanced / Expert), "
        "description, and line-of-sight notes. Pass a map name to look one up, or "
        "omit it to list every map with its difficulty (use for 'which maps are "
        "beginner', 'is Logs beginner', 'list the maps')."
    ),
    parameters={
        "type": "object",
        "properties": {
            "map": {
                "type": "string",
                "description": "Map name (e.g. 'Logs'); omit to list all maps.",
            },
        },
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


def _map_dict(entry: Any) -> dict[str, Any]:
    return {
        "name": entry.canonical,
        "difficulty": entry.difficulty,
        "description": entry.description,
        "line_of_sight_notes": entry.lines_of_sight_notes,
    }


async def _btd6_map_lookup(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_data_service

    name = str(arguments.get("map") or "").strip()
    if name:
        entry = btd6_data_service.find_map(name)
        if entry is None:
            return {"found": False, "note": f"unknown map: {name!r}"}
        return {"found": True, "map": _map_dict(entry)}
    maps = btd6_data_service.get_dataset().maps
    return {"found": True, "count": len(maps), "maps": [_map_dict(m) for m in maps]}


# --- btd6_mode_lookup --------------------------------------------------------

_BTD6_MODE_LOOKUP_SPEC = AIToolSpec(
    name="btd6_mode_lookup",
    description=(
        "BTD6 game mode info: starting cash, starting lives, and rule restrictions "
        "(e.g. CHIMPS = no Continues, Hearts lost, Income, Monkey knowledge, "
        "Powers, Selling). Pass a mode name to look one up, or omit it to list all "
        "modes (use for 'what are CHIMPS restrictions', 'CHIMPS starting cash', "
        "'list game modes')."
    ),
    parameters={
        "type": "object",
        "properties": {
            "mode": {
                "type": "string",
                "description": "Mode name (e.g. 'CHIMPS'); omit to list all modes.",
            },
        },
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


def _mode_dict(entry: Any) -> dict[str, Any]:
    return {
        "name": entry.canonical,
        "starting_cash": entry.starting_cash,
        "starting_lives": entry.starting_lives,
        "description": entry.description,
        "restrictions": list(entry.restrictions),
    }


async def _btd6_mode_lookup(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_data_service

    name = str(arguments.get("mode") or "").strip()
    if name:
        entry = btd6_data_service.find_mode(name)
        if entry is None:
            return {"found": False, "note": f"unknown mode: {name!r}"}
        return {"found": True, "mode": _mode_dict(entry)}
    modes = btd6_data_service.get_dataset().modes
    return {"found": True, "count": len(modes), "modes": [_mode_dict(m) for m in modes]}


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


# --- btd6_paragon_stats_at_degree -------------------------------------------

_BTD6_PARAGON_STATS_AT_DEGREE_SPEC = AIToolSpec(
    name="btd6_paragon_stats_at_degree",
    description=(
        "Exact paragon stats at a specific DEGREE (1-100), as a per-attack "
        "breakdown. USE THIS instead of interpolating between the Degree 1 and "
        "Degree 100 numbers — paragons scale NON-linearly (attack speed is a "
        "square-root curve, damage/pierce jump to ~2x at Degree 100), so linear "
        "interpolation is wrong. Give 'paragon' (a paragon name or its tower, "
        "e.g. 'Goliath Doomship' or 'Ace') and a 'degree' (1-100). Returns each "
        "attack with its exact cooldown and every projectile's damage/pierce "
        "(quote these for anything precise), the boss-damage multiplier, and "
        "cumulative power, plus 'rough_dps' — a ROUGH estimate only (sums all "
        "projectile damage / cooldown; ignores targeting/pierce/AoE/uptime). "
        "Present DPS as approximate; never as an exact figure."
    ),
    parameters={
        "type": "object",
        "properties": {
            "paragon": {
                "type": "string",
                "description": (
                    "Paragon name or its tower, e.g. 'Goliath Doomship' or 'Ace'."
                ),
            },
            "degree": {
                "type": "integer",
                "description": "1-100; the degree to compute stats for (default 1).",
            },
        },
        "required": ["paragon"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


async def _btd6_paragon_stats_at_degree(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_stats_service as ss

    paragon = str(arguments.get("paragon") or "").strip()
    paragon_id = ss.resolve_paragon(paragon) if paragon else None
    if paragon_id is None:
        return {"found": False, "note": f"no paragon matched {paragon!r}"}

    degree_arg = arguments.get("degree", 1)
    try:
        degree = int(degree_arg) if degree_arg is not None else 1
    except (TypeError, ValueError):
        return {"found": False, "note": "degree must be an integer 1-100"}

    stats = ss.paragon_stats_at_degree(paragon_id, degree)
    if stats is None:
        return {"found": False, "note": f"{paragon_id} has no computable attack"}
    return {
        "found": True,
        "paragon": stats.canonical,
        "tower": stats.tower_canonical,
        "degree": stats.degree,
        "attacks": [
            {
                "name": atk.name,
                "cooldown_seconds": atk.cooldown,
                "projectiles": [
                    {"name": name, "damage": dmg, "pierce": pierce}
                    for (name, dmg, pierce) in atk.projectiles
                ],
            }
            for atk in stats.attacks
        ],
        "rough_dps": stats.rough_dps,
        "rough_dps_note": (
            "ROUGH estimate only — sums all projectile damage / cooldown across "
            "every attack; ignores targeting, pierce, AoE, and uptime. Use the "
            "per-attack breakdown above for exact damage/cooldown; do not present "
            "rough_dps as a precise DPS figure."
        ),
        "boss_damage_multiplier": stats.boss_multiplier,
        "power": stats.power,
    }


# --- btd6_ct_team_status (guild-scoped) -------------------------------

_BTD6_CT_TEAM_SPEC = AIToolSpec(
    name="btd6_ct_team_status",
    description=(
        "Return THIS server's Contested Territory (CT) TEAM standing for the "
        "current event: the team's live score and rank within its weekly "
        "bracket, plus the rival teams it is matched against. Use for 'how is "
        "our CT team doing', 'our team's score', 'are we winning our bracket', "
        "'CT team standing'. The team is whichever CT bracket an admin pasted "
        "with the '!btd6 ctteam' command; if none is set, or the saved id has "
        "gone stale (Ninja Kiwi rotates it each event), the tool says so — "
        "relay that instead of guessing. This is team SCORES only: Ninja Kiwi "
        "does not publish per-tile ownership, so never claim to know which team "
        "holds which tile."
    ),
    parameters={
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


def _make_btd6_ct_team_status(guild_id: int) -> ToolHandler:
    async def handler(_arguments: dict[str, Any]) -> dict[str, Any]:
        from services import btd6_ct_team_service

        group_id = await btd6_ct_team_service.get_team_group_id(guild_id)
        if not group_id:
            return {
                "configured": False,
                "note": (
                    "No CT team is configured for this server. An admin can set "
                    "one with '!btd6 ctteam <bracket id or group URL>'."
                ),
            }
        result = await btd6_ct_team_service.get_ct_bracket(group_id)
        if result.ct_id is None:
            return {
                "configured": True,
                "active_event": False,
                "note": "No Contested Territory event is active right now.",
            }
        if result.stale:
            return {
                "configured": True,
                "active_event": True,
                "stale": True,
                "note": (
                    "The saved bracket id returned no teams for the current CT "
                    "event — Ninja Kiwi rotates it each event, so re-paste this "
                    "week's bracket id with '!btd6 ctteam <id or URL>'."
                ),
            }
        return {
            "configured": True,
            "active_event": True,
            "ct_event_id": result.ct_id,
            "bracket": [
                {"rank": row.rank, "team": row.display_name, "score": row.score}
                for row in result.rows
            ],
        }

    return handler


@dataclass(frozen=True)
class ToolRegistry:
    """The tools offered for one request: specs (data) + live handlers."""

    specs: tuple[AIToolSpec, ...]
    handlers: Mapping[str, ToolHandler]


# Tools whose results are BTD6 *facts* and may therefore ground a BTD6 answer.
# The natural-language stage captures ONLY these tools' outputs into the
# faithfulness ledger — server/user/config tools (member counts, timestamps,
# IDs) must never whitelist a hallucinated BTD6 name or number. Keep in sync
# with the ``btd6_*`` specs above; ``tests/unit/services/test_ai_tools.py``
# pins this set ⊆ the registered ``btd6_*`` tool names so it cannot drift.
BTD6_GROUNDING_TOOL_NAMES: frozenset[str] = frozenset(
    {
        "btd6_lookup",
        "btd6_list_roster",
        "btd6_capability_lookup",
        "btd6_superlative_lookup",
        "btd6_difficulty_cost",
        "btd6_round_composition",
        "btd6_map_lookup",
        "btd6_mode_lookup",
        "btd6_paragon_calculate",
        "btd6_paragon_requirements",
        "btd6_paragon_stats_at_degree",
        "btd6_ct_team_status",
    },
)


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
        (_BTD6_LIST_ROSTER_SPEC, _btd6_list_roster),
        (_BTD6_CAPABILITY_SPEC, _btd6_capability_lookup),
        (_BTD6_SUPERLATIVE_SPEC, _btd6_superlative_lookup),
        (_BTD6_DIFFICULTY_COST_SPEC, _btd6_difficulty_cost),
        (_BTD6_ROUND_COMPOSITION_SPEC, _btd6_round_composition),
        (_BTD6_MAP_LOOKUP_SPEC, _btd6_map_lookup),
        (_BTD6_MODE_LOOKUP_SPEC, _btd6_mode_lookup),
        (_PARAGON_CALCULATE_SPEC, _paragon_calculate),
        (_PARAGON_REQUIREMENTS_SPEC, _paragon_requirements),
        (_BTD6_PARAGON_STATS_AT_DEGREE_SPEC, _btd6_paragon_stats_at_degree),
        (_BTD6_CT_TEAM_SPEC, _make_btd6_ct_team_status(guild_id)),
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


__all__ = ["BTD6_GROUNDING_TOOL_NAMES", "ToolRegistry", "build_registry"]
