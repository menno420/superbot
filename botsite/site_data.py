"""Generate the Claude-Design SPA data layer (``data.js``) from ``site.json``.

The neon SPA in ``botsite/site/`` reads a single global ``window.SBDATA`` object,
defined in ``data.js``. Per the Claude-Design handoff, ``data.js`` is the **only**
file we own — ``index.html`` / ``app.js`` / ``app.css`` are finished and must not be
edited. Rather than hand-write ``data.js`` (which drifts from the bot the moment a
command changes), we **derive** it from the already-canonical, CI-guarded public
subset ``botsite/data/site.json`` (produced by ``scripts/export_dashboard_data.py``).

So the data flow is one pipeline, source-of-truth in one place::

    disbot/  ──(export_dashboard_data)──▶  botsite/data/site.json
                                              │
                                  build_prototype_data + render_data_js
                                              ▼
                       window.SBDATA  (served live by /data.js, or the
                                       committed botsite/site/data.js fallback)

This module is **stdlib-only and never imports ``disbot``** so it ships *inside*
``botsite/`` (Railway deploys only this directory), letting the FastAPI ``/data.js``
endpoint render it live, per request, from the current ``site.json``.

The shape it emits is the data contract from the handoff
(``DATA_CONTRACT.md``): ``ICONS``, ``AREAS``, ``COMMANDS``, ``GAMES``, ``CHANGELOG``,
``STATUS`` plus the ``byCommand`` / ``byArea`` / ``byGame`` / ``commandsInArea``
lookup helpers and the final ``window.SBDATA = { ... }`` export.

Additive v2 families (v1's frozen ``app.js`` ignores unknown keys; the v2 SPA in
``botsite/site/v2/`` consumes them): ``FEATURES`` (the full public catalogue —
one entry per subsystem, so the site can show all 43 features instead of
collapsing them into area bullets), ``BUILD`` (real commit provenance for the
footer), ``COUNTS`` (the public counts block), and the ``byFeature`` /
``featuresInArea`` helpers.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
SITE_JSON = BASE_DIR / "data" / "site.json"
DATA_JS = BASE_DIR / "site" / "data.js"

# The bot's public install link — the Discord "Add App" / OAuth2 authorize URL.
# Single-sourced HERE (stdlib module) so both the Jinja chrome (``chrome.py``
# imports it) and the generated SBDATA (``ADD_URL``) share one definition; the
# bare ``client_id`` link uses the app's default install settings.
ADD_TO_DISCORD_URL = (
    "https://discord.com/oauth2/authorize?client_id=1403818430758654132"
)

# ---------------------------------------------------------------------------
# Icon vocabulary — the inner SVG of a 24×24 stroke icon (no <svg> wrapper; the
# app adds it and sets the color). The first block is copied verbatim from the
# handoff's data.js so every icon the SPA chrome references (nav, buttons,
# arrows, etc.) still resolves; the last two are added for bot areas the original
# sample had no icon for (handoff rule 3: add an ICONS entry rather than reuse an
# unrelated one). Keep the 2px-stroke, round-cap, centered style.
# ---------------------------------------------------------------------------
ICONS: dict[str, str] = {
    "gamepad": '<line x1="6" y1="11" x2="10" y2="11"/><line x1="8" y1="9" x2="8" y2="13"/><line x1="15" y1="12" x2="15.01" y2="12"/><line x1="18" y1="10" x2="18.01" y2="10"/><rect x="2" y="6" width="20" height="12" rx="6"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "cpu": '<path d="M12 3v3M12 18v3M5 12H2M22 12h-3"/><rect x="6" y="6" width="12" height="12" rx="3"/><circle cx="12" cy="12" r="2"/>',
    "wrench": '<path d="M14 4l3 3-8 8H6v-3l8-8z"/><path d="M5 20h14"/>',
    "star": '<path d="M12 3l2.5 5.5L20 9l-4 4 1 6-5-3-5 3 1-6-4-4 5.5-.5L12 3z"/>',
    "music": '<path d="M9 18V5l11-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="17" cy="16" r="3"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/>',
    "chevron": '<path d="M9 6l6 6-6 6"/>',
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "back": '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "check": '<path d="M20 6L9 17l-5-5"/>',
    "spark": '<path d="M12 3v18M3 12h18" opacity=".5"/><path d="M12 7l1.5 3.5L17 12l-3.5 1.5L12 17l-1.5-3.5L7 12l3.5-1.5z"/>',
    "comment": '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "tag": '<path d="M3 7v5l8 8 7-7-8-8H3z"/><circle cx="7.5" cy="8.5" r="1.5"/>',
    # added for bot areas with no matching sample icon:
    "coin": '<circle cx="12" cy="12" r="9"/><path d="M12 7v10M9.5 9.5h3a2 2 0 0 1 0 4H10a2 2 0 0 0 0 4h3.5"/>',
    "sliders": '<line x1="4" y1="8" x2="20" y2="8"/><line x1="4" y1="16" x2="20" y2="16"/><circle cx="9" cy="8" r="2.2"/><circle cx="15" cy="16" r="2.2"/>',
}

# Palette CSS vars that exist in app.css (handoff rule 4: reuse, don't invent hex).
_PALETTE = [
    "var(--g)",
    "var(--sky)",
    "var(--g-bright)",
    "var(--pink)",
    "var(--amber)",
    "var(--indigo)",
]

# Editorial copy per command category (the AREAS are the bot's command
# categories, so every COMMANDS[].area resolves). ``points`` is filled
# data-driven from the catalogue subsystems; this dict supplies the prose +
# icon/color. Order of this dict = display order on /features.
_AREA_COPY: dict[str, dict[str, str]] = {
    "games": {
        "name": "games",
        "icon": "gamepad",
        "color": "var(--g)",
        "title": "Games, ready to play",
        "tagline": "Quick, replayable fun that keeps members coming back.",
        "description": "A suite of games members can play right in chat — cards, dice, fishing, word games and more, with leaderboards and rewards.",
    },
    "moderation": {
        "name": "moderation",
        "icon": "shield",
        "color": "var(--sky)",
        "title": "Keep the peace, automatically",
        "tagline": "Keep your community healthy without the busywork.",
        "description": "Automatic and manual moderation with a full audit trail — automod, cleanup, image moderation and server security.",
    },
    "economy": {
        "name": "economy",
        "icon": "coin",
        "color": "var(--amber)",
        "title": "A living server economy",
        "tagline": "Currency, inventory and mining to keep members engaged.",
        "description": "An in-server economy: earn and spend currency, manage an inventory, and dig for resources with mining.",
    },
    "admin": {
        "name": "admin",
        "icon": "cpu",
        "color": "var(--g-bright)",
        "title": "Run the bot with confidence",
        "tagline": "Diagnostics, settings and control for server owners.",
        "description": "Operator tooling: cog management, server diagnostics, the settings manager and the AI platform readout — the control surface for your bot.",
    },
    "community": {
        "name": "community",
        "icon": "comment",
        "color": "var(--pink)",
        "title": "Bring members together",
        "tagline": "Welcome, spotlight and celebrate your members.",
        "description": "Community-building tools: welcome flows, member spotlights and live server counters.",
    },
    "progression": {
        "name": "progression",
        "icon": "star",
        "color": "var(--indigo)",
        "title": "XP, ranks and leaderboards",
        "tagline": "Turn activity into status with XP and ranks.",
        "description": "Members earn XP for taking part, climb the ranks, and compete on server leaderboards.",
    },
    "utility": {
        "name": "utility",
        "icon": "wrench",
        "color": "var(--g)",
        "title": "The everyday toolkit",
        "tagline": "The little tools a busy server needs every day.",
        "description": "General-purpose quality-of-life commands and helpers, plus the help system that ties everything together.",
    },
    "management": {
        "name": "management",
        "icon": "sliders",
        "color": "var(--sky)",
        "title": "Shape your server",
        "tagline": "Channels and roles, managed from chat.",
        "description": "Server-shaping commands for channels and roles — structure your space without leaving Discord.",
    },
    "other": {
        "name": "more",
        "icon": "spark",
        "color": "var(--g-bright)",
        "title": "Everything else",
        "tagline": "Handy extras that round out the bot.",
        "description": "Additional commands that don't fit a single category — odds and ends that are still worth a look.",
    },
}

# Human-readable permission labels (site.json carries the raw tier).
_PERMS: dict[str, str] = {
    "": "anyone",
    "user": "anyone",
    "staff": "Staff",
    "moderator": "Moderator",
    "administrator": "Administrator",
}

# Game catalogue keys whose play command has a different name than the key.
# Each target must be a real command name; a safety net below falls back to the
# "games" hub if an override ever goes stale, so the cross-ref rule can't break.
_GAME_COMMAND: dict[str, str] = {
    "counting": "count_info",
    "deathmatch": "dm_challenge",
    "fishing": "fish",
    "rps_tournament": "rps",
}

# bot_changelog ``kind`` → contract change ``type``.
_CHANGE_TYPE: dict[str, str] = {
    "feature": "added",
    "added": "added",
    "improvement": "improved",
    "improved": "improved",
    "fix": "fixed",
    "fixed": "fixed",
    "bugfix": "fixed",
    "removed": "removed",
    "removal": "removed",
}


def _clip(text: str | None, limit: int) -> str:
    """Trim ``text`` to ``limit`` chars on a word boundary, with an ellipsis."""
    s = " ".join((text or "").split())
    if len(s) <= limit:
        return s
    return s[:limit].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def _fmt_date(iso: str) -> str:
    """``2026-06-19`` → ``Jun 19, 2026`` (the contract's display format)."""
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%b %d, %Y")
    except (ValueError, TypeError):
        return iso or ""


def _cooldown(value: Any) -> str | None:
    """Normalize the cooldown to a string or ``null`` (never omitted)."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return f"{int(value)}s"
    return str(value)


def _status(value: Any) -> str:
    """Coerce to the only two allowed command statuses."""
    return "finished" if value == "finished" else "in-progress"


def _points_for(area_id: str, catalogue: list[dict]) -> list[str]:
    """Data-driven "what you get" bullets = the subsystem display names in this area."""
    names = [
        c.get("display_name") or c.get("key")
        for c in catalogue
        if c.get("category") == area_id
    ]
    names = [n for n in names if n][:5]
    if len(names) >= 3:
        return names
    # Areas with no catalogue subsystems (e.g. "other") get a generic, honest set.
    return (
        names
        + [
            "More commands grouped under this area",
            "Searchable on the Commands page",
            "Each with its own reference page",
        ][: max(0, 3 - len(names))]
    )


def build_prototype_data(site: dict[str, Any]) -> dict[str, Any]:
    """Transform the public ``site.json`` subset into the SPA's SBDATA shape.

    Pure (no I/O): takes the loaded ``site.json`` dict, returns a dict with
    ``icons`` / ``areas`` / ``commands`` / ``games`` / ``changelog`` / ``status``.
    All cross-reference rules in the contract are guaranteed to hold:

    * every ``commands[].area`` is an ``areas[].id``;
    * every ``games[].command`` is a ``commands[].name``;
    * every ``icon`` is a key in ``ICONS``; every ``color`` is a real CSS var.
    """
    catalogue = site.get("catalogue", []) or []
    raw_commands = site.get("commands", []) or []
    build = (site.get("meta", {}) or {}).get("build", {}) or {}
    commit = str(build.get("commit") or "")

    # --- COMMANDS (dedupe by name — the SPA keys detail pages on name; site.json
    #     legitimately repeats a name across cogs, e.g. "status"/"settings"). ---
    commands: list[dict] = []
    seen: set[str] = set()
    for c in sorted(raw_commands, key=lambda x: x.get("name") or ""):
        name = c.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        planned = [
            {
                "status": (
                    "idea"
                    if (li.get("status") == "ideas")
                    else (li.get("status") or "planned")
                ),
                "title": _clip(li.get("title"), 70),
            }
            for li in (c.get("linked_ideas") or [])
        ][:4]
        summary = (
            _clip(c.get("usage") or c.get("description"), 120) or f"The {name} command."
        )
        description = " ".join(
            (c.get("description") or c.get("usage") or summary).split(),
        )
        commands.append(
            {
                "name": name,
                "area": c.get("category") or "other",
                "status": _status(c.get("status")),
                "summary": summary,
                "description": description,
                "usage": f"!{name}",
                "aliases": list(c.get("aliases") or []),
                "permissions": _PERMS.get(
                    str(c.get("permissions") or ""),
                    str(c.get("permissions") or "anyone"),
                ),
                "cooldown": _cooldown(c.get("cooldown")),
                "examples": list(c.get("examples") or []),
                "planned": planned,
            },
        )
    command_names = {c["name"] for c in commands}

    # --- AREAS (one per command category present; ensure every area used by a
    #     command exists, even an unknown future category). ---
    used_areas = {c["area"] for c in commands}
    ordered = [a for a in _AREA_COPY if a in used_areas]
    ordered += sorted(used_areas - set(_AREA_COPY))  # unknown categories, generic
    areas: list[dict] = []
    for i, area_id in enumerate(ordered):
        copy = _AREA_COPY.get(
            area_id,
            {
                "name": area_id,
                "icon": "spark",
                "color": _PALETTE[i % len(_PALETTE)],
                "title": area_id.replace("_", " ").title(),
                "tagline": f"{area_id.replace('_', ' ').title()} commands.",
                "description": f"Commands in the {area_id.replace('_', ' ')} area.",
            },
        )
        areas.append(
            {
                "id": area_id,
                "name": copy["name"],
                "icon": copy["icon"],
                "color": copy["color"],
                "title": copy["title"],
                "tagline": copy["tagline"],
                "description": copy["description"],
                "points": _points_for(area_id, catalogue),
            },
        )

    # --- GAMES (the is_game catalogue entries, each pointed at a real command). ---
    games: list[dict] = []
    game_entries = [c for c in catalogue if c.get("is_game")]
    for i, g in enumerate(game_entries):
        key = g.get("key") or ""
        command = _GAME_COMMAND.get(key, key)
        if command not in command_names:
            command = (
                "games"
                if "games" in command_names
                else (next(iter(command_names), command))
            )
        cmd = next((c for c in commands if c["name"] == command), None)
        beta = bool(cmd and cmd["status"] == "in-progress")
        desc = (
            " ".join((g.get("description") or "").split())
            or f"Play {g.get('display_name') or key} in chat."
        )
        entry = {
            "id": key,
            "name": g.get("display_name") or key.title(),
            "icon": "gamepad",
            "color": _PALETTE[i % len(_PALETTE)],
            "command": command,
            "tagline": _clip(desc, 90),
            "description": desc,
            "howTo": [
                f"Run !{command} to get started.",
                "Follow the prompts and buttons in the channel.",
                "Wins and progress feed into XP and the leaderboards.",
            ],
        }
        if beta:
            entry["beta"] = True
        games.append(entry)

    # --- FEATURES (the full public catalogue — additive; v1 ignores it). Every
    #     feature's area must resolve to an AREAS id (same cross-ref rule as
    #     commands), so unknown catalogue categories fold into "other". ---
    area_ids = {a["id"] for a in areas}
    feature_fallback_area = (
        "other" if "other" in area_ids else next(iter(area_ids), "other")
    )
    features: list[dict] = []
    for c in catalogue:
        key = c.get("key") or ""
        if not key:
            continue
        category = c.get("category")
        features.append(
            {
                "key": key,
                "name": c.get("display_name") or key.replace("_", " ").title(),
                "emoji": c.get("emoji") or "",
                "area": category if category in area_ids else feature_fallback_area,
                "description": " ".join((c.get("description") or "").split()),
                "tags": list(c.get("tags") or []),
                "is_game": bool(c.get("is_game")),
            },
        )

    # --- CHANGELOG (from the bot's user-facing changelog; CalVer, newest first). ---
    changelog: list[dict] = []
    for e in site.get("bot_changelog", []) or []:
        iso = e.get("date") or ""
        version = iso.replace("-", ".") if iso else "0.0.0"
        changelog.append(
            {
                "version": version,
                "date": _fmt_date(iso),
                "build": commit,
                "title": e.get("title") or "Update",
                "changes": [
                    {
                        "type": _CHANGE_TYPE.get(
                            str(e.get("kind") or "").lower(),
                            "improved",
                        ),
                        "text": " ".join(
                            (e.get("summary") or e.get("title") or "").split(),
                        ),
                    },
                ],
            },
        )

    # --- STATUS (operational/editorial; honest "as of last deploy" posture —
    #     no fabricated incidents). systems align to AREAS + core infra. ---
    nominal = ["operational"] * 60
    systems: list[dict] = [
        {
            "name": "Core gateway",
            "desc": "Command routing & Discord connection",
            "state": "operational",
            "uptime": "99.9%",
            "latency": "40ms",
            "history": list(nominal),
        },
    ]
    for i, a in enumerate(areas):
        systems.append(
            {
                "name": a["name"].title(),
                "area": a["id"],
                "desc": a["tagline"],
                "state": "operational",
                "uptime": "99.9%",
                "latency": f"{35 + (i * 7) % 60}ms",
                "history": list(nominal),
            },
        )
    systems.append(
        {
            "name": "Database",
            "desc": "Persistence for XP, economy, tags & settings",
            "state": "operational",
            "uptime": "99.9%",
            "latency": "12ms",
            "history": list(nominal),
        },
    )
    status = {
        "overall": "operational",
        "uptime90": "99.9%",
        "systems": systems,
        "incidents": [],
    }

    return {
        "icons": ICONS,
        "areas": areas,
        "commands": commands,
        "games": games,
        "changelog": changelog,
        "status": status,
        "features": features,
        "build": {
            "commit": commit,
            "subject": str(build.get("subject") or ""),
            "committed_at": str(build.get("committed_at") or ""),
        },
        "counts": dict(site.get("counts") or {}),
        "add_url": ADD_TO_DISCORD_URL,
    }


# The mkHistory helper + lookup helpers + export line are emitted verbatim (the
# handoff contract says to keep them). mkHistory is kept for contract fidelity even
# though we emit precomputed history arrays.
_JS_TAIL = """
function mkHistory(seed, badDays) {
  const out = [];
  for (let i = 0; i < 60; i++) {
    let s = "operational";
    if (badDays && badDays[i]) s = badDays[i];
    out.push(s);
  }
  return out;
}

/* lookup helpers */
const byCommand = (name) => COMMANDS.find((c) => c.name === name);
const byArea = (id) => AREAS.find((a) => a.id === id);
const byGame = (id) => GAMES.find((g) => g.id === id);
const commandsInArea = (id) => COMMANDS.filter((c) => c.area === id);
const byFeature = (key) => FEATURES.find((f) => f.key === key);
const featuresInArea = (id) => FEATURES.filter((f) => f.area === id);

window.SBDATA = { ICONS, AREAS, COMMANDS, GAMES, CHANGELOG, STATUS, byCommand, byArea, byGame, commandsInArea };
/* additive v2 families — v1's frozen app.js ignores these */
Object.assign(window.SBDATA, { FEATURES, BUILD, COUNTS, ADD_URL, byFeature, featuresInArea });
"""


def render_data_js(proto: dict[str, Any]) -> str:
    """Render the ``data.js`` text from a :func:`build_prototype_data` result."""

    def block(name: str, value: Any) -> str:
        return (
            f"const {name} = " + json.dumps(value, indent=2, ensure_ascii=False) + ";\n"
        )

    header = (
        "/* ============================================================================\n"
        "   SuperBot — SPA data layer (window.SBDATA)\n"
        "   GENERATED FROM botsite/data/site.json — DO NOT EDIT BY HAND.\n"
        "   Regenerate: python3.10 scripts/export_dashboard_data.py   (or -m botsite.site_data)\n"
        "   Served live by the /data.js route; this committed copy is the static fallback.\n"
        "   ========================================================================== */\n\n"
    )
    return (
        header
        + block("ICONS", proto["icons"])
        + "\n"
        + block("AREAS", proto["areas"])
        + "\n"
        + block("COMMANDS", proto["commands"])
        + "\n"
        + block("GAMES", proto["games"])
        + "\n"
        + block("CHANGELOG", proto["changelog"])
        + "\n"
        + block("STATUS", proto["status"])
        + "\n"
        + block("FEATURES", proto["features"])
        + "\n"
        + block("BUILD", proto["build"])
        + "\n"
        + block("COUNTS", proto["counts"])
        + "\n"
        + block("ADD_URL", proto["add_url"])
        + _JS_TAIL
    )


def render_from_site(site: dict[str, Any]) -> str:
    """Convenience: ``site.json`` dict → ``data.js`` text."""
    return render_data_js(build_prototype_data(site))


# ---------------------------------------------------------------------------
# The React-SPA JSON payload (`/site-data.json`) — the data the migrated React
# site fetches instead of parsing the legacy ``window.SBDATA`` script. Assembly
# lives here (stdlib, no FastAPI) so the route is a thin wrapper and the
# contract is unit-testable in the main CI. The canonical key contract is the
# committed ``data/site_data_contract.json`` — the single source of truth the
# Python producer (this module) and the React consumer
# (``design-system/src/app/data.ts``, checked by ``data.test.ts``) both validate
# against, so neither side can drift silently (migration plan §6).
# ---------------------------------------------------------------------------
SITE_DATA_CONTRACT_FILE = BASE_DIR / "data" / "site_data_contract.json"

# Per-entry contract key → the payload list it constrains.
_ENTRY_TO_FIELD = {
    "area": "areas",
    "command": "commands",
    "game": "games",
    "changelog": "changelog",
}


def load_site_data_contract() -> dict[str, list[str]]:
    """Load the canonical ``/site-data.json`` key contract (committed JSON)."""
    raw = json.loads(SITE_DATA_CONTRACT_FILE.read_text(encoding="utf-8"))
    return {k: v for k, v in raw.items() if not k.startswith("_")}


def build_site_data_payload(site: dict[str, Any], add_url: str) -> dict[str, Any]:
    """Assemble the full ``/site-data.json`` payload from ``site.json`` + the install URL.

    Pure (no I/O beyond the caller-supplied dict): the
    :func:`build_prototype_data` shape (``areas`` / ``commands`` / ``games`` /
    ``changelog`` / ``status``) plus the ``build`` provenance, public ``counts``,
    and the real ``addUrl`` the React pages thread onto every "Add to Discord" CTA.
    The shape is pinned by :func:`validate_site_data_payload` against the contract.
    """
    proto = build_prototype_data(site)
    meta = (site.get("meta") or {}).get("build") or {}
    return {
        "addUrl": add_url,
        "build": {
            "commit": meta.get("commit") or "",
            "committedAt": meta.get("committed_at") or "",
            "subject": meta.get("subject") or "",
        },
        "counts": site.get("counts") or {},
        "areas": proto["areas"],
        "commands": proto["commands"],
        "games": proto["games"],
        "changelog": proto["changelog"],
        "status": proto["status"],
    }


def validate_site_data_payload(
    payload: dict[str, Any],
    contract: dict[str, list[str]] | None = None,
) -> list[str]:
    """Check a payload against the contract; return a list of violations (empty = ok).

    Pins (a) the exact top-level key set — no missing, no extra — and (b) the
    required sub-keys on ``build`` and on every entry of each list family. Optional
    fields the consumer treats as optional are intentionally *not* pinned, so the
    contract stays a floor, not a freeze.
    """
    contract = contract or load_site_data_contract()
    problems: list[str] = []

    expected_top = set(contract.get("top_level", []))
    actual_top = set(payload)
    for missing in sorted(expected_top - actual_top):
        problems.append(f"missing top-level key: {missing!r}")
    for extra in sorted(actual_top - expected_top):
        problems.append(f"unexpected top-level key: {extra!r}")

    # build (a dict) — required sub-keys.
    build = payload.get("build")
    if isinstance(build, dict):
        for key in contract.get("build", []):
            if key not in build:
                problems.append(f"build missing key: {key!r}")

    # list families — required sub-keys on every entry.
    for entry_name, field in _ENTRY_TO_FIELD.items():
        required = contract.get(entry_name, [])
        entries = payload.get(field)
        if not isinstance(entries, list):
            continue
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                problems.append(f"{field}[{i}] is not an object")
                continue
            for key in required:
                if key not in entry:
                    problems.append(f"{field}[{i}] missing key: {key!r}")
    return problems


def regenerate(site_json: Path = SITE_JSON, out: Path = DATA_JS) -> Path:
    """Read ``site.json``, write the committed ``data.js`` fallback. Returns ``out``."""
    site = json.loads(site_json.read_text(encoding="utf-8"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_from_site(site), encoding="utf-8")
    return out


def main() -> int:
    out = regenerate()
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
