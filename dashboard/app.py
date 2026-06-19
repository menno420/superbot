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

import hmac
import json
import os
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
import github_mirror  # noqa: E402  - after the sys.path shim above
import ratelimit  # noqa: E402  - after the sys.path shim above
import submissions_db  # noqa: E402  - after the sys.path shim above
import websession  # noqa: E402  - after the sys.path shim above

# Abuse-brakes for the public live surface (R3 hardening). Coarse + per-process;
# the bot still authority-checks every write, so these only blunt bursts.
_LOGIN_LIMITER = ratelimit.SlidingWindowLimiter(max_events=10, window_seconds=300.0)
_EDIT_LIMITER = ratelimit.SlidingWindowLimiter(max_events=40, window_seconds=60.0)
# Moderation actions (approve/reject) reuse the same per-actor edit-budget shape, but on
# a separate limiter so a burst of moderation clicks can't exhaust the per-guild editor
# budget (and vice-versa).
_MODERATION_LIMITER = ratelimit.SlidingWindowLimiter(max_events=40, window_seconds=60.0)

# Bot-owner gate for the dev-site owner-only ring (submission moderation, plan §2.4).
# The dev site MUST NOT import ``disbot`` (decoupling — plan §0 / architecture.md), so
# the owner id is read from the environment here — the SAME ``BOT_OWNER_USER_ID`` env
# var + hardcoded default the bot uses (``disbot/config.py``), kept in sync by env, not
# by import.
_BOT_OWNER_DEFAULT = "340415158583296000"


def _bot_owner_id() -> str | None:
    """The configured bot-owner Discord id (str), or ``None`` if explicitly disabled.

    Read at call time (not import) so a deployment can override it and tests can
    monkeypatch the env. A blank/garbage value disables the owner ring (fails closed —
    :func:`_is_bot_owner` then matches nobody).
    """
    raw = os.environ.get("BOT_OWNER_USER_ID", _BOT_OWNER_DEFAULT).strip()
    return raw or None


def _is_bot_owner(session: dict[str, Any]) -> bool:
    """``True`` only when the signed-in user's id equals the configured bot owner.

    Mirrors the bot's identity model: authority is the authoritative Discord *user id*
    from the verified OAuth session, never a claim in the request body — so it cannot be
    spoofed. Fails closed when logged out or when no owner is configured.
    """
    owner = _bot_owner_id()
    if owner is None:
        return False
    user = session.get("user") or {}
    return str(user.get("id")) == owner


def _client_ip(request: Request) -> str:
    """Best-effort client IP — first ``X-Forwarded-For`` hop (Railway proxy), else peer."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client.host if client else "unknown"


def _ensure_csrf(session: dict[str, Any]) -> str:
    """Return the session's CSRF token, minting one into the session if absent."""
    token = session.get("csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf"] = token
    return token


def _csrf_ok(session: dict[str, Any], submitted: str | None) -> bool:
    """Constant-time check that ``submitted`` matches the session's CSRF token."""
    expected = session.get("csrf")
    if not expected or not submitted:
        return False
    return hmac.compare_digest(str(submitted), str(expected))


_EMPTY: dict[str, Any] = {
    "meta": {"generated_at": "", "counts": {}},
    "catalogue": [],
    "ideas": [],
    "bugs": [],
    "reviews": [],
    "updates": [],
    "env_usage": [],
    "settings": [],
    "access": {"tiers": [], "total_visible": 0, "internal_count": 0},
    "synonyms": [],
}

app = FastAPI(title="SuperBot Dashboard", docs_url=None, redoc_url=None)


def session_context(request: Request) -> dict[str, Any]:
    """Login state merged into every template (the nav login button / avatar).

    ``is_bot_owner`` gates the owner-only Moderation nav link — the link is only shown
    to the signed-in bot owner (the route itself re-checks, so this is a UX filter).
    """
    session = websession.read(request)
    return {
        "current_user": session.get("user"),
        "login_enabled": auth.is_configured(),
        "is_bot_owner": _is_bot_owner(session),
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


@app.get("/reviews", response_class=HTMLResponse)
def reviews(request: Request):
    """Owner review inbox (read-only) — open vs. resolved reviews grouped by area.

    Phase 1 of the owner↔agent review channel (Q-0169): a read view over the
    committed ``docs/owner/review-inbox.md`` ledger. ``OPEN`` reviews are the
    actionable list (a bugs-first cousin); the rest are the resolved history. The
    write side (post-from-the-dashboard) is Phase 2 and stays Held.
    """
    data = load_data()
    items = data.get("reviews", [])
    open_reviews = [r for r in items if (r.get("status") or "").upper() == "OPEN"]
    resolved_reviews = [r for r in items if (r.get("status") or "").upper() != "OPEN"]
    by_area: dict[str, list[dict]] = {}
    for review in open_reviews:
        by_area.setdefault(review.get("area") or "general", []).append(review)
    return templates.TemplateResponse(
        request,
        "reviews.html",
        {
            "data": data,
            "page": "reviews",
            "open_by_area": sorted(by_area.items()),
            "open_reviews": open_reviews,
            "resolved_reviews": resolved_reviews,
        },
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
    if not _LOGIN_LIMITER.allow(_client_ip(request)):
        session = websession.read(request)
        session["flash"] = {
            "ok": False,
            "status": 429,
            "message": "Too many sign-in attempts — wait a minute and try again.",
        }
        resp = RedirectResponse("/admin", status_code=302)
        websession.write(resp, session)
        return resp
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


# ===========================================================================
# Submission moderation — the owner-only ring (plan §2.3 / §2.4 / §4.1)
#
# The public bot site's /submit form INSERTs `pending` rows into the separate,
# dashboard-owned submissions DB; they are NEVER shown publicly. This page is the
# ONLY place they surface: the owner reviews the pending queue and approves/rejects
# each. On approve the dev site mirrors the row to ONE GitHub issue (github_mirror),
# records the URL, and flips status='approved'; reject just flips status='rejected'.
#
# Owner-gated (restricted to BOT_OWNER_USER_ID — the stricter ring than the
# any-admin per-guild editors), CSRF-protected, and rate-limited — reusing the same
# dashboard machinery as the per-guild editors. Unmoderated user input is rendered
# ESCAPED by the template (plan §4.2); this layer never renders it.
#
# IMPORTANT (route order): `/admin/moderation` is registered BEFORE the dynamic
# `/admin/{guild_id}` route so the literal path wins — otherwise "moderation" would be
# captured as a guild id.
# ===========================================================================


def _moderation_context(request: Request) -> dict[str, Any]:
    """Shared template context for the moderation page (pending rows + flags).

    Degrades honestly: when the submissions store is dormant
    (``SUBMISSIONS_DB_DSN`` unset) it shows a "set this up" state with no query; the
    page never errors. ``mirror_configured`` drives whether **approve** is offered
    (approve needs the GitHub mirror token; reject works regardless).
    """
    return {
        "data": load_data(),
        "page": "moderation",
        "store_configured": submissions_db.is_configured(),
        "mirror_configured": github_mirror.is_configured(),
    }


def _moderation_redirect(
    session: dict[str, Any],
    flash: dict[str, Any],
) -> RedirectResponse:
    """PRG redirect back to the moderation page, carrying a one-shot flash."""
    session["flash"] = flash
    resp = RedirectResponse("/admin/moderation", status_code=303)
    websession.write(resp, session)
    return resp


@app.get("/admin/moderation", response_class=HTMLResponse)
async def admin_moderation(request: Request):
    """Owner-only submission moderation queue — list `pending`, approve / reject.

    Logged-out → bounce to ``/admin`` (the sign-in surface). Logged-in but not the
    bot owner → a 403-style "owner only" page (never the queue). Owner → the pending
    queue, or a dormant "set this up" state when the store has no DSN.
    """
    session = websession.read(request)
    if session.get("user") is None:
        return RedirectResponse("/admin", status_code=302)
    ctx = _moderation_context(request)
    if not _is_bot_owner(session):
        # An admin who is not the owner: honest "this ring is owner-only", not the data.
        return templates.TemplateResponse(
            request,
            "moderation.html",
            {**ctx, "authorized": False, "pending": [], "csrf_token": None},
        )
    pending: list[dict[str, Any]] = []
    load_error = False
    if ctx["store_configured"]:
        try:
            pending = await submissions_db.list_pending()
        except Exception:  # noqa: BLE001 - a DB hiccup shows an error banner, not a 500
            load_error = True
    csrf_token = _ensure_csrf(session)
    flash = session.pop("flash", None)
    resp = templates.TemplateResponse(
        request,
        "moderation.html",
        {
            **ctx,
            "authorized": True,
            "pending": pending,
            "load_error": load_error,
            "csrf_token": csrf_token,
            "flash": flash,
        },
    )
    # Always persist: the CSRF token (minted above) must survive to the POST, and any
    # popped flash is consumed here.
    websession.write(resp, session)
    return resp


async def _moderate(
    request: Request,
    submission_id: int,
    decision: str,
    csrf_token: str | None,
) -> RedirectResponse:
    """Shared moderation POST: owner gate + CSRF + rate-limit → DB (+ mirror on approve).

    ``decision`` is ``submissions_db.STATUS_APPROVED`` or ``STATUS_REJECTED``.

    **Approve** is a guarded sequence: mirror the row to a GitHub issue → record the
    URL → only then flip ``status='approved'``. The row stays ``pending`` if the mirror
    fails, so the owner can retry; ``attach_issue_url`` (URL-IS-NULL guard) +
    ``set_status`` (status='pending' guard) make a double-click idempotent (plan §4.2).
    **Reject** simply flips ``status='rejected'``.
    """
    session = websession.read(request)
    if session.get("user") is None:
        return RedirectResponse("/admin", status_code=303)
    if not _is_bot_owner(session):
        return RedirectResponse("/admin", status_code=303)
    if not _csrf_ok(session, csrf_token):
        return _moderation_redirect(
            session,
            {
                "ok": False,
                "status": 400,
                "message": "Your session expired or the form was stale — reload and try again.",
            },
        )
    actor_key = str((session.get("user") or {}).get("id") or _client_ip(request))
    if not _MODERATION_LIMITER.allow(actor_key):
        return _moderation_redirect(
            session,
            {
                "ok": False,
                "status": 429,
                "message": "Too many moderation actions too quickly — slow down a moment.",
            },
        )
    if not submissions_db.is_configured():
        return _moderation_redirect(
            session,
            {
                "ok": False,
                "status": 503,
                "message": "The submissions store is not configured (SUBMISSIONS_DB_DSN unset).",
            },
        )
    moderator = str((session.get("user") or {}).get("id") or "")

    if decision == submissions_db.STATUS_REJECTED:
        try:
            changed = await submissions_db.set_status(
                submission_id,
                submissions_db.STATUS_REJECTED,
                moderated_by=moderator,
            )
        except Exception:  # noqa: BLE001 - surface a flash, never a 500
            return _moderation_redirect(
                session,
                {
                    "ok": False,
                    "status": 502,
                    "message": "Couldn't reach the submissions store.",
                },
            )
        msg = (
            f"Rejected submission #{submission_id}."
            if changed
            else f"Submission #{submission_id} was already moderated — no change."
        )
        return _moderation_redirect(
            session,
            {"ok": True, "status": 200, "message": msg},
        )

    # --- approve: mirror → attach URL → flip status (guarded, idempotent) ---
    if not github_mirror.is_configured():
        return _moderation_redirect(
            session,
            {
                "ok": False,
                "status": 503,
                "message": "Approve is disabled — set GITHUB_ISSUE_MIRROR_TOKEN to mirror to GitHub.",
            },
        )
    pending = await submissions_db.list_pending()
    row = next((r for r in pending if int(r["id"]) == submission_id), None)
    if row is None:
        # Not pending anymore (already moderated, or never existed) — idempotent no-op.
        return _moderation_redirect(
            session,
            {
                "ok": True,
                "status": 200,
                "message": f"Submission #{submission_id} is no longer pending — no change.",
            },
        )
    try:
        issue_url = await github_mirror.create_issue(row)
    except Exception:  # noqa: BLE001 - leave the row pending so the owner can retry
        return _moderation_redirect(
            session,
            {
                "ok": False,
                "status": 502,
                "message": f"GitHub issue creation failed — #{submission_id} left pending, retry.",
            },
        )
    await submissions_db.attach_issue_url(submission_id, issue_url)
    await submissions_db.set_status(
        submission_id,
        submissions_db.STATUS_APPROVED,
        moderated_by=moderator,
    )
    return _moderation_redirect(
        session,
        {
            "ok": True,
            "status": 200,
            "message": f"Approved #{submission_id} → mirrored to {issue_url}",
        },
    )


@app.post("/admin/moderation/{submission_id}/approve")
async def post_moderation_approve(request: Request, submission_id: int):
    """Approve a pending submission → mirror to a GitHub issue → flip approved."""
    form = await _form(request)
    return await _moderate(
        request,
        submission_id,
        submissions_db.STATUS_APPROVED,
        form.get("csrf_token"),
    )


@app.post("/admin/moderation/{submission_id}/reject")
async def post_moderation_reject(request: Request, submission_id: int):
    """Reject a pending submission → flip status='rejected' (no mirror)."""
    form = await _form(request)
    return await _moderate(
        request,
        submission_id,
        submissions_db.STATUS_REJECTED,
        form.get("csrf_token"),
    )


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
    csrf_token = _ensure_csrf(session)
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
            "csrf_token": csrf_token,
            "flash": flash,
        },
    )
    # Always persist: the CSRF token (minted above) must survive to the POST, and
    # any popped flash is consumed here.
    websession.write(resp, session)
    return resp


async def _edit(
    request: Request,
    guild_id: str,
    path: str,
    payload: dict[str, Any],
    csrf_token: str | None,
) -> RedirectResponse:
    """Shared editor POST: session admin + CSRF + rate limit → control API → flash."""
    session = websession.read(request)
    if session.get("user") is None or _find_admin_guild(session, guild_id) is None:
        return RedirectResponse("/admin", status_code=303)
    if not _csrf_ok(session, csrf_token):
        session["flash"] = {
            "ok": False,
            "status": 400,
            "message": "Your session expired or the form was stale — reload the page and try again.",
        }
        resp = RedirectResponse(f"/admin/{guild_id}", status_code=303)
        websession.write(resp, session)
        return resp
    actor_key = str((session.get("user") or {}).get("id") or _client_ip(request))
    if not _EDIT_LIMITER.allow(actor_key):
        session["flash"] = {
            "ok": False,
            "status": 429,
            "message": "Too many changes too quickly — slow down a moment.",
        }
        resp = RedirectResponse(f"/admin/{guild_id}", status_code=303)
        websession.write(resp, session)
        return resp
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
    return await _edit(
        request,
        guild_id,
        "/control/settings",
        payload,
        form.get("csrf_token"),
    )


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
    return await _edit(
        request,
        guild_id,
        "/control/help/overlay",
        payload,
        form.get("csrf_token"),
    )


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
    return await _edit(
        request,
        guild_id,
        "/control/help/home",
        payload,
        form.get("csrf_token"),
    )


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
    return await _edit(
        request,
        guild_id,
        "/control/routing",
        payload,
        form.get("csrf_token"),
    )
