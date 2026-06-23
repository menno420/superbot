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
import time
from dataclasses import dataclass

from core.events import bus
from services import economy_service, game_xp_service
from utils import db
from utils.fishing import MAX_LEVEL, Catch
from utils.fishing import bait as bait_mod
from utils.fishing import energy as fish_energy
from utils.fishing import fish as fish_mod
from utils.fishing import rods as rods_mod
from utils.fishing import roll_catch
from utils.fishing import venue as venue_mod
from utils.fishing import weather as weather_mod

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


async def roll_cast(
    user_id: int,
    guild_id: int,
    rod: rods_mod.Rod | None = None,
    *,
    rarity_pull: float | None = None,
    venue: str = venue_mod.SHORE,
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
    return Cast(catch=catch, level_before=level_before, venue=venue)


async def commit_catch(user_id: int, guild_id: int, cast: Cast) -> FishResult:
    """Commit a successfully-reeled cast: log it + grant the item + award xp.

    The audited write boundary (RS02 / Q-0071): the catch-log write, the
    inventory grant, and the xp award all run on ONE workflow-owned
    ``db.transaction()`` connection; the xp event emits only after commit. A
    ``cast`` with no ``catch`` (empty catalog) writes nothing.
    """
    catch = cast.catch
    level_before = cast.level_before
    if catch is None:
        return FishResult(catch=None, fishing_level=level_before)

    async with db.transaction() as conn:
        prev_best = await db.record_catch(
            user_id,
            guild_id,
            catch.species.name,
            catch.weight,
            conn=conn,
        )
        # The caught fish is now a tangible inventory item (owner decision
        # 2026-06-22): sellable for coins via the market, and cookable into food
        # at a campfire (mining_workflow.cook). The catch-log row above stays the
        # dex/leaderboard record; this grant makes the fish usable — same atomic
        # catch transaction, conn-composed (RS02).
        await db.update_mining_item(
            str(user_id),
            guild_id,
            catch.species.name,
            1,
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


def _fmt_wait(seconds: int) -> str:
    """Human "ready in" — ``45s`` / ``2m 05s``."""
    if seconds < 60:
        return f"{seconds}s"
    return f"{seconds // 60}m {seconds % 60:02d}s"


async def get_energy(user_id: int, guild_id: int) -> int:
    """The player's *settled* current fishing energy (for the ⚡ gauge / menu)."""
    now = int(time.time())
    cur, ts = await db.get_fishing_energy(user_id, guild_id)
    return fish_energy.settle(fish_energy.EnergyState(cur, ts), now).current


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
    cur, ts = await db.get_fishing_energy(user_id, guild_id)
    state = fish_energy.EnergyState(cur, ts)
    settled = fish_energy.settle(state, now)
    if settled.current < fish_energy.CAST_COST:
        wait = fish_energy.seconds_until(state, now, fish_energy.CAST_COST)
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
    # Three "how-well" knobs compound: rod × bait × the day's weather. rarity_pull
    # (all ≥ 1) pulls the catch toward the big end of the SAME unlocked band (never
    # a new band — that stays the fishing-level axis); bite_speed (rod/bait ≤ 1,
    # weather either way) scales the bite wait. Weather is the transient, shared,
    # free knob (a storm makes a rarer catch likelier but the wait longer).
    effective_pull = (
        rod.rarity_pull * (bait.rarity_pull if bait else 1.0) * weather.rarity_mult
    )
    effective_bite_speed = (
        rod.bite_speed * (bait.bite_speed if bait else 1.0) * weather.bite_speed_mult
    )
    cast = await roll_cast(
        user_id,
        guild_id,
        rod,
        rarity_pull=effective_pull,
        venue=profile.key,
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

    spent = fish_energy.spend(state, now)
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


def _plan_fish_spend(
    inventory: dict[str, int],
    recipe: bait_mod.BaitRecipe,
) -> dict[str, int] | None:
    """Choose which eligible fish to consume for *recipe* (smallest-first).

    Eligible = a known fish species whose ``size_rank`` is ``≤ recipe.max_size_rank``.
    Consumes the smallest ranks first (ties broken by name) so the player keeps
    their bigger catches. Returns a ``{fish_name: count}`` spend map, or ``None``
    when the player lacks ``recipe.fish_count`` eligible fish.
    """
    eligible: list[tuple[int, str, int]] = []  # (size_rank, name, have)
    for name, have in inventory.items():
        if have <= 0:
            continue
        species = fish_mod.species_by_name(name)
        if species is None or species.size_rank > recipe.max_size_rank:
            continue
        eligible.append((species.size_rank, name, have))

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
