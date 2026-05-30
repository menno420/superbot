"""Unit tests for :class:`FlagManagerView` (Phase 6.5a).

Pins the canonical-pipeline contract:

* Enable/Disable buttons route through
  :func:`RolloutMutationPipeline.set_flag_state` — they never touch
  ``utils.db.feature_flag_state`` directly.
* The view module contains no direct DB-mutation call sites (the
  test scans the source as a regression guard).
* Mutation errors and unknown-flag rejections surface as ephemerals.
* The flag select lists every declared flag, sorted.
* After a successful mutation, the embed refreshes with the new
  resolution.

A grep-based source assertion holds the no-direct-DB-write rule in
place across future edits.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.diagnostic import flag_manager as fm

_FAKE_FLAG_NAMES = [
    "settings.manager_cog.enabled",
    "platform.bindings.primary",
    "platform.participation.enabled",
]


def _author(id_: int = 99) -> MagicMock:
    member = MagicMock(spec=discord.Member)
    member.id = id_
    member.display_name = "Op"
    return member


def _interaction(*, user_id: int = 99, guild_id: int | None = 42) -> MagicMock:
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = MagicMock()
    interaction.user.id = user_id
    interaction.guild_id = guild_id
    interaction.guild = MagicMock()
    interaction.guild.id = guild_id
    interaction.channel = MagicMock()
    interaction.client = MagicMock()
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.edit_message = AsyncMock()
    return interaction


# ---------------------------------------------------------------------------
# Module-level invariants
# ---------------------------------------------------------------------------


def test_flag_manager_module_does_not_import_db_layer_at_top_level():
    """The view must not pull the DB module at import time.

    A direct import line would make this view module depend on the DB
    package eagerly; the existing convention is function-local imports
    only.
    """
    src = Path(fm.__file__).read_text()
    # Find module-import section: everything before the first ``def``.
    head = src.split("\ndef ", 1)[0]
    assert "from utils.db" not in head
    assert "import utils.db" not in head
    assert "from utils.db.feature_flag_state" not in head


def test_flag_manager_does_not_call_db_mutations_directly():
    """The view must never invoke ``ff_db`` mutation functions.

    The pipeline is the only sanctioned write path; this assertion
    guards against a future edit that "just adds a quick delete".
    """
    src = Path(fm.__file__).read_text()
    for forbidden in (
        "upsert_global_with_audit",
        "upsert_guild_with_audit",
        "delete_guild_override",
        "delete_global_override",
    ):
        assert (
            forbidden not in src
        ), f"flag_manager.py contains forbidden DB mutation call {forbidden!r}"


# ---------------------------------------------------------------------------
# Overview + detail embeds
# ---------------------------------------------------------------------------


def test_overview_embed_describes_read_only_default():
    embed = fm.build_flag_manager_overview_embed()
    desc = (embed.description or "") + (embed.footer.text or "")
    assert "pipeline" in desc.lower() or "audit" in desc.lower()
    assert "guild" in desc.lower()


def test_detail_embed_renders_required_fields():
    details = {
        "name": "platform.example.flag",
        "default": "off",
        "effective": "on",
        "source": "guild_override",
        "owner": "platform",
        "description": "Example",
        "removal_target": "Phase 99 stable",
        "has_guild_override": True,
    }
    embed = fm.build_flag_detail_embed(details)
    field_names = [f.name for f in embed.fields]
    assert "Default" in field_names
    assert "Effective" in field_names
    assert "Source" in field_names
    assert "Owner" in field_names
    assert "Guild override" in field_names
    assert "Removal target" in field_names


def test_detail_embed_omits_removal_when_empty():
    details = {
        "name": "x.y",
        "default": "off",
        "effective": "off",
        "source": "default",
        "owner": "platform",
        "description": "",
        "removal_target": "",
        "has_guild_override": False,
    }
    embed = fm.build_flag_detail_embed(details)
    assert "Removal target" not in [f.name for f in embed.fields]


# ---------------------------------------------------------------------------
# View shape
# ---------------------------------------------------------------------------


def test_view_lists_every_declared_flag_in_select():
    with patch.object(fm, "_sorted_flag_names", return_value=list(_FAKE_FLAG_NAMES)):
        view = fm.FlagManagerView(_author(), guild_id=42)
        select = next(c for c in view.children if isinstance(c, discord.ui.Select))
        assert [o.value for o in select.options] == list(_FAKE_FLAG_NAMES)


def test_view_exposes_expected_button_set():
    view = fm.FlagManagerView(_author(), guild_id=42)
    custom_ids = {
        c.custom_id for c in view.children if isinstance(c, discord.ui.Button)
    }
    assert custom_ids == {
        "flag_manager:enable",
        "flag_manager:disable",
        "flag_manager:refresh",
        "flag_manager:back",
    }


def test_view_omits_reset_button_until_pipeline_supports_it():
    """The pipeline does not expose a guild-override delete path today,
    so the manager intentionally does not show a Reset button. Confirm
    the omission so a future re-introduction is deliberate.
    """
    view = fm.FlagManagerView(_author(), guild_id=42)
    button_labels = {c.label for c in view.children if isinstance(c, discord.ui.Button)}
    assert not any("reset" in (label or "").lower() for label in button_labels)


# ---------------------------------------------------------------------------
# Select handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_select_none_sentinel_sends_ephemeral():
    with patch.object(fm, "_sorted_flag_names", return_value=[]):
        view = fm.FlagManagerView(_author(), guild_id=42)
        interaction = _interaction()
        await view.handle_select(interaction, "__none__")
    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_select_routes_through_resolve_details():
    with patch.object(fm, "_sorted_flag_names", return_value=list(_FAKE_FLAG_NAMES)):
        view = fm.FlagManagerView(_author(), guild_id=42)
    interaction = _interaction()
    fake_details = {
        "name": "platform.bindings.primary",
        "default": "off",
        "effective": "on",
        "source": "guild_override",
        "owner": "platform",
        "description": "Bindings primary",
        "removal_target": "",
        "has_guild_override": True,
    }
    with patch.object(
        fm,
        "_resolve_flag_details",
        AsyncMock(return_value=fake_details),
    ) as fake_resolve:
        await view.handle_select(interaction, "platform.bindings.primary")
    fake_resolve.assert_awaited_once_with("platform.bindings.primary", 42)
    interaction.response.edit_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# Enable / Disable — pipeline routing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_enable_calls_pipeline_set_flag_state_with_guild_scope():
    with patch.object(fm, "_sorted_flag_names", return_value=list(_FAKE_FLAG_NAMES)):
        view = fm.FlagManagerView(_author(), guild_id=42)
        view.selected_flag = "platform.bindings.primary"
    interaction = _interaction()

    fake_pipeline = MagicMock()
    fake_pipeline.set_flag_state = AsyncMock()
    fake_details = {
        "name": "platform.bindings.primary",
        "default": "off",
        "effective": "on",
        "source": "guild_override",
        "owner": "platform",
        "description": "",
        "removal_target": "",
        "has_guild_override": True,
    }
    with (
        patch(
            "services.rollout_mutation.RolloutMutationPipeline",
            return_value=fake_pipeline,
        ),
        patch.object(
            fm,
            "_resolve_flag_details",
            AsyncMock(return_value=fake_details),
        ),
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.custom_id == "flag_manager:enable"
        )
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    fake_pipeline.set_flag_state.assert_awaited_once()
    kwargs = fake_pipeline.set_flag_state.call_args.kwargs
    assert kwargs["flag_name"] == "platform.bindings.primary"
    assert kwargs["scope"] == "guild"
    assert kwargs["state"] == "on"
    assert kwargs["guild_id"] == 42
    assert kwargs["actor_id"] == 99
    assert kwargs["actor_type"] == "platform_owner"
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_disable_calls_pipeline_with_state_off():
    with patch.object(fm, "_sorted_flag_names", return_value=list(_FAKE_FLAG_NAMES)):
        view = fm.FlagManagerView(_author(), guild_id=42)
        view.selected_flag = "platform.bindings.primary"
    interaction = _interaction()

    fake_pipeline = MagicMock()
    fake_pipeline.set_flag_state = AsyncMock()
    fake_details = {
        "name": "platform.bindings.primary",
        "default": "off",
        "effective": "off",
        "source": "guild_override",
        "owner": "platform",
        "description": "",
        "removal_target": "",
        "has_guild_override": True,
    }
    with (
        patch(
            "services.rollout_mutation.RolloutMutationPipeline",
            return_value=fake_pipeline,
        ),
        patch.object(
            fm,
            "_resolve_flag_details",
            AsyncMock(return_value=fake_details),
        ),
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "flag_manager:disable"
        )
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    fake_pipeline.set_flag_state.assert_awaited_once()
    kwargs = fake_pipeline.set_flag_state.call_args.kwargs
    assert kwargs["state"] == "off"
    assert kwargs["scope"] == "guild"


@pytest.mark.asyncio
async def test_enable_without_selection_sends_ephemeral():
    view = fm.FlagManagerView(_author(), guild_id=42)
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "flag_manager:enable"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]
    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_enable_without_guild_id_sends_ephemeral():
    view = fm.FlagManagerView(_author(), guild_id=None)
    view.selected_flag = "platform.bindings.primary"
    interaction = _interaction(guild_id=None)
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "flag_manager:enable"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_enable_pipeline_error_surfaces_ephemeral():
    with patch.object(fm, "_sorted_flag_names", return_value=list(_FAKE_FLAG_NAMES)):
        view = fm.FlagManagerView(_author(), guild_id=42)
        view.selected_flag = "platform.bindings.primary"
    interaction = _interaction()

    from services.rollout_mutation import UnknownFeatureFlagError

    fake_pipeline = MagicMock()
    fake_pipeline.set_flag_state = AsyncMock(
        side_effect=UnknownFeatureFlagError("unknown"),
    )
    with patch(
        "services.rollout_mutation.RolloutMutationPipeline",
        return_value=fake_pipeline,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.custom_id == "flag_manager:enable"
        )
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_message.assert_awaited_once()
    interaction.response.edit_message.assert_not_called()


@pytest.mark.asyncio
async def test_unexpected_exception_does_not_crash_view():
    with patch.object(fm, "_sorted_flag_names", return_value=list(_FAKE_FLAG_NAMES)):
        view = fm.FlagManagerView(_author(), guild_id=42)
        view.selected_flag = "platform.bindings.primary"
    interaction = _interaction()

    fake_pipeline = MagicMock()
    fake_pipeline.set_flag_state = AsyncMock(side_effect=RuntimeError("boom"))
    with patch(
        "services.rollout_mutation.RolloutMutationPipeline",
        return_value=fake_pipeline,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.custom_id == "flag_manager:enable"
        )
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# Refresh + Back
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_without_selection_rebuilds_overview():
    view = fm.FlagManagerView(_author(), guild_id=42)
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "flag_manager:refresh"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_after_selection_resolves_again():
    with patch.object(fm, "_sorted_flag_names", return_value=list(_FAKE_FLAG_NAMES)):
        view = fm.FlagManagerView(_author(), guild_id=42)
        view.selected_flag = "platform.bindings.primary"
    interaction = _interaction()

    fake_details = {
        "name": "platform.bindings.primary",
        "default": "off",
        "effective": "off",
        "source": "default",
        "owner": "platform",
        "description": "",
        "removal_target": "",
        "has_guild_override": False,
    }
    with patch.object(
        fm,
        "_resolve_flag_details",
        AsyncMock(return_value=fake_details),
    ) as fake_resolve:
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button)
            and c.custom_id == "flag_manager:refresh"
        )
        await btn.callback(interaction)  # type: ignore[union-attr,misc]
    fake_resolve.assert_awaited_once_with("platform.bindings.primary", 42)


@pytest.mark.asyncio
async def test_back_button_returns_to_platform_hub():
    view = fm.FlagManagerView(_author(), guild_id=42)
    interaction = _interaction()
    btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.custom_id == "flag_manager:back"
    )
    await btn.callback(interaction)  # type: ignore[union-attr,misc]
    interaction.response.edit_message.assert_awaited_once()
    from views.diagnostic.platform_panel import _PlatformHubView

    _args, kwargs = interaction.response.edit_message.call_args
    assert isinstance(kwargs["view"], _PlatformHubView)


# ---------------------------------------------------------------------------
# Cog wiring — !platform flag
# ---------------------------------------------------------------------------


def test_platform_flag_subcommand_exists():
    from cogs.diagnostic_cog import DiagnosticCog

    sub = DiagnosticCog.platform_grp.get_command("flag")
    assert sub is not None
    assert sub.name == "flag"


def test_platform_flags_read_only_command_still_exists():
    """`!platform flags` (plural) must remain — the new manager is a sibling,
    not a replacement.
    """
    from cogs.diagnostic_cog import DiagnosticCog

    sub = DiagnosticCog.platform_grp.get_command("flags")
    assert sub is not None


# ---------------------------------------------------------------------------
# PR2 — audience / db_editable surfaces + editor guard
# ---------------------------------------------------------------------------


def test_detail_embed_renders_audience_and_editable():
    details = {
        "name": "feature_flag.primary",
        "default": "off",
        "effective": "off",
        "source": "default",
        "owner": "platform",
        "description": "meta",
        "removal_target": "",
        "has_guild_override": False,
        "audience": "internal",
        "db_editable": False,
        "label": "Feature-flag runtime gate (env-only, internal)",
    }
    embed = fm.build_flag_detail_embed(details)
    field_names = [f.name for f in embed.fields]
    assert "Key" in field_names
    assert "Audience" in field_names
    assert "Editable" in field_names
    editable_field = next(f for f in embed.fields if f.name == "Editable")
    assert "env-only" in editable_field.value
    # Title uses the operator label, not the dotted key.
    assert "Feature-flag runtime" in (embed.title or "")


@pytest.mark.asyncio
async def test_enable_refuses_non_db_editable_flag():
    """A real env-only / internal gate (``feature_flag.primary``, declared
    ``db_editable=False``) cannot be toggled in the UI — the override would be
    a no-op, so the view refuses and never calls the pipeline.
    """
    view = fm.FlagManagerView(_author(), guild_id=42)
    view.selected_flag = "feature_flag.primary"
    interaction = _interaction()

    fake_pipeline = MagicMock()
    fake_pipeline.set_flag_state = AsyncMock()
    with patch(
        "services.rollout_mutation.RolloutMutationPipeline",
        return_value=fake_pipeline,
    ):
        btn = next(
            c
            for c in view.children
            if isinstance(c, discord.ui.Button) and c.custom_id == "flag_manager:enable"
        )
        await btn.callback(interaction)  # type: ignore[union-attr,misc]

    interaction.response.send_message.assert_awaited_once()
    fake_pipeline.set_flag_state.assert_not_called()
    interaction.response.edit_message.assert_not_called()
