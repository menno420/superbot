"""Per-guild Contested Territory team (bracket) configuration.

A server pastes its CT *bracket / group id* — the token Ninja Kiwi puts in
each team's ``/btd6/ct/<ctID>/leaderboard/group/<groupID>`` URL — so the bot
can show that team's live CT standing. This service owns the read/write of the
``BTD6_CT_GROUP_ID`` setting (so no raw key string appears elsewhere) and the
parsing of a pasted id-or-URL into the bare group id.

Consumers: the ``btd6_ct_team_status`` AI tool and the ``!btd6 ctteam``
command. The live standings come from :func:`get_ct_bracket`, which fetches
the bracket on demand (Ninja Kiwi only exposes it per event).
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from utils import db
from utils.settings_keys import BTD6_CT_GROUP_ID

logger = logging.getLogger("bot.services.btd6_ct_team")

# A Ninja Kiwi group id is a hex token (the live example is 42 chars). Accept a
# bare id or the tail of a full ``.../group/<id>`` URL; reject anything that is
# not a plausible hex token so a mis-paste fails loudly instead of being
# fetched as a bad path param.
_GROUP_ID_RE = re.compile(r"[0-9a-fA-F]{8,64}")
_GROUP_URL_MARKER = "/group/"


def parse_group_id(raw: str) -> str | None:
    """Extract a bare group id from a pasted id or full group URL.

    Returns the lower-cased hex id, or ``None`` when ``raw`` carries no
    plausible group token.
    """
    text = (raw or "").strip()
    if not text:
        return None
    # Full URL: take the segment after ``/group/``.
    if _GROUP_URL_MARKER in text:
        text = text.split(_GROUP_URL_MARKER, 1)[1]
    text = text.split("?", 1)[0].split("#", 1)[0].strip().strip("/")
    match = _GROUP_ID_RE.fullmatch(text)
    return match.group(0).lower() if match else None


async def get_team_group_id(guild_id: int) -> str:
    """The configured CT bracket id for ``guild_id`` (``""`` when unset)."""
    return await db.get_setting(guild_id, BTD6_CT_GROUP_ID, "")


async def set_team_group_id(guild_id: int, raw: str) -> str | None:
    """Parse ``raw`` and persist it as the guild's CT bracket id.

    Returns the stored id, or ``None`` when ``raw`` is not a valid group id /
    URL (in which case nothing is written).
    """
    gid = parse_group_id(raw)
    if gid is None:
        return None
    await db.set_setting(guild_id, BTD6_CT_GROUP_ID, gid)
    return gid


async def clear_team_group_id(guild_id: int) -> None:
    """Forget the guild's configured CT bracket id."""
    await db.set_setting(guild_id, BTD6_CT_GROUP_ID, "")


# ---------------------------------------------------------------------------
# Live bracket standings (on-demand fetch of the per-event "group" endpoint)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CTBracketRow:
    """One team in a CT bracket, with its live score and computed rank."""

    rank: int
    display_name: str
    score: int


@dataclass(frozen=True)
class CTBracketResult:
    """A team's CT bracket standings for the active event.

    ``rows`` is the bracket sorted by score (rank 1 = leader). ``ct_id`` is the
    active event the bracket was fetched for. ``stale`` is True when the
    configured group id returned no teams for the active event — almost always
    a bracket id from a previous (ended) event, since Ninja Kiwi mints a new
    group id per event.
    """

    ct_id: str | None
    rows: tuple[CTBracketRow, ...]
    stale: bool


def _parse_bracket_rows(payload: Any) -> list[tuple[str, int]]:
    """Extract ``(display_name, score)`` pairs from a CT group response body."""
    body = payload.get("body") if isinstance(payload, dict) else payload
    out: list[tuple[str, int]] = []
    if not isinstance(body, list):
        return out
    for entry in body:
        if not isinstance(entry, dict):
            continue
        name = entry.get("displayName")
        score = entry.get("score")
        if isinstance(name, str) and name and isinstance(score, (int, float)):
            out.append((name.strip(), int(score)))
    return out


async def get_ct_bracket(group_id: str) -> CTBracketResult:
    """Live CT bracket standings for ``group_id`` in the newest active event.

    Ninja Kiwi only exposes a bracket per event, so this fetches
    ``/btd6/ct/<active>/leaderboard/group/<group_id>`` on demand, ranks the
    teams by score, and flags ``stale`` when the id yields no teams (it belongs
    to a past event and must be re-pasted). Returns an empty, non-stale result
    with ``ct_id=None`` when no CT event is active or the fetch is refused.
    """
    gid = (group_id or "").strip()
    if not gid:
        return CTBracketResult(ct_id=None, rows=(), stale=False)

    from services import btd6_fetch_service, btd6_live_query_service

    events = await btd6_live_query_service.get_active_events(("btd6_ct",))
    if not events:
        return CTBracketResult(ct_id=None, rows=(), stale=False)
    ct_id = events[0].entity_key

    try:
        result = await btd6_fetch_service.fetch(
            "nk_btd6_ct_lb_group",
            path_params={"ctID": ct_id, "groupID": gid},
        )
        payload = json.loads(result.raw_body)
    except (
        btd6_fetch_service.BTD6FetchRefusedError,
        btd6_fetch_service.BTD6FetchHTTPError,
    ):
        logger.warning("ct bracket fetch refused/failed for group=%s", gid)
        return CTBracketResult(ct_id=ct_id, rows=(), stale=False)
    except Exception:  # noqa: BLE001 — never raise into the caller
        logger.exception("ct bracket fetch errored for group=%s", gid)
        return CTBracketResult(ct_id=ct_id, rows=(), stale=False)

    pairs = _parse_bracket_rows(payload)
    if not pairs:
        # The endpoint answered but the bracket is empty — a past-event id.
        return CTBracketResult(ct_id=ct_id, rows=(), stale=True)
    pairs.sort(key=lambda p: p[1], reverse=True)
    rows = tuple(
        CTBracketRow(rank=i + 1, display_name=name, score=score)
        for i, (name, score) in enumerate(pairs)
    )
    return CTBracketResult(ct_id=ct_id, rows=rows, stale=False)


__all__ = [
    "CTBracketResult",
    "CTBracketRow",
    "clear_team_group_id",
    "get_ct_bracket",
    "get_team_group_id",
    "parse_group_id",
    "set_team_group_id",
]
