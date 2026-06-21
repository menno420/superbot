"""Embed theme presets + starter-message templates for role menus.

Plan §4.6 (b) themes + (c) templates: cheap data that makes a freshly-built role
menu look good in two taps instead of starting from a blank page.

* **Themes** (code) — a named accent colour + optional footer styling, keyed by
  ``role_menus.theme``. Built on :mod:`utils.ui_constants` so the palette stays
  consistent with the rest of the bot.
* **Templates** (data) — ready-made title/description starters loaded from
  ``disbot/data/role_menu_templates.json`` (the ``creatures`` / ``general_content``
  JSON-catalogue precedent), with a fail-safe fallback so a missing/garbled file
  never breaks the builder.

Both apply to the in-Discord builder now and, later, the web builder (§3.5) —
they are pure presentation data, surface-agnostic.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import discord

from utils.ui_constants import GAME_COLOR, INFO_COLOR, ROLE_COLOR

_TEMPLATES_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "role_menu_templates.json",
)


@dataclass(frozen=True)
class Theme:
    """A named embed theme — accent colour + optional footer."""

    key: str
    name: str
    color: discord.Color
    footer: str | None = None


# Ordered so the builder's theme picker lists them predictably; ``default`` first.
_THEMES: tuple[Theme, ...] = (
    Theme("default", "Default", ROLE_COLOR, "Pick your roles below."),
    Theme(
        "announcement",
        "Announcement",
        discord.Color.blurple(),
        "Self-assign the roles you want.",
    ),
    Theme("neon", "Neon", discord.Color.magenta(), None),
    Theme("pastel", "Pastel", discord.Color.from_rgb(186, 225, 255), None),
    Theme("game", "Game", GAME_COLOR, "Game on — grab your roles."),
    Theme("info", "Info", INFO_COLOR, None),
)

_THEME_INDEX: dict[str, Theme] = {t.key: t for t in _THEMES}
_DEFAULT_THEME = _THEMES[0]


def all_themes() -> tuple[Theme, ...]:
    """Every theme preset, in display order."""
    return _THEMES


def resolve_theme(key: str | None) -> Theme:
    """Return the theme for ``key`` (falls back to ``default`` for unknown keys)."""
    return _THEME_INDEX.get(key or "", _DEFAULT_THEME)


@dataclass(frozen=True)
class Template:
    """A starter message — pre-filled title/description (and optional theme)."""

    key: str
    name: str
    title: str
    description: str
    theme: str = "default"


# Fail-safe defaults — also the canonical set; the JSON file may extend/override.
_FALLBACK_TEMPLATES: tuple[Template, ...] = (
    Template(
        "blank",
        "Blank",
        "Pick your roles",
        "Select the roles you'd like below.",
    ),
    Template(
        "game",
        "🎮 Game roles",
        "🎮 Game Roles",
        "Pick the games you play to get pinged for squads and find teammates.",
        theme="game",
    ),
    Template(
        "notify",
        "🔔 Notification roles",
        "🔔 Notifications",
        "Choose which announcements you want to be pinged for.",
        theme="announcement",
    ),
    Template(
        "colour",
        "🎨 Colour roles",
        "🎨 Colour Roles",
        "Give yourself a splash of colour — pick a name colour below.",
        theme="pastel",
    ),
    Template(
        "verify",
        "✅ Verify to enter",
        "✅ Verify",
        "React/click below to verify and unlock the rest of the server.",
        theme="info",
    ),
)


def _load_templates() -> tuple[Template, ...]:
    """Load starter templates from the JSON catalogue (fail-safe → fallback)."""
    try:
        with open(_TEMPLATES_FILE, encoding="utf-8") as fh:
            raw = json.load(fh)
        rows = raw.get("templates", []) if isinstance(raw, dict) else []
        loaded: list[Template] = []
        for r in rows:
            if not isinstance(r, dict) or not {"key", "title"} <= r.keys():
                continue
            loaded.append(
                Template(
                    key=str(r["key"]),
                    name=str(r.get("name", r["title"])),
                    title=str(r["title"]),
                    description=str(r.get("description", "")),
                    theme=str(r.get("theme", "default")),
                ),
            )
        return tuple(loaded) if loaded else _FALLBACK_TEMPLATES
    except (OSError, ValueError):
        return _FALLBACK_TEMPLATES


_TEMPLATES: tuple[Template, ...] = _load_templates()
_TEMPLATE_INDEX: dict[str, Template] = {t.key: t for t in _TEMPLATES}


def all_templates() -> tuple[Template, ...]:
    """Every starter template, in catalogue order."""
    return _TEMPLATES


def resolve_template(key: str | None) -> Template | None:
    """Return the template for ``key``, or ``None`` if unknown."""
    return _TEMPLATE_INDEX.get(key or "")


__all__ = [
    "Template",
    "Theme",
    "all_templates",
    "all_themes",
    "resolve_template",
    "resolve_theme",
]
