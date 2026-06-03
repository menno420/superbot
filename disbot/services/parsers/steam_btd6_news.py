"""Steam news → BTD6 patch-notes parser.

Unlike the ``ninjakiwi_*`` parsers, this source is **not** a Ninja Kiwi
API endpoint and does **not** use the NK envelope (``_envelope.unwrap``).
It consumes the public Steam Web API ``ISteamNews/GetNewsForApp`` feed
for BTD6 (Steam appid ``960090``), which requires **no API key**::

    https://api.steampowered.com/ISteamNews/GetNewsForApp/v0002/
        ?appid=960090&count=20&maxlength=0&format=json

The response shape is::

    {"appnews": {"appid": 960090, "count": N,
                 "newsitems": [{"gid", "title", "url", "is_external_url",
                                "author", "contents", "feedlabel", "date",
                                "feedname", "feed_type", "appid"}, ...]}}

This parser is registered for the ``steam_btd6_news`` source_key, whose
``source_kind`` is ``patch_notes``. The ingestion service routes
``patch_notes`` sources to :func:`services.btd6_patch_service.store_parsed_notes`
(the ``btd6_patch_notes`` table that ``btd6_knowledge_api.get_patch_notes``
already reads) rather than the generic fact store — so each dict this
parser returns is a *patch-note record*, not a fact row::

    {"version": "54.0", "body": "...", "published_at": datetime|None,
     "title": "Bloons TD 6 - Update 54.0", "url": "https://..."}

Selection policy (intentionally strict — this feeds the bot's knowledge):

* Only items from the official developer feed
  (``feedname == "steam_community_announcements"``) are considered;
  external press articles are ignored.
* The title must mention an update ("update"/"version", case-insensitive)
  **and** carry an ``X.Y`` version number. This skips non-patch
  announcements ("Social Seasons Is Live!", "Limited Edition Plushies!").
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from services import btd6_source_parser
from services.parsers._envelope import ParserAdapter

logger = logging.getLogger("bot.services.parsers.steam_btd6_news")

_SOURCE = "steam_btd6_news"

# Only the official developer announcement feed carries Ninja Kiwi's
# patch notes; external-press feeds (is_external_url) are ignored.
_OFFICIAL_FEEDNAME = "steam_community_announcements"

# A patch-note title both names an update and carries an ``X.Y`` version.
_UPDATE_KEYWORDS = ("update", "version", "patch notes")
_VERSION_RE = re.compile(r"\b[vV]?(\d+\.\d+)\b")

# Steam ``contents`` is BBCode ([h2]…[/h2], [list][*]…, [url=…]…[/url]).
# Strip the tags for a clean prose body; the bracketed inner text stays.
_BBCODE_TAG_RE = re.compile(r"\[/?[^\]]+\]")
_MULTI_BLANK_RE = re.compile(r"\n{3,}")

# Sanity bound so a pathological news item can't write a multi-MB row.
# Full BTD6 patch notes comfortably fit; this only guards the tail.
_MAX_BODY_CHARS = 16000


def _clean_body(contents: str) -> str:
    """Strip Steam BBCode tags and collapse runaway blank lines."""
    stripped = _BBCODE_TAG_RE.sub("", contents)
    stripped = _MULTI_BLANK_RE.sub("\n\n", stripped)
    stripped = stripped.strip()
    if len(stripped) > _MAX_BODY_CHARS:
        stripped = stripped[:_MAX_BODY_CHARS].rstrip() + "\n\n[truncated]"
    return stripped


def _is_patch_title(title: str) -> bool:
    lowered = title.lower()
    return any(keyword in lowered for keyword in _UPDATE_KEYWORDS)


def _published_at(raw_date: Any) -> datetime | None:
    """Convert a Steam unix ``date`` (epoch seconds) to an aware datetime."""
    try:
        return datetime.fromtimestamp(int(raw_date), tz=timezone.utc)
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def parse_steam_news(
    payload: Any,
    *,
    game_version: str | None = None,  # noqa: ARG001 — version derives from title
    path_params: dict[str, str] | None = None,  # noqa: ARG001 — no path params
) -> list[dict[str, Any]]:
    """Parse a Steam ``GetNewsForApp`` payload into patch-note records.

    Returns one record per official update announcement that carries an
    ``X.Y`` version. Non-update announcements and external-press items
    are skipped. The newest item per version wins implicitly downstream
    (``upsert_patch_note`` is ``ON CONFLICT (version) DO UPDATE``).
    """
    if not isinstance(payload, dict):
        return []
    appnews = payload.get("appnews")
    if not isinstance(appnews, dict):
        return []
    items = appnews.get("newsitems")
    if not isinstance(items, list):
        return []

    records: list[dict[str, Any]] = []
    seen_versions: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("feedname") != _OFFICIAL_FEEDNAME:
            continue
        title = str(item.get("title") or "").strip()
        if not title or not _is_patch_title(title):
            continue
        match = _VERSION_RE.search(title)
        if match is None:
            continue
        version = match.group(1)
        # newsitems is newest-first; the first hit for a version is the
        # canonical one. Skip later (older) duplicates within one payload.
        if version in seen_versions:
            continue
        body = _clean_body(str(item.get("contents") or ""))
        if not body:
            continue
        seen_versions.add(version)
        records.append(
            {
                "version": version,
                "body": body,
                "published_at": _published_at(item.get("date")),
                "title": title,
                "url": item.get("url"),
            },
        )
    return records


btd6_source_parser.register(ParserAdapter(_SOURCE, parse_steam_news))


__all__ = ["parse_steam_news"]
