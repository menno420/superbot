"""Battle-outcome embed renderer for creature PvP (creature-game v1).

Turns a :class:`services.creature_battle_service.PvpResult` into a readable
Discord embed: each side's roster (with fainted markers), the key KO moments
from the engine's turn-by-turn log, and the winner. Pure presentation — no
Discord IO, so it is unit-testable on a plain result object.
"""

from __future__ import annotations

import discord

from services.creature_battle_service import PvpResult
from utils.creatures import Combatant
from utils.ui_constants import SUCCESS_COLOR

#: Cap on KO lines shown in the highlights field (a 6v6 fight KOs at most 12).
_MAX_HIGHLIGHTS = 12


def _roster_line(team: tuple[Combatant, ...]) -> str:
    """One creature per line: emoji + name, with a 💀 marker if it fainted.

    Reads each combatant's *final* HP state (the result snapshot holds the same
    combatant objects the engine resolved), so survivors and casualties are
    distinguishable at a glance.
    """
    if not team:
        return "*no creatures*"
    return "\n".join(
        f"{'💀 ' if m.fainted else ''}{m.creature.emoji} {m.name}" for m in team
    )


def _highlights(result: PvpResult) -> str:
    """The KO moments from the battle log, in order, capped for readability."""
    kos = [
        f"💥 **{e.actor}** took down **{e.target}**"
        for e in result.outcome.events
        if e.faint
    ]
    if not kos:
        return "*A swift, decisive bout.*"
    shown = kos[:_MAX_HIGHLIGHTS]
    if len(kos) > _MAX_HIGHLIGHTS:
        shown.append(f"…and {len(kos) - _MAX_HIGHLIGHTS} more")
    return "\n".join(shown)


def _records_line(
    challenger: discord.abc.User,
    opponent: discord.abc.User,
    records: dict[int, tuple[int, int]],
) -> str:
    """One ``name — W–L`` line per fighter from their updated tally."""
    lines = []
    for member in (challenger, opponent):
        wins, losses = records.get(member.id, (0, 0))
        lines.append(f"{member.display_name} — **{wins}**W · **{losses}**L")
    return "\n".join(lines)


def build_result_embed(
    challenger: discord.abc.User,
    opponent: discord.abc.User,
    result: PvpResult,
    *,
    records: dict[int, tuple[int, int]] | None = None,
    xp_note: str | None = None,
) -> discord.Embed:
    """Render the resolved PvP battle for the channel.

    ``challenger`` is team A, ``opponent`` is team B (the order
    :func:`services.creature_battle_service.resolve_pvp` was called with).

    When *records* is given (``{user_id: (wins, losses)}`` from a recorded battle),
    a *Records* field shows each fighter's updated standing; *xp_note* adds the
    winner's level-up notice when the win crossed a shared game level.
    """
    winner = challenger if result.a_won else opponent
    embed = discord.Embed(
        title="⚔️ Creature Battle",
        description=(
            f"{challenger.mention} vs {opponent.mention}\n"
            f"*Teams are level-normalized — type matchups and your collection decide it.*"
        ),
        color=SUCCESS_COLOR,
    )
    embed.add_field(
        name=f"{challenger.display_name}'s team",
        value=_roster_line(result.team_a),
        inline=True,
    )
    embed.add_field(
        name=f"{opponent.display_name}'s team",
        value=_roster_line(result.team_b),
        inline=True,
    )
    embed.add_field(name="Highlights", value=_highlights(result), inline=False)
    winner_value = f"🏆 {winner.mention}"
    if xp_note:
        winner_value += f"\n{xp_note}"
    embed.add_field(name="Winner", value=winner_value, inline=False)
    if records is not None:
        embed.add_field(
            name="Records",
            value=_records_line(challenger, opponent, records),
            inline=False,
        )
    return embed
