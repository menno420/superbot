"""utils.creatures.encounters — wild roll + catch (seed-deterministic)."""

from __future__ import annotations

import random
from collections import Counter

from utils.creatures import creature
from utils.creatures.encounters import (
    MAX_CATCH_CHANCE,
    attempt_catch,
    catch_chance,
    roll_encounter,
)


def test_roll_is_deterministic_for_a_fixed_seed():
    a = roll_encounter(random.Random(42))
    b = roll_encounter(random.Random(42))
    assert a == b


def test_roll_only_yields_catalog_creatures():
    rng = random.Random(7)
    names = {c.name for c in creature.CREATURES}
    for _ in range(500):
        enc = roll_encounter(rng)
        assert enc is not None
        assert enc.creature.name in names


def test_common_creatures_appear_more_than_epic_ones():
    rng = random.Random(99)
    rarities = Counter(roll_encounter(rng).creature.rarity for _ in range(8000))
    assert rarities["Common"] > rarities["Epic"]


def test_catch_chance_is_higher_for_commons_than_epics():
    common = next(c for c in creature.CREATURES if c.rarity == "Common")
    epic = next(c for c in creature.CREATURES if c.rarity == "Epic")
    assert catch_chance(common, 1) > catch_chance(epic, 1)


def test_level_increases_catch_chance_but_is_capped():
    epic = next(c for c in creature.CREATURES if c.rarity == "Epic")
    low = catch_chance(epic, 1)
    high = catch_chance(epic, 50)
    assert high > low
    assert high <= MAX_CATCH_CHANCE


def test_catch_chance_never_exceeds_the_ceiling_even_for_a_common():
    common = next(c for c in creature.CREATURES if c.rarity == "Common")
    assert catch_chance(common, 1000) <= MAX_CATCH_CHANCE


def test_attempt_catch_succeeds_on_a_low_roll_and_fails_on_a_high_one():
    common = next(c for c in creature.CREATURES if c.rarity == "Common")

    class _LowRoll(random.Random):
        def random(self):  # type: ignore[override]
            return 0.0

    class _HighRoll(random.Random):
        def random(self):  # type: ignore[override]
            return 0.999

    assert attempt_catch(common, 1, _LowRoll()) is True
    assert attempt_catch(common, 1, _HighRoll()) is False


def test_roll_returns_none_when_catalog_empty(monkeypatch):
    monkeypatch.setattr("utils.creatures.encounters.CREATURES", ())
    assert roll_encounter() is None
