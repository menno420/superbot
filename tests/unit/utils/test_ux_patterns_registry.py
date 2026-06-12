"""UX pattern registry integrity — ids, completeness, spec-card caps."""

from __future__ import annotations

import pytest

# Importing the views package registers every exhibit's PatternSpec.
import views.ux_lab  # noqa: F401  — registration side effect is the point
from utils.ux_patterns import (
    REGISTRY,
    PatternCategory,
    PatternSpec,
    PatternStatus,
    category_counts,
    get_spec,
    register,
    specs_for,
    validate_registry,
)
from utils.ux_patterns.builders import spec_card


def test_registry_is_populated_per_wing():
    counts = category_counts()
    assert counts[PatternCategory.BUTTONS] == 10
    assert counts[PatternCategory.SELECTS] == 8
    assert counts[PatternCategory.MODALS] == 6
    assert counts[PatternCategory.EMBEDS] == 14
    assert counts[PatternCategory.PROBE] == 4


def test_registry_completeness():
    assert validate_registry() == []


def test_duplicate_registration_rejected():
    existing = next(iter(REGISTRY.values()))
    with pytest.raises(ValueError, match="duplicate"):
        register(existing)


def test_malformed_pattern_id_rejected():
    bad = PatternSpec(
        pattern_id="Not Snake",
        title="x",
        category=PatternCategory.BUTTONS,
        status=PatternStatus.STABLE,
        recommended_for=("y",),
        limits=("z",),
    )
    with pytest.raises(ValueError, match="snake_case"):
        register(bad)


def test_get_spec_unknown_id_names_the_problem():
    with pytest.raises(KeyError, match="unknown pattern_id"):
        get_spec("definitely_not_registered")


def test_every_spec_card_stays_within_embed_caps():
    for spec in REGISTRY.values():
        card = spec_card(spec)
        assert len(card) <= 6000, spec.pattern_id
        assert len(card.fields) <= 25, spec.pattern_id
        for f in card.fields:
            assert len(str(f.value)) <= 1024, spec.pattern_id


def test_specs_for_returns_only_that_category():
    for spec in specs_for(PatternCategory.MODALS):
        assert spec.category is PatternCategory.MODALS
        assert spec.requires_modal
