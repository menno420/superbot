"""Cache cadence contract for BTD6 sources (M3A seam).

BTD6 owns its cadence — not AI policy. M3A ships the contract; M3B
wires real polling using ``services.btd6_fetch_service``.

Cadence ownership:

* ``maps`` and other long-stable endpoints → daily.
* ``races`` / ``bosses`` / ``odyssey`` → hourly.
* ``challenges`` → spot-poll on demand.

Per-source overrides live in
``btd6_source_registry.cache_policy_key``. Settings tuning lands in
``utils/settings_keys/btd6_cache.py`` (created in M3B alongside the
real cadence loop). M3A keeps the surface inert.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger("bot.services.btd6_cache")


_DEFAULT_CADENCES_SECONDS: dict[str, int] = {
    "nk_btd6_maps": 24 * 3600,
    "nk_btd6_maps_filter": 24 * 3600,
    "nk_btd6_maps_one": 24 * 3600,
    "nk_btd6_races": 3600,
    "nk_btd6_races_metadata": 3600,
    "nk_btd6_races_leaderboard": 3600,
    "nk_btd6_bosses": 3600,
    "nk_btd6_bosses_metadata": 3600,
    "nk_btd6_bosses_leaderboard": 3600,
    "nk_btd6_odyssey": 3600,
    "nk_btd6_odyssey_diff": 3600,
    "nk_btd6_odyssey_diff_maps": 3600,
    "nk_btd6_events": 3600,
    "nk_btd6_challenges": 0,  # spot-poll on demand
    "nk_btd6_challenges_filter": 0,
    "nk_btd6_challenges_one": 0,
}


@dataclass(frozen=True)
class CadenceEntry:
    source_key: str
    interval_seconds: int  # 0 = on-demand only


def cadence_for(source_key: str) -> CadenceEntry:
    """Return the configured cadence for ``source_key``.

    M3A returns the static default; M3B reads
    ``btd6_source_registry.cache_policy_key`` and the BTD6 settings
    surface to allow overrides.
    """
    return CadenceEntry(
        source_key=source_key,
        interval_seconds=int(_DEFAULT_CADENCES_SECONDS.get(source_key, 0)),
    )


def default_cadences() -> dict[str, CadenceEntry]:
    return {
        key: CadenceEntry(source_key=key, interval_seconds=int(seconds))
        for key, seconds in _DEFAULT_CADENCES_SECONDS.items()
    }


__all__ = ["CadenceEntry", "cadence_for", "default_cadences"]
