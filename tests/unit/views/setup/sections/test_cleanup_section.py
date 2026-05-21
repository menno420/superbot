"""Tests for the cleanup inheritance setup section.

Pins:

* Registration: slug, order, emoji, style.
* The LEVELS table maps each operator-facing level to the
  cleanup_policies column values the resolver expects.
* The embed describes the four levels and the scope chain.
* ``_stage_cleanup_policy`` drafts a ``set_cleanup_policy`` op with
  the right scope fields and canonical metadata.
* Each scope (guild / category / channel) produces a draft with
  the right ``target_kind`` and ``target_id``.
* Unknown level rejection.
* DM context rejection.
* Append failure surfacing.
* The section never calls ``services.setup_operations.apply_operations``.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.setup_sections import REGISTRY
from views.setup.sections import cleanup


def _interaction(guild_id: int = 1):
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild_id = guild_id
    interaction.guild = SimpleNamespace(id=guild_id)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_cleanup_section_registered_with_expected_slug():
    section = REGISTRY.get("cleanup")
    assert section is not None
    assert section.slug == "cleanup"
    assert section.order == 60
    assert section.emoji == "🧹"


# ---------------------------------------------------------------------------
# LEVELS table
# ---------------------------------------------------------------------------


def test_levels_table_covers_four_documented_levels():
    assert set(cleanup.LEVELS) == {"Off", "Light", "Standard", "Strict"}


def test_level_off_disables_everything():
    values = cleanup.level_metadata("Off")
    assert values == {
        "delete_invalid_commands": False,
        "delete_failed_commands": False,
        "delete_after_seconds": 0,
    }


def test_level_strict_deletes_invalid_and_failed_quickly():
    values = cleanup.level_metadata("Strict")
    assert values["delete_invalid_commands"] is True
    assert values["delete_failed_commands"] is True
    assert values["delete_after_seconds"] == 2


def test_level_standard_is_5s_invalid_and_failed():
    values = cleanup.level_metadata("Standard")
    assert values == {
        "delete_invalid_commands": True,
        "delete_failed_commands": True,
        "delete_after_seconds": 5,
    }


def test_level_light_deletes_invalid_only():
    values = cleanup.level_metadata("Light")
    assert values["delete_invalid_commands"] is True
    assert values["delete_failed_commands"] is False
    assert values["delete_after_seconds"] == 10


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def test_embed_describes_scope_chain():
    embed = cleanup.build_cleanup_embed()
    description = (embed.description or "").lower()
    assert "thread" in description
    assert "channel" in description
    assert "category" in description
    assert "guild" in description


def test_embed_lists_all_levels():
    embed = cleanup.build_cleanup_embed()
    levels_field = next((f for f in embed.fields if f.name == "Levels"), None)
    assert levels_field is not None
    for level in ("Off", "Light", "Standard", "Strict"):
        assert level in levels_field.value


# ---------------------------------------------------------------------------
# _stage_cleanup_policy
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stage_guild_default_drafts_set_cleanup_policy():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await cleanup._stage_cleanup_policy(
            interaction,
            scope_kind="guild",
            scope_id=None,
            scope_name="guild",
            level="Standard",
        )
    append_mock.assert_awaited_once()
    op = append_mock.await_args.args[0]
    assert op.kind == "set_cleanup_policy"
    assert op.subsystem == "cleanup"
    assert op.target_kind == "guild"
    assert op.target_id is None
    assert op.value == "Standard"


@pytest.mark.asyncio
async def test_stage_category_override_drafts_with_category_scope():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await cleanup._stage_cleanup_policy(
            interaction,
            scope_kind="category",
            scope_id=42,
            scope_name="Staff",
            level="Strict",
        )
    op = append_mock.await_args.args[0]
    assert op.target_kind == "category"
    assert op.target_id == 42
    assert op.target_name == "Staff"
    assert op.value == "Strict"


@pytest.mark.asyncio
async def test_stage_channel_override_drafts_with_channel_scope():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await cleanup._stage_cleanup_policy(
            interaction,
            scope_kind="channel",
            scope_id=99,
            scope_name="#general",
            level="Off",
        )
    op = append_mock.await_args.args[0]
    assert op.target_kind == "channel"
    assert op.target_id == 99
    assert op.target_name == "#general"
    assert op.value == "Off"


@pytest.mark.asyncio
async def test_stage_populates_canonical_metadata():
    """Cleanup ops carry the canonical metadata via SetupOperation.metadata
    (not the `metadata=` kwarg on append) so the service's metadata
    merge picks up the operator-supplied values.
    """
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await cleanup._stage_cleanup_policy(
            interaction,
            scope_kind="guild",
            scope_id=None,
            scope_name="guild",
            level="Strict",
        )
    op = append_mock.await_args.args[0]
    assert op.metadata is not None
    md = op.metadata
    assert md["source"] == "manual"
    assert md["confidence"] == "high"
    assert md["risk"] == "low"
    assert "Operator chose" in md["reason"]
    assert "Strict" in md["reason"]
    assert "rollback" in md["rollback_note"].lower() or "re-stage" in md["rollback_note"].lower()


@pytest.mark.asyncio
async def test_stage_rejects_unknown_level():
    interaction = _interaction()
    with patch(
        "services.setup_draft.append",
        new_callable=AsyncMock,
    ) as append_mock:
        await cleanup._stage_cleanup_policy(
            interaction,
            scope_kind="guild",
            scope_id=None,
            scope_name="guild",
            level="Garbage",
        )
    append_mock.assert_not_called()
    interaction.response.send_message.assert_awaited_once()
    args = interaction.response.send_message.await_args.args
    assert "level" in args[0].lower()


@pytest.mark.asyncio
async def test_stage_rejects_dm_context():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    with patch(
        "services.setup_draft.append",
        new_callable=AsyncMock,
    ) as append_mock:
        await cleanup._stage_cleanup_policy(
            interaction,
            scope_kind="guild",
            scope_id=None,
            scope_name="guild",
            level="Off",
        )
    append_mock.assert_not_called()


@pytest.mark.asyncio
async def test_stage_surfaces_append_failure():
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
        await cleanup._stage_cleanup_policy(
            interaction,
            scope_kind="guild",
            scope_id=None,
            scope_name="guild",
            level="Standard",
        )
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "stage" in msg.lower() or "could not" in msg.lower()
    mark_mock.assert_not_called()


@pytest.mark.asyncio
async def test_stage_does_not_call_apply_operations():
    interaction = _interaction()
    with (
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
        patch(
            "services.setup_operations.apply_operations",
            new_callable=AsyncMock,
        ) as apply_mock,
    ):
        await cleanup._stage_cleanup_policy(
            interaction,
            scope_kind="guild",
            scope_id=None,
            scope_name="guild",
            level="Standard",
        )
    apply_mock.assert_not_called()


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_rejects_dm_context():
    """PR 3 routes ``run`` through the section card, which rejects DMs
    with a 'server'/'guild' phrasing inside its ``show`` helper."""
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    await cleanup.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()
    args = interaction.response.send_message.await_args.args
    assert "server" in args[0].lower() or "guild" in args[0].lower()


@pytest.mark.asyncio
async def test_run_opens_section_card_in_guild():
    """``run`` now shows the shared section card; the detailed cleanup
    picker is reachable via the card's Customize button."""
    from views.setup.section_card import SectionCardView

    interaction = _interaction()

    with (
        patch(
            "views.setup.section_card.setup_session.resume_session",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "views.setup.section_card.setup_draft.list_ops",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "views.setup.section_card.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await cleanup.run(interaction, MagicMock())

    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert isinstance(kwargs["view"], SectionCardView)
    assert "Cleanup" in (kwargs["embed"].title or "")


# ---------------------------------------------------------------------------
# Profile batch picker
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_profile_select_stages_every_profile_op():
    """Picking a profile stages each of its ops via setup_draft.append
    with metadata.source = 'cleanup_profile:<slug>'."""
    from views.setup.sections.cleanup import _ProfileSelect

    select = _ProfileSelect()
    select._values = ["light"]
    interaction = _interaction()
    interaction.guild = MagicMock(id=1, name="Test")

    fake_ops = [
        SimpleNamespace(
            kind="set_cleanup_policy",
            subsystem="cleanup",
            target_kind="guild",
            target_id=1,
            target_name="Test",
            value="Light",
        ),
    ]

    with (
        patch(
            "services.cleanup_profiles.apply_profile",
            return_value=fake_ops,
        ),
        patch(
            "services.setup_draft.append",
            new_callable=AsyncMock,
            return_value=1,
        ) as append_mock,
        patch(
            "services.setup_draft.count",
            new_callable=AsyncMock,
            return_value=1,
        ),
        patch(
            "services.setup_session.mark_in_progress",
            new_callable=AsyncMock,
        ),
    ):
        await select.callback(interaction)

    append_mock.assert_awaited_once()
    metadata = append_mock.await_args.kwargs.get("metadata")
    assert metadata["source"] == "cleanup_profile:light"
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_profile_select_rejects_unknown_slug():
    from views.setup.sections.cleanup import _ProfileSelect

    select = _ProfileSelect()
    select._values = ["bogus"]
    interaction = _interaction()

    with patch(
        "services.cleanup_profiles.get_profile",
        return_value=None,
    ):
        await select.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "unknown" in msg.lower()


@pytest.mark.asyncio
async def test_profile_select_requires_guild_context():
    from views.setup.sections.cleanup import _ProfileSelect

    select = _ProfileSelect()
    select._values = ["light"]
    interaction = _interaction()
    interaction.guild = None
    interaction.guild_id = None

    await select.callback(interaction)

    interaction.response.send_message.assert_awaited_once()


def test_cleanup_section_view_includes_profile_select():
    """The section view exposes both the scope select AND the new
    profile-batch select to the operator."""
    from views.setup.sections.cleanup import (
        CleanupSectionView,
        _ProfileSelect,
        _ScopeSelect,
    )

    view = CleanupSectionView(SimpleNamespace(id=99))
    child_types = {type(c) for c in view.children}
    assert _ScopeSelect in child_types
    assert _ProfileSelect in child_types
