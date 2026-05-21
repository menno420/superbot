"""Tests for Final Review's draft-driven apply path.

Pins:

* The final_review section reads ``services.setup_draft.list_ops``
  and constructs the view with ``ops=`` instead of ``accepted=``.
* ``_sort_ops_for_apply`` partitions ops by canonical phase order
  (resources → bindings → settings → cleanup → cog_routing →
   automation_add → automation_toggle → other).
* ``_apply_ops_in_order`` applies each op as its own single-op batch,
  ordered by phase, and the resulting ApplySummary aggregates the
  per-op results.
* On apply success the FinalReviewView clears the draft and marks
  the session complete.
* The embed renders both SetupRecommendation and SetupOperation
  shapes.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.setup_operations import (
    SetupOperation,
    SetupOperationBatchResult,
    SetupOperationResult,
)
from services.setup_plan import SetupRecommendation
from views.setup.final_review import (
    FinalReviewView,
    _apply_ops_in_order,
    _sort_ops_for_apply,
    build_final_review_embed,
)
from views.setup.sections import final_review as final_review_section


# ---------------------------------------------------------------------------
# _sort_ops_for_apply
# ---------------------------------------------------------------------------


def _op(kind: str, **kwargs) -> SetupOperation:
    return SetupOperation(kind=kind, subsystem=kwargs.pop("subsystem", "x"), **kwargs)


def test_sort_orders_resources_before_bindings():
    ordered = _sort_ops_for_apply(
        [_op("bind_channel"), _op("create_channel"), _op("set_setting")],
    )
    assert [o.kind for o in ordered] == [
        "create_channel",
        "bind_channel",
        "set_setting",
    ]


def test_sort_orders_full_phase_chain():
    ordered = _sort_ops_for_apply([
        _op("enable_automation_rule"),
        _op("set_cog_routing"),
        _op("set_cleanup_policy"),
        _op("add_automation_rule"),
        _op("set_setting"),
        _op("bind_channel"),
        _op("create_role"),
    ])
    kinds = [o.kind for o in ordered]
    assert kinds == [
        "create_role",
        "bind_channel",
        "set_setting",
        "set_cleanup_policy",
        "set_cog_routing",
        "add_automation_rule",
        "enable_automation_rule",
    ]


def test_sort_puts_unknown_kinds_at_the_back():
    ordered = _sort_ops_for_apply([
        _op("preset_unknown:weird"),
        _op("bind_channel"),
    ])
    assert ordered[0].kind == "bind_channel"
    assert ordered[1].kind == "preset_unknown:weird"


def test_sort_preserves_intra_phase_order():
    """Two ops in the same phase keep their input order."""
    a = _op("bind_channel", binding_name="a")
    b = _op("bind_channel", binding_name="b")
    ordered = _sort_ops_for_apply([a, b])
    assert ordered == [a, b]


# ---------------------------------------------------------------------------
# _apply_ops_in_order
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_ops_in_order_dispatches_each_op_in_phase_order():
    ops = [_op("bind_channel"), _op("create_channel"), _op("set_setting")]

    def _result(op):
        return SetupOperationResult(
            status="applied",
            operation=op,
            label=f"{op.kind}",
            mutation_id="m1",
        )

    async def fake_apply(ops_in, *, guild, actor, actor_type="user"):
        return SetupOperationBatchResult(results=[_result(ops_in[0])])

    with patch(
        "services.setup_operations.apply_operations",
        new=fake_apply,
    ):
        summary = await _apply_ops_in_order(ops, guild=MagicMock(), actor=MagicMock())

    # All three applied.
    assert len(summary.applied) == 3
    # The applied labels show the phase-order sort:
    # create_channel ran first, then bind_channel, then set_setting.
    assert summary.applied == ["create_channel", "bind_channel", "set_setting"]


@pytest.mark.asyncio
async def test_apply_ops_in_order_partitions_failures_and_skipped():
    ops = [
        _op("bind_channel", binding_name="a"),
        _op("create_channel"),
        _op("preset_unknown:weird"),
    ]

    async def fake_apply(ops_in, *, guild, actor, actor_type="user"):
        op = ops_in[0]
        if op.kind == "create_channel":
            return SetupOperationBatchResult(
                results=[
                    SetupOperationResult(
                        status="failed",
                        operation=op,
                        label=op.kind,
                        error="boom",
                    ),
                ],
            )
        if op.kind == "preset_unknown:weird":
            return SetupOperationBatchResult(
                results=[
                    SetupOperationResult(
                        status="not_yet_implemented",
                        operation=op,
                        label=op.kind,
                        error=f"kind {op.kind!r} not implemented",
                    ),
                ],
            )
        return SetupOperationBatchResult(
            results=[
                SetupOperationResult(
                    status="applied",
                    operation=op,
                    label=op.kind,
                    mutation_id="m",
                ),
            ],
        )

    with patch("services.setup_operations.apply_operations", new=fake_apply):
        summary = await _apply_ops_in_order(ops, guild=MagicMock(), actor=MagicMock())

    assert len(summary.applied) == 1
    assert len(summary.failed) == 1
    assert "boom" in summary.failed[0]
    # not_yet_implemented results land in summary.skipped; the error
    # text is appended inline so the operator sees the diagnostic.
    assert any("not implemented" in s for s in summary.skipped)


# ---------------------------------------------------------------------------
# FinalReviewView — ops=
# ---------------------------------------------------------------------------


def _owner_member():
    m = MagicMock(spec=discord.Member)
    m.id = 99
    m.guild = SimpleNamespace(owner_id=99)
    return m


def _interaction_with_guild():
    interaction = MagicMock()
    interaction.user = _owner_member()
    interaction.guild_id = 1
    interaction.guild = MagicMock(id=1)
    interaction.message = MagicMock(id=100)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.edit_message = AsyncMock()
    return interaction


def test_view_with_ops_disables_apply_when_ops_list_empty():
    view = FinalReviewView(_owner_member(), ops=[])
    apply_btn = next(c for c in view.children if isinstance(c, discord.ui.Button) and c.label == "Apply")
    assert apply_btn.disabled is True


def test_view_with_ops_enables_apply_when_ops_non_empty():
    view = FinalReviewView(_owner_member(), ops=[_op("bind_channel")])
    apply_btn = next(c for c in view.children if isinstance(c, discord.ui.Button) and c.label == "Apply")
    assert apply_btn.disabled is False


@pytest.mark.asyncio
async def test_view_apply_runs_ops_path_when_ops_set():
    """When constructed with ``ops=`` the apply button goes through
    ``_apply_ops_in_order`` rather than ``_apply_accepted``.
    """
    view = FinalReviewView(_owner_member(), ops=[_op("bind_channel")])
    interaction = _interaction_with_guild()

    with (
        patch(
            "views.setup.final_review._apply_ops_in_order",
            new_callable=AsyncMock,
        ) as ops_path,
        patch(
            "views.setup.final_review._apply_accepted",
            new_callable=AsyncMock,
        ) as recs_path,
        patch(
            "services.setup_draft.clear",
            new_callable=AsyncMock,
        ) as clear_mock,
        patch(
            "services.setup_session.mark_complete",
            new_callable=AsyncMock,
        ),
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            new_callable=AsyncMock,
        ),
    ):
        from views.setup.final_review import ApplySummary

        ops_path.return_value = ApplySummary(applied=["bind_channel"])
        await view._apply.callback(interaction)

    ops_path.assert_awaited_once()
    recs_path.assert_not_called()
    clear_mock.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_view_apply_runs_accepted_path_when_only_accepted_set():
    """Legacy AI / suggestions path: ``accepted=`` uses
    ``_apply_accepted`` and does NOT touch the draft store.
    """
    rec = SetupRecommendation(
        subsystem="logging",
        binding_name="mod_channel",
        target_kind="channel",
        target_id=42,
        target_name="#mod-log",
        confidence="high",
        reason="x",
        source="deterministic",
    )
    view = FinalReviewView(_owner_member(), accepted=[rec])
    interaction = _interaction_with_guild()

    with (
        patch(
            "views.setup.final_review._apply_ops_in_order",
            new_callable=AsyncMock,
        ) as ops_path,
        patch(
            "views.setup.final_review._apply_accepted",
            new_callable=AsyncMock,
        ) as recs_path,
        patch(
            "services.setup_draft.clear",
            new_callable=AsyncMock,
        ) as clear_mock,
        patch(
            "services.setup_session.mark_complete",
            new_callable=AsyncMock,
        ),
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            new_callable=AsyncMock,
        ),
    ):
        from views.setup.final_review import ApplySummary

        recs_path.return_value = ApplySummary(applied=["x"])
        await view._apply.callback(interaction)

    recs_path.assert_awaited_once()
    ops_path.assert_not_called()
    clear_mock.assert_not_called()  # legacy path does not touch the draft


# ---------------------------------------------------------------------------
# Final review section — loads draft
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_section_loads_draft_and_constructs_view_with_ops():
    """The section reads setup_draft.list_ops and passes the result
    to FinalReviewView's ``ops=`` parameter.
    """
    fake_ops = [_op("bind_channel", binding_name="mod_channel")]
    interaction = _interaction_with_guild()
    with patch(
        "services.setup_draft.list_ops",
        new_callable=AsyncMock,
        return_value=fake_ops,
    ) as list_mock:
        await final_review_section.run(interaction, MagicMock())
    list_mock.assert_awaited_once_with(1)
    interaction.response.send_message.assert_awaited_once()
    view = interaction.response.send_message.await_args.kwargs["view"]
    assert isinstance(view, FinalReviewView)
    assert view.ops == fake_ops


@pytest.mark.asyncio
async def test_section_tolerates_list_ops_failure():
    """A draft-store outage must not crash the section — Final
    review opens with an empty ops list so the operator at least
    sees the empty-state embed.
    """
    interaction = _interaction_with_guild()
    with patch(
        "services.setup_draft.list_ops",
        new_callable=AsyncMock,
        side_effect=RuntimeError("DB down"),
    ):
        await final_review_section.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()
    view = interaction.response.send_message.await_args.kwargs["view"]
    assert view.ops == []


# ---------------------------------------------------------------------------
# build_final_review_embed — accepts both shapes
# ---------------------------------------------------------------------------


def test_embed_renders_setup_operation_list():
    ops = [_op("bind_channel", binding_name="mod_channel", target_name="#mod-log")]
    embed = build_final_review_embed(ops)
    pending = next((f for f in embed.fields if f.name == "Pending"), None)
    assert pending is not None
    assert "mod_channel" in pending.value


def test_embed_says_operations_when_given_ops():
    embed = build_final_review_embed([_op("bind_channel")])
    assert "operation" in (embed.description or "").lower()


def test_embed_says_recommendations_when_given_recs():
    rec = SetupRecommendation(
        subsystem="logging",
        binding_name="mod_channel",
        target_kind="channel",
        target_id=42,
        target_name="#mod-log",
        confidence="high",
        reason="x",
        source="deterministic",
    )
    embed = build_final_review_embed([rec])
    assert "recommendation" in (embed.description or "").lower()
