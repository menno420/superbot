"""M3B — distinct fact_types for endpoints that share ``_btd6challengedocument``.

The Ninja Kiwi API reuses the ``_btd6challengedocument`` model name
across four endpoint families:

* race metadata
* boss metadata
* odyssey maps (per-stage)
* challenge metadata

Each parser must emit its own ``fact_type`` (and ``entity_kind``) so
downstream grounding code can filter cleanly without inspecting the
upstream ``model`` field — the plan's "fact_type classifies, not the
model name" rule.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services.parsers.ninjakiwi_bosses import parse_boss_metadata  # noqa: E402
from services.parsers.ninjakiwi_challenges import (  # noqa: E402
    parse_challenge_metadata,
)
from services.parsers.ninjakiwi_odyssey import parse_odyssey_maps  # noqa: E402
from services.parsers.ninjakiwi_races import parse_race_metadata  # noqa: E402

_FIXTURES = Path(__file__).parents[4] / "tests" / "fixtures" / "ninjakiwi"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def test_all_four_endpoints_advertise_btd6challengedocument_model():
    """Confirm the test premise: these four fixtures really do share
    the same upstream model name (so distinct fact_types are required
    on the consumer side)."""
    expected = "_btd6challengedocument"
    pairs = [
        ("btd6_races_Reversed_Loop_mpbd7tcu_metadata.json", expected),
        ("btd6_bosses_Diamondback5_mpfz8mi4_metadata_standard.json", expected),
        ("btd6_odyssey_mpbd858c_easy_maps.json", expected),
        ("btd6_challenges_challenge_rot284420260525.json", expected),
    ]
    for fixture_name, model_name in pairs:
        payload = _load(fixture_name)
        assert payload["model"]["name"] == model_name, fixture_name


def test_each_parser_emits_a_distinct_fact_type():
    race_facts = parse_race_metadata(
        _load("btd6_races_Reversed_Loop_mpbd7tcu_metadata.json"),
        path_params={"raceID": "Reversed_Loop_mpbd7tcu"},
    )
    boss_facts = parse_boss_metadata(
        _load("btd6_bosses_Diamondback5_mpfz8mi4_metadata_standard.json"),
        path_params={"bossID": "Diamondback5_mpfz8mi4", "difficulty": "standard"},
    )
    odyssey_facts = parse_odyssey_maps(
        _load("btd6_odyssey_mpbd858c_easy_maps.json"),
        path_params={"odysseyID": "mpbd858c", "difficulty": "easy"},
    )
    challenge_facts = parse_challenge_metadata(
        _load("btd6_challenges_challenge_rot284420260525.json"),
    )

    assert race_facts and boss_facts and odyssey_facts and challenge_facts

    fact_types = {
        race_facts[0]["fact_type"],
        boss_facts[0]["fact_type"],
        odyssey_facts[0]["fact_type"],
        challenge_facts[0]["fact_type"],
    }
    assert fact_types == {
        "btd6.race_metadata",
        "btd6.boss_metadata",
        "btd6.odyssey_maps",
        "btd6.challenge_metadata",
    }


def test_each_parser_uses_a_distinct_entity_kind():
    """``entity_kind`` is the secondary grouping axis. Each endpoint
    family addresses a different conceptual entity even though the
    upstream model is identical."""
    race_facts = parse_race_metadata(
        _load("btd6_races_Reversed_Loop_mpbd7tcu_metadata.json"),
        path_params={"raceID": "Reversed_Loop_mpbd7tcu"},
    )
    boss_facts = parse_boss_metadata(
        _load("btd6_bosses_Diamondback5_mpfz8mi4_metadata_standard.json"),
        path_params={"bossID": "Diamondback5_mpfz8mi4", "difficulty": "standard"},
    )
    odyssey_facts = parse_odyssey_maps(
        _load("btd6_odyssey_mpbd858c_easy_maps.json"),
        path_params={"odysseyID": "mpbd858c", "difficulty": "easy"},
    )
    challenge_facts = parse_challenge_metadata(
        _load("btd6_challenges_challenge_rot284420260525.json"),
    )

    entity_kinds = {
        race_facts[0]["entity_kind"],
        boss_facts[0]["entity_kind"],
        odyssey_facts[0]["entity_kind"],
        challenge_facts[0]["entity_kind"],
    }
    assert entity_kinds == {
        "btd6_race",
        "btd6_boss_difficulty",
        "btd6_odyssey_stage",
        "btd6_challenge",
    }


@pytest.mark.parametrize(
    "facts_loader",
    [
        lambda: parse_race_metadata(
            _load("btd6_races_Reversed_Loop_mpbd7tcu_metadata.json"),
            path_params={"raceID": "Reversed_Loop_mpbd7tcu"},
        ),
        lambda: parse_boss_metadata(
            _load("btd6_bosses_Diamondback5_mpfz8mi4_metadata_standard.json"),
            path_params={"bossID": "Diamondback5_mpfz8mi4", "difficulty": "standard"},
        ),
        lambda: parse_challenge_metadata(
            _load("btd6_challenges_challenge_rot284420260525.json"),
        ),
    ],
)
def test_no_parser_leaks_the_raw_model_name_into_facts(facts_loader):
    facts = facts_loader()
    for fact in facts:
        # The upstream model name must not influence downstream filtering.
        assert "_btd6challengedocument" not in fact["fact_type"]
        assert "_btd6challengedocument" not in fact["entity_kind"]
