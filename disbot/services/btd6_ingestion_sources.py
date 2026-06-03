"""Canonical parent-source policy for BTD6 ingestion.

Single source of truth for the parent sources the supervisor schedules
and that the admin panel's "Fetch All" iterates. Lives in its own
module so views/admin paths don't depend on supervisor internals.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParentSourceSpec:
    """One scheduled parent source and its base interval."""

    source_key: str
    interval_s: int


PARENT_SOURCES: tuple[ParentSourceSpec, ...] = (
    # Live rotations — refresh frequently so the bot sees the current
    # race / boss / odyssey / event within ~one cycle.
    ParentSourceSpec("nk_btd6_events", 1800),
    ParentSourceSpec("nk_btd6_races", 1800),
    ParentSourceSpec("nk_btd6_bosses", 1800),
    ParentSourceSpec("nk_btd6_odyssey", 1800),
    ParentSourceSpec("nk_btd6_ct", 1800),
    # Map / challenge directories rotate daily.
    ParentSourceSpec("nk_btd6_maps", 86400),
    ParentSourceSpec("nk_btd6_challenges", 86400),
    # Steam update / patch notes (no API key) — drops are infrequent, so
    # a 6h cadence catches a new version well within a day of release.
    ParentSourceSpec("steam_btd6_news", 21600),
)


def parent_source_keys() -> tuple[str, ...]:
    """Return parent source keys in scheduled order."""
    return tuple(spec.source_key for spec in PARENT_SOURCES)


def source_intervals() -> dict[str, int]:
    """Return ``{source_key: interval_s}`` for the supervisor loop."""
    return {spec.source_key: spec.interval_s for spec in PARENT_SOURCES}


__all__ = [
    "PARENT_SOURCES",
    "ParentSourceSpec",
    "parent_source_keys",
    "source_intervals",
]
