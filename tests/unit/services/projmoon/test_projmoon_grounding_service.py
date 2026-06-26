"""Tests for the Limbus answer-faithfulness verifier (``projmoon_grounding_service``).

Project Moon knowledge-domain Slice A follow-up (b) — the prose-faithfulness
validation guard (plan §6). These pins cover the name-index discipline (distinctive
Sinners + E.G.O letters in, common-English categories out), the grounded /
unsupported verdicts, the fail-open-on-error posture, and the constraint / refusal
string helpers.
"""

from __future__ import annotations

import sys
from pathlib import Path

_DISBOT = Path(__file__).parents[4] / "disbot"
if str(_DISBOT) not in sys.path:
    sys.path.insert(0, str(_DISBOT))

import pytest  # noqa: E402

from services import projmoon_context_service as ctx_svc  # noqa: E402
from services import projmoon_grounding_service as svc  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_index() -> None:
    svc._reset_for_tests()
    yield
    svc._reset_for_tests()


def _grounded_facts(text: str) -> tuple[str, ...]:
    """The real grounding facts the context service would inject for ``text``."""
    return ctx_svc.build(text).facts


# --- distinctive proper names: caught when unsupported -----------------------


def test_unsupported_sinner_name_is_not_grounded() -> None:
    # Facts ground Faust only; a reply that drifts to Heathcliff is unsupported.
    facts = _grounded_facts("tell me about Faust in limbus")
    verdict = svc.validate_projmoon_reply(
        "Faust is steady, and Heathcliff hits hard too.",
        facts=facts,
    )
    assert not verdict.grounded
    assert "heathcliff" in verdict.offending_names
    assert "entity_name_unsupported" in verdict.notes


def test_supported_sinner_name_is_grounded() -> None:
    facts = _grounded_facts("tell me about Faust in limbus")
    verdict = svc.validate_projmoon_reply(
        "Faust is one of the twelve Sinners.",
        facts=facts,
    )
    assert verdict.grounded
    assert verdict.offending_names == ()


def test_multiword_sinner_name_matches_as_phrase() -> None:
    facts = _grounded_facts("who is Faust")  # no Don Quixote here
    verdict = svc.validate_projmoon_reply(
        "Don Quixote charges in with a lance.",
        facts=facts,
    )
    assert not verdict.grounded
    assert "don quixote" in verdict.offending_names


def test_roster_facts_ground_every_sinner_named() -> None:
    facts = _grounded_facts("list every sinner in limbus")
    verdict = svc.validate_projmoon_reply(
        "The roster includes Faust, Heathcliff, Outis and Gregor.",
        facts=facts,
    )
    assert verdict.grounded


# --- common-English categories are NOT single-token matched ------------------


def test_sin_and_status_words_are_not_offending() -> None:
    # No grounding facts at all; ordinary English words that happen to be Sin /
    # status / damage-type names must never be treated as proper-name evidence.
    verdict = svc.validate_projmoon_reply(
        "Pride and wrath can make you slash out in a fit of gloom and burn bridges.",
        facts=(),
    )
    assert verdict.grounded, verdict.offending_names


def test_ambiguous_ego_he_is_not_matched_bare() -> None:
    # "HE" the E.G.O grade is excluded; the pronoun "he" must not offend.
    verdict = svc.validate_projmoon_reply(
        "If he wants a strong unit, he should look around.",
        facts=(),
    )
    assert verdict.grounded


def test_distinctive_ego_letter_is_caught() -> None:
    # ALEPH is a distinctive token; unsupported it offends.
    verdict = svc.validate_projmoon_reply(
        "That is an ALEPH grade E.G.O.",
        facts=(),
    )
    assert not verdict.grounded
    assert "aleph" in verdict.offending_names


# --- robustness --------------------------------------------------------------


def test_empty_reply_grounds() -> None:
    assert svc.validate_projmoon_reply("", facts=()).grounded


def test_fails_open_on_internal_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom() -> None:
        raise RuntimeError("index build exploded")

    monkeypatch.setattr(svc, "_name_index", _boom)
    verdict = svc.validate_projmoon_reply("Heathcliff is unsupported here", facts=())
    # A verifier *bug* must not refuse a legitimate Limbus answer (fail open).
    assert verdict.grounded
    assert "verifier_error" in verdict.notes


def test_name_index_skips_common_categories() -> None:
    index = svc._name_index()
    # Sinners present, common-word categories absent from the single-token set.
    assert "faust" in index.single
    assert "gregor" in index.single
    for ordinary in ("wrath", "pride", "slash", "burn", "bleed", "charge", "he"):
        assert ordinary not in index.single


# --- helper strings ----------------------------------------------------------


def test_grounding_constraint_lists_offending_names() -> None:
    verdict = svc.validate_projmoon_reply(
        "Heathcliff is great", facts=_grounded_facts("Faust")
    )
    constraint = svc.build_grounding_constraint(verdict)
    assert "GROUNDING CORRECTION" in constraint
    assert "heathcliff" in constraint


def test_no_data_refusal_is_deterministic_prose() -> None:
    text = svc.no_data_refusal()
    assert "Project Moon" in text
    assert text == svc.no_data_refusal()  # stable
