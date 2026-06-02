"""PR3 — btd6_context_service.build wires resolver + fact_store grounding.

Round-trip:  message text → ResolvedIntent → BTD6FactQuery rows →
fetch_for_intent → sanitised, source-labelled BTD6Context.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[3] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import btd6_context_service, btd6_fact_store  # noqa: E402


def _make_row(
    *,
    fact_type: str = "btd6.map_metadata",
    entity_kind: str = "btd6_map",
    entity_key: str = "TreeStump",
    trust_tier: int = 1,
    fetched_at: datetime | None = None,
    version: int = 1,
    body_json: dict | None = None,
    source_name: str = "data.ninjakiwi.com",
    source_kind: str = "official_api",
) -> dict:
    return {
        "id": 1,
        "source_id": 100,
        "fact_type": fact_type,
        "entity_kind": entity_kind,
        "entity_key": entity_key,
        "body_json": body_json or {"name": entity_key},
        "game_version": "54.3",
        "fetched_at": fetched_at or datetime.now(timezone.utc),
        "validated_at": None,
        "confidence": 1.0,
        "version": version,
        "source_key": "nk_btd6_maps_one",
        "source_name": source_name,
        "trust_tier": trust_tier,
        "source_kind": source_kind,
    }


# ---------------------------------------------------------------------------
# _render_fact / _sanitise / _relative_time unit checks
# ---------------------------------------------------------------------------


def test_render_fact_appends_source_label_and_relative_time():
    fetched = datetime.now(timezone.utc).replace(microsecond=0)
    fetched = fetched.replace(minute=(fetched.minute - 5) % 60)
    row = _make_row(
        body_json={"name": "TreeStump", "map": "TreeStump", "mode": "Standard"},
        fetched_at=fetched,
    )
    rendered = btd6_context_service._render_fact(row)
    assert "TreeStump" in rendered
    assert "map=TreeStump" in rendered
    assert "mode=Standard" in rendered
    assert "source: data.ninjakiwi.com" in rendered
    assert " ago)" in rendered or "just now)" in rendered


def test_render_fact_omits_url_fields_even_when_present_in_body():
    row = _make_row(
        body_json={
            "name": "Reversed Loop",
            "creator_url": "https://attacker.example/click-me",
            "metadata_url": "https://attacker.example/data",
            "map_url": "https://attacker.example/img.png",
            "profile_url": "https://attacker.example/profile",
        },
    )
    rendered = btd6_context_service._render_fact(row)
    assert "attacker.example" not in rendered
    assert "https://" not in rendered.replace(
        # the only legitimate URL fragment is the source label itself,
        # but we use a plain domain there (no scheme).
        "data.ninjakiwi.com",
        "",
    )


def test_sanitise_strips_control_chars_and_caps_length():
    raw = "Hello\x00World\x07!" + "x" * 300
    cleaned = btd6_context_service._sanitise(raw)
    assert "\x00" not in cleaned
    assert "\x07" not in cleaned
    assert len(cleaned) <= 240


def test_sanitise_returns_empty_for_non_string():
    assert btd6_context_service._sanitise(None) == ""
    assert btd6_context_service._sanitise(42) == ""
    assert btd6_context_service._sanitise({"x": 1}) == ""


def test_relative_time_buckets_into_s_m_h_d():
    from datetime import timedelta

    now = datetime.now(timezone.utc)
    rel = btd6_context_service._relative_time
    assert rel(now) in ("just now", "0s ago")
    # Use timedelta math so the test is wall-clock-independent —
    # the prior ``minute - 5`` arithmetic broke whenever the current
    # minute was < 5 and rolled into the future.
    assert "m ago" in rel(now - timedelta(minutes=5))
    assert "h ago" in rel(now - timedelta(hours=3))
    assert "d ago" in rel(now - timedelta(days=2))


def test_render_fact_treats_id_na_as_no_headline():
    row = _make_row(body_json={"id": "n/a", "name": "Reversed Loop"})
    rendered = btd6_context_service._render_fact(row)
    # The body's name is preferred since id="n/a" is rejected.
    assert "Reversed Loop" in rendered
    assert "n/a" not in rendered


# ---------------------------------------------------------------------------
# _intent_to_queries
# ---------------------------------------------------------------------------


class _FakeEntity:
    def __init__(self, id_: str) -> None:
        self.id = id_


class _FakeIntent:
    def __init__(
        self,
        *,
        towers: list[_FakeEntity] | None = None,
        heroes: list[_FakeEntity] | None = None,
        maps: list[_FakeEntity] | None = None,
        modes: list[_FakeEntity] | None = None,
        confidence: float = 0.0,
    ) -> None:
        self.towers = tuple(towers or [])
        self.heroes = tuple(heroes or [])
        self.maps = tuple(maps or [])
        self.modes = tuple(modes or [])
        self.confidence = confidence


def test_intent_to_queries_covers_every_resolver_entity_kind():
    intent = _FakeIntent(
        towers=[_FakeEntity("dart-monkey")],
        heroes=[_FakeEntity("quincy")],
        maps=[_FakeEntity("TreeStump")],
        modes=[_FakeEntity("standard")],
    )
    queries = btd6_context_service._intent_to_queries(intent)
    entity_kinds = sorted(q.entity_kind for q in queries)
    assert entity_kinds == ["btd6_hero", "btd6_map", "btd6_mode", "btd6_tower"]
    # fact_type is None — any fact about the entity matches.
    assert all(q.fact_type is None for q in queries)


def test_intent_to_queries_skips_entities_without_id():
    class _NoId:
        pass

    intent = _FakeIntent(towers=[_NoId(), _FakeEntity("dart-monkey")])  # type: ignore[list-item]
    queries = btd6_context_service._intent_to_queries(intent)
    assert len(queries) == 1
    assert queries[0].entity_key == "dart-monkey"


# ---------------------------------------------------------------------------
# build() end-to-end
# ---------------------------------------------------------------------------


async def test_build_with_no_intent_entities_returns_empty_facts(monkeypatch):
    monkeypatch.setattr(
        btd6_context_service,
        "_intent_to_queries",
        lambda _intent: [],
    )

    async def _explode(*args, **kwargs):
        raise AssertionError("fetch_for_intent must not run with no queries")

    monkeypatch.setattr(btd6_fact_store, "fetch_for_intent", _explode)
    ctx = await btd6_context_service.build("hello")
    assert ctx.facts == ()
    assert ctx.source_summary == btd6_context_service._FALLBACK_SOURCE_SUMMARY


async def test_build_renders_facts_with_source_label_when_rows_found(monkeypatch):
    monkeypatch.setattr(
        btd6_context_service,
        "_intent_to_queries",
        lambda _intent: [btd6_fact_store.BTD6FactQuery(None, "btd6_map", "TreeStump")],
    )

    async def _stub(queries, **kwargs):
        return [
            _make_row(
                body_json={"name": "TreeStump", "map": "TreeStump"},
                source_name="data.ninjakiwi.com",
            ),
        ]

    monkeypatch.setattr(btd6_fact_store, "fetch_for_intent", _stub)
    ctx = await btd6_context_service.build("how do I beat treestump?")
    assert len(ctx.facts) == 1
    fact = ctx.facts[0]
    assert "TreeStump" in fact
    assert "source: data.ninjakiwi.com" in fact
    assert ctx.source_summary == btd6_context_service._DEFAULT_SOURCE_SUMMARY


async def test_build_falls_back_when_resolver_raises(monkeypatch):
    def _explode(_text):
        raise RuntimeError("resolver down")

    monkeypatch.setattr(
        "services.btd6_resolver_service.resolve",
        _explode,
    )
    ctx = await btd6_context_service.build("anything")
    # Graceful: empty facts, default fallback summary, zero confidence.
    assert ctx.facts == ()
    assert ctx.confidence == 0.0


async def test_build_passes_confidence_through_from_resolver(monkeypatch):
    monkeypatch.setattr(
        "services.btd6_resolver_service.resolve",
        lambda _text: _FakeIntent(confidence=0.67),
    )

    async def _stub(queries, **kwargs):
        return []

    monkeypatch.setattr(btd6_fact_store, "fetch_for_intent", _stub)
    ctx = await btd6_context_service.build("text")
    assert ctx.confidence == pytest.approx(0.67)


async def test_build_caps_renderer_output_at_240_chars(monkeypatch):
    """Even with a verbose body, each rendered fact stays within the
    240-char cap so the instruction stack window is predictable."""
    monkeypatch.setattr(
        btd6_context_service,
        "_intent_to_queries",
        lambda _intent: [btd6_fact_store.BTD6FactQuery(None, "btd6_map", "x")],
    )

    async def _stub(queries, **kwargs):
        return [
            _make_row(
                body_json={
                    "name": "X" * 400,
                    "map": "Y" * 400,
                    "mode": "Z" * 400,
                },
            ),
        ]

    monkeypatch.setattr(btd6_fact_store, "fetch_for_intent", _stub)
    ctx = await btd6_context_service.build("text")
    assert len(ctx.facts) == 1
    assert len(ctx.facts[0]) <= 240


# ---------------------------------------------------------------------------
# build() upgrade grounding — the live failures from #444/#445 wired in
# ---------------------------------------------------------------------------


async def test_build_grounds_upgrade_by_abbreviation_without_tower():
    # "POD" alone used to return no facts ("I don't have verified data for POD").
    ctx = await btd6_context_service.build("POD cooldown")
    blob = "\n".join(ctx.facts)
    assert "[btd6_upgrade] Prince of Darkness" in blob
    assert "Wizard Monkey 0-0-5" in blob
    assert "0.275s cooldown" in blob


async def test_build_grounds_upgrade_minion_pierce_detail():
    ctx = await btd6_context_service.build("Prince of Darkness minion pierce?")
    blob = "\n".join(ctx.facts)
    reanimate = next(line for line in ctx.facts if "Reanimate" in line)
    assert "1 pierce" in reanimate
    assert "Undead Bloon buff" in blob


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("BEZ", "Bloon Exclusion Zone"),
        ("What are the stats for the MAD", "M.A.D"),
        ("What are PMFC's stats?", "Plasma Monkey Fan Club"),
        ("Prince of Darkness", "Prince of Darkness"),
        ("050 dart", "Plasma Monkey Fan Club"),
    ],
)
async def test_build_grounds_reported_upgrade_queries(query, expected):
    ctx = await btd6_context_service.build(query)
    assert any(
        f.startswith("[btd6_upgrade]") and expected in f for f in ctx.facts
    ), f"{query!r} did not ground {expected!r}: {ctx.facts}"


async def test_build_ignores_non_upgrade_text():
    # A plain greeting must not spuriously ground an upgrade.
    ctx = await btd6_context_service.build("hello there")
    assert not any(f.startswith("[btd6_upgrade]") for f in ctx.facts)


# ---------------------------------------------------------------------------
# build() paragon ability grounding (curated from bloonswiki)
# ---------------------------------------------------------------------------


async def test_build_grounds_paragon_abilities_by_paragon_name():
    ctx = await btd6_context_service.build("Magus Perfectus abilities")
    blob = "\n".join(ctx.facts)
    assert "Phoenix Explosion" in blob
    assert "Arcane Metamorphosis" in blob
    assert "40s cooldown" in blob


async def test_build_grounds_paragon_by_ability_name():
    # Naming only the ability grounds the owning paragon — searchable abilities.
    ctx = await btd6_context_service.build("what is Spikeageddon's cooldown")
    assert any(
        "Mega Massive Munitions Factory" in f and "Spikeageddon" in f and "75s" in f
        for f in ctx.facts
    ), ctx.facts


async def test_build_states_apex_plasma_master_has_no_ability():
    ctx = await btd6_context_service.build("does Apex Plasma Master have an ability")
    assert any("no activated ability" in f for f in ctx.facts)


async def test_build_grounds_paragon_nonlinear_scaling_note():
    ctx = await btd6_context_service.build("Magus Perfectus stats at degree 50")
    blob = "\n".join(ctx.facts)
    assert "do NOT scale linearly" in blob
    assert "square-root curve" in blob
    # Every grounding line stays within the per-fact cap.
    assert all(len(f) <= 240 for f in ctx.facts)


async def test_build_grounds_paragon_roster_and_excludes_heroes():
    ctx = await btd6_context_service.build("which paragons can't see camo")
    blob = "\n".join(f for f in ctx.facts if "paragon_roster" in f)
    assert "exactly 13 paragons" in blob
    assert "NEVER a paragon" in blob  # the hero-exclusion rule
    assert "Magus Perfectus" in blob and "Glaive Dominus" in blob
    # A specific-paragon question must NOT trigger the roster dump.
    specific = await btd6_context_service.build("Magus Perfectus cost")
    assert not any("paragon_roster" in f for f in specific.facts)
