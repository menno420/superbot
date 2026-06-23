"""Phase 9f / Track 5 PR 14 — AI review panel tests.

Pins:

* The aggregate panel renders counts per confidence and groups
  recommendations by subsystem.
* The "Accept all high-confidence" button adds every high
  recommendation to the accepted set; subsequent click is a no-op
  (deduplication by (subsystem, binding_name)).
* "Reject all AI suggestions" strips ``source="openai"``
  recommendations from both the draft and the accepted set.
* "Rerun deterministic-only" calls ``DeterministicAdvisor.suggest``
  with the stored snapshot, replaces the draft, and strips AI items
  from the accepted set.
* The per-recommendation view advances through the draft and
  transitions back to the parent overview when it runs out of items.
* AST invariants: panels don't import ``utils.db`` and don't call
  ``guild.create_*``.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.guild_snapshot import GuildSnapshot
from services.setup_plan import SetupPlanDraft, SetupRecommendation
from views.setup.ai_review.main_panel import (
    AcceptedSet,
    AIReviewPanelView,
    build_ai_review_embed,
)
from views.setup.ai_review.per_recommendation import (
    PerRecommendationView,
    build_per_recommendation_embed,
)


def _rec(
    *,
    subsystem="logging",
    binding="mod_channel",
    confidence="high",
    source="deterministic",
    target_id=100,
):
    return SetupRecommendation(
        subsystem=subsystem,
        binding_name=binding,
        target_kind="channel",
        target_id=target_id,
        target_name=f"{binding}-{target_id}",
        confidence=confidence,
        reason="x",
        source=source,
    )


def _author():
    member = MagicMock()
    member.id = 99
    return member


def _interaction(*, guild_id=1):
    interaction = MagicMock()
    interaction.guild_id = guild_id
    interaction.guild = MagicMock(id=guild_id)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    return interaction


def _create_rec(*, subsystem="welcome", binding="welcome_channel", name="welcome"):
    """A ``create``-mode recommendation (target_id=None) — the Edit case."""
    return SetupRecommendation(
        subsystem=subsystem,
        binding_name=binding,
        target_kind="channel",
        target_name=name,
        confidence="high",
        reason="x",
        mode="create",
        source="openai",
    )


# ---------------------------------------------------------------------------
# AcceptedSet
# ---------------------------------------------------------------------------


def test_accepted_set_dedupes_by_subsystem_and_binding():
    accepted = AcceptedSet()
    rec_a = _rec(target_id=100)
    rec_b = _rec(target_id=101)  # same (subsystem, binding)
    assert accepted.add(rec_a) is True
    assert accepted.add(rec_b) is False
    assert accepted.count == 1


def test_accepted_set_remove():
    accepted = AcceptedSet()
    rec = _rec()
    accepted.add(rec)
    assert accepted.remove("logging", "mod_channel") is True
    assert accepted.count == 0
    assert accepted.remove("logging", "mod_channel") is False


def test_accepted_set_contains():
    accepted = AcceptedSet()
    rec = _rec()
    assert accepted.contains(rec) is False
    accepted.add(rec)
    assert accepted.contains(rec) is True


# ---------------------------------------------------------------------------
# Aggregate embed
# ---------------------------------------------------------------------------


def test_build_ai_review_embed_renders_header_and_counts():
    draft = SetupPlanDraft(
        recommendations=(
            _rec(confidence="high"),
            _rec(binding="audit_channel", target_id=101, confidence="medium"),
        ),
    )
    embed = build_ai_review_embed(draft)
    desc = embed.description or ""
    assert "recommendations" in desc.lower()
    assert "High:** 1" in desc
    assert "Medium:** 1" in desc


def test_build_ai_review_embed_groups_by_subsystem():
    draft = SetupPlanDraft(
        recommendations=(
            _rec(subsystem="logging", binding="mod_channel"),
            _rec(subsystem="counting", binding="channel", target_id=200),
        ),
    )
    embed = build_ai_review_embed(draft)
    field_names = [f.name for f in embed.fields]
    assert "counting" in field_names
    assert "logging" in field_names


def test_build_ai_review_embed_shows_dropped_diagnostics():
    draft = SetupPlanDraft(
        recommendations=(),
        dropped=("openai: invalid",) * 7,
    )
    embed = build_ai_review_embed(draft)
    dropped = next(f for f in embed.fields if f.name == "Dropped")
    assert "openai" in (dropped.value or "")
    assert "2 more" in (dropped.value or "")


# ---------------------------------------------------------------------------
# AIReviewPanelView buttons
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_accept_high_button_adds_high_confidence_recs():
    draft = SetupPlanDraft(
        recommendations=(
            _rec(confidence="high"),
            _rec(binding="audit_channel", target_id=101, confidence="high"),
            _rec(binding="cleanup_channel", target_id=102, confidence="medium"),
        ),
    )
    view = AIReviewPanelView(_author(), draft=draft)
    interaction = _interaction()

    await view._accept_high.callback(interaction)

    assert view.accepted.count == 2
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_accept_high_button_is_idempotent():
    """A second click should NOT re-add the same recommendations."""
    draft = SetupPlanDraft(
        recommendations=(
            _rec(confidence="high"),
            _rec(binding="audit_channel", target_id=101, confidence="high"),
        ),
    )
    view = AIReviewPanelView(_author(), draft=draft)
    interaction = _interaction()

    await view._accept_high.callback(interaction)
    await view._accept_high.callback(interaction)

    assert view.accepted.count == 2


@pytest.mark.asyncio
async def test_review_each_transitions_to_per_recommendation_view():
    draft = SetupPlanDraft(recommendations=(_rec(confidence="high"),))
    view = AIReviewPanelView(_author(), draft=draft)
    interaction = _interaction()

    await view._review_each.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    new_view = interaction.response.edit_message.await_args.kwargs["view"]
    assert isinstance(new_view, PerRecommendationView)


@pytest.mark.asyncio
async def test_review_each_with_empty_draft_sends_ephemeral_message():
    view = AIReviewPanelView(_author(), draft=SetupPlanDraft())
    interaction = _interaction()

    await view._review_each.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert "empty" in interaction.response.send_message.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_reject_ai_strips_openai_recommendations_only():
    draft = SetupPlanDraft(
        recommendations=(
            _rec(confidence="high", source="openai"),
            _rec(
                binding="audit_channel",
                target_id=101,
                confidence="high",
                source="deterministic",
            ),
        ),
        source="openai",
    )
    accepted = AcceptedSet()
    accepted.add_many(draft.recommendations)
    view = AIReviewPanelView(_author(), draft=draft, accepted=accepted)
    interaction = _interaction()

    await view._reject_ai.callback(interaction)

    assert len(view.draft.recommendations) == 1
    assert view.draft.recommendations[0].source == "deterministic"
    # Accepted set drops the AI item too.
    assert view.accepted.count == 1
    assert view.accepted.recommendations[0].source == "deterministic"


@pytest.mark.asyncio
async def test_rerun_deterministic_replaces_draft():
    snapshot = GuildSnapshot(guild_id=1, guild_name="x", owner_id=99)
    deterministic_draft = SetupPlanDraft(
        recommendations=(
            _rec(confidence="medium", source="deterministic"),
        ),
        source="deterministic",
    )

    fake_advisor = MagicMock()
    fake_advisor.suggest = AsyncMock(return_value=deterministic_draft)

    view = AIReviewPanelView(
        _author(),
        draft=SetupPlanDraft(
            recommendations=(_rec(source="openai", confidence="high"),),
            source="openai",
        ),
        snapshot=snapshot,
    )
    interaction = _interaction()

    with patch(
        "views.setup.ai_review.main_panel.DeterministicAdvisor",
        return_value=fake_advisor,
    ):
        await view._rerun_deterministic.callback(interaction)

    fake_advisor.suggest.assert_awaited_once_with(snapshot)
    assert view.draft is deterministic_draft


@pytest.mark.asyncio
async def test_rerun_deterministic_refuses_without_snapshot():
    view = AIReviewPanelView(
        _author(),
        draft=SetupPlanDraft(recommendations=(_rec(),)),
        snapshot=None,
    )
    interaction = _interaction()

    await view._rerun_deterministic.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert (
        "no snapshot"
        in interaction.response.send_message.await_args.args[0].lower()
    )


@pytest.mark.asyncio
async def test_stage_final_stages_accepted_into_draft_and_opens_final_review():
    """The Stage & open Final review button adapts the accepted set to
    SetupOperations, writes them through the recommended-staging helper,
    and swaps the panel for the draft-driven FinalReviewView — closing the
    old dead end where accepted suggestions never applied.
    """
    import discord

    from views.setup.final_review import FinalReviewView

    rec = _rec(confidence="high")
    draft = SetupPlanDraft(recommendations=(rec,))
    accepted = AcceptedSet()
    accepted.add(rec)

    member = MagicMock(spec=discord.Member)
    member.id = 99
    view = AIReviewPanelView(member, draft=draft, accepted=accepted)
    interaction = _interaction()
    interaction.user = member

    with (
        patch(
            "services.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch("services.setup_access.can_apply_setup", return_value=True),
        patch(
            "services.setup_draft.replace_recommended_for_section",
            new_callable=AsyncMock,
        ) as replace_mock,
        patch(
            "services.setup_draft.list_ops",
            new_callable=AsyncMock,
            return_value=[MagicMock()],
        ),
    ):
        await view._stage_final.callback(interaction)

    replace_mock.assert_awaited_once()
    assert replace_mock.await_args.args[1] == "suggestions"
    sent_view = interaction.response.edit_message.await_args.kwargs["view"]
    assert isinstance(sent_view, FinalReviewView)


@pytest.mark.asyncio
async def test_stage_final_requires_accepted_recommendations():
    """With nothing accepted, the button nudges the operator instead of
    staging an empty draft.
    """
    import discord

    member = MagicMock(spec=discord.Member)
    member.id = 99
    view = AIReviewPanelView(member, draft=SetupPlanDraft(recommendations=(_rec(),)))
    interaction = _interaction()
    interaction.user = member

    await view._stage_final.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    assert "accept" in interaction.response.send_message.await_args.args[0].lower()


# ---------------------------------------------------------------------------
# PerRecommendationView
# ---------------------------------------------------------------------------


def test_per_recommendation_embed_renders_current_item():
    draft = SetupPlanDraft(
        recommendations=(
            _rec(confidence="high"),
            _rec(binding="audit_channel", target_id=101, confidence="medium"),
        ),
    )
    accepted = AcceptedSet()
    embed = build_per_recommendation_embed(draft, 1, accepted)
    assert "2 / 2" in (embed.title or "")
    assert "audit_channel" in (embed.description or "")


@pytest.mark.asyncio
async def test_per_recommendation_accept_advances():
    draft = SetupPlanDraft(
        recommendations=(
            _rec(),
            _rec(binding="audit_channel", target_id=101),
        ),
    )
    accepted = AcceptedSet()
    view = PerRecommendationView(
        _author(),
        draft=draft,
        accepted=accepted,
        index=0,
    )
    interaction = _interaction()

    await view._accept.callback(interaction)

    assert view.index == 1
    assert accepted.count == 1


@pytest.mark.asyncio
async def test_per_recommendation_deny_removes_and_advances():
    draft = SetupPlanDraft(recommendations=(_rec(),))
    accepted = AcceptedSet()
    accepted.add(draft.recommendations[0])
    parent = AIReviewPanelView(_author(), draft=draft, accepted=accepted)
    view = PerRecommendationView(
        _author(),
        draft=draft,
        accepted=accepted,
        index=0,
        parent_view=parent,
    )
    interaction = _interaction()

    await view._deny.callback(interaction)

    assert accepted.count == 0
    # End of list → returns to overview (parent's embed gets edited in).
    interaction.response.edit_message.assert_awaited()


# ---------------------------------------------------------------------------
# Edit (Q-0048 finalize — Accept / Deny / Edit)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_per_recommendation_edit_opens_modal_for_create_rec():
    """A `create` suggestion's Edit button opens the rename modal."""
    draft = SetupPlanDraft(recommendations=(_create_rec(),))
    view = PerRecommendationView(_author(), draft=draft, accepted=AcceptedSet(), index=0)
    interaction = _interaction()

    await view._edit.callback(interaction)

    interaction.response.send_modal.assert_awaited_once()
    interaction.response.edit_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_per_recommendation_edit_opens_repick_for_bind_channel():
    """A `bind` channel suggestion's Edit opens the re-pick target sub-view."""
    from views.setup.ai_review.per_recommendation import _RepickTargetView

    draft = SetupPlanDraft(recommendations=(_rec(),))  # _rec() is a bind channel
    view = PerRecommendationView(_author(), draft=draft, accepted=AcceptedSet(), index=0)
    interaction = _interaction()

    await view._edit.callback(interaction)

    interaction.response.send_modal.assert_not_awaited()
    interaction.response.edit_message.assert_awaited_once()
    assert isinstance(
        interaction.response.edit_message.await_args.kwargs["view"],
        _RepickTargetView,
    )


@pytest.mark.asyncio
async def test_per_recommendation_edit_explains_for_unselectable_bind_kind():
    """A `bind` suggestion of a non-pickable kind (thread/member) still explains."""
    thread_rec = SetupRecommendation(
        subsystem="logging",
        binding_name="thread_target",
        target_kind="thread",
        target_id=55,
        target_name="some-thread",
        confidence="medium",
        reason="x",
    )
    draft = SetupPlanDraft(recommendations=(thread_rec,))
    view = PerRecommendationView(_author(), draft=draft, accepted=AcceptedSet(), index=0)
    interaction = _interaction()

    await view._edit.callback(interaction)

    interaction.response.send_modal.assert_not_awaited()
    interaction.response.edit_message.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    assert interaction.response.send_message.await_args.kwargs.get("ephemeral") is True


def test_apply_retarget_swaps_id_and_name_and_accepts():
    rec = _rec(target_id=100)  # bind channel, target_name "mod_channel-100"
    draft = SetupPlanDraft(recommendations=(rec,))
    accepted = AcceptedSet()
    parent = AIReviewPanelView(_author(), draft=draft, accepted=accepted)
    view = PerRecommendationView(
        _author(), draft=draft, accepted=accepted, index=0, parent_view=parent,
    )

    edited = view.apply_retarget(rec, target_id=777, target_name="staff-logs")

    assert edited.target_id == 777
    assert edited.target_name == "staff-logs"
    assert edited.mode == "bind"
    assert view.draft.recommendations[0].target_id == 777
    assert parent.draft.recommendations[0].target_id == 777
    assert accepted.count == 1
    assert accepted.recommendations[0].target_id == 777


@pytest.mark.asyncio
async def test_repick_select_retargets_and_advances():
    from views.setup.ai_review.per_recommendation import _RepickTargetView

    rec = _rec(target_id=100)
    draft = SetupPlanDraft(recommendations=(rec,))
    accepted = AcceptedSet()
    parent = AIReviewPanelView(_author(), draft=draft, accepted=accepted)
    per = PerRecommendationView(
        _author(), draft=draft, accepted=accepted, index=0, parent_view=parent,
    )
    repick = _RepickTargetView(_author(), per_view=per, rec=rec)
    # Simulate the operator picking a channel (#777 "staff-logs"). NB: ``name``
    # is a reserved MagicMock kwarg, so set the attribute explicitly.
    picked = MagicMock(id=777)
    picked.name = "staff-logs"
    repick._select = MagicMock(values=[picked])
    interaction = _interaction()

    await repick._on_select(interaction)

    assert accepted.count == 1
    assert accepted.recommendations[0].target_id == 777
    assert accepted.recommendations[0].target_name == "staff-logs"
    # End of single-item list → returned to overview.
    interaction.response.edit_message.assert_awaited()


def test_apply_edit_rewrites_name_swaps_draft_and_accepts():
    rec = _create_rec(name="welcome")
    draft = SetupPlanDraft(recommendations=(rec,))
    accepted = AcceptedSet()
    parent = AIReviewPanelView(_author(), draft=draft, accepted=accepted)
    view = PerRecommendationView(
        _author(), draft=draft, accepted=accepted, index=0, parent_view=parent,
    )

    edited = view.apply_edit(rec, "greetings")

    assert edited.target_name == "greetings"
    assert edited.mode == "create"
    # Swapped into both this view's draft and the parent overview's draft.
    assert view.draft.recommendations[0].target_name == "greetings"
    assert parent.draft.recommendations[0].target_name == "greetings"
    # The edited recommendation is now accepted (exactly once — keyed by binding).
    assert accepted.count == 1
    assert accepted.recommendations[0].target_name == "greetings"


@pytest.mark.asyncio
async def test_edit_modal_submit_applies_and_advances():
    from views.setup.ai_review.per_recommendation import _EditRecommendationModal

    rec = _create_rec(name="welcome")
    draft = SetupPlanDraft(recommendations=(rec,))
    accepted = AcceptedSet()
    parent = AIReviewPanelView(_author(), draft=draft, accepted=accepted)
    view = PerRecommendationView(
        _author(), draft=draft, accepted=accepted, index=0, parent_view=parent,
    )
    modal = _EditRecommendationModal(view, rec)
    modal.name_input.default = "greetings"
    # Simulate the submitted value (TextInput.value reads the live component).
    object.__setattr__(modal.name_input, "_value", "greetings")
    interaction = _interaction()

    await modal.on_submit(interaction)

    assert accepted.count == 1
    assert accepted.recommendations[0].target_name == "greetings"
    # End of single-item list → returned to overview.
    interaction.response.edit_message.assert_awaited()


@pytest.mark.asyncio
async def test_per_recommendation_skip_does_not_modify_accepted():
    draft = SetupPlanDraft(
        recommendations=(_rec(), _rec(binding="audit_channel", target_id=101)),
    )
    accepted = AcceptedSet()
    view = PerRecommendationView(
        _author(),
        draft=draft,
        accepted=accepted,
        index=0,
    )
    interaction = _interaction()

    await view._skip.callback(interaction)

    assert view.index == 1
    assert accepted.count == 0


@pytest.mark.asyncio
async def test_per_recommendation_end_of_list_returns_to_overview():
    draft = SetupPlanDraft(recommendations=(_rec(),))
    accepted = AcceptedSet()
    parent = AIReviewPanelView(_author(), draft=draft, accepted=accepted)
    view = PerRecommendationView(
        _author(),
        draft=draft,
        accepted=accepted,
        index=0,
        parent_view=parent,
    )
    interaction = _interaction()

    await view._skip.callback(interaction)

    # The interaction got the parent view back.
    new_view = interaction.response.edit_message.await_args.kwargs["view"]
    assert new_view is parent


@pytest.mark.asyncio
async def test_per_recommendation_back_button_returns_immediately():
    draft = SetupPlanDraft(
        recommendations=(_rec(), _rec(binding="audit_channel", target_id=101)),
    )
    parent = AIReviewPanelView(_author(), draft=draft)
    view = PerRecommendationView(
        _author(),
        draft=draft,
        accepted=parent.accepted,
        index=0,
        parent_view=parent,
    )
    interaction = _interaction()

    await view._back.callback(interaction)

    # Returns immediately even at index 0.
    new_view = interaction.response.edit_message.await_args.kwargs["view"]
    assert new_view is parent


# ---------------------------------------------------------------------------
# Module invariants
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module_name",
    [
        "views.setup.ai_review.main_panel",
        "views.setup.ai_review.per_recommendation",
    ],
)
def test_module_has_no_db_imports(module_name):
    import importlib

    mod = importlib.import_module(module_name)
    src = mod.__file__
    assert src is not None
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    for forbidden in ("from utils.db import", "import utils.db"):
        assert forbidden not in text, (
            f"{module_name} must not import {forbidden}; views never "
            "write directly to the DB."
        )


@pytest.mark.parametrize(
    "module_name",
    [
        "views.setup.ai_review.main_panel",
        "views.setup.ai_review.per_recommendation",
    ],
)
def test_module_has_no_direct_discord_create_calls(module_name):
    import importlib

    mod = importlib.import_module(module_name)
    src = mod.__file__
    assert src is not None
    with open(src, encoding="utf-8") as fh:
        text = fh.read()
    for forbidden in (
        "guild.create_text_channel",
        "guild.create_role",
        "guild.create_category",
        "create_text_channel(",
        "create_role(",
        "create_category(",
    ):
        assert forbidden not in text, (
            f"{module_name} must not call {forbidden}; route through "
            "services.resource_provisioning when needed."
        )
