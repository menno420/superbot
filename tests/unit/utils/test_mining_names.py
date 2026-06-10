"""Fuzzy item-name resolution — the modernized legacy matcher."""

from __future__ import annotations

import pytest

from utils.mining.names import resolve_item_name

_CANDIDATES = (
    "pickaxe",
    "iron pickaxe",
    "gold pickaxe",
    "diamond pickaxe",
    "torch",
    "lantern",
    "diamond lantern",
    "lucky charm",
    "dynamite",
)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("pickaxe", "pickaxe"),  # exact
        ("  Iron_Pickaxe ", "iron pickaxe"),  # normalization
        ("pickax", "pickaxe"),  # typo within cutoff
        ("iron pickax", "iron pickaxe"),
        ("lanttern", "lantern"),
        ("ipick", "iron pickaxe"),  # alias
        ("dpick", "diamond pickaxe"),  # alias
        ("charm", "lucky charm"),  # alias
        ("tnt", "dynamite"),  # alias
        ("spaceship", None),  # genuinely unknown
        ("", None),
    ],
)
def test_resolution_table(query, expected):
    assert resolve_item_name(query, _CANDIDATES) == expected


def test_only_ever_returns_a_candidate():
    # An alias whose target isn't in the candidate pool must not leak out.
    assert resolve_item_name("tnt", ("pickaxe",)) is None


def test_resolves_against_dict_keys():
    assert resolve_item_name("torch", {"torch": {"wood": 2}}) == "torch"
