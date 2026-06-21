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
    """

    label: str


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
        return [
            RankEntry(
                label=(
                    f"**{resources.member_display(guild, row['user_id'])}** "
                    f"— Level {row['level']} ({row['xp']} XP)"
                ),
            )
            for row in rows
        ]

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
        return [
            RankEntry(
                label=(
                    f"**{resources.member_display(guild, row['user_id'])}** "
                    f"— {row['coins']} 🪙"
                ),
            )
            for row in rows
        ]

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

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        rows = await db.get_all_mining_totals(guild.id)
        return [
            RankEntry(
                label=(
                    f"**{resources.member_display(guild, user_id)}** "
                    f"— {total} items"
                ),
            )
            for user_id, total in rows[:10]
        ]

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

    @staticmethod
    def _render(caught: int, species: int) -> str:
        return f"{caught} caught ({species} species)"

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        rows = await db.top_collectors(guild.id, creature_names())
        return [
            RankEntry(
                label=(
                    f"**{resources.member_display(guild, user_id)}** "
                    f"— {self._render(caught, species)}"
                ),
            )
            for user_id, caught, species in rows[:10]
        ]

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
        return [
            RankEntry(
                label=(
                    f"**{resources.member_display(guild, user_id)}** "
                    f"— {self._render(total)}"
                ),
            )
            for user_id, total in rows[:10]
        ]

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

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        rows = await db.top_game_xp(guild.id, "crafting")
        return [
            RankEntry(
                label=(
                    f"**{resources.member_display(guild, user_id)}** "
                    f"— {xp} crafting XP"
                ),
            )
            for user_id, xp in rows[:10]
        ]

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

    async def top(self, guild: discord.Guild) -> list[RankEntry]:
        rows = await db.get_deathmatch_leaderboard(guild.id)
        return [
            RankEntry(
                label=(
                    f"**{resources.member_display(guild, row['user_id'])}** "
                    f"— {row['wins']}W / {row['losses']}L"
                ),
            )
            for row in rows[:10]
        ]

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
        return [
            RankEntry(
                label=(
                    f"**{row['name']}** — "
                    f"{row['wins']}W / {row['losses']}L / {row['ties']}T"
                ),
            )
            for row in rows[:10]
        ]

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
        return [
            RankEntry(
                label=f"**{resources.member_display(guild, uid)}** — {cnt} counts",
            )
            for uid, cnt in sorted_totals[:10]
        ]

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
