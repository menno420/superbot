"""FastAPI app for the SuperBot developer dashboard (read-only MVP).

Decoupled from the bot: it reads only the generated
``dashboard/data/dashboard.json`` (produced by
``scripts/export_dashboard_data.py``) and never imports ``disbot``.

Local run::

    pip install -r dashboard/requirements.txt
    uvicorn dashboard.app:app --reload

Deploy: a second Railway service — see ``dashboard/README.md``.
"""

from __future__ import annotations

import json
import secrets
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "dashboard.json"

# The dashboard runs both as a package (`dashboard.app`, local) and as a top-level
# module (`app:app`, Railway Root Directory = dashboard) — and the test loads
# app.py by file path. Putting this directory on sys.path lets the sibling helper
# modules import identically in all three contexts.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import auth  # noqa: E402  - after the sys.path shim above
import control_client  # noqa: E402  - after the sys.path shim above
import websession  # noqa: E402  - after the sys.path shim above

_EMPTY: dict[str, Any] = {
    "meta": {"generated_at": "", "counts": {}},
    "catalogue": [],
    "ideas": [],
    "bugs": [],
    "updates": [],
    "env_usage": [],
    "settings": [],
    "access": {"tiers": [], "total_visible": 0, "internal_count": 0},
    "synonyms": [],
}

app = FastAPI(title="SuperBot Dashboard", docs_url=None, redoc_url=None)


def session_context(request: Request) -> dict[str, Any]:
    """Login state merged into every template (the nav login button / avatar)."""
    return {
        "current_user": websession.read(request).get("user"),
        "login_enabled": auth.is_configured(),
    }


templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates"),
    context_processors=[session_context],
)


async def _form(request: Request) -> dict[str, str]:
    """Parse an ``application/x-www-form-urlencoded`` body (stdlib, no multipart)."""
    raw = (await request.body()).decode("utf-8", "replace")
    parsed = parse_qs(raw, keep_blank_values=True)
    return {key: values[0] for key, values in parsed.items()}


def load_data() -> dict[str, Any]:
    """Load the generated dashboard payload, falling back to an empty shape."""
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(_EMPTY)


def _command_names(data: dict[str, Any]) -> list[str]:
    """Sorted, de-duplicated set of every command name across all cogs."""
    return sorted({c["name"] for cog in data.get("cogs", []) for c in cog["commands"]})


def _build_taken_map(data: dict[str, Any]) -> dict[str, str]:
    """Map every token already in use -> a human label of what owns it.

    Synonyms first, then aliases, then command names last so the strongest owner
    (a real command) wins a tie. Shared by ``/aliases`` and the per-command alias
    box on ``/commands`` so both apply identical collision logic.
    """
    taken: dict[str, str] = {}
    for syn in data.get("synonyms", []):
        for token in syn["synonyms"]:
            taken[token.lower()] = f"synonym of !{syn['canonical']}"
    for cog in data.get("cogs", []):
        for cmd in cog["commands"]:
            for token in cmd.get("aliases") or []:
                taken[token.lower()] = f"alias of !{cmd['name']}"
    for name in _command_names(data):
        taken[name.lower()] = "a command"
    return taken


def _routable_subsystems(data: dict[str, Any]) -> list[str]:
    """Operator-routable subsystem keys — registered and not internal.

    Mirrors ``views/setup/sections/cog_routing.py``: ``command_routing`` keys on
    the subsystem key and only non-internal subsystems appear in the operator
    routing picker, so this is the set a cog's per-server enable/disable state
    applies to.
    """
    return sorted(
        entry["key"]
        for entry in data.get("catalogue", [])
        if entry.get("visibility_mode", "normal") != "internal"
    )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe (used by Railway)."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    """Public showcase landing page."""
    return templates.TemplateResponse(
        request,
        "index.html",
        {"data": load_data(), "page": "home"},
    )


@app.get("/functions", response_class=HTMLResponse)
def functions(request: Request):
    """Bot-function catalogue, grouped by category."""
    data = load_data()
    grouped: dict[str, list[dict]] = {}
    for entry in data["catalogue"]:
        grouped.setdefault(entry.get("category") or "other", []).append(entry)
    return templates.TemplateResponse(
        request,
        "functions.html",
        {"data": data, "page": "functions", "groups": sorted(grouped.items())},
    )


@app.get("/ideas", response_class=HTMLResponse)
def ideas(request: Request):
    """Read-only idea backlog."""
    return templates.TemplateResponse(
        request,
        "ideas.html",
        {"data": load_data(), "page": "ideas"},
    )


@app.get("/bugs", response_class=HTMLResponse)
def bugs(request: Request):
    """Read-only bug board (public report form arrives in Phase 2)."""
    return templates.TemplateResponse(
        request,
        "bugs.html",
        {"data": load_data(), "page": "bugs"},
    )


@app.get("/updates", response_class=HTMLResponse)
def updates(request: Request):
    """Updates feed built from session logs."""
    return templates.TemplateResponse(
        request,
        "updates.html",
        {"data": load_data(), "page": "updates"},
    )


@app.get("/env", response_class=HTMLResponse)
def env(request: Request):
    """Read-only env-var usage map (names + locations only — never values)."""
    return templates.TemplateResponse(
        request,
        "env.html",
        {"data": load_data(), "page": "env"},
    )


@app.get("/settings", response_class=HTMLResponse)
def settings(request: Request):
    """Settings catalogue — every per-guild setting key, grouped by subsystem."""
    return templates.TemplateResponse(
        request,
        "settings.html",
        {"data": load_data(), "page": "settings"},
    )


@app.get("/access", response_class=HTMLResponse)
def access(request: Request):
    """Permissions & access map — visibility tier ladder (mirrors visibility_rules)."""
    return templates.TemplateResponse(
        request,
        "access.html",
        {"data": load_data(), "page": "access"},
    )


@app.get("/games", response_class=HTMLResponse)
def games(request: Request):
    """Player-facing showcase — games, economy, and progression subsystems."""
    data = load_data()
    wanted = ("games", "economy", "progression")
    by_cat: dict[str, list[dict]] = {}
    for entry in data.get("catalogue", []):
        if entry.get("category") in wanted:
            by_cat.setdefault(entry["category"], []).append(entry)
    groups = [(cat, by_cat[cat]) for cat in wanted if cat in by_cat]
    tunables = [
        domain
        for domain in data.get("settings", [])
        if domain["domain"] in ("games", "economy", "xp")
    ]
    return templates.TemplateResponse(
        request,
        "games.html",
        {"data": data, "page": "games", "groups": groups, "tunables": tunables},
    )


@app.get("/aliases", response_class=HTMLResponse)
def aliases(request: Request):
    """Suggest a command alias — pick a command, propose an alias, get a live
    collision check (against every command name, alias, and synonym) plus a
    prefilled GitHub issue and a ready-to-paste ``synonyms.py`` snippet.
    """
    data = load_data()
    return templates.TemplateResponse(
        request,
        "aliases.html",
        {
            "data": data,
            "page": "aliases",
            "commands": _command_names(data),
            "taken": _build_taken_map(data),
        },
    )


@app.get("/status", response_class=HTMLResponse)
def status(request: Request):
    """Live status & health — deployed build, inventory counts, bug & access health."""
    data = load_data()
    bugs = data.get("bugs", [])
    open_bugs = [b for b in bugs if (b.get("status") or "").upper() == "OPEN"]
    health = {
        "bugs_total": len(bugs),
        "bugs_open": len(open_bugs),
        "open_bugs": open_bugs,
    }
    # Count map for the inventory grid -> (label, detail page) per known count key.
    count_links = {
        "functions": ("Subsystems", "/functions"),
        "cogs": ("Cogs", "/commands"),
        "commands": ("Commands", "/commands"),
        "setting_keys": ("Settings", "/settings"),
        "setting_domains": ("Setting domains", "/settings"),
        "synonyms": ("Synonyms", "/aliases"),
        "env_vars": ("Env vars", "/env"),
        "ideas": ("Ideas", "/ideas"),
        "bugs": ("Bugs", "/bugs"),
        "updates": ("Updates", "/updates"),
        "visible_subsystems": ("Visible subsystems", "/access"),
    }
    counts = data.get("meta", {}).get("counts", {})
    cards = [
        {"key": k, "label": label, "href": href, "value": counts.get(k, 0)}
        for k, (label, href) in count_links.items()
    ]
    tiers = [t for t in data.get("access", {}).get("tiers", []) if t.get("subsystems")]
    return templates.TemplateResponse(
        request,
        "status.html",
        {
            "data": data,
            "page": "status",
            "build": data.get("meta", {}).get("build", {}),
            "health": health,
            "cards": cards,
            "tiers": tiers,
        },
    )


@app.get("/commands", response_class=HTMLResponse)
def commands(request: Request):
    """Cog & command management surface — explorer + a per-item Manage panel.

    The read side of the Q-0158 ask: every command and cog gets a Manage button
    opening a panel with its current aliases, its cog's (cog-level) routing
    state, and a per-command alias suggest box. Front-ends the bot's seams
    (``command_routing`` + the synonym layer); the live write side lands with the
    control API (Phase 2). Owner direction Q-0160: routing is cog-level.
    """
    data = load_data()
    cmds = [c for cog in data.get("cogs", []) for c in cog["commands"]]
    stats = {
        "total": len(cmds),
        "top_prefix": sum(
            1 for c in cmds if c["type"] in ("prefix", "both") and not c["parent"]
        ),
        "subcommands": sum(1 for c in cmds if c["parent"]),
        "slash": sum(1 for c in cmds if c["type"] == "slash" and not c["parent"]),
        "button": sum(1 for c in cmds if c["button_backed"]),
        "cogs": sum(1 for cog in data.get("cogs", []) if cog.get("is_cog")),
    }
    sysmap = {c["key"]: c for c in data.get("catalogue", [])}
    return templates.TemplateResponse(
        request,
        "commands.html",
        {
            "data": data,
            "page": "commands",
            "stats": stats,
            "sysmap": sysmap,
            "routable": _routable_subsystems(data),
            "taken": _build_taken_map(data),
            "synonyms_by_canonical": {
                s["canonical"]: s["synonyms"] for s in data.get("synonyms", [])
            },
        },
    )


# ===========================================================================
# Control panel — Discord OAuth login + the per-guild editors
#
# Dormant until the owner configures the Discord OAuth app + the bot control
# API token on Railway. With nothing configured, /admin renders a "set this up"
# page and the nav shows no login button — the read-only site is unchanged.
# Every edit POSTs to the bot's control API, which resolves the live member and
# writes through the EXISTING audited seam — the website never writes the DB.
# ===========================================================================


def _find_admin_guild(
    session: dict[str, Any],
    guild_id: str,
) -> dict[str, Any] | None:
    """The session's admin-guild entry matching ``guild_id``, or ``None``."""
    for guild in session.get("guilds", []):
        if str(guild.get("id")) == str(guild_id):
            return guild
    return None


async def _control_flash(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Call the control API; return a one-shot flash dict describing the outcome."""
    status, body = await control_client.post(path, payload)
    ok = status == 200 and bool(body.get("ok"))
    return {
        "ok": ok,
        "status": status,
        "message": (
            "Saved — the bot applied it live."
            if ok
            else str(body.get("error") or f"Failed (HTTP {status}).")
        ),
    }


def _blank_current() -> dict[str, Any]:
    """The empty current-state shape (no reads yet / reads unavailable)."""
    return {
        "settings": {},
        "help_overlay": None,
        "help_catalogue": None,
        "routing_map": {},
        "reads_ok": False,
    }


def _setup_health(current: dict[str, Any]) -> dict[str, Any]:
    """Summarize the live current-state read into a one-glance server-health card.

    A pure projection of :func:`_fetch_current_state`'s result (no I/O) that drives
    the read-only server overview: how many settings are invalid (→ falling back to
    default), how many are customised away from the default, how many Help entities
    are overridden (and whether the Home message is customised), and which cogs are
    disabled for the guild.
    """
    invalid: list[dict[str, str]] = []
    customised = 0
    total_settings = 0
    for subsystem, items in (current.get("settings") or {}).items():
        for item in items:
            total_settings += 1
            if not item.get("valid", True):
                invalid.append({"subsystem": subsystem, "name": item.get("name", "")})
            elif item.get("provenance") and item["provenance"] != "default":
                customised += 1

    overlay = current.get("help_overlay") or {}
    help_overrides = len(overlay.get("rows") or [])
    home_customised = bool(overlay.get("home"))

    routing = current.get("routing_map") or {}
    disabled_cogs = sorted(name for name, enabled in routing.items() if not enabled)

    return {
        "total_settings": total_settings,
        "customised": customised,
        "invalid": invalid,
        "invalid_count": len(invalid),
        "help_overrides": help_overrides,
        "home_customised": home_customised,
        "disabled_cogs": disabled_cogs,
        "disabled_count": len(disabled_cogs),
        "healthy": not invalid,
    }


def _authority_preview(authority: dict[str, Any] | None) -> dict[str, Any]:
    """An honest "what you may read / change here" matrix from the authority bridge.

    A pure projection — it sets expectations, it never grants anything: the bot
    remains the only real authority and re-checks every write live. The current
    read + write control-API surfaces are all administrator-gated, so an admin (or
    the guild owner, who holds admin) may read current config and edit settings /
    help / cog routing; a plain member may do none of it here. Env-value
    management lives in the separate owner (platform) zone, not per-guild.
    """
    found = bool(authority and authority.get("member_found"))
    is_admin = bool(authority and authority.get("is_admin"))
    is_owner = bool(authority and authority.get("is_owner"))
    return {
        "member_found": found,
        "tier": (authority or {}).get("tier"),
        "is_admin": is_admin,
        "is_owner": is_owner,
        "may_read_config": is_admin,
        "may_edit_settings": is_admin,
        "may_edit_help": is_admin,
        "may_edit_routing": is_admin,
    }


async def _fetch_current_state(guild_id: int, user_id: int) -> dict[str, Any]:
    """Fetch the guild's live current config from the bot (Phase E reads).

    Turns the editors from "write blind" into "see-then-change". Each read
    degrades independently: a failure leaves an empty/None slot so that section
    falls back to its blind form rather than erroring the whole page.
    ``reads_ok`` is True only when the (gating) settings read succeeded.
    """
    state: dict[str, Any] = {
        "settings": {},
        "help_overlay": None,
        "help_catalogue": None,
        "routing_map": {},
        "reads_ok": False,
    }
    ids = {"guild_id": guild_id, "user_id": user_id}

    s_status, s_body = await control_client.get("/control/settings/current", ids)
    if s_status == 200 and s_body.get("ok"):
        state["settings"] = s_body.get("subsystems", {})
        state["reads_ok"] = True

    h_status, h_body = await control_client.get("/control/help/overlay", ids)
    if h_status == 200 and h_body.get("ok"):
        state["help_overlay"] = h_body

    c_status, c_body = await control_client.get("/control/help/catalogue")
    if c_status == 200 and c_body.get("ok"):
        state["help_catalogue"] = c_body

    r_status, r_body = await control_client.get("/control/routing", ids)
    if r_status == 200 and r_body.get("ok"):
        # Guild-scope rows drive the per-cog current state (default = enabled).
        state["routing_map"] = {
            row["cog_name"]: row["enabled"]
            for row in r_body.get("rows", [])
            if row.get("scope_type") == "guild" and row.get("cog_name")
        }
    return state


@app.get("/auth/login")
def auth_login(request: Request):
    """Begin Discord OAuth — redirect to consent, or fall back to /admin if off."""
    if not auth.is_configured():
        return RedirectResponse("/admin", status_code=302)
    session = websession.read(request)
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    resp = RedirectResponse(auth.authorize_url(state), status_code=302)
    websession.write(resp, session)
    return resp


@app.get("/auth/callback")
async def auth_callback(request: Request):
    """OAuth redirect target — verify state, exchange the code, store identity."""
    session = websession.read(request)
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    expected = session.pop("oauth_state", None)
    if not code or not state or state != expected:
        return RedirectResponse("/admin", status_code=302)
    try:
        token = await auth.exchange_code(code)
        identity = await auth.fetch_identity(token)
    except Exception:  # noqa: BLE001 - any OAuth failure → back to /admin with a flash
        session["flash"] = {
            "ok": False,
            "status": 502,
            "message": "Discord sign-in failed — please try again.",
        }
        resp = RedirectResponse("/admin", status_code=302)
        websession.write(resp, session)
        return resp
    user = identity.get("user", {})
    session["user"] = {
        "id": user.get("id"),
        "username": user.get("username"),
        "global_name": user.get("global_name"),
        "avatar": user.get("avatar"),
    }
    session["guilds"] = auth.admin_guilds(identity.get("guilds", []))
    resp = RedirectResponse("/admin", status_code=302)
    websession.write(resp, session)
    return resp


@app.get("/auth/logout")
def auth_logout(request: Request):
    """Clear the session and return home."""
    resp = RedirectResponse("/", status_code=302)
    websession.clear(resp)
    return resp


@app.get("/me", response_class=HTMLResponse)
def me_overview(request: Request):
    """Personal overview — the logged-in hinge between the public site and
    per-server management. Greets the user and lists the servers they administer,
    each linking to its read-only overview. Redirects to ``/admin`` (the sign-in
    surface) when logged out. Pure session data — no per-guild bot calls, so it
    stays fast for a user who administers many servers.
    """
    session = websession.read(request)
    user = session.get("user")
    if user is None:
        return RedirectResponse("/admin", status_code=302)
    return templates.TemplateResponse(
        request,
        "me.html",
        {
            "data": load_data(),
            "page": "me",
            "guilds": session.get("guilds", []),
            "control_configured": control_client.is_configured(),
        },
    )


@app.get("/admin", response_class=HTMLResponse)
def admin_home(request: Request):
    """The control-panel home — sign-in prompt or the user's admin-guild picker."""
    session = websession.read(request)
    user = session.get("user")
    guilds = session.get("guilds", []) if user else []
    flash = session.pop("flash", None)
    resp = templates.TemplateResponse(
        request,
        "admin.html",
        {
            "data": load_data(),
            "page": "admin",
            "guilds": guilds,
            "control_configured": control_client.is_configured(),
            "flash": flash,
        },
    )
    if flash is not None:
        websession.write(resp, session)  # persist the flash pop
    return resp


@app.get("/admin/{guild_id}/overview", response_class=HTMLResponse)
async def admin_guild_overview(request: Request, guild_id: str):
    """Read-only per-server overview — authority + a setup-health summary.

    The non-editing companion to ``/admin/{guild}``: a one-glance picture (invalid
    settings, customisations, help overrides, disabled cogs) plus an honest
    authority preview, all from the Phase E read endpoints. Never writes.
    """
    session = websession.read(request)
    user = session.get("user")
    if user is None:
        return RedirectResponse("/admin", status_code=302)
    guild = _find_admin_guild(session, guild_id)
    if guild is None:
        return RedirectResponse("/admin", status_code=302)
    authority = None
    current = _blank_current()
    if control_client.is_configured():
        authority = await control_client.get_authority(int(guild_id), int(user["id"]))
        if authority and authority.get("is_admin"):
            current = await _fetch_current_state(int(guild_id), int(user["id"]))
    return templates.TemplateResponse(
        request,
        "admin_overview.html",
        {
            "data": load_data(),
            "page": "admin",
            "guild": guild,
            "authority": authority,
            "preview": _authority_preview(authority),
            "health": _setup_health(current),
            "current": current,
            "control_configured": control_client.is_configured(),
        },
    )


@app.get("/admin/{guild_id}", response_class=HTMLResponse)
async def admin_guild(request: Request, guild_id: str):
    """The per-guild editor — settings, help appearance, and cog routing."""
    session = websession.read(request)
    user = session.get("user")
    if user is None:
        return RedirectResponse("/admin", status_code=302)
    guild = _find_admin_guild(session, guild_id)
    if guild is None:
        return RedirectResponse("/admin", status_code=302)
    authority = None
    current: dict[str, Any] = _blank_current()
    if control_client.is_configured():
        authority = await control_client.get_authority(int(guild_id), int(user["id"]))
        # Live current state (see-then-change) — only when the bot says you're an
        # admin here; otherwise the reads would 403 and the editors stay blind.
        if authority and authority.get("is_admin"):
            current = await _fetch_current_state(int(guild_id), int(user["id"]))
    data = load_data()
    flash = session.pop("flash", None)
    resp = templates.TemplateResponse(
        request,
        "admin_guild.html",
        {
            "data": data,
            "page": "admin",
            "guild": guild,
            "authority": authority,
            "control_configured": control_client.is_configured(),
            "settings": data.get("settings", []),
            "cogs": [c for c in data.get("cogs", []) if c.get("is_cog")],
            "catalogue": data.get("catalogue", []),
            "current": current,
            "flash": flash,
        },
    )
    if flash is not None:
        websession.write(resp, session)
    return resp


async def _edit(
    request: Request,
    guild_id: str,
    path: str,
    payload: dict[str, Any],
) -> RedirectResponse:
    """Shared editor POST: gate on session admin → control API → flash → redirect."""
    session = websession.read(request)
    if session.get("user") is None or _find_admin_guild(session, guild_id) is None:
        return RedirectResponse("/admin", status_code=303)
    session["flash"] = await _control_flash(path, payload)
    resp = RedirectResponse(f"/admin/{guild_id}", status_code=303)
    websession.write(resp, session)
    return resp


def _actor_id(request: Request) -> int | None:
    user = websession.read(request).get("user")
    try:
        return int(user["id"]) if user else None
    except (KeyError, TypeError, ValueError):
        return None


@app.post("/admin/{guild_id}/settings")
async def post_setting(request: Request, guild_id: str):
    """Edit one setting → POST /control/settings (the bot capability-gates it)."""
    form = await _form(request)
    payload = {
        "guild_id": int(guild_id),
        "user_id": _actor_id(request),
        "subsystem": form.get("subsystem", "").strip(),
        "name": form.get("name", "").strip(),
        "value": form.get("value", "").strip(),
    }
    return await _edit(request, guild_id, "/control/settings", payload)


@app.post("/admin/{guild_id}/help/overlay")
async def post_help_overlay(request: Request, guild_id: str):
    """Hide / rename / re-describe a Help entity → POST /control/help/overlay."""
    form = await _form(request)
    payload: dict[str, Any] = {
        "guild_id": int(guild_id),
        "user_id": _actor_id(request),
        "entity_kind": form.get("entity_kind", "").strip(),
        "entity_key": form.get("entity_key", "").strip(),
        "display_hidden": form.get("display_hidden") == "on",
    }
    # Only forward text overrides the user actually filled in (blank = untouched).
    if form.get("display_name", "").strip():
        payload["display_name"] = form["display_name"].strip()
    if form.get("description", "").strip():
        payload["description"] = form["description"].strip()
    return await _edit(request, guild_id, "/control/help/overlay", payload)


@app.post("/admin/{guild_id}/help/home")
async def post_help_home(request: Request, guild_id: str):
    """Edit the Help Home message → POST /control/help/home."""
    form = await _form(request)
    payload: dict[str, Any] = {
        "guild_id": int(guild_id),
        "user_id": _actor_id(request),
    }
    if form.get("title", "").strip():
        payload["title"] = form["title"].strip()
    if form.get("body", "").strip():
        payload["body"] = form["body"].strip()
    return await _edit(request, guild_id, "/control/help/home", payload)


@app.post("/admin/{guild_id}/routing")
async def post_routing(request: Request, guild_id: str):
    """Enable / disable a cog for the guild → POST /control/routing."""
    form = await _form(request)
    payload = {
        "guild_id": int(guild_id),
        "user_id": _actor_id(request),
        "cog_name": form.get("cog_name", "").strip(),
        "enabled": form.get("enabled") == "enabled",
        "scope_type": "guild",
    }
    return await _edit(request, guild_id, "/control/routing", payload)
