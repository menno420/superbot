"""Private control API — the bot side of the developer-dashboard control panel.

The decoupled dashboard (``dashboard/``) cannot import the bot, so to let it
*read and (later) drive* the bot's existing audited seams it talks to the bot
over HTTP. This module adds a small ``/control/*`` surface to the **existing**
health server (``healthserver.py``) — same aiohttp app, same private port — so
no second server is introduced.

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
  the live member and reports what that member may do, using the **same**
  visibility/permission rules every in-Discord surface uses. The browser's claim
  is never trusted on its own.

This first slice is **read-only**: ``/control/ping`` (auth smoke) and
``/control/authority`` (the identity→authority bridge — "what can this user do in
this guild"). Mutation endpoints (front-ending ``settings_mutation`` /
``help_overlay_mutation`` / ``command_routing`` / participation) land in a later
PR, each over its existing audited seam.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
from typing import Any

from aiohttp import web

logger = logging.getLogger("bot.control_api")


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
# Handlers
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
    logger.info(
        "control_api: enabled — /control/ping, /control/authority (auth required)",
    )
    return True


__all__ = [
    "control_token",
    "is_authorized",
    "register_control_routes",
    "resolve_authority",
]
