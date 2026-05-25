"""Tests for the Phase 5 logging-presets section.

Pins:

* The section is registered with a stable slug, order, and
  ``recommended_ops_builder`` that maps to the Balanced preset.
* Each preset's ops are ONLY ``create_channel`` (no invented kinds).
* The Single preset shares one resource_name; Balanced uses two;
  Detailed uses one per binding.
* Preset buttons route through
  :func:`services.setup_draft.replace_recommended_for_section` so
  swapping presets cleanly removes the prior pick.
* Mutating buttons re-check ``can_apply_setup``.
* The picker delegates to the channels section's detailed picker on
  ``Custom``.
* ``infer_current_preset`` reads the typed draft rows correctly.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

import views.setup.sections  # noqa: F401 — populate REGISTRY
from services.setup_draft import (
    DraftOperationRow,
    ReplaceRecommendedResult,
)
from services.setup_operations import SetupOperation
from services.setup_sections import REGISTRY
from services.setup_session import SetupSession
from views.setup.sections.logging_presets import (
    _LOGGING_BINDINGS,
    SLUG,
    LoggingPresetsView,
    _preset_balanced_ops,
    _preset_detailed_ops,
    _preset_single_ops,
    _recommended_logging_ops,
    _supported_bindings,
    build_logging_presets_embed,
    infer_current_preset,
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


def _interaction(member, *, guild_id: int = 1) -> MagicMock:
    interaction = MagicMock()
    interaction.user = member
    interaction.guild_id = guild_id
    interaction.guild = MagicMock(id=guild_id)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    interaction.response.is_done = MagicMock(return_value=False)
    interaction.message = MagicMock(id=3000)
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Registry presence + section invariants
# ---------------------------------------------------------------------------


def test_logging_presets_section_registered():
    section = REGISTRY.get(SLUG)
    assert section is not None
    assert section.label == "Logging presets"


def test_logging_presets_section_order_after_channels():
    """Logging presets renders right after the channels section so
    operators see related steps grouped in the wizard."""
    section = REGISTRY.get(SLUG)
    channels = REGISTRY.get("channels")
    assert section is not None
    assert channels is not None
    assert section.order > channels.order


def test_logging_presets_op_kinds_only_resource_kinds():
    """The plan restricts the section to ``create_channel`` /
    ``bind_channel`` ops — anything else is a contract violation."""
    section = REGISTRY.get(SLUG)
    assert section is not None
    assert section.op_kinds <= frozenset({"create_channel", "bind_channel"})


def test_logging_presets_runs_in_standard_and_advanced_depths():
    """Quick depth intentionally omits this step — quick is a 3-step
    on-ramp, presets are an advanced choice."""
    section = REGISTRY.get(SLUG)
    assert section is not None
    assert section.depths == frozenset({"standard", "advanced"})


def test_logging_presets_has_recommended_builder():
    """Apply Recommended is wired to the Balanced preset."""
    section = REGISTRY.get(SLUG)
    assert section is not None
    assert section.recommended_ops_builder is not None


# ---------------------------------------------------------------------------
# Preset op builders
# ---------------------------------------------------------------------------


def test_single_preset_uses_one_resource_name():
    ops = _preset_single_ops(_LOGGING_BINDINGS)
    assert all(op.kind == "create_channel" for op in ops)
    assert len(ops) == len(_LOGGING_BINDINGS)
    # Every op points at the same resource name — that's how
    # ensure_channel reuse merges them onto one channel.
    names = {op.resource_name for op in ops}
    assert names == {"superbot-logs"}


def test_balanced_preset_splits_by_intent():
    ops = _preset_balanced_ops(_LOGGING_BINDINGS)
    assert all(op.kind == "create_channel" for op in ops)
    names = {op.resource_name for op in ops}
    assert names == {"bot-logs", "mod-logs"}
    # The mod_logs binding routes to mod-logs; everything else to
    # bot-logs.
    mod_ops = [op for op in ops if op.resource_name == "mod-logs"]
    assert len(mod_ops) == sum(
        1 for b in _LOGGING_BINDINGS if b.intent == "mod_logs"
    )


def test_detailed_preset_has_one_channel_per_binding():
    ops = _preset_detailed_ops(_LOGGING_BINDINGS)
    assert all(op.kind == "create_channel" for op in ops)
    assert len(ops) == len(_LOGGING_BINDINGS)
    # Every binding gets a distinct resource_name.
    names = {op.resource_name for op in ops}
    assert len(names) == len(_LOGGING_BINDINGS)


def test_all_preset_ops_set_resource_mode_create():
    """``create_channel`` ops must declare ``resource_mode="create"``
    so the provisioning pipeline dispatches to ensure_channel; the
    reuse-by-name behaviour falls out of that path.
    """
    for ops in (
        _preset_single_ops(_LOGGING_BINDINGS),
        _preset_balanced_ops(_LOGGING_BINDINGS),
        _preset_detailed_ops(_LOGGING_BINDINGS),
    ):
        for op in ops:
            assert op.resource_mode == "create"


def test_no_preset_invents_binding_names():
    """Every staged op binding_name must come from the documented
    catalogue — sections can't invent names that don't exist in the
    subsystem schema.
    """
    known_names = {b.binding_name for b in _LOGGING_BINDINGS}
    for ops in (
        _preset_single_ops(_LOGGING_BINDINGS),
        _preset_balanced_ops(_LOGGING_BINDINGS),
        _preset_detailed_ops(_LOGGING_BINDINGS),
    ):
        for op in ops:
            assert op.binding_name in known_names


@pytest.mark.asyncio
async def test_recommended_builder_returns_balanced_ops():
    """``recommended_ops_builder`` (Apply Recommended) is the Balanced
    preset.  Direct-equivalence with _preset_balanced_ops covers it.
    """
    ops = await _recommended_logging_ops(MagicMock())
    balanced = _preset_balanced_ops(_supported_bindings())
    # Compare op shapes; SetupOperation is a dataclass so direct ==
    # checks work.
    assert ops == balanced


@pytest.mark.asyncio
async def test_recommended_builder_accepts_phase_2_kwargs():
    """The Phase 2 ``call_recommended_ops_builder`` adapter passes
    ``session``, ``purpose``, ``depth``, ``section_slug`` to builders
    that accept them via **kwargs.  The logging-presets builder
    declares **kwargs so the adapter never errors when these arrive.
    """
    ops = await _recommended_logging_ops(
        MagicMock(),
        session=_session(),
        purpose="community",
        depth="standard",
        section_slug=SLUG,
    )
    assert isinstance(ops, list)


# ---------------------------------------------------------------------------
# Embed + infer_current_preset
# ---------------------------------------------------------------------------


def test_embed_lists_all_four_preset_choices():
    embed = build_logging_presets_embed(_LOGGING_BINDINGS)
    field_names = {(f.name or "").lower() for f in embed.fields}
    assert any("single" in n for n in field_names)
    assert any("balanced" in n for n in field_names)
    assert any("detailed" in n for n in field_names)
    assert any("custom" in n for n in field_names)


def test_embed_highlights_current_preset():
    embed = build_logging_presets_embed(_LOGGING_BINDINGS, current_preset="balanced")
    field_names = {(f.name or "") for f in embed.fields}
    assert any(name.startswith("✅") and "Balanced" in name for name in field_names)


def _row(
    *,
    section_slug: str | None = SLUG,
    staging_kind: str | None = "recommended",
    resource_name: str = "superbot-logs",
) -> DraftOperationRow:
    return DraftOperationRow(
        id=1,
        seq=1,
        section_slug=section_slug,
        staging_kind=staging_kind,
        group_id=None,
        parent_seq=None,
        label="x",
        op=SetupOperation(
            kind="create_channel",
            subsystem="logging",
            binding_name="audit_channel",
            resource_name=resource_name,
            resource_mode="create",
        ),
    )


def test_infer_current_preset_recognises_single():
    rows = [_row(resource_name="superbot-logs") for _ in range(3)]
    # Same resource_name across rows → "single".
    assert infer_current_preset(rows) == "single"


def test_infer_current_preset_recognises_balanced():
    rows = [
        _row(resource_name="bot-logs"),
        _row(resource_name="mod-logs"),
    ]
    assert infer_current_preset(rows) == "balanced"


def test_infer_current_preset_recognises_detailed():
    rows = [
        _row(resource_name=f"{n}-logs")
        for n in ("audit", "debug", "mod", "info")
    ]
    assert infer_current_preset(rows) == "detailed"


def test_infer_current_preset_returns_none_for_other_sections():
    rows = [_row(section_slug="channels")]  # owned by another section
    assert infer_current_preset(rows) is None


def test_infer_current_preset_ignores_non_recommended_rows():
    """Custom / manual / preset rows shouldn't drive the highlight."""
    rows = [_row(staging_kind="custom")]
    assert infer_current_preset(rows) is None


# ---------------------------------------------------------------------------
# LoggingPresetsView buttons
# ---------------------------------------------------------------------------


def test_view_has_preset_buttons_plus_custom_and_cancel():
    view = LoggingPresetsView(
        _owner_member(),
        hub=None,
        supported=_LOGGING_BINDINGS,
        current_preset=None,
    )
    custom_ids = {
        c.custom_id
        for c in view.children
        if isinstance(c, discord.ui.Button)
    }
    assert "setup_logging_preset:single" in custom_ids
    assert "setup_logging_preset:balanced" in custom_ids
    assert "setup_logging_preset:detailed" in custom_ids
    assert "setup_logging_preset:custom" in custom_ids
    assert "setup_logging_preset:cancel" in custom_ids


def test_view_highlights_current_preset_button():
    view = LoggingPresetsView(
        _owner_member(),
        hub=None,
        supported=_LOGGING_BINDINGS,
        current_preset="detailed",
    )
    detailed_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "setup_logging_preset:detailed"
    )
    assert detailed_btn.style is discord.ButtonStyle.success
    single_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button)
        and c.custom_id == "setup_logging_preset:single"
    )
    assert single_btn.style is discord.ButtonStyle.secondary


@pytest.mark.asyncio
async def test_preset_button_routes_through_replace_recommended():
    view = LoggingPresetsView(
        _owner_member(),
        hub=None,
        supported=_LOGGING_BINDINGS,
        current_preset=None,
    )
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.logging_presets.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.sections.logging_presets.setup_draft."
            "replace_recommended_for_section",
            new_callable=AsyncMock,
            return_value=ReplaceRecommendedResult(
                inserted_seqs=[1, 2],
                deleted_count=0,
                conflicts=[],
            ),
        ) as replace_mock,
        patch(
            "views.setup.sections.logging_presets.setup_session."
            "unmark_section_skipped",
            new_callable=AsyncMock,
        ),
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_logging_preset:balanced"
        )
        await btn.callback(interaction)

    replace_mock.assert_awaited_once()
    args = replace_mock.await_args.args
    # Positional args: guild_id, section_slug, ops.
    assert args[0] == 1
    assert args[1] == SLUG
    # All staged ops are create_channel.
    assert all(op.kind == "create_channel" for op in args[2])


@pytest.mark.asyncio
async def test_preset_button_rejects_non_delegated_admin():
    view = LoggingPresetsView(
        _random_member(),
        hub=None,
        supported=_LOGGING_BINDINGS,
        current_preset=None,
    )
    interaction = _interaction(_random_member())

    with (
        patch(
            "views.setup.sections.logging_presets.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(delegated=()),
        ),
        patch(
            "views.setup.sections.logging_presets.setup_draft."
            "replace_recommended_for_section",
            new_callable=AsyncMock,
        ) as replace_mock,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_logging_preset:balanced"
        )
        await btn.callback(interaction)

    replace_mock.assert_not_awaited()
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "owner" in msg or "delegate" in msg


@pytest.mark.asyncio
async def test_switching_presets_replaces_prior_rows():
    """Pressing Single then Balanced calls replace_recommended twice;
    the helper deletes the section's prior recommended rows on each
    call so the operator never accumulates duplicates.
    """
    view = LoggingPresetsView(
        _owner_member(),
        hub=None,
        supported=_LOGGING_BINDINGS,
        current_preset=None,
    )
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.logging_presets.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.sections.logging_presets.setup_draft."
            "replace_recommended_for_section",
            new_callable=AsyncMock,
            return_value=ReplaceRecommendedResult(
                inserted_seqs=[1],
                deleted_count=0,
                conflicts=[],
            ),
        ) as replace_mock,
        patch(
            "views.setup.sections.logging_presets.setup_session."
            "unmark_section_skipped",
            new_callable=AsyncMock,
        ),
    ):
        single_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_logging_preset:single"
        )
        await single_btn.callback(interaction)

        # After the press the view rebuilt — re-look-up by custom_id.
        balanced_btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_logging_preset:balanced"
        )
        await balanced_btn.callback(interaction)

    assert replace_mock.await_count == 2
    # Both calls target the same (guild, section).
    for call_args in replace_mock.await_args_list:
        assert call_args.args[0] == 1
        assert call_args.args[1] == SLUG


@pytest.mark.asyncio
async def test_preset_button_surfaces_db_failure():
    view = LoggingPresetsView(
        _owner_member(),
        hub=None,
        supported=_LOGGING_BINDINGS,
        current_preset=None,
    )
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.logging_presets.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.sections.logging_presets.setup_draft."
            "replace_recommended_for_section",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB down"),
        ),
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_logging_preset:detailed"
        )
        await btn.callback(interaction)

    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "could not" in msg


@pytest.mark.asyncio
async def test_preset_button_handles_empty_supported_bindings():
    """If the runtime has no logging bindings (degenerate case), the
    button surfaces a friendly message instead of staging an empty
    op list.
    """
    view = LoggingPresetsView(
        _owner_member(),
        hub=None,
        supported=(),
        current_preset=None,
    )
    interaction = _interaction(_owner_member())

    with (
        patch(
            "views.setup.sections.logging_presets.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=_session(),
        ),
        patch(
            "views.setup.sections.logging_presets.setup_draft."
            "replace_recommended_for_section",
            new_callable=AsyncMock,
        ) as replace_mock,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_logging_preset:single"
        )
        await btn.callback(interaction)

    replace_mock.assert_not_awaited()
    msg = interaction.response.send_message.await_args.args[0].lower()
    assert "no logging bindings" in msg


@pytest.mark.asyncio
async def test_custom_button_delegates_to_channels_customize():
    view = LoggingPresetsView(
        _owner_member(),
        hub=None,
        supported=_LOGGING_BINDINGS,
        current_preset=None,
    )
    interaction = _interaction(_owner_member())

    with patch(
        "views.setup.sections.channels._customize_run",
        new_callable=AsyncMock,
    ) as custom_mock:
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "setup_logging_preset:custom"
        )
        await btn.callback(interaction)

    custom_mock.assert_awaited_once()
