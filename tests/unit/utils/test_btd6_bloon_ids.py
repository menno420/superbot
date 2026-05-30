"""Unit tests for utils.btd6.bloon_ids — canonical bloon-name normalisation."""

from __future__ import annotations

from utils.btd6 import bloon_ids as bi


def test_normalize_bloon_name():
    assert bi.normalize_bloon_name("Black Bloon") == "black"
    assert bi.normalize_bloon_name("[[Black Bloon (BTD6)|Black Bloon]]") == "black"
    assert bi.normalize_bloon_name("Black") == "black"
    assert bi.normalize_bloon_name("ZOMG") == "zomg"
    assert bi.normalize_bloon_name("DynamiteBloon") == "dynamite"
    assert bi.normalize_bloon_name("Ceramic") == "ceramic"
    assert bi.normalize_bloon_name("Red Bloon (BTD6)") == "red"


def test_strip_links():
    assert bi.strip_links("[[X (BTD6)|Display]] ×2") == "Display ×2"
    assert bi.strip_links("[[Regrow]] plain") == "Regrow plain"


def test_constants():
    assert "red" in bi.BASIC_IDS and "moab" in bi.MOAB_IDS
    assert set(bi.MODIFIER_TOKENS) == {"camo", "regrow", "fortified"}


def test_parse_round_bloon_key():
    assert bi.parse_round_bloon_key("Red") == ("red", [])
    assert bi.parse_round_bloon_key("Zomg") == ("zomg", [])
    assert bi.parse_round_bloon_key("DdtCamo") == ("ddt", ["camo"])
    assert bi.parse_round_bloon_key("LeadFortifiedCamo") == (
        "lead",
        ["fortified", "camo"],
    )
    assert bi.parse_round_bloon_key("CeramicRegrowFortifiedCamo") == (
        "ceramic",
        ["regrow", "fortified", "camo"],
    )
