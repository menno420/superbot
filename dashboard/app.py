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
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "dashboard.json"

_EMPTY: dict[str, Any] = {
    "meta": {"generated_at": "", "counts": {}},
    "catalogue": [],
    "ideas": [],
    "bugs": [],
    "updates": [],
}

app = FastAPI(title="SuperBot Dashboard", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def load_data() -> dict[str, Any]:
    """Load the generated dashboard payload, falling back to an empty shape."""
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(_EMPTY)


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
