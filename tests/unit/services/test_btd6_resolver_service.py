"""Resolver-service tests — deterministic NL → intent."""

from __future__ import annotations

from services.btd6_resolver_service import resolve


def test_resolves_dart_monkey_by_canonical_name():
    intent = resolve("Tell me about the Dart Monkey")
    assert any(t.id == "dart_monkey" for t in intent.towers)
    assert intent.confidence > 0.0


def test_resolves_dart_monkey_by_alias():
    intent = resolve("Is the dart good vs ceramics?")
    assert any(t.id == "dart_monkey" for t in intent.towers)


def test_resolves_round_number():
    intent = resolve("How do I survive round 63?")
    assert 63 in intent.candidate_round_numbers
    assert any(r.round_number == 63 for r in intent.rounds)


def test_resolves_short_round_form():
    intent = resolve("any tips for r78?")
    assert 78 in intent.candidate_round_numbers


def test_resolves_chimps_mode_alias():
    intent = resolve("What's a good CHIMPS start?")
    assert any(m.id == "chimps" for m in intent.modes)


def test_resolves_multiple_entities_boosts_confidence():
    single = resolve("Dart Monkey")
    triple = resolve("Dart Monkey on Logs in CHIMPS on round 28")
    assert triple.confidence >= single.confidence
    assert triple.confidence > 0.5


def test_no_matches_returns_zero_confidence():
    intent = resolve("hello there friend")
    assert intent.confidence == 0.0
    assert not intent.towers and not intent.rounds


def test_empty_input_returns_zero_confidence():
    intent = resolve("")
    assert intent.confidence == 0.0


def test_round_filter_drops_unknown_round():
    intent = resolve("round 200")  # outside the representative fixture
    assert 200 in intent.candidate_round_numbers
    # No matching round in the fixture → empty rounds tuple.
    assert not intent.rounds


def test_resolver_is_case_insensitive():
    upper = resolve("DART MONKEY ON LOGS")
    lower = resolve("dart monkey on logs")
    assert {t.id for t in upper.towers} == {t.id for t in lower.towers}
    assert {m.id for m in upper.maps} == {m.id for m in lower.maps}
