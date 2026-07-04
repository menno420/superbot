"""Pure parsing for bot-to-bot XP/level migration.

SuperBot can adopt the chat levels a server already earned under another
leveling bot.  The live case is **Arcane**, whose level-up channel posts one
message per level-up:

    @Nicely has reached level 3. GG!

Arcane exposes **no** import/export API (their API access is restricted; the
only exits are a browser scrape of the web leaderboard or a manual export via
their support), so scanning that announcement channel is the primary
mechanism — exactly the fallback the owner asked for.  This module is the
Discord-free core: it turns raw announcement text (+ the message's mention
ids) into ``(user, level)`` records and reduces them to the highest level seen
per user.  The Discord I/O (reading channel history, resolving names to
members) lives in the cog; the audited write lives in ``services.xp_service``.

**Extensible by announcer, not just Arcane.** ``FORMATS`` keys a regex per
known leveling bot (Arcane / MEE6 / SuperBot / a permissive generic), so the
same scan adopts a server that switched announcers.  A future *direct* provider
(e.g. MEE6's public leaderboard API) produces the same ``(user_id, level)``
records and feeds the identical import path — this module is only the
channel-scan source.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from re import Pattern


@dataclass(frozen=True)
class AnnouncerFormat:
    """A known leveling bot's level-up announcement shape.

    ``level_re`` must expose the reached level as group 1.  ``name_re`` (group
    1 = the display name) is the *fallback* used only when the message carried
    no user mention — Arcane pings the member, so the mention path is the
    reliable one and the name path exists for announcers that post plain text.
    """

    key: str
    label: str
    level_re: Pattern[str]
    name_re: Pattern[str] | None


# Optional bold markers (``**``) surround the number/level in most announcers'
# markdown; tolerate 0–2 asterisks and arbitrary spacing everywhere.
_B = r"\*{0,2}"

FORMATS: dict[str, AnnouncerFormat] = {
    "arcane": AnnouncerFormat(
        key="arcane",
        label="Arcane",
        # "@User has reached level **3**. GG!"
        level_re=re.compile(rf"reached\s+level\s+{_B}(\d+)", re.IGNORECASE),
        name_re=re.compile(r"^\s*@?(.+?)\s+has\s+reached\s+level", re.IGNORECASE),
    ),
    "mee6": AnnouncerFormat(
        key="mee6",
        label="MEE6",
        # "GG @User, you just advanced to level **3**!"
        level_re=re.compile(
            rf"(?:advanced\s+to|reached)\s+{_B}level\s+{_B}(\d+)",
            re.IGNORECASE,
        ),
        name_re=re.compile(
            r"(?:GG\s+)?@?([^,]+?),\s+you\s+just\s+advanced",
            re.IGNORECASE,
        ),
    ),
    "superbot": AnnouncerFormat(
        key="superbot",
        label="SuperBot",
        # SuperBot's own announce embed: "@User reached **Level 3**!"
        level_re=re.compile(rf"reached\s+{_B}level\s+{_B}(\d+)", re.IGNORECASE),
        name_re=None,
    ),
    "generic": AnnouncerFormat(
        key="generic",
        label="Generic (any “level N”)",
        # Permissive: any "... level 3 ..." — use when the announcer is unknown.
        level_re=re.compile(rf"\blevel\s+{_B}(\d+)", re.IGNORECASE),
        name_re=None,
    ),
}

DEFAULT_FORMAT = "arcane"


def get_format(key: str | None) -> AnnouncerFormat | None:
    """Return the :class:`AnnouncerFormat` for ``key`` (case-insensitive)."""
    if key is None:
        return None
    return FORMATS.get(key.strip().lower())


def format_keys() -> list[str]:
    """The known announcer keys, in a stable display order."""
    return list(FORMATS.keys())


@dataclass(frozen=True)
class ParsedLevelUp:
    """One parsed level-up announcement.

    Exactly one of ``user_id`` / ``name`` identifies the subject: ``user_id``
    when the announcement mentioned the member (the reliable path), otherwise
    ``name`` for the cog to resolve against the guild roster.  Both ``None``
    means the level was found but the subject could not be identified.
    """

    level: int
    user_id: int | None = None
    name: str | None = None


def parse_level_message(
    content: str,
    mention_ids: Iterable[int] = (),
    *,
    fmt: AnnouncerFormat,
) -> ParsedLevelUp | None:
    """Parse one announcement into a :class:`ParsedLevelUp`, or ``None``.

    Returns ``None`` when ``content`` carries no level for ``fmt`` (e.g. a
    human's chatter in the channel, or a different bot's message).  The subject
    is the **first** mention id when present (the leveler is named at the start
    of every known format); otherwise the name-fallback regex is tried.
    """
    if not content:
        return None
    m = fmt.level_re.search(content)
    if m is None:
        return None
    level = int(m.group(1))

    for mid in mention_ids:
        return ParsedLevelUp(level=level, user_id=int(mid))

    if fmt.name_re is not None:
        nm = fmt.name_re.search(content)
        if nm is not None:
            name = nm.group(1).strip().strip("*").strip()
            if name:
                return ParsedLevelUp(level=level, name=name)

    return ParsedLevelUp(level=level)


@dataclass(frozen=True)
class ScanPlan:
    """A previewed, resolved channel scan — everything the confirm panel and
    the import service need, with no Discord objects retained.

    ``records`` is the resolved, max-reduced ``(user_id, level)`` set ready for
    :func:`services.xp_migration.import_levels`.  The rest is preview metadata:
    ``sample`` is a display slice ``(display_name, level)`` sorted for the
    embed, and ``unresolved_names`` are plain-text names from mention-less
    announcements that matched no current member.
    """

    source_key: str
    source_label: str
    channel_id: int
    scanned_messages: int
    matched: int
    records: tuple[tuple[int, int], ...]
    sample: tuple[tuple[str, int], ...] = ()
    unresolved_names: tuple[str, ...] = ()

    @property
    def user_count(self) -> int:
        return len(self.records)


def reduce_max_levels(records: Iterable[tuple[int, int]]) -> dict[int, int]:
    """Collapse ``(user_id, level)`` pairs to the highest level per user.

    A member levels up many times, so the channel holds many rows per user;
    the migration cares only about the peak each user reached.
    """
    best: dict[int, int] = {}
    for user_id, level in records:
        if level > best.get(user_id, -1):
            best[user_id] = level
    return best
