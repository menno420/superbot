"""Private control API — the bot side of the developer-dashboard control panel.

The decoupled dashboard (``dashboard/``) cannot import the bot, so to let it
*read and drive* the bot's existing audited seams it talks to the bot over HTTP.
This module adds a small ``/control/*`` surface to the **existing** health server
(``healthserver.py``) — same aiohttp app, same private port — so no second server
is introduced.

Design (Q-0156 / Q-0159 — the live-editor foundation):

* **Dormant by default.** The routes are registered **only** when the
  ``CONTROL_API_TOKEN`` environment variable is set. A bot with no such variable
  (every current deploy) gets *zero* behaviour change — the surface does not
  exist. This makes merging it to production safe; it activates only when the
  token is deliberately configured on Railway.
* **Shared-secret auth.** Every ``/control/*`` request must present
  ``Authorization: Bearer <CONTROL_API_TOKEN>`` (constant-time compared). The
  health server already binds the **private** network only (a ``worker`` has no
  public domain), so the token is defence-in-depth, not the sole gate.
* **The bot is the authority (identity → authority bridge).** The dashboard
  asserts *"user X, guild Y"* (from its Discord OAuth session); the bot resolves
  the **live member** for every request and the **existing audited seam** enforces
  what that member may do — the same capability/permission gate every in-Discord
  surface uses. The browser's claim is never trusted on its own; the token only
  proves *the dashboard* is calling, never *who* the acting user is.

Endpoints:

* ``GET  /control/ping``                 — auth smoke.
* ``GET  /control/authority``            — the identity→authority bridge (read).
* ``POST /control/settings``             — front ``settings_mutation`` (capability-gated).
* ``POST /control/help/overlay``         — front ``help_overlay_mutation.set_overlay_fields``.
* ``POST /control/help/home``            — front ``help_overlay_mutation.set_home_message``.
* ``POST /control/help/reset``           — front ``help_overlay_mutation.reset_guild_overlay``.
* ``POST /control/routing``              — front ``command_routing.set_policy`` (admin-gated here,
  since that seam does not self-authorize — its in-bot caller does).

Every mutation flows through the **existing** audited service seam (validate → DB
write → cache invalidate → audit emit); this module never writes the bot's tables
directly (the CLAUDE.md "no mutation path bypasses the audited seam" rule). Live
alias editing has no audited DB seam yet (only the committed ``utils/synonyms.py``
map), so it is intentionally absent until that overlay lands.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
from typing import Any

from aiohttp import web

logger = logging.getLogger("bot.control_api")


# ---------------------------------------------------------------------------
# Token + auth
# ---------------------------------------------------------------------------


def control_token() -> str | None:
    """The shared control-API token, or ``None`` when the API is dormant."""
    token = os.environ.get("CONTROL_API_TOKEN", "").strip()
    return token or None


def _bearer(auth_header: str | None) -> str | None:
    """Extract the token from an ``Authorization: Bearer <token>`` header."""
    if not auth_header:
        return None
    prefix = "Bearer "
    if not auth_header.startswith(prefix):
        return None
    return auth_header[len(prefix) :].strip() or None


def is_authorized(auth_header: str | None, token: str | None) -> bool:
    """``True`` when ``auth_header`` carries the bearer ``token``.

    Constant-time comparison. A ``None``/empty configured ``token`` is never
    authorised (the API is dormant and the routes are not even registered).
    """
    if not token:
        return False
    presented = _bearer(auth_header)
    if presented is None:
        return False
    return hmac.compare_digest(presented, token)


# ---------------------------------------------------------------------------
# Response helpers
# ---------------------------------------------------------------------------


def _unauthorized() -> web.Response:
    return web.Response(
        text=json.dumps({"error": "unauthorized"}),
        status=401,
        content_type="application/json",
    )


def _json_response(payload: dict[str, Any], status: int = 200) -> web.Response:
    return web.Response(
        text=json.dumps(payload),
        status=status,
        content_type="application/json",
    )


# ---------------------------------------------------------------------------
# Identity → authority bridge (read)
# ---------------------------------------------------------------------------


def resolve_authority(bot: Any, guild_id: int, user_id: int) -> dict[str, Any]:
    """Resolve what ``user_id`` may do in ``guild_id`` — the authority bridge.

    Reads the live member from the bot's guild cache and reports the same
    **visibility tier** (`utils.visibility_rules`) every in-Discord surface uses,
    plus convenience flags. Read-only and side-effect-free. ``tier`` is ``None``
    when the bot is not in the guild or the user is not a member there (so the
    dashboard shows no controls for a guild the user cannot act in).
    """
    from core.runtime.guild_resources import resolve_member
    from utils.visibility_rules import get_member_visibility_tier

    guild = bot.get_guild(guild_id)
    if guild is None:
        return {
            "guild_id": guild_id,
            "user_id": user_id,
            "guild_found": False,
            "member_found": False,
            "tier": None,
        }
    member = resolve_member(guild, user_id)
    if member is None:
        return {
            "guild_id": guild_id,
            "user_id": user_id,
            "guild_found": True,
            "guild_name": guild.name,
            "member_found": False,
            "tier": None,
        }
    tier = get_member_visibility_tier(member, guild.owner_id)
    return {
        "guild_id": guild_id,
        "user_id": user_id,
        "guild_found": True,
        "guild_name": guild.name,
        "member_found": True,
        "tier": tier,
        "is_admin": bool(member.guild_permissions.administrator),
        "is_owner": member.id == guild.owner_id,
    }


# ---------------------------------------------------------------------------
# Write-context resolution + seam-error mapping
# ---------------------------------------------------------------------------


class _ControlError(Exception):
    """A pre-seam failure (auth / parse / resolution) carrying an HTTP status."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


# Seam exception class-name → HTTP status. Mapping by name keeps imports
# function-local (the services' cycle discipline) and is robust: 4xx for caller
# error, 403 for authority, 503 for an operator kill-switch.
_SEAM_ERROR_STATUS: dict[str, int] = {
    # settings_mutation
    "UnauthorizedSettingsMutationError": 403,
    "SettingsMutationDisabledError": 503,
    "UnknownSubsystemError": 400,
    "UndeclaredSettingError": 400,
    "UnmigrateableSettingError": 400,
    "SettingsCoercionError": 400,
    "SettingsValidationError": 400,
    "InvalidActorTypeError": 400,
    # help_overlay_mutation
    "UnauthorizedHelpOverlayMutationError": 403,
    "InvalidHelpOverlayValueError": 400,
}


async def _authed_write_context(
    request: web.Request,
) -> tuple[Any, Any, dict[str, Any]]:
    """Auth + parse + resolve the live member for a mutation request.

    Returns ``(guild, member, body)``. Raises :class:`_ControlError` with the
    right status when the token is wrong (401), the body is not a JSON object or
    is missing ``guild_id``/``user_id`` (400), the bot is not in the guild (404),
    or the user is not a live member there (403 — no authority to act).
    """
    if not is_authorized(request.headers.get("Authorization"), control_token()):
        raise _ControlError(401, "unauthorized")
    try:
        body = await request.json()
    except Exception as exc:  # noqa: BLE001 - any malformed body is a 400
        raise _ControlError(400, "request body must be a JSON object") from exc
    if not isinstance(body, dict):
        raise _ControlError(400, "request body must be a JSON object")
    try:
        guild_id = int(body["guild_id"])
        user_id = int(body["user_id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise _ControlError(400, "guild_id and user_id are required integers") from exc

    from core.runtime.guild_resources import resolve_member

    bot = request.app["bot"]
    guild = bot.get_guild(guild_id)
    if guild is None:
        raise _ControlError(404, f"bot is not in guild {guild_id}")
    member = resolve_member(guild, user_id)
    if member is None:
        raise _ControlError(403, f"user {user_id} is not a member of guild {guild_id}")
    return guild, member, body


def _seam_error_or_500(exc: Exception, context: str) -> web.Response:
    """Map a known seam exception to its HTTP status, else log + 500."""
    status = _SEAM_ERROR_STATUS.get(type(exc).__name__)
    if status is not None:
        return _json_response(
            {"error": str(exc), "kind": type(exc).__name__},
            status=status,
        )
    logger.exception("control_api: unexpected error in %s mutation", context)
    return _json_response({"error": "internal error"}, status=500)


def _is_admin(member: Any) -> bool:
    """True when ``member`` holds Discord's administrator permission."""
    perms = getattr(member, "guild_permissions", None)
    return bool(getattr(perms, "administrator", False))


# ---------------------------------------------------------------------------
# Read handlers
# ---------------------------------------------------------------------------


async def _ping_handler(request: web.Request) -> web.Response:
    """Auth smoke test — confirms the token without touching guild state."""
    if not is_authorized(request.headers.get("Authorization"), control_token()):
        return _unauthorized()
    return _json_response({"status": "ok", "service": "control_api"})


async def _authority_handler(request: web.Request) -> web.Response:
    """``GET /control/authority?guild_id=&user_id=`` → the authority bridge."""
    if not is_authorized(request.headers.get("Authorization"), control_token()):
        return _unauthorized()
    try:
        guild_id = int(request.query["guild_id"])
        user_id = int(request.query["user_id"])
    except (KeyError, ValueError):
        return _json_response(
            {"error": "guild_id and user_id are required integer query params"},
            status=400,
        )
    bot = request.app["bot"]
    return _json_response(resolve_authority(bot, guild_id, user_id))


# ---------------------------------------------------------------------------
# Mutation handlers — each fronts one existing audited seam
# ---------------------------------------------------------------------------


async def _settings_set_handler(request: web.Request) -> web.Response:
    """``POST /control/settings`` → ``SettingsMutationPipeline.set_value``.

    Body: ``{guild_id, user_id, subsystem, name, value}``. The pipeline coerces +
    validates ``value``, capability-gates the acting member, writes + audits, and
    invalidates the cache; its typed errors map to 400/403/503.
    """
    try:
        guild, member, body = await _authed_write_context(request)
    except _ControlError as err:
        return _json_response({"error": err.message}, status=err.status)

    subsystem = body.get("subsystem")
    name = body.get("name")
    if not isinstance(subsystem, str) or not isinstance(name, str):
        return _json_response(
            {"error": "subsystem and name are required strings"},
            status=400,
        )
    if "value" not in body:
        return _json_response({"error": "value is required"}, status=400)

    from services.settings_mutation import SettingsMutationPipeline

    try:
        result = await SettingsMutationPipeline().set_value(
            guild,
            subsystem,
            name,
            body["value"],
            member,
        )
    except Exception as exc:  # noqa: BLE001 - mapped to a status by _seam_error_or_500
        return _seam_error_or_500(exc, "settings")

    return _json_response(
        {
            "ok": True,
            "mutation_id": result.mutation_id,
            "subsystem": result.subsystem,
            "name": result.name,
            "settings_key": result.settings_key,
            "old_value": result.old_value,
            "new_value": result.new_value,
        },
    )


async def _help_overlay_handler(request: web.Request) -> web.Response:
    """``POST /control/help/overlay`` → ``help_overlay_mutation.set_overlay_fields``.

    Body: ``{guild_id, user_id, entity_kind, entity_key, display_hidden?,
    display_name?, description?}``. An **omitted** override field is left
    untouched; a field present as ``null`` resets it to inherit; a value
    overrides. The seam admin-gates the acting member.
    """
    try:
        guild, member, body = await _authed_write_context(request)
    except _ControlError as err:
        return _json_response({"error": err.message}, status=err.status)

    entity_kind = body.get("entity_kind")
    entity_key = body.get("entity_key")
    if not isinstance(entity_kind, str) or not isinstance(entity_key, str):
        return _json_response(
            {"error": "entity_kind and entity_key are required strings"},
            status=400,
        )
    # Only forward fields the caller actually sent → omitted == UNSET (untouched).
    overrides = {
        field: body[field]
        for field in ("display_hidden", "display_name", "description")
        if field in body
    }

    from services.help_overlay_mutation import set_overlay_fields

    try:
        result = await set_overlay_fields(
            guild.id,
            entity_kind,
            entity_key,
            actor=member,
            **overrides,
        )
    except Exception as exc:  # noqa: BLE001 - mapped by _seam_error_or_500
        return _seam_error_or_500(exc, "help_overlay")

    return _json_response(
        {
            "ok": True,
            "mutation_id": result.mutation_id,
            "entity_kind": result.entity_kind,
            "entity_key": result.entity_key,
            "new": result.new,
        },
    )


async def _help_home_handler(request: web.Request) -> web.Response:
    """``POST /control/help/home`` → ``help_overlay_mutation.set_home_message``.

    Body: ``{guild_id, user_id, title?, body?, color?}`` (omitted == untouched,
    null == reset to default).
    """
    try:
        guild, member, body = await _authed_write_context(request)
    except _ControlError as err:
        return _json_response({"error": err.message}, status=err.status)

    fields = {
        field: body[field] for field in ("title", "body", "color") if field in body
    }

    from services.help_overlay_mutation import set_home_message

    try:
        result = await set_home_message(guild.id, actor=member, **fields)
    except Exception as exc:  # noqa: BLE001 - mapped by _seam_error_or_500
        return _seam_error_or_500(exc, "help_home")

    return _json_response(
        {"ok": True, "mutation_id": result.mutation_id, "new": result.new},
    )


async def _help_reset_handler(request: web.Request) -> web.Response:
    """``POST /control/help/reset`` → ``help_overlay_mutation.reset_guild_overlay``.

    Body: ``{guild_id, user_id}``. Deletes every overlay row for the guild.
    """
    try:
        guild, member, _body = await _authed_write_context(request)
    except _ControlError as err:
        return _json_response({"error": err.message}, status=err.status)

    from services.help_overlay_mutation import reset_guild_overlay

    try:
        result = await reset_guild_overlay(guild.id, actor=member)
    except Exception as exc:  # noqa: BLE001 - mapped by _seam_error_or_500
        return _seam_error_or_500(exc, "help_reset")

    return _json_response(
        {"ok": True, "mutation_id": result.mutation_id, "prev": result.prev},
    )


async def _routing_set_handler(request: web.Request) -> web.Response:
    """``POST /control/routing`` → ``command_routing.set_policy``.

    Body: ``{guild_id, user_id, cog_name, enabled, scope_type?, scope_id?}``
    (``scope_type`` defaults to ``guild``; ``scope_id`` required for
    ``category``/``channel``). ``set_policy`` does **not** self-authorize, so this
    handler enforces the administrator gate before calling it.
    """
    try:
        guild, member, body = await _authed_write_context(request)
    except _ControlError as err:
        return _json_response({"error": err.message}, status=err.status)

    if not _is_admin(member):
        return _json_response(
            {"error": "cog routing requires administrator"},
            status=403,
        )

    cog_name = body.get("cog_name")
    enabled = body.get("enabled")
    scope_type = body.get("scope_type", "guild")
    scope_id = body.get("scope_id")
    if not isinstance(cog_name, str) or not cog_name:
        return _json_response({"error": "cog_name is required"}, status=400)
    if not isinstance(enabled, bool):
        return _json_response({"error": "enabled must be a boolean"}, status=400)
    if scope_type not in ("guild", "category", "channel"):
        return _json_response(
            {"error": "scope_type must be guild, category, or channel"},
            status=400,
        )
    if scope_type == "guild":
        scope_id = None
    elif not isinstance(scope_id, int) or isinstance(scope_id, bool):
        return _json_response(
            {"error": "scope_id (int) is required for category/channel scope"},
            status=400,
        )

    from services.command_routing import set_policy

    try:
        result = await set_policy(
            guild_id=guild.id,
            scope_type=scope_type,
            scope_id=scope_id,
            cog_name=cog_name,
            enabled=enabled,
            actor_id=member.id,
        )
    except Exception as exc:  # noqa: BLE001 - unexpected routing failure → 500
        return _seam_error_or_500(exc, "routing")

    return _json_response(
        {
            "ok": True,
            "mutation_id": result.mutation_id,
            "cog_name": result.cog_name,
            "scope_type": result.scope_type,
            "scope_id": result.scope_id,
            "old_enabled": result.old_enabled,
            "new_enabled": result.new_enabled,
        },
    )


# ---------------------------------------------------------------------------
# Guild-scoped read handlers (Phase E — "see-then-change")
#
# Until these existed, the live editors POSTed a new value but never showed the
# server's CURRENT one — they wrote blind. Each read resolves the live member and
# requires administrator (the same surface the editors gate on); the catalogue is
# global defaults so it is token-only. All read-only, dormant without the token.
# ---------------------------------------------------------------------------


async def _authed_read_context(request: web.Request) -> tuple[Any, Any]:
    """Auth + resolve the live member for a guild-scoped GET (query params).

    Returns ``(guild, member)``. Raises :class:`_ControlError` for 401 (token),
    400 (missing/non-int ``guild_id``/``user_id``), 404 (bot not in guild), or
    403 (user not a live member). The read mirror of :func:`_authed_write_context`.
    """
    if not is_authorized(request.headers.get("Authorization"), control_token()):
        raise _ControlError(401, "unauthorized")
    try:
        guild_id = int(request.query["guild_id"])
        user_id = int(request.query["user_id"])
    except (KeyError, ValueError) as exc:
        raise _ControlError(
            400,
            "guild_id and user_id are required integer query params",
        ) from exc

    from core.runtime.guild_resources import resolve_member

    bot = request.app["bot"]
    guild = bot.get_guild(guild_id)
    if guild is None:
        raise _ControlError(404, f"bot is not in guild {guild_id}")
    member = resolve_member(guild, user_id)
    if member is None:
        raise _ControlError(403, f"user {user_id} is not a member of guild {guild_id}")
    return guild, member


async def _resolve_guild_settings(guild_id: int) -> dict[str, list[dict[str, Any]]]:
    """Every subsystem's current scalar settings for ``guild_id``.

    Composes the canonical read path (``settings_resolution.resolve_batch`` —
    value · provenance · valid) with the declaring ``SettingSpec`` metadata (type
    · default · hint · allowed-values · governing capability) so the editor renders
    current-vs-default and the right input without a second source. Grouped by
    subsystem; subsystems with no settings are omitted.
    """
    from core.runtime.subsystem_schema import get_schema
    from services.settings_resolution import resolve_batch
    from utils.subsystem_registry import SUBSYSTEMS

    grouped: dict[str, list[dict[str, Any]]] = {}
    for subsystem in sorted(SUBSYSTEMS):
        schema = get_schema(subsystem)
        if schema is None or not schema.settings:
            continue
        spec_by_name = {spec.name: spec for spec in schema.settings}
        items: list[dict[str, Any]] = []
        for res in await resolve_batch(guild_id, subsystem):
            spec = spec_by_name.get(res.name)
            items.append(
                {
                    "name": res.name,
                    "settings_key": getattr(spec, "settings_key", "") or "",
                    "value": res.value,
                    "default": res.default,
                    "provenance": res.provenance,
                    "valid": res.valid,
                    "value_type": getattr(
                        getattr(spec, "value_type", None),
                        "__name__",
                        "str",
                    ),
                    "hint": getattr(spec, "hint", "") or "",
                    "allowed_values": list(getattr(spec, "allowed_values", ()) or ()),
                    "capability_required": getattr(spec, "capability_required", "")
                    or "",
                },
            )
        if items:
            grouped[subsystem] = items
    return grouped


async def _settings_current_handler(request: web.Request) -> web.Response:
    """``GET /control/settings/current?guild_id=&user_id=`` → current values.

    Administrator-gated (the editor surface). Returns every subsystem's resolved
    current scalar settings so the editor shows current-vs-default, not a blank box.
    """
    try:
        _guild, member = await _authed_read_context(request)
    except _ControlError as err:
        return _json_response({"error": err.message}, status=err.status)
    if not _is_admin(member):
        return _json_response(
            {"error": "reading server settings requires administrator"},
            status=403,
        )
    guild_id = int(request.query["guild_id"])
    try:
        subsystems = await _resolve_guild_settings(guild_id)
    except Exception as exc:  # noqa: BLE001 - never 500 the whole read on one bad spec
        return _seam_error_or_500(exc, "settings_current")
    return _json_response({"ok": True, "guild_id": guild_id, "subsystems": subsystems})


async def _help_overlay_get_handler(request: web.Request) -> web.Response:
    """``GET /control/help/overlay?guild_id=&user_id=`` → current help overlay.

    Administrator-gated. Returns the guild's per-entity overrides + Home message
    (``home`` is ``None`` when the default frame renders).
    """
    try:
        guild, member = await _authed_read_context(request)
    except _ControlError as err:
        return _json_response({"error": err.message}, status=err.status)
    if not _is_admin(member):
        return _json_response(
            {"error": "reading help overlay requires administrator"},
            status=403,
        )

    from services.help_overlay import get_guild_help_overlay

    try:
        overlay = await get_guild_help_overlay(guild.id)
    except Exception as exc:  # noqa: BLE001
        return _seam_error_or_500(exc, "help_overlay_read")

    rows = [
        {
            "entity_kind": r.entity_kind,
            "entity_key": r.entity_key,
            "display_hidden": r.display_hidden,
            "display_name": r.display_name,
            "description": r.description,
        }
        for r in overlay.rows
    ]
    home = (
        {
            "title": overlay.home.title,
            "body": overlay.home.body,
            "color": overlay.home.color,
        }
        if overlay.home is not None
        else None
    )
    return _json_response(
        {"ok": True, "guild_id": guild.id, "rows": rows, "home": home},
    )


async def _help_catalogue_handler(request: web.Request) -> web.Response:
    """``GET /control/help/catalogue`` → the editable hub/subsystem targets.

    Token-only (global defaults, no guild data). Lets the editor offer a real
    target picker + show each entity's default name/description (what an override
    deviates from).
    """
    if not is_authorized(request.headers.get("Authorization"), control_token()):
        return _unauthorized()

    from services.help_catalogue import build_help_catalogue

    try:
        catalogue = build_help_catalogue()
    except Exception as exc:  # noqa: BLE001
        return _seam_error_or_500(exc, "help_catalogue")

    hubs = [
        {
            "key": h.key,
            "display_name": getattr(h.entry, "display_name", h.key),
            "purpose": getattr(h.entry, "purpose", ""),
            "minimum_tier": getattr(h.entry, "minimum_tier", "user"),
            "host_subsystem": h.host_subsystem,
        }
        for h in catalogue.hubs
    ]
    subsystems = [
        {
            "key": s.key,
            "display_name": s.display_name,
            "description": s.description,
            "emoji": s.emoji,
            "visibility_tier": s.visibility_tier,
            "parent_hub": s.parent_hub,
            "top_level": s.top_level,
        }
        for s in catalogue.subsystems
    ]
    return _json_response({"ok": True, "hubs": hubs, "subsystems": subsystems})


async def _routing_get_handler(request: web.Request) -> web.Response:
    """``GET /control/routing?guild_id=&user_id=`` → current cog-routing rows.

    Administrator-gated. Returns every routing row for the guild (scope-ordered)
    so the editor shows which cogs are currently disabled and where.
    """
    try:
        guild, member = await _authed_read_context(request)
    except _ControlError as err:
        return _json_response({"error": err.message}, status=err.status)
    if not _is_admin(member):
        return _json_response(
            {"error": "reading cog routing requires administrator"},
            status=403,
        )

    from services.command_routing import list_for_guild

    try:
        raw = await list_for_guild(guild.id)
    except Exception as exc:  # noqa: BLE001
        return _seam_error_or_500(exc, "routing_read")

    rows = [
        {
            "scope_type": r.get("scope_type"),
            "scope_id": r.get("scope_id"),
            "cog_name": r.get("cog_name"),
            "enabled": r.get("enabled"),
            "actor_id": r.get("actor_id"),
            "updated_at": (
                r["updated_at"].isoformat() if r.get("updated_at") is not None else None
            ),
        }
        for r in raw
    ]
    return _json_response({"ok": True, "guild_id": guild.id, "rows": rows})


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register_control_routes(app: web.Application, bot: Any) -> bool:
    """Register ``/control/*`` on ``app`` — **only when configured**.

    Returns ``True`` when the routes were added (``CONTROL_API_TOKEN`` set),
    ``False`` when the API stays dormant. ``bot`` is already attached as
    ``app["bot"]`` by the health server; the parameter keeps the call explicit.
    """
    if control_token() is None:
        logger.info("control_api: dormant (CONTROL_API_TOKEN unset) — no routes added")
        return False
    app.router.add_get("/control/ping", _ping_handler)
    app.router.add_get("/control/authority", _authority_handler)
    # Phase E read endpoints (current state — so the editors stop writing blind).
    app.router.add_get("/control/settings/current", _settings_current_handler)
    app.router.add_get("/control/help/overlay", _help_overlay_get_handler)
    app.router.add_get("/control/help/catalogue", _help_catalogue_handler)
    app.router.add_get("/control/routing", _routing_get_handler)
    app.router.add_post("/control/settings", _settings_set_handler)
    app.router.add_post("/control/help/overlay", _help_overlay_handler)
    app.router.add_post("/control/help/home", _help_home_handler)
    app.router.add_post("/control/help/reset", _help_reset_handler)
    app.router.add_post("/control/routing", _routing_set_handler)
    logger.info(
        "control_api: enabled — ping, authority + reads "
        "(settings/current, help/overlay, help/catalogue, routing) + writes "
        "(settings, help/overlay, help/home, help/reset, routing; "
        "auth + per-request authority)",
    )
    return True


__all__ = [
    "control_token",
    "is_authorized",
    "register_control_routes",
    "resolve_authority",
]
