"""Tests for the Phase 7 section-recovery embed + view."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.setup_sections import SetupSection
from services.setup_session import SetupSession
from views.setup.recovery import (
    RecoveryContext,
    SectionRecoveryView,
    build_recovery_embed,
    recovery_context_from_exception,
)


async def _noop(_interaction, _hub):  # pragma: no cover — not exercised
    return None


def _section(
    slug: str = "channels",
    *,
    op_kinds=frozenset({"bind_channel"}),
    description_if_skipped: str = "",
    builder=None,
) -> SetupSection:
    return SetupSection(
        slug=slug,
        label=slug.replace("_", " ").title(),
        style=discord.ButtonStyle.secondary,
        run=_noop,
        op_kinds=op_kinds,
        description_if_skipped=description_if_skipped,
        recommended_ops_builder=builder,
    )


def _context(
    *,
    section: SetupSection | None = None,
    origin: str = "wizard",
    step_index: int = 0,
    total_steps: int = 5,
    what_happened: str = "Test cause",
    why: str = "Test reason",
    recommended: str = "Test suggestion",
    if_skipped: str = "Test consequence",
) -> RecoveryContext:
    return RecoveryContext(
        section=section if section is not None else _section(),
        origin=origin,
        step_index=step_index,
        total_steps=total_steps,
        what_happened=what_happened,
        why=why,
        recommended=recommended,
        if_skipped=if_skipped,
    )


def _owner_member(user_id: int = 99) -> MagicMock:
    m = MagicMock(spec=discord.Member)
    m.id = user_id
    m.guild = SimpleNamespace(owner_id=user_id)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _random_member(user_id: int = 42) -> MagicMock:
    m = MagicMock(spec=discord.Member)
    m.id = user_id
    m.guild = SimpleNamespace(owner_id=99)
    m.guild_permissions = SimpleNamespace(administrator=False)
    return m


def _session(*, delegated=()):
    return SetupSession(
        guild_id=1,
        guild_name="Test",
        owner_id=99,
        setup_status="in_progress",
        setup_channel_id=None,
        setup_message_id=None,
        last_readiness_score=None,
        current_step=None,
        delegated_admins=delegated,
    )


def _interaction(member, *, guild_id: int = 1):
    interaction = MagicMock()
    interaction.user = member
    interaction.guild_id = guild_id
    interaction.guild = MagicMock(id=guild_id)
    interaction.message = MagicMock(id=5000)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# build_recovery_embed
# ---------------------------------------------------------------------------


def test_embed_has_all_four_structured_fields():
    embed = build_recovery_embed(_context())
    field_names = [(f.name or "") for f in embed.fields]
    assert "What happened" in field_names
    assert "Why" in field_names
    assert "Recommended" in field_names
    assert "If skipped" in field_names


def test_embed_renders_step_counter_when_wizard_origin():
    embed = build_recovery_embed(
        _context(origin="wizard", step_index=2, total_steps=7),
    )
    assert "Step 3/7" in (embed.title or "")


def test_embed_omits_step_counter_for_hub_origin():
    embed = build_recovery_embed(
        _context(origin="hub", step_index=-1, total_steps=0),
    )
    assert "Step" not in (embed.title or "")


def test_embed_falls_back_when_fields_empty():
    """Missing context fields render with a placeholder rather than
    leaving the embed visually broken.
    """
    embed = build_recovery_embed(
        _context(
            what_happened="",
            why="",
            recommended="",
            if_skipped="",
        ),
    )
    for f in embed.fields:
        assert (
            "no detail" in (f.value or "").lower()
            or "no suggestion" in (f.value or "").lower()
            or "no consequence" in (f.value or "").lower()
        )


def test_embed_uses_gold_accent():
    """Recovery embed is visually distinct from the normal step embed
    (blue) and the success embed (green).
    """
    embed = build_recovery_embed(_context())
    assert embed.color == discord.Color.gold()


# ---------------------------------------------------------------------------
# recovery_context_from_exception
# ---------------------------------------------------------------------------


def test_context_from_exception_includes_exception_type_in_why():
    ctx = recovery_context_from_exception(
        section=_section(),
        exc=ValueError("bad input"),
        origin="wizard",
        step_index=0,
        total_steps=3,
    )
    assert "ValueError" in ctx.why
    assert "bad input" in ctx.why


def test_context_from_exception_uses_permission_hint_for_forbidden():
    forbidden = discord.Forbidden(MagicMock(), "no permission")
    ctx = recovery_context_from_exception(
        section=_section(),
        exc=forbidden,
    )
    assert "permission" in ctx.why.lower()


def test_context_from_exception_uses_section_skip_text_when_present():
    section = _section(description_if_skipped="Skipping this is fine.")
    ctx = recovery_context_from_exception(
        section=section,
        exc=RuntimeError("x"),
    )
    assert "Skipping this is fine." in ctx.if_skipped


# ---------------------------------------------------------------------------
# SectionRecoveryView buttons
# ---------------------------------------------------------------------------


def test_view_has_five_buttons():
    view = SectionRecoveryView(_owner_member(), context=_context())
    custom_ids = {
        c.custom_id for c in view.children if isinstance(c, discord.ui.Button)
    }
    assert custom_ids == {
        "setup_recovery:continue",
        "setup_recovery:retry",
        "setup_recovery:skip",
        "setup_recovery:customize",
        "setup_recovery:cancel",
    }


def test_view_disables_customize_for_read_only_section():
    """Sections with no op_kinds AND no builder (e.g. server_scan,
    readiness, final_review) have no useful detail view — disable
    the Customize button rather than open something empty."""
    readonly = _section(op_kinds=frozenset(), builder=None)
    view = SectionRecoveryView(_owner_member(), context=_context(section=readonly))
    customize_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "setup_recovery:customize"
    )
    assert customize_btn.disabled is True


def test_view_enables_customize_for_section_with_builder():
    async def _builder(_guild):  # pragma: no cover — not exercised
        return []

    section = _section(builder=_builder)
    view = SectionRecoveryView(_owner_member(), context=_context(section=section))
    customize_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "setup_recovery:customize"
    )
    assert customize_btn.disabled is False


@pytest.mark.asyncio
async def test_continue_calls_resume_callback():
    resume = AsyncMock()
    view = SectionRecoveryView(
        _owner_member(),
        context=_context(),
        resume_callback=resume,
    )
    interaction = _interaction(_owner_member())

    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "setup_recovery:continue"
    )
    await btn.callback(interaction)

    resume.assert_awaited_once_with(interaction)


@pytest.mark.asyncio
async def test_continue_without_resume_callback_closes_view():
    view = SectionRecoveryView(_owner_member(), context=_context())
    interaction = _interaction(_owner_member())

    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "setup_recovery:continue"
    )
    await btn.callback(interaction)

    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_retry_re_invokes_section_run_callback():
    run_called = AsyncMock()

    async def _run(interaction, hub):  # noqa: ARG001
        await run_called(interaction, hub)

    section = SetupSection(
        slug="test_retry",
        label="Test",
        style=discord.ButtonStyle.secondary,
        run=_run,
        op_kinds=frozenset({"bind_channel"}),
    )
    view = SectionRecoveryView(_owner_member(), context=_context(section=section))
    interaction = _interaction(_owner_member())

    with patch(
        "views.setup.recovery.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=_session(),
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_recovery:retry"
        )
        await btn.callback(interaction)

    run_called.assert_awaited_once()


@pytest.mark.asyncio
async def test_retry_rejects_non_delegated_admin():
    view = SectionRecoveryView(_random_member(), context=_context())
    interaction = _interaction(_random_member())

    with patch(
        "views.setup.recovery.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=_session(delegated=()),
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_recovery:retry"
        )
        await btn.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "owner" in msg or "delegate" in msg


@pytest.mark.asyncio
async def test_skip_writes_mark_section_skipped_and_deletes_provenance_rows():
    section = _section("logging_presets", op_kinds=frozenset({"create_channel"}))
    resume = AsyncMock()
    view = SectionRecoveryView(
        _owner_member(),
        context=_context(section=section),
        resume_callback=resume,
    )
    interaction = _interaction(_owner_member())

    fake_rows = [
        MagicMock(id=11),
        MagicMock(id=22),
    ]
    with (
        patch(
            "views.setup.recovery.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.recovery.setup_session.mark_section_skipped",
            new_callable=AsyncMock,
        ) as mark_mock,
        patch(
            "views.setup.recovery.setup_draft.list_by_section",
            new_callable=AsyncMock,
            return_value=fake_rows,
        ),
        patch(
            "views.setup.recovery.setup_draft.delete_by_ids",
            new_callable=AsyncMock,
            return_value=2,
        ) as delete_mock,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.custom_id == "setup_recovery:skip"
        )
        await btn.callback(interaction)

    mark_mock.assert_awaited_once_with(1, "logging_presets")
    delete_mock.assert_awaited_once_with(1, [11, 22])
    resume.assert_awaited_once_with(interaction)


@pytest.mark.asyncio
async def test_skip_surfaces_db_failure():
    view = SectionRecoveryView(_owner_member(), context=_context())
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.recovery.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.recovery.setup_session.mark_section_skipped",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB down"),
        ),
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.custom_id == "setup_recovery:skip"
        )
        await btn.callback(interaction)

    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "could not" in msg


@pytest.mark.asyncio
async def test_cancel_closes_view_without_side_effects():
    view = SectionRecoveryView(_owner_member(), context=_context())
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.recovery.setup_session.mark_section_skipped",
            new_callable=AsyncMock,
        ) as skip_mock,
        patch(
            "views.setup.recovery.setup_draft.delete_by_ids",
            new_callable=AsyncMock,
        ) as delete_mock,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_recovery:cancel"
        )
        await btn.callback(interaction)

    skip_mock.assert_not_awaited()
    delete_mock.assert_not_awaited()
    interaction.response.edit_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# Stale-button cleanup — _close_in_place pins the post-stop() contract
# ---------------------------------------------------------------------------


def _btn(view: SectionRecoveryView, custom_id: str) -> discord.ui.Button:
    return next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == custom_id
    )


def _all_children_disabled(view: SectionRecoveryView) -> bool:
    return all(getattr(c, "disabled", False) for c in view.children)


@pytest.mark.asyncio
async def test_continue_disables_buttons_when_resume_callback_doesnt_touch_view():
    """Resume callback that repaints a separate host anchor must NOT
    leave the recovery view's buttons clickable after ``self.stop()``."""

    async def _resume_without_touching_recovery(_inter):
        return None  # repaint happens on a different message

    view = SectionRecoveryView(
        _owner_member(),
        context=_context(),
        resume_callback=_resume_without_touching_recovery,
    )
    interaction = _interaction(_owner_member())

    await _btn(view, "setup_recovery:continue").callback(interaction)

    assert _all_children_disabled(view)
    # Without an upstream response, safe_edit routes through
    # response.edit_message and updates the recovery message in place.
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_continue_close_routes_through_followup_when_already_responded():
    """If the resume callback already consumed the response slot,
    `_close_in_place` must route through `followup.edit_message`
    (the post-defer/post-response path) to still disable the buttons."""

    async def _resume_that_responds(inter):
        inter.response.is_done.return_value = True
        await inter.response.send_message("repaint happened", ephemeral=True)

    view = SectionRecoveryView(
        _owner_member(),
        context=_context(),
        resume_callback=_resume_that_responds,
    )
    interaction = _interaction(_owner_member())
    interaction.followup.edit_message = AsyncMock()

    await _btn(view, "setup_recovery:continue").callback(interaction)

    assert _all_children_disabled(view)
    # Once is_done() is True, response.edit_message must NOT be touched —
    # safe_edit goes through followup.edit_message instead.
    interaction.followup.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_retry_disables_buttons_after_section_run():
    """After ``section.run`` (which consumes the response slot via
    ``response.send_message``), the recovery view's buttons must still
    be disabled so they don't outlive ``self.stop()``."""

    async def _section_run(inter, _hub):
        inter.response.is_done.return_value = True
        await inter.response.send_message("section took it from here")

    section = SetupSection(
        slug="retry_test",
        label="Test",
        style=discord.ButtonStyle.secondary,
        run=_section_run,
        op_kinds=frozenset({"bind_channel"}),
    )
    view = SectionRecoveryView(_owner_member(), context=_context(section=section))
    interaction = _interaction(_owner_member())
    interaction.followup.edit_message = AsyncMock()

    with patch(
        "views.setup.recovery.setup_session.resume_session",
        new_callable=AsyncMock,
        return_value=_session(),
    ):
        await _btn(view, "setup_recovery:retry").callback(interaction)

    assert _all_children_disabled(view)
    interaction.followup.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_skip_with_resume_callback_disables_buttons_and_shows_skip_label():
    """The plan's B3 bug: skip with resume_callback used to call
    ``self.stop()`` without disabling the recovery view's buttons.
    The fix runs ``_close_in_place`` after the resume callback so the
    recovery message becomes a disabled "⏭ Skipped" shell."""

    captured: dict = {}

    async def _resume(_inter):
        return None

    async def _safe_edit_spy(_inter, **kw):
        captured.update(kw)
        return True

    section = _section("identity")
    view = SectionRecoveryView(
        _owner_member(),
        context=_context(section=section),
        resume_callback=_resume,
    )
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.recovery.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.recovery.setup_session.mark_section_skipped",
            new_callable=AsyncMock,
        ),
        patch(
            "views.setup.recovery.setup_draft.list_by_section",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "views.setup.recovery.safe_edit",
            AsyncMock(side_effect=_safe_edit_spy),
        ),
    ):
        await _btn(view, "setup_recovery:skip").callback(interaction)

    assert _all_children_disabled(view)
    assert "Skipped" in (captured.get("content") or "")
    assert captured.get("view") is view


@pytest.mark.asyncio
async def test_close_in_place_swallows_notfound_when_message_was_deleted():
    """If the upstream branch deleted/replaced the recovery message,
    ``safe_edit`` raises (and swallows) ``discord.NotFound`` — the
    callback must still complete and stop the view."""
    view = SectionRecoveryView(_owner_member(), context=_context())
    interaction = _interaction(_owner_member())

    not_found = discord.NotFound(MagicMock(status=404, reason="gone"), "msg gone")
    interaction.response.edit_message.side_effect = not_found

    # Should not raise even though safe_edit's underlying edit failed.
    await _btn(view, "setup_recovery:continue").callback(interaction)

    # Buttons are still disabled — local state cleanup happens before
    # the edit, so the Python-side view is consistent for stop().
    assert _all_children_disabled(view)
    assert view.is_finished()
