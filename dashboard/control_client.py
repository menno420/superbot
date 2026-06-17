"""Client for the bot's private control API (``disbot/control_api.py``).

The dashboard is a separate process that never imports the bot; to drive the
bot's audited seams it calls the bot's control API over Railway's **private**
network (``http://worker.railway.internal:8080`` by default), authenticating with
the shared ``CONTROL_API_TOKEN``. Every call carries the acting user's Discord id
+ the target guild id; the **bot** resolves the live member and the audited seam
makes the real authority decision — this client never decides permissions.

**Dormant by default.** When ``CONTROL_API_URL`` / ``CONTROL_API_TOKEN`` are not
set, :func:`is_configured` is ``False`` and the editor surface shows a
"not connected" state instead of calling anything. Nothing here is exercised
until the owner sets both on the dashboard Railway service.
"""

from __future__ import annotations

import os
from typing import Any

# The bot's control API is reachable on the Railway private network. The default
# matches the health server's port; override with CONTROL_API_URL if needed.
_DEFAULT_BASE = "http://worker.railway.internal:8080"


def control_config() -> tuple[str, str] | None:
    """Return ``(base_url, token)`` or ``None`` when the client is dormant."""
    token = os.environ.get("CONTROL_API_TOKEN", "").strip()
    if not token:
        return None
    base = os.environ.get("CONTROL_API_URL", "").strip() or _DEFAULT_BASE
    return base.rstrip("/"), token


def is_configured() -> bool:
    """``True`` when the bot control API is reachable (token configured)."""
    return control_config() is not None


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


async def get_authority(guild_id: int, user_id: int) -> dict[str, Any] | None:
    """Ask the bot what ``user_id`` may do in ``guild_id`` (the authority bridge).

    Returns the bridge payload (``tier`` / ``is_admin`` / ``member_found`` …), or
    ``None`` when the client is dormant or the bot is unreachable.
    """
    config = control_config()
    if config is None:
        return None
    import httpx

    base, token = config
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                f"{base}/control/authority",
                params={"guild_id": guild_id, "user_id": user_id},
                headers=_headers(token),
            )
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception:  # noqa: BLE001 - bot unreachable / network error → no authority
        return None


async def get(
    path: str,
    params: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    """GET a control-API ``path`` (e.g. ``/control/settings/current``).

    Returns ``(status_code, body)``. A dormant client returns ``(503, …)``; a
    network failure returns ``(502, …)`` so the caller can degrade to a blind
    editor rather than erroring. The Phase E read sibling of :func:`post`.
    """
    config = control_config()
    if config is None:
        return 503, {"error": "control API not configured"}
    import httpx

    base, token = config
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{base}{path}",
                params=params or {},
                headers=_headers(token),
            )
        try:
            body = resp.json()
        except Exception:  # noqa: BLE001 - non-JSON body
            body = {"error": resp.text[:200]}
        return resp.status_code, body
    except Exception as exc:  # noqa: BLE001 - bot unreachable
        return 502, {"error": f"could not reach the bot control API: {exc}"}


async def post(path: str, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
    """POST ``payload`` to a control-API ``path`` (e.g. ``/control/settings``).

    Returns ``(status_code, body)``. A dormant client returns ``(503, …)``; a
    network failure returns ``(502, …)`` so the editor can show a clear message.
    """
    config = control_config()
    if config is None:
        return 503, {"error": "control API not configured"}
    import httpx

    base, token = config
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{base}{path}",
                json=payload,
                headers=_headers(token),
            )
        try:
            body = resp.json()
        except Exception:  # noqa: BLE001 - non-JSON body
            body = {"error": resp.text[:200]}
        return resp.status_code, body
    except Exception as exc:  # noqa: BLE001 - bot unreachable
        return 502, {"error": f"could not reach the bot control API: {exc}"}
