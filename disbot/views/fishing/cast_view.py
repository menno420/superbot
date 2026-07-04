"""The fishing cast minigame — ``cast → wait → BITE → reel`` + trophy reel-fight.

``FishingCastView`` turns the prefix-only instant catch into a skill moment
(owner design Q-0175; sim-backed numbers in :mod:`utils.fishing.minigame`).

On cast the catch is *rolled but not written* (``fishing_workflow.roll_cast``); a
managed background task waits a randomised delay, optionally fakes a nibble, then
arms the bite. The single **Reel** button resolves it:

* reel **before** the bite → you spooked it;
* reel **within the window** → hooked it;
* reel **too late** / never → the fish gets away.

For an **ordinary** fish, hooking it lands the catch (committed via
``fishing_workflow.commit_catch``). For a **trophy** (the top of your unlocked
band — the owner's "hybrid" decision), hooking it starts a short **reel-fight**:
a few more timed reel taps, each its own presence-check window, and each able to
let the fish snap free with a small escape chance. Land every tap → the trophy is
yours; miss a window or get snapped → it gets away. Owner decision 2026-06-22: a
missed reel = the fish gets away (no catch, no write).

Every window is generous on purpose — over Discord a reaction window is a
*presence check*, not a reflex test. Mirrors the ``views/blackjack`` pattern:
extends ``discord.ui.View`` directly (specialised timed lifecycle),
author-restricted, disable-on-terminal. Game state is in-memory and not
restart-safe (ADR-002, accepted for game views).

Concurrency note: each armed window carries a ``_round_id`` token. A reel tap
bumps the token (and re-arms via a fresh task), so the *previous* round's
background task — which may still be sleeping out its window — sees a stale token
on wake and exits instead of false-failing the fish.
"""

from __future__ import annotations

import asyncio
import logging
import time

import discord

from core.runtime import tasks
from core.runtime.interaction_helpers import safe_defer, safe_edit
from services import fishing_workflow
from utils.fishing import energy, minigame
from utils.fishing import rods as rods_mod
from utils.fishing import venue as venue_mod
from utils.fishing import weather as weather_mod
from utils.fishing.fish import max_size_rank_for_level, species_for_venue
from utils.ui_constants import ERROR_COLOR, GAME_COLOR, SUCCESS_COLOR
from views.base import HubView
from views.base import handle_view_error as _on_view_error

logger = logging.getLogger("bot.views.fishing")

#: In-flight casts keyed by ``(user_id, guild_id)`` — the soft-pacing guard so a
#: player can't run several casts at once (the cog checks this before starting).
#: In-memory only (ADR-002); cleared on every terminal path + on timeout.
active_casts: set[tuple[int, int]] = set()

#: Safety-net timeout — the loop resolves itself within the bite (~9 s) plus a
#: bounded fight (≤ 4 × ~3.3 s); this only fires if a background task never ran.
_VIEW_TIMEOUT = 45.0

_PHASE_BITE = "bite"
_PHASE_FIGHT = "fight"


def _tension_bar(done: int, total: int) -> str:
    """A tiny reel-progress bar, e.g. ``▰▰▱▱`` (2 of 4 reeled in)."""
    done = max(0, min(done, total))
    return "▰" * done + "▱" * (total - done)


async def prepare_cast(
    user_id: int,
    guild_id: int,
) -> tuple[discord.Embed, FishingCastView] | str:
    """Set up a cast: active-guard → equipped rod → roll → the view + opening embed.

    The single source of truth shared by the ``!fish`` command and the fishing
    menu's Cast button. Returns ``(embed, view)`` ready to send (the caller sets
    ``view.message`` then calls ``view.start()``), or a player-facing string when
    a cast can't begin (already casting / out of energy / catalog unavailable).
    """
    if (user_id, guild_id) in active_casts:
        return "🎣 You've already got a line in the water — reel that one in first!"
    start = await fishing_workflow.begin_cast(user_id, guild_id)
    if not start.ok or start.cast is None:
        return start.message or "🎣 You can't cast right now — try later."
    view = FishingCastView(
        user_id,
        guild_id,
        start.cast,
        rod=start.rod,
        bite_speed=start.effective_bite_speed,
        profile=start.venue_profile,
    )
    profile = start.venue_profile
    where = (
        "from the boat, out over the deep water"
        if profile.key == venue_mod.DEEPWATER
        else "from the shoreline"
    )
    embed = discord.Embed(
        description=(
            f"You cast a line {where}… {profile.emoji}\n"
            "*Watch the water — hit **Reel** the moment it bites, but not before!*"
        ),
        color=GAME_COLOR,
    )
    w = start.weather
    if w.bite_speed_mult != 1.0 or w.rarity_mult != 1.0:
        # Only show the forecast when it actually changes the cast (clear = silent).
        embed.add_field(
            name=f"{w.emoji} {w.name}",
            value=f"*{w.blurb}* ({weather_mod.effect_text(w)})",
            inline=False,
        )
    footer = f"{profile.emoji} {profile.name} · " + energy.bar(start.energy_current)
    if start.bait_used is not None:
        footer += (
            f" · {start.bait_used.emoji} {start.bait_used.name} "
            f"({start.bait_charges_left} left)"
        )
    if start.fishing_gear_bonus:
        # Equipped fishing gear is biasing this cast (rarer catches + quicker
        # bites) — its stats are already folded into the roll / bite speed.
        footer += " · 🎣 fishing gear"
    if start.tide_pool_bonus:
        # A built Tide Pool is nudging this cast toward rarer fish (its pull
        # bonus is already folded into the roll).
        footer += " · 🪸 tide pool"
    if start.dock_bonus:
        # A built Dock is speeding up the bite (its bite-speed bonus is already
        # folded into effective_bite_speed).
        footer += " · ⚓ dock"
    embed.set_footer(text=footer)
    return embed, view


class FishingCastView(discord.ui.View):
    def __init__(
        self,
        user_id: int,
        guild_id: int,
        cast: fishing_workflow.Cast,
        rod: rods_mod.Rod | None = None,
        bite_speed: float | None = None,
        profile: venue_mod.VenueProfile | None = None,
    ) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT)
        self.user_id = user_id
        self.guild_id = guild_id
        self.cast = cast
        self.rod = rod or rods_mod.STARTER
        #: The venue this cast runs at — its profile carries the bite band,
        #: base reaction window, and base escape the deep makes far higher.
        self._profile = profile or venue_mod.profile_for(cast.venue)
        #: The rod's window bonus widens every reaction window (bite + each fight
        #: tap) — the fairness knob, so a weak connection on a good rod is comfy.
        #: The base window is the venue's (deepwater's is a touch tighter, but a
        #: rod buys it back — the design's "rod expected" deepwater window).
        self._window = self._profile.reaction_window + self.rod.window_bonus
        #: The bite-wait multiplier (≤ 1 = faster). ``begin_cast`` compounds the
        #: rod's ``bite_speed`` with any loaded bait's and passes it here; the
        #: direct ``!fish``/test path falls back to the rod's own knob.
        self._bite_speed = self.rod.bite_speed if bite_speed is None else bite_speed
        self.message: discord.Message | None = None

        self._phase = _PHASE_BITE
        self._armed = False  # a window is currently open
        self._armed_at = 0.0  # monotonic timestamp the current window opened
        self._round_id = 0  # staleness token (see module docstring)
        self._resolved = False  # terminal reached
        self._taps_total = 0  # reel-fight length (trophy only)
        self._taps_left = 0
        self._grace_used = False  # the rod's one premature-reel forgiveness, spent

    # ------------------------------------------------------------------ lifecycle

    def start(self) -> None:
        """Spawn the managed bite task. Called by the cog once ``message`` is set."""
        active_casts.add((self.user_id, self.guild_id))
        tasks.spawn(f"fishing:bite:{self.user_id}", self._run_bite())

    def _release(self) -> None:
        active_casts.discard((self.user_id, self.guild_id))

    async def _arm(self, text: str, color: discord.Color, label: str) -> int:
        """Open a reaction window: bump the token, render the prompt, return the id."""
        self._round_id += 1
        self._armed = True
        self._armed_at = time.monotonic()
        # Record the timestamp BEFORE the edit so the edit's own network latency
        # counts against the (generous) window, exactly as the sim models it.
        self.reel_btn.label = label
        self.reel_btn.style = discord.ButtonStyle.success
        await self._edit_message(text, color)
        return self._round_id

    async def _run_bite(self) -> None:
        """Wait → (maybe fake-out) → arm the bite → expire the window if ignored."""
        delay = minigame.roll_bite_delay(
            speed=self._bite_speed,
            lo=self._profile.bite_delay_min,
            hi=self._profile.bite_delay_max,
            floor=self._profile.bite_delay_floor,
        )
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

        my_id = await self._arm(
            "🐟 **BITE!** Reel it in — quick!",
            SUCCESS_COLOR,
            "Reel it in!",
        )
        await asyncio.sleep(self._window)
        if self._resolved or self._round_id != my_id:
            return
        await self._fail(
            self._got_away("🌊 *...the line goes slack. The fish got away.*"),
        )

    async def _run_fight_round(self) -> None:
        """One reel-fight round: a suspense beat, arm the tap, expire if ignored."""
        await asyncio.sleep(minigame.FIGHT_INTER_ROUND_DELAY)
        if self._resolved:
            return
        bar = _tension_bar(self._taps_total - self._taps_left, self._taps_total)
        my_id = await self._arm(
            f"💪 **It's a big one — it dives!** Keep reeling!\n`{bar}`",
            GAME_COLOR,
            "Reel!",
        )
        await asyncio.sleep(self._window)
        if self._resolved or self._round_id != my_id:
            return
        await self._fail(
            self._got_away(
                "🌊 You let the line go slack — it thrashed free and escaped.",
            ),
        )

    # ------------------------------------------------------------------ the button

    def _got_away(self, text: str) -> str:
        """A 'got away' line, with a trophy clue appended when a big one escaped.

        Soft-fail UX (the design's "Other ideas"): if the fish on the line was a
        trophy, name it so the loss baits the next cast (``minigame.escape_clue``)
        instead of a flat denial. Ordinary fish keep the plain *text*.
        """
        species = self.cast.catch.species if self.cast.catch else None
        if species is None:
            return text
        clue = minigame.escape_clue(species, self.cast.level_before)
        return f"{text}\n{clue}" if clue else text

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
            if self._phase == _PHASE_BITE:
                # Reeled before the bite. A good rod's premature_grace can forgive
                # one such slip per cast — the line stays in the water and the real
                # bite still comes (the still-running bite task arms it). A second
                # slip, or a bare rod (grace 0), spooks the fish for good.
                if not self._grace_used and minigame.roll_premature_grace(
                    self.rod.premature_grace,
                ):
                    self._grace_used = True
                    await safe_defer(interaction)
                    await self._edit_message(
                        "😅 *You twitch the rod too soon — but the "
                        f"{self.rod.name} steadies it. The line's still in the "
                        "water… hold your nerve.*",
                        GAME_COLOR,
                    )
                else:
                    # Spooked it (no grace left / bare rod).
                    await self._terminate_interaction(
                        interaction,
                        "🌀 You reeled too early — the fish darted off. "
                        "*Hold your nerve!*",
                    )
            else:
                # Between fight rounds — ignore the extra mash.
                await safe_defer(interaction)
            return

        # A window is open. Disarm it and bump the token so the round's task,
        # which is still sleeping out its window, exits instead of false-failing.
        elapsed = time.monotonic() - self._armed_at
        self._armed = False
        self._round_id += 1

        if not minigame.reel_is_in_time(elapsed, self._window):
            await self._terminate_interaction(
                interaction,
                self._got_away("🌊 *...too slow. The fish got away.*"),
            )
            return

        if self._phase == _PHASE_BITE:
            await self._on_hooked(interaction)
        else:
            await self._on_fight_tap(interaction)

    async def _on_hooked(self, interaction: discord.Interaction) -> None:
        """A successful initial reel: ordinary → land it, trophy → start the fight."""
        species = self.cast.catch.species if self.cast.catch else None
        if species is not None and minigame.is_trophy(species, self.cast.level_before):
            self._phase = _PHASE_FIGHT
            self._taps_total = minigame.reel_fight_taps(species)
            self._taps_left = self._taps_total
            if not await safe_defer(interaction):
                self._terminate_silent()
                return
            await safe_edit(
                interaction,
                embed=self._embed(
                    "🎣 **Hooked a big one!** It dives deep — hang on…",
                    GAME_COLOR,
                ),
                view=self,
            )
            tasks.spawn(f"fishing:fight:{self.user_id}", self._run_fight_round())
            return
        await self._land_catch(interaction)

    async def _on_fight_tap(self, interaction: discord.Interaction) -> None:
        """A successful in-time fight tap: maybe snap free, else advance / land."""
        species = self.cast.catch.species if self.cast.catch else None
        if species is not None and minigame.roll_escape(
            species,
            escape_resist=self.rod.escape_resist,
            base_escape=self._profile.base_escape,
        ):
            await self._terminate_interaction(
                interaction,
                self._got_away(
                    "💥 It gave one last thrash, **snapped the line**, and bolted!",
                ),
            )
            return

        self._taps_left -= 1
        if self._taps_left <= 0:
            await self._land_catch(interaction)
            return

        if not await safe_defer(interaction):
            self._terminate_silent()
            return
        bar = _tension_bar(self._taps_total - self._taps_left, self._taps_total)
        await safe_edit(
            interaction,
            embed=self._embed(f"💪 Reeling it in… `{bar}`", GAME_COLOR),
            view=self,
        )
        tasks.spawn(f"fishing:fight:{self.user_id}", self._run_fight_round())

    async def _land_catch(self, interaction: discord.Interaction) -> None:
        """Commit the (now fully reeled) catch — the audited write — and finish."""
        if not await safe_defer(interaction):
            self._terminate_silent()
            return
        result = await fishing_workflow.commit_catch(
            self.user_id,
            self.guild_id,
            self.cast,
        )
        await self._finish_caught(interaction, result)

    # ------------------------------------------------------------------ rendering

    async def _finish_caught(
        self,
        interaction: discord.Interaction,
        result: fishing_workflow.FishResult,
    ) -> None:
        self._resolved = True
        self._release()
        if result.catch is None:
            await self._terminate_interaction(
                interaction,
                "🎣 The fishing spot is unavailable right now — try later.",
                already_terminal=True,
            )
            return
        species = result.catch.species
        trophy = minigame.is_trophy(species, result.fishing_level)
        pool_size = len(species_for_venue(species.venue))
        title = "🏆 Trophy landed!" if trophy else "🎣 Caught it!"
        desc = (
            f"You reeled in {species.emoji} a **{species.name.title()}**!  "
            f"(size #{species.size_rank} of {pool_size} {self._profile.name.lower()})"
        )
        if result.weight > 0:
            desc += f"\n⚖️ It weighs **{result.weight:g} kg**."
            if result.new_personal_best:
                desc += " 🏅 **New personal best!**"
        if result.bonus_catch:
            desc += (
                f"\n🍀 **Lucky double catch!** A second {species.emoji} "
                f"**{species.name.title()}** for the craft bin."
            )
        if result.pearl_found:
            desc += (
                "\n🦪 **A pearl!** A rare crafting material — save them up to "
                "craft the premium **Royal Feast** bait (`!craftpearl`)."
            )
        if result.coral_found:
            desc += (
                "\n🪸 **A piece of coral!** A rare deepwater find — carve it into "
                "cosmetic curios for your collection (`!curios`)."
            )
        if result.unlocked_bigger:
            cap = max_size_rank_for_level(result.fishing_level, species.venue)
            desc += (
                f"\n\n🌟 **Fishing level {result.fishing_level}!** "
                f"You can now catch fish up to size #{cap}."
            )
        if result.xp_note:
            desc += f"\n{result.xp_note}"
        embed = discord.Embed(title=title, description=desc, color=SUCCESS_COLOR)
        embed.set_footer(text="🎣 Cast again · !fishlog for your collection")
        # Hand off to the terminal continuation view (Cast again + standard nav)
        # so a landed catch is never a dead-end (owner directive 2026-06-23).
        await safe_edit(
            interaction,
            embed=embed,
            view=_FishingDoneView(interaction.user, self.guild_id),
        )
        self.stop()

    def _disable(self) -> None:
        for item in self.children:
            item.disabled = True  # type: ignore[attr-defined]

    def _embed(self, text: str, color: discord.Color) -> discord.Embed:
        return discord.Embed(description=text, color=color)

    async def _edit_message(self, text: str, color: discord.Color) -> None:
        """Edit the anchor message from a background task (no interaction)."""
        if self.message is None:
            return
        try:
            await self.message.edit(embed=self._embed(text, color), view=self)
        except discord.HTTPException:
            logger.debug("fishing: window edit failed (message gone)", exc_info=True)

    async def _fail(self, text: str) -> None:
        """Terminal 'got away' from a background task (window expired)."""
        self._resolved = True
        self._release()
        self._disable()
        await self._edit_message(text, ERROR_COLOR)
        self.stop()

    async def _terminate_interaction(
        self,
        interaction: discord.Interaction,
        text: str,
        *,
        already_terminal: bool = False,
    ) -> None:
        """Terminal edit from a button click (got away / spooked / snapped)."""
        if not already_terminal:
            self._resolved = True
            self._release()
        if not await safe_defer(interaction):
            self.stop()
            return
        # Continuation view (Cast again + standard nav) — even a fish that got
        # away leaves the player one click from another cast, the hub, and Help.
        await safe_edit(
            interaction,
            embed=self._embed(text, ERROR_COLOR),
            view=_FishingDoneView(interaction.user, self.guild_id),
        )
        self.stop()

    def _terminate_silent(self) -> None:
        """Tear down when the interaction token died and no edit is possible."""
        self._resolved = True
        self._release()
        self.stop()

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
        # Safety net only; a background task normally resolves first and stop()s.
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


class _FishingDoneView(HubView):
    """Terminal screen after a cast resolves — never a dead-end.

    A ``HubView`` with ``SUBSYSTEM = "fishing"`` so
    :func:`views.navigation.attach_standard_nav` auto-attaches **📚 Help** and
    **↩ Games** — the player is one click from the Games hub and Help. The
    **🎣 Cast again** button re-runs :func:`prepare_cast`, mirroring
    ``FishingMenuView.cast_btn`` so a landed (or escaped) catch flows straight
    into the next cast.
    """

    SUBSYSTEM = "fishing"

    def __init__(self, author: discord.Member | discord.User, guild_id: int) -> None:
        super().__init__(author)
        self.guild_id = guild_id

    @discord.ui.button(
        label="Cast again",
        emoji="🎣",
        style=discord.ButtonStyle.success,
        custom_id="fishing_done:cast_again",
        row=0,
    )
    async def cast_again(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        prepared = await prepare_cast(self._author.id, self.guild_id)
        if isinstance(prepared, str):
            await interaction.response.send_message(prepared, ephemeral=True)
            return
        embed, view = prepared
        await interaction.response.edit_message(embed=embed, view=view)
        view.message = interaction.message
        view.start()
        self.stop()
