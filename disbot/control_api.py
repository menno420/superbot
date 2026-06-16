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
    app.router.add_post("/control/settings", _settings_set_handler)
    app.router.add_post("/control/help/overlay", _help_overlay_handler)
    app.router.add_post("/control/help/home", _help_home_handler)
    app.router.add_post("/control/help/reset", _help_reset_handler)
    app.router.add_post("/control/routing", _routing_set_handler)
    logger.info(
        "control_api: enabled — ping, authority (read) + settings, help/overlay, "
        "help/home, help/reset, routing (write; auth + per-request authority)",
    )
    return True


__all__ = [
    "control_token",
    "is_authorized",
    "register_control_routes",
    "resolve_authority",
]
