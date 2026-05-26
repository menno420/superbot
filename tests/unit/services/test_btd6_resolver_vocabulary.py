"""PR-E tests for the BTD6 live-entity vocabulary registry."""

from __future__ import annotations

from services.btd6_resolver_vocabulary import (
    known_entity_kinds,
    resolve_live_entities,
)


def test_known_entity_kinds_covers_each_live_kind():
    kinds = known_entity_kinds()
    expected = {
        "btd6_race",
        "btd6_boss",
        "btd6_ct",
        "btd6_ct_tile",
        "btd6_odyssey",
        "btd6_challenge",
        "btd6_event",
        "btd6_race_leaderboard_row",
    }
    assert expected <= kinds


def test_recognises_race():
    matches, _ambig = resolve_live_entities("what's the current race today?")
    kinds = {m.entity_kind for m in matches}
    assert "btd6_race" in kinds


def test_recognises_boss_by_name():
    matches, _ambig = resolve_live_entities(
        "what is the diamondback strategy?",
    )
    kinds = {m.entity_kind for m in matches}
    assert "btd6_boss" in kinds


def test_recognises_ct_index():
    matches, _ambig = resolve_live_entities("what is the current ct?")
    kinds = {m.entity_kind for m in matches}
    assert "btd6_ct" in kinds
    assert "btd6_ct_tile" not in kinds


def test_recognises_ct_tiles_as_tile_kind():
    matches, _ambig = resolve_live_entities("explain ct tiles")
    kinds = {m.entity_kind for m in matches}
    assert "btd6_ct_tile" in kinds
    # Note: bare "ct" token also matches btd6_ct; that is expected behaviour.
    # The key invariant is that ct_tile kind is resolved — not that ct kind is absent.


def test_recognises_ct_tile_singular():
    matches, _ambig = resolve_live_entities("what does this ct tile do?")
    kinds = {m.entity_kind for m in matches}
    assert "btd6_ct_tile" in kinds


def test_recognises_relic_tile():
    matches, _ambig = resolve_live_entities("show me relic tiles")
    kinds = {m.entity_kind for m in matches}
    assert "btd6_ct_tile" in kinds


def test_recognises_contested_territory_tile():
    matches, _ambig = resolve_live_entities("contested territory tile info")
    kinds = {m.entity_kind for m in matches}
    assert "btd6_ct_tile" in kinds


def test_recognises_odyssey():
    matches, _ambig = resolve_live_entities("can you do the easy odyssey?")
    kinds = {m.entity_kind for m in matches}
    assert "btd6_odyssey" in kinds


def test_recognises_challenge():
    matches, _ambig = resolve_live_entities("how do I beat the daily challenge?")
    kinds = {m.entity_kind for m in matches}
    assert "btd6_challenge" in kinds


def test_recognises_event():
    matches, _ambig = resolve_live_entities("are there any live events?")
    kinds = {m.entity_kind for m in matches}
    assert "btd6_event" in kinds


def test_recognises_leaderboard():
    matches, _ambig = resolve_live_entities("show me the race leaderboard")
    kinds = {m.entity_kind for m in matches}
    assert "btd6_race_leaderboard_row" in kinds


def test_ambiguous_current_alone_flagged():
    """The bare word "current" could mean current race / boss / CT /
    odyssey / event / challenge — refuse and let the caller emit
    ambiguous_term audit."""
    _matches, ambiguous = resolve_live_entities("what's current?")
    assert "current" in ambiguous


def test_empty_text_returns_empty():
    matches, ambig = resolve_live_entities("")
    assert matches == []
    assert ambig == []


def test_no_match_returns_empty():
    matches, ambig = resolve_live_entities("hello world")
    assert matches == []
    assert ambig == []


def test_dedupes_repeated_terms():
    matches, _ambig = resolve_live_entities("race race race")
    # The "race" surface term should only produce one match.
    by_kind = [m for m in matches if m.entity_kind == "btd6_race"]
    assert len(by_kind) == 1
