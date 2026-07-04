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
    """A ready-made starter message an operator picks then tweaks.

    ``mode`` / ``show_counts`` let a template pre-pick the assignment behaviour
    that fits its shape (e.g. the RSVP template is button + ``unique`` + counts),
    so the right config is one tap away — the operator can still change any of it.
    """

    key: str
    label: str  # gallery button text, e.g. "🎮 Game roles"
    title: str
    description: str
    theme: str = DEFAULT_THEME_KEY
    style: str = "dropdown"
    mode: str = "normal"
    show_counts: bool = False


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
        # A colour menu is naturally single-choice.
        mode="unique",
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
        mode="verify",
    ),
    MenuTemplate(
        "event_rsvp",
        "📣 Event RSVP",
        title="📣 Event RSVP",
        description=(
            "**Are you in?** Tap an option below — pick **one**, and you can "
            "change your mind anytime.\n\n"
            "The live count beside each option updates as people respond, so "
            "everyone can see who's coming at a glance."
        ),
        theme="announcement",
        # Buttons (one per option) + unique (one answer each) + the live counter:
        # a self-updating RSVP poll — pair with the 📣 Event RSVP role pack.
        style="button",
        mode="unique",
        show_counts=True,
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


# ---------------------------------------------------------------------------
# Gradient presets (Enhanced Role Styles) — one-tap styled colour roles
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CardTemplate:
    """A preset banner-card style for a role menu (plan §4.6d).

    ``style`` selects the renderer's background treatment
    (:data:`utils.role_menu_render.KNOWN_STYLES`); the chosen ``key`` is stored in
    ``role_menus.card_template`` and re-rendered at post/edit/restart. ``None`` (no
    card) is the default — a menu only gets a banner when an operator picks one.
    """

    key: str
    label: str  # gallery button text, e.g. "🎀 Banner"
    style: str  # the renderer style key


# Ordered for the builder's card-style picker. Every ``style`` here must be a
# member of ``role_menu_render.KNOWN_STYLES`` (pinned by a test).
_CARD_TEMPLATES: tuple[CardTemplate, ...] = (
    CardTemplate("banner", "🎀 Banner", "banner"),
    CardTemplate("gradient", "🌈 Gradient", "gradient"),
    CardTemplate("minimal", "▫️ Minimal", "minimal"),
    CardTemplate("spotlight", "🔦 Spotlight", "spotlight"),
)

_CARD_TEMPLATE_BY_KEY: dict[str, CardTemplate] = {t.key: t for t in _CARD_TEMPLATES}


def card_templates() -> tuple[CardTemplate, ...]:
    """Every banner-card preset, in picker order."""
    return _CARD_TEMPLATES


def get_card_template(key: str | None) -> CardTemplate | None:
    """Return the card template for ``key``, or ``None`` (no card / unknown)."""
    if not key:
        return None
    return _CARD_TEMPLATE_BY_KEY.get(key)


@dataclass(frozen=True)
class GradientPreset:
    """A ready-made two-colour gradient an operator applies as a styled role.

    ``primary`` / ``secondary`` are ``0xRRGGBB`` ints (→ :class:`discord.Color`).
    Only renders on guilds with the Enhanced Role Styles perk (3 applied boosts);
    the builder gates on it and falls back to the primary solid colour otherwise.
    """

    key: str
    label: str  # gallery text, e.g. "🌅 Sunset"
    name: str  # the created role's name, e.g. "Sunset"
    primary: int
    secondary: int


# Ordered for the builder gallery. Colours chosen to read well as Discord role
# names (decent contrast against both light and dark themes).
_GRADIENT_PRESETS: tuple[GradientPreset, ...] = (
    GradientPreset("sunset", "🌅 Sunset", "Sunset", 0xFF7E5F, 0xFEB47B),
    GradientPreset("ocean", "🌊 Ocean", "Ocean", 0x2193B0, 0x6DD5ED),
    GradientPreset("berry", "🍇 Berry", "Berry", 0x8E2DE2, 0x4A00E0),
    GradientPreset("forest", "🌲 Forest", "Forest", 0x11998E, 0x38EF7D),
    GradientPreset("fire", "🔥 Fire", "Fire", 0xF12711, 0xF5AF19),
    GradientPreset("candy", "🍬 Candy", "Candy", 0xFF6FD8, 0x3813C2),
)


def gradient_presets() -> tuple[GradientPreset, ...]:
    """Every gradient preset, in gallery order."""
    return _GRADIENT_PRESETS


__all__ = [
    "DEFAULT_THEME_KEY",
    "GradientPreset",
    "MenuTemplate",
    "MenuTheme",
    "get_template",
    "get_theme",
    "gradient_presets",
    "templates",
    "theme_color",
    "themes",
]
