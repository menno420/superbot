"""Title service — the write boundary for the equipped-title selection (§7.6).

Earned titles are **derived** (``utils.mining.titles`` over already-owned
progression), so this service grants nothing on a mutation path: it builds the
:class:`~utils.mining.titles.TitleContext` from the player's skills / depth /
level, and owns the only ``equipped_title`` mutation
(:func:`equip` / :func:`unequip` through ``db.set_equipped_title``, which is on
the RS02 write-boundary ratchet — the ``skill_service`` precedent).

Equipping is self-service (no coins move, so no audit/transaction — the
``allocate`` precedent). The displayed title is **gated on still being earned**
(:func:`equipped_title`): a respec that drops a branch below its cap silently
un-displays a mastery title without needing to clear the stored choice.
"""

from __future__ import annotations

from dataclasses import dataclass

from services import game_xp_service
from utils import db
from utils.mining import titles


@dataclass(frozen=True)
class TitleResult:
    """Outcome of an equip/unequip attempt — the cog/view owns final copy."""

    ok: bool
    message: str


async def build_context(guild_id: int, user_id: int) -> titles.TitleContext:
    """Assemble the earn-check inputs from the player's existing progression."""
    suid = str(user_id)
    alloc = await db.get_skills(user_id, guild_id)
    max_depth = await db.get_max_depth(suid, guild_id)
    level, _, _ = await game_xp_service.level_info(guild_id, user_id)
    return titles.TitleContext(skills=alloc, max_depth=max_depth, level=level)


async def earned(guild_id: int, user_id: int) -> tuple[titles.Title, ...]:
    """Every title this player currently qualifies for (catalogue order)."""
    return titles.earned_titles(await build_context(guild_id, user_id))


async def equipped_title(guild_id: int, user_id: int) -> titles.Title | None:
    """The player's equipped title **iff still earned**, else None.

    Gating on the live earn-check means an un-earned (e.g. post-respec) stored
    choice simply stops displaying — no migration / cleanup of the column.
    """
    title_id = await db.get_equipped_title(str(user_id), guild_id)
    title = titles.get_title(title_id)
    if title is None:
        return None
    ctx = await build_context(guild_id, user_id)
    return title if titles.is_earned(title.id, ctx) else None


async def equip(guild_id: int, user_id: int, title_id: str) -> TitleResult:
    """Equip an earned title (validates it exists and is earned)."""
    title = titles.get_title(title_id.strip().lower())
    if title is None:
        return TitleResult(
            False,
            "That isn't a real title — open the 🏆 Titles panel to see yours.",
        )
    ctx = await build_context(guild_id, user_id)
    if not titles.is_earned(title.id, ctx):
        return TitleResult(
            False,
            f"You haven't earned **{title.label}** yet — {title.requirement}.",
        )
    await db.set_equipped_title(str(user_id), guild_id, title.id)
    return TitleResult(True, f"Title set to {titles.display(title)}.")


async def unequip(guild_id: int, user_id: int) -> TitleResult:
    """Clear the equipped title (no-op-safe — always succeeds)."""
    await db.set_equipped_title(str(user_id), guild_id, None)
    return TitleResult(True, "Title cleared — none displayed.")


__all__ = [
    "TitleResult",
    "build_context",
    "earned",
    "equipped_title",
    "equip",
    "unequip",
]
