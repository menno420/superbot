"""The fishing cast minigame — ``cast → wait → BITE → reel`` (owner design Q-0175).

``FishingCastView`` turns the prefix-only instant catch into a skill moment. On
cast the catch is *rolled but not written* (``fishing_workflow.roll_cast``); a
managed background task waits a randomised delay, optionally fakes a nibble, then
arms the bite. The single **Reel** button resolves it:

* reel **before** the bite → you spooked it (a premature miss);
* reel **within the window** → landed — the catch is committed
  (``fishing_workflow.commit_catch``);
* reel **too late** / never → the fish gets away.

Owner decision 2026-06-22: a missed reel = the fish gets away (no catch, no
write). The window is generous on purpose — over Discord a reaction window is a
*presence check*, not a reflex test (see :mod:`utils.fishing.minigame`).

Mirrors the ``views/blackjack`` pattern: extends ``discord.ui.View`` directly
(specialised timed lifecycle), author-restricted, disable-on-terminal. Game
state is in-memory and not restart-safe (ADR-002, accepted for game views).
"""

from __future__ import annotations

import asyncio
import logging
import time

import discord

from core.runtime import tasks
from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import fishing_workflow
from utils.fishing import minigame
from utils.fishing.fish import SPECIES, max_size_rank_for_level
from utils.ui_constants import ERROR_COLOR, GAME_COLOR, SUCCESS_COLOR
from views.base import handle_view_error as _on_view_error

logger = logging.getLogger("bot.views.fishing")

#: In-flight casts keyed by ``(user_id, guild_id)`` — the soft-pacing guard so a
#: player can't run several casts at once (the cog checks this before starting).
#: In-memory only (ADR-002); cleared on every terminal path + on timeout.
active_casts: set[tuple[int, int]] = set()

#: Safety-net timeout — the loop resolves itself within ~delay + window (≈9 s);
#: this only fires if the background task never ran (e.g. spawn failed).
_VIEW_TIMEOUT = 30.0


class FishingCastView(discord.ui.View):
    def __init__(
        self,
        user_id: int,
        guild_id: int,
        cast: fishing_workflow.Cast,
    ) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT)
        self.user_id = user_id
        self.guild_id = guild_id
        self.cast = cast
        self.message: discord.Message | None = None

        self._armed = False  # the bite has landed → the window is open
        self._bite_at = 0.0  # monotonic timestamp of the bite
        self._resolved = False  # terminal reached (guards the background task)

    # ------------------------------------------------------------------ lifecycle

    def start(self) -> None:
        """Spawn the managed bite task. Called by the cog once ``message`` is set."""
        active_casts.add((self.user_id, self.guild_id))
        tasks.spawn(f"fishing:bite:{self.user_id}", self._run_bite())

    def _release(self) -> None:
        active_casts.discard((self.user_id, self.guild_id))

    async def _run_bite(self) -> None:
        """Wait → (maybe fake-out) → arm the bite → expire the window if ignored."""
        delay = minigame.roll_bite_delay()
        fakeout = minigame.roll_fakeout()

        if fakeout and delay - minigame.FAKEOUT_LEAD > minigame.BITE_DELAY_FLOOR:
            await asyncio.sleep(delay - minigame.FAKEOUT_LEAD)
            if self._resolved:
                return
            await self._edit_message(
                "🎣 *...something nibbles at the bait...*",
                GAME_COLOR,
            )
            await asyncio.sleep(minigame.FAKEOUT_LEAD)
        else:
            await asyncio.sleep(delay)
        if self._resolved:
            return

        # The bite — arm the window. Record the timestamp BEFORE the edit so the
        # network latency of the edit itself counts against the (generous)
        # window, exactly as the sim models it.
        self._armed = True
        self._bite_at = time.monotonic()
        self.reel_btn.label = "Reel it in!"
        self.reel_btn.style = discord.ButtonStyle.success
        await self._edit_message("🐟 **BITE!** Reel it in — quick!", SUCCESS_COLOR)

        await asyncio.sleep(minigame.REACTION_WINDOW)
        if self._resolved:
            return
        # Window elapsed with no reel → it got away.
        self._resolved = True
        self._release()
        await self._end_message(
            "🌊 *...the line goes slack. The fish got away.*",
            ERROR_COLOR,
        )
        self.stop()

    # ------------------------------------------------------------------ the button

    @discord.ui.button(label="🎣 Waiting for a bite…", style=discord.ButtonStyle.grey)
    async def reel_btn(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ) -> None:
        if self._resolved:
            await safe_defer(interaction)
            return

        if not self._armed:
            # Reeled before the bite — spooked it.
            self._resolved = True
            self._release()
            await self._end_interaction(
                interaction,
                "🌀 You reeled too early — the fish darted off. *Hold your nerve!*",
                ERROR_COLOR,
            )
            self.stop()
            return

        elapsed = time.monotonic() - self._bite_at
        self._resolved = True
        self._release()

        if not minigame.reel_is_in_time(elapsed):
            await self._end_interaction(
                interaction,
                "🌊 *...too slow. The fish got away.*",
                ERROR_COLOR,
            )
            self.stop()
            return

        # Landed it — commit the catch now (the audited write).
        if not await safe_defer(interaction):
            self.stop()
            return
        result = await fishing_workflow.commit_catch(
            self.user_id,
            self.guild_id,
            self.cast,
        )
        await self._finish_caught(interaction, result)
        self.stop()

    # ------------------------------------------------------------------ rendering

    async def _finish_caught(
        self,
        interaction: discord.Interaction,
        result: fishing_workflow.FishResult,
    ) -> None:
        if result.catch is None:
            await self._end_interaction(
                interaction,
                "🎣 The fishing spot is unavailable right now — try later.",
                ERROR_COLOR,
            )
            return
        species = result.catch.species
        trophy = minigame.is_trophy(species, result.fishing_level)
        title = "🏆 Trophy catch!" if trophy else "🎣 Caught it!"
        desc = (
            f"You reeled in {species.emoji} a **{species.name.title()}**!  "
            f"(size #{species.size_rank} of {len(SPECIES)})"
        )
        if result.unlocked_bigger:
            cap = max_size_rank_for_level(result.fishing_level)
            desc += (
                f"\n\n🌟 **Fishing level {result.fishing_level}!** "
                f"You can now catch fish up to size #{cap}."
            )
        if result.xp_note:
            desc += f"\n{result.xp_note}"
        embed = discord.Embed(
            title=title,
            description=desc,
            color=SUCCESS_COLOR,
        )
        embed.set_footer(text="!fish to cast again · !fishlog for your collection")
        self._disable()
        await safe_edit(interaction, embed=embed, view=self)

    def _disable(self) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]

    def _embed(self, text: str, color: discord.Color) -> discord.Embed:
        return discord.Embed(description=text, color=color)

    async def _edit_message(self, text: str, color: discord.Color) -> None:
        """Edit the anchor message from the background task (no interaction)."""
        if self.message is None:
            return
        try:
            await self.message.edit(embed=self._embed(text, color), view=self)
        except discord.HTTPException:
            logger.debug("fishing: bite edit failed (message gone)", exc_info=True)

    async def _end_message(self, text: str, color: discord.Color) -> None:
        """Terminal edit from the background task (disables the button)."""
        self._disable()
        await self._edit_message(text, color)

    async def _end_interaction(
        self,
        interaction: discord.Interaction,
        text: str,
        color: discord.Color,
    ) -> None:
        """Terminal edit from a button click."""
        self._disable()
        if not await safe_defer(interaction):
            return
        await safe_edit(interaction, embed=self._embed(text, color), view=self)

    # ------------------------------------------------------------------ guards

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "🎣 This isn't your line — cast your own with `!fish`.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        # Safety net only; the bite task normally resolves first and stop()s.
        if self._resolved:
            return
        self._resolved = True
        self._release()
        self._disable()
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        item: discord.ui.Item,  # type: ignore[type-arg]
    ) -> None:
        self._release()
        await _on_view_error(self, interaction, error, item)
