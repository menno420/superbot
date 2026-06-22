"""fishing minigame — pure tuning + resolve logic (owner design Q-0175).

Pins the sim-recommended numbers and the pure helpers
(``utils/fishing/minigame.py``). No Discord, no clock — every assertion is
deterministic via a seeded ``random.Random``.
"""

from __future__ import annotations

import random

from utils.fishing import minigame
from utils.fishing.fish import FishSpecies


def test_bite_delay_stays_in_band_and_never_below_floor():
    rng = random.Random(0)
    samples = [minigame.roll_bite_delay(rng) for _ in range(2000)]
    assert all(s >= minigame.BITE_DELAY_FLOOR for s in samples)
    assert all(s <= minigame.BITE_DELAY_MAX for s in samples)
    # the band is exercised (not pinned to one value)
    assert min(samples) < max(samples)


def test_bite_delay_floor_dominates_when_band_is_below_it(monkeypatch):
    # If the band were tuned below the floor, the floor still wins (never instant).
    monkeypatch.setattr(minigame, "BITE_DELAY_MIN", 0.1)
    monkeypatch.setattr(minigame, "BITE_DELAY_MAX", 0.2)
    rng = random.Random(1)
    assert all(
        minigame.roll_bite_delay(rng) == minigame.BITE_DELAY_FLOOR for _ in range(50)
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
