"""Channel enable / disable / mutate helpers for CountingCog (panel-driven).

The counting cog grew to the S4.6 warn-tier when these methods were added
directly to counting_cog.py, so they live here following the established
``cogs/<sub>/_helpers.py`` decomposition pattern.

All functions receive the cog instance so they share its lock, count_data,
game_logic dependency, and tasks.spawn path — none of the concurrency
contracts change.
"""

from __future__ import annotations

from datetime import datetime, timezone

from cogs.counting import game_logic
from core.runtime import scope_locks, tasks

# No-argument modes panel can enable directly. ``multiples`` (factor)
# and ``custom`` (sequence) need extra input, so they stay on !start_match.
NO_ARG_MODES: frozenset[str] = frozenset(
    {
        "normal",
        "reverse",
        "skip",
        "random",
        "prime",
        "fibonacci",
        "squares",
        "cubes",
        "factorials",
    },
)


def _scope_id(channel_id: str) -> str:
    return f"counting:channel:{channel_id}"


def default_channel_config(mode: str, *, skip_step: int = 5) -> dict:
    """Build a fresh per-channel counting config for a no-arg mode."""
    starting_count = 1000 if mode == "reverse" else 0
    rand_target = rand_lo = rand_hi = None
    if mode == "random":
        rand_target, rand_lo, rand_hi = game_logic.start_random_round(starting_count)
    config: dict = {
        "current_count": starting_count,
        "last_user": None,
        "taking_turns": False,
        "leaderboard": {},
        "mode": mode,
        "step": skip_step if mode == "skip" else 1,
        "multiple": None,
        "custom_sequence": None,
        "sequence_index": 0,
        "last_count_time": datetime.now(tz=timezone.utc).timestamp(),
        "reset_on_wrong_count": False,
        "next_expected": rand_target,
        "range_lo": rand_lo,
        "range_hi": rand_hi,
    }
    if mode == "prime":
        config["prime_numbers"] = []
    return config


async def enable_channel(cog, guild_id: str, channel_id: str, mode: str) -> bool:
    """Register an EXISTING channel as an active counting channel.

    No Discord channel is created (unlike ``!start_match``). Returns
    ``False`` if the channel is already active or ``mode`` needs arguments.
    """
    if mode not in NO_ARG_MODES:
        return False
    async with cog.lock:
        cog.count_data.setdefault(guild_id, {}).setdefault("channels", {})
        if channel_id in cog.count_data[guild_id]["channels"]:
            return False
        cog.count_data[guild_id]["channels"][channel_id] = default_channel_config(mode)
        tasks.spawn(f"counting:save:{guild_id}", cog._save_guild(guild_id))
    return True


async def disable_channel(cog, guild_id: str, channel_id: str) -> bool:
    """Remove a channel from the active counting set WITHOUT deleting the
    Discord channel (distinct from ``!end_match``). Returns ``False`` if it
    wasn't active.
    """
    async with cog.lock:
        channels = cog.count_data.get(guild_id, {}).get("channels", {})
        if channel_id not in channels:
            return False
        del channels[channel_id]
        scope_locks.forget(_scope_id(channel_id))
        tasks.spawn(f"counting:save:{guild_id}", cog._save_guild(guild_id))
    return True


async def toggle_channel_flag(cog, guild_id: str, channel_id: str, flag: str) -> bool:
    """Flip a per-channel boolean (``taking_turns`` / ``reset_on_wrong_count``)."""
    async with cog.lock:
        ch_data = cog.count_data.get(guild_id, {}).get("channels", {}).get(channel_id)
        if ch_data is None:
            return False
        ch_data[flag] = not ch_data.get(flag, False)
        tasks.spawn(f"counting:save:{guild_id}", cog._save_guild(guild_id))
    return True


async def reset_channel_count(cog, guild_id: str, channel_id: str) -> bool:
    """Reset a counting channel to its starting state."""
    async with cog.lock:
        ch_data = cog.count_data.get(guild_id, {}).get("channels", {}).get(channel_id)
        if ch_data is None:
            return False
        mode = ch_data.get("mode", "normal")
        ch_data["current_count"] = 1000 if mode == "reverse" else 0
        ch_data["sequence_index"] = 0
        ch_data["last_user"] = None
        ch_data["leaderboard"] = {}
        ch_data["last_count_time"] = datetime.now(tz=timezone.utc).timestamp()
        if mode == "random":
            ch_data["next_expected"] = None
            ch_data["range_lo"] = None
            ch_data["range_hi"] = None
        tasks.spawn(f"counting:save:{guild_id}", cog._save_guild(guild_id))
    return True
