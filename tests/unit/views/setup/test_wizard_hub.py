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


def test_build_hub_embed_surfaces_pending_ops_count():
    embed = build_hub_embed(None, pending_ops=4)
    description = (embed.description or "").lower()
    assert "pending operations" in description
    assert "4" in description


def test_build_hub_embed_omits_pending_count_when_none():
    embed = build_hub_embed(None)
    assert "pending operations" not in (embed.description or "").lower()


def test_build_hub_embed_shows_zero_pending_when_drafts_empty():
    """An explicit zero count still surfaces so the operator knows
    the wizard checked the draft store and found nothing pending.
    """
    embed = build_hub_embed(None, pending_ops=0)
    description = (embed.description or "").lower()
    assert "pending operations" in description
    assert "0" in description


def test_build_hub_embed_renders_section_status_badges_when_draft_ops_provided():
    """When ``draft_ops`` is passed, every Sections-field row gets a status
    glyph; sections with matching staged ops show their op count."""
    from services.setup_operations import SetupOperation

    ops = [
        SetupOperation(
            kind="set_cleanup_policy",
            subsystem="cleanup",
            metadata={"source": "setup_ux:recommended"},
        ),
    ]
    embed = build_hub_embed(None, pending_ops=1, draft_ops=ops)
    sections_field = next(
        f for f in embed.fields if (f.name or "").lower() == "sections"
    )
    value = sections_field.value or ""
    # Cleanup row shows the recommended badge and a pending-op hint.
    assert "Cleanup" in value
    assert "✅" in value
    assert "pending" in value


def test_build_hub_embed_without_draft_ops_falls_back_to_legacy_layout():
    """Existing callers that don't pass ``draft_ops`` see the original
    numbered-label list with no badges."""
    embed = build_hub_embed(None, pending_ops=0)
    sections_field = next(
        f for f in embed.fields if (f.name or "").lower() == "sections"
    )
    value = sections_field.value or ""
    # No badge glyphs from the new layout — Cleanup still appears, but
    # without ⬜/✅/🟡 prefixes.
    assert "Cleanup" in value
    assert "⬜" not in value
    assert "✅" not in value


def test_build_hub_embed_marks_skipped_sections_with_warning_badge():
    """A section slug in ``session.skipped_sections`` renders as SKIPPED
    even when no draft ops match its op_kinds."""
    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
        skipped_sections=frozenset({"cleanup"}),
    )
    embed = build_hub_embed(session, pending_ops=0, draft_ops=[])
    sections_field = next(
        f for f in embed.fields if (f.name or "").lower() == "sections"
    )
    value = sections_field.value or ""
    assert "⚠️" in value


# ---------------------------------------------------------------------------
# Phase 1 — _gate_apply (replaces _gate_owner) accepts delegated admins
# ---------------------------------------------------------------------------


def _delegated_member(member_id: int = 42, guild_owner_id: int = 99):
    """Member who is not the server owner but is in delegated_admins."""
    import discord

    m = MagicMock(spec=discord.Member)
    m.id = member_id
    m.guild = SimpleNamespace(owner_id=guild_owner_id)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _session_with_delegated(delegated_admins=(42,)):
    return SetupSession(
        guild_id=1,
        guild_name="Test",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=delegated_admins,
        skipped_sections=frozenset(),
    )


@pytest.mark.asyncio
async def test_hub_section_button_accepts_delegated_admin():
    """A delegated admin (non-owner) can press section buttons.

    Pre-Phase-1 the hub's _gate_owner allowed only the server owner,
    blocking delegated admins even though hub entry accepted them.
    The replacement _gate_apply defers to can_apply_setup.
    """
    delegated = _delegated_member(42)
    view = SetupHubView(delegated, session=_session_with_delegated((42,)))
    interaction = _interaction(delegated)
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
        ),
    ):
        await _section_button(view, "readiness").callback(interaction)
    # Section ran (readiness embed was sent) — not the access-denied embed.
    interaction.response.send_message.assert_awaited_once()
    sent_kwargs = interaction.response.send_message.await_args.kwargs
    assert sent_kwargs.get("embed") is fake_embed


@pytest.mark.asyncio
async def test_hub_section_button_rejects_non_delegated_admin():
    """A plain administrator (not delegated, not owner) is rejected."""
    other = _other_member()  # admin=True, id=42, owner=99, no delegation
    view = SetupHubView(other, session=_session_with_delegated(()))
    interaction = _interaction(other)
    await _section_button(view, "readiness").callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0].lower()
    # Reject message now mentions delegation as the recovery path.
    assert "delegate" in msg or "owner" in msg


@pytest.mark.asyncio
async def test_hub_section_button_rejects_member_without_delegation_when_session_changes():
    """Even if the hub was constructed with a session granting delegation,
    a later session without that delegation must NOT be silently used —
    the gate reads the live ``self.session``.  We verify by mutating
    the view's session in-place.
    """
    delegated = _delegated_member(42)
    session_granting = _session_with_delegated((42,))
    view = SetupHubView(delegated, session=session_granting)
    # Mutate the session to revoke delegation.
    view.session = _session_with_delegated(())
    interaction = _interaction(delegated)
    await _section_button(view, "readiness").callback(interaction)
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "delegate" in msg or "owner" in msg


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
    assert (
        registered <= rendered
    ), f"hub missing registered sections: {registered - rendered}"


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
    description = (embed.description or "").lower()
    # The embed used to refer to "recommendations" specifically; the
    # draft-first model means it now refers to staged work generically.
    assert "no staged" in description or "nothing" in description


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


# ---------------------------------------------------------------------------
# "Apply all recommended" hub button
# ---------------------------------------------------------------------------


def _find_button(view, custom_id: str):
    for child in view.children:
        if isinstance(child, discord.ui.Button) and child.custom_id == custom_id:
            return child
    return None


def test_apply_all_recommended_button_appears_when_section_has_builder():
    """If any depth-filtered section declares a recommended_ops_builder,
    the hub renders the "Apply all recommended" button on row 4."""
    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
        depth="standard",  # standard includes cleanup + channels
    )
    view = SetupHubView(_owner_member(), session=session)
    btn = _find_button(view, "setup_hub:apply_all_recommended")
    assert btn is not None
    assert btn.label == "Apply all recommended"
    assert btn.row == 4


def test_apply_all_recommended_button_absent_when_no_builders():
    """If no section in the depth has a recommended_ops_builder (e.g.
    a depth that only includes read-only sections), the button is
    omitted from the hub."""
    from unittest.mock import patch

    from services.setup_sections import REGISTRY

    # Patch the registry's for_depth to return only sections without
    # builders. We use server_scan (read-only, no builder).
    server_scan = REGISTRY.get("server_scan")
    if server_scan is None:
        pytest.skip("server_scan section not registered")

    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
        depth="standard",
    )
    with patch.object(REGISTRY, "for_depth", return_value=[server_scan]):
        view = SetupHubView(_owner_member(), session=session)
    btn = _find_button(view, "setup_hub:apply_all_recommended")
    assert btn is None


@pytest.mark.asyncio
async def test_apply_all_recommended_iterates_sections_and_stages_via_replace():
    """Phase 2: Clicking ``Apply all recommended`` calls every
    depth-filtered section's ``recommended_ops_builder`` via the
    Phase 2 adapter and stages each section's ops through the
    transactional ``replace_recommended_for_section`` helper.
    """
    from services.setup_draft import ReplaceRecommendedResult
    from services.setup_operations import SetupOperation
    from services.setup_sections import REGISTRY, SetupSection

    async def _build(_guild):
        return [
            SetupOperation(
                kind="set_cleanup_policy",
                subsystem="cleanup",
                target_kind="guild",
                target_id=1,
                value="Light",
            ),
        ]

    async def _section_run(_interaction, _hub):
        return None

    fake_section = SetupSection(
        slug="_fake_apply_all",
        label="Fake",
        style=discord.ButtonStyle.secondary,
        run=_section_run,
        order=999,
        depths=frozenset({"standard"}),
        recommended_ops_builder=_build,
    )

    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
        depth="standard",
    )

    with patch.object(REGISTRY, "for_depth", return_value=[fake_section]):
        view = SetupHubView(_owner_member(), session=session)
        button = _find_button(view, "setup_hub:apply_all_recommended")
        assert button is not None
        interaction = _interaction(_owner_member())
        interaction.guild = MagicMock(id=1)
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()
        with (
            patch.object(
                view,
                "_refresh_session",
                new_callable=AsyncMock,
            ),
            patch(
                "services.setup_draft.replace_recommended_for_section",
                new_callable=AsyncMock,
                return_value=ReplaceRecommendedResult(
                    inserted_seqs=[1],
                    deleted_count=0,
                    conflicts=[],
                ),
            ) as replace_mock,
        ):
            await button.callback(interaction)

    assert replace_mock.await_count == 1
    # Positional args: guild_id, section_slug, ops
    args = replace_mock.await_args.args
    assert args[0] == 1
    assert args[1] == "_fake_apply_all"
    assert len(args[2]) == 1
    interaction.followup.send.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_all_recommended_handles_empty_builder_output():
    """If every builder returns an empty list, the followup tells the
    operator nothing was staged.  Empty-output paths short-circuit
    before reaching the staging helper.
    """
    from services.setup_sections import REGISTRY, SetupSection

    async def _build(_guild):
        return []

    async def _section_run(_interaction, _hub):
        return None

    fake_section = SetupSection(
        slug="_fake_empty",
        label="Empty",
        style=discord.ButtonStyle.secondary,
        run=_section_run,
        order=999,
        depths=frozenset({"standard"}),
        recommended_ops_builder=_build,
    )

    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
        depth="standard",
    )

    with patch.object(REGISTRY, "for_depth", return_value=[fake_section]):
        view = SetupHubView(_owner_member(), session=session)
        button = _find_button(view, "setup_hub:apply_all_recommended")
        assert button is not None
        interaction = _interaction(_owner_member())
        interaction.guild = MagicMock(id=1)
        interaction.response.defer = AsyncMock()
        interaction.followup = MagicMock()
        interaction.followup.send = AsyncMock()
        with (
            patch.object(
                view,
                "_refresh_session",
                new_callable=AsyncMock,
            ),
            patch(
                "services.setup_draft.replace_recommended_for_section",
                new_callable=AsyncMock,
            ) as replace_mock,
        ):
            await button.callback(interaction)

    replace_mock.assert_not_awaited()
    interaction.followup.send.assert_awaited_once()
    msg = interaction.followup.send.await_args.args[0]
    assert "no" in msg.lower()


# ---------------------------------------------------------------------------
# Next-step hint
# ---------------------------------------------------------------------------


def test_hub_embed_next_step_hint_complete_session():
    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="complete",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
    )
    embed = build_hub_embed(session, pending_ops=0, draft_ops=[])
    hint = next((f for f in embed.fields if f.name == "Next step"), None)
    assert hint is not None
    assert "summary" in (hint.value or "").lower()


def test_hub_embed_next_step_hint_suggests_apply_all_when_nothing_staged():
    """No pending ops + at least one section has a recommended builder
    → hint mentions Apply all recommended."""
    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
    )
    embed = build_hub_embed(session, pending_ops=0, draft_ops=[])
    hint = next((f for f in embed.fields if f.name == "Next step"), None)
    assert hint is not None
    value = (hint.value or "").lower()
    # Cleanup + channels have recommended_ops_builder so the hint
    # should mention Apply all recommended.
    assert "apply all" in value


def test_hub_embed_next_step_hint_routes_to_final_review_when_ops_staged():
    """Pending ops + some sections not started → hint nudges toward
    either more sections or Final Review."""
    from services.setup_operations import SetupOperation

    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
    )
    ops = [
        SetupOperation(
            kind="set_cleanup_policy",
            subsystem="cleanup",
            metadata={"source": "setup_ux:recommended"},
        ),
    ]
    embed = build_hub_embed(session, pending_ops=1, draft_ops=ops)
    hint = next((f for f in embed.fields if f.name == "Next step"), None)
    assert hint is not None
    value = (hint.value or "").lower()
    assert "final review" in value
    assert "staged" in value


def test_hub_embed_omits_next_step_hint_without_draft_ops():
    """Legacy callers that don't pass draft_ops also don't get the
    next-step hint — there's not enough info to compute it."""
    embed = build_hub_embed(None, pending_ops=0)
    field_names = {f.name for f in embed.fields}
    assert "Next step" not in field_names


def test_hub_embed_surfaces_depth_when_set():
    """When the operator has picked a depth, the status line shows it
    alongside the existing status / step / readiness markers."""
    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
        depth="standard",
    )
    embed = build_hub_embed(session)
    description = (embed.description or "").lower()
    assert "depth: `standard`" in description


def test_hub_embed_omits_depth_marker_when_unset():
    session = SetupSession(
        guild_id=1,
        guild_name="x",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=(),
        depth=None,
    )
    embed = build_hub_embed(session)
    description = (embed.description or "").lower()
    assert "depth:" not in description
