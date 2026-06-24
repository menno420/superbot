"""Provider registry for ``!rank`` and ``!leaderboard`` (PR G).

Centralises the per-category ranking logic that previously lived as
inline branches in :mod:`cogs.leaderboard_cog._build_embed` and
:mod:`cogs.xp._helpers._build_rank_embed`. Each provider declares:

* ``name`` — canonical identifier ("xp", "coins", "mining", …).
* ``display_title`` / ``select_label`` / ``select_emoji`` — UI strings.
* ``empty_hint`` — operator-friendly empty-state line.
* :meth:`top` — async, returns up to 10 :class:`RankEntry` rows.
* :meth:`member_rank` — async, returns ``(rank, rendered_value)`` for
  one user, or ``(None, None)`` when the user is not on the board.

The registry is read via :func:`get_provider` (alias-aware) and
:func:`provider_names`. ``leaderboard_cog`` and ``xp_cog`` are the
two consumers; new categories are added by registering a provider
here, not by editing either cog.

Identity / aliases match the historical
:data:`cogs.leaderboard_cog.ALIASES_MAP` so existing prefix
shortcuts (``!minelb``, ``!dm_lb``, ``!rpslb``, ``!countlb``, etc.)
continue to resolve to the same provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import discord

from core.runtime import resources
from utils import db
from utils.creatures import creature_names


@dataclass(frozen=True)
class RankEntry:
    """One row in a ranked top-N response.

    ``label`` is the fully-rendered text that follows the rank/medal
    prefix — e.g. ``"**Alice** — Level 5 (250 XP)"``. Providers own
    their own formatting so the registry doesn't need a per-category
    schema.

    ``name`` / ``score`` / ``value_text`` are the *structured* projection
    of the same row, consumed by the leaderboard **image card**
    (``render_leaderboard_image``): the plain display name (no markdown),
    the numeric primary statistic that drives the bar width, and the short
    value text drawn at the bar's end (e.g. ``"250 XP"`` / ``"5W / 2L"``).
    They default to ``None`` so every existing consumer (the embeds, which
    render from ``label``) is unaffected; a provider opts a category into
    the image card by populating all three.
    """

    label: str
    name: str | None = None
    score: float | None = None
    value_text: str | None = None


class RankProvider(ABC):
    """Abstract base for a leaderboard category.

    Subclasses must define the class-level metadata attributes
    (``name``, ``display_title``, ``select_label``, ``select_emoji``,
    ``empty_hint``) and implement :meth:`top` + :meth:`member_rank`.
    """

    name: str
    display_title: str
    select_label: str
    select_emoji: str | None
    empty_hint: str
    # The card_render skin the leaderboard image card renders in. A safe
    # default ("midnight"); get_theme() falls back to the default skin on an
    # unknown key, so an override can never take a render down. Overridden
    # per category for at-a-glance visual distinction (zero new art — the
    # engine's "a new look = a few RGB tuples" property, in practice).
    card_theme: str = "midnight"

    @abstractmethod
    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        """Return up to 10 ranked rows, sorted highest-first."""

    @abstractmethod
    async def member_rank(
        self,
        guild: discord.Guild,
        user_id: int,
    ) -> tuple[int | None, str | None]:
        """Return ``(rank, rendered_value)`` for ``user_id``.

        ``rank`` is the 1-based position in the full ordering or
        ``None`` if the user has no entry on this board. ``rendered_value``
        is the provider-formatted statistic (e.g. ``"250 XP"``) or
        ``None`` matching ``rank=None``.
        """


# ---------------------------------------------------------------------------
# Concrete providers
# ---------------------------------------------------------------------------


class XpProvider(RankProvider):
    name = "xp"
    display_title = "🏆 XP Leaderboard"
    select_label = "XP"
    select_emoji = "🏆"
    empty_hint = "No XP earned yet. Chat in this server to start ranking up."

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        rows = await db.fetchall(
            "SELECT user_id, xp, level FROM xp WHERE guild_id=$1 "
            "ORDER BY xp DESC LIMIT 10",
            (guild.id,),
        )
        entries: list[RankEntry] = []
        for row in rows:
            name = resources.member_display(guild, row["user_id"])
            entries.append(
                RankEntry(
                    label=f"**{name}** — Level {row['level']} ({row['xp']} XP)",
                    name=name,
                    score=float(row["xp"]),
                    value_text=f"{row['xp']:,} XP",
                ),
            )
        return entries

    async def member_rank(
        self,
        guild: discord.Guild,
        user_id: int,
    ) -> tuple[int | None, str | None]:
        all_xp = await db.fetchall(
            "SELECT user_id, xp, level FROM xp WHERE guild_id=$1 ORDER BY xp DESC",
            (guild.id,),
        )
        for i, row in enumerate(all_xp):
            if row["user_id"] == user_id:
                return i + 1, f"Level {row['level']} ({row['xp']} XP)"
        return None, None


class CoinsProvider(RankProvider):
    name = "coins"
    display_title = "🪙 Coin Leaderboard"
    select_label = "Coins"
    select_emoji = "🪙"
    empty_hint = (
        "No coin totals yet. Use `!daily` once per day or `!work` to start earning."
    )

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        rows = await db.fetchall(
            "SELECT user_id, coins FROM xp WHERE guild_id=$1 "
            "ORDER BY coins DESC LIMIT 10",
            (guild.id,),
        )
        entries: list[RankEntry] = []
        for row in rows:
            name = resources.member_display(guild, row["user_id"])
            entries.append(
                RankEntry(
                    label=f"**{name}** — {row['coins']} 🪙",
                    name=name,
                    score=float(row["coins"]),
                    value_text=f"{row['coins']:,} 🪙",
                ),
            )
        return entries

    async def member_rank(
        self,
        guild: discord.Guild,
        user_id: int,
    ) -> tuple[int | None, str | None]:
        all_coins = await db.fetchall(
            "SELECT user_id, coins FROM xp WHERE guild_id=$1 ORDER BY coins DESC",
            (guild.id,),
        )
        for i, row in enumerate(all_coins):
            if row["user_id"] == user_id:
                return i + 1, f"{row['coins']} 🪙"
        return None, None


class MiningProvider(RankProvider):
    name = "mining"
    display_title = "⛏️ Mining Leaderboard"
    select_label = "Mining"
    select_emoji = "⛏️"
    empty_hint = "No mining records yet. Use `!mine` to start collecting items."
    card_theme = "abyss"  # the underground / deep-cave skin

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        rows = await db.get_all_mining_totals(guild.id)
        entries: list[RankEntry] = []
        for user_id, total in rows[:10]:
            name = resources.member_display(guild, user_id)
            entries.append(
                RankEntry(
                    label=f"**{name}** — {total} items",
                    name=name,
                    score=float(total),
                    value_text=f"{total:,} items",
                ),
            )
        return entries

    async def member_rank(
        self,
        guild: discord.Guild,
        user_id: int,
    ) -> tuple[int | None, str | None]:
        rows = await db.get_all_mining_totals(guild.id)
        for i, (uid, total) in enumerate(rows):
            if uid == user_id:
                return i + 1, f"{total} items"
        return None, None


class CreaturesProvider(RankProvider):
    """The creature-catch game — ranked by total creatures caught.

    Mirrors the standalone ``!dextop`` command but as a registered category so
    the creature game appears in the unified ``!leaderboard`` hub alongside every
    other game. Reads the catalog-scoped ``top_collectors`` (only current-roster
    creatures count, so a superseded roster never inflates totals).
    """

    name = "creatures"
    display_title = "🐾 Creature Collector Leaderboard"
    select_label = "Creatures"
    select_emoji = "🐾"
    empty_hint = "No creatures caught yet. Use `!catch` to start your collection."
    card_theme = "verdant"  # the nature / collection skin

    @staticmethod
    def _render(caught: int, species: int) -> str:
        return f"{caught} caught ({species} species)"

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        rows = await db.top_collectors(guild.id, creature_names())
        entries: list[RankEntry] = []
        for user_id, caught, species in rows[:10]:
            name = resources.member_display(guild, user_id)
            entries.append(
                RankEntry(
                    label=f"**{name}** — {self._render(caught, species)}",
                    name=name,
                    score=float(caught),
                    value_text=f"{caught:,} caught",
                ),
            )
        return entries

    async def member_rank(
        self,
        guild: discord.Guild,
        user_id: int,
    ) -> tuple[int | None, str | None]:
        rows = await db.top_collectors(guild.id, creature_names(), limit=500)
        for i, (uid, caught, species) in enumerate(rows):
            if uid == user_id:
                return i + 1, self._render(caught, species)
        return None, None


class GameXpProvider(RankProvider):
    """The shared cross-game progression track (game_xp_service)."""

    name = "gamexp"
    display_title = "🎮 Game Level Leaderboard"
    select_label = "Game Level"
    select_emoji = "🎮"
    empty_hint = (
        "No game XP earned yet. Play `!mine`, craft gear, or explore to "
        "start levelling."
    )

    @staticmethod
    def _render(total: int) -> str:
        level, _, _ = db.level_progress(total)
        return f"Level {level} ({total} XP)"

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        rows = await db.top_total_xp(guild.id)
        entries: list[RankEntry] = []
        for user_id, total in rows[:10]:
            name = resources.member_display(guild, user_id)
            level, _, _ = db.level_progress(total)
            entries.append(
                RankEntry(
                    label=f"**{name}** — {self._render(total)}",
                    name=name,
                    score=float(total),
                    value_text=f"Lv {level} · {total:,} XP",
                ),
            )
        return entries

    async def member_rank(
        self,
        guild: discord.Guild,
        user_id: int,
    ) -> tuple[int | None, str | None]:
        rows = await db.top_total_xp(guild.id, limit=200)
        for i, (uid, total) in enumerate(rows):
            if uid == user_id:
                return i + 1, self._render(total)
        return None, None


class CraftingProvider(RankProvider):
    """Crafting-game XP (the old ``crafting_top`` leaderboard, reborn)."""

    name = "crafting"
    display_title = "🔧 Crafting Leaderboard"
    select_label = "Crafting"
    select_emoji = "🔧"
    empty_hint = "No crafting XP yet. Craft or repair gear at the 🔧 Workshop."
    card_theme = "ember"  # the forge / fire skin

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        rows = await db.top_game_xp(guild.id, "crafting")
        entries: list[RankEntry] = []
        for user_id, xp in rows[:10]:
            name = resources.member_display(guild, user_id)
            entries.append(
                RankEntry(
                    label=f"**{name}** — {xp} crafting XP",
                    name=name,
                    score=float(xp),
                    value_text=f"{xp:,} XP",
                ),
            )
        return entries

    async def member_rank(
        self,
        guild: discord.Guild,
        user_id: int,
    ) -> tuple[int | None, str | None]:
        rows = await db.top_game_xp(guild.id, "crafting", limit=200)
        for i, (uid, xp) in enumerate(rows):
            if uid == user_id:
                return i + 1, f"{xp} crafting XP"
        return None, None


class DeathmatchProvider(RankProvider):
    name = "deathmatch"
    display_title = "⚔️ Deathmatch Leaderboard"
    select_label = "Deathmatch"
    select_emoji = "⚔️"
    empty_hint = (
        "No deathmatch results yet. Start a match with `!deathmatch` to appear here."
    )
    card_theme = "ember"  # the combat / fire skin

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        rows = await db.get_deathmatch_leaderboard(guild.id)
        entries: list[RankEntry] = []
        for row in rows[:10]:
            name = resources.member_display(guild, row["user_id"])
            entries.append(
                RankEntry(
                    label=f"**{name}** — {row['wins']}W / {row['losses']}L",
                    name=name,
                    score=float(row["wins"]),
                    value_text=f"{row['wins']}W / {row['losses']}L",
                ),
            )
        return entries

    async def member_rank(
        self,
        guild: discord.Guild,
        user_id: int,
    ) -> tuple[int | None, str | None]:
        rows = await db.get_deathmatch_leaderboard(guild.id)
        for i, row in enumerate(rows):
            if row["user_id"] == user_id:
                return i + 1, f"{row['wins']}W / {row['losses']}L"
        return None, None


class RpsProvider(RankProvider):
    name = "rps"
    display_title = "✂️ RPS Leaderboard"
    select_label = "RPS"
    select_emoji = "✂️"
    empty_hint = (
        "No RPS games played yet. Challenge someone with `!rps` to appear here."
    )

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        # The RPS leaderboard query already returns a "name" column —
        # display name is captured at game time, so don't re-resolve.
        rows = await db.rps_get_leaderboard(guild.id)
        entries: list[RankEntry] = []
        for row in rows[:10]:
            entries.append(
                RankEntry(
                    label=(
                        f"**{row['name']}** — "
                        f"{row['wins']}W / {row['losses']}L / {row['ties']}T"
                    ),
                    name=str(row["name"]),
                    score=float(row["wins"]),
                    value_text=f"{row['wins']}W / {row['losses']}L / {row['ties']}T",
                ),
            )
        return entries

    async def member_rank(
        self,
        guild: discord.Guild,
        user_id: int,
    ) -> tuple[int | None, str | None]:
        rows = await db.rps_get_leaderboard(guild.id)
        for i, row in enumerate(rows):
            # The query may not return user_id in every row shape;
            # match on the resolved display name as a fallback.
            row_uid = row.get("user_id") if isinstance(row, dict) else None
            if row_uid == user_id:
                return (
                    i + 1,
                    f"{row['wins']}W / {row['losses']}L / {row['ties']}T",
                )
        return None, None


class CountingProvider(RankProvider):
    name = "counting"
    display_title = "🔢 Counting Leaderboard"
    select_label = "Counting"
    select_emoji = "🔢"
    empty_hint = (
        "No counting activity yet. Count in the counting channel to appear here."
    )

    async def _all_totals(
        self,
        guild: discord.Guild,
    ) -> list[tuple[int, int]]:
        state = await db.get_counting_state(guild.id)
        totals: dict[int, int] = {}
        for ch_data in state.get("channels", {}).values():
            for uid_str, cnt in ch_data.get("leaderboard", {}).items():
                try:
                    uid = int(uid_str)
                except (TypeError, ValueError):
                    continue
                totals[uid] = totals.get(uid, 0) + int(cnt)
        return sorted(totals.items(), key=lambda x: x[1], reverse=True)

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        sorted_totals = await self._all_totals(guild)
        entries: list[RankEntry] = []
        for uid, cnt in sorted_totals[:10]:
            name = resources.member_display(guild, uid)
            entries.append(
                RankEntry(
                    label=f"**{name}** — {cnt} counts",
                    name=name,
                    score=float(cnt),
                    value_text=f"{cnt:,} counts",
                ),
            )
        return entries

    async def member_rank(
        self,
        guild: discord.Guild,
        user_id: int,
    ) -> tuple[int | None, str | None]:
        sorted_totals = await self._all_totals(guild)
        for i, (uid, cnt) in enumerate(sorted_totals):
            if uid == user_id:
                return i + 1, f"{cnt} counts"
        return None, None


class KarmaProvider(RankProvider):
    name = "karma"
    display_title = "✨ Karma Leaderboard"
    select_label = "Karma"
    select_emoji = "✨"
    empty_hint = "No karma yet. Thank a helpful member with `!thanks @user`."

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        rows = await db.top_karma(guild.id, 10)
        entries: list[RankEntry] = []
        for row in rows:
            name = resources.member_display(guild, row["user_id"])
            entries.append(
                RankEntry(
                    label=f"**{name}** — {row['karma_points']} ✨",
                    name=name,
                    score=float(row["karma_points"]),
                    value_text=f"{row['karma_points']:,} ✨",
                ),
            )
        return entries

    async def member_rank(
        self,
        guild: discord.Guild,
        user_id: int,
    ) -> tuple[int | None, str | None]:
        row = await db.get_karma(user_id, guild.id)
        points = int(row.get("karma_points", 0) or 0)
        if points <= 0:
            return None, None
        rank = await db.karma_rank(user_id, guild.id)
        return rank, f"{points} ✨"


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


_PROVIDERS: dict[str, RankProvider] = {
    p.name: p
    for p in (
        XpProvider(),
        CoinsProvider(),
        MiningProvider(),
        CreaturesProvider(),
        GameXpProvider(),
        CraftingProvider(),
        DeathmatchProvider(),
        RpsProvider(),
        CountingProvider(),
        KarmaProvider(),
    )
}

# Alias map — historical ``!leaderboard`` shortcuts that should resolve
# to the same provider. Pin compatibility for existing operators.
ALIASES: dict[str, str] = {
    "lb": "xp",
    "rankings": "xp",
    "minelb": "mining",
    "miningleaderboard": "mining",
    "creature": "creatures",
    "creaturelb": "creatures",
    "gxp": "gamexp",
    "gamelevel": "gamexp",
    "game_xp": "gamexp",
    "crafting_top": "crafting",
    "craftlb": "crafting",
    "dm_leaderboard": "deathmatch",
    "dm_lb": "deathmatch",
    "board": "deathmatch",
    "rpslb": "rps",
    "countlb": "counting",
    "counting_leaderboard": "counting",
    "rep": "karma",
    "reputation": "karma",
    "karmalb": "karma",
}


def provider_names() -> list[str]:
    """Return the canonical provider names in registration order."""
    return list(_PROVIDERS.keys())


def get_provider(name: str) -> RankProvider | None:
    """Resolve a provider by canonical name or alias.

    Returns ``None`` if the key is unknown — callers handle that as
    an operator error (typed wrong category).
    """
    key = name.lower().strip()
    key = ALIASES.get(key, key)
    return _PROVIDERS.get(key)


__all__ = [
    "ALIASES",
    "CoinsProvider",
    "CountingProvider",
    "CreaturesProvider",
    "DeathmatchProvider",
    "MiningProvider",
    "RankEntry",
    "RankProvider",
    "RpsProvider",
    "XpProvider",
    "get_provider",
    "provider_names",
]
