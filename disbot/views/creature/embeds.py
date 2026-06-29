"""Creature embeds — one home for every render path (panel + both cogs).

The Creatures surface is rendered from three places: the ``creature_cog`` commands
(``!catch`` / ``!dex`` / ``!dextop``), the ``creature_battle_cog`` commands
(``!cbrecord`` / ``!cbattletop``), and the interactive :mod:`views.creature.menu`
panel. Keeping each embed builder here — instead of inline in each cog — is the
one-source-of-truth rule: the panel's dex/ladder/record cards can't drift from the
typed commands' (the completion-cert deepening, Q-0209).

Pure embed construction (no Discord I/O, no DB) so the builders are trivially
unit-testable; the callers fetch the rows and hand them in.
"""

from __future__ import annotations

import discord

from utils.creatures import CREATURES
from utils.ui_constants import INFO_COLOR

#: The shared Creatures colour (the green the cog used for dex/catch embeds).
CREATURE_COLOR = discord.Color.green()
#: The PvP battle colour (the red the battle cog used for record/ladder embeds).
BATTLE_COLOR = discord.Color.red()

#: Distinct elements in catalog order — the dex browser's filter options.
ELEMENTS: tuple[str, ...] = tuple(dict.fromkeys(c.element for c in CREATURES))


def winrate(wins: int, losses: int) -> str:
    """A ``NN%`` win-rate string from a W/L tally (``—`` with no battles)."""
    total = wins + losses
    if total == 0:
        return "—"
    return f"{round(100 * wins / total)}%"


def build_menu_embed(caught_unique: int = 0, level: int = 1) -> discord.Embed:
    """The Creatures-panel landing embed — what the hub shows before you act.

    *caught_unique* / *level* personalise the blurb when the caller has loaded the
    player's progress; the defaults render a generic overview (the Help-hook path
    passes the real numbers).
    """
    embed = discord.Embed(
        title="🐾 Creatures",
        description=(
            f"Catch from **{len(CREATURES)}** original creatures across "
            f"{len(ELEMENTS)} elements. Rarer creatures show up less often and are "
            "harder to catch — fill out your dex, then battle other trainers in a "
            "level-normalized PvP where type matchups decide it.\n\n"
            "**🐾 Catch** — head into the wild\n"
            "**📖 Dex** — browse your collection by element\n"
            "**⚔️ Challenge** — battle another trainer\n"
            "**🏆 Ladder** — the server's top trainers\n"
            "**📖 How to play** — the rules"
        ),
        color=CREATURE_COLOR,
    )
    embed.add_field(
        name="Your progress",
        value=f"**{caught_unique}/{len(CREATURES)}** creatures · level **{level}**",
        inline=False,
    )
    embed.set_footer(text="Only you can use this panel.")
    return embed


def build_catch_result_embed(
    author_name: str,
    result,
) -> discord.Embed:
    """The outcome of one ``!catch`` / Catch-button attempt.

    Shared by the typed ``!catch`` command and the panel's 🐾 Catch button so the
    flee / caught / new-entry copy is identical. *result* is a
    ``services.creature_workflow.CatchResult``.
    """
    creature = result.creature
    if creature is None:
        return discord.Embed(
            title="🐾 Creatures",
            description="The wilds are quiet right now — try again in a moment.",
            color=CREATURE_COLOR,
        )
    if not result.caught:
        return discord.Embed(
            title="🐾 It got away!",
            description=(
                f"{author_name} spotted a wild {creature.emoji} **{creature.name}** "
                f"({creature.rarity} {creature.element}) — but it escaped. Try again!"
            ),
            color=discord.Color.orange(),
        )
    lines = [
        f"{author_name} caught {creature.emoji} a **{creature.name}**! "
        f"({creature.rarity} {creature.element})",
    ]
    if result.is_new:
        lines.append("✨ **New dex entry!**")
    if result.xp_note:
        lines.append(result.xp_note)
    return discord.Embed(
        title="🎉 Caught!",
        description="\n".join(lines),
        color=CREATURE_COLOR,
    )


def build_dex_embed(
    display_name: str,
    log: dict[str, int],
    level: int,
    *,
    element: str | None = None,
) -> discord.Embed:
    """The collection embed — shared by ``!dex`` and the panel's dex browser.

    Pass *element* to filter to a single element (the browser's filter); ``None``
    shows every element grouped. Counts only current-catalog creatures so legacy
    rows from a superseded roster never show impossible progress (the fishing
    reconciliation lesson, mirrored from the original ``!dex``).
    """
    known = {c.name for c in CREATURES}
    caught_unique = sum(1 for name in log if name in known)
    total = sum(c for name, c in log.items() if name in known)
    embed = discord.Embed(
        title=f"🐾 {display_name}'s Creature Dex",
        color=CREATURE_COLOR,
    )
    scope = f" · filtered to **{element}**" if element else ""
    embed.description = (
        f"**{caught_unique}/{len(CREATURES)}** creatures discovered · "
        f"**{total}** total catches · Creature level **{level}**{scope}"
    )
    by_element: dict[str, list[str]] = {}
    for creature in CREATURES:
        if element is not None and creature.element != element:
            continue
        count = log.get(creature.name, 0)
        if count:
            line = f"{creature.emoji} **{creature.name}** ×{count}"
        else:
            line = f"{creature.emoji} {creature.name} — *not yet caught*"
        by_element.setdefault(creature.element, []).append(line)
    for element_name, lines in by_element.items():
        embed.add_field(name=element_name, value="\n".join(lines), inline=True)
    embed.set_footer(text="🐾 Catch to hunt · 🏆 Ladder for the leaderboard")
    return embed


def build_collectors_embed(
    rows: list[tuple[int, int, int]],
    resolve_name,
) -> discord.Embed:
    """The top-collectors leaderboard — shared by ``!dextop``.

    *rows* are ``(user_id, caught, unique)`` tuples; *resolve_name* maps a user id
    to a display name (the caller owns guild/member resolution so this stays pure).
    """
    embed = discord.Embed(title="🐾 Top Collectors", color=CREATURE_COLOR)
    if not rows:
        embed.description = "No one has been catching yet — be the first with `!catch`!"
        return embed
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for rank, (user_id, caught, unique) in enumerate(rows):
        prefix = medals[rank] if rank < len(medals) else f"**{rank + 1}.**"
        lines.append(
            f"{prefix} {resolve_name(user_id)} — **{caught}** caught "
            f"({unique}/{len(CREATURES)} creatures)",
        )
    embed.description = "\n".join(lines)
    return embed


def build_record_embed(display_name: str, wins: int, losses: int) -> discord.Embed:
    """A trainer's PvP win/loss record — shared by ``!cbrecord`` and the panel."""
    embed = discord.Embed(
        title=f"⚔️ {display_name}'s Battle Record",
        description=(
            f"**{wins}** wins · **{losses}** losses · "
            f"win rate **{winrate(wins, losses)}**"
        ),
        color=BATTLE_COLOR,
    )
    embed.set_footer(
        text="⚔️ Challenge a trainer to fight · 🏆 Ladder for the rankings",
    )
    return embed


def build_battletop_embed(
    rows: list[tuple[int, int, int]],
    resolve_name,
) -> discord.Embed:
    """The PvP win ladder — shared by ``!cbattletop`` and the panel's 🏆 Ladder.

    *rows* are ``(user_id, wins, losses)`` tuples; *resolve_name* maps a user id to
    a display name (the caller owns guild/member resolution).
    """
    embed = discord.Embed(title="⚔️ Top Trainers", color=BATTLE_COLOR)
    if not rows:
        embed.description = (
            "No battles won yet — challenge someone with `!cbattle @member`!"
        )
        return embed
    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for rank, (user_id, wins, losses) in enumerate(rows):
        prefix = medals[rank] if rank < len(medals) else f"**{rank + 1}.**"
        lines.append(
            f"{prefix} {resolve_name(user_id)} — **{wins}**W · {losses}L "
            f"({winrate(wins, losses)})",
        )
    embed.description = "\n".join(lines)
    return embed


def build_rules_embed() -> discord.Embed:
    """The "how to play Creatures" quick-reference — the panel's 📖 affordance."""
    return discord.Embed(
        title="📖 How to play Creatures",
        description=(
            "**The loop**\n"
            "1. **🐾 Catch** — head into the wild. A creature appears (rarer ones "
            "show up less often); the catch can succeed or it can flee.\n"
            "2. **📖 Dex** — every creature you've caught, browsable by element. "
            "Fill it out by catching the rarer elements and rarities.\n"
            "3. **⚔️ Challenge** — battle another trainer. Both teams are "
            "**normalized to level 50**, so it's about your collection and **type "
            "matchups**, never who ground more XP (anti-pay-to-win).\n\n"
            "**Good to know**\n"
            "• Catching and winning battles both award **creature XP** — no coins, "
            "nothing to lose.\n"
            "• You need **at least one creature** to battle, so catch first.\n"
            "• **🏆 Ladder** ranks the server's top trainers by wins."
        ),
        color=INFO_COLOR,
    )
