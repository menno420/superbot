"""Phase 9f / Track 5 PR 12 — deterministic advisor tests.

Pins:

* ``SetupRecommendation`` rejects unknown confidence values at
  ``__post_init__``.
* The rule table matches the documented channel/category name
  tokens at the right confidence (exact → high, prefix/suffix →
  medium, substring → low).
* Output validation drops every recommendation whose
  (subsystem, binding, kind) is not in the live schemas.
* Empty snapshot → empty draft, no dropped reasons.
* ``DeterministicAdvisor.suggest`` is identity-pure: calling it
  twice with the same snapshot produces the same recommendations
  in the same order.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SubsystemSchema,
)
from services.guild_snapshot import CategoryMeta, ChannelMeta, GuildSnapshot
from services.setup_plan import (
    DeterministicAdvisor,
    SetupPlanDraft,
    SetupRecommendation,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _channel(*, id, name, kind="text"):
    return ChannelMeta(
        id=id,
        name=name,
        type=kind,
        topic=None,
        parent_category=None,
        position=0,
        bot_can_view=True,
        bot_can_send=True,
        bot_can_embed=True,
    )


def _category(*, id, name):
    return CategoryMeta(id=id, name=name, position=0, bot_can_manage=True)


def _snapshot(*, channels=(), categories=()):
    return GuildSnapshot(
        guild_id=1,
        guild_name="Test",
        owner_id=99,
        channels=tuple(channels),
        categories=tuple(categories),
    )


def _spec(name: str, kind: BindingKind) -> BindingSpec:
    return BindingSpec(
        name=name,
        kind=kind,
        required=True,
        hint="",
        capability_required=f"{name}.bind",
    )


@pytest.fixture
def _full_schemas():
    """A schema dict that satisfies every rule's (subsystem,
    binding) so validation passes."""
    schemas = {
        "logging": SubsystemSchema(
            subsystem="logging",
            bindings=(
                _spec("rules_channel", BindingKind.CHANNEL),
                _spec("mod_channel", BindingKind.CHANNEL),
                _spec("cleanup_channel", BindingKind.CHANNEL),
                _spec("audit_channel", BindingKind.CHANNEL),
            ),
        ),
        "onboarding": SubsystemSchema(
            subsystem="onboarding",
            bindings=(_spec("welcome_channel", BindingKind.CHANNEL),),
        ),
        "general": SubsystemSchema(
            subsystem="general",
            bindings=(_spec("main_channel", BindingKind.CHANNEL),),
        ),
        "commands": SubsystemSchema(
            subsystem="commands",
            bindings=(_spec("bot_channel", BindingKind.CHANNEL),),
        ),
        "counting": SubsystemSchema(
            subsystem="counting",
            bindings=(_spec("channel", BindingKind.CHANNEL),),
        ),
        "economy": SubsystemSchema(
            subsystem="economy",
            bindings=(_spec("announce_channel", BindingKind.CHANNEL),),
        ),
        "moderation": SubsystemSchema(
            subsystem="moderation",
            bindings=(_spec("staff_category", BindingKind.CATEGORY),),
        ),
    }
    with patch(
        "core.runtime.subsystem_schema.all_schemas",
        return_value=schemas,
    ):
        yield schemas


@pytest.fixture
def _empty_schemas():
    with patch(
        "core.runtime.subsystem_schema.all_schemas",
        return_value={},
    ):
        yield {}


# ---------------------------------------------------------------------------
# SetupRecommendation construction
# ---------------------------------------------------------------------------


def test_setup_recommendation_rejects_unknown_confidence():
    with pytest.raises(ValueError, match="confidence"):
        SetupRecommendation(
            subsystem="logging",
            binding_name="mod_channel",
            target_kind="channel",
            target_id=1,
            target_name="mod-log",
            confidence="totally_made_up",
            reason="x",
        )


def test_setup_plan_draft_query_helpers():
    rec_a = SetupRecommendation(
        subsystem="logging",
        binding_name="mod_channel",
        target_kind="channel",
        target_id=1,
        target_name="mod-log",
        confidence="high",
        reason="x",
    )
    rec_b = SetupRecommendation(
        subsystem="counting",
        binding_name="channel",
        target_kind="channel",
        target_id=2,
        target_name="counting",
        confidence="medium",
        reason="x",
    )
    draft = SetupPlanDraft(recommendations=(rec_a, rec_b))
    assert draft.by_subsystem("logging") == (rec_a,)
    assert draft.by_confidence("medium") == (rec_b,)


# ---------------------------------------------------------------------------
# DeterministicAdvisor — happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_empty_snapshot_yields_empty_draft(_full_schemas):
    advisor = DeterministicAdvisor()
    draft = await advisor.suggest(_snapshot())
    assert draft.recommendations == ()
    assert draft.dropped == ()


@pytest.mark.asyncio
async def test_exact_channel_match_is_high_confidence(_full_schemas):
    advisor = DeterministicAdvisor()
    snap = _snapshot(channels=[_channel(id=100, name="mod-log")])
    draft = await advisor.suggest(snap)
    assert len(draft.recommendations) == 1
    rec = draft.recommendations[0]
    assert rec.subsystem == "logging"
    assert rec.binding_name == "mod_channel"
    assert rec.target_id == 100
    assert rec.confidence == "high"


@pytest.mark.asyncio
async def test_prefix_match_is_medium_confidence(_full_schemas):
    advisor = DeterministicAdvisor()
    snap = _snapshot(channels=[_channel(id=100, name="general-chat")])
    draft = await advisor.suggest(snap)
    assert len(draft.recommendations) == 1
    rec = draft.recommendations[0]
    # "general" is the first token, channel "general-chat" starts with it.
    assert rec.subsystem == "general"
    assert rec.confidence == "medium"


@pytest.mark.asyncio
async def test_substring_match_is_low_confidence(_full_schemas):
    advisor = DeterministicAdvisor()
    snap = _snapshot(channels=[_channel(id=100, name="public-shop-feed")])
    draft = await advisor.suggest(snap)
    assert len(draft.recommendations) == 1
    rec = draft.recommendations[0]
    # "shop" appears inside the name, not at start/end.
    assert rec.subsystem == "economy"
    assert rec.confidence == "low"


@pytest.mark.asyncio
async def test_recommendations_sorted_by_confidence_then_subsystem(_full_schemas):
    advisor = DeterministicAdvisor()
    snap = _snapshot(
        channels=[
            _channel(id=100, name="public-shop-feed"),  # economy, low
            _channel(id=101, name="audit-log"),  # logging.audit_channel, high
            _channel(id=102, name="bot-commands"),  # commands.bot_channel, high
        ]
    )
    draft = await advisor.suggest(snap)
    confidences = [r.confidence for r in draft.recommendations]
    # high entries before low entries.
    assert confidences == ["high", "high", "low"]
    # within the same confidence, alphabetised by (subsystem, binding).
    high_subs = [r.subsystem for r in draft.recommendations if r.confidence == "high"]
    assert high_subs == sorted(high_subs)


@pytest.mark.asyncio
async def test_category_rule_emits_category_recommendation(_full_schemas):
    advisor = DeterministicAdvisor()
    snap = _snapshot(categories=[_category(id=200, name="Staff")])
    draft = await advisor.suggest(snap)
    assert len(draft.recommendations) == 1
    rec = draft.recommendations[0]
    assert rec.subsystem == "moderation"
    assert rec.binding_name == "staff_category"
    assert rec.target_kind == "category"
    assert rec.target_id == 200


@pytest.mark.asyncio
async def test_advisor_keeps_highest_confidence_per_slot(_full_schemas):
    """If two channels match the same binding, only the
    highest-confidence one survives."""
    advisor = DeterministicAdvisor()
    snap = _snapshot(
        channels=[
            _channel(id=100, name="mod-log"),  # high
            _channel(id=101, name="mod-log-archive"),  # medium (prefix)
        ]
    )
    draft = await advisor.suggest(snap)
    recs = draft.recommendations
    assert len(recs) == 1
    assert recs[0].target_id == 100
    assert recs[0].confidence == "high"


# ---------------------------------------------------------------------------
# Validation — drop invalid recommendations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recommendation_dropped_when_subsystem_not_in_schema(_empty_schemas):
    advisor = DeterministicAdvisor()
    snap = _snapshot(channels=[_channel(id=100, name="mod-log")])
    draft = await advisor.suggest(snap)
    assert draft.recommendations == ()
    assert any("not registered" in r for r in draft.dropped)


@pytest.mark.asyncio
async def test_recommendation_dropped_when_binding_kind_mismatches():
    # logging.mod_channel declared as ROLE — advisor proposes channel.
    schemas = {
        "logging": SubsystemSchema(
            subsystem="logging",
            bindings=(_spec("mod_channel", BindingKind.ROLE),),
        ),
    }
    with patch(
        "core.runtime.subsystem_schema.all_schemas",
        return_value=schemas,
    ):
        advisor = DeterministicAdvisor()
        snap = _snapshot(channels=[_channel(id=100, name="mod-log")])
        draft = await advisor.suggest(snap)
    assert draft.recommendations == ()
    assert any("kind" in r and "advisor proposed channel" in r for r in draft.dropped)


@pytest.mark.asyncio
async def test_recommendation_dropped_when_binding_name_not_declared():
    # Only an unrelated binding declared.
    schemas = {
        "logging": SubsystemSchema(
            subsystem="logging",
            bindings=(_spec("some_other_channel", BindingKind.CHANNEL),),
        ),
    }
    with patch(
        "core.runtime.subsystem_schema.all_schemas",
        return_value=schemas,
    ):
        advisor = DeterministicAdvisor()
        snap = _snapshot(channels=[_channel(id=100, name="mod-log")])
        draft = await advisor.suggest(snap)
    assert draft.recommendations == ()
    assert any("not declared" in r for r in draft.dropped)


# ---------------------------------------------------------------------------
# Deterministic stability
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_advisor_is_deterministic(_full_schemas):
    """Calling the advisor twice with the same snapshot returns
    the same recommendations in the same order — important for
    test-suite stability and operator predictability."""
    advisor = DeterministicAdvisor()
    snap = _snapshot(
        channels=[
            _channel(id=100, name="bot-commands"),
            _channel(id=101, name="audit-log"),
            _channel(id=102, name="mod-log"),
        ]
    )
    a = await advisor.suggest(snap)
    b = await advisor.suggest(snap)
    assert a == b
