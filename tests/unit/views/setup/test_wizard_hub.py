"""Phase 9i / Track 8 PR 23 — wizard hub + final review tests.

Pins:

* The wizard hub gates every button on ``setup_access.is_server_owner``.
* The Readiness button posts the ephemeral readiness embed.
* The Smart Suggestions button collects a snapshot + invokes the
  advisor + opens the ``AIReviewPanelView``.
* The Final Review button opens the ``FinalReviewView`` with the
  current accepted set (empty in this view's lifecycle).
* ``FinalReviewView`` routes each accepted recommendation through
  :func:`services.setup_operations.apply_operations` (not directly
  through ``BindingMutationPipeline``) and isolates per-rec failures.
* ``FinalReviewView`` disables Apply when ``accepted`` is empty.

Hub buttons are no longer hardcoded; they are rendered from the
``services.setup_sections`` registry.  These tests look buttons up by
``custom_id`` (``setup_section:<slug>``) so the contract under test is
"section X is reachable from the hub," not "view exposes a `_X` field."
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.setup_plan import SetupRecommendation
from services.setup_session import SetupSession
from views.setup.final_review import (
    ApplySummary,
    FinalReviewView,
    build_final_review_embed,
)
from views.setup.hub import SetupHubView, build_hub_embed


def _section_button(view: SetupHubView, slug: str) -> discord.ui.Button:
    target_id = f"setup_section:{slug}"
    for item in view.children:
        if isinstance(item, discord.ui.Button) and item.custom_id == target_id:
            return item
    raise AssertionError(
        f"section button {slug!r} not found on hub view "
        f"(children: {[getattr(c, 'custom_id', None) for c in view.children]})",
    )


def _owner_member(guild_owner_id: int = 99):
    import discord

    m = MagicMock(spec=discord.Member)
    m.id = guild_owner_id
    m.guild = SimpleNamespace(owner_id=guild_owner_id)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _other_member():
    import discord

    m = MagicMock(spec=discord.Member)
    m.id = 42
    m.guild = SimpleNamespace(owner_id=99)
    m.guild_permissions = SimpleNamespace(administrator=True)
    return m


def _interaction(user, guild=None):
    interaction = MagicMock()
    interaction.user = user
    interaction.guild_id = 1
    interaction.guild = guild if guild is not None else MagicMock(id=1)
    interaction.message = MagicMock(id=100)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.edit_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Hub
# ---------------------------------------------------------------------------


def test_build_hub_embed_handles_no_session():
    embed = build_hub_embed(None)
    assert "wizard" in (embed.title or "").lower()


def test_build_hub_embed_surfaces_session_status():
    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=87,
        current_step="readiness",
        delegated_admins=(),
    )
    embed = build_hub_embed(session)
    description = (embed.description or "").lower()
    assert "in_progress" in description
    assert "readiness" in description
    assert "87" in description


@pytest.mark.asyncio
async def test_hub_readiness_button_owner_only():
    view = SetupHubView(_other_member())
    interaction = _interaction(_other_member())
    await _section_button(view, "readiness").callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    assert "owner" in interaction.response.send_message.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_hub_readiness_button_owner_posts_embed_and_marks_progress():
    view = SetupHubView(_owner_member())
    interaction = _interaction(_owner_member())
    fake_embed = MagicMock()
    with (
        patch(
            "cogs.diagnostic._platform_embeds.build_setup_readiness_embed",
            new_callable=AsyncMock,
            return_value=fake_embed,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await _section_button(view, "readiness").callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    mark_mock.assert_awaited_once_with(1, step="readiness")


@pytest.mark.asyncio
async def test_hub_suggestions_button_renders_deterministic_draft_inline():
    import services.guild_snapshot  # noqa: F401

    view = SetupHubView(_owner_member())
    interaction = _interaction(_owner_member())
    fake_snapshot = MagicMock()
    fake_draft = SimpleNamespace(
        recommendations=(
            SetupRecommendation(
                subsystem="logging",
                binding_name="mod_channel",
                target_kind="channel",
                target_id=100,
                target_name="mod-log",
                confidence="high",
                reason="x",
            ),
        ),
    )
    fake_advisor = MagicMock()
    fake_advisor.suggest = AsyncMock(return_value=fake_draft)
    with (
        patch(
            "services.guild_snapshot.collect",
            new_callable=AsyncMock,
            return_value=fake_snapshot,
        ),
        patch(
            "services.setup_plan.DeterministicAdvisor",
            return_value=fake_advisor,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await _section_button(view, "suggestions").callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    embed = interaction.response.send_message.await_args.kwargs["embed"]
    rendered = "\n".join(f.value or "" for f in embed.fields)
    assert "mod_channel" in rendered


@pytest.mark.asyncio
async def test_hub_final_review_button_opens_panel_even_when_empty():
    view = SetupHubView(_owner_member())
    interaction = _interaction(_owner_member())
    await _section_button(view, "final_review").callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    sent_view = interaction.response.send_message.await_args.kwargs["view"]
    assert isinstance(sent_view, FinalReviewView)


def test_hub_renders_one_button_per_registered_section():
    """Hub layout is derived from `services.setup_sections.REGISTRY`."""
    from services.setup_sections import REGISTRY

    view = SetupHubView(_owner_member())
    registered = {section.slug for section in REGISTRY.all()}
    rendered = {
        item.custom_id.split(":", 1)[1]
        for item in view.children
        if isinstance(item, discord.ui.Button)
        and (item.custom_id or "").startswith("setup_section:")
    }
    assert registered <= rendered, (
        f"hub missing registered sections: {registered - rendered}"
    )


@pytest.mark.asyncio
async def test_hub_isolates_section_run_exceptions():
    """A buggy section must not silently swallow the interaction.

    The hub wraps every section's `run` and surfaces a friendly error
    when the section hasn't already responded.
    """
    from services.setup_sections import REGISTRY, SetupSection

    async def _boom(_interaction, _hub):
        raise RuntimeError("section blew up")

    REGISTRY.register(
        SetupSection(
            slug="boom_test",
            label="Boom",
            style=discord.ButtonStyle.danger,
            run=_boom,
            order=999,
        ),
    )
    try:
        view = SetupHubView(_owner_member())
        interaction = _interaction(_owner_member())
        interaction.response.is_done = MagicMock(return_value=False)
        await _section_button(view, "boom_test").callback(interaction)
    finally:
        REGISTRY.unregister("boom_test")

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "boom_test" in msg and "failed" in msg


# ---------------------------------------------------------------------------
# Final review
# ---------------------------------------------------------------------------


def _rec(target_id: int = 100, target_kind: str = "channel"):
    return SetupRecommendation(
        subsystem="logging",
        binding_name="mod_channel",
        target_kind=target_kind,
        target_id=target_id,
        target_name=f"target-{target_id}",
        confidence="high",
        reason="x",
    )


def test_build_final_review_embed_empty_state():
    embed = build_final_review_embed([])
    assert "no recommendations" in (embed.description or "").lower()


def test_build_final_review_embed_pre_apply_lists_pending():
    embed = build_final_review_embed([_rec()])
    assert "1" in (embed.description or "")
    assert any(f.name == "Pending" for f in embed.fields)


def test_build_final_review_embed_post_apply_shows_summary():
    summary = ApplySummary(applied=["a"], failed=["b"], skipped=["c"])
    embed = build_final_review_embed([_rec()], summary=summary)
    desc = embed.description or ""
    assert "Applied **1**" in desc
    assert "failed **1**" in desc
    assert "skipped **1**" in desc


def test_final_review_view_disables_apply_when_empty():
    import discord

    view = FinalReviewView(_owner_member(), accepted=[])
    apply_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == "Apply"
    )
    assert apply_btn.disabled is True


@pytest.mark.asyncio
async def test_final_review_apply_calls_setup_operations_dispatcher():
    """FinalReviewView.Apply routes through setup_operations.apply_operations,
    not directly through BindingMutationPipeline."""
    from services.setup_operations import (
        SetupOperationBatchResult,
        SetupOperationResult,
    )

    fake_op = MagicMock()
    fake_result = SetupOperationResult(
        status="applied",
        operation=fake_op,
        label="logging.mod_channel → mod-log",
        mutation_id="m1",
    )
    fake_batch = SetupOperationBatchResult(results=[fake_result])

    view = FinalReviewView(_owner_member(), accepted=[_rec()])
    interaction = _interaction(_owner_member())
    with (
        patch(
            "services.setup_operations.apply_operations",
            new_callable=AsyncMock,
            return_value=fake_batch,
        ) as apply_mock,
        patch(
            "services.setup_session.mark_complete",
            new_callable=AsyncMock,
        ),
    ):
        await view._apply.callback(interaction)
    apply_mock.assert_awaited_once()
    assert view.summary is not None
    assert len(view.summary.applied) == 1
    assert view.summary.failed == []


@pytest.mark.asyncio
async def test_final_review_apply_does_not_call_binding_pipeline_directly():
    """After the dispatcher migration, BindingMutationPipeline must NOT be
    instantiated directly by FinalReviewView._apply."""
    from services.setup_operations import (
        SetupOperationBatchResult,
        SetupOperationResult,
    )

    fake_batch = SetupOperationBatchResult(
        results=[
            SetupOperationResult(
                status="applied",
                operation=MagicMock(),
                label="x",
                mutation_id="m1",
            )
        ]
    )

    view = FinalReviewView(_owner_member(), accepted=[_rec()])
    interaction = _interaction(_owner_member())
    binding_ctor = MagicMock()
    with (
        patch(
            "services.setup_operations.apply_operations",
            new_callable=AsyncMock,
            return_value=fake_batch,
        ),
        patch("services.binding_mutation.BindingMutationPipeline", binding_ctor),
        patch("services.setup_session.mark_complete", new_callable=AsyncMock),
    ):
        await view._apply.callback(interaction)
    # The view must not have constructed BindingMutationPipeline itself.
    binding_ctor.assert_not_called()


@pytest.mark.asyncio
async def test_final_review_apply_isolates_per_rec_failures():
    """One failed operation in the batch does not abort later ones; the
    summary receives correct applied/failed counts."""
    from services.setup_operations import (
        SetupOperationBatchResult,
        SetupOperationResult,
    )

    op = MagicMock()
    fake_batch = SetupOperationBatchResult(
        results=[
            SetupOperationResult(
                status="applied", operation=op, label="a", mutation_id="m1"
            ),
            SetupOperationResult(
                status="failed", operation=op, label="b", error="boom"
            ),
        ]
    )
    view = FinalReviewView(
        _owner_member(),
        accepted=[_rec(target_id=100), _rec(target_id=101)],
    )
    interaction = _interaction(_owner_member())
    with (
        patch(
            "services.setup_operations.apply_operations",
            new_callable=AsyncMock,
            return_value=fake_batch,
        ),
        patch("services.setup_session.mark_complete", new_callable=AsyncMock),
    ):
        await view._apply.callback(interaction)
    assert view.summary is not None
    assert len(view.summary.applied) == 1
    assert len(view.summary.failed) == 1
    assert "boom" in view.summary.failed[0]


@pytest.mark.asyncio
async def test_final_review_apply_skips_unsupported_target_kind():
    """Unsupported/not_yet_implemented operations land in summary.skipped,
    not in failed, and do not crash the apply."""
    from services.setup_operations import (
        SetupOperationBatchResult,
        SetupOperationResult,
    )

    op = MagicMock()
    fake_batch = SetupOperationBatchResult(
        results=[
            SetupOperationResult(
                status="not_yet_implemented",
                operation=op,
                label="logging.mod_channel → ?",
                error="operation kind 'bind_totally_made_up_kind' is not a known OperationKind",
            )
        ]
    )
    view = FinalReviewView(
        _owner_member(),
        accepted=[_rec(target_kind="totally_made_up_kind")],
    )
    interaction = _interaction(_owner_member())
    with (
        patch(
            "services.setup_operations.apply_operations",
            new_callable=AsyncMock,
            return_value=fake_batch,
        ),
        patch("services.setup_session.mark_complete", new_callable=AsyncMock),
    ):
        await view._apply.callback(interaction)
    assert view.summary is not None
    assert len(view.summary.skipped) == 1
    assert view.summary.applied == []
    assert view.summary.failed == []


@pytest.mark.asyncio
async def test_final_review_apply_partial_success_renders_applied_failed_skipped():
    """build_final_review_embed renders correct counts from a mixed-status batch."""
    from services.setup_operations import (
        SetupOperationBatchResult,
        SetupOperationResult,
    )

    op = MagicMock()
    fake_batch = SetupOperationBatchResult(
        results=[
            SetupOperationResult(
                status="applied", operation=op, label="a", mutation_id="x"
            ),
            SetupOperationResult(status="failed", operation=op, label="b", error="err"),
            SetupOperationResult(
                status="not_yet_implemented", operation=op, label="c", error="nyi"
            ),
        ]
    )
    view = FinalReviewView(
        _owner_member(),
        accepted=[_rec(), _rec(target_id=2), _rec(target_id=3)],
    )
    interaction = _interaction(_owner_member())
    with (
        patch(
            "services.setup_operations.apply_operations",
            new_callable=AsyncMock,
            return_value=fake_batch,
        ),
        patch("services.setup_session.mark_complete", new_callable=AsyncMock),
    ):
        await view._apply.callback(interaction)
    embed = build_final_review_embed(view.accepted, summary=view.summary)
    desc = embed.description or ""
    assert "Applied **1**" in desc
    assert "failed **1**" in desc
    assert "skipped **1**" in desc
