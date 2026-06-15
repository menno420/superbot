"""PR-E tests for context-service live-entity grounding."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest


@pytest.mark.asyncio
async def test_live_entity_lookup_populates_facts(monkeypatch):
    """A race question should land race facts in the context bundle."""
    from services import btd6_context_service
    from utils.db import btd6_sources as btd6_db

    async def _fake_search(*, entity_kind=None, fact_type=None, limit=50):
        if entity_kind == "btd6_race":
            return [
                {
                    "id": 7,
                    "fact_type": "race_metadata",
                    "entity_kind": "btd6_race",
                    "entity_key": "Reversed_Loop_mpbd7tcu",
                    "body_json": {"name": "Reversed Loop", "type": "race"},
                    "game_version": "44.0",
                    "fetched_at": datetime.now(tz=timezone.utc),
                    "validated_at": None,
                    "confidence": 1.0,
                    "version": 1,
                    "source_name": "Ninja Kiwi /races",
                },
            ]
        return []

    monkeypatch.setattr(btd6_db, "search_facts", _fake_search)

    ctx = await btd6_context_service.build("what is the current race?")
    assert ctx.facts, "expected at least one fact for the race intent"
    assert any("Reversed Loop" in f for f in ctx.facts)


@pytest.mark.asyncio
async def test_live_entity_lookup_caps_per_kind(monkeypatch):
    """One noisy kind cannot drown out others — per_kind_limit caps."""
    from services import btd6_context_service
    from utils.db import btd6_sources as btd6_db

    captured = []

    async def _fake_search(*, entity_kind=None, fact_type=None, limit=50):
        captured.append({"entity_kind": entity_kind, "limit": limit})
        return []

    monkeypatch.setattr(btd6_db, "search_facts", _fake_search)

    class _Intent:
        confidence = 0.5

        class _Match:
            def __init__(self, k):
                self.entity_kind = k
                self.matched_term = k

        live_entities = (_Match("btd6_race"), _Match("btd6_boss"))
        towers = ()
        heroes = ()
        maps = ()
        modes = ()
        rounds = ()
        ambiguous_terms = ()
        candidate_round_numbers = ()

    rows = await btd6_context_service._fetch_live_entity_rows(_Intent())
    assert rows == []
    assert {c["entity_kind"] for c in captured} == {"btd6_race", "btd6_boss"}
    # Each call respects the per-kind cap.
    for call in captured:
        assert call["limit"] == 3


@pytest.mark.asyncio
async def test_no_live_entities_skips_lookup(monkeypatch):
    """When the resolver yields no live entities, we never call
    search_facts."""
    from services import btd6_context_service
    from utils.db import btd6_sources as btd6_db

    called = False

    async def _fake_search(**_kw):
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(btd6_db, "search_facts", _fake_search)

    class _Intent:
        live_entities = ()

    rows = await btd6_context_service._fetch_live_entity_rows(_Intent())
    assert rows == []
    assert called is False


def test_coerce_body_handles_legacy_string_form():
    """Legacy btd6_facts rows store body_json as a JSON string — the
    grounding renderer must still decode them so it doesn't fall back
    to '(no summary)' for every fact in the bundle."""
    import json as _json

    from services import btd6_context_service

    body = {"name": "Reversed Loop", "type": "race"}
    assert btd6_context_service.coerce_body(body) is body
    assert btd6_context_service.coerce_body(_json.dumps(body)) == body
    assert btd6_context_service.coerce_body("not-json {") == {}
    assert btd6_context_service.coerce_body(None) == {}


def test_render_fact_decodes_legacy_string_body():
    """When body_json is a JSON-string (legacy double-encoded row),
    _render_fact must still produce a meaningful headline."""
    import json as _json

    from services import btd6_context_service

    body = {"name": "Reversed Loop", "type": "race"}
    row = {
        "body_json": _json.dumps(body),
        "source_name": "Ninja Kiwi /races",
        "fetched_at": datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        "version": 1,
    }
    rendered = btd6_context_service._render_fact(row)
    assert "Reversed Loop" in rendered
    assert "(no summary)" not in rendered


def test_render_fact_prefixes_entity_kind_tag():
    """Each grounded fact carries a ``[entity_kind]`` tag so the LLM
    can disambiguate boss / race / event names.

    Regression: a user asking "what was the previous boss?" was
    getting hallucinated training-data names because the rendered
    grounding had no kind tags and the model couldn't filter race
    names out of the candidate set.
    """
    from services import btd6_context_service

    row = {
        "entity_kind": "btd6_boss",
        "body_json": {"name": "Diamondback5"},
        "source_name": "Ninja Kiwi /bosses",
        "fetched_at": datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        "version": 1,
    }
    rendered = btd6_context_service._render_fact(row)
    assert rendered.startswith(
        "[btd6_boss] "
    ), f"expected entity_kind prefix, got: {rendered!r}"
    assert "Diamondback5" in rendered


def test_render_fact_no_tag_when_kind_missing():
    """Defensive: rows without ``entity_kind`` render unchanged."""
    from services import btd6_context_service

    row = {
        "body_json": {"name": "Mystery"},
        "fetched_at": datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
        "version": 1,
    }
    rendered = btd6_context_service._render_fact(row)
    assert not rendered.startswith("[")
    assert "Mystery" in rendered
