"""Path/line-aware BTD6 resolution — Layer A of the absence-claim guard.

The bug class this pins (``docs/btd6/btd6-absence-claim-guard-design.md`` §4.1):
path/line phrasing like "bomb shooter middle path" resolves to no single upgrade,
so ``resolve_upgrade`` returns ``none``, nothing grounds, and the model fills the
vacuum with a confident false negative ("that path has no MOAB bonus"). The MOAB
bonus is committed, reachable data — it was just never *queried*. These tests pin
that a ``<tower> <direction> path`` reference now resolves to the whole path and
grounds every tier (the +15/+30/+99 vs MOAB-Class data the design proved reachable),
while staying conservative enough that incidental "top tier" / "bottom line" phrasing
never fires.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import (  # noqa: E402
    btd6_context_service,
    btd6_upgrade_detail_service,
    btd6_upgrade_service,
)

resolve_path_reference = btd6_upgrade_service.resolve_path_reference
path_grounding_for_query = btd6_upgrade_detail_service.path_grounding_for_query


# --- resolve_path_reference --------------------------------------------------


def test_canonical_middle_path_resolves_to_all_five_tiers():
    """The design's canonical repro: "bomb shooter middle path"."""
    ref = resolve_path_reference("bomb shooter middle path")
    assert ref is not None
    assert ref.tower_id == "bomb_shooter"
    assert ref.path == "mid" and ref.path_index == 2
    # All five tiers, in tier order 1..5.
    assert [u.tier for u in ref.tiers] == [1, 2, 3, 4, 5]
    names = [u.canonical for u in ref.tiers]
    assert "MOAB Mauler" in names
    assert "MOAB Assassin" in names
    assert "MOAB Eliminator" in names


@pytest.mark.parametrize(
    ("query", "expected_path"),
    [
        ("dart monkey top path", "top"),
        ("dart monkey upper path", "top"),
        ("wizard middle path", "mid"),
        ("wizard mid path", "mid"),
        ("super monkey center path", "mid"),
        ("super monkey centre path", "mid"),
        ("super monkey central path", "mid"),
        ("wizard bottom path", "bot"),
        ("ninja monkey bot path", "bot"),
        ("ninja monkey lower path", "bot"),
    ],
)
def test_direction_synonyms_map_to_the_right_path(query, expected_path):
    ref = resolve_path_reference(query)
    assert ref is not None, f"{query!r} should resolve"
    assert ref.path == expected_path


def test_all_three_paths_resolve_for_one_tower():
    paths = {
        resolve_path_reference(f"dart monkey {word} path").path
        for word in ("top", "middle", "bottom")
    }
    assert paths == {"top", "mid", "bot"}


def test_tier_text_does_not_narrow_the_path():
    """"<tower> <path> path tier 4" still grounds the whole path (we want the
    model to see every tier, not just the one named)."""
    ref = resolve_path_reference("wizard bottom path tier 4")
    assert ref is not None
    assert [u.tier for u in ref.tiers] == [1, 2, 3, 4, 5]


# --- conservatism (must NOT fire) --------------------------------------------


def test_path_phrase_without_a_tower_does_not_resolve():
    assert resolve_path_reference("middle path") is None
    assert resolve_path_reference("what is the best bottom path") is None


def test_direction_without_the_path_keyword_does_not_resolve():
    # "top tier" is not a path reference; the literal "path" token is required.
    assert resolve_path_reference("top tier dart monkey") is None
    assert resolve_path_reference("bomb shooter middle") is None
    assert resolve_path_reference("the best dart monkey upgrades") is None


def test_idiomatic_negation_does_not_resolve():
    # "the bottom line is ..." — direction word present, but no tower and no
    # adjacent "path" token, so it must stay out.
    assert resolve_path_reference("the bottom line is profit") is None


def test_named_upgrade_without_a_path_phrase_does_not_resolve():
    # A specific tier named outright resolves via resolve_upgrade, not here.
    assert resolve_path_reference("how much damage does moab mauler do") is None


# --- path_grounding_for_query ------------------------------------------------


def test_path_grounding_surfaces_the_tier_roster_and_moab_bonus():
    lines = path_grounding_for_query("bomb shooter middle path")
    assert lines, "the canonical path query must ground something"
    # A header line names every tier — the direct absence-claim antidote.
    header = lines[0]
    assert header.startswith("[btd6_path]")
    for name in ("MOAB Mauler", "MOAB Assassin", "MOAB Eliminator"):
        assert name in header
    # The previously-unqueried numeric data is now grounded verbatim.
    joined = "\n".join(lines)
    assert "+15 damage vs MOAB-Class" in joined
    assert "+99 damage vs MOAB-Class" in joined


def test_path_grounding_is_empty_for_a_non_path_query():
    assert path_grounding_for_query("bomb shooter stats") == []
    assert path_grounding_for_query("how good is the dart monkey") == []


def test_explicitly_named_tier_is_not_double_grounded():
    """A tier the user names outright is skipped from the per-tier render (Pass 3c
    grounds it) but still appears in the header roster."""
    lines = path_grounding_for_query("bomb shooter middle path moab eliminator")
    assert "MOAB Eliminator" in lines[0]  # still in the roster header
    identity_lines = [
        ln for ln in lines if ln.startswith("[btd6_upgrade] MOAB Eliminator =")
    ]
    assert identity_lines == [], "named tier should not be re-rendered in full"
    # A tier the user did NOT name is still rendered in full.
    assert any(ln.startswith("[btd6_upgrade] MOAB Mauler =") for ln in lines)


# --- build() integration -----------------------------------------------------


@pytest.mark.asyncio
async def test_build_grounds_a_path_reference():
    ctx = await btd6_context_service.build("bomb shooter middle path")
    path_lines = [f for f in ctx.facts if f.startswith("[btd6_path]")]
    assert path_lines, f"no path grounding in: {ctx.facts!r}"
    assert any("+15 damage vs MOAB-Class" in f for f in ctx.facts)


@pytest.mark.asyncio
async def test_build_does_not_add_path_grounding_for_a_plain_tower_query():
    ctx = await btd6_context_service.build("bomb shooter stats")
    assert not any(f.startswith("[btd6_path]") for f in ctx.facts)
