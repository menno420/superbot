"""Guild Help-overlay read model (HLP-3 — the presentation-deviation store).

The cached, fault-tolerant read side of the guild Help overlay
(migration 064): which hubs/subsystems this guild display-hides, renames,
or re-describes **in Help only**. The Help projection composes this with
governance — overlay rows can only affect presentation states
(``display_hidden`` / labels), never execution (Q-0055 / HLP-4).

* Reads are cached per guild; :func:`invalidate_help_overlay_cache` is
  called by the audited mutation seam (:mod:`services.help_overlay_mutation`)
  after every write — the audit §9 "per-guild Help-overlay generation/cache"
  requirement.
* A DB fault degrades to the **empty overlay** (registry defaults render)
  and is logged — Help must never crash on the overlay path.
* Orphan rows (keys the catalogue no longer knows) are **preserved and
  reported**, never dropped here: the projection surfaces them as
  ``orphaned_override`` decisions for operator surfaces.

Cycle discipline (mirrors :mod:`services.help_projection`): cross-package
imports are function-local; top-level imports are stdlib only.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("bot.services.help_overlay")

VALID_ENTITY_KINDS: frozenset[str] = frozenset({"hub", "subsystem"})

# Bounds mirror the tightest Discord surface rendering these fields (select
# option label/description = 100 chars); the DB CHECKs are the backstop.
MAX_DISPLAY_NAME_LEN = 100
MAX_DESCRIPTION_LEN = 100

# Q-0059 Home-message bounds (migration 067): embed-title cap / a bounded
# body well under the 4096 description cap / Discord's 24-bit color space.
MAX_HOME_TITLE_LEN = 256
MAX_HOME_BODY_LEN = 2000
MAX_HOME_COLOR = 0xFFFFFF

# The default Home frame (what renders when no home row exists). Owned here
# so the live render path and the builder's mandatory preview compose the
# exact same embed frame from one source.
DEFAULT_HOME_TITLE = "📚 Help Menu"
DEFAULT_HOME_BODY = "Pick a category from the dropdown below."


@dataclass(frozen=True)
class HomeMessage:
    """The guild's Q-0059 Help-Home customization (``None`` field = default)."""

    title: str | None = None
    body: str | None = None
    color: int | None = None

    @property
    def is_noop(self) -> bool:
        return self.title is None and self.body is None and self.color is None


def home_embed_frame(
    home: HomeMessage | None,
    *,
    default_color: int,
) -> tuple[str, str, int]:
    """``(title, description, color)`` for the Help Home embed.

    The one frame both the live Home render and the builder's preview use
    (preview-is-exact rule). Stored text is mention-suppressed here —
    embeds never ping, but suppression keeps copied/quoted text safe too.
    """
    import discord.utils as _dutils

    if home is None:
        return DEFAULT_HOME_TITLE, DEFAULT_HOME_BODY, default_color
    title = (
        _dutils.escape_mentions(home.title)
        if home.title is not None
        else DEFAULT_HOME_TITLE
    )
    body = (
        _dutils.escape_mentions(home.body)
        if home.body is not None
        else DEFAULT_HOME_BODY
    )
    color = home.color if home.color is not None else default_color
    return title, body, color


@dataclass(frozen=True)
class HelpOverlayRow:
    """One entity's presentation deviations (``None`` field = inherit)."""

    entity_kind: str  # 'hub' | 'subsystem'
    entity_key: str
    display_hidden: bool | None = None
    display_name: str | None = None
    description: str | None = None

    @property
    def is_noop(self) -> bool:
        """``True`` when every override field inherits (row should not exist)."""
        return (
            self.display_hidden is None
            and self.display_name is None
            and self.description is None
        )


@dataclass(frozen=True)
class GuildHelpOverlay:
    """All of one guild's Help presentation deviations (possibly empty).

    ``home`` is the Q-0059 Home-message customization (migration 067) —
    ``None`` renders the byte-identical default Home frame.
    """

    guild_id: int | None
    rows: tuple[HelpOverlayRow, ...] = field(default=())
    home: HomeMessage | None = None

    def get(self, entity_kind: str, entity_key: str) -> HelpOverlayRow | None:
        return next(
            (
                r
                for r in self.rows
                if r.entity_kind == entity_kind and r.entity_key == entity_key
            ),
            None,
        )

    @property
    def is_empty(self) -> bool:
        return not self.rows


EMPTY_OVERLAY = GuildHelpOverlay(guild_id=None)

# ---------------------------------------------------------------------------
# Cached read
# ---------------------------------------------------------------------------

_cache: dict[int, GuildHelpOverlay] = {}


async def get_guild_help_overlay(guild_id: int | None) -> GuildHelpOverlay:
    """The guild's overlay (cached; empty for DMs / faults / no rows)."""
    if guild_id is None:
        return EMPTY_OVERLAY
    cached = _cache.get(guild_id)
    if cached is not None:
        return cached
    from utils.db import help_overlay as db

    try:
        raw = await db.get_guild_rows(guild_id)
        home_raw = await db.get_home_row(guild_id)
    except Exception as exc:  # noqa: BLE001 — Help must render without the overlay
        logger.warning(
            "help_overlay: read failed for guild %s — rendering defaults: %s",
            guild_id,
            exc,
        )
        return GuildHelpOverlay(guild_id=guild_id)
    overlay = GuildHelpOverlay(
        guild_id=guild_id,
        rows=tuple(
            HelpOverlayRow(
                entity_kind=r["entity_kind"],
                entity_key=r["entity_key"],
                display_hidden=r["display_hidden"],
                display_name=r["display_name"],
                description=r["description"],
            )
            for r in raw
        ),
        home=(
            HomeMessage(
                title=home_raw["home_title"],
                body=home_raw["home_body"],
                color=home_raw["home_color"],
            )
            if home_raw is not None
            else None
        ),
    )
    _cache[guild_id] = overlay
    return overlay


def invalidate_help_overlay_cache(guild_id: int | None = None) -> None:
    """Drop the cached overlay for ``guild_id`` (or all, when ``None``)."""
    if guild_id is None:
        _cache.clear()
    else:
        _cache.pop(guild_id, None)


__all__ = [
    "DEFAULT_HOME_BODY",
    "DEFAULT_HOME_TITLE",
    "EMPTY_OVERLAY",
    "MAX_DESCRIPTION_LEN",
    "MAX_DISPLAY_NAME_LEN",
    "MAX_HOME_BODY_LEN",
    "MAX_HOME_COLOR",
    "MAX_HOME_TITLE_LEN",
    "VALID_ENTITY_KINDS",
    "GuildHelpOverlay",
    "HelpOverlayRow",
    "HomeMessage",
    "get_guild_help_overlay",
    "home_embed_frame",
    "invalidate_help_overlay_cache",
]
