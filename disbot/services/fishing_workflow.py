"""Fishing workflow service — the audited write boundary for fishing.

Owner design Q-0175 (``docs/planning/fishing-open-world-expansion-plan-2026-06-18.md``):
fishing v1 is a **level-gated catch** — the player's fishing level (derived from
their per-game ``GAME_FISHING`` xp, reusing the shared ``game_xp`` system) gates
which size band of fish they can catch; each level unlocks +3 bigger fish.
**Fish value/use is an explicitly OPEN owner question, so v1 pays no coins** —
the reward is progression (level up → unlock bigger fish) + the collection log.

Mirrors ``services/mining_workflow.py`` (RS02 / Q-0071): the catch-log write +
the xp award commit inside ONE ``db.transaction()`` from conn-aware ``utils/db``
primitives; EventBus emission happens **after** commit. The catch math is pure
(``utils/fishing``); this service sequences the read → roll → atomic writes →
post-commit events.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Protocol

from core.events import bus
from services import economy_service, game_xp_service
from utils import db
from utils.fishing import (
    CORAL_ITEM,
    MAX_LEVEL,
    PEARL_ITEM,
    Catch,
)
from utils.fishing import bait as bait_mod
from utils.fishing import curios as curios_mod
from utils.fishing import energy as fish_energy
from utils.fishing import fish as fish_mod
from utils.fishing import gear as fishing_gear
from utils.fishing import rewards as rewards_mod
from utils.fishing import rods as rods_mod
from utils.fishing import (
    roll_bonus_catch,
    roll_catch,
    roll_coral_drop,
    roll_pearl_drop,
)
from utils.fishing import venue as venue_mod
from utils.fishing import weather as weather_mod
from utils.mining import character
from utils.mining import structures as structures_mod

logger = logging.getLogger("bot.fishing_workflow")

#: Audit/event reason tag for a rod purchase (mirrors mining's "<game>:<action>").
ROD_PURCHASE_REASON = "fishing:rod_purchase"
#: Audit/event reason tag for a bait purchase (the second fishing coin sink).
BAIT_PURCHASE_REASON = "fishing:bait_purchase"


def fishing_level_from_xp(fishing_xp: int) -> int:
    """The player's fishing level (1…MAX_LEVEL) from their fishing xp total.

    Reuses the shared game-xp level curve (``db.level_progress``) rather than
    inventing a parallel system (the owner's "reuse game_xp" directive), capped
    at MAX_LEVEL (= 7 size bands). The *shape* of leveling — a dedicated rod-tier
    ladder vs. this skill-xp derivation — is an OPEN owner question (Q-0175); this
    is the deferrable v1 choice.
    """
    level_index, _, _ = db.level_progress(max(0, fishing_xp))
    return min(MAX_LEVEL, 1 + level_index)


@dataclass(frozen=True)
class FishResult:
    """One cast — the rolled catch plus the progression it produced."""

    catch: Catch | None
    #: The player's fishing level after this cast (1…MAX_LEVEL).
    fishing_level: int
    #: True when this cast crossed a fishing level → bigger fish just unlocked.
    unlocked_bigger: bool = False
    #: Inline shared-game level-up notice (set only when that crossed a level).
    xp_note: str | None = None
    #: This catch's individual weight in kg (0 when there was no catch).
    weight: float = 0.0
    #: True when this catch beat the player's previous heaviest of the species
    #: (a new trophy record) — drives the "🏆 New personal best!" celebration.
    new_personal_best: bool = False
    #: True when the lucky-double-catch bonus fired — the reel landed a **second**
    #: copy of the same fish (extra craft fodder). Inventory-only; never a second
    #: dex/trophy row. Byte-identical economics when ``False``.
    bonus_catch: bool = False
    #: True when this reel also yielded a **pearl** — the rare crafting material
    #: (``utils.fishing.PEARL_ITEM``) that crafts the premium Royal Feast bait.
    #: Granted into the inventory; never a dex/trophy row. Byte-identical when
    #: ``False``. Bigger fish drop pearls more often (size-scaled roll).
    pearl_found: bool = False
    #: True when this reel also yielded a **coral** — the second rare crafting
    #: material (``utils.fishing.CORAL_ITEM``), a **deepwater-only** reef find that
    #: carves into the cosmetic curio collection (``utils.fishing.curios``).
    #: Granted into the inventory; never a dex/trophy row. Always ``False`` on a
    #: shore cast; byte-identical economics when ``False``.
    coral_found: bool = False


@dataclass(frozen=True)
class Cast:
    """A cast in progress — the fish on the line, *before* it is committed.

    The minigame (``views/fishing``) rolls the catch at cast time so it knows
    what is biting, then commits it only if the player successfully reels in
    (owner decision 2026-06-22: a missed reel = the fish gets away, no write).
    The instant ``fish()`` below rolls + commits in one go for the legacy path.
    """

    catch: Catch | None
    #: The player's fishing level at cast time (gates the roll + the catch math).
    level_before: int
    #: The venue this cast was made in (``shore`` / ``deepwater``) — picks the
    #: species pool + the minigame difficulty (``utils.fishing.venue``).
    venue: str = venue_mod.SHORE
    #: The lucky-double-catch chance fixed at cast time — a built **Fishery**
    #: structure raises it above ``rewards.BONUS_CATCH_CHANCE`` (``commit_catch``
    #: rolls it). Defaults to the base chance so a hand-built ``Cast`` (and the
    #: legacy path) is byte-identical.
    double_catch_chance: float = rewards_mod.BONUS_CATCH_CHANCE


async def roll_cast(
    user_id: int,
    guild_id: int,
    rod: rods_mod.Rod | None = None,
    *,
    rarity_pull: float | None = None,
    venue: str = venue_mod.SHORE,
    double_catch_chance: float | None = None,
) -> Cast:
    """Read the player's level and roll a catch **without writing anything**.

    The read-only half of a cast: the minigame calls this when the line goes
    out, holds the rolled :class:`Cast`, and only calls :func:`commit_catch`
    once the reel succeeds. Returns ``Cast(catch=None, …)`` if the catalog
    failed to load (no species) — the caller surfaces an honest empty result.

    *rod* (defaulting to the starter) applies its ``rarity_pull`` knob: a better
    rod biases the catch toward the big end of the *same* unlocked band — never a
    new band (that stays the fishing-level axis). *rarity_pull*, when given,
    overrides the rod's own pull — ``begin_cast`` passes ``rod.rarity_pull``
    multiplied by any loaded bait so the two how-well knobs compound.

    *double_catch_chance*, when given, is the fishery-adjusted lucky-double-catch
    chance ``begin_cast`` computed from its one structures read (so the read isn't
    repeated at commit). When ``None`` (the legacy ``fish()`` seam, which has no
    runtime callers), it defaults to the base ``rewards.BONUS_CATCH_CHANCE`` — i.e.
    the Fishery bonus is applied through ``begin_cast``, the real cast path.
    """
    rod = rod or rods_mod.STARTER
    venue = venue_mod.normalize(venue)
    pull = rod.rarity_pull if rarity_pull is None else rarity_pull
    xp_map = await db.get_game_xp(user_id, guild_id)
    fishing_xp_before = xp_map.get(game_xp_service.GAME_FISHING, 0)
    level_before = fishing_level_from_xp(fishing_xp_before)
    catch = roll_catch(level_before, rarity_pull=pull, venue=venue)
    if catch is None:
        logger.error("fishing: no catchable species (venue=%s, catalog empty?)", venue)
    if double_catch_chance is None:
        double_catch_chance = rewards_mod.BONUS_CATCH_CHANCE
    return Cast(
        catch=catch,
        level_before=level_before,
        venue=venue,
        double_catch_chance=double_catch_chance,
    )


async def commit_catch(
    user_id: int,
    guild_id: int,
    cast: Cast,
    *,
    rng: random.Random | None = None,
) -> FishResult:
    """Commit a successfully-reeled cast: log it + grant the item + award xp.

    The audited write boundary (RS02 / Q-0071): the catch-log write, the
    inventory grant, and the xp award all run on ONE workflow-owned
    ``db.transaction()`` connection; the xp event emits only after commit. A
    ``cast`` with no ``catch`` (empty catalog) writes nothing.

    Rolls the **lucky-double-catch** bonus (``utils.fishing.roll_bonus_catch``) at
    commit time — only a *landed* catch can double — so on a lucky reel the
    inventory grant is **2** of the species instead of 1 (extra craft fodder).
    Also rolls a **pearl drop** (``utils.fishing.roll_pearl_drop``, size-scaled):
    a rare crafting material granted alongside the fish, on the same transaction.
    The dex/leaderboard row is unaffected by either (still the single heaviest
    weight); *rng* is injectable for seed-determinism in tests — the bonus roll
    is drawn first, then the pearl roll.
    """
    catch = cast.catch
    level_before = cast.level_before
    if catch is None:
        return FishResult(catch=None, fishing_level=level_before)

    # The double-catch chance was fixed at cast time (``roll_cast``) — a built
    # **Fishery** (4th coral structure, coral's yield/abundance sink) raises it above
    # the base ``BONUS_CATCH_CHANCE``; unbuilt ⇒ exactly the base ⇒ byte-identical
    # catch economics. The bonus roll is still drawn first, so the pearl/coral draws
    # below stay deterministic under an injected rng.
    bonus = roll_bonus_catch(rng, chance=cast.double_catch_chance)
    grant = 2 if bonus else 1
    pearl = roll_pearl_drop(catch.species.size_rank, rng)
    coral = roll_coral_drop(cast.venue, rng)
    async with db.transaction() as conn:
        prev_best = await db.record_catch(
            user_id,
            guild_id,
            catch.species.name,
            catch.weight,
            conn=conn,
        )
        # The rare-material drops (pearl, coral) are granted before the fish so the
        # fish grant stays the last write — a stable seam for callers/tests that
        # read the species-grant call. Inventory-only, same atomic catch
        # transaction (RS02); neither is ever a dex/trophy row. The rolls are
        # drawn (bonus → pearl → coral) before the transaction so the write set is
        # deterministic under an injected rng.
        if pearl:
            await db.update_mining_item(
                str(user_id),
                guild_id,
                PEARL_ITEM,
                1,
                conn=conn,
            )
        # Coral is deepwater-only (roll_coral_drop returns False on shore), the
        # boat venue's unique reward — it carves into the cosmetic curio set.
        if coral:
            await db.update_mining_item(
                str(user_id),
                guild_id,
                CORAL_ITEM,
                1,
                conn=conn,
            )
        # The caught fish is now a tangible inventory item (owner decision
        # 2026-06-22): sellable for coins via the market, and cookable into food
        # at a campfire (mining_workflow.cook). The catch-log row above stays the
        # dex/leaderboard record; this grant makes the fish usable — same atomic
        # catch transaction, conn-composed (RS02). A lucky double-catch grants 2.
        await db.update_mining_item(
            str(user_id),
            guild_id,
            catch.species.name,
            grant,
            conn=conn,
        )
        award = await game_xp_service.award(
            guild_id,
            user_id,
            game=game_xp_service.GAME_FISHING,
            action="fish",
            conn=conn,
        )
    if award is not None:
        await game_xp_service.emit_award_events(award)
        level_after = fishing_level_from_xp(award.game_total)
    else:
        level_after = level_before
    new_best = catch.weight > 0 and (prev_best is None or catch.weight > prev_best)
    return FishResult(
        catch=catch,
        fishing_level=level_after,
        unlocked_bigger=level_after > level_before,
        xp_note=award.note if award is not None and award.leveled_up else None,
        weight=catch.weight,
        new_personal_best=new_best,
        bonus_catch=bonus,
        pearl_found=pearl,
        coral_found=coral,
    )


async def fish(user_id: int, guild_id: int) -> FishResult:
    """One instant cast: roll a catch from the unlocked band + commit it.

    The legacy / non-interactive path (kept for the shared-game seam and tests).
    The interactive minigame instead calls :func:`begin_cast` then
    :func:`commit_catch` so the write happens only on a successful reel.
    """
    cast = await roll_cast(user_id, guild_id)
    return await commit_catch(user_id, guild_id, cast)


# ---------------------------------------------------------------------------
# Energy pacing — a separate fishing-energy bar that throttles casting (Q-0175)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CastStart:
    """The outcome of trying to begin a cast — energy gated, then rolled."""

    ok: bool
    message: str | None = None  # player-facing reason when ``ok`` is False
    cast: Cast | None = None
    rod: rods_mod.Rod = rods_mod.STARTER
    #: Energy remaining after the (successful) cast — for the ⚡ gauge.
    energy_current: int = 0
    #: The bite-wait multiplier this cast runs at — ``rod.bite_speed`` compounded
    #: with any loaded bait's (≤ 1 = faster). The cast view paces its bite on it.
    effective_bite_speed: float = 1.0
    #: The bait consumed by this cast (``None`` = fished bait-less), for the
    #: 🪱 cast-panel note. Its ``rarity_pull`` was already applied to the roll.
    bait_used: bait_mod.Bait | None = None
    #: Bait charges remaining after this cast spent one (0 = pack just ran out).
    bait_charges_left: int = 0
    #: The venue profile this cast runs at — the source of the bite band, reaction
    #: window, and base escape the cast view feeds into the minigame math.
    venue_profile: venue_mod.VenueProfile = venue_mod.SHORE_PROFILE
    #: The day's weather, already compounded into ``effective_bite_speed`` /
    #: the roll's rarity pull — carried for the cast-panel forecast note.
    weather: weather_mod.Weather = weather_mod.CONDITIONS[0]
    #: Whether the player's equipped gear contributed a fishing bonus (its
    #: ``fishing_power``/``bite_luck`` are already folded into the roll pull /
    #: ``effective_bite_speed``) — for the 🎣 cast-panel note. ``False`` when no
    #: fishing gear is equipped, in which case the cast is byte-identical.
    fishing_gear_bonus: bool = False
    #: Whether a built **Tide Pool** structure biased this cast toward rarer fish
    #: (its rarity-pull bonus is already folded into the roll pull) — for the 🪸
    #: cast-panel note. ``False`` when the Tide Pool is unbuilt (level 0), in which
    #: case that knob is ×1.0 and the cast is byte-identical.
    tide_pool_bonus: bool = False
    #: Whether a built **Dock** structure sped up this cast's bite (its bite-speed
    #: multiplier is already folded into ``effective_bite_speed``) — for the ⚓
    #: cast-panel note. ``False`` when the Dock is unbuilt (level 0).
    dock_bonus: bool = False
    #: Whether a built **Fishery** structure raised this cast's double-catch chance
    #: (already fixed onto ``cast.double_catch_chance``) — for the 🐟 cast-panel
    #: note. ``False`` when the Fishery is unbuilt (level 0), in which case the
    #: chance is exactly ``rewards.BONUS_CATCH_CHANCE`` and the cast is byte-identical.
    fishery_bonus: bool = False


def _fmt_wait(seconds: int) -> str:
    """Human "ready in" — ``45s`` / ``2m 05s``."""
    if seconds < 60:
        return f"{seconds}s"
    return f"{seconds // 60}m {seconds % 60:02d}s"


async def get_energy(user_id: int, guild_id: int) -> int:
    """The player's *settled* current fishing energy (for the ⚡ gauge / menu).

    Settles at the player's Boathouse-adjusted regen interval so the gauge matches the
    faster refill a built Boathouse grants (unbuilt ⇒ REGEN_SECONDS ⇒ byte-identical).
    """
    now = int(time.time())
    built = await db.get_structures(user_id, guild_id)
    regen_seconds = fish_energy.regen_seconds_for(
        structures_mod.boathouse_regen_mult(built.get(structures_mod.BOATHOUSE, 0)),
    )
    cur, ts = await db.get_fishing_energy(user_id, guild_id)
    return fish_energy.settle(
        fish_energy.EnergyState(cur, ts),
        now,
        regen_seconds=regen_seconds,
    ).current


async def get_active_bait(
    user_id: int,
    guild_id: int,
) -> tuple[bait_mod.Bait | None, int]:
    """The player's loaded ``(bait, charges)`` (``(None, 0)`` when none/unknown).

    Resolves the stored bait key to a :class:`~utils.fishing.bait.Bait`; a stale
    key (catalog entry removed) or non-positive charges both read as no bait.
    """
    key, charges = await db.get_active_bait(user_id, guild_id)
    bait = bait_mod.bait_by_key(key)
    if bait is None or charges <= 0:
        return None, 0
    return bait, charges


async def begin_cast(user_id: int, guild_id: int) -> CastStart:
    """Energy-gate a cast: settle → (out of energy?) → spend → roll.

    Spends one fishing energy per *attempt* (the pacing brake — a missed reel
    still costs, exactly like a dig). Energy is direct game state (no audit, like
    mining energy). Energy is only spent once a catch is actually rolled, so a
    catalog-load failure never charges the player.
    """
    now = int(time.time())
    # One structures read serves every structure knob (Tide Pool / Dock below) *and*
    # the Boathouse's energy-regen speed-up, which must be known before the energy
    # settle so the out-of-energy gate + "ready in" wait already reflect it. A built
    # Boathouse shortens the regen interval; unbuilt (level 0) ⇒ ×1.0 ⇒ exactly
    # REGEN_SECONDS ⇒ byte-identical energy.
    built = await db.get_structures(user_id, guild_id)
    regen_seconds = fish_energy.regen_seconds_for(
        structures_mod.boathouse_regen_mult(built.get(structures_mod.BOATHOUSE, 0)),
    )
    cur, ts = await db.get_fishing_energy(user_id, guild_id)
    state = fish_energy.EnergyState(cur, ts)
    settled = fish_energy.settle(state, now, regen_seconds=regen_seconds)
    if settled.current < fish_energy.CAST_COST:
        wait = fish_energy.seconds_until(
            state,
            now,
            fish_energy.CAST_COST,
            regen_seconds=regen_seconds,
        )
        return CastStart(
            ok=False,
            message=(
                "🎣 You're out of energy — let the line rest. "
                f"Ready to cast again in **{_fmt_wait(wait)}**."
            ),
            energy_current=settled.current,
        )

    rod = rods_mod.rod_for_tier(await db.get_rod_tier(user_id, guild_id))
    venue = await db.get_fishing_venue(user_id, guild_id)
    profile = venue_mod.profile_for(venue)
    weather = weather_mod.current_weather()
    bait, bait_charges = await get_active_bait(user_id, guild_id)
    # The 4th "how-well" knob: equipped fishing gear (Q-0175 / V-14). Read the
    # character's gear+skill stats and fold fishing_power → rarity pull and
    # bite_luck → bite speed. No fishing gear ⇒ both multipliers are 1.0 ⇒ the
    # cast is byte-identical to the pre-gear behaviour (additive safety property).
    gear_stats = character.character_stats(
        await db.get_equipment(str(user_id), guild_id),
        await db.get_skills(user_id, guild_id),
    )
    gear_pull = fishing_gear.fishing_pull_mult(gear_stats)
    gear_bite_speed = fishing_gear.fishing_bite_speed_mult(gear_stats)
    # The structure knobs: the built **Tide Pool** (rarity-pull, coral's functional
    # sink) and its sibling the **Dock** (bite-speed). Both default to their neutral
    # multiplier when unbuilt (level 0) ⇒ ×1.0 ⇒ byte-identical, exactly like the
    # gear knob's additive-safety property. ``built`` was read once above (it also
    # feeds the Boathouse regen speed-up).
    tide_pool_level = built.get(structures_mod.TIDE_POOL, 0)
    tide_pool_pull = structures_mod.tide_pool_pull_mult(tide_pool_level)
    dock_level = built.get(structures_mod.DOCK, 0)
    dock_bite_speed = structures_mod.dock_bite_speed_mult(dock_level)
    # The Fishery (4th coral structure) raises the lucky-double-catch chance —
    # fixed here from the same one structures read and threaded onto the Cast so
    # commit_catch stays DB-free. Unbuilt ⇒ +0.0 ⇒ the base chance ⇒ byte-identical.
    fishery_level = built.get(structures_mod.FISHERY, 0)
    double_catch_chance = rewards_mod.BONUS_CATCH_CHANCE + (
        structures_mod.fishery_bonus_chance(fishery_level)
    )
    # The "how-well" knobs compound: rod × bait × weather × gear × tide pool (pull),
    # and rod × bait × weather × gear × dock (bite speed). rarity_pull (all ≥ 1)
    # pulls the catch toward the big end of the SAME unlocked band (never a new band
    # — that stays the fishing-level axis); bite_speed (rod/bait/gear/dock ≤ 1,
    # weather either way) scales the bite wait. Weather is the transient, shared,
    # free knob (a storm makes a rarer catch likelier but the wait longer).
    effective_pull = (
        rod.rarity_pull
        * (bait.rarity_pull if bait else 1.0)
        * weather.rarity_mult
        * gear_pull
        * tide_pool_pull
    )
    effective_bite_speed = (
        rod.bite_speed
        * (bait.bite_speed if bait else 1.0)
        * weather.bite_speed_mult
        * gear_bite_speed
        * dock_bite_speed
    )
    cast = await roll_cast(
        user_id,
        guild_id,
        rod,
        rarity_pull=effective_pull,
        venue=profile.key,
        double_catch_chance=double_catch_chance,
    )
    if cast.catch is None:
        return CastStart(
            ok=False,
            message=(
                f"{profile.emoji} The {profile.name.lower()} is quiet right now — "
                "try later."
            ),
            energy_current=settled.current,
        )

    spent = fish_energy.spend(state, now, regen_seconds=regen_seconds)
    await db.set_fishing_energy(user_id, guild_id, spent.current, spent.updated_at)

    # Consume one bait charge — only now that the cast is actually happening (the
    # same "charge per attempt" rule as energy; a missed reel still spends it).
    charges_left = 0
    if bait is not None:
        charges_left = bait_charges - 1
        if charges_left <= 0:
            await db.clear_active_bait(user_id, guild_id)
            charges_left = 0
        else:
            await db.set_active_bait(user_id, guild_id, bait.key, charges_left)

    return CastStart(
        ok=True,
        cast=cast,
        rod=rod,
        energy_current=spent.current,
        effective_bite_speed=effective_bite_speed,
        bait_used=bait,
        bait_charges_left=charges_left,
        venue_profile=profile,
        weather=weather,
        fishing_gear_bonus=fishing_gear.has_fishing_bonus(gear_stats),
        tide_pool_bonus=tide_pool_level > 0,
        dock_bonus=dock_level > 0,
        fishery_bonus=fishery_level > 0,
    )


def get_forecast() -> weather_mod.Weather:
    """Today's fishing weather (UTC date) — for the menu / ``!forecast`` command.

    Pure read of the date-seeded weather; the same for everyone on a given day.
    """
    return weather_mod.current_weather()


# ---------------------------------------------------------------------------
# Venue — shore ↔ deepwater (the ⛵ Set sail / 🏖️ Dock toggle, Q-0175 §5)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VenueChange:
    """The outcome of a set-sail / dock toggle — the new venue + a message."""

    venue: str
    message: str
    #: True when the toggle actually changed the venue (always True today; kept
    #: so a future "already there" no-op path reads clearly).
    changed: bool = True


async def get_venue(user_id: int, guild_id: int) -> venue_mod.VenueProfile:
    """The player's current venue profile (shore when no row / unknown)."""
    return venue_mod.profile_for(await db.get_fishing_venue(user_id, guild_id))


async def set_venue(
    user_id: int,
    guild_id: int,
    venue: str,
) -> VenueChange:
    """Set the player's fishing venue to *venue* (normalised; unknown → shore).

    Plain game state, like the rod tier / energy — a single CRUD write, no audit
    (no coins or external effect). Returns the resolved profile + a player-facing
    line. The deepwater message names what changes (boat-only fish, tougher
    fights) so the choice reads as the design's "optimization, not a gate".
    """
    profile = venue_mod.profile_for(venue)
    await db.set_fishing_venue(user_id, guild_id, profile.key)
    if profile.key == venue_mod.DEEPWATER:
        message = (
            f"{profile.emoji} **You set sail for deepwater.** Rare boat-only fish "
            "lurk here — they bite slower and fight harder to break free, so a "
            "rod with good escape-resist pays off. Cast with `!fish`."
        )
    else:
        message = (
            f"{profile.emoji} **You docked back on the shore.** Relaxed casting "
            "for the everyday catch. Cast with `!fish`."
        )
    return VenueChange(venue=profile.key, message=message, changed=True)


async def toggle_venue(user_id: int, guild_id: int) -> VenueChange:
    """Flip the player between shore and deepwater (the menu / `!sail` action)."""
    current = await db.get_fishing_venue(user_id, guild_id)
    return await set_venue(user_id, guild_id, venue_mod.toggle(current))


# ---------------------------------------------------------------------------
# Rod ladder — the coin-bought progression axis (Q-0175)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RodPurchaseResult:
    """The outcome of a ``buy_rod`` attempt — a flag + a player-facing message."""

    success: bool
    message: str
    #: The rod tier owned *after* the attempt (unchanged on failure).
    tier: int


async def get_rod(user_id: int, guild_id: int) -> rods_mod.Rod:
    """The player's currently-equipped rod (the highest tier they own)."""
    tier = await db.get_rod_tier(user_id, guild_id)
    return rods_mod.rod_for_tier(tier)


async def buy_rod(user_id: int, guild_id: int) -> RodPurchaseResult:
    """Buy the next rod up the ladder — an audited coin sink.

    Mirrors ``mining_workflow.vault_upgrade``: read state + cost, debit coins and
    raise the owned tier inside ONE transaction (the debit audits itself), then
    emit the balance event after commit. Insufficient funds rolls everything back.
    """
    current_tier = await db.get_rod_tier(user_id, guild_id)
    nxt = rods_mod.next_rod(current_tier)
    if nxt is None:
        top = rods_mod.rod_for_tier(current_tier)
        return RodPurchaseResult(
            False,
            f"You already wield the **{top.name}** {top.emoji} — the finest rod there is!",
            current_tier,
        )

    try:
        async with db.transaction() as conn:
            new_balance = await economy_service.debit_in_txn(
                conn,
                guild_id,
                user_id,
                nxt.price,
                reason=ROD_PURCHASE_REASON,
                actor_id=user_id,
            )
            await db.set_rod_tier(user_id, guild_id, nxt.tier, conn=conn)
    except economy_service.InsufficientFundsError:
        balance = await db.get_coins(user_id, guild_id)
        return RodPurchaseResult(
            False,
            f"The **{nxt.name}** {nxt.emoji} costs **{nxt.price}** 🪙 — "
            f"you only have **{balance}** 🪙.",
            current_tier,
        )

    await bus.emit(
        economy_service.EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=-nxt.price,
        new_balance=new_balance,
        reason=ROD_PURCHASE_REASON,
    )
    return RodPurchaseResult(
        True,
        f"You upgraded to the **{nxt.name}** {nxt.emoji} for **{nxt.price}** 🪙! "
        f"Balance: **{new_balance}** 🪙.",
        nxt.tier,
    )


# ---------------------------------------------------------------------------
# Bait shelf — the consumable second coin sink / how-well knob (Q-0175 §4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BaitPurchaseResult:
    """The outcome of a ``buy_bait`` attempt — a flag + a player-facing message."""

    success: bool
    message: str
    #: The bait loaded after the attempt (``None`` on failure / when unchanged).
    bait: bait_mod.Bait | None = None
    #: Charges loaded after the attempt.
    charges: int = 0


async def buy_bait(
    user_id: int,
    guild_id: int,
    bait_key: str,
) -> BaitPurchaseResult:
    """Buy one pack of *bait_key* — an audited coin sink, like :func:`buy_rod`.

    A player loads at most one bait at a time: buying the **same** bait again
    stacks its charges; buying a **different** bait replaces the loadout (the
    message says so). The coin debit + the load run in ONE transaction (the debit
    audits itself); the balance event emits after commit. Insufficient funds rolls
    everything back and loads nothing.
    """
    bait = bait_mod.bait_by_key(bait_key)
    if bait is None:
        return BaitPurchaseResult(False, "That bait doesn't exist on the shelf.")

    cur_key, cur_charges = await db.get_active_bait(user_id, guild_id)
    stacking = cur_key == bait.key and cur_charges > 0
    new_charges = (cur_charges if stacking else 0) + bait.charges

    try:
        async with db.transaction() as conn:
            new_balance = await economy_service.debit_in_txn(
                conn,
                guild_id,
                user_id,
                bait.price,
                reason=BAIT_PURCHASE_REASON,
                actor_id=user_id,
            )
            await db.set_active_bait(
                user_id,
                guild_id,
                bait.key,
                new_charges,
                conn=conn,
            )
    except economy_service.InsufficientFundsError:
        balance = await db.get_coins(user_id, guild_id)
        return BaitPurchaseResult(
            False,
            f"A pack of **{bait.name}** {bait.emoji} costs **{bait.price}** 🪙 — "
            f"you only have **{balance}** 🪙.",
        )

    await bus.emit(
        economy_service.EVT_BALANCE_CHANGED,
        guild_id=guild_id,
        user_id=user_id,
        delta=-bait.price,
        new_balance=new_balance,
        reason=BAIT_PURCHASE_REASON,
    )
    verb = "Topped up" if stacking else "Loaded"
    return BaitPurchaseResult(
        True,
        f"{verb} **{bait.name}** {bait.emoji} ({bait_mod.effect_text(bait)}) — "
        f"**{new_charges}** casts ready for **{bait.price}** 🪙. "
        f"Balance: **{new_balance}** 🪙.",
        bait=bait,
        charges=new_charges,
    )


# ---------------------------------------------------------------------------
# Bait crafting — turn small caught fish into bait (the catch→bait loop, idea
# fishing-bait-crafting-2026-06-22). The gameplay-native second source beside
# the coin shop: an inventory→bait conversion, NOT a coin sink.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BaitCraftResult:
    """The outcome of a ``craft_bait`` attempt — a flag + a player-facing message."""

    success: bool
    message: str
    #: The bait loaded after the attempt (``None`` on failure / when unchanged).
    bait: bait_mod.Bait | None = None
    #: Charges loaded after the attempt.
    charges: int = 0


class _FishRecipe(Protocol):
    """The shape ``_plan_fish_spend`` needs — shared by bait and charm recipes."""

    fish_count: int
    max_size_rank: int


def _eligible_fish(
    inventory: dict[str, int],
    recipe: _FishRecipe,
) -> list[tuple[int, str, int]]:
    """The player's fish eligible toward *recipe*, as ``(size_rank, name, have)``.

    Eligible = a known fish species whose ``size_rank`` is ``≤ recipe.max_size_rank``.
    Shared by :func:`_plan_fish_spend` (which fish to debit) and
    :func:`eligible_fish_total` (live progress display) so both read the exact
    same eligibility rule.
    """
    eligible: list[tuple[int, str, int]] = []  # (size_rank, name, have)
    for name, have in inventory.items():
        if have <= 0:
            continue
        species = fish_mod.species_by_name(name)
        if species is None or species.size_rank > recipe.max_size_rank:
            continue
        eligible.append((species.size_rank, name, have))
    return eligible


def eligible_fish_total(inventory: dict[str, int], recipe: _FishRecipe) -> int:
    """Total fish in *inventory* eligible toward *recipe* (size_rank ≤ cap).

    A pure progress readout — unlike :func:`_plan_fish_spend` it never gates on
    ``recipe.fish_count`` being met, so a caller can show "7/10 eligible fish"
    before the player has enough to craft.
    """
    return sum(have for _, _, have in _eligible_fish(inventory, recipe))


def _plan_fish_spend(
    inventory: dict[str, int],
    recipe: _FishRecipe,
) -> dict[str, int] | None:
    """Choose which eligible fish to consume for *recipe* (smallest-first).

    Consumes the smallest ranks first (ties broken by name) so the player keeps
    their bigger catches. Returns a ``{fish_name: count}`` spend map, or ``None``
    when the player lacks ``recipe.fish_count`` eligible fish.
    """
    eligible = _eligible_fish(inventory, recipe)
    if sum(have for _, _, have in eligible) < recipe.fish_count:
        return None

    eligible.sort(key=lambda e: (e[0], e[1]))  # smallest size, then name
    spend: dict[str, int] = {}
    remaining = recipe.fish_count
    for _, name, have in eligible:
        if remaining <= 0:
            break
        take = min(have, remaining)
        spend[name] = take
        remaining -= take
    return spend


async def craft_bait(
    user_id: int,
    guild_id: int,
    bait_key: str,
) -> BaitCraftResult:
    """Craft one pack of *bait_key* from small caught fish — the catch→bait loop.

    Mirrors :func:`mining_workflow.cook` / :func:`mining_workflow.craft`: an
    inventory-only conversion (no coins, no external call) — debit the eligible
    fish and load/stack the bait in ONE ``db.transaction()`` (Q-0071). Like
    :func:`buy_bait`, crafting the same bait stacks charges and a different bait
    replaces the loadout. Only baits with a recipe are craftable; the premium
    combo stays a pure coin sink.
    """
    bait = bait_mod.bait_by_key(bait_key)
    recipe = bait_mod.craft_recipe(bait_key)
    if bait is None or recipe is None:
        return BaitCraftResult(
            False,
            "That bait can't be crafted from fish — buy it with `!bait`.",
        )

    inventory = await db.get_mining_inventory(str(user_id), guild_id)
    spend = _plan_fish_spend(inventory, recipe)
    if spend is None:
        return BaitCraftResult(
            False,
            f"You need **{recipe.fish_count}** fish of size ≤ "
            f"**{recipe.max_size_rank}** to craft **{bait.name}** {bait.emoji} — "
            "catch more small fish with `!fish`.",
        )

    cur_key, cur_charges = await db.get_active_bait(user_id, guild_id)
    stacking = cur_key == bait.key and cur_charges > 0
    new_charges = (cur_charges if stacking else 0) + bait.charges

    deltas = {name: -qty for name, qty in spend.items()}
    async with db.transaction() as conn:
        await db.apply_inventory_deltas(str(user_id), guild_id, deltas, conn=conn)
        await db.set_active_bait(user_id, guild_id, bait.key, new_charges, conn=conn)

    used = ", ".join(f"{qty}× {name}" for name, qty in spend.items())
    verb = "Topped up" if stacking else "Crafted"
    return BaitCraftResult(
        True,
        f"{verb} **{bait.name}** {bait.emoji} ({bait_mod.effect_text(bait)}) from "
        f"**{used}** — **{new_charges}** casts ready.",
        bait=bait,
        charges=new_charges,
    )


# ---------------------------------------------------------------------------
# Pearl crafting — turn the rare reel-drop material into the premium bait (the
# one bait with no fish recipe). The pearl's sole sink — a repeatable home for
# the rare drop. Mirrors craft_bait, but spends PEARLS instead of fish.
# ---------------------------------------------------------------------------


async def craft_pearl_bait(
    user_id: int,
    guild_id: int,
    bait_key: str,
) -> BaitCraftResult:
    """Craft one pack of *bait_key* from **pearls** — the rare-material sink.

    The premium combo bait is deliberately absent from the fish-craft shelf (a
    pure coin sink); this gives it a gameplay-native earn path via the pearl, the
    rare drop :func:`commit_catch` grants. An inventory-only conversion (no coins,
    no external call): debit the pearls and load/stack the bait in ONE
    ``db.transaction()`` (Q-0071). Like :func:`buy_bait`, crafting the same bait
    stacks charges. Only baits with a pearl recipe are craftable this way.
    """
    bait = bait_mod.bait_by_key(bait_key)
    pearl_cost = bait_mod.pearl_recipe(bait_key)
    if bait is None or pearl_cost is None:
        return BaitCraftResult(
            False,
            "That bait isn't crafted from pearls — buy it with `!bait`.",
        )

    inventory = await db.get_mining_inventory(str(user_id), guild_id)
    have = inventory.get(PEARL_ITEM, 0)
    if have < pearl_cost:
        return BaitCraftResult(
            False,
            f"You need **{pearl_cost}** 🦪 pearls to craft **{bait.name}** "
            f"{bait.emoji} — you have **{have}**. Pearls drop rarely when you "
            "reel in a fish (bigger fish, better odds).",
        )

    cur_key, cur_charges = await db.get_active_bait(user_id, guild_id)
    stacking = cur_key == bait.key and cur_charges > 0
    new_charges = (cur_charges if stacking else 0) + bait.charges

    async with db.transaction() as conn:
        await db.update_mining_item(
            str(user_id),
            guild_id,
            PEARL_ITEM,
            -pearl_cost,
            conn=conn,
        )
        await db.set_active_bait(user_id, guild_id, bait.key, new_charges, conn=conn)

    verb = "Topped up" if stacking else "Crafted"
    return BaitCraftResult(
        True,
        f"{verb} **{bait.name}** {bait.emoji} ({bait_mod.effect_text(bait)}) from "
        f"**{pearl_cost}** 🦪 pearls — **{new_charges}** casts ready.",
        bait=bait,
        charges=new_charges,
    )


# ---------------------------------------------------------------------------
# Curio carving — turn the deepwater rare-material (coral) into cosmetic
# collectibles (the coral sink; S1 "▶ next offline successor"). Coral's analogue
# of craft_pearl_bait, but the target is a cosmetic TREASURE item (a completionist
# collection), not a bait. An inventory-only conversion: debit coral, grant the
# curio, in ONE db.transaction() (Q-0071). Never a coin sink, never sellable.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CurioCraftResult:
    """The outcome of a ``craft_curio`` attempt — a flag + a player-facing message."""

    success: bool
    message: str
    #: The curio carved on success (``None`` on failure).
    curio: curios_mod.Curio | None = None


async def craft_curio(
    user_id: int,
    guild_id: int,
    curio_key: str,
) -> CurioCraftResult:
    """Carve one *curio_key* from **coral** — the deepwater rare-material sink.

    Coral drops only on a deepwater (boat) reel; this is its sole home — a
    cosmetic carving collection (:mod:`utils.fishing.curios`). An inventory-only
    conversion (no coins, no external call): debit the coral and grant the curio
    item in ONE ``db.transaction()`` (Q-0071). The curio is a cosmetic
    :class:`utils.mining.items.ItemKind` ``TREASURE`` — never sellable, no gameplay
    effect; the reward is the collection. Crafting a curio you already own simply
    adds another copy (harmless; the collection tally counts distinct curios).
    """
    curio = curios_mod.curio_by_key(curio_key)
    if curio is None:
        return CurioCraftResult(
            False,
            "That isn't a carvable curio — see `!curios` for the collection.",
        )

    inventory = await db.get_mining_inventory(str(user_id), guild_id)
    have = inventory.get(CORAL_ITEM, 0)
    if have < curio.coral_cost:
        return CurioCraftResult(
            False,
            f"You need **{curio.coral_cost}** 🪸 coral to carve **{curio.name}** "
            f"{curio.emoji} — you have **{have}**. Coral drops rarely when you reel "
            "in a fish out in **deepwater** (`!sail` to the boat first).",
        )

    async with db.transaction() as conn:
        await db.update_mining_item(
            str(user_id),
            guild_id,
            CORAL_ITEM,
            -curio.coral_cost,
            conn=conn,
        )
        await db.update_mining_item(
            str(user_id),
            guild_id,
            curio.item,
            1,
            conn=conn,
        )

    owned, total = curios_mod.collection_progress(
        {**inventory, curio.item: inventory.get(curio.item, 0) + 1},
    )
    return CurioCraftResult(
        True,
        f"Carved **{curio.name}** {curio.emoji} from **{curio.coral_cost}** 🪸 "
        f"coral — a cosmetic collectible for your shelf. "
        f"Collection: **{owned}/{total}** curios.",
        curio=curio,
    )


# Charm crafting — turn small caught fish into the CHARM-slot fishing charms
# (the catch→charm earn path, S1 acquisition-depth follow-up to #1504). The
# gameplay-native second source beside the mining gear shop's coin price: an
# inventory→gear conversion, NOT a coin sink. Mirrors craft_bait exactly.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CharmCraftResult:
    """The outcome of a ``craft_charm`` attempt — a flag + a player-facing message."""

    success: bool
    message: str
    #: The charm item name crafted (``None`` on failure).
    charm: str | None = None


async def craft_charm(
    user_id: int,
    guild_id: int,
    charm_name: str,
) -> CharmCraftResult:
    """Craft one *charm_name* fishing charm from small caught fish.

    Mirrors :func:`craft_bait`: an inventory-only conversion (no coins, no
    external call) — debit the eligible fish (smallest-first) and grant one
    charm into the mining inventory in ONE ``db.transaction()`` (Q-0071). The
    charm then equips through the normal mining gear panel (CHARM slot). Only the
    three fishing charms have a recipe; coins remain the fast alternative via the
    gear shop (``!gear``). The fish a charm consumes are worth far less sold than
    the charm's shop price, so neither path is free arbitrage.
    """
    recipe = fishing_gear.charm_recipe(charm_name)
    if recipe is None:
        return CharmCraftResult(
            False,
            "That charm can't be crafted from fish — buy it with `!gear`.",
        )

    inventory = await db.get_mining_inventory(str(user_id), guild_id)
    spend = _plan_fish_spend(inventory, recipe)
    if spend is None:
        return CharmCraftResult(
            False,
            f"You need **{recipe.fish_count}** fish of size ≤ "
            f"**{recipe.max_size_rank}** to craft a **{recipe.charm}** — "
            "catch more fish with `!fish`.",
        )

    deltas: dict[str, int] = {name: -qty for name, qty in spend.items()}
    deltas[recipe.charm] = deltas.get(recipe.charm, 0) + 1
    async with db.transaction() as conn:
        await db.apply_inventory_deltas(str(user_id), guild_id, deltas, conn=conn)

    used = ", ".join(f"{qty}× {name}" for name, qty in spend.items())
    return CharmCraftResult(
        True,
        f"Crafted a **{recipe.charm}** from **{used}** — "
        "equip it from the gear panel (`!gear`) to fish better.",
        charm=recipe.charm,
    )


# Rod crafting — earn the next rod up the ladder from caught fish (the catch→rod
# earn path, S1 acquisition-depth follow-up to the charm craft #1508). The
# gameplay-native second source beside the coin shop (``buy_rod``): an
# inventory→tier conversion, NOT a coin sink. Mirrors craft_charm exactly, and
# like buy_rod it crafts the *next* rod up (requires owning the tier below).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RodCraftResult:
    """The outcome of a ``craft_rod`` attempt — a flag + a player-facing message."""

    success: bool
    message: str
    #: The rod tier owned *after* the attempt (unchanged on failure).
    tier: int


async def craft_rod(user_id: int, guild_id: int) -> RodCraftResult:
    """Craft the next rod up the ladder from small caught fish.

    Mirrors :func:`craft_charm`: an inventory-only conversion (no coins, no
    external call) — debit the eligible fish (smallest-first) and raise the
    owned rod tier by one in ONE ``db.transaction()`` (Q-0071). Like
    :func:`buy_rod`, this advances the *next* tier from the one you own, so a
    fisher works up the ladder by fishing. Coins remain the fast alternative via
    ``buy_rod`` / the rod shop (``!rod``); the fish a rod consumes are worth far
    less sold than the rod's coin price, so neither path is free arbitrage.
    """
    current_tier = await db.get_rod_tier(user_id, guild_id)
    nxt = rods_mod.next_rod(current_tier)
    if nxt is None:
        top = rods_mod.rod_for_tier(current_tier)
        return RodCraftResult(
            False,
            f"You already wield the **{top.name}** {top.emoji} — the finest rod there is!",
            current_tier,
        )

    recipe = rods_mod.rod_recipe(nxt.tier)
    if recipe is None:  # pragma: no cover — every non-starter tier has a recipe
        return RodCraftResult(
            False,
            f"The **{nxt.name}** {nxt.emoji} can't be crafted from fish — "
            "buy it with `!rod`.",
            current_tier,
        )

    inventory = await db.get_mining_inventory(str(user_id), guild_id)
    spend = _plan_fish_spend(inventory, recipe)
    if spend is None:
        return RodCraftResult(
            False,
            f"You need **{recipe.fish_count}** fish of size ≤ "
            f"**{recipe.max_size_rank}** to craft the **{nxt.name}** {nxt.emoji} — "
            "catch more fish with `!fish` (or buy it with `!rod`).",
            current_tier,
        )

    deltas = {name: -qty for name, qty in spend.items()}
    async with db.transaction() as conn:
        await db.apply_inventory_deltas(str(user_id), guild_id, deltas, conn=conn)
        await db.set_rod_tier(user_id, guild_id, nxt.tier, conn=conn)

    used = ", ".join(f"{qty}× {name}" for name, qty in spend.items())
    return RodCraftResult(
        True,
        f"Crafted the **{nxt.name}** {nxt.emoji} from **{used}** — "
        "cast with `!fish` to feel the difference!",
        nxt.tier,
    )
