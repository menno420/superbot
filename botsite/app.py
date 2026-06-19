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

import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

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
def index(request: Request) -> HTMLResponse:
    """Marketing landing — hero, feature bands, capability counts, 'Add to Discord'."""
    data = data_loader.load_site_data()
    return _render(
        request,
        "index.html",
        "home",
        features=data_loader.features_by_category(data)[:5],
    )


@app.get("/commands", response_class=HTMLResponse)
def commands(request: Request) -> HTMLResponse:
    """Read-only command reference (search + filters). Template: P2 (commands.html)."""
    data = data_loader.load_site_data()
    return _render(
        request,
        "commands.html",
        "commands",
        groups=data_loader.commands_by_category(data),
    )


@app.get("/features", response_class=HTMLResponse)
def features(request: Request) -> HTMLResponse:
    """Feature showcase (function + game catalogue). Template: P2 (features.html)."""
    data = data_loader.load_site_data()
    return _render(
        request,
        "features.html",
        "features",
        groups=data_loader.features_by_category(data),
    )


@app.get("/changelog", response_class=HTMLResponse)
def changelog(request: Request) -> HTMLResponse:
    """User-facing bot changelog. Template: P3 (changelog.html)."""
    data = data_loader.load_site_data()
    return _render(
        request,
        "changelog.html",
        "changelog",
        entries=data.get("bot_changelog", []),
    )


@app.get("/status", response_class=HTMLResponse)
def status(request: Request) -> HTMLResponse:
    """User trust band — online (as of last deploy) · build · counts. Template: P3."""
    data = data_loader.load_site_data()
    return _render(
        request,
        "status.html",
        "status",
        build=data_loader.build_meta(data),
    )


# /submit — GET form + POST intake. Owned by botsite/submit.py (an empty stub here;
# unit P4 fills it). Mounted up front so app.py stays the single routing owner.
app.include_router(submit_router)
