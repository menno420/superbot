"""Discord OAuth2 for the dashboard control panel — login + identity.

The dashboard is a **free, multi-user control panel**: anyone signs in with their
Discord account, and the site then knows *who they are* and *which guilds they
administer*. That identity is handed to the bot's control API, which makes the
**real** authority decision (the bot resolves the live member and the audited
seam enforces permissions — see ``disbot/control_api.py``). The browser's claim
is never trusted on its own.

**Dormant by default.** Every helper reads its config from the environment and
returns ``None`` / a "not configured" signal when the OAuth app is not set up, so
the dashboard runs exactly as the read-only site until the owner provisions
``DISCORD_OAUTH_CLIENT_ID`` / ``DISCORD_OAUTH_CLIENT_SECRET`` /
``DISCORD_OAUTH_REDIRECT_URI`` on Railway. No secret is ever committed.

Scopes are the minimum needed: ``identify`` (who you are) + ``guilds`` (which
servers you're in, with your permission bits) — never ``email`` or message access.
"""

from __future__ import annotations

import os
from typing import Any
from urllib.parse import urlencode

AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
TOKEN_URL = "https://discord.com/api/oauth2/token"
API_BASE = "https://discord.com/api/v10"
SCOPES = "identify guilds"

# Discord permission bit for ADMINISTRATOR (0x8). A guild where the user is owner
# or holds this bit is one they can administer — the only guilds the editor offers
# (the bot re-verifies per write, so this is a UX filter, not the security gate).
_PERM_ADMINISTRATOR = 0x8


def oauth_config() -> tuple[str, str, str] | None:
    """Return ``(client_id, client_secret, redirect_uri)`` or ``None`` if unset."""
    client_id = os.environ.get("DISCORD_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.environ.get("DISCORD_OAUTH_CLIENT_SECRET", "").strip()
    redirect_uri = os.environ.get("DISCORD_OAUTH_REDIRECT_URI", "").strip()
    if not (client_id and client_secret and redirect_uri):
        return None
    return client_id, client_secret, redirect_uri


def is_configured() -> bool:
    """``True`` when the Discord OAuth app is fully configured (login enabled)."""
    return oauth_config() is not None


def authorize_url(state: str) -> str | None:
    """The Discord consent URL to redirect a logging-in user to, or ``None``."""
    config = oauth_config()
    if config is None:
        return None
    client_id, _secret, redirect_uri = config
    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": SCOPES,
            "state": state,
            "prompt": "none",
        },
    )
    return f"{AUTHORIZE_URL}?{query}"


async def exchange_code(code: str) -> str:
    """Exchange an OAuth ``code`` for an access token. Returns the access token.

    Raises ``RuntimeError`` if OAuth is not configured and propagates HTTP errors
    from httpx so the caller can render a failure page.
    """
    config = oauth_config()
    if config is None:
        raise RuntimeError("Discord OAuth is not configured")
    import httpx

    client_id, client_secret, redirect_uri = config
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        token: str = resp.json()["access_token"]
    return token


async def fetch_identity(access_token: str) -> dict[str, Any]:
    """Fetch the user + their guild list with the access token.

    Returns ``{"user": {...}, "guilds": [...]}`` where ``guilds`` carries each
    guild's ``permissions`` bits (so :func:`admin_guilds` can filter).
    """
    import httpx

    headers = {"Authorization": f"Bearer {access_token}"}
    async with httpx.AsyncClient(timeout=10.0) as client:
        user_resp = await client.get(f"{API_BASE}/users/@me", headers=headers)
        user_resp.raise_for_status()
        guilds_resp = await client.get(f"{API_BASE}/users/@me/guilds", headers=headers)
        guilds_resp.raise_for_status()
    return {"user": user_resp.json(), "guilds": guilds_resp.json()}


def admin_guilds(guilds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter ``guilds`` to those the user owns or holds ADMINISTRATOR in.

    UX filter only — the editor offers these, but the bot re-checks authority on
    every write against the live member, so a stale/forged list cannot escalate.
    """
    out: list[dict[str, Any]] = []
    for guild in guilds:
        if not isinstance(guild, dict):
            continue
        try:
            perms = int(guild.get("permissions", 0))
        except (TypeError, ValueError):
            perms = 0
        if guild.get("owner") or (perms & _PERM_ADMINISTRATOR):
            out.append(guild)
    return out
