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
* Phase 0 safety: on **full success** the FinalReviewView clears the
  draft and marks the session complete; on any failed / skipped
  result it preserves the draft, does NOT mark complete, and mounts
  :class:`PartialApplyRecoveryView` so the operator can retry or
  cancel.
* The apply path runs under
  :func:`services.setup_operations.acquire_setup_apply_lock`; a
  concurrent press is rejected with an ephemeral.
* The embed renders both SetupRecommendation and SetupOperation
  shapes; partial-failure embed surfaces a distinct title /
  description so the operator sees that setup is not complete.
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
    PartialApplyRecoveryView,
    _apply_ops_in_order,
    _sort_ops_for_apply,
    build_final_review_embed,
)
from views.setup.sections import final_review as final_review_section


@pytest.fixture(autouse=True)
def _reset_apply_lock():
    """The single-flight lock is module-level state; reset between tests."""
    from services.setup_operations import _reset_apply_inflight_for_tests

    _reset_apply_inflight_for_tests()
    yield
    _reset_apply_inflight_for_tests()

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
    interaction.response.edit_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.followup = MagicMock()
    interaction.followup.edit_message = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


def test_view_with_ops_disables_apply_when_ops_list_empty():
    view = FinalReviewView(_owner_member(), ops=[])
    apply_btn = next(c for c in view.children if isinstance(c, discord.ui.Button) and c.label == "Apply staged setup")
    assert apply_btn.disabled is True


def test_view_with_ops_enables_apply_when_ops_non_empty():
    view = FinalReviewView(_owner_member(), ops=[_op("bind_channel")])
    apply_btn = next(c for c in view.children if isinstance(c, discord.ui.Button) and c.label == "Apply staged setup")
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
async def test_view_apply_preserves_draft_on_failed_result():
    """Phase 0: any failed op preserves the draft and does NOT mark complete."""
    view = FinalReviewView(_owner_member(), ops=[_op("bind_channel")])
    interaction = _interaction_with_guild()

    with (
        patch(
            "views.setup.final_review._apply_ops_in_order",
            new_callable=AsyncMock,
        ) as ops_path,
        patch(
            "services.setup_draft.clear",
            new_callable=AsyncMock,
        ) as clear_mock,
        patch(
            "services.setup_session.mark_complete",
            new_callable=AsyncMock,
        ) as complete_mock,
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            new_callable=AsyncMock,
        ),
    ):
        from views.setup.final_review import ApplySummary

        ops_path.return_value = ApplySummary(
            applied=["one"],
            failed=["two: boom"],
        )
        await view._apply.callback(interaction)

    clear_mock.assert_not_called()
    complete_mock.assert_not_called()
    # The followup edit installed a PartialApplyRecoveryView instead of
    # the now-stale FinalReviewView.
    edit_kwargs = interaction.followup.edit_message.await_args.kwargs
    assert isinstance(edit_kwargs["view"], PartialApplyRecoveryView)
    embed = edit_kwargs["embed"]
    assert "partially applied" in (embed.description or "").lower() or \
        "partial" in (embed.title or "").lower()


@pytest.mark.asyncio
async def test_view_apply_preserves_draft_on_skipped_result():
    """skipped results (including NYI-folded ones) block completion."""
    view = FinalReviewView(_owner_member(), ops=[_op("bind_channel")])
    interaction = _interaction_with_guild()

    with (
        patch(
            "views.setup.final_review._apply_ops_in_order",
            new_callable=AsyncMock,
        ) as ops_path,
        patch(
            "services.setup_draft.clear",
            new_callable=AsyncMock,
        ) as clear_mock,
        patch(
            "services.setup_session.mark_complete",
            new_callable=AsyncMock,
        ) as complete_mock,
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            new_callable=AsyncMock,
        ),
    ):
        from views.setup.final_review import ApplySummary

        ops_path.return_value = ApplySummary(
            applied=["one"],
            skipped=["weird (not yet implemented)"],
        )
        await view._apply.callback(interaction)

    clear_mock.assert_not_called()
    complete_mock.assert_not_called()
    edit_kwargs = interaction.followup.edit_message.await_args.kwargs
    assert isinstance(edit_kwargs["view"], PartialApplyRecoveryView)


@pytest.mark.asyncio
async def test_view_apply_full_success_clears_and_marks_complete():
    """Full success: draft is cleared, session is marked complete, and
    (Phase 8) the SetupCompleteView is mounted so the operator can
    delete the now-empty setup channel or keep it.
    """
    from views.setup.final_review import SetupCompleteView

    view = FinalReviewView(_owner_member(), ops=[_op("bind_channel")])
    interaction = _interaction_with_guild()

    with (
        patch(
            "views.setup.final_review._apply_ops_in_order",
            new_callable=AsyncMock,
        ) as ops_path,
        patch(
            "services.setup_draft.clear",
            new_callable=AsyncMock,
        ) as clear_mock,
        patch(
            "services.setup_session.mark_complete",
            new_callable=AsyncMock,
        ) as complete_mock,
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            new_callable=AsyncMock,
        ),
    ):
        from views.setup.final_review import ApplySummary

        ops_path.return_value = ApplySummary(applied=["one"])
        await view._apply.callback(interaction)

    clear_mock.assert_awaited_once_with(1)
    complete_mock.assert_awaited_once_with(1)
    # Phase 8: on full success the SetupCompleteView is mounted with
    # the Delete / Keep cleanup buttons.  Partial-recovery NEVER gets
    # these buttons (pinned separately).
    edit_kwargs = interaction.followup.edit_message.await_args.kwargs
    assert isinstance(edit_kwargs["view"], SetupCompleteView)


@pytest.mark.asyncio
async def test_view_apply_single_flight_rejects_concurrent_press():
    """A second Apply press while one is in flight must be rejected with
    an ephemeral and never enter the apply path.
    """
    from services.setup_operations import (
        _reset_apply_inflight_for_tests,
        acquire_setup_apply_lock,
    )

    _reset_apply_inflight_for_tests()
    view = FinalReviewView(_owner_member(), ops=[_op("bind_channel")])
    interaction = _interaction_with_guild()

    # Manually mark guild 1 inflight so the apply path raises immediately.
    async with acquire_setup_apply_lock(1):
        with (
            patch(
                "views.setup.final_review._apply_ops_in_order",
                new_callable=AsyncMock,
            ) as ops_path,
            patch(
                "core.runtime.interaction_helpers.safe_defer",
                new_callable=AsyncMock,
            ),
        ):
            await view._apply.callback(interaction)

        ops_path.assert_not_called()
        interaction.response.send_message.assert_awaited()
        kwargs = interaction.response.send_message.await_args.kwargs
        msg_args = interaction.response.send_message.await_args.args
        text = (msg_args[0] if msg_args else kwargs.get("content", "")) or ""
        assert "already in progress" in text.lower()
        assert kwargs.get("ephemeral") is True


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


def test_embed_partial_state_signals_not_complete():
    """Partial-failure embed must make clear setup is not complete and
    the draft is preserved.
    """
    from views.setup.final_review import ApplySummary

    summary = ApplySummary(applied=["one"], failed=["two: boom"])
    embed = build_final_review_embed([_op("bind_channel")], summary=summary)
    title = (embed.title or "").lower()
    description = (embed.description or "").lower()
    assert "partial" in title or "partial" in description
    assert "not" in description and "complete" in description
    assert "preserved" in description
    # Footer surfaces the retry/cancel guidance.
    footer = (embed.footer.text or "").lower() if embed.footer else ""
    assert "retry" in footer
    assert "cancel" in footer


def test_embed_full_success_does_not_signal_partial():
    """Full-success embed must not falsely surface the partial state."""
    from views.setup.final_review import ApplySummary

    summary = ApplySummary(applied=["one", "two"])
    embed = build_final_review_embed([_op("bind_channel")], summary=summary)
    title = (embed.title or "").lower()
    assert "partial" not in title


# ---------------------------------------------------------------------------
# PartialApplyRecoveryView
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recovery_view_retry_reruns_apply_path():
    """Retry button re-runs the canonical apply flow under the same
    single-flight lock, with the same ops list, and renders the new
    result.  When the retry succeeds the draft is cleared.
    """
    from views.setup.final_review import ApplySummary

    initial_summary = ApplySummary(applied=["a"], failed=["b: boom"])
    recovery = PartialApplyRecoveryView(
        _owner_member(),
        ops=[_op("bind_channel")],
        accepted=[],
        summary=initial_summary,
    )
    interaction = _interaction_with_guild()

    with (
        patch(
            "views.setup.final_review._apply_ops_in_order",
            new_callable=AsyncMock,
        ) as ops_path,
        patch(
            "services.setup_draft.clear",
            new_callable=AsyncMock,
        ) as clear_mock,
        patch(
            "services.setup_session.mark_complete",
            new_callable=AsyncMock,
        ) as complete_mock,
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            new_callable=AsyncMock,
        ),
    ):
        ops_path.return_value = ApplySummary(applied=["a", "b"])
        await recovery._retry.callback(interaction)

    ops_path.assert_awaited_once()
    clear_mock.assert_awaited_once_with(1)
    complete_mock.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_recovery_view_retry_preserves_draft_on_second_failure():
    """Retry that itself fails / skips must preserve the draft again."""
    from views.setup.final_review import ApplySummary

    recovery = PartialApplyRecoveryView(
        _owner_member(),
        ops=[_op("bind_channel")],
        accepted=[],
        summary=ApplySummary(applied=[], failed=["x: boom"]),
    )
    interaction = _interaction_with_guild()

    with (
        patch(
            "views.setup.final_review._apply_ops_in_order",
            new_callable=AsyncMock,
        ) as ops_path,
        patch(
            "services.setup_draft.clear",
            new_callable=AsyncMock,
        ) as clear_mock,
        patch(
            "services.setup_session.mark_complete",
            new_callable=AsyncMock,
        ) as complete_mock,
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            new_callable=AsyncMock,
        ),
    ):
        ops_path.return_value = ApplySummary(failed=["x: still broken"])
        await recovery._retry.callback(interaction)

    clear_mock.assert_not_called()
    complete_mock.assert_not_called()


@pytest.mark.asyncio
async def test_recovery_view_cancel_preserves_draft():
    """Cancel just closes the recovery view; nothing else."""
    from views.setup.final_review import ApplySummary

    recovery = PartialApplyRecoveryView(
        _owner_member(),
        ops=[_op("bind_channel")],
        accepted=[],
        summary=ApplySummary(failed=["b: boom"]),
    )
    interaction = _interaction_with_guild()
    interaction.response.edit_message = AsyncMock()

    with patch(
        "services.setup_draft.clear",
        new_callable=AsyncMock,
    ) as clear_mock:
        await recovery._cancel.callback(interaction)

    clear_mock.assert_not_called()
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_recovery_view_finish_anyway_clears_draft_and_marks_complete():
    """Finish anyway drops the remaining draft and marks setup complete —
    the escape hatch from the partial-apply stickiness trap so a single
    un-appliable op can't keep the wizard stuck forever."""
    from views.setup.final_review import ApplySummary

    recovery = PartialApplyRecoveryView(
        _owner_member(),
        ops=[_op("bind_channel")],
        accepted=[],
        summary=ApplySummary(applied=["a"], failed=["b: boom"], skipped=["c"]),
    )
    interaction = _interaction_with_guild()
    interaction.response.edit_message = AsyncMock()

    with (
        patch(
            "services.setup_draft.clear",
            new_callable=AsyncMock,
        ) as clear_mock,
        patch(
            "services.setup_session.mark_complete",
            new_callable=AsyncMock,
        ) as complete_mock,
    ):
        await recovery._finish_anyway.callback(interaction)

    clear_mock.assert_awaited_once_with(1)
    complete_mock.assert_awaited_once_with(1)
    interaction.response.edit_message.assert_awaited_once()
    embed = interaction.response.edit_message.await_args.kwargs["embed"]
    assert "with skips" in (embed.title or "").lower()


@pytest.mark.asyncio
async def test_recovery_view_retry_rejects_concurrent_press():
    """Retry honours the same single-flight gate as the initial Apply."""
    from services.setup_operations import (
        _reset_apply_inflight_for_tests,
        acquire_setup_apply_lock,
    )
    from views.setup.final_review import ApplySummary

    _reset_apply_inflight_for_tests()
    recovery = PartialApplyRecoveryView(
        _owner_member(),
        ops=[_op("bind_channel")],
        accepted=[],
        summary=ApplySummary(failed=["b: boom"]),
    )
    interaction = _interaction_with_guild()

    async with acquire_setup_apply_lock(1):
        with (
            patch(
                "views.setup.final_review._apply_ops_in_order",
                new_callable=AsyncMock,
            ) as ops_path,
            patch(
                "core.runtime.interaction_helpers.safe_defer",
                new_callable=AsyncMock,
            ),
        ):
            await recovery._retry.callback(interaction)
        ops_path.assert_not_called()
        interaction.response.send_message.assert_awaited()


# ---------------------------------------------------------------------------
# Retry idempotency for binding_failed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_retry_after_binding_failed_does_not_duplicate_resource():
    """End-to-end pin of the Phase 0 safety guarantee.

    Scenario:

    * Final Review apply runs a ``create_channel`` op whose
      provisioning returns ``outcome="binding_failed"``.
    * The op surfaces as ``failed``; the draft and session are NOT
      cleared / marked complete; the recovery view mounts.
    * The operator presses Retry.  The retry must run the same op
      through ``_apply_ops_in_order`` exactly once — no duplicate
      pipeline call from the original Final Review flow leaks
      through.  Resource pipeline idempotency (create_with_reuse,
      bind_channel already-bound short-circuit) is the production
      mechanism that prevents duplicate Discord side effects; we
      pin the call-count here so a future refactor cannot retry
      twice per click.
    """
    from views.setup.final_review import ApplySummary

    op = _op("create_channel", binding_name="mod_channel", resource_name="mod-log")
    view = FinalReviewView(_owner_member(), ops=[op])
    interaction = _interaction_with_guild()

    ops_path_mock = AsyncMock()
    # First call (initial Apply) returns binding_failed; second call
    # (Retry) succeeds.  If the retry button accidentally called the
    # path more than once, the test's await count would jump.
    ops_path_mock.side_effect = [
        ApplySummary(failed=["create_channel: resource provisioning outcome='binding_failed'"]),
        ApplySummary(applied=["create_channel"]),
    ]

    with (
        patch(
            "views.setup.final_review._apply_ops_in_order",
            new=ops_path_mock,
        ),
        patch(
            "services.setup_draft.clear",
            new_callable=AsyncMock,
        ) as clear_mock,
        patch(
            "services.setup_session.mark_complete",
            new_callable=AsyncMock,
        ) as complete_mock,
        patch(
            "core.runtime.interaction_helpers.safe_defer",
            new_callable=AsyncMock,
        ),
    ):
        # 1. Initial Apply: binding_failed → recovery view.
        await view._apply.callback(interaction)
        clear_mock.assert_not_called()
        complete_mock.assert_not_called()
        recovery_view = interaction.followup.edit_message.await_args.kwargs[
            "view"
        ]
        assert isinstance(recovery_view, PartialApplyRecoveryView)

        # 2. Retry from the recovery view: success → clear + complete.
        await recovery_view._retry.callback(interaction)
        # Exactly two calls total — one initial, one retry.  No
        # accidental double-dispatch on either path.
        assert ops_path_mock.await_count == 2
        clear_mock.assert_awaited_once_with(1)
        complete_mock.assert_awaited_once_with(1)


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


# ---------------------------------------------------------------------------
# Phase 7 — Final Review copy polish
# ---------------------------------------------------------------------------


def test_pre_apply_embed_uses_new_copy_and_button_label():
    """Phase 7 plan copy: 'Final review — nothing has changed yet.
    These setup operations are staged and ready to apply.'
    Primary button label is 'Apply staged setup'.
    """
    embed = build_final_review_embed([_op("bind_channel")])
    description = (embed.description or "").lower()
    assert "nothing has changed yet" in description
    assert "apply staged setup" in description


def test_full_success_embed_says_setup_complete():
    """Full-success branch: 'Setup complete. Applied: ...'"""
    from views.setup.final_review import ApplySummary

    summary = ApplySummary(applied=["a", "b"])
    embed = build_final_review_embed([_op("bind_channel")], summary=summary)
    title = (embed.title or "").lower()
    description = (embed.description or "").lower()
    assert "setup complete" in title or "setup complete" in description


def test_partial_success_embed_says_partially_applied():
    """Partial-failure copy from Phase 0 stays exactly as the plan
    documents in Phase 7."""
    from views.setup.final_review import ApplySummary

    summary = ApplySummary(applied=["a"], failed=["b: boom"])
    embed = build_final_review_embed([_op("bind_channel")], summary=summary)
    description = (embed.description or "").lower()
    assert "partially applied" in description
    assert "preserved" in description


def test_final_review_view_has_apply_edit_back_cancel_buttons():
    """Phase 7 button row: Apply staged setup / Edit setup / Back / Cancel."""
    view = FinalReviewView(_owner_member(), ops=[_op("bind_channel")])
    labels = {c.label for c in view.children if isinstance(c, discord.ui.Button)}
    assert "Apply staged setup" in labels
    assert "Edit setup" in labels
    assert "Back" in labels
    assert "Cancel" in labels


def test_apply_button_has_stable_custom_id():
    """The Apply button identity is anchored on a custom_id, not the
    label — Phase 7 renamed the label but the custom_id stays so
    test patches and persistent-view bindings (if any) keep working.
    """
    view = FinalReviewView(_owner_member(), ops=[_op("bind_channel")])
    apply_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and getattr(c, "custom_id", None) == "setup_final_review:apply"
    )
    assert apply_btn.label == "Apply staged setup"


@pytest.mark.asyncio
async def test_edit_button_closes_with_keep_editing_message():
    view = FinalReviewView(_owner_member(), ops=[_op("bind_channel")])
    interaction = _interaction_with_guild()

    edit_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and getattr(c, "custom_id", None) == "setup_final_review:edit"
    )
    await edit_btn.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    assert "edit" in (kwargs.get("content", "")).lower()


@pytest.mark.asyncio
async def test_back_button_closes_with_back_message():
    view = FinalReviewView(_owner_member(), ops=[_op("bind_channel")])
    interaction = _interaction_with_guild()

    back_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and getattr(c, "custom_id", None) == "setup_final_review:back"
    )
    await back_btn.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# Phase 8 — SetupCompleteView cleanup buttons
# ---------------------------------------------------------------------------


def test_setup_complete_view_has_delete_and_keep_buttons():
    from views.setup.final_review import ApplySummary, SetupCompleteView

    view = SetupCompleteView(_owner_member(), summary=ApplySummary(applied=["x"]))
    custom_ids = {
        c.custom_id
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    assert custom_ids == {"setup_complete:delete", "setup_complete:keep"}


@pytest.mark.asyncio
async def test_setup_complete_delete_calls_cleanup_service():
    """Pressing Delete ACKs the interaction (defer) before the
    destructive delete, invokes the guarded cleanup service, and
    confirms via an ephemeral followup on success.
    """
    from services.setup_channel import CleanupResult
    from views.setup.final_review import ApplySummary, SetupCompleteView

    view = SetupCompleteView(_owner_member(), summary=ApplySummary(applied=["x"]))
    interaction = _interaction_with_guild()
    fake_session = MagicMock()
    fake_session.delegated_admins = ()
    fake_session.guild = SimpleNamespace(owner_id=99)

    with (
        patch(
            "services.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=fake_session,
        ),
        patch(
            "services.setup_channel.cleanup_setup_channel_after_completion",
            new_callable=AsyncMock,
            return_value=CleanupResult(
                reason="ok",
                detail="Setup channel deleted.",
            ),
        ) as cleanup_mock,
        patch(
            "services.setup_session.set_setup_message_id",
            new_callable=AsyncMock,
        ),
        # _gate_apply uses resume_session + can_apply_setup; the
        # owner member always passes can_apply_setup against the
        # session.owner_id.
        patch(
            "views.setup.final_review.setup_access.can_apply_setup",
            return_value=True,
        ),
    ):
        delete_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_complete:delete"
        )
        await delete_btn.callback(interaction)

    cleanup_mock.assert_awaited_once()
    # The interaction is ACKed (deferred) before the destructive delete,
    # then confirmed via an ephemeral followup.  The setup channel (and
    # this view's message) is gone, so response.edit_message must NOT be
    # used — that path 404'd with "Unknown Webhook".
    interaction.response.defer.assert_awaited_once()
    interaction.response.edit_message.assert_not_awaited()
    interaction.followup.send.assert_awaited_once()
    confirm = interaction.followup.send.await_args.args[0]
    assert "deleted" in confirm.lower()


@pytest.mark.asyncio
async def test_setup_complete_delete_surfaces_guard_failure_as_ephemeral():
    """Guard failure (e.g. channel renamed) shows the reason
    ephemerally and leaves the buttons clickable for retry.
    """
    from services.setup_channel import CleanupResult
    from views.setup.final_review import ApplySummary, SetupCompleteView

    view = SetupCompleteView(_owner_member(), summary=ApplySummary(applied=["x"]))
    interaction = _interaction_with_guild()
    fake_session = MagicMock()
    fake_session.delegated_admins = ()
    fake_session.guild = SimpleNamespace(owner_id=99)

    with (
        patch(
            "services.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=fake_session,
        ),
        patch(
            "services.setup_channel.cleanup_setup_channel_after_completion",
            new_callable=AsyncMock,
            return_value=CleanupResult(
                reason="channel_renamed",
                detail="Channel renamed; refusing to delete.",
            ),
        ),
        patch(
            "views.setup.final_review.setup_access.can_apply_setup",
            return_value=True,
        ),
    ):
        delete_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_complete:delete"
        )
        await delete_btn.callback(interaction)

    # Guard failure is surfaced via an ephemeral followup (the
    # interaction was deferred first); buttons stay clickable for retry.
    interaction.followup.send.assert_awaited_once()
    msg = interaction.followup.send.await_args.args[0]
    assert "renamed" in msg.lower()


@pytest.mark.asyncio
async def test_setup_complete_delete_rejects_non_delegated_admin():
    from views.setup.final_review import ApplySummary, SetupCompleteView

    # Use _owner_member here just for the BaseView author check;
    # _gate_apply patches can_apply_setup to False below.
    view = SetupCompleteView(_owner_member(), summary=ApplySummary(applied=["x"]))
    interaction = _interaction_with_guild()

    with (
        patch(
            "services.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=MagicMock(),
        ),
        patch(
            "views.setup.final_review.setup_access.can_apply_setup",
            return_value=False,
        ),
        patch(
            "services.setup_channel.cleanup_setup_channel_after_completion",
            new_callable=AsyncMock,
        ) as cleanup_mock,
    ):
        delete_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_complete:delete"
        )
        await delete_btn.callback(interaction)

    cleanup_mock.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_setup_complete_keep_closes_view_without_deletion():
    from views.setup.final_review import ApplySummary, SetupCompleteView

    view = SetupCompleteView(_owner_member(), summary=ApplySummary(applied=["x"]))
    interaction = _interaction_with_guild()

    with (
        patch(
            "services.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=MagicMock(),
        ),
        patch(
            "views.setup.final_review.setup_access.can_apply_setup",
            return_value=True,
        ),
        patch(
            "services.setup_channel.cleanup_setup_channel_after_completion",
            new_callable=AsyncMock,
        ) as cleanup_mock,
    ):
        keep_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_complete:keep"
        )
        await keep_btn.callback(interaction)

    cleanup_mock.assert_not_awaited()
    interaction.response.edit_message.assert_awaited_once()
    interaction.followup.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_partial_recovery_view_does_not_offer_cleanup_buttons():
    """Phase 8: partial-recovery flows NEVER offer the Delete / Keep
    buttons.  Pinned because the plan explicitly forbids it.
    """
    from views.setup.final_review import ApplySummary

    summary = ApplySummary(applied=["one"], failed=["two: boom"])
    recovery = PartialApplyRecoveryView(
        _owner_member(),
        ops=[_op("bind_channel")],
        accepted=[],
        summary=summary,
    )
    custom_ids = {
        getattr(c, "custom_id", None) or c.label
        for c in recovery.children
        if isinstance(c, discord.ui.Button)
    }
    # Neither cleanup-button custom_id appears on the recovery view.
    assert "setup_complete:delete" not in custom_ids
    assert "setup_complete:keep" not in custom_ids
