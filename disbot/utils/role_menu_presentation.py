"""Theme presets + starter-message templates for role menus (plan §4.6 b/c).

Pure data on top of :mod:`utils.ui_constants` and the embed archetypes in
``docs/ux/pattern-library.md`` — no DB, no Discord I/O — so both the in-Discord
builder (PR 2) and, later, the web builder (Surface A) read the same catalogue.

* **Themes** (§4.6b) — a named accent-colour + footer catalogue surfaced as a
  one-tap picker in the builder. The chosen ``key`` is stored in
  ``role_menus.theme`` and re-applied on render/edit/restart.
* **Templates** (§4.6c) — ready-made starter messages (title + decorated
  description + a suggested theme/style) shown as a gallery so a good-looking
  menu is two taps away. The template only *pre-fills* the builder; the operator
  then tweaks the title/description that actually get stored.

Layer note: lives in ``utils/`` (may import stdlib + discord only) so any view
can import it without crossing a layer boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

import discord

from utils import ui_constants

# The key persisted when a menu has no explicit theme.
DEFAULT_THEME_KEY = "default"


@dataclass(frozen=True)
class MenuTheme:
    """A named accent-colour preset for a role-menu embed."""

    key: str
    label: str
    color: discord.Color
    footer: str | None = None


@dataclass(frozen=True)
class MenuTemplate:
    """A ready-made starter message an operator picks then tweaks."""

    key: str
    label: str  # gallery button text, e.g. "🎮 Game roles"
    title: str
    description: str
    theme: str = DEFAULT_THEME_KEY
    style: str = "dropdown"


# Ordered so the builder renders them deterministically.  Colours reference
# ui_constants where one fits, with explicit RGB for the decorative themes.
_THEMES: tuple[MenuTheme, ...] = (
    MenuTheme(
        "default",
        "Default",
        ui_constants.ROLE_COLOR,
        footer="Pick the roles you want — tap again to remove.",
    ),
    MenuTheme(
        "minimal",
        "Minimal",
        discord.Color.from_rgb(47, 49, 54),  # Discord dark — blends into the channel
    ),
    MenuTheme(
        "announcement",
        "Announcement",
        ui_constants.ECONOMY_COLOR,  # gold
        footer="React below to opt in.",
    ),
    MenuTheme(
        "neon",
        "Neon",
        discord.Color.from_rgb(255, 0, 200),
    ),
    MenuTheme(
        "pastel",
        "Pastel",
        discord.Color.from_rgb(181, 199, 255),
    ),
    MenuTheme(
        "game",
        "Game",
        ui_constants.GAME_COLOR,  # purple
        footer="Choose your squads.",
    ),
)

_THEME_BY_KEY: dict[str, MenuTheme] = {t.key: t for t in _THEMES}


_TEMPLATES: tuple[MenuTemplate, ...] = (
    MenuTemplate(
        "game_roles",
        "🎮 Game roles",
        title="🎮 Game Roles",
        description=(
            "Pick the games you play to get pinged for squads and find teammates.\n\n"
            "Use the menu below to add or remove your game roles."
        ),
        theme="game",
    ),
    MenuTemplate(
        "notification_roles",
        "🔔 Notification roles",
        title="🔔 Notification Roles",
        description=(
            "Choose which announcements you want to be pinged for.\n\n"
            "Only opt into what you care about — you can change this anytime."
        ),
        theme="announcement",
    ),
    MenuTemplate(
        "colour_roles",
        "🎨 Colour roles",
        title="🎨 Colour Roles",
        description=(
            "Give your name some colour! Pick **one** colour role below.\n\n"
            "Selecting a new colour replaces your current one."
        ),
        theme="pastel",
        # A colour menu is naturally single-choice — the builder pre-selects
        # unique mode when this template is chosen.
    ),
    MenuTemplate(
        "verify",
        "✅ Verify to enter",
        title="✅ Verify",
        description=(
            "Welcome! Tap below to verify you're human and unlock the rest of the "
            "server.\n\nThis only ever **adds** your member role."
        ),
        theme="minimal",
        style="button",
    ),
)

_TEMPLATE_BY_KEY: dict[str, MenuTemplate] = {t.key: t for t in _TEMPLATES}


def themes() -> tuple[MenuTheme, ...]:
    """Every theme preset, in display order."""
    return _THEMES


def get_theme(key: str | None) -> MenuTheme:
    """Return the theme for ``key``, falling back to the default preset."""
    if key and key in _THEME_BY_KEY:
        return _THEME_BY_KEY[key]
    return _THEME_BY_KEY[DEFAULT_THEME_KEY]


def theme_color(key: str | None) -> discord.Color:
    """Convenience: the accent colour for a theme key (default-safe)."""
    return get_theme(key).color


def templates() -> tuple[MenuTemplate, ...]:
    """Every starter-message template, in display order."""
    return _TEMPLATES


def get_template(key: str | None) -> MenuTemplate | None:
    """Return the template for ``key``, or ``None`` if unknown/absent."""
    if not key:
        return None
    return _TEMPLATE_BY_KEY.get(key)


__all__ = [
    "DEFAULT_THEME_KEY",
    "MenuTemplate",
    "MenuTheme",
    "get_template",
    "get_theme",
    "templates",
    "theme_color",
    "themes",
]
