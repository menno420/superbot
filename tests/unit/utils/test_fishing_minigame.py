"""fishing minigame — pure tuning + resolve logic (owner design Q-0175).

Pins the sim-recommended numbers and the pure helpers
(``utils/fishing/minigame.py``). No Discord, no clock — every assertion is
deterministic via a seeded ``random.Random``.
"""

from __future__ import annotations

import random

import pytest

from utils.fishing import minigame
from utils.fishing.fish import FishSpecies


def test_bite_delay_stays_in_band_and_never_below_floor():
    rng = random.Random(0)
    samples = [minigame.roll_bite_delay(rng) for _ in range(2000)]
    assert all(s >= minigame.BITE_DELAY_FLOOR for s in samples)
    assert all(s <= minigame.BITE_DELAY_MAX for s in samples)
    # the band is exercised (not pinned to one value)
    assert min(samples) < max(samples)


def test_bite_delay_floor_dominates_when_band_is_below_it():
    # If a venue's band were tuned below the floor, the floor still wins (never
    # instant). The band is now passed per-venue (lo/hi/floor args), so this
    # checks the floor clamp directly.
    rng = random.Random(1)
    assert all(
        minigame.roll_bite_delay(rng, lo=0.1, hi=0.2, floor=minigame.BITE_DELAY_FLOOR)
        == minigame.BITE_DELAY_FLOOR
        for _ in range(50)
    )


def test_fakeout_is_a_coin_flip_around_its_chance():
    rng = random.Random(7)
    hits = sum(minigame.roll_fakeout(rng) for _ in range(5000))
    rate = hits / 5000
    assert abs(rate - minigame.FAKEOUT_CHANCE) < 0.05


def test_reel_is_in_time_window_boundaries():
    assert minigame.reel_is_in_time(0.0) is True
    assert minigame.reel_is_in_time(minigame.REACTION_WINDOW) is True
    assert minigame.reel_is_in_time(minigame.REACTION_WINDOW + 0.01) is False
    # a negative elapsed (clock skew) is never "in time"
    assert minigame.reel_is_in_time(-0.5) is False


def test_window_is_generous_enough_to_be_a_presence_check():
    # The design's load-bearing point: the window must clear a realistic
    # round trip (down-latency + reaction + up-latency ~ 0.8-1.3s), so an
    # attentive player lands it. Pin that it's comfortably above 1.5s.
    assert minigame.REACTION_WINDOW >= 1.5


def test_trophy_is_the_top_of_the_unlocked_band():
    # At level 1 the band is sizes 1-3; size 3 is the trophy, size 1 is not.
    big = FishSpecies("whopper", 3, "🐠")
    small = FishSpecies("minnow", 1, "🐟")
    assert minigame.is_trophy(big, fishing_level=1) is True
    assert minigame.is_trophy(small, fishing_level=1) is False


def test_trophy_scales_with_progression():
    # The same size-3 fish stops being a trophy once you out-level its band.
    fish = FishSpecies("whopper", 3, "🐠")
    assert minigame.is_trophy(fish, fishing_level=1) is True
    assert minigame.is_trophy(fish, fishing_level=7) is False


def test_escape_clue_only_fires_for_a_trophy_and_names_the_fish():
    big = FishSpecies("whopper", 3, "🐠")
    small = FishSpecies("minnow", 1, "🐟")
    clue = minigame.escape_clue(big, fishing_level=1)
    assert clue is not None
    assert "Whopper" in clue  # the species is named so the loss baits the next cast
    # An ordinary fish gets no story — only big ones leave a clue.
    assert minigame.escape_clue(small, fishing_level=1) is None


def test_escape_clue_follows_the_progression_band():
    fish = FishSpecies("whopper", 3, "🐠")
    assert minigame.escape_clue(fish, fishing_level=1) is not None
    assert minigame.escape_clue(fish, fishing_level=7) is None  # no longer a trophy


# ---------------------------------------------------------------------------
# Reel-fight (trophy) helpers
# ---------------------------------------------------------------------------


def test_reel_fight_taps_scale_with_fish_size_within_bounds():
    smallest = FishSpecies("a", 1, "🐟")
    biggest = FishSpecies("z", 21, "🦑")
    assert minigame.reel_fight_taps(smallest) == minigame.FIGHT_MIN_TAPS
    assert minigame.reel_fight_taps(biggest) == minigame.FIGHT_MAX_TAPS
    # monotonic non-decreasing across the catalog, always inside the bounds
    taps = [minigame.reel_fight_taps(FishSpecies("x", r, "🐟")) for r in range(1, 22)]
    assert taps == sorted(taps)
    assert all(minigame.FIGHT_MIN_TAPS <= t <= minigame.FIGHT_MAX_TAPS for t in taps)


def test_fight_escape_chance_is_small_and_grows_with_size():
    small = minigame.fight_escape_chance(FishSpecies("a", 1, "🐟"))
    big = minigame.fight_escape_chance(FishSpecies("z", 21, "🦑"))
    assert 0.0 < small < big
    # even the biggest fish stays a *small* per-tap chance — trophies mostly land.
    assert big < 0.20


def test_escape_resist_buys_down_the_escape_chance():
    fish = FishSpecies("z", 21, "🦑")
    base = minigame.fight_escape_chance(fish, escape_resist=0.0)
    halved = minigame.fight_escape_chance(fish, escape_resist=0.5)
    assert halved == pytest.approx(base * 0.5)
    # full resist (a future top-tier rod) removes the snap-free risk entirely.
    assert minigame.fight_escape_chance(fish, escape_resist=1.0) == 0.0


def test_roll_escape_matches_its_probability():
    fish = FishSpecies("z", 21, "🦑")
    rng = random.Random(3)
    hits = sum(minigame.roll_escape(fish, rng=rng) for _ in range(20000))
    expected = minigame.fight_escape_chance(fish)
    assert abs(hits / 20000 - expected) < 0.02


def test_bite_speed_shortens_the_wait_but_respects_the_floor():
    import random as _random

    fast = [minigame.roll_bite_delay(_random.Random(i), speed=0.7) for i in range(500)]
    slow = [minigame.roll_bite_delay(_random.Random(i), speed=1.0) for i in range(500)]
    assert sum(fast) / len(fast) < sum(slow) / len(slow)  # faster rod bites sooner
    assert all(d >= minigame.BITE_DELAY_FLOOR for d in fast)  # never below the floor


# ---------------------------------------------------------------------------
# Venue awareness (Q-0175 §5) — the deepwater band & escape thread through
# ---------------------------------------------------------------------------


def test_base_escape_param_scales_the_snap_free_chance():
    fish = FishSpecies("x", 10, "🐟")
    shore = minigame.fight_escape_chance(fish)  # shore default
    deep = minigame.fight_escape_chance(fish, base_escape=0.22)
    # A higher venue base escape makes the fish snap free more often (the deep).
    assert deep > shore
    assert deep == pytest.approx(shore * (0.22 / minigame.SHORE_ESCAPE_CHANCE))


def test_roll_escape_honours_the_venue_base_escape():
    fish = FishSpecies("y", 14, "🐠")
    rng = random.Random(5)
    hits = sum(
        minigame.roll_escape(fish, base_escape=0.22, rng=rng) for _ in range(20000)
    )
    expected = minigame.fight_escape_chance(fish, base_escape=0.22)
    assert abs(hits / 20000 - expected) < 0.02


def test_is_trophy_judges_a_fish_against_its_own_venue_band():
    # A deepwater fish is judged against the deepwater cap, not the shore cap —
    # species.venue is authoritative, so the caller need not pass the venue.
    deep_big = FishSpecies("colossal squid", 20, "🦑", venue="deepwater")
    assert minigame.is_trophy(deep_big, fishing_level=7) is True
    deep_small = FishSpecies("lanternfish", 2, "🐟", venue="deepwater")
    assert minigame.is_trophy(deep_small, fishing_level=7) is False


def test_deepwater_band_bites_slower_than_shore_on_the_same_seed():
    from utils.fishing import venue

    shore_p, deep_p = venue.SHORE_PROFILE, venue.DEEPWATER_PROFILE
    shore = [
        minigame.roll_bite_delay(
            random.Random(i),
            lo=shore_p.bite_delay_min,
            hi=shore_p.bite_delay_max,
            floor=shore_p.bite_delay_floor,
        )
        for i in range(500)
    ]
    deep = [
        minigame.roll_bite_delay(
            random.Random(i),
            lo=deep_p.bite_delay_min,
            hi=deep_p.bite_delay_max,
            floor=deep_p.bite_delay_floor,
        )
        for i in range(500)
    ]
    assert sum(deep) / len(deep) > sum(shore) / len(shore)
