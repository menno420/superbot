"""Tests for the create-and-bind setup recommendation path.

Covers the full thread of the "propose resource creation from a description"
feature: the model's ``mode`` validation, the AI payload parser building create
recs, the op adapter mapping a create rec to a ``create_<kind>`` provisioning
op, and the review embed marking creates distinctly.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SubsystemSchema,
)
from services.guild_snapshot import GuildSnapshot
from services.setup_ai_advisor import OpenAISetupAdvisor
from services.setup_operations import operations_from_recommendations
from services.setup_plan import SetupPlanDraft, SetupRecommendation


def _snap() -> GuildSnapshot:
    return GuildSnapshot(guild_id=1, guild_name="Test", owner_id=9)


# ---------------------------------------------------------------------------
# Model validation
# ---------------------------------------------------------------------------


def test_create_recommendation_allows_null_target_id():
    rec = SetupRecommendation(
        subsystem="logging",
        binding_name="mod_channel",
        target_kind="channel",
        target_name="mod-logs",
        confidence="high",
        reason="no mod-log channel exists yet",
        mode="create",
    )
    assert rec.mode == "create"
    assert rec.target_id is None


def test_bind_recommendation_requires_target_id():
    with pytest.raises(ValueError, match="requires a target_id"):
        SetupRecommendation(
            subsystem="logging",
            binding_name="mod_channel",
            target_kind="channel",
            target_name="mod-log",
            confidence="high",
            reason="match",
        )  # mode defaults to "bind"; no target_id


def test_create_recommendation_requires_target_name():
    with pytest.raises(ValueError, match="requires a target_name"):
        SetupRecommendation(
            subsystem="logging",
            binding_name="mod_channel",
            target_kind="channel",
            target_name="",
            confidence="high",
            reason="x",
            mode="create",
        )


def test_bad_mode_raises():
    with pytest.raises(ValueError, match="mode must be one of"):
        SetupRecommendation(
            subsystem="logging",
            binding_name="mod_channel",
            target_kind="channel",
            target_name="mod-log",
            confidence="high",
            reason="x",
            target_id=1,
            mode="frobnicate",
        )


# ---------------------------------------------------------------------------
# Op adapter
# ---------------------------------------------------------------------------


def test_create_rec_maps_to_create_channel_op():
    rec = SetupRecommendation(
        subsystem="logging",
        binding_name="mod_channel",
        target_kind="channel",
        target_name="mod-logs",
        confidence="high",
        reason="missing",
        mode="create",
    )
    ops = operations_from_recommendations([rec])
    assert len(ops) == 1
    op = ops[0]
    assert op.kind == "create_channel"
    assert op.resource_mode == "create"
    assert op.resource_name == "mod-logs"
    assert op.subsystem == "logging"
    assert op.binding_name == "mod_channel"
    assert op.target_id is None


def test_create_role_and_category_map_too():
    role = SetupRecommendation(
        subsystem="moderation",
        binding_name="staff_role",
        target_kind="role",
        target_name="Staff",
        confidence="medium",
        reason="m",
        mode="create",
    )
    cat = SetupRecommendation(
        subsystem="moderation",
        binding_name="staff_category",
        target_kind="category",
        target_name="Staff Zone",
        confidence="medium",
        reason="m",
        mode="create",
    )
    kinds = {op.kind for op in operations_from_recommendations([role, cat])}
    assert kinds == {"create_role", "create_category"}


def test_bind_rec_still_maps_to_bind_op():
    rec = SetupRecommendation(
        subsystem="logging",
        binding_name="mod_channel",
        target_kind="channel",
        target_name="mod-log",
        confidence="high",
        reason="match",
        target_id=123,
    )
    ops = operations_from_recommendations([rec])
    assert ops[0].kind == "bind_channel"
    assert ops[0].target_id == 123
    assert ops[0].resource_mode is None


# ---------------------------------------------------------------------------
# AI payload parsing
# ---------------------------------------------------------------------------


@pytest.fixture
def _logging_schema():
    schemas = {
        "logging": SubsystemSchema(
            subsystem="logging",
            bindings=(
                BindingSpec(
                    name="mod_channel",
                    kind=BindingKind.CHANNEL,
                    required=True,
                    hint="",
                    capability_required="logging.mod_channel.bind",
                ),
            ),
        ),
    }
    with patch(
        "core.runtime.subsystem_schema.all_schemas",
        return_value=schemas,
    ):
        yield schemas


def _fake_client(payload: dict) -> MagicMock:
    message = MagicMock()
    message.content = json.dumps(payload)
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=response)
    return client


@pytest.mark.asyncio
async def test_ai_create_recommendation_parsed(_logging_schema):
    payload = {
        "recommendations": [
            {
                "subsystem": "logging",
                "binding_name": "mod_channel",
                "target_kind": "channel",
                "mode": "create",
                "target_id": None,
                "target_name": "mod-logs",
                "confidence": "high",
                "reason": "no moderation log channel exists",
            },
        ],
    }
    advisor = OpenAISetupAdvisor(client=_fake_client(payload), api_key="sk-test")
    draft = await advisor.suggest(_snap())

    assert len(draft.recommendations) == 1
    rec = draft.recommendations[0]
    assert rec.mode == "create"
    assert rec.target_id is None
    assert rec.target_name == "mod-logs"


@pytest.mark.asyncio
async def test_ai_create_of_noncreatable_kind_dropped(_logging_schema):
    payload = {
        "recommendations": [
            {
                "subsystem": "logging",
                "binding_name": "mod_channel",
                "target_kind": "member",  # members are never created
                "mode": "create",
                "target_id": None,
                "target_name": "x",
                "confidence": "high",
                "reason": "y",
            },
        ],
    }
    advisor = OpenAISetupAdvisor(client=_fake_client(payload), api_key="sk-test")
    draft = await advisor.suggest(_snap())

    assert draft.recommendations == ()
    assert any("cannot create" in d for d in draft.dropped)


@pytest.mark.asyncio
async def test_ai_bind_with_explicit_mode_still_validates(_logging_schema):
    payload = {
        "recommendations": [
            {
                "subsystem": "logging",
                "binding_name": "mod_channel",
                "target_kind": "channel",
                "mode": "bind",
                "target_id": 555,
                "target_name": "mod-log",
                "confidence": "high",
                "reason": "exact match",
            },
        ],
    }
    advisor = OpenAISetupAdvisor(client=_fake_client(payload), api_key="sk-test")
    draft = await advisor.suggest(_snap())

    assert len(draft.recommendations) == 1
    assert draft.recommendations[0].mode == "bind"
    assert draft.recommendations[0].target_id == 555


# ---------------------------------------------------------------------------
# Review rendering
# ---------------------------------------------------------------------------


def test_review_embed_marks_create_recs():
    from views.setup.ai_review.main_panel import build_ai_review_embed

    rec = SetupRecommendation(
        subsystem="logging",
        binding_name="mod_channel",
        target_kind="channel",
        target_name="mod-logs",
        confidence="high",
        reason="missing",
        mode="create",
    )
    embed = build_ai_review_embed(SetupPlanDraft(recommendations=(rec,)))
    body = " ".join(f.value or "" for f in embed.fields)
    assert "➕ create" in body
