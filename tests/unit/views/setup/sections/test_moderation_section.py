"""Tests for the moderation setup section.

Pins:

* Registration: slug, order, emoji, style, depth, recommended builder.
* The embed explains the surfaced knobs (static) and renders a Detected
  field when current values are supplied.
* ``_stage_setting`` drafts a ``set_setting`` op with subsystem
  "moderation", the right ``setting_name`` / value, canonical metadata,
  and ``section_slug="moderation"`` provenance.
* Each select stages the correct setting (dm_on_action, require_reason,
  warn_escalation_action, moderator_role).
* The recommended builder enables DM-on-action + require-a-reason.
* DM-context rejection, append-failure surfacing, and that the section
  never calls ``apply_operations`` (Final Review is the only apply gate).
* The detail view stays within rows 0–3 (row 4 is reserved by the
  wizard's step-detail Back button).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.setup_sections import REGISTRY
from views.setup.sections import moderation


def _interaction(guild_id: int = 1):
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild_id = guild_id
    interaction.guild = SimpleNamespace(id=guild_id, name="Test")
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_moderation_section_registered_with_expected_metadata():
    section = REGISTRY.get("moderation")
    assert section is not None
    assert section.slug == "moderation"
    assert section.order == 65
    assert section.emoji == "🛡️"
    assert section.style == discord.ButtonStyle.secondary
    # Not a "quick" section — moderation config is standard/advanced.
    assert "quick" not in section.depths
    assert {"standard", "advanced"} <= section.depths
    assert section.recommended_ops_builder is moderation._recommended_moderation_ops


def test_moderation_section_label_fits_button():
    section = REGISTRY.get("moderation")
    assert section is not None
    assert 1 <= len(section.label) <= 80


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def test_static_embed_lists_surfaced_knobs():
    embed = moderation.build_moderation_embed()
    blob = (embed.title or "") + " ".join(f.value for f in embed.fields)
    lowered = blob.lower()
    assert "dm on action" in lowered
    assert "require a reason" in lowered
    assert "warn escalation" in lowered
    assert "moderator role" in lowered
    # No Detected field when no current state supplied.
    assert all(f.name != "Detected" for f in embed.fields)


def test_embed_renders_detected_when_state_supplied():
    guild = MagicMock()
    guild.get_role.return_value = SimpleNamespace(mention="@Mods")
    embed = moderation.build_moderation_embed(
        dm_on_action=True,
        require_reason=False,
        warn_escalation_action="kick",
        moderator_role_id=555,
        guild=guild,
    )
    detected = next((f for f in embed.fields if f.name == "Detected"), None)
    assert detected is not None
    assert "on" in detected.value.lower()
    assert "kick" in detected.value.lower()
    assert "@Mods" in detected.value


# ---------------------------------------------------------------------------
# _stage_setting
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stage_setting_drafts_set_setting_with_provenance():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append", new_callable=AsyncMock, return_value=1
        ) as append_mock,
        patch("services.setup_draft.count", new_callable=AsyncMock, return_value=1),
        patch("services.setup_session.mark_in_progress", new_callable=AsyncMock),
    ):
        await moderation._stage_setting(
            interaction,
            setting_name="dm_on_action",
            value=True,
            label="moderation.dm_on_action = True",
            reason="unit test",
        )
    append_mock.assert_awaited_once()
    op = append_mock.await_args.args[0]
    assert op.kind == "set_setting"
    assert op.subsystem == "moderation"
    assert op.setting_name == "dm_on_action"
    assert op.value is True
    # Section provenance is passed so progress badges attribute correctly.
    assert append_mock.await_args.kwargs.get("section_slug") == "moderation"
    md = op.metadata
    assert md["source"] == "manual"
    assert md["confidence"] == "high"
    assert "rollback_note" in md


@pytest.mark.asyncio
async def test_stage_setting_rejects_dm_context():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    with patch("services.setup_draft.append", new_callable=AsyncMock) as append_mock:
        await moderation._stage_setting(
            interaction,
            setting_name="dm_on_action",
            value=True,
            label="x",
            reason="x",
        )
    append_mock.assert_not_called()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_stage_setting_surfaces_append_failure():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB explosion"),
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await moderation._stage_setting(
            interaction,
            setting_name="require_reason",
            value=True,
            label="x",
            reason="x",
        )
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "could not" in msg.lower() or "stage" in msg.lower()
    mark_mock.assert_not_called()


@pytest.mark.asyncio
async def test_stage_setting_does_not_apply():
    interaction = _interaction()
    with (
        patch("services.setup_draft.append", new_callable=AsyncMock, return_value=1),
        patch("services.setup_draft.count", new_callable=AsyncMock, return_value=1),
        patch("services.setup_session.mark_in_progress", new_callable=AsyncMock),
        patch(
            "services.setup_operations.apply_operations",
            new_callable=AsyncMock,
        ) as apply_mock,
    ):
        await moderation._stage_setting(
            interaction,
            setting_name="dm_on_action",
            value=False,
            label="x",
            reason="x",
        )
    apply_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Select callbacks
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dm_select_stages_bool():
    select = moderation._DmOnActionSelect()
    select._values = ["true"]
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append", new_callable=AsyncMock, return_value=1
        ) as append_mock,
        patch("services.setup_draft.count", new_callable=AsyncMock, return_value=1),
        patch("services.setup_session.mark_in_progress", new_callable=AsyncMock),
    ):
        await select.callback(interaction)
    op = append_mock.await_args.args[0]
    assert op.setting_name == "dm_on_action"
    assert op.value is True


@pytest.mark.asyncio
async def test_require_reason_select_stages_bool_false():
    select = moderation._RequireReasonSelect()
    select._values = ["false"]
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append", new_callable=AsyncMock, return_value=1
        ) as append_mock,
        patch("services.setup_draft.count", new_callable=AsyncMock, return_value=1),
        patch("services.setup_session.mark_in_progress", new_callable=AsyncMock),
    ):
        await select.callback(interaction)
    op = append_mock.await_args.args[0]
    assert op.setting_name == "require_reason"
    assert op.value is False


@pytest.mark.asyncio
async def test_warn_escalation_select_stages_action():
    select = moderation._WarnEscalationSelect()
    select._values = ["kick"]
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append", new_callable=AsyncMock, return_value=1
        ) as append_mock,
        patch("services.setup_draft.count", new_callable=AsyncMock, return_value=1),
        patch("services.setup_session.mark_in_progress", new_callable=AsyncMock),
    ):
        await select.callback(interaction)
    op = append_mock.await_args.args[0]
    assert op.setting_name == "warn_escalation_action"
    assert op.value == "kick"


@pytest.mark.asyncio
async def test_moderator_role_select_stages_role_id_string():
    select = moderation._ModeratorRoleSelect()
    select._values = [SimpleNamespace(id=555, name="Mods")]
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append", new_callable=AsyncMock, return_value=1
        ) as append_mock,
        patch("services.setup_draft.count", new_callable=AsyncMock, return_value=1),
        patch("services.setup_session.mark_in_progress", new_callable=AsyncMock),
    ):
        await select.callback(interaction)
    op = append_mock.await_args.args[0]
    assert op.setting_name == "moderator_role"
    assert op.value == "555"  # stored as numeric string
    assert op.metadata["risk"] == "medium"


# ---------------------------------------------------------------------------
# Recommended ops
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recommended_ops_enable_dm_and_require_reason():
    ops = await moderation._recommended_moderation_ops(MagicMock())
    by_name = {op.setting_name: op for op in ops}
    assert by_name.keys() == {"dm_on_action", "require_reason"}
    assert all(op.kind == "set_setting" for op in ops)
    assert all(op.subsystem == "moderation" for op in ops)
    assert by_name["dm_on_action"].value is True
    assert by_name["require_reason"].value is True
    assert all(op.metadata["source"] == "setup_ux:recommended" for op in ops)


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_detail_view_has_four_selects_in_rows_0_to_3():
    view = moderation.ModerationSectionView(SimpleNamespace(id=99))
    child_types = {type(c) for c in view.children}
    assert moderation._DmOnActionSelect in child_types
    assert moderation._RequireReasonSelect in child_types
    assert moderation._WarnEscalationSelect in child_types
    assert moderation._ModeratorRoleSelect in child_types
    # Row 4 is reserved by wizard_nav for the injected Back button.
    rows = {c.row for c in view.children}
    assert rows <= {0, 1, 2, 3}


def test_build_detail_view_returns_section_view():
    section = REGISTRY.get("moderation")
    view = moderation._build_detail_view(
        SimpleNamespace(id=99),
        section=section,
        guild=MagicMock(),
    )
    assert isinstance(view, moderation.ModerationSectionView)


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_rejects_dm_context():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.guild_id = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    await moderation.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()
    args = interaction.response.send_message.await_args.args
    assert "server" in args[0].lower() or "guild" in args[0].lower()


@pytest.mark.asyncio
async def test_run_opens_section_card_in_guild():
    from views.setup.section_card import SectionCardView

    interaction = _interaction()
    with (
        patch(
            "views.setup.section_card.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "views.setup.section_card.setup_draft.list_rows",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "views.setup.section_card.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await moderation.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert isinstance(kwargs["view"], SectionCardView)
    assert "Moderation" in (kwargs["embed"].title or "")
