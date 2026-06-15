"""Tests for the roles (auto-role thresholds) setup section.

Pins:

* Registration: slug, order, emoji, style, depth, op_kinds, and that it
  declares **no** recommended builder (thresholds are server-specific).
* The embed explains time/XP tiers (static) and renders a Detected
  summary when current thresholds are supplied.
* ``_stage_threshold`` drafts a ``set_role_threshold`` op with the right
  sub-kind / target / value, canonical metadata, and
  ``section_slug="roles"`` provenance.
* The time/XP role selects open the matching threshold modal.
* The modals validate their numeric input and stage on success.
* DM-context rejection, append-failure surfacing, and that the section
  never calls ``apply_operations``.
* The detail view stays within rows 0–3.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services.setup_sections import REGISTRY
from views.setup.sections import roles


def _interaction(guild_id: int = 1):
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild_id = guild_id
    interaction.guild = SimpleNamespace(id=guild_id, name="Test")
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.send_modal = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_roles_section_registered_with_expected_metadata():
    section = REGISTRY.get("roles")
    assert section is not None
    assert section.slug == "roles"
    assert section.order == 55
    assert section.emoji == "🎖️"
    assert section.style == discord.ButtonStyle.secondary
    assert section.op_kinds == frozenset({"set_role_threshold"})
    assert "quick" not in section.depths
    # Server-specific — there is no safe auto-recommend.
    assert section.recommended_ops_builder is None


def test_roles_section_label_fits_button():
    section = REGISTRY.get("roles")
    assert section is not None
    assert 1 <= len(section.label) <= 80


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def test_static_embed_explains_both_tiers():
    embed = roles.build_roles_embed()
    blob = ((embed.description or "") + " ".join(f.value for f in embed.fields)).lower()
    assert "time tier" in blob
    assert "xp tier" in blob
    assert all(f.name != "Detected" for f in embed.fields)


def test_embed_detected_summary_when_supplied():
    embed = roles.build_roles_embed(current_summary="• @Veteran — after **7d**")
    detected = next((f for f in embed.fields if f.name == "Detected"), None)
    assert detected is not None
    assert "Veteran" in detected.value


def test_embed_detected_empty_summary_renders_placeholder():
    embed = roles.build_roles_embed(current_summary="")
    detected = next((f for f in embed.fields if f.name == "Detected"), None)
    assert detected is not None
    assert "no auto-role tiers" in detected.value.lower()


# ---------------------------------------------------------------------------
# _parse_positive_int
# ---------------------------------------------------------------------------


def test_parse_positive_int_bounds():
    assert roles._parse_positive_int("7", 3650) == 7
    assert roles._parse_positive_int("0", 3650) is None
    assert roles._parse_positive_int("-3", 3650) is None
    assert roles._parse_positive_int("99999", 3650) is None
    assert roles._parse_positive_int("nope", 3650) is None


# ---------------------------------------------------------------------------
# _stage_threshold
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stage_threshold_drafts_set_role_threshold():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
        patch("services.setup_draft.count", new_callable=AsyncMock, return_value=1),
        patch("services.setup_session.mark_in_progress", new_callable=AsyncMock),
    ):
        await roles._stage_threshold(
            interaction,
            kind="time",
            role_id=555,
            role_name="Veteran",
            value=7,
            label="role tier: @Veteran after 7d",
        )
    append_mock.assert_awaited_once()
    op = append_mock.await_args.args[0]
    assert op.kind == "set_role_threshold"
    assert op.subsystem == "roles"
    assert op.setting_name == "time"
    assert op.target_id == 555
    assert op.target_name == "Veteran"
    assert op.target_kind == "role"
    assert op.value == 7
    assert append_mock.await_args.kwargs.get("section_slug") == "roles"
    assert op.metadata["risk"] == "medium"
    assert "rollback_note" in op.metadata


@pytest.mark.asyncio
async def test_stage_threshold_uses_per_role_slot_discriminator():
    """Two roles' tiers must not collide on a single draft slot.

    The draft replace-on-conflict key is
    ``(op_kind, subsystem, setting_name, binding_name)`` and excludes
    ``target_id``; ``binding_name`` carries the role id so staging a time tier
    for role A then role B yields two distinct rows (regression: before this
    fix the second overwrote the first).
    """
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
        patch("services.setup_draft.count", new_callable=AsyncMock, return_value=2),
        patch("services.setup_session.mark_in_progress", new_callable=AsyncMock),
    ):
        await roles._stage_threshold(
            interaction,
            kind="time",
            role_id=111,
            role_name="A",
            value=7,
            label="a",
        )
        await roles._stage_threshold(
            interaction,
            kind="time",
            role_id=222,
            role_name="B",
            value=14,
            label="b",
        )
    op1 = append_mock.await_args_list[0].args[0]
    op2 = append_mock.await_args_list[1].args[0]
    assert op1.binding_name == "tier:111"
    assert op2.binding_name == "tier:222"
    assert op1.binding_name != op2.binding_name


@pytest.mark.asyncio
async def test_stage_threshold_rejects_dm_context():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    with patch("services.setup_draft.append", new_callable=AsyncMock) as append_mock:
        await roles._stage_threshold(
            interaction,
            kind="xp",
            role_id=1,
            role_name="X",
            value=5,
            label="x",
        )
    append_mock.assert_not_called()


@pytest.mark.asyncio
async def test_stage_threshold_surfaces_append_failure():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ) as mark_mock,
    ):
        await roles._stage_threshold(
            interaction,
            kind="time",
            role_id=1,
            role_name="X",
            value=5,
            label="x",
        )
    interaction.response.send_message.assert_awaited_once()
    mark_mock.assert_not_called()


@pytest.mark.asyncio
async def test_stage_threshold_does_not_apply():
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
        await roles._stage_threshold(
            interaction,
            kind="xp",
            role_id=1,
            role_name="X",
            value=5,
            label="x",
        )
    apply_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Role select -> modal
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_time_role_select_opens_time_modal():
    select = roles._TimeRoleSelect()
    select._values = [SimpleNamespace(id=555, name="Veteran")]
    interaction = _interaction()
    await select.callback(interaction)
    interaction.response.send_modal.assert_awaited_once()
    modal = interaction.response.send_modal.await_args.args[0]
    assert isinstance(modal, roles._TimeDaysModal)
    assert modal._role_id == 555
    assert modal._role_name == "Veteran"


@pytest.mark.asyncio
async def test_xp_role_select_opens_xp_modal():
    select = roles._XpRoleSelect()
    select._values = [SimpleNamespace(id=777, name="Pro")]
    interaction = _interaction()
    await select.callback(interaction)
    interaction.response.send_modal.assert_awaited_once()
    modal = interaction.response.send_modal.await_args.args[0]
    assert isinstance(modal, roles._XpLevelModal)
    assert modal._role_id == 777


# ---------------------------------------------------------------------------
# Modal on_submit
# ---------------------------------------------------------------------------


def _time_modal(text: str) -> roles._TimeDaysModal:
    modal = roles._TimeDaysModal(role_id=555, role_name="Veteran")
    modal.days = SimpleNamespace(value=text)  # type: ignore[assignment]
    return modal


def _xp_modal(text: str) -> roles._XpLevelModal:
    modal = roles._XpLevelModal(role_id=777, role_name="Pro")
    modal.level = SimpleNamespace(value=text)  # type: ignore[assignment]
    return modal


@pytest.mark.asyncio
async def test_time_modal_stages_on_valid_input():
    modal = _time_modal("7")
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
        patch("services.setup_draft.count", new_callable=AsyncMock, return_value=1),
        patch("services.setup_session.mark_in_progress", new_callable=AsyncMock),
    ):
        await modal.on_submit(interaction)
    op = append_mock.await_args.args[0]
    assert op.setting_name == "time"
    assert op.value == 7
    assert op.target_id == 555


@pytest.mark.asyncio
async def test_time_modal_rejects_bad_input():
    modal = _time_modal("nope")
    interaction = _interaction()
    with patch("services.setup_draft.append", new_callable=AsyncMock) as append_mock:
        await modal.on_submit(interaction)
    append_mock.assert_not_called()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_xp_modal_stages_on_valid_input():
    modal = _xp_modal("25")
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
        patch("services.setup_draft.count", new_callable=AsyncMock, return_value=1),
        patch("services.setup_session.mark_in_progress", new_callable=AsyncMock),
    ):
        await modal.on_submit(interaction)
    op = append_mock.await_args.args[0]
    assert op.setting_name == "xp"
    assert op.value == 25


# ---------------------------------------------------------------------------
# View shape + run()
# ---------------------------------------------------------------------------


def test_detail_view_has_two_role_selects_in_rows_0_1():
    view = roles.RolesSectionView(SimpleNamespace(id=99))
    child_types = {type(c) for c in view.children}
    assert roles._TimeRoleSelect in child_types
    assert roles._XpRoleSelect in child_types
    assert {c.row for c in view.children} <= {0, 1, 2, 3}


@pytest.mark.asyncio
async def test_run_rejects_dm_context():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.guild_id = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    await roles.run(interaction, MagicMock())
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
        await roles.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert isinstance(kwargs["view"], SectionCardView)
    assert "roles" in (kwargs["embed"].title or "").lower()
