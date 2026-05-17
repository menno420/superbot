"""RPS bot-match command + on-message handler (S4.6).

Extracted from ``cogs/rps_tournament_cog.py``.  Module-level state
(``_bot_matches``, ``_bot_match_channels``) is initialised by the
cog's ``__init__`` (via :func:`reset_state`) and cleared by
``cog_unload`` so cog-reload semantics match the pre-extraction
layout — a reload starts with empty bot-match state, same as before.

The functions take the discord.py ctx/message/bot as parameters
rather than the cog instance so they're testable without a fully-
initialised RPSTournamentCog.  The cog method bodies that delegate
here pass through the inputs they receive from discord.py.
"""

from __future__ import annotations

import logging
import random

import discord

from cogs.rps_tournament._helpers import (
    create_bot_match_channel,
    schedule_channel_deletion,
    update_player_stats,
)
from cogs.rps_tournament.rules import GAME_MODES, determine_winner, normalize_move

logger = logging.getLogger("bot")


# ---------------------------------------------------------------------------
# Module-level state (cog lifecycle owns initialization + teardown)
# ---------------------------------------------------------------------------

_bot_matches: dict[discord.Member, dict] = {}
_bot_match_channels: set[int] = set()


def reset_state() -> None:
    """Clear bot-match state.  Called from cog ``__init__`` and ``cog_unload``.

    Preserves the pre-extraction "reload wipes state" behavior.
    """
    _bot_matches.clear()
    _bot_match_channels.clear()


# ---------------------------------------------------------------------------
# !rpsbot — start bot matches for one or more players
# ---------------------------------------------------------------------------


async def run_rps_bot_command(
    ctx,
    default_mode: str,
    default_best_of: int,
    mode: str | None,
    best_of: int | None,
    members_or_roles: tuple,
) -> None:
    """Body of the ``!rpsbot`` command.

    Resolves players from the provided members/roles (or ``ctx.author``
    if empty), creates one private channel per player, and seeds the
    in-memory bot-match state.
    """
    if mode is None:
        mode = default_mode
    if mode not in GAME_MODES:
        await ctx.send(
            f"Invalid game mode. Available modes: {', '.join(GAME_MODES.keys())}",
        )
        return

    if best_of is None:
        best_of = default_best_of
    if best_of % 2 == 0 or best_of < 1:
        await ctx.send(
            "Please provide an odd positive integer for the number of rounds.",
        )
        return

    players = []
    if members_or_roles:
        for item in members_or_roles:
            member = None
            if isinstance(item, discord.Member):
                member = item
            elif isinstance(item, str):
                # Try to get member by ID or mention
                member = ctx.guild.get_member_named(item)
            elif isinstance(item, discord.Role):
                players.extend(item.members)
                continue
            if member:
                players.append(member)
    else:
        players.append(ctx.author)

    for player in players:
        match_channel = await create_bot_match_channel(ctx.guild, player, ctx)
        if match_channel is None:
            await ctx.send(
                f"Failed to create match channel for {player.display_name}.",
            )
            continue

        _bot_matches[player] = {
            "channel": match_channel.id,
            "wins": 0,
            "bot_wins": 0,
            "best_of": best_of,
            "mode": mode,
        }
        _bot_match_channels.add(match_channel.id)

        await match_channel.send(
            f"{player.mention} vs **Bot**\n"
            f"Game mode: {mode.capitalize()}, Best of {best_of}\n"
            "Please enter your move.",
        )


# ---------------------------------------------------------------------------
# Bot-match move handler (called from cog.on_message)
# ---------------------------------------------------------------------------


def channel_is_bot_match(channel_id: int) -> bool:
    """Whether the given channel hosts an active bot match."""
    return channel_id in _bot_match_channels


async def handle_bot_match_move(message: discord.Message) -> None:
    """Handle a move typed in a bot-match channel.

    Mirrors the pre-extraction ``handle_bot_match_move`` body — pulls
    the player's match record, normalises the move, plays the bot,
    updates wins/losses, and ends the match when either side hits the
    required win count.

    Bot matches only run in guild text channels (the channel id is
    in ``_bot_match_channels``, populated by ``create_bot_match_channel``
    which always creates a guild channel).  The isinstance narrow is
    defensive — a DM cannot have its channel id in the set, so this
    is also a static-type narrow for mypy.
    """
    player = message.author
    if not isinstance(player, discord.Member):
        return
    match = _bot_matches.get(player)
    if not match:
        return

    # Check if the match is already over
    required_wins = (match["best_of"] // 2) + 1
    if match["wins"] >= required_wins or match["bot_wins"] >= required_wins:
        # Match is over; inform the player and return
        await message.channel.send("The match is already over.")
        return

    move = message.content.lower().strip()
    move = normalize_move(move, match["mode"])
    if move is None:
        await message.channel.send(
            f"{player.mention}, invalid move. Please try again.",
        )
        return

    bot_move = random.choice(GAME_MODES[match["mode"]])
    await message.channel.send(f"Bot played: {bot_move.capitalize()}.")

    winner = determine_winner(move, bot_move, match["mode"])
    if winner == 0:
        await message.channel.send("It's a tie!")
        update_player_stats(player, "tie")
    elif winner == 1:
        match["wins"] += 1
        await message.channel.send(f"{player.mention} wins this round!")
        update_player_stats(player, "win")
    else:
        match["bot_wins"] += 1
        await message.channel.send("Bot wins this round!")
        update_player_stats(player, "loss")

    # Check if someone has won the match
    if match["wins"] >= required_wins:
        await message.channel.send(
            f"{player.mention} wins the match against the bot!",
        )
        await schedule_channel_deletion(message.channel)
        del _bot_matches[player]
        _bot_match_channels.discard(message.channel.id)
        return  # Prevent further execution
    if match["bot_wins"] >= required_wins:
        await message.channel.send("Bot wins the match!")
        await schedule_channel_deletion(message.channel)
        del _bot_matches[player]
        _bot_match_channels.discard(message.channel.id)
        return  # Prevent further execution
    await message.channel.send("Please enter your next move.")
