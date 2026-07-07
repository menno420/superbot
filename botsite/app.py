"""FastAPI app for the SuperBot public marketing site (the bot site).

The **public** half of the website two-site split
(``docs/planning/website-two-site-split-plan-2026-06-19.md``). It is decoupled from
the bot: it reads only the committed public subset ``botsite/data/site.json``
(produced by ``scripts/export_dashboard_data.py``) and **never imports ``disbot``**.

This module is the **single owner of routing** (plan §5 — P1): it wires *every* route
up front so the parallel back-half units (templates, the submit intake) can fill in
their pieces without touching this file. The page routes render their template by
filename; the template files for ``/commands`` / ``/features`` / ``/changelog`` /
``/status`` land in later units (P2/P3), so those routes are wired now but their
templates may not exist yet — that is expected. ``/`` and ``/healthz`` are the only
surfaces this unit fully ships templates for.

Secret posture (plan §4.4): this app holds **at most one** secret — the INSERT-only
submissions DSN used by the ``/submit`` intake (mounted from ``botsite/submit.py``,
an empty stub until unit P4). It never holds the GitHub mirror token, the control-API
token, or any OAuth secret. The gated "manage my server" surface is a **separate
service**, not a router mounted here — so this marketing app stays secret-free and the
manager drops in without re-coupling.

Local run::

    pip install -r botsite/requirements.txt
    python3.10 scripts/export_dashboard_data.py --targets site   # (re)generate site.json
    uvicorn botsite.app:app --reload

Deploy: a new Railway service (Root Directory = ``botsite``) — see ``botsite/README.md``.
There is intentionally **no ``static/`` directory** — the repo's ``.gitignore`` ignores
``static/`` (the #970 deploy-crash gotcha); styling is the Tailwind CDN + a small inline
block in ``base.html``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
# The Claude-Design SPA lives here (NOT a static/ dir — that name is gitignored, the
# #970 deploy-crash gotcha). index.html/app.js/app.css are copied verbatim from the
# design handoff (do-not-edit); data.js is generated from site.json.
SITE_DIR = BASE_DIR / "site"
# The program design system + the v2 front-end + the program console (all new
# files — v1's three design-owned files stay untouched; v1 remains the default
# front-end until the owner flips BOTSITE_FRONTEND=v2).
DS_DIR = BASE_DIR / "ds"
V2_DIR = SITE_DIR / "v2"
CONSOLE_DIR = BASE_DIR / "console"
CONSOLE_JSON = BASE_DIR / "data" / "console.json"

# Which front-end `/` serves: "v1" (default — the Claude-Design SPA) or "v2"
# (the program-design-system rebuild). v2 is always reachable at /v2 either way,
# so the owner can review it live before flipping the env var on Railway.
FRONTEND = os.environ.get("BOTSITE_FRONTEND", "v1").strip().lower()

# The app runs both as a package (`botsite.app`, local) and as a top-level module
# (`app:app`, Railway Root Directory = botsite), and the test loads app.py by file
# path. Putting this directory on sys.path lets the sibling modules import
# identically in all three contexts (mirrors the dashboard's proven shim). The
# sibling imports below intentionally follow the shim (E402), so they are isolated
# from the third-party imports above.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import chrome  # noqa: E402  - sibling, after the sys.path shim above
import data_loader  # noqa: E402  - after the sys.path shim above
import site_data  # noqa: E402  - site.json → SPA data.js generator (stdlib-only)
from submit import router as submit_router  # noqa: E402  - after the shim

app = FastAPI(title="SuperBot", docs_url=None, redoc_url=None)

# The shared template chrome (the freshness band + the "Add to Discord" install URL)
# lives in ``chrome.py`` so BOTH this app's Jinja env and the /submit router's own Jinja
# env inject the same context — otherwise a page rendered by one env shows empty chrome
# (the /submit dead-install-button regression). See ``chrome.site_context``.
templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates"),
    context_processors=[chrome.site_context],
)


def _render(request: Request, template: str, page: str, **extra: Any) -> HTMLResponse:
    """Render ``template`` with the shared data payload + page marker.

    Centralises the ``load_site_data`` + ``page`` plumbing every page route shares,
    so the wired routes stay one-liners and a later unit's template only needs the
    context keys it consumes.
    """
    context: dict[str, Any] = {"data": data_loader.load_site_data(), "page": page}
    context.update(extra)
    return templates.TemplateResponse(request, template, context)


# ===========================================================================
# Routes — ALL wired up front (plan §5). Page templates for /commands,
# /features, /changelog, /status land in later units; the routes reference them
# by filename now. /submit is mounted from the (stub) submit router.
# ===========================================================================


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe (used by Railway)."""
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def index() -> FileResponse:
    """Serve the public site front-end (v1 by default; v2 behind the env flip).

    Both front-ends are hash-routed SPAs rendering client-side from
    ``window.SBDATA`` (loaded from ``/data.js``). v1 (the Claude-Design SPA)
    stays the default; setting ``BOTSITE_FRONTEND=v2`` on the Railway service
    flips ``/`` to the v2 shell (which references its assets absolutely, so it
    serves identically from ``/`` and ``/v2``). v1 keeps working at its asset
    routes either way — the flip is one env var, and the rollback is unsetting it.
    """
    if FRONTEND == "v2":
        return FileResponse(V2_DIR / "index.html", media_type="text/html")
    return FileResponse(SITE_DIR / "index.html", media_type="text/html")


@app.get("/app.js")
def spa_js() -> FileResponse:
    """SPA router + views (verbatim design asset)."""
    return FileResponse(SITE_DIR / "app.js", media_type="application/javascript")


@app.get("/app.css")
def spa_css() -> FileResponse:
    """SPA theme (verbatim design asset)."""
    return FileResponse(SITE_DIR / "app.css", media_type="text/css")


@app.get("/data.js")
def spa_data() -> Response:
    """The SPA data layer — generated **live** from the current ``site.json``.

    This is the dynamic seam (owner goal: "all data should dynamically load"): each
    request renders ``window.SBDATA`` from the latest committed ``site.json`` via
    ``site_data``. The committed ``botsite/site/data.js`` is the static fallback for
    opening the prototype as a bare file; in the running service this route wins.
    """
    js = site_data.render_from_site(data_loader.load_site_data())
    # No long cache: the data tracks each deploy's site.json.
    return Response(
        content=js,
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )


@app.get("/site-data.json")
def site_data_json() -> Response:
    """The React-SPA data layer — the same public data as ``/data.js``, as pure JSON.

    The migrated React site (``design-system/src/app``) ``fetch()``es this instead of
    parsing the legacy ``window.SBDATA`` script. It returns the
    :func:`site_data.build_prototype_data` shape (``areas`` / ``commands`` / ``games``
    / ``changelog`` / ``status``) plus the ``build`` provenance, public ``counts``, and
    the real ``addUrl`` install link — so the React app needs no second data path and
    its "Add to Discord" CTA resolves. Same public subset, same redaction posture as
    ``/data.js``; ``botsite`` never imports ``disbot``.
    """
    site = data_loader.load_site_data()
    payload = site_data.build_site_data_payload(site, chrome.ADD_TO_DISCORD_URL)
    return Response(
        content=json.dumps(payload, ensure_ascii=False),
        media_type="application/json",
        headers={"Cache-Control": "no-cache"},
    )


# ===========================================================================
# The v2 estate — program design system (/ds, /design), the v2 SPA (/v2), and
# the program console (/console). All explicit FileResponses: app.py stays the
# single owner of routing, and only these named files are ever served.
# ===========================================================================

_V2_FILES = {
    "index.html": "text/html",
    "app.js": "application/javascript",
    "app.css": "text/css",
}
_DS_FILES = {
    "tokens.css": "text/css",
    "components.css": "text/css",
    "ds.js": "application/javascript",
    "styleguide.js": "application/javascript",
}
_CONSOLE_FILES = {
    "index.html": "text/html",
    "console.js": "application/javascript",
    "console.css": "text/css",
}


@app.get("/v2", response_class=HTMLResponse)
@app.get("/v2/", response_class=HTMLResponse)
def site_v2() -> FileResponse:
    """The v2 front-end shell (always reachable; `/` flips via BOTSITE_FRONTEND)."""
    return FileResponse(V2_DIR / "index.html", media_type="text/html")


@app.get("/v2/{asset}")
def v2_asset(asset: str) -> Response:
    """v2 SPA assets (explicit whitelist — no directory serving)."""
    media = _V2_FILES.get(asset)
    if media is None:
        return Response(status_code=404)
    return FileResponse(V2_DIR / asset, media_type=media)


@app.get("/ds/{asset}")
def ds_asset(asset: str) -> Response:
    """Program design-system assets shared by every program site."""
    media = _DS_FILES.get(asset)
    if media is None:
        return Response(status_code=404)
    return FileResponse(DS_DIR / asset, media_type=media)


@app.get("/design", response_class=HTMLResponse)
def design_styleguide() -> FileResponse:
    """The living style guide — renders every design-system token + component."""
    return FileResponse(DS_DIR / "styleguide.html", media_type="text/html")


@app.get("/console", response_class=HTMLResponse)
@app.get("/console/", response_class=HTMLResponse)
def console_index() -> FileResponse:
    """The program console — the owner's one-glance page (honest lanes only)."""
    return FileResponse(CONSOLE_DIR / "index.html", media_type="text/html")


@app.get("/console/{asset}")
def console_asset(asset: str) -> Response:
    """Console assets + its data feed (committed console.json, if exported)."""
    if asset == "data.json":
        if CONSOLE_JSON.exists():
            return FileResponse(
                CONSOLE_JSON,
                media_type="application/json",
                headers={"Cache-Control": "no-cache"},
            )
        return JSONResponse(
            {"available": False, "reason": "console.json not exported yet"},
            status_code=404,
        )
    media = _CONSOLE_FILES.get(asset)
    if media is None:
        return Response(status_code=404)
    return FileResponse(CONSOLE_DIR / asset, media_type=media)


# Legacy page routes — the earlier server-rendered Jinja front-end, kept as a
# working fallback (owner decision: the SPA is what visitors see at `/`; the Jinja
# pages stay in repo and reachable). The SPA's own nav uses in-page hash routes
# such as "#/commands", so normal visitors never hit these; they remain for old
# bookmarks / no-JS fallback and render the same site.json data.
@app.get("/commands", response_class=HTMLResponse)
def commands(request: Request) -> HTMLResponse:
    """Read-only command reference (Jinja fallback). SPA equivalent: /#/commands."""
    data = data_loader.load_site_data()
    return _render(
        request,
        "commands.html",
        "commands",
        groups=data_loader.commands_by_category(data),
    )


@app.get("/features", response_class=HTMLResponse)
def features(request: Request) -> HTMLResponse:
    """Feature showcase (Jinja fallback). SPA equivalent: /#/features."""
    data = data_loader.load_site_data()
    return _render(
        request,
        "features.html",
        "features",
        groups=data_loader.features_by_category(data),
    )


@app.get("/changelog", response_class=HTMLResponse)
def changelog(request: Request) -> HTMLResponse:
    """User-facing changelog (Jinja fallback). SPA equivalent: /#/changelog."""
    data = data_loader.load_site_data()
    return _render(
        request,
        "changelog.html",
        "changelog",
        entries=data.get("bot_changelog", []),
    )


@app.get("/status", response_class=HTMLResponse)
def status(request: Request) -> HTMLResponse:
    """Trust band (Jinja fallback). SPA equivalent: /#/status."""
    data = data_loader.load_site_data()
    return _render(request, "status.html", "status", build=data_loader.build_meta(data))


# /submit — GET form + POST intake. Owned by botsite/submit.py (an empty stub here;
# unit P4 fills it). Mounted up front so app.py stays the single routing owner.
app.include_router(submit_router)
