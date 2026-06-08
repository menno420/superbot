"""Tests for the role-templates setup section (server-management PR13).

Pins:

* registration metadata (slug / order / emoji / style / depth / op_kinds; no
  recommended builder — creation is deliberate, never swept in);
* ``_compute_plan`` reads the guild's live roles and partitions correctly;
* ``_build_create_op`` produces a ``create_managed_role`` op with a per-role
  slot discriminator and the role spec in metadata;
* ``_stage_creations`` appends one op per *new* role, skips when nothing is new,
  rejects DM context, and **never applies**;
* selecting a template edits the message into the preview + adds a stage button.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from services import setup_role_templates as rt
from services.setup_sections import REGISTRY
from views.setup.sections import role_templates as section


def _guild(gid: int = 1, *, roles=None, manage_roles: bool = True):
    return SimpleNamespace(
        id=gid,
        roles=roles or [],
        me=SimpleNamespace(
            guild_permissions=SimpleNamespace(manage_roles=manage_roles),
        ),
    )


def _interaction(guild=None):
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = guild if guild is not None else _guild()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_section_registered_with_expected_metadata():
    s = REGISTRY.get("role_templates")
    assert s is not None
    assert s.slug == "role_templates"
    assert s.order == 56
    assert s.emoji == "🧩"
    assert s.style == discord.ButtonStyle.secondary
    assert s.op_kinds == frozenset({"create_managed_role"})
    assert "quick" not in s.depths
    # Creating roles is deliberate — never part of "apply all recommended".
    assert s.recommended_ops_builder is None
    assert 1 <= len(s.label) <= 80


# ---------------------------------------------------------------------------
# Planning + op building
# ---------------------------------------------------------------------------


def test_compute_plan_marks_existing_roles():
    template = rt.get_template("community-hierarchy")
    guild = _guild(roles=[SimpleNamespace(name="Owner", id=10)])
    plan = section._compute_plan(guild, template)
    existing_names = {p.suggestion.name for p in plan.existing}
    assert "Owner" in existing_names
    assert plan.create_count == template.role_count - 1


def test_build_create_op_shape():
    s = rt.RoleSuggestion("Owner", "Founder", "#E91E63", hoist=True, time_days=30)
    template = rt.get_template("community-hierarchy")
    op = section._build_create_op(s, template=template)
    assert op.kind == "create_managed_role"
    assert op.subsystem == "roles"
    assert op.resource_name == "Owner"
    # Per-role slot discriminator so multiple roles don't collide in the draft.
    assert op.binding_name == "role:owner"
    spec = op.metadata["role_template"]
    assert spec["color"] == "#E91E63"
    assert spec["hoist"] is True
    assert spec["time_days"] == 30
    assert "permissions" not in spec


def test_build_create_op_distinct_slots_per_role():
    template = rt.get_template("community-hierarchy")
    ops = [section._build_create_op(s, template=template) for s in template.suggestions]
    slots = {op.binding_name for op in ops}
    assert len(slots) == len(ops), "every template role must get a distinct draft slot"


# ---------------------------------------------------------------------------
# Staging
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stage_creations_appends_one_op_per_new_role():
    template = rt.get_template("community-hierarchy")
    plan = rt.plan_template(template, existing_roles={})  # all new
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append", new_callable=AsyncMock, return_value=1
        ) as append_mock,
        patch("services.setup_draft.count", new_callable=AsyncMock, return_value=4),
        patch("services.setup_session.mark_in_progress", new_callable=AsyncMock),
    ):
        await section._stage_creations(interaction, template=template, plan=plan)
    assert append_mock.await_count == template.role_count
    op = append_mock.await_args_list[0].args[0]
    assert op.kind == "create_managed_role"
    assert append_mock.await_args_list[0].kwargs.get("section_slug") == "role_templates"


@pytest.mark.asyncio
async def test_stage_creations_skips_when_nothing_new():
    template = rt.get_template("community-hierarchy")
    existing = {s.name.lower(): i for i, s in enumerate(template.suggestions)}
    plan = rt.plan_template(template, existing_roles=existing)  # all exist
    interaction = _interaction()
    with patch("services.setup_draft.append", new_callable=AsyncMock) as append_mock:
        await section._stage_creations(interaction, template=template, plan=plan)
    append_mock.assert_not_called()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_stage_creations_rejects_dm_context():
    template = rt.get_template("community-hierarchy")
    plan = rt.plan_template(template, existing_roles={})
    interaction = _interaction(guild=None)
    interaction.guild = None
    with patch("services.setup_draft.append", new_callable=AsyncMock) as append_mock:
        await section._stage_creations(interaction, template=template, plan=plan)
    append_mock.assert_not_called()


@pytest.mark.asyncio
async def test_stage_creations_never_applies():
    template = rt.get_template("xp-progression")
    plan = rt.plan_template(template, existing_roles={})
    interaction = _interaction()
    with (
        patch("services.setup_draft.append", new_callable=AsyncMock, return_value=1),
        patch("services.setup_draft.count", new_callable=AsyncMock, return_value=5),
        patch("services.setup_session.mark_in_progress", new_callable=AsyncMock),
        patch(
            "services.setup_operations.apply_operations",
            new_callable=AsyncMock,
        ) as apply_mock,
    ):
        await section._stage_creations(interaction, template=template, plan=plan)
    apply_mock.assert_not_called()


@pytest.mark.asyncio
async def test_stage_creations_surfaces_append_failure():
    template = rt.get_template("support-server")
    plan = rt.plan_template(template, existing_roles={})
    interaction = _interaction()
    with patch(
        "services.setup_draft.append",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    ):
        await section._stage_creations(interaction, template=template, plan=plan)
    interaction.response.send_message.assert_awaited_once()
    assert "Could not stage" in interaction.response.send_message.await_args.args[0]


# ---------------------------------------------------------------------------
# Picker interaction
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_on_template_selected_renders_preview_and_adds_stage_button():
    view = section.RoleTemplatesSectionView(SimpleNamespace(id=99))
    interaction = _interaction(guild=_guild(roles=[]))
    await view.on_template_selected(interaction, "moderation-team")
    interaction.response.edit_message.assert_awaited_once()
    kwargs = interaction.response.edit_message.await_args.kwargs
    assert kwargs["view"] is view
    assert view._plan is not None
    assert view._stage_button is not None
    assert view._stage_button.disabled is False  # there are new roles to create


@pytest.mark.asyncio
async def test_on_template_selected_disables_stage_when_all_exist():
    template = rt.get_template("support-server")
    roles = [
        SimpleNamespace(name=s.name, id=i) for i, s in enumerate(template.suggestions)
    ]
    view = section.RoleTemplatesSectionView(SimpleNamespace(id=99))
    interaction = _interaction(guild=_guild(roles=roles))
    await view.on_template_selected(interaction, "support-server")
    assert view._stage_button is not None
    assert view._stage_button.disabled is True


def test_detail_view_stays_in_rows_0_to_3():
    view = section.RoleTemplatesSectionView(SimpleNamespace(id=99))
    view._sync_stage_button()
    assert {c.row for c in view.children} <= {0, 1, 2, 3}


# ---------------------------------------------------------------------------
# Embeds
# ---------------------------------------------------------------------------


def test_picker_embed_lists_every_template():
    embed = section.build_role_templates_embed()
    blob = " ".join(f.name for f in embed.fields)
    for t in rt.list_templates():
        assert t.display_name in blob


def test_preview_embed_marks_create_and_exists():
    template = rt.get_template("community-hierarchy")
    plan = rt.plan_template(template, existing_roles={"owner": 1})
    embed = section.build_template_preview_embed(template, plan)
    roles_field = next(f for f in embed.fields if f.name == "Roles")
    assert "✅" in roles_field.value  # Owner exists
    assert "➕" in roles_field.value  # others are new
