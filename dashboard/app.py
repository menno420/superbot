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
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "dashboard.json"

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


@app.get("/aliases", response_class=HTMLResponse)
def aliases(request: Request):
    """Suggest a command alias — pick a command, propose an alias, get a live
    collision check (against every command name, alias, and synonym) plus a
    prefilled GitHub issue and a ready-to-paste ``synonyms.py`` snippet.
    """
    data = load_data()
    commands_list = sorted(
        {c["name"] for cog in data.get("cogs", []) for c in cog["commands"]},
    )
    # Map every token already in use -> what owns it, so the suggestion form can
    # say *why* a proposed alias collides. Synonyms first, then aliases, then
    # command names last so the strongest owner (a real command) wins a tie.
    taken: dict[str, str] = {}
    for syn in data.get("synonyms", []):
        for token in syn["synonyms"]:
            taken[token.lower()] = f"synonym of !{syn['canonical']}"
    for cog in data.get("cogs", []):
        for cmd in cog["commands"]:
            for token in cmd.get("aliases") or []:
                taken[token.lower()] = f"alias of !{cmd['name']}"
    for name in commands_list:
        taken[name.lower()] = "a command"
    return templates.TemplateResponse(
        request,
        "aliases.html",
        {
            "data": data,
            "page": "aliases",
            "commands": commands_list,
            "taken": taken,
        },
    )


@app.get("/commands", response_class=HTMLResponse)
def commands(request: Request):
    """Cog & command explorer — invocation type (prefix/slash) + button backing."""
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
        {"data": data, "page": "commands", "stats": stats, "sysmap": sysmap},
    )
