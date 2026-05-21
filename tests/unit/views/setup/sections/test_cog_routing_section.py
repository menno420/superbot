"""Tests for the cog routing setup section.

Pins:

* Registration: slug, order=70, emoji=🧭, secondary button.
* Embed describes the scope chain and the default-true contract.
* ``_stage_cog_routing`` drafts a ``set_cog_routing`` op with the
  right scope/cog fields and canonical metadata; ``enabled`` flag
  flows into the metadata so the future dispatcher can read it.
* DM context rejection.
* Append failure surfacing.
* The section never calls ``services.setup_operations.apply_operations``.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.setup_sections import REGISTRY
from views.setup.sections import cog_routing


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


def test_cog_routing_section_registered_with_expected_slug():
    section = REGISTRY.get("cog_routing")
    assert section is not None
    assert section.slug == "cog_routing"
    assert section.order == 70
    assert section.emoji == "🧭"


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def test_embed_describes_scope_chain_and_default_true():
    embed = cog_routing.build_cog_routing_embed()
    description = (embed.description or "").lower()
    assert "channel" in description
    assert "category" in description
    assert "guild" in description
    assert "default" in description


def test_embed_lists_usage_steps():
    embed = cog_routing.build_cog_routing_embed()
    how = next((f for f in embed.fields if "How to use" in f.name), None)
    assert how is not None
    assert "scope" in how.value.lower()
    assert "cog" in how.value.lower()


# ---------------------------------------------------------------------------
# Operator-visible cog discovery
# ---------------------------------------------------------------------------


def test_operator_visible_cogs_returns_known_cog_names():
    visible = cog_routing._operator_visible_cogs()
    # Sanity: a handful of known visible cogs must be present.
    assert "moderation" in visible
    assert "logging" in visible
    assert "economy" in visible


def test_operator_visible_cogs_caps_at_25():
    visible = cog_routing._operator_visible_cogs()
    assert len(visible) <= 25


# ---------------------------------------------------------------------------
# _stage_cog_routing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_stage_drafts_set_cog_routing_op():
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
        await cog_routing._stage_cog_routing(
            interaction,
            scope_kind="guild",
            scope_id=None,
            scope_name="guild",
            cog_name="games",
            enabled=False,
        )
    append_mock.assert_awaited_once()
    op = append_mock.await_args.args[0]
    assert op.kind == "set_cog_routing"
    assert op.subsystem == "cog_routing"
    assert op.target_kind == "guild"
    assert op.target_id is None
    assert op.target_name == "guild"
    assert op.value == "games"
    # Metadata carries the enabled flag so the dispatcher can read it
    # without needing a parallel column.
    assert op.metadata is not None
    assert op.metadata["enabled"] == "false"


@pytest.mark.asyncio
async def test_stage_category_scope_includes_target_id():
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
        await cog_routing._stage_cog_routing(
            interaction,
            scope_kind="category",
            scope_id=42,
            scope_name="Staff",
            cog_name="moderation",
            enabled=True,
        )
    op = append_mock.await_args.args[0]
    assert op.target_kind == "category"
    assert op.target_id == 42
    assert op.target_name == "Staff"
    assert op.metadata["enabled"] == "true"


@pytest.mark.asyncio
async def test_stage_channel_scope_includes_channel_id():
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
        await cog_routing._stage_cog_routing(
            interaction,
            scope_kind="channel",
            scope_id=999,
            scope_name="general",
            cog_name="economy",
            enabled=False,
        )
    op = append_mock.await_args.args[0]
    assert op.target_kind == "channel"
    assert op.target_id == 999


@pytest.mark.asyncio
async def test_stage_populates_canonical_metadata():
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
        await cog_routing._stage_cog_routing(
            interaction,
            scope_kind="guild",
            scope_id=None,
            scope_name="guild",
            cog_name="games",
            enabled=False,
        )
    op = append_mock.await_args.args[0]
    md = op.metadata
    assert md["source"] == "manual"
    assert md["confidence"] == "high"
    assert md["risk"] == "medium"  # disabling cogs is more impactful than bindings
    assert "Operator" in md["reason"]
    assert "games" in md["reason"]
    assert "rollback" in md["rollback_note"].lower() or "re-stage" in md["rollback_note"].lower()


@pytest.mark.asyncio
async def test_stage_rejects_dm_context():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    with patch("services.setup_draft.append", new_callable=AsyncMock) as append_mock:
        await cog_routing._stage_cog_routing(
            interaction,
            scope_kind="guild",
            scope_id=None,
            scope_name="guild",
            cog_name="games",
            enabled=False,
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
        await cog_routing._stage_cog_routing(
            interaction,
            scope_kind="guild",
            scope_id=None,
            scope_name="guild",
            cog_name="games",
            enabled=True,
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
        await cog_routing._stage_cog_routing(
            interaction,
            scope_kind="guild",
            scope_id=None,
            scope_name="guild",
            cog_name="games",
            enabled=False,
        )
    apply_mock.assert_not_called()


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_rejects_dm_context():
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    await cog_routing.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()
    args = interaction.response.send_message.await_args.args
    assert "guild" in args[0].lower()


@pytest.mark.asyncio
async def test_run_sends_routing_panel_in_guild():
    interaction = _interaction()
    await cog_routing.run(interaction, MagicMock())
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.await_args.kwargs
    assert kwargs.get("ephemeral") is True
    assert isinstance(kwargs["view"], cog_routing.CogRoutingSectionView)
    assert "Cog routing" in kwargs["embed"].title


# ---------------------------------------------------------------------------
# Routing profile batch picker
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_routing_profile_select_stages_every_op():
    """Picking a routing profile stages each of its ops via setup_draft.append
    with metadata.source = 'cog_routing_profile:<slug>'."""
    from types import SimpleNamespace
    from unittest.mock import AsyncMock, MagicMock, patch

    from views.setup.sections.cog_routing import _RoutingProfileSelect

    select = _RoutingProfileSelect()
    select._values = ["games_in_game_channels"]
    interaction = MagicMock()
    interaction.user = SimpleNamespace(id=99)
    interaction.guild_id = 1
    interaction.guild = MagicMock(id=1, name="Test")
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()

    fake_ops = [
        SimpleNamespace(
            kind="set_cog_routing",
            subsystem="cog_routing",
            target_kind="guild",
            target_id=1,
            target_name="Test",
            value="games",
            metadata={"enabled": "false"},
        ),
    ]

    with (
        patch(
            "services.cog_routing_profiles.apply_profile",
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
    assert metadata["source"] == "cog_routing_profile:games_in_game_channels"
    interaction.response.send_message.assert_awaited_once()


def test_cog_routing_section_view_includes_profile_select():
    """The section view exposes both the scope select AND the new
    routing-profile batch select to the operator."""
    from types import SimpleNamespace

    from views.setup.sections.cog_routing import (
        CogRoutingSectionView,
        _RoutingProfileSelect,
        _ScopeSelect,
    )

    view = CogRoutingSectionView(SimpleNamespace(id=99))
    child_types = {type(c) for c in view.children}
    assert _ScopeSelect in child_types
    assert _RoutingProfileSelect in child_types
