"""Tests for the Limbus → AI grounding context (``projmoon_context_service``).

Project Moon knowledge-domain PR 2 (Slice A item 2). The service turns the
committed Limbus fixtures into provenanced grounding fact lines that the AI
instruction stack injects. These pins cover per-entity matching, bounded roster
expansion, the ambiguous-bare-token exclusion, provenance survival, the fact cap,
and graceful degradation.
"""

from __future__ import annotations

import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

from services import projmoon_context_service as svc  # noqa: E402


def _joined(text: str) -> str:
    return "\n".join(svc.build(text).facts)


def test_named_sinner_is_grounded_with_origin() -> None:
    facts = svc.build("tell me about Faust in limbus").facts
    assert any(f.startswith("Faust:") for f in facts)
    joined = "\n".join(facts)
    assert "Goethe" in joined  # the literary origin is folded into the fact
    assert "source: Limbus Company structural data" in joined


def test_ego_grade_is_grounded_with_rank() -> None:
    facts = svc.build("what is the ZAYIN grade").facts
    assert any("E.G.O grade, rank 1/5" in f for f in facts)


def test_sin_is_grounded_with_affinity_colour() -> None:
    # "wrath" alone wouldn't route, but the context service is given the text
    # directly — it should still ground the Sin with its colour affinity.
    facts = svc.build("limbus wrath affinity").facts
    assert any(f.startswith("Wrath (Red Sin affinity):") for f in facts)


def test_roster_query_expands_to_the_whole_kind() -> None:
    facts = svc.build("list every sinner in limbus").facts
    # all 12 Sinners ground (12 <= the 16-fact cap)
    assert len(facts) == 12
    joined = "\n".join(facts)
    for name in ("Yi Sang", "Faust", "Don Quixote", "Heathcliff", "Outis"):
        assert f"{name}:" in joined


def test_damage_types_roster() -> None:
    facts = svc.build("what are the three damage types").facts
    joined = "\n".join(facts)
    for dmg in ("Slash:", "Pierce:", "Blunt:"):
        assert dmg in joined


def test_ambiguous_bare_tokens_do_not_match() -> None:
    # "he" / "don" / "sang" must not pull the HE grade / Don Quixote / Yi Sang.
    assert svc.build("he won the match").facts == ()
    assert svc.build("don't do that").facts == ()
    assert svc.build("i sang loudly").facts == ()


def test_distinctive_alias_still_matches_those_entities() -> None:
    # the ambiguous *bare* token is excluded, but a distinctive alias/canonical
    # still grounds the same entity.
    assert "Don Quixote:" in _joined("about don quixote")
    assert "Yi Sang:" in _joined("about yi sang")
    assert any("rank 3/5" in f for f in svc.build("the HE grade explained").facts)


def test_provenance_is_never_truncated_away() -> None:
    for fact in svc.build("list every sinner and the three damage types").facts:
        assert fact.endswith("(committed fixture))")
        assert len(fact) <= svc._FACT_TEXT_CAP


def test_fact_count_is_capped() -> None:
    # every roster at once would exceed the cap; the result is bounded.
    facts = svc.build(
        "list every sinner, the seven sins, all damage types, the ego grades, "
        "and all statuses",
    ).facts
    assert len(facts) <= svc._MAX_FACTS


def test_empty_and_non_limbus_text_grounds_nothing() -> None:
    assert svc.build("").facts == ()
    assert svc.build("what is the weather today").facts == ()


def test_facts_are_deterministic_for_a_fixed_message() -> None:
    assert svc.build("faust and heathcliff").facts == svc.build(
        "faust and heathcliff",
    ).facts
