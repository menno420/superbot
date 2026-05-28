"""Tests for ``scripts/parse_bloonswiki.py`` (bloonswiki upgrades parser).

The sample page is synthesised from real, public cost numbers (facts) with
placeholder descriptions, and uses links with parentheses in the URL
(``Foo_(BTD6)``) to lock the nested-paren link-stripping fix.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO_ROOT / "scripts" / "parse_bloonswiki.py"

# (medium, easy, hard, impoppable) tuples that satisfy the cost formula.
_PATHS = {
    "Path 1": [
        ("Bigger Bombs", 250, 210, 270, 300),
        ("Heavy Bombs", 650, 550, 700, 780),
        ("Really Big Bombs", 1100, 935, 1190, 1320),
        ("Bloon Impact", 2800, 2380, 3025, 3360),
        ("Bloon Crush", 55000, 46750, 59400, 66000),
    ],
    "Path 2": [
        ("Faster Reload", 250, 210, 270, 300),
        ("Missile Launcher", 400, 340, 430, 480),
        ("MOAB Mauler", 1000, 850, 1080, 1200),
        ("MOAB Assassin", 3450, 2930, 3725, 4140),
        ("MOAB Eliminator", 26000, 22100, 28080, 31200),
    ],
    "Path 3": [
        ("Extra Range", 200, 170, 215, 240),
        ("Frag Bombs", 300, 255, 325, 360),
        ("Cluster Bombs", 700, 595, 755, 840),
        ("Recursive Cluster", 2500, 2125, 2700, 3000),
        ("Bomb Blitz", 30000, 25500, 32400, 36000),
    ],
}
_PARAGON = ("Ballistic Obliteration Missile Bunker", 600000, 510000, 648000, 720000)


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("parse_bloonswiki_under_test", _SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _diff_links() -> str:
    return (
        "[Easy](https://www.bloonswiki.com/Easy)"
        "[Medium](https://www.bloonswiki.com/Medium)"
        "[Hard](https://www.bloonswiki.com/Hard)"
        "[Impoppable](https://www.bloonswiki.com/Impoppable_(BTD6))"
    )


def _upgrade_block(name: str, medium: int, easy: int, hard: int, imp: int) -> list[str]:
    # Link URL carries parentheses to exercise the nested-paren stripper.
    slug = name.replace(" ", "_")
    return [
        f"[{name}](https://www.bloonswiki.com/{slug}_(BTD6))",
        "XP cost: 1,000",
        f"Placeholder description for {name}.",
        f"{_diff_links()}${easy:,}${medium:,}${hard:,}${imp:,}",
    ]


def _build_page(paths=_PATHS, paragon=_PARAGON) -> str:
    lines = [
        "The Test Tower is a [Primary](https://www.bloonswiki.com/Primary) tower "
        "that pops [Lead Bloons](https://www.bloonswiki.com/Lead_Bloon_(BTD6)).",
        "Upgrades",
        "[edit](https://www.bloonswiki.com/Test?action=edit)",
        "",
    ]
    for header, upgrades in paths.items():
        lines.append(header)
        for name, medium, easy, hard, imp in upgrades:
            lines.extend(_upgrade_block(name, medium, easy, hard, imp))
    if paragon is not None:
        name, medium, easy, hard, imp = paragon
        lines.append("[Paragon](https://www.bloonswiki.com/Paragon)")
        lines.extend(_upgrade_block(name, medium, easy, hard, imp))
    return "\n".join(lines)


def test_clean_parse_has_no_warnings(mod):
    result = mod.parse_upgrades_page(_build_page())
    assert result.ok, result.warnings
    assert result.intro.startswith("The Test Tower is a Primary tower")
    # Intro links fully stripped, including the nested-paren one.
    assert "(" not in result.intro.replace("Bloons TD", "") or "BTD6" not in result.intro


def test_names_are_clean(mod):
    result = mod.parse_upgrades_page(_build_page())
    for u in result.upgrades:
        assert ")" not in u.name and "(" not in u.name, u.name
        assert "BTD6" not in u.name


def test_costs_and_structure(mod):
    result = mod.parse_upgrades_page(_build_page())
    by_path = {p: [u for u in result.upgrades if u.section == p] for p in ("top", "mid", "bot")}
    assert [len(by_path[p]) for p in ("top", "mid", "bot")] == [5, 5, 5]
    top1 = by_path["top"][0]
    assert top1.name == "Bigger Bombs"
    assert top1.medium_cost == 250
    assert top1.tier == 1
    crush = by_path["top"][4]
    assert crush.medium_cost == 55000 and crush.tier == 5


def test_paragon_parsed(mod):
    result = mod.parse_upgrades_page(_build_page())
    paragons = [u for u in result.upgrades if u.section == "paragon"]
    assert len(paragons) == 1
    assert paragons[0].name == "Ballistic Obliteration Missile Bunker"
    assert paragons[0].medium_cost == 600000
    assert paragons[0].tier == 0


def test_short_path_warns(mod):
    short = {**_PATHS, "Path 1": _PATHS["Path 1"][:4]}
    result = mod.parse_upgrades_page(_build_page(paths=short, paragon=None))
    assert any("expected 5" in w for w in result.warnings)


def test_formula_mismatch_warns(mod):
    # Corrupt one Hard price so it no longer matches medium × 1.08.
    bad = {**_PATHS, "Path 3": [("Extra Range", 200, 170, 999, 240)] + _PATHS["Path 3"][1:]}
    result = mod.parse_upgrades_page(_build_page(paths=bad, paragon=None))
    assert any("formula" in w and "Extra Range" in w for w in result.warnings)
