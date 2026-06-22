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
        # rarity_pull ≥ 1 so it compounds onto the rod without ever penalising;
        # bounded charges + a positive price make it a real consumable coin sink.
        assert bait.rarity_pull >= 1.0
        assert bait.charges > 0
        assert bait.price > 0


def test_pricier_bait_pulls_harder():
    by_price = sorted(bait_mod.BAIT_CATALOG, key=lambda b: b.price)
    pulls = [b.rarity_pull for b in by_price]
    assert pulls == sorted(pulls)  # more expensive ⇒ at least as strong a pull


def test_bait_by_key_resolves_known_and_rejects_unknown():
    first = bait_mod.BAIT_CATALOG[0]
    assert bait_mod.bait_by_key(first.key) is first
    assert bait_mod.bait_by_key("nope") is None
    assert bait_mod.bait_by_key("") is None
    assert bait_mod.bait_by_key(None) is None
