from __future__ import annotations

import asyncio

import discord

from utils import db


class TournamentRegistration:
    """Shared registration state used by both BJ and RPS tournament cogs.

    Handles: player tracking, entry-fee gating, pot calculation,
    fee deduction at launch, and timer task bookkeeping.
    """

    def __init__(
        self,
        host_id: int,
        guild_id: int,
        announce_id: int,
        entry_fee: int,
        duration_mins: int,
    ):
        self.host_id = host_id
        self.guild_id = guild_id
        self.announce_id = announce_id
        self.entry_fee = entry_fee
        self.duration_mins = duration_mins
        self.players: set[int] = set()
        self.started: bool = False
        self.reg_message: discord.Message | None = None
        self.timer_task: asyncio.Task | None = None

    @property
    def pot(self) -> int:
        return self.entry_fee * len(self.players)

    async def try_join(self, user_id: int) -> tuple[bool, str]:
        """Validate and register a player.  Returns (success, message)."""
        if self.started:
            return False, "The tournament has already started."
        if user_id in self.players:
            return False, "You're already registered!"
        if self.entry_fee > 0:
            bal = await db.get_coins(user_id, self.guild_id)
            if bal < self.entry_fee:
                return False, (
                    f"❌ Need **{self.entry_fee}** 🪙 to enter (you have {bal})."
                )
        self.players.add(user_id)
        return True, f"✅ Registered! ({len(self.players)} player(s) so far)"

    # Note (P0-1): fee collection moved OUT of this shared helper into
    # ``services.game_wager_workflow.enter_tournament``, which debits the
    # fee and writes the recovery row in ONE transaction.  The old
    # ``deduct_fees`` debited each player in a separate top-level call
    # from the row that recovery refunds from — a crash in that window
    # lost the fee.  Both tournament cogs now call ``enter_tournament``
    # per player; do not re-add an un-escrowed batch debit here.
