"""AI tools the model may call during a natural-language turn.

Handlers live in the services layer (not ``core/runtime``) because they
read from other services. For a given request the gateway is handed the
``{name: handler}`` map; the matching :class:`AIToolSpec` objects travel
on the request as pure data. Tools return a small, JSON-serialisable dict.

**No tool here mutates state.** Every tool reads and returns a dict. The one
tool that touches the outside world is ``open_support_ticket``, and even it
does **not** open a ticket: it validates eligibility (read-only) and, when
allowed, emits ``ticket.open_requested`` so ``cogs.ticket_cog`` posts a
one-click **[Open ticket]/[Cancel]** confirmation. The actual write runs only
when the user clicks, through the deterministic, **audited**
``services.ticket_mutation.open_ticket`` seam — so the AI proposes and the
human commits (Q-0201). This keeps the original contract intact: *mutations
flow through the deterministic mutation services after explicit confirmation*
(``docs/ai-config-ownership.md`` § "Mutation seam"). A genuinely write-capable
tool is still out of scope — route it through a confirmation like this one.

Scope gating: ``build_registry`` only includes a tool when the caller's
:class:`AIScope` satisfies the tool's ``min_scope``. A tool above the
caller's privilege is never offered to the model at all, so the model
cannot even attempt to call it.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from core.runtime.ai.contracts import AIScope, AIToolSpec
from core.runtime.ai.providers.base import ToolHandler
from services import (
    ai_config_projection_service,
    ai_decision_audit_service,
    ai_permission_service,
    ai_tool_catalogue,
)
from services.health_contracts import HealthAudience

_NO_ARGS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}

# Scope ordering + offered-tool selection now live in the canonical tool catalogue
# (``services.ai_tool_catalogue``), the orchestration foundation. ``_scope_allows`` is
# re-exported so the historical ``from services.ai_tools import _scope_allows`` import
# (and its test) keep working against the single source of truth.
_scope_allows = ai_tool_catalogue.scope_allows


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
        from config import is_platform_owner

        result["is_bot_owner"] = is_platform_owner(actor_id)
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


# --- diagnostics_health_snapshot (platform owner) ----------------------

# AIScope -> HealthAudience boundary. Kept explicit (and tested) even though
# this tool is owner-gated, so the redaction audience is never derived ad hoc.
# TODO(#536): when the AIToolDescriptor / `diagnostics` toolset lands, register
# this tool there instead of the flat build_registry catalog.


def _audience_for_scope(scope: AIScope) -> HealthAudience:
    """Map an :class:`AIScope` to the health-snapshot redaction audience."""
    if scope is AIScope.PLATFORM_OWNER:
        return HealthAudience.PLATFORM_OWNER
    if scope in (AIScope.SERVER_OWNER, AIScope.ADMIN):
        return HealthAudience.GUILD_ADMIN
    return HealthAudience.PUBLIC


_DIAGNOSTICS_HEALTH_SPEC = AIToolSpec(
    name="diagnostics_health_snapshot",
    description=(
        "Return a bounded, redacted snapshot of THIS bot's own operational "
        "health: overall status, per-subsystem status (runtime, gateway, "
        "database, AI, startup, tasks, …), and recent grouped findings with "
        "occurrence counts. Platform-owner only. Call this to answer questions "
        "about how the bot itself is doing right now — uptime, errors, degraded "
        "or unavailable subsystems. Pass fresh=true to run bounded live checks "
        "(database ping, fresh consistency) instead of the cached view."
    ),
    parameters={
        "type": "object",
        "properties": {
            "fresh": {
                "type": "boolean",
                "description": (
                    "Run bounded live checks instead of the cached snapshot "
                    "(default false)."
                ),
            },
        },
        "additionalProperties": False,
    },
    min_scope=AIScope.PLATFORM_OWNER,
)


def _make_diagnostics_health(bot: Any, guild_id: int) -> ToolHandler:
    async def handler(arguments: dict[str, Any]) -> dict[str, Any]:
        # Function-local: keep the heavy health graph out of ai_tools import.
        from services import health_snapshot_service
        from services.health_contracts import HealthSnapshotRequest

        fresh = bool(arguments.get("fresh", False))
        audience = _audience_for_scope(AIScope.PLATFORM_OWNER)
        request = HealthSnapshotRequest(
            purpose="ai_context",
            audience=audience,
            guild_id=guild_id,
            include_fresh_consistency=fresh,
        )
        # collect_*_snapshot already projects to request.audience; the payload
        # is therefore the owner-scoped, redacted, bounded JSON view.
        if fresh:
            snapshot = await health_snapshot_service.collect_snapshot(request, bot=bot)
        else:
            snapshot = health_snapshot_service.collect_cached_snapshot(request, bot=bot)
        return health_snapshot_service.snapshot_to_payload(snapshot)

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
        "the same across difficulties. For 'how much do N of these cost', "
        "pass quantity too and read total_costs_by_difficulty — never "
        "multiply yourself."
    ),
    parameters={
        "type": "object",
        "properties": {
            "medium_cost": {
                "type": "integer",
                "description": "The Medium-difficulty cost to convert.",
            },
            "quantity": {
                "type": "integer",
                "description": (
                    "How many are being bought (optional, default 1); adds "
                    "total_costs_by_difficulty = quantity x adjusted cost."
                ),
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
    per_difficulty = difficulty_costs.all_difficulty_costs(medium)
    result = {
        "found": True,
        "medium_cost": medium,
        "costs_by_difficulty": per_difficulty,
    }
    raw_quantity = arguments.get("quantity")
    if raw_quantity is not None:
        # Bulk pricing ("how much do 10 041 despos cost on impop", BUG-0003 —
        # owner-corrected: that notation is TEN 0-4-1 towers): the product must
        # come from the tool, not model arithmetic — the faithfulness guard
        # rightly blocks numbers absent from the ledger.
        try:
            quantity = int(raw_quantity)
        except (TypeError, ValueError):
            return {"found": False, "note": "quantity must be an integer"}
        if quantity <= 0:
            return {"found": False, "note": "quantity must be > 0"}
        if quantity > 999:
            # An absurd count is almost always the "10 041" notation misread
            # as one number — without this gate the tool computes the wrong
            # product and LAUNDERS it into the trusted ledger, where the
            # faithfulness guard then approves it (live miss 2026-06-11).
            return {
                "found": False,
                "note": (
                    f"quantity {quantity} is not a plausible tower count. "
                    "If the user wrote something like '10 041', that means "
                    "10 towers at crosspath 0-4-1 — retry with quantity=10 "
                    "and the crosspath upgrade costs."
                ),
            }
        result["quantity"] = quantity
        result["total_costs_by_difficulty"] = {
            difficulty: cost * quantity for difficulty, cost in per_difficulty.items()
        }
    return result


# --- btd6_round_composition --------------------------------------------------

_BTD6_ROUND_COMPOSITION_SPEC = AIToolSpec(
    name="btd6_round_composition",
    description=(
        "Exact BTD6 bloon composition for a round or a round RANGE (rounds "
        "1-140; standard by default, or Alternate Bloons Rounds via "
        "roundset='abr'). Use for 'how many purples in rounds 35-70', 'what "
        "spawns in round 63', 'what comes on ABR round 40', 'which rounds have "
        "MOABs', 'RBE of round 80'. Pass round_start (and round_end for a "
        "range). Pass a bloon (e.g. 'purple', 'ceramic', 'MOAB') to get its "
        "TOTAL across the range plus the per-round counts; omit it for each "
        "round's full spawn list + RBE. Do not count or sum yourself — this "
        "returns the exact totals, including `bloons_entering` per round and "
        "`total_bloons_entering` over the range (use these for 'how many bloons "
        "spawn / enter on round N'). For 'heaviest / most / which rounds have "
        "the most' questions, read the pre-ranked `heaviest` (with a bloon, "
        "ranked by count) or `heaviest_by_rbe` (without, ranked by RBE) — do "
        "NOT re-rank the per-round list yourself. Always state the round set "
        "(`roundset_label`, standard vs ABR) next to every round figure — the "
        "same round number differs between sets. ABR answers carry a note: "
        "the set is entered at round 3 (rounds 1-2 are never played)."
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
            "roundset": {
                "type": "string",
                "enum": ["default", "abr"],
                "description": "Round set: 'default' (standard) or 'abr' (Alternate Bloons Rounds). Omit for standard.",
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
    roundset = str(arguments.get("roundset") or "default")
    return btd6_data_service.round_composition(start, end, bloon, roundset=roundset)


# --- btd6_round_cash ---------------------------------------------------------

_BTD6_ROUND_CASH_SPEC = AIToolSpec(
    name="btd6_round_cash",
    description=(
        "BTD6 cash EARNED for a round or an inclusive round RANGE (rounds "
        "1-140; standard/Medium $650 start by default, or Alternate Bloons "
        "Rounds via roundset='abr' — Hard rules, entered at round 3, same "
        "$650 start; no income towers either way). Use for 'how much cash "
        "from round 50 to 60', 'cash on round 80', 'money earned rounds 1-40', "
        "'ABR cash from 3 to 40', 'cumulative cash by round 60'. Pass "
        "round_start (and round_end for a range). The range is INCLUSIVE of "
        "both endpoints and the returned range_cash IS the grounded answer — "
        "do NOT add the per-round cash or subtract cumulative values yourself; "
        "this returns the exact total. For a single round you get round_cash + "
        "cumulative_cash; for a range you also get cumulative_before_start / "
        "cumulative_at_end plus a ready-made `identity` sentence — quote "
        "range_cash as the answer and, if you explain the math, use `identity` "
        "verbatim (never subtract the cumulative AT the start round; that drops "
        "the start round's earnings from an inclusive range). It does NOT apply "
        "Double Cash, Half Cash, or other "
        "difficulties — those come back as a found=false reason, never a "
        "guessed number. ABR cumulative totals start at round 3 (rounds 1-2 "
        "are never played; results carry the note)."
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
            "roundset": {
                "type": "string",
                "enum": ["default", "abr"],
                "description": "Round set: 'default' (standard) or 'abr' (Alternate Bloons Rounds). Omit for standard.",
            },
        },
        "required": ["round_start"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


async def _btd6_round_cash(arguments: dict[str, Any]) -> dict[str, Any]:
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
    roundset = str(arguments.get("roundset") or "default")
    return btd6_data_service.round_cash(start, end, roundset=roundset)


# --- btd6_map_lookup ---------------------------------------------------------

_BTD6_MAP_LOOKUP_SPEC = AIToolSpec(
    name="btd6_map_lookup",
    description=(
        "BTD6 map info: difficulty (Beginner / Intermediate / Advanced / Expert), "
        "whether the map has water (naval-tower placement), description, and "
        "line-of-sight notes. Pass a map name to look one up, or omit it to list "
        "every map with its difficulty (use for 'which maps are beginner', 'is "
        "Logs beginner', 'which maps have water', 'list the maps')."
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
        "has_water": entry.has_water,
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
    out: dict[str, Any] = {
        "name": entry.canonical,
        "kind": getattr(entry, "kind", "mode"),
        "starting_cash": entry.starting_cash,
        "starting_lives": entry.starting_lives,
        "description": entry.description,
        "restrictions": list(entry.restrictions),
    }
    difficulties = getattr(entry, "difficulties", ())
    if difficulties:
        out["difficulties"] = list(difficulties)
    # Game-sourced structured rules (the modes cutover): start/end rounds,
    # cost/speed/income multipliers, locked towers, no-continue/sell/MK flags.
    # Without this the ingested block is dark to the model.
    rules = getattr(entry, "rules", None)
    if rules:
        out["rules"] = dict(rules)
    return out


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


# --- btd6_relic_lookup -------------------------------------------------------

_BTD6_RELIC_LOOKUP_SPEC = AIToolSpec(
    name="btd6_relic_lookup",
    description=(
        "BTD6 Contested Territory (CT) relic info: each relic's effect and "
        "category (offense / economy / lives / powerup / utility). Pass a relic "
        "name to look one up, a category to list that group, or omit both to "
        "list every relic. Use for 'list the CT relics', 'which relics are "
        "offense', 'what does the Super Monkey Storm relic do'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "relic": {
                "type": "string",
                "description": "Relic name/abbrev (e.g. 'Super Monkey Storm', 'SMS'); omit to list.",
            },
            "category": {
                "type": "string",
                "description": "Filter the roster: offense / economy / lives / powerup / utility.",
            },
        },
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


def _relic_dict(entry: Any) -> dict[str, Any]:
    return {
        "name": entry.canonical,
        "category": entry.category,
        "effect": entry.effect,
        "abbrev": entry.abbrev,
    }


async def _btd6_relic_lookup(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_data_service

    name = str(arguments.get("relic") or "").strip()
    if name:
        entry = btd6_data_service.resolve_relic(name)
        if entry is None:
            return {"found": False, "note": f"unknown relic: {name!r}"}
        return {"found": True, "relic": _relic_dict(entry)}
    relics = btd6_data_service.list_ct_relics()
    category = str(arguments.get("category") or "").strip().lower()
    if category:
        relics = tuple(r for r in relics if r.category == category)
        if not relics:
            return {"found": False, "note": f"no relics in category {category!r}"}
    return {
        "found": True,
        "count": len(relics),
        "category": category or "all",
        "relics": [_relic_dict(r) for r in relics],
    }


# --- btd6_power_lookup -------------------------------------------------------

_BTD6_POWER_LOOKUP_SPEC = AIToolSpec(
    name="btd6_power_lookup",
    description=(
        "BTD6 consumable Power info (Monkey Boost, Cash Drop, Road Spikes, Camo "
        "Trap, MOAB Mine, Super Monkey Storm, Pontoon, Tech Bot, …): each Power's "
        "effect, Monkey Money cost, and how many a purchase grants. Pass a Power "
        "name to look one up, or omit it to list every Power. Use for 'what does "
        "Monkey Boost do', 'how much is the Camo Trap power', 'list the powers'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "power": {
                "type": "string",
                "description": "Power name (e.g. 'Monkey Boost'); omit to list all.",
            },
        },
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


def _power_dict(entry: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        "name": entry.canonical,
        "description": entry.description,
        "monkey_money_cost": entry.monkey_money_cost,
        "quantity": entry.quantity,
        "usable_between_rounds": entry.between_rounds,
    }
    if entry.effect:
        # Structured headline factor(s) — e.g. Monkey Boost rate_scale 0.5 (2x
        # attack speed) for 15s. Lets the model state the effect precisely, though
        # *applying* it to a specific tower's stat is a separate (future) tool.
        out["effect"] = dict(entry.effect)
    return out


def _find_power(name: str) -> Any:
    from services import btd6_data_service

    return btd6_data_service.find_power(name)


async def _btd6_power_lookup(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_data_service

    name = str(arguments.get("power") or "").strip()
    if name:
        entry = _find_power(name)
        if entry is None:
            return {"found": False, "note": f"unknown power: {name!r}"}
        return {"found": True, "power": _power_dict(entry)}
    powers = btd6_data_service.get_dataset().powers
    return {
        "found": True,
        "count": len(powers),
        "powers": [_power_dict(p) for p in powers],
    }


# --- btd6_monkey_knowledge_lookup --------------------------------------------

_BTD6_MK_LOOKUP_SPEC = AIToolSpec(
    name="btd6_monkey_knowledge_lookup",
    description=(
        "BTD6 Monkey Knowledge info: each MK point's effect, in-game category "
        "(Primary / Military / Magic / Support / Heroes / Powers), Monkey Money "
        "cost, and how many points must already be spent in that tab to unlock it. "
        "Pass a knowledge name to look one up, a category to list that tab, or omit "
        "both to list everything. Use for 'what does Supa-Thrive do', 'list the "
        "magic monkey knowledge', 'how much is Bigger Bloon Sabotage'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "knowledge": {
                "type": "string",
                "description": "MK point name (e.g. 'Supa-Thrive'); omit to list.",
            },
            "category": {
                "type": "string",
                "description": "Filter: Primary / Military / Magic / Support / Heroes / Powers.",
            },
        },
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


def _mk_dict(entry: Any) -> dict[str, Any]:
    out = {
        "name": entry.canonical,
        "category": entry.category,
        "description": entry.description,
        "monkey_money_cost": entry.monkey_money_cost,
        "investment_required": entry.investment_required,
    }
    # Structured, dump-native magnitude(s) where the knowledge carries them (e.g.
    # More Cash {"factors": [{"kind": "starting_cash", "addition": 200}]}). Lets
    # the model state the exact factor, grounded by both the number and the
    # description. Absent for purely behavioural knowledge (description-only).
    if entry.effect:
        out["effect"] = dict(entry.effect)
    return out


def _find_mk(name: str) -> Any:
    from services import btd6_data_service

    needle = name.strip().lower()
    entries = btd6_data_service.get_dataset().monkey_knowledge
    exact = [k for k in entries if k.canonical.lower() == needle or k.id == needle]
    if exact:
        return exact[0]
    partial = [k for k in entries if needle in k.canonical.lower()]
    return partial[0] if len(partial) == 1 else None


async def _btd6_monkey_knowledge_lookup(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_data_service

    name = str(arguments.get("knowledge") or "").strip()
    if name:
        entry = _find_mk(name)
        if entry is None:
            return {"found": False, "note": f"unknown monkey knowledge: {name!r}"}
        return {"found": True, "knowledge": _mk_dict(entry)}
    entries = btd6_data_service.get_dataset().monkey_knowledge
    category = str(arguments.get("category") or "").strip().lower()
    if category:
        entries = tuple(k for k in entries if k.category.lower() == category)
        if not entries:
            return {"found": False, "note": f"no monkey knowledge in {category!r}"}
    return {
        "found": True,
        "count": len(entries),
        "category": category or "all",
        "knowledge": [_mk_dict(k) for k in entries],
    }


# --- btd6_geraldo_lookup -----------------------------------------------------

_BTD6_GERALDO_SPEC = AIToolSpec(
    name="btd6_geraldo_lookup",
    description=(
        "BTD6 Geraldo shop item info (Blade Trap, Genie Bottle, Sharpening "
        "Stone, Pet Rabbit, Paragon Power Totem, …): each item's effect, in-game "
        "cash cost, the Geraldo level it unlocks at, and how many he stocks. "
        "Geraldo (the hero) sells these from his shop. Some items carry a "
        "structured `effect` with exact numbers (Sharpening Stone +1 pierce for "
        "10 rounds, Jar of Pickles +1 damage at 0.75x attack speed for 5 rounds, "
        "Fertilizer +20% farm cash for 4 rounds, Rejuv Potion +50 lives). Pass an "
        "item name to look one up, or omit it to list every item. Use for 'what "
        "does Geraldo's Sharpening Stone do', 'how much is the Genie Bottle', "
        "'what level does the Paragon Power Totem unlock', 'list Geraldo's items'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "item": {
                "type": "string",
                "description": "Geraldo item name (e.g. 'Genie Bottle'); omit to list all.",
            },
        },
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


def _geraldo_dict(entry: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        "name": entry.canonical,
        "description": entry.description,
        "cost": entry.cost,
        "unlock_level": entry.unlock_level,
        "starting_quantity": entry.starting_quantity,
        "max_quantity": entry.max_quantity,
        "rounds_to_replenish": entry.rounds_to_replenish,
        "amount_to_replenish": entry.amount_to_replenish,
        "usable_between_rounds": entry.between_rounds,
    }
    if entry.effect:
        # Structured factor(s) decoded from the dump — e.g. Sharpening Stone
        # +1 pierce for 10 rounds; lets the model state the exact numbers.
        out["effect"] = dict(entry.effect)
    return out


async def _btd6_geraldo_lookup(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_data_service

    name = str(arguments.get("item") or "").strip()
    if name:
        entry = btd6_data_service.find_geraldo_item(name)
        if entry is None:
            return {"found": False, "note": f"unknown geraldo item: {name!r}"}
        return {"found": True, "item": _geraldo_dict(entry)}
    items = btd6_data_service.get_dataset().geraldo_items
    return {
        "found": True,
        "count": len(items),
        "items": [_geraldo_dict(g) for g in items],
    }


# --- btd6_boss_lookup --------------------------------------------------------

_BTD6_BOSS_SPEC = AIToolSpec(
    name="btd6_boss_lookup",
    description=(
        "BTD6 Boss Bloon info (Bloonarius, Lych, Vortex, Dreadbloon, "
        "Blastapopoulos, Phayze, Diamondback): each boss's game-authored mechanic "
        "description, its damage-type immunities, and the per-tier health + speed "
        "for all five boss tiers — Standard in `tiers` AND the Elite variant in "
        "`elite_tiers` (health scales up sharply by tier; co-op multiplies it "
        "further). Answer Elite questions from elite_tiers, never from the "
        "Standard table. Pass a boss name to look one up, or omit it to "
        "list every boss. Use for 'how much health does a tier 3 Bloonarius have', "
        "'elite lych hp per tier', 'what is Dreadbloon immune to', 'how fast is "
        "Vortex', 'what does Lych do', 'list the bosses'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "boss": {
                "type": "string",
                "description": "Boss name (e.g. 'Bloonarius'); omit to list all.",
            },
        },
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


def _boss_dict(entry: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        "name": entry.canonical,
        "description": entry.description,
        # Per-tier {tier, health, speed} for the five boss tiers — the headline
        # grounded numbers (e.g. tier 3 Bloonarius = 350,000 health).
        "tiers": [dict(t) for t in entry.tiers],
    }
    if entry.elite_tiers:
        # The Elite variant's own table (BUG-0002: without it, Standard
        # figures were the only numbers available to "Elite" questions).
        out["elite_tiers"] = [dict(t) for t in entry.elite_tiers]
    if entry.tagline:
        out["tagline"] = entry.tagline
    if entry.immune_to:
        out["immune_to"] = list(entry.immune_to)
    return out


async def _btd6_boss_lookup(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_data_service

    name = str(arguments.get("boss") or "").strip()
    if name:
        entry = btd6_data_service.find_boss(name)
        if entry is None:
            return {"found": False, "note": f"unknown boss: {name!r}"}
        return {"found": True, "boss": _boss_dict(entry)}
    bosses = btd6_data_service.get_dataset().bosses
    return {
        "found": True,
        "count": len(bosses),
        "bosses": [_boss_dict(b) for b in bosses],
    }


# --- btd6_bloon_filter -------------------------------------------------------

_BTD6_BLOON_FILTER_SPEC = AIToolSpec(
    name="btd6_bloon_filter",
    description=(
        "Filter the BTD6 bloon catalog by trait. Use for 'which bloons are camo "
        "/ lead / fortified / regrow', 'which bloons are immune to Explosion', "
        "'list the MOAB-class bloons'. Pass property (camo, lead, fortified, "
        "regrow, black, moab-class), category (basic, special, moab_class, "
        "modifier), and/or immune (a damage type: Explosion, Sharp, Cold, "
        "Energy, Plasma, Fire …). Omit all to list every bloon. IMPORTANT: "
        "camo / fortified / regrow are also MODIFIERS that can be applied to "
        "other bloons in some rounds/modes — when the result carries a "
        "`modifiers` entry, say so rather than implying only the listed bloons "
        "ever carry the trait."
    ),
    parameters={
        "type": "object",
        "properties": {
            "property": {
                "type": "string",
                "description": "Trait tag, e.g. 'camo', 'lead', 'fortified', 'regrow', 'moab-class'.",
            },
            "category": {
                "type": "string",
                "description": "Bloon class: basic / special / moab_class / modifier.",
            },
            "immune": {
                "type": "string",
                "description": "Damage type the bloon resists, e.g. 'Explosion', 'Sharp', 'Cold'.",
            },
        },
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


def _bloon_dict(entry: Any) -> dict[str, Any]:
    return {
        "name": entry.canonical,
        "category": entry.category,
        "properties": list(entry.properties),
        "immune_to": list(entry.immune_to),
        "description": entry.description,
    }


async def _btd6_bloon_filter(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_data_service

    prop = str(arguments.get("property") or "").strip() or None
    category = str(arguments.get("category") or "").strip() or None
    immune = str(arguments.get("immune") or "").strip() or None
    matches = btd6_data_service.filter_bloons(
        bloon_property=prop,
        category=category,
        immune=immune,
    )
    # Split the inherently-tagged bloons from the modifier pseudo-entries so the
    # model can answer faithfully ("DDT is inherently Camo; Camo is also a
    # modifier other bloons can gain") instead of implying a closed set.
    real = [b for b in matches if b.category != "modifier"]
    modifiers = [b for b in matches if b.category == "modifier"]
    if not matches:
        return {
            "found": False,
            "filter": {"property": prop, "category": category, "immune": immune},
            "note": "no bloons match that filter",
        }
    out: dict[str, Any] = {
        "found": True,
        "filter": {"property": prop, "category": category, "immune": immune},
        "count": len(real),
        "bloons": [_bloon_dict(b) for b in real],
    }
    if modifiers:
        out["modifiers"] = [
            {"name": m.canonical, "applies_broadly": True, "note": m.description}
            for m in modifiers
        ]
    return out


# --- btd6_cumulative_cost ----------------------------------------------------

_BTD6_CUMULATIVE_COST_SPEC = AIToolSpec(
    name="btd6_cumulative_cost",
    description=(
        "Total cumulative cost to REACH each BTD6 upgrade tier on a tower — the "
        "tower base cost plus every earlier tier on that path, ALREADY SUMMED. "
        "Use for 'total cost to reach <upgrade>', 'cost to get to tier 5', 'how "
        "much for the whole path', 'base cost and all earlier upgrades "
        "included'. Pass the tower and optionally difficulty (easy / medium / "
        "hard / impoppable; default medium) and/or path (top / mid / bot). "
        "For a CROSSPATHED tower ('how much is a 0-4-1 desperado', '10 041 "
        "despos' = TEN 0-4-1s), pass crosspath (e.g. '0-4-1') and optionally "
        "quantity — that returns the full unit cost for all four difficulties "
        "plus quantity totals. Returns the exact running totals — do NOT add "
        "the per-tier prices yourself: difficulty pricing rounds each purchase "
        "to $5 before summing, so a sum-then-scale total is off by a few "
        "dollars. The returned figures ARE the grounded answer."
    ),
    parameters={
        "type": "object",
        "properties": {
            "tower": {
                "type": "string",
                "description": "Tower name (e.g. 'Tack Shooter').",
            },
            "difficulty": {
                "type": "string",
                "description": "easy / medium / hard / impoppable (default medium).",
            },
            "path": {
                "type": "string",
                "description": "Limit to one path: top / mid / bot (omit for all three).",
            },
            "crosspath": {
                "type": "string",
                "description": (
                    "Full upgrade state, e.g. '0-4-1' or '041' — returns the "
                    "complete tower cost (base + both paths) per difficulty."
                ),
            },
            "quantity": {
                "type": "integer",
                "description": (
                    "How many such towers (with crosspath); adds "
                    "total_costs_by_difficulty."
                ),
            },
        },
        "required": ["tower"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


async def _btd6_cumulative_cost(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_data_service

    tower = str(arguments.get("tower") or "").strip()
    if not tower:
        return {"found": False, "note": "tower is required"}
    crosspath = str(arguments.get("crosspath") or "").strip()
    if crosspath:
        raw_quantity = arguments.get("quantity")
        quantity: int | None = None
        if raw_quantity is not None:
            try:
                quantity = int(raw_quantity)
            except (TypeError, ValueError):
                return {"found": False, "note": "quantity must be an integer"}
            if quantity > 999:
                # Same laundering gate as btd6_difficulty_cost: an absurd
                # count is the "10 041" notation misread as one number; the
                # product would enter the trusted ledger and self-ground.
                return {
                    "found": False,
                    "note": (
                        f"quantity {quantity} is not a plausible tower count. "
                        "If the user wrote something like '10 041', that "
                        "means 10 towers at crosspath 0-4-1 — retry with "
                        "quantity=10."
                    ),
                }
        return btd6_data_service.crosspath_cost(
            tower,
            crosspath,
            quantity=quantity,
        )
    difficulty = str(arguments.get("difficulty") or "medium").strip() or "medium"
    path = str(arguments.get("path") or "").strip() or None
    return btd6_data_service.cumulative_upgrade_costs(
        tower,
        difficulty=difficulty,
        path=path,
    )


# --- btd6_power_effect -------------------------------------------------------

_BTD6_POWER_EFFECT_SPEC = AIToolSpec(
    name="btd6_power_effect",
    description=(
        "Apply a BTD6 Power to a specific tower/upgrade's attack stat and get the "
        "boosted number. Use for 'what's <tower>'s attack speed ON a Monkey "
        "Boost', '<upgrade> with Monkey Boost', 'how fast does <tower> attack "
        "while boosted'. Pass the power (e.g. 'Monkey Boost') and the tower or "
        "upgrade (e.g. 'Crossbow Master', 'Dart Monkey', 'ninja 0-4-0'). Returns "
        "base vs boosted attacks-per-second and cooldown plus the duration — the "
        "grounded answer; do NOT compute the multiplied rate yourself. Only "
        "Powers that actually change a tower stat resolve (Monkey Boost speeds up "
        "attacks); for economy/bloon/placed-damage Powers it returns found=false "
        "with a note — use btd6_power_lookup for those."
    ),
    parameters={
        "type": "object",
        "properties": {
            "power": {
                "type": "string",
                "description": "Power name (e.g. 'Monkey Boost').",
            },
            "tower": {
                "type": "string",
                "description": "Tower or upgrade (e.g. 'Crossbow Master', 'Dart Monkey').",
            },
        },
        "required": ["power", "tower"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


async def _btd6_power_effect(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_upgrade_detail_service

    power = str(arguments.get("power") or "").strip()
    tower = str(arguments.get("tower") or "").strip()
    if not power or not tower:
        return {"found": False, "note": "both power and tower are required"}
    return btd6_upgrade_detail_service.power_effect(power, tower)


# --- btd6_buff_uptime --------------------------------------------------------

_BTD6_BUFF_UPTIME_SPEC = AIToolSpec(
    name="btd6_buff_uptime",
    description=(
        "Compute an Alchemist buff's UPTIME on a specific tower. Use for 'what's "
        "the uptime of a <alch tier> buff on <tower>', 'can a <alch> keep <tower> "
        "buffed', 'does <tower> attack fast enough to drain the brew'. The buff "
        "(Berserker Brew / Stronger Stimulant, or the Acidic Mixture Dip lead "
        "buff) is dual-limited — it ends at the earlier of a time window OR a "
        "number of the buffed tower's attacks — so a fast tower can hit the "
        "attack cap before the timer. Pass buff_source (e.g. 'Stronger Stimulant', "
        "'alchemist 4-0-0', 'Berserker Brew') and target (e.g. 'Grandmaster "
        "Ninja', 'ninja 5-0-0'). Returns which limiter binds (time vs attacks), "
        "the effective window, attacks buffed, and uptime% — the grounded answer; "
        "do NOT estimate it yourself. Pass targets=N when the one Alchemist is "
        "buffing N towers in range (it round-robins, so per-tower uptime drops) — "
        "for 'can one alch keep N towers buffed'. Returns found=false with an "
        "honest note if the buff's duration/cap isn't decoded into the data yet."
    ),
    parameters={
        "type": "object",
        "properties": {
            "buff_source": {
                "type": "string",
                "description": (
                    "Alchemist upgrade/tier applying the buff "
                    "(e.g. 'Stronger Stimulant', 'alchemist 4-0-0')."
                ),
            },
            "target": {
                "type": "string",
                "description": (
                    "Tower/upgrade receiving the buff "
                    "(e.g. 'Grandmaster Ninja', 'ninja 5-0-0')."
                ),
            },
            "targets": {
                "type": "integer",
                "minimum": 1,
                "description": (
                    "How many towers in range the one Alchemist is buffing "
                    "(default 1). The alch round-robins its throws across them."
                ),
            },
            "alch_speed": {
                "type": "string",
                "description": (
                    "Optional attack-speed buff ON THE ALCHEMIST itself (e.g. "
                    "'Monkey Boost', 'Jungle Drums', 'Overclock') — it speeds the "
                    "brew throw, so the alch keeps more towers buffed. Use for "
                    "'with Jungle Drums, can my alch keep N towers buffed'."
                ),
            },
        },
        "required": ["buff_source", "target"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


async def _btd6_buff_uptime(arguments: dict[str, Any]) -> dict[str, Any]:
    from services import btd6_upgrade_detail_service

    buff_source = str(arguments.get("buff_source") or "").strip()
    target = str(arguments.get("target") or "").strip()
    if not buff_source or not target:
        return {"found": False, "note": "both buff_source and target are required"}
    raw_targets = arguments.get("targets", 1)
    try:
        targets = max(1, int(raw_targets))
    except (TypeError, ValueError):
        targets = 1
    alch_speed = str(arguments.get("alch_speed") or "").strip() or None
    return btd6_upgrade_detail_service.buff_uptime(
        buff_source,
        target,
        targets=targets,
        alch_speed=alch_speed,
    )


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
    # Degree-independent end-of-round income (Navarch of the Seas $3,200) —
    # without it the tool reads as pure combat and the model denies the income.
    pstats = ss.get_paragon_stats(paragon_id)
    income = pstats.income_per_round if pstats is not None else None
    income_fields: dict[str, Any] = (
        {
            "income_per_round": income,
            "income_note": (
                "generates this cash at the end of each round, at every degree"
            ),
        }
        if income is not None
        else {}
    )
    return {
        "found": True,
        "paragon": stats.canonical,
        "tower": stats.tower_canonical,
        "degree": stats.degree,
        **income_fields,
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


# --- self-awareness tools (answerability Phase 3, Q-0047/Q-0048) -------
#
# Thin read-only wrappers over ``services.ai_introspection_service`` (the #616
# read model). Audience filtering happens at CONSTRUCTION: each factory bakes
# the caller's ``AIScope`` in, so the model can never ask for a higher tier —
# there is no scope/audience tool argument at all. All three are deterministic
# reads; none mutates settings, cooldown, or audit state. Imports are lazy
# because ``ai_introspection_service`` imports this module (specs/catalogue).

_AI_TOOL_CATALOG_SPEC = AIToolSpec(
    name="get_ai_tool_catalog",
    description=(
        "List the tools YOU (this bot) can call for the asking user — your "
        "live capability catalog: each tool's name, a one-line purpose, its "
        "toolsets, and that it is read-only. Call this to answer 'what can "
        "you do (here)?', 'what tools/capabilities do you have?', 'can you "
        "look up X?'. The list is already filtered to the asker's permission "
        "tier — higher-tier tools are counted in hidden_above_scope but "
        "never named, so answer from the returned list only and do not "
        "speculate about hidden tools. Every listed tool is read-only: you "
        "can look things up but never change settings or perform actions."
    ),
    parameters=_NO_ARGS_SCHEMA,
    min_scope=AIScope.USER,
)

# One-line purpose cap for the catalog payload. Full spec descriptions run to
# paragraphs (the model already sees them verbatim as its tool specs); the
# catalog answer needs a scannable line per tool, not a second copy of the
# whole registry, or a single call would eat the token budget.
_PURPOSE_SUMMARY_CHARS = 160


def _one_line_purpose(purpose: str) -> str:
    collapsed = " ".join(purpose.split())
    if len(collapsed) <= _PURPOSE_SUMMARY_CHARS:
        return collapsed
    return collapsed[: _PURPOSE_SUMMARY_CHARS - 1].rstrip() + "…"


def _make_ai_tool_catalog(scope: AIScope) -> ToolHandler:
    async def handler(_arguments: dict[str, Any]) -> dict[str, Any]:
        from services import ai_introspection_service

        snap = ai_introspection_service.build_tool_catalog(scope)
        return {
            "audience": snap.audience,
            "total_visible": snap.total_visible,
            "hidden_above_scope": snap.hidden_above_scope,
            "toolsets_present": list(snap.toolsets_present),
            "tools": [
                {
                    "name": tool.name,
                    "purpose": _one_line_purpose(tool.purpose),
                    "min_scope": tool.min_scope,
                    "toolsets": list(tool.toolsets),
                    "read_only": tool.read_only,
                    "grounds_btd6": tool.grounds_btd6,
                }
                for tool in snap.tools
            ],
            "note": (
                "Read-only capability catalog, already filtered to the asking "
                "user's permission tier; hidden_above_scope counts higher-tier "
                "tools without naming them."
            ),
        }

    return handler


_AI_POLICY_EXPLANATION_SPEC = AIToolSpec(
    name="get_ai_policy_explanation",
    description=(
        "Explain the bot's reply policy for THIS channel and the asking "
        "user: whether a mentioning message is allowed right now, the "
        "effective reply mode, which level of configuration decided it "
        "(guild / category / channel / role), the minimum XP level, and the "
        "cooldown — plus, for admins, the policy precedence trace and the "
        "most recent allow/deny decisions in this channel. Call this for "
        "'why didn't you reply (to me / to them)?', 'why can't you talk "
        "here?', 'what are the AI reply rules here?'. Answer from the "
        "returned fields; never guess at cooldowns, levels, or policy."
    ),
    parameters=_NO_ARGS_SCHEMA,
    min_scope=AIScope.USER,
)


def _make_ai_policy_explanation(
    guild_id: int,
    actor_id: int,
    scope: AIScope,
    member: Any = None,
    channel: Any = None,
) -> ToolHandler:
    async def handler(_arguments: dict[str, Any]) -> dict[str, Any]:
        from services import ai_introspection_service
        from services.ai_natural_language_policy import MessageContext

        # The explanation is bound to the asking user in the asking channel —
        # the model cannot point it at another member or channel. Evaluated as
        # a mentioning message (the shape of the turn that invoked it), so the
        # answer describes the rules in effect rather than re-litigating the
        # current, already-allowed turn.
        snap = await ai_permission_service.snapshot(guild_id, actor_id)
        channel_id = int(getattr(channel, "id", 0) or 0)
        raw_category_id = getattr(channel, "category_id", None)
        ctx = MessageContext(
            guild_id=guild_id,
            channel_id=channel_id,
            category_id=(int(raw_category_id) if raw_category_id is not None else None),
            user_id=actor_id,
            user_level=snap.level,
            user_role_ids=tuple(
                int(role.id) for role in (getattr(member, "roles", None) or ())
            ),
            is_mention=True,
            is_fresh_user=snap.is_fresh_user,
        )
        explanation = await ai_introspection_service.build_policy_explanation(
            ctx,
            scope=scope,
        )
        return {
            "audience": explanation.audience,
            "channel_id": channel_id or None,
            "allowed": explanation.allowed,
            "reason_code": explanation.reason_code,
            "effective_mode": explanation.effective_mode,
            "effective_source": explanation.effective_source,
            "effective_min_level": explanation.effective_min_level,
            "effective_cooldown_seconds": explanation.effective_cooldown,
            "precedence_trace": list(explanation.precedence_trace),
            "recent_decisions": [
                {
                    "decision": row.decision,
                    "reason_code": row.reason_code,
                    "task": row.task,
                    "at": row.at,
                }
                for row in explanation.recent_decisions
            ],
            "note": (
                "Evaluated for the asking user in this channel as a "
                "mentioning message; precedence_trace and recent_decisions "
                "are admin-only and empty for regular users."
            ),
        }

    return handler


_BTD6_ANSWERABILITY_SPEC = AIToolSpec(
    name="btd6_answerability",
    description=(
        "Inventory of the verified BTD6 data this bot can answer about: each "
        "loaded data domain (towers, heroes, maps, rounds, bloons, bosses, "
        "powers, Monkey Knowledge, Geraldo items, CT relics, …) with its item "
        "count, the deterministic calculations (round cash, difficulty cost, "
        "cumulative upgrade cost, paragon math), the live Ninja-Kiwi-backed "
        "domain, and the EXPLICIT unsupported gaps (alternate round sets/ABR, "
        "achievements, Rogue/Frontier, modified economy). Call this for 'what "
        "BTD6 data do you know/have?', 'what BTD6 questions can you answer?', "
        "'do you have X data?'. Quote counts and versions from the result, "
        "and state unsupported areas from the returned gaps instead of "
        "guessing or overclaiming."
    ),
    parameters=_NO_ARGS_SCHEMA,
    min_scope=AIScope.USER,
)


async def _btd6_answerability(_arguments: dict[str, Any]) -> dict[str, Any]:
    from services import ai_introspection_service

    snap = ai_introspection_service.build_btd6_answerability()
    return {
        "available": snap.available,
        "data_version": snap.data_version,
        "game_version": snap.game_version,
        "source": snap.source_label,
        "domains": [
            {
                "name": domain.name,
                "kind": domain.kind,
                "item_count": domain.item_count,
                "note": domain.note,
            }
            for domain in snap.domains
        ],
    }


@dataclass(frozen=True)
class ToolRegistry:
    """The tools offered for one request: specs (data) + live handlers."""

    specs: tuple[AIToolSpec, ...]
    handlers: Mapping[str, ToolHandler]


# Tools whose results are BTD6 *facts* and may therefore ground a BTD6 answer.
# The natural-language stage captures ONLY these tools' outputs into the
# faithfulness ledger — server/user/config tools (member counts, timestamps,
# IDs) must never whitelist a hallucinated BTD6 name or number. **Derived** from
# the canonical catalogue's ``grounding_domain`` metadata (the single source of
# truth), so it can no longer drift from the registered tool set by hand;
# ``tests/unit/services/test_ai_tools.py`` still pins it == the registered
# ``btd6_*`` tools.
BTD6_GROUNDING_TOOL_NAMES: frozenset[str] = ai_tool_catalogue.grounding_tool_names(
    "btd6",
)


# --- open_support_ticket (the one confirmation-REQUESTING tool) --------
#
# Every other tool here reads and returns a dict. This one does the same plus
# one advisory side effect: it does NOT open a ticket itself. It validates the
# asker's eligibility (the per-user open cap + blacklist + "is the guild set
# up?") and, when eligible, emits ``ticket.open_requested`` so TicketCog posts a
# one-click [Open ticket]/[Cancel] confirmation in the channel. The actual write
# runs only when the user clicks, through the audited
# ``ticket_mutation.open_ticket`` seam — so the mutation stays behind an explicit
# human confirmation (the module's mutation contract), and the AI never opens a
# channel on its own. Owner decision Q-0201 (the feature was requested to "work
# through the AI with natural language", confirmed by a button click).

_OPEN_SUPPORT_TICKET_SPEC = AIToolSpec(
    name="open_support_ticket",
    description=(
        "Offer to open a PRIVATE support ticket for the asking user in THIS "
        "server. Call this when the user wants staff help, wants to report "
        "something privately, or asks to open/create a ticket (e.g. 'open a "
        "ticket, I need help with X', 'can I talk to a mod privately', 'I want "
        "to report a user'). Pass a concise `subject` summarising their issue. "
        "This does NOT open the ticket directly — it posts a one-click confirm "
        "button the user taps to actually create it (so they stay in control). "
        "It only works when an admin has set tickets up and the user is under "
        "the open-ticket limit / not blacklisted; the result tells you whether "
        "a confirmation was offered (`requested`) or why not (`reason`). When "
        "`requested` is true, tell the user to click the button below. Do NOT "
        "call it for general questions you can answer yourself."
    ),
    parameters={
        "type": "object",
        "properties": {
            "subject": {
                "type": "string",
                "description": (
                    "A short summary of what the user needs help with "
                    "(becomes the ticket's subject)."
                ),
            },
        },
        "required": ["subject"],
        "additionalProperties": False,
    },
    min_scope=AIScope.USER,
)


def _make_open_support_ticket(guild: Any, member: Any, channel: Any) -> ToolHandler:
    async def handler(arguments: dict[str, Any]) -> dict[str, Any]:
        subject = str(arguments.get("subject") or "").strip()
        if not subject:
            return {
                "requested": False,
                "reason": "missing_subject",
                "note": "Ask the user what they need help with, then call again.",
            }
        channel_id = getattr(channel, "id", None)
        if channel_id is None:
            return {
                "requested": False,
                "reason": "no_channel",
                "note": "I can't post a confirmation here.",
            }
        from services import ticket_service

        eligibility = await ticket_service.check_open_eligibility(guild.id, member.id)
        if not eligibility.allowed:
            return {
                "requested": False,
                "reason": eligibility.reason,
                "note": eligibility.message,
            }
        # Eligible: ask TicketCog to post the [Open ticket]/[Cancel] confirm.
        # No ticket is created here — the write waits for the user's click.
        from core.events import bus

        try:
            await bus.emit(
                "ticket.open_requested",
                guild_id=guild.id,
                channel_id=channel_id,
                user_id=member.id,
                subject=subject[:200],
            )
        except Exception:  # pragma: no cover — publish-accepted; never raises up
            return {
                "requested": False,
                "reason": "post_failed",
                "note": "I couldn't post the confirmation. Try `!ticket new`.",
            }
        return {
            "requested": True,
            "subject": subject[:200],
            "note": (
                "I've posted an 'Open ticket' button below — tell the user to "
                "click it to create their private ticket."
            ),
        }

    return handler


# Every registered tool's spec, with no runtime binding (no guild/member/bot, no
# handlers). ``build_registry`` pairs these same spec constants with runtime-bound
# handlers per request; this flat tuple is the **runtime-independent** half a read
# model (the introspection / effective-policy preview layer) needs to report a tool's
# name, purpose, and ``min_scope`` without standing up a live registry. Includes the
# guild-/member-gated tools so a preview can describe the full surface. Pinned ==
# the canonical catalogue by ``test_ai_tools`` / ``test_ai_tool_catalogue``, so a tool
# added to ``build_registry`` (and the catalogue) without an entry here fails CI.
_ALL_TOOL_SPECS: tuple[AIToolSpec, ...] = (
    _USER_STANDING_SPEC,
    _SERVER_TIME_SPEC,
    _BTD6_LOOKUP_SPEC,
    _BTD6_LIST_ROSTER_SPEC,
    _BTD6_CAPABILITY_SPEC,
    _BTD6_SUPERLATIVE_SPEC,
    _BTD6_DIFFICULTY_COST_SPEC,
    _BTD6_ROUND_COMPOSITION_SPEC,
    _BTD6_ROUND_CASH_SPEC,
    _BTD6_MAP_LOOKUP_SPEC,
    _BTD6_MODE_LOOKUP_SPEC,
    _BTD6_RELIC_LOOKUP_SPEC,
    _BTD6_POWER_LOOKUP_SPEC,
    _BTD6_MK_LOOKUP_SPEC,
    _BTD6_GERALDO_SPEC,
    _BTD6_BOSS_SPEC,
    _BTD6_BLOON_FILTER_SPEC,
    _BTD6_CUMULATIVE_COST_SPEC,
    _BTD6_POWER_EFFECT_SPEC,
    _BTD6_BUFF_UPTIME_SPEC,
    _PARAGON_CALCULATE_SPEC,
    _PARAGON_REQUIREMENTS_SPEC,
    _BTD6_PARAGON_STATS_AT_DEGREE_SPEC,
    _BTD6_CT_TEAM_SPEC,
    _BTD6_ANSWERABILITY_SPEC,
    _GUILD_AI_CONFIG_SPEC,
    _RECENT_AUDIT_SPEC,
    _DIAGNOSTICS_HEALTH_SPEC,
    _AI_TOOL_CATALOG_SPEC,
    _AI_POLICY_EXPLANATION_SPEC,
    _SERVER_OVERVIEW_SPEC,
    _SERVER_ROLES_SPEC,
    _SERVER_CHANNELS_SPEC,
    _MEMBER_LOOKUP_SPEC,
    _MEMBER_LIST_SPEC,
    _OPEN_SUPPORT_TICKET_SPEC,
)


def all_tool_specs() -> dict[str, AIToolSpec]:
    """Every registered tool's provider-neutral spec, keyed by name.

    The runtime-independent catalogue half: no handlers, no ``guild``/``member``/
    ``bot`` arguments, so a read-only introspection or effective-policy preview can
    report each tool's name, purpose (``description``), and authoritative ``min_scope``
    without building a per-request :class:`ToolRegistry`. ``min_scope`` stays the single
    source of truth for authority. Keys match the canonical catalogue exactly (pinned by
    test), so this never silently diverges from the tools the model can actually be offered.
    """
    return {spec.name: spec for spec in _ALL_TOOL_SPECS}


def build_registry(
    *,
    scope: AIScope,
    guild_id: int,
    actor_id: int,
    guild: Any = None,
    member: Any = None,
    bot: Any = None,
    channel: Any = None,
    enabled_toolsets: Collection[str] | None = None,
    disabled_tools: Collection[str] | None = None,
) -> ToolRegistry:
    """Build the read-only tool set the caller's ``scope`` may be offered.

    ``specs`` are attached to the :class:`AIRequest` (the model sees
    them); ``handlers`` are passed to ``ai_gateway.execute`` as
    ``tool_handlers``. Only tools whose ``min_scope`` the caller
    satisfies are included.

    ``enabled_toolsets`` / ``disabled_tools`` are the optional orchestration policy
    (canonical-catalogue toolset names / explicit tool names). They can only **narrow**
    the offered set — never grant a tool above ``scope``. Both default to ``None``, which
    means "no toolset restriction": the registry then offers exactly the scope-allowed
    tools, identical to the historical behaviour. Selection is delegated to
    :func:`services.ai_tool_catalogue.select_tools` so it stays deterministic and
    inspectable.

    ``guild`` (the live ``discord.Guild``) and ``member`` (the asking
    ``discord.Member``) enable the server-introspection tools. When
    ``guild`` is ``None`` those tools are omitted, so existing callers
    that do not have a live guild keep the prior toolset. Member-level
    data (the ``lookup_member`` and ``list_all_members`` tools, plus member
    counts) is gated behind
    :func:`feature_flags.ai_server_member_lookup_enabled` — default off.

    ``bot`` (the live client) lets the platform-owner-only
    ``diagnostics_health_snapshot`` tool include gateway/latency facts; it is
    ``None``-tolerant, so callers without a client simply get a snapshot
    without the gateway subsystem. That tool is filtered out for every scope
    below ``PLATFORM_OWNER`` regardless.

    ``channel`` (the live channel the request came from) binds the
    ``get_ai_policy_explanation`` tool to the asking channel; ``None``-tolerant
    — without it the explanation is evaluated with no channel-specific layer
    (guild-level policy only).
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
        (_BTD6_ROUND_CASH_SPEC, _btd6_round_cash),
        (_BTD6_MAP_LOOKUP_SPEC, _btd6_map_lookup),
        (_BTD6_MODE_LOOKUP_SPEC, _btd6_mode_lookup),
        (_BTD6_RELIC_LOOKUP_SPEC, _btd6_relic_lookup),
        (_BTD6_POWER_LOOKUP_SPEC, _btd6_power_lookup),
        (_BTD6_MK_LOOKUP_SPEC, _btd6_monkey_knowledge_lookup),
        (_BTD6_GERALDO_SPEC, _btd6_geraldo_lookup),
        (_BTD6_BOSS_SPEC, _btd6_boss_lookup),
        (_BTD6_BLOON_FILTER_SPEC, _btd6_bloon_filter),
        (_BTD6_CUMULATIVE_COST_SPEC, _btd6_cumulative_cost),
        (_BTD6_POWER_EFFECT_SPEC, _btd6_power_effect),
        (_BTD6_BUFF_UPTIME_SPEC, _btd6_buff_uptime),
        (_PARAGON_CALCULATE_SPEC, _paragon_calculate),
        (_PARAGON_REQUIREMENTS_SPEC, _paragon_requirements),
        (_BTD6_PARAGON_STATS_AT_DEGREE_SPEC, _btd6_paragon_stats_at_degree),
        (_BTD6_CT_TEAM_SPEC, _make_btd6_ct_team_status(guild_id)),
        (_BTD6_ANSWERABILITY_SPEC, _btd6_answerability),
        (_GUILD_AI_CONFIG_SPEC, _make_guild_ai_config(guild_id)),
        (_RECENT_AUDIT_SPEC, _make_recent_audit(guild_id)),
        (_DIAGNOSTICS_HEALTH_SPEC, _make_diagnostics_health(bot, guild_id)),
        (_AI_TOOL_CATALOG_SPEC, _make_ai_tool_catalog(scope)),
        (
            _AI_POLICY_EXPLANATION_SPEC,
            _make_ai_policy_explanation(
                guild_id,
                actor_id,
                scope,
                member=member,
                channel=channel,
            ),
        ),
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
        if member is not None:
            # Needs the live guild + member + channel. It does not open a ticket
            # itself — it validates eligibility (guild set up, under the open
            # cap, not blacklisted) and emits ticket.open_requested so the cog
            # posts a one-click confirm; the open waits for the user's click.
            catalog.append(
                (
                    _OPEN_SUPPORT_TICKET_SPEC,
                    _make_open_support_ticket(guild, member, channel),
                ),
            )
    decisions = {
        d.name: d
        for d in ai_tool_catalogue.select_tools(
            [spec for spec, _ in catalog],
            scope=scope,
            enabled_toolsets=enabled_toolsets,
            disabled_tools=disabled_tools,
        )
    }
    specs: list[AIToolSpec] = []
    handlers: dict[str, ToolHandler] = {}
    for spec, handler in catalog:
        if decisions[spec.name].included:
            specs.append(spec)
            handlers[spec.name] = handler
    return ToolRegistry(specs=tuple(specs), handlers=handlers)


__all__ = ["BTD6_GROUNDING_TOOL_NAMES", "ToolRegistry", "build_registry"]
