"""Skill service — the audited write boundary for the player skill tree (§7.4).

Owns every ``player_skills`` mutation, the way ``game_xp_service`` owns
``game_xp`` writes: a cog/view reads with ``available_points`` /
``db.get_skills`` and mutates only through :func:`allocate` / :func:`respec`
here.  ``db.set_skill_points`` is on the RS02 write-boundary ratchet, so this
service is its one caller.

Points are spent from the shared game-XP **level** (``game_xp_service``):
``available = min(level, SOFT_TOTAL_CAP) − sum(spent)``.  The soft total cap
(20) sits below ``4 × PER_BRANCH_CAP`` (40), so a player can never max every
branch — the forced specialization that is the feature's point.

``allocate`` is self-service (no audit — the craft precedent).  ``respec`` moves
coins, so it runs through ``economy_service.debit_in_txn`` inside one
transaction (the repair precedent — the coin debit is economy-audited and the
allocation clear commits or rolls back with it).
"""

from __future__ import annotations

from dataclasses import dataclass

from core.events import bus
from services import economy_service, game_xp_service
from utils import db
from utils.mining import skills

# Respec price: a base fee plus a per-level scaler, so deep characters pay more
# to re-spend a bigger pool (a real, level-scaled coin sink).
RESPEC_BASE_COST = 200
RESPEC_COST_PER_LEVEL = 50
RESPEC_REASON = "mining:skill_respec"


@dataclass(frozen=True)
class SkillResult:
    """Outcome of an allocate/respec attempt — the cog/view owns final copy."""

    ok: bool
    message: str
    #: Coins moved (negative on a respec debit), for the balance event / footer.
    coins_delta: int = 0
    new_balance: int | None = None


def respec_cost(level: int) -> int:
    """The coin cost to respec at *level* (base + per-level scaler)."""
    return RESPEC_BASE_COST + RESPEC_COST_PER_LEVEL * max(0, level)


async def available_points(guild_id: int, user_id: int) -> int:
    """Unspent skill points: ``min(level, SOFT_TOTAL_CAP) − sum(allocated)``.

    Floored at 0 (a player can't go negative even if the cap is lowered later).
    """
    level, _, _ = await game_xp_service.level_info(guild_id, user_id)
    alloc = await db.get_skills(user_id, guild_id)
    pool = min(level, skills.SOFT_TOTAL_CAP)
    return max(0, pool - skills.total_spent(alloc))


async def allocate(
    guild_id: int,
    user_id: int,
    branch: str,
    n: int = 1,
) -> SkillResult:
    """Spend *n* points into *branch* (validates branch, amount, caps, budget)."""
    branch = branch.strip().lower()
    if not skills.is_branch(branch):
        names = ", ".join(skills.BRANCHES)
        return SkillResult(
            False,
            f"**{branch or '(blank)'}** isn't a skill branch — pick one of: {names}.",
        )
    if n <= 0:
        return SkillResult(False, "Spend a positive number of points.")
    alloc = await db.get_skills(user_id, guild_id)
    current = alloc.get(branch, 0)
    if current + n > skills.PER_BRANCH_CAP:
        room = skills.PER_BRANCH_CAP - current
        return SkillResult(
            False,
            f"**{branch}** caps at **{skills.PER_BRANCH_CAP}** points "
            f"(you have {current} — room for {room}).",
        )
    avail = await available_points(guild_id, user_id)
    if n > avail:
        return SkillResult(
            False,
            f"You only have **{avail}** skill point{'s' if avail != 1 else ''} "
            "to spend — level up (play more) to earn more.",
        )
    # Self-service, single-row write — no coins move, so no economy/audit leg.
    await db.set_skill_points(user_id, guild_id, branch, current + n)
    remaining = avail - n
    return SkillResult(
        True,
        f"Spent **{n}** point{'s' if n != 1 else ''} into **{branch}** "
        f"(now {current + n}/{skills.PER_BRANCH_CAP}). "
        f"**{remaining}** point{'s' if remaining != 1 else ''} left.",
    )


async def respec(guild_id: int, user_id: int) -> SkillResult:
    """Clear every allocation for a coin fee — refunds all points to re-spend.

    The coin debit and the allocation clear commit in ONE transaction so a
    mid-respec failure never charges without clearing (or clears without
    charging).  The debit is economy-audited; the balance event emits after
    commit (the repair precedent).
    """
    alloc = await db.get_skills(user_id, guild_id)
    if not alloc:
        return SkillResult(False, "You have no skill points allocated to refund.")
    level, _, _ = await game_xp_service.level_info(guild_id, user_id)
    cost = respec_cost(level)
    try:
        async with db.transaction() as conn:
            new_balance = await economy_service.debit_in_txn(
                conn,
                guild_id,
                user_id,
                cost,
                reason=RESPEC_REASON,
                actor_id=user_id,
            )
            for branch in alloc:
                await db.set_skill_points(user_id, guild_id, branch, 0, conn=conn)
    except economy_service.InsufficientFundsError:
        balance = await db.get_coins(user_id, guild_id)
        return SkillResult(
            False,
            f"Respec costs **{cost}** 🪙 — you only have **{balance}** 🪙.",
        )
    # Balance event emits AFTER commit, never inside the transaction (the
    # economy_service / mining_workflow precedent).
    await bus.emit(
        economy_service.EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=-cost,
        new_balance=new_balance,
        reason=RESPEC_REASON,
    )
    return SkillResult(
        True,
        f"Respec complete — all points refunded for **{cost}** 🪙. "
        f"Balance: **{new_balance}** 🪙.",
        coins_delta=-cost,
        new_balance=new_balance,
    )


__all__ = [
    "RESPEC_BASE_COST",
    "RESPEC_COST_PER_LEVEL",
    "RESPEC_REASON",
    "SkillResult",
    "respec_cost",
    "available_points",
    "allocate",
    "respec",
]
