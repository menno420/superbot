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
    # Match the Necromancer *attack* line (the wiki-era "Reanimate"; game
    # names since the v55.1 cutover) — key off the per-attack "pierce" stat.
    reanimate = next(
        line for line in ctx.facts if "Attack Necromancer" in line and "pierce" in line
    )
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


async def test_build_grounds_tower_upgrade_descriptions():
    # Live `grounding_failed`: "list all the upgrades and descriptions of the
    # super monkey" — build() listed upgrade NAMES + costs but not their prose,
    # so the model free-recalled the descriptions and the guard rejected them.
    # Every described card is now surfaced as a [btd6_upgrade] grounding line.
    ctx = await btd6_context_service.build(
        "list all the upgrades and descriptions of the super monkey",
    )
    desc_lines = [f for f in ctx.facts if f.startswith("[btd6_upgrade] Super Monkey ")]
    assert len(desc_lines) == 15  # all three paths, five tiers each
    blob = "\n".join(desc_lines)
    assert "Laser Blasts: Shoots powerful blasts of laser" in blob
    assert "True Sun God" in blob  # the tier-5 card is present, not dropped
    assert all("(source: BTD6 in-game description)" in f for f in desc_lines)


async def test_build_grounds_tower_costs_all_difficulties_and_cumulative():
    # Live grounding_failed: "list upgrade prices for super monkey" — build()
    # carried only the Medium per-buy price, so the model's all-difficulty /
    # cumulative table emitted derived numbers that weren't grounded. Every
    # derived number is now a [btd6_cost] line (header + base + 15 upgrades).
    ctx = await btd6_context_service.build("list me upgrade prices for super monkey")
    cost = [f for f in ctx.facts if f.startswith("[btd6_cost]")]
    assert len(cost) == 17
    blob = "\n".join(cost)
    # base scales per the documented multipliers (Easy = round5(2500 * 0.85)).
    assert "base placement: Easy $2,125, Medium $2,500" in blob
    # True Sun God Impoppable per-buy = round5(500000 * 1.2) = 600,000 — the kind
    # of derived figure that previously got rejected.
    assert "True Sun God" in blob and "I$600,000" in blob


async def test_build_ignores_non_upgrade_text():
    # A plain greeting must not spuriously ground an upgrade.
    ctx = await btd6_context_service.build("hello there")
    assert not any(f.startswith("[btd6_upgrade]") for f in ctx.facts)


async def test_build_grounds_parent_tower_for_upgrade_only_query():
    # PMFC names the upgrade but not its tower, so resolution used to attach only
    # the upgrade's ~4 detail lines — too thin for "what's the damage type when
    # the ability is active" to stand on, and the model refused despite holding
    # the Sharp fact (docs/btd6/btd6-absence-claim-guard-design.md Update 3 / §4.1,
    # mechanism 2). The parent tower (Dart Monkey) is now grounded alongside the
    # upgrade so a conceptual question has the full tower context to answer from.
    ctx = await btd6_context_service.build(
        "what is the damage type when plasma monkey fan club ability is activated",
    )
    # The upgrade grounding is still present...
    assert any(
        f.startswith("[btd6_upgrade]") and "Plasma Monkey Fan Club" in f
        for f in ctx.facts
    ), ctx.facts
    # ...and now the parent Dart Monkey tower identity is grounded too.
    assert any(
        f.startswith("[btd6_tower] Dart Monkey") and "base cost" in f for f in ctx.facts
    ), ctx.facts


async def test_build_grounds_parent_tower_for_abbreviation_only_query():
    # The same enrichment for an abbreviation that resolves to a different tower:
    # POD -> Wizard Monkey (not Dart Monkey), proving the parent is the upgrade's
    # own tower, not a hardcoded fallback.
    ctx = await btd6_context_service.build("POD cooldown")
    assert any(f.startswith("[btd6_upgrade] Prince of Darkness") for f in ctx.facts)
    assert any(
        f.startswith("[btd6_tower] Wizard Monkey") and "base cost" in f
        for f in ctx.facts
    ), ctx.facts


async def test_build_does_not_double_ground_a_named_parent_tower():
    # When the tower IS named, Pass 3 already grounds it; the parent-tower pass
    # must dedupe so it is not grounded a second time (which would duplicate the
    # identity + 17 [btd6_cost] lines). This query names Dart Monkey AND resolves
    # one of its own upgrades (PMFC) — the exact dedup path.
    ctx = await btd6_context_service.build("dart monkey plasma monkey fan club stats")
    identity = [
        f
        for f in ctx.facts
        if f.startswith("[btd6_tower] Dart Monkey") and "base cost" in f
    ]
    assert len(identity) == 1, ctx.facts  # grounded exactly once, not doubled
    cost_lines = [f for f in ctx.facts if f.startswith("[btd6_cost]")]
    assert len(cost_lines) == 17  # header + base + 15 — not doubled


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


async def test_build_grounds_hero_roster_with_costs():
    # Regression (post-#468 faithfulness guard): heroes had no roster grounding
    # (only paragons did), so "which heroes are in the game" reached the guard
    # with zero facts and was refused. The roster must also carry COSTS — a
    # name-only roster let the model's listed hero costs read as ungrounded
    # numbers and refused the whole answer.
    from core.runtime.ai.contracts import AITask
    from services import btd6_grounding_service

    ctx = await btd6_context_service.build("which heroes are in the game?")
    blob = "\n".join(f for f in ctx.facts if "hero_roster" in f)
    assert "17 heroes" in blob
    assert "Quincy" in blob and "Gwendolin" in blob and "Benjamin" in blob
    assert "$540" in blob  # Quincy's base cost is grounded, not just the name
    # A realistic cost-listing answer now grounds end-to-end.
    answer = "BTD6 has 17 heroes: Quincy ($540), Gwendolin ($725), Benjamin ($1200)."
    verdict = btd6_grounding_service.validate_btd6_reply(
        answer,
        facts=tuple(ctx.facts),
        task=AITask.BTD6_ANSWER,
    )
    assert verdict.grounded is True
    # "list all heroes" must ground too; a specific-hero question must NOT.
    listed = await btd6_context_service.build("list all heroes in btd6")
    assert any("hero_roster" in f for f in listed.facts)
    specific = await btd6_context_service.build("Quincy cost")
    assert not any("hero_roster" in f for f in specific.facts)


async def test_build_grounds_tower_roster_with_costs_and_category():
    ctx = await btd6_context_service.build("list all primary towers")
    blob = "\n".join(f for f in ctx.facts if "tower_roster" in f)
    assert "towers" in blob
    assert "Dart Monkey" in blob
    assert "$200" in blob and "primary" in blob  # cost + category grounded
    # A named-entity question ("dart monkey stats") must NOT dump the roster.
    specific = await btd6_context_service.build("dart monkey stats")
    assert not any("tower_roster" in f for f in specific.facts)


@pytest.mark.asyncio
async def test_build_grounds_map_summary_counts():
    # Live test: the bot recited stale training counts (25/28/22/14, "~73"/"76"
    # water — even labelled "verified") because no aggregate count was grounded.
    # The summary now grounds the real figures (total, by-difficulty, water/land).
    ctx = await btd6_context_service.build("how many maps have water")
    blob = "\n".join(f for f in ctx.facts if "[btd6_map]" in f)
    # 86 real player maps — the 3 non-standard (Blons / Base Editor Map / Protect
    # the Yacht, IsStandard=False) are filtered out of the catalogue.
    assert "86 maps total" in blob
    assert "67 have water" in blob and "19 are land-only" in blob
    assert "26 Beginner" in blob and "25 Intermediate" in blob
    # A specific-map question must NOT dump the summary.
    specific = await btd6_context_service.build("does Cargo have water")
    assert "86 maps total" not in "\n".join(specific.facts)


def test_deterministic_roster_reply_lists_full_rosters():
    # The model can't restate 17+ costs verbatim, so a list request floors to a
    # code-built roster that is always correct (it IS the source).
    heroes = btd6_context_service.deterministic_roster_reply("list all heroes")
    assert heroes is not None
    assert "17" in heroes
    for name in ("Quincy", "Benjamin", "Sauda", "Silas"):
        assert name in heroes
    assert "$540" in heroes  # Quincy's cost is code-built

    primary = btd6_context_service.deterministic_roster_reply("list all primary towers")
    assert primary is not None and "Dart Monkey" in primary
    assert "Sniper Monkey" not in primary  # military tower excluded by category

    paragons = btd6_context_service.deterministic_roster_reply("list all paragons")
    assert paragons is not None and "Apex Plasma Master" in paragons


def test_deterministic_roster_reply_skips_strategy_and_specific_questions():
    # Recommendation/opinion questions must reach the model, not dump a roster.
    assert btd6_context_service.deterministic_roster_reply("which hero is best") is None
    assert (
        btd6_context_service.deterministic_roster_reply("what tower should I use")
        is None
    )
    assert btd6_context_service.deterministic_roster_reply("dart monkey stats") is None


def test_deterministic_roster_reply_maps_water_land_removables():
    # The model gave FIVE different water counts (73/75/76/77), each falsely
    # "verified from the tool", while its own land-only list held the right 20.
    # Floor map count/list questions to code-built truth (69 water / 20 land /
    # 18 removables) so they can't be fabricated.
    r = btd6_context_service.deterministic_roster_reply
    count = r("how many maps have water")
    assert (
        count is not None and "67 have water" in count and "19 are land-only" in count
    )
    water = r("list all maps with water")
    assert water is not None and "67 of 86" in water and "Cubism" in water
    land = r("land-only maps")  # fires without a generic list verb
    assert land is not None and "19 of 86" in land
    assert "Monkey Meadow" in land and "Cornfield" in land
    rem = r("list maps with removables")
    assert rem is not None and "18 of 86" in rem
    assert "Cargo" in rem and "Bazaar" in rem
    # Combined request returns both sections.
    both = r("list all maps with water and all maps with removables")
    assert (
        both is not None and "Maps with water" in both and "removable obstacles" in both
    )
    # Strategy / opinion still reaches the model.
    assert r("which water map is best for beginners") is None


# --- hero per-level game descriptions (step 4b) -----------------------------


def test_render_hero_descriptions_grounds_every_defined_level():
    lines = btd6_context_service._render_hero_descriptions("ezili", "Ezili")
    # Ezili defines all 20 levels; each grounds one tagged, sourced line.
    assert len(lines) == 20
    assert all(ln.startswith("[btd6_hero_level] Ezili Level ") for ln in lines)
    assert all("(source: BTD6 in-game description)" in ln for ln in lines)


def test_render_hero_descriptions_surfaces_the_l11_showcase():
    # The doc's marquee case: Ezili L11 grants +50% pierce to reanimated Bloons.
    lines = btd6_context_service._render_hero_descriptions("ezili", "Ezili")
    l11 = next(ln for ln in lines if "Level 11:" in ln)
    assert "reanimated Bloons by 50%" in l11


def test_render_hero_descriptions_empty_for_unknown_hero():
    assert btd6_context_service._render_hero_descriptions("not_a_hero", "Nope") == []


async def test_build_grounds_hero_level_descriptions():
    ctx = await btd6_context_service.build("what does Ezili do at level 11?")
    levels = [f for f in ctx.facts if "[btd6_hero_level] Ezili Level 11:" in f]
    assert len(levels) == 1
    assert "reanimated Bloons by 50%" in levels[0]


# ---------------------------------------------------------------------------
# grounding budget — a single named tower must not flood the prompt
# ---------------------------------------------------------------------------

# A named tower now grounds identity + paths + description + paragon + per-upgrade
# descriptions + all-difficulty cumulative costs + stats. That broad auto-grounding
# fixed real grounding_failed refusals, but the per-tower fact count must stay
# bounded so it can't silently balloon the prompt. The current worst case is 60
# lines (Bomb Shooter / Wizard / Ninja); crossing this ceiling should be a
# deliberate decision — split grounding into intent-sensitive packets (descriptions
# vs. costs vs. stats), per the analysis recommendation — not a quiet drift.
_MAX_GROUNDING_LINES_PER_TOWER = 80


def test_fixture_tower_grounding_respects_line_cap_and_budget():
    from services import btd6_data_service

    towers = btd6_data_service.get_dataset().towers
    assert towers, "dataset has no towers — fixture load failed"

    worst_name, worst_lines = "", 0
    for tower in towers:
        lines = btd6_context_service._render_fixture_tower(tower)
        for line in lines:
            # Every emitted line goes through _cap, so no single grounding fact is
            # ever truncated mid-token (or runs unbounded) in the prompt.
            assert len(line) <= btd6_context_service._FACT_TEXT_CAP, (
                f"{tower.canonical} grounding line exceeds "
                f"{btd6_context_service._FACT_TEXT_CAP}-char cap: {line!r}"
            )
        if len(lines) > worst_lines:
            worst_name, worst_lines = tower.canonical, len(lines)

    assert worst_lines <= _MAX_GROUNDING_LINES_PER_TOWER, (
        f"{worst_name} now grounds {worst_lines} lines (ceiling "
        f"{_MAX_GROUNDING_LINES_PER_TOWER}). Rich auto-grounding has grown — split "
        "it into intent-sensitive packets before raising this ceiling."
    )


async def test_build_grounds_per_round_cash():
    # The per-round cash now reaches the model, so "how much money by round 80"
    # is groundable instead of free-recalled.
    ctx = await btd6_context_service.build("how much cash do I have by round 80")
    line = next(f for f in ctx.facts if f.startswith("[btd6_round] Round 80"))
    assert "cash this round ~$1,400" in line
    assert "cumulative ~$98,254" in line


async def test_build_grounds_freeplay_round_cash():
    # 81+ cash is now derived from our v55 composition (cyberquincy was stale —
    # freeplay cash was buffed), so freeplay rounds also ground their cash.
    ctx = await btd6_context_service.build("round 81")
    line = next(f for f in ctx.facts if f.startswith("[btd6_round] Round 81"))
    assert "cash this round ~$5,366" in line


# --- Pass 3e: powers / Monkey Knowledge / bosses catalog grounding ----------
# (#655 answerability item 5: these three fixture catalogs were reachable only
# through their dedicated AI tools; the shared pipeline never matched them.)


@pytest.mark.asyncio
async def test_power_named_in_text_grounds_catalog_fact():
    ctx = await btd6_context_service.build("what does monkey boost do")
    power_lines = [f for f in ctx.facts if f.startswith("[btd6_power]")]
    assert any("Monkey Boost (power)" in f for f in power_lines)


@pytest.mark.asyncio
async def test_monkey_knowledge_requires_knowledge_keyword():
    # MK names are generic English ("More Cash") — without the keyword the
    # catalog must stay silent so strategy prose doesn't ground stray facts.
    with_kw = await btd6_context_service.build("more cash monkey knowledge")
    assert any(
        f.startswith("[btd6_knowledge]") and "More Cash" in f for f in with_kw.facts
    )
    without_kw = await btd6_context_service.build("how to get more cash early")
    assert not any(f.startswith("[btd6_knowledge]") for f in without_kw.facts)


@pytest.mark.asyncio
async def test_boss_named_in_text_grounds_catalog_fact():
    ctx = await btd6_context_service.build("tell me about bloonarius")
    boss_lines = [f for f in ctx.facts if f.startswith("[btd6_boss]")]
    assert any("Bloonarius (boss bloon)" in f for f in boss_lines)
