"""V/M/A handler for the counting on_message hot path (Phase S2.1 / H-2).

Implements the **Validate / Mutate / Apply** pattern documented in
``docs/architecture.md`` §"Realtime / event-driven systems":

  * :func:`compute_decision` — pure-ish function (state-in,
    decision-out; mutates ``channel_data`` in place).  MUST be called
    under the channel's ``scope_locks.lock_for(...)`` block.
  * :func:`apply_decision` — performs the Discord I/O.  MUST be called
    OUTSIDE the scope_lock so a slow API roundtrip cannot stall
    concurrent messages on the same or other channels.

This split fixes H-2 from the audit: the original
``cogs/counting_cog.py:on_message`` held a cog-wide ``self.lock``
across every Discord ``message.delete`` / ``channel.send`` / ``add_reaction``
call, serialising EVERY counting message in the bot through one
critical section.  After the refactor, the lock holds only for the
in-memory state transition (microseconds) and is released before any
Discord API call.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import discord

from cogs.counting import game_logic, parsing
from services import moderation_service

logger = logging.getLogger("bot.counting.handler")

# Modes that reset to 0 on a wrong count (everything in the bot today).
# Preserved verbatim from the pre-refactor listener so behavior matches.
_RESET_TO_ZERO_MODES = (
    "normal",
    "random",
    "skip",
    "multiples",
    "prime",
    "fibonacci",
    "squares",
    "cubes",
    "factorials",
    "custom",
)

# Modes whose success path advances a sequence_index counter.
_SEQUENCE_MODES = ("fibonacci", "squares", "cubes", "factorials", "custom")


@dataclass(frozen=True)
class CountingDecision:
    """Side-effects for one counting message.

    Computed under ``scope_locks.lock_for(f"counting:channel:{cid}")``
    and applied OUTSIDE the lock.  ``state_mutated`` tells the caller
    to spawn the persistence task.
    """

    accepted: bool
    delete_message: bool = False
    reply: str | None = None
    add_reaction: str | None = None
    state_mutated: bool = False
    # Seconds before the bot's reply auto-deletes; ``None`` keeps it.
    # Random mode's range hints must persist so players can see the
    # current window between guesses.
    reply_delete_after: int | None = 5


def compute_decision(
    *,
    message: discord.Message,
    channel_data: dict[str, Any],
    user_id: str,
) -> CountingDecision:
    """Validate the message, mutate ``channel_data`` in place, return a Decision.

    MUST be called under the channel's scope_lock — ``channel_data`` is
    mutated for success and reset paths.

    The pure-ish shape (state-in / decision-out, no Discord I/O) makes
    the listener unit-testable without a Discord mock harness.
    """
    mode = channel_data.get("mode", "normal")
    taking_turns = channel_data.get("taking_turns", False)
    current_count = channel_data.get("current_count", 0)
    last_user = channel_data.get("last_user")
    multiple = channel_data.get("multiple")
    reset_on_wrong = channel_data.get("reset_on_wrong_count", False)

    parsed = parsing.parse_message(message.content)
    if parsed is None:
        return CountingDecision(
            accepted=False,
            delete_message=True,
            reply=(
                f"{message.author.mention}, please send a valid number "
                f"or mathematical expression."
            ),
        )

    if mode == "random":
        return _decide_random(channel_data, parsed, user_id)

    expected = game_logic.calculate_expected_count(channel_data, current_count, mode)

    if parsed != expected:
        if reset_on_wrong:
            _reset_channel_data(channel_data, mode)
            return CountingDecision(
                accepted=False,
                delete_message=True,
                reply=(
                    f"{message.author.mention}, incorrect count! "
                    f"The count has been reset."
                ),
                state_mutated=True,
            )
        return CountingDecision(
            accepted=False,
            delete_message=True,
            reply=(
                f"{message.author.mention}, incorrect count! "
                f"The next number should be {expected}."
            ),
        )

    if taking_turns and user_id == last_user:
        return CountingDecision(
            accepted=False,
            delete_message=True,
            reply=f"{message.author.mention}, you cannot count twice in a row!",
        )

    if mode == "multiples" and multiple and parsed % multiple != 0:
        return CountingDecision(
            accepted=False,
            delete_message=True,
            reply=(
                f"{message.author.mention}, please count in multiples of {multiple}."
            ),
        )

    if mode == "prime" and not game_logic.is_prime(parsed):
        return CountingDecision(
            accepted=False,
            delete_message=True,
            reply=f"{message.author.mention}, please count prime numbers only.",
        )

    # Success — mutate channel_data in place.
    channel_data["current_count"] = parsed
    channel_data["last_user"] = user_id
    channel_data["last_count_time"] = datetime.now(tz=timezone.utc).timestamp()
    if mode == "random":
        rng = channel_data.get("random_range", [1, 3])
        channel_data["next_expected"] = parsed + random.randint(*rng)
    if mode in _SEQUENCE_MODES:
        channel_data["sequence_index"] = channel_data.get("sequence_index", 0) + 1
    leaderboard = channel_data.get("leaderboard", {})
    leaderboard[user_id] = leaderboard.get(user_id, 0) + 1
    channel_data["leaderboard"] = leaderboard

    return CountingDecision(
        accepted=True,
        add_reaction="✅",
        state_mutated=True,
    )


def _reset_channel_data(channel_data: dict[str, Any], mode: str) -> None:
    """Wipe channel_data to the start-of-match state, preserving config.

    Mirrors the inline reset block that lived in the pre-refactor
    listener.  The reset-target for ``current_count`` is mode-specific:
    1000 for modes that are NOT in the reset-to-zero list (today only
    "reverse"; left as future-proofing in case more reverse modes are
    added).
    """
    channel_data["current_count"] = 0 if mode in _RESET_TO_ZERO_MODES else 1000
    channel_data["sequence_index"] = 0
    channel_data["last_user"] = None
    channel_data["leaderboard"] = {}
    channel_data["last_count_time"] = datetime.now(tz=timezone.utc).timestamp()


def _decide_random(
    channel_data: dict[str, Any],
    parsed: int,
    user_id: str,
) -> CountingDecision:
    """Decision for ``random`` mode — a guess-the-secret-number game.

    A hidden ``next_expected`` target sits inside an announced
    ``[range_lo, range_hi]`` window.  A correct guess advances the count
    and rolls a fresh target + wide window; a wrong guess halves the
    window toward the target (min width 10) and re-announces it with a
    higher/lower hint.  Wrong guesses do NOT reset the count — players
    keep narrowing until they land it, and their guesses stay in the
    channel as part of play.
    """
    target = channel_data.get("next_expected")
    lo = channel_data.get("range_lo")
    hi = channel_data.get("range_hi")
    if not (isinstance(target, int) and isinstance(lo, int) and isinstance(hi, int)):
        # Legacy / missing state — (re)initialise a round so play continues.
        target, lo, hi = game_logic.start_random_round(
            int(channel_data.get("current_count", 0) or 0),
        )
        channel_data["next_expected"] = target
        channel_data["range_lo"], channel_data["range_hi"] = lo, hi

    if parsed == target:
        channel_data["current_count"] = parsed
        channel_data["last_user"] = user_id
        leaderboard = channel_data.get("leaderboard", {})
        leaderboard[user_id] = leaderboard.get(user_id, 0) + 1
        channel_data["leaderboard"] = leaderboard
        n_target, n_lo, n_hi = game_logic.start_random_round(parsed)
        channel_data["next_expected"] = n_target
        channel_data["range_lo"], channel_data["range_hi"] = n_lo, n_hi
        return CountingDecision(
            accepted=True,
            add_reaction="✅",
            state_mutated=True,
            reply=(
                f"✅ Correct — it was **{parsed}**! "
                f"Next secret number is between **{n_lo}–{n_hi}**."
            ),
            reply_delete_after=None,
        )

    n_lo, n_hi = game_logic.narrow_random_range(lo, hi, target)
    channel_data["range_lo"], channel_data["range_hi"] = n_lo, n_hi
    direction = "Higher" if parsed < target else "Lower"
    return CountingDecision(
        accepted=False,
        state_mutated=True,
        reply=f"❌ Not **{parsed}**. {direction} — it's between **{n_lo}–{n_hi}**.",
        reply_delete_after=None,
    )


async def apply_decision(
    decision: CountingDecision,
    message: discord.Message,
) -> None:
    """Apply Discord side-effects.  MUST be called OUTSIDE the scope_lock.

    Each Discord call is independently guarded with try/except so a
    single ``Forbidden`` (e.g. missing manage_messages perm) does not
    skip the remaining steps.

    Deletions route through ``moderation_service.auto_delete`` so the
    ``mod_logs`` audit table and ``EVT_MOD_ACTION`` event bus see
    every counting-rule removal — closing the §2.2 gap (CountingCog
    deletes were previously invisible to moderation audit).
    """
    if decision.delete_message:
        await moderation_service.auto_delete(
            message,
            reason=decision.reply or "Invalid count",
            rule="counting.invalid",
        )
    if decision.reply:
        try:
            await message.channel.send(
                decision.reply,
                delete_after=decision.reply_delete_after,
            )
        except discord.Forbidden:
            pass
    if decision.add_reaction:
        try:
            await message.add_reaction(decision.add_reaction)
        except discord.Forbidden:
            pass
