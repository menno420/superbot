"""Deathmatch action helpers (PR 6).

Shared helpers for the playable Help/Games → Deathmatch panel
(``views.games.deathmatch_panel``). The cog's typed ``!deathmatch``
command body remains authoritative for the human-PvP path; these
helpers wrap the same ``_Duel`` state for both PvP-from-panel and
the new bot-duel path.

Bot-duel stats rule (PR 6, plan §13):

* Player-vs-bot duels do **NOT** call ``Deathmatch.update_leaderboard``
  or ``db.update_deathmatch``. Bot wins/losses are shown only in the
  match result embed.
* Player-vs-player duels keep the existing leaderboard write path
  exactly as it was.
* Rationale: prevent farming or distortion of PvP rankings via the
  bot opponent.
"""

from __future__ import annotations

import random

import discord

from cogs.deathmatch_cog import Deathmatch

# ---------------------------------------------------------------------------
# Bot AI v1
# ---------------------------------------------------------------------------


def pick_bot_action(bot_hp: int) -> str:
    """Return ``"attack"`` or ``"defend"`` for the bot's turn.

    v1 strategy is intentionally simple and deterministic-seedable for
    tests: 70% attack / 30% defend at full health; biases slightly
    more defensive as HP drops below 50%.
    """
    choices: tuple[str, ...]
    if bot_hp < 25:
        choices = ("attack", "defend", "defend")
    elif bot_hp < 50:
        choices = ("attack", "attack", "defend")
    else:
        choices = ("attack", "attack", "attack", "defend")
    return random.choice(choices)


# ---------------------------------------------------------------------------
# Duel-key helpers
# ---------------------------------------------------------------------------


def make_duel_key(p1_id: int, p2_id: int) -> tuple[int, int]:
    """Stable duel-key matching the cog's existing
    ``tuple(sorted([author_id, opponent_id]))`` shape.
    """
    a, b = sorted((p1_id, p2_id))
    return (a, b)


def has_existing_duel(
    cog: Deathmatch,
    user_a_id: int,
    user_b_id: int,
) -> str | None:
    """Return an error message if either user is already in any duel,
    else ``None``.

    Mirrors the cog's ``!deathmatch`` body check:
        for existing_key in self.active_duels:
            if author.id in existing_key or opponent.id in existing_key:
                return error
    """
    key = make_duel_key(user_a_id, user_b_id)
    if key in cog.active_duels:
        return "A duel between you and that opponent is already in progress."
    for existing in cog.active_duels:
        if user_a_id in existing or user_b_id in existing:
            return "Either you or the opponent is already in a duel."
    return None


# ---------------------------------------------------------------------------
# PvP challenge check — extracted from the !deathmatch command body
# ---------------------------------------------------------------------------


def can_challenge_human(
    author: discord.Member,
    opponent: discord.Member,
) -> str | None:
    """Validate that ``author`` can challenge ``opponent`` to a PvP
    duel. Returns an error message or ``None`` if the pair is valid.

    The command body at ``cogs/deathmatch_cog.py:271-276`` does the
    same checks. The panel's "Challenge Player" path uses this; the
    panel's "Fight Bot" path bypasses ``opponent.bot`` (that's the
    whole point).
    """
    if opponent.id == author.id:
        return "You cannot challenge yourself!"
    if opponent.bot:
        return "You cannot PvP-challenge a bot — use Fight Bot instead."
    return None
