"""Render the current Contested Territory map as a PNG for Discord.

Bridges the live tile data (``services.btd6_live_query_service``) and the
pure hex renderer (``utils.btd6.ct_map_render``): it classifies each tile
into a colour bucket and a short relic label, then returns a
``discord.File`` ready to attach. Returns ``None`` when Pillow is absent
or no CT tile data is loaded, so callers degrade to the text browser.
"""

from __future__ import annotations

import io
import logging

import discord

from utils.btd6.ct_map_render import MapTile, render_ct_map

logger = logging.getLogger("bot.views.btd6.ct_map")

_MAP_FILENAME = "ct_map.png"


def _tile_kind(placement: object) -> str:
    if getattr(placement, "relic_name", None):
        return "relic"
    tile_type = (getattr(placement, "tile_type", None) or "").lower()
    if tile_type == "relic":
        return "relic"
    if "banner" in tile_type:
        return "banner"
    if "team" in tile_type:
        return "team"
    if "regular" in tile_type:
        return "regular"
    return "unknown"


def _relic_label(placement: object) -> str:
    """A ≤4-char tag for a relic tile (abbreviation, else initials)."""
    relic_id = getattr(placement, "relic_id", None)
    if relic_id:
        from services import btd6_data_service

        entry = btd6_data_service.get_ct_relic(relic_id)
        if entry is not None and entry.abbrev:
            return entry.abbrev[:4]
    name = getattr(placement, "relic_canonical", None) or getattr(
        placement,
        "relic_name",
        "",
    )
    words = [w for w in str(name).replace("-", " ").split() if w]
    if len(words) >= 2:
        return "".join(w[0] for w in words[:4]).upper()
    return str(name)[:3].upper()


def _placement_to_tile(placement: object) -> MapTile | None:
    pos = getattr(placement, "position", None)
    if pos is None:
        return None
    kind = _tile_kind(placement)
    label = _relic_label(placement) if kind == "relic" else ""
    return MapTile(
        q=pos.axial[0],
        r=pos.axial[1],
        kind=kind,
        label=label,
        is_center=bool(getattr(pos, "is_center", False)),
    )


async def build_ct_map_file(
    ct_id: str | None = None,
) -> tuple[discord.File | None, str | None]:
    """Render the newest active CT (or ``ct_id``) to a ``discord.File``.

    Returns ``(file, event_id)``. ``file`` is ``None`` when Pillow is
    unavailable, no CT event is active, or the tile data isn't loaded;
    ``event_id`` is still returned (when known) so the caller can word a
    fallback message.
    """
    from services import btd6_live_query_service as btd6_live

    try:
        if ct_id is None:
            events = await btd6_live.get_active_events(("btd6_ct",))
            if not events:
                return None, None
            ct_id = events[0].entity_key
        placements = await btd6_live.get_ct_tiles(ct_id)
    except Exception:  # noqa: BLE001 — degrade to text browser
        logger.exception("ct map: live tile fetch failed for %s", ct_id)
        return None, ct_id

    tiles = [t for t in (_placement_to_tile(p) for p in placements) if t is not None]
    # ASCII hyphen: the default Pillow bitmap font has no em-dash glyph.
    png = render_ct_map(tiles, title=f"Contested Territory - {ct_id}")
    if png is None:
        return None, ct_id
    return discord.File(io.BytesIO(png), filename=_MAP_FILENAME), ct_id


__all__ = ["build_ct_map_file"]
