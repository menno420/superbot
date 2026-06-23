"""Fishing bait catalog — pure-data invariants (Q-0175 §4)."""

from __future__ import annotations

from utils.fishing import bait as bait_mod


def test_catalog_is_non_empty_with_unique_keys():
    assert bait_mod.BAIT_CATALOG
    keys = [b.key for b in bait_mod.BAIT_CATALOG]
    assert len(keys) == len(set(keys))  # no duplicate keys
    assert bait_mod.BAIT_KEYS == tuple(keys)  # keys mirror the shelf order


def test_every_bait_is_a_meaningful_consumable_sink():
    for bait in bait_mod.BAIT_CATALOG:
        # Knobs never penalise: rarity_pull ≥ 1 compounds onto the rod, bite_speed
        # ≤ 1 (and > 0) only shortens the wait; bounded charges + a positive price
        # make it a real consumable coin sink, and it must improve ≥ 1 knob.
        assert bait.rarity_pull >= 1.0
        assert 0.0 < bait.bite_speed <= 1.0
        assert bait.charges > 0
        assert bait.price > 0
        assert bait.rarity_pull > 1.0 or bait.bite_speed < 1.0


def test_both_knob_families_and_a_combo_are_on_the_shelf():
    rarity_only = [b for b in bait_mod.BAIT_CATALOG if b.rarity_pull > 1.0 and b.bite_speed == 1.0]
    speed_only = [b for b in bait_mod.BAIT_CATALOG if b.bite_speed < 1.0 and b.rarity_pull == 1.0]
    combo = [b for b in bait_mod.BAIT_CATALOG if b.rarity_pull > 1.0 and b.bite_speed < 1.0]
    assert rarity_only and speed_only and combo  # the orthogonal shelf design


def test_pricier_bait_is_stronger_within_each_pure_knob_family():
    # Cross-family price isn't comparable (different knobs), but within a pure
    # family a pricier pack must be at least as strong.
    rarity = sorted(
        (b for b in bait_mod.BAIT_CATALOG if b.rarity_pull > 1.0 and b.bite_speed == 1.0),
        key=lambda b: b.price,
    )
    assert [b.rarity_pull for b in rarity] == sorted(b.rarity_pull for b in rarity)
    speed = sorted(
        (b for b in bait_mod.BAIT_CATALOG if b.bite_speed < 1.0 and b.rarity_pull == 1.0),
        key=lambda b: b.price,
    )
    # lower bite_speed = faster, so pricier ⇒ non-increasing bite_speed
    assert [b.bite_speed for b in speed] == sorted((b.bite_speed for b in speed), reverse=True)


def test_effect_text_describes_only_the_knobs_a_bait_turns():
    rarity = bait_mod.bait_by_key("worm")  # ×1.25 rarity, neutral speed
    speed = bait_mod.bait_by_key("minnow")  # neutral rarity, 0.80 speed
    combo = bait_mod.bait_by_key("feast")  # both
    assert bait_mod.effect_text(rarity) == "×1.25 rarity"
    assert bait_mod.effect_text(speed) == "−20% wait"
    assert "rarity" in bait_mod.effect_text(combo) and "wait" in bait_mod.effect_text(combo)
    # a hypothetical neutral bait reads honestly rather than claiming a knob
    neutral = bait_mod.Bait("x", "X", "🧪", rarity_pull=1.0, charges=1, price=1)
    assert bait_mod.effect_text(neutral) == "no effect"


def test_bait_by_key_resolves_known_and_rejects_unknown():
    first = bait_mod.BAIT_CATALOG[0]
    assert bait_mod.bait_by_key(first.key) is first
    assert bait_mod.bait_by_key("nope") is None
    assert bait_mod.bait_by_key("") is None
    assert bait_mod.bait_by_key(None) is None
