"""Unit tests for the S7 resource-provisioning launcher.

Covers :class:`views.settings.provision_resource.ProvisionResourceView`
and its `_provision_create` path.

Pins:

* The view exposes both a **Use existing** and a **Create new**
  button for channel/role/category/thread kinds.
* `_provision_create` runs `pipeline.preview(...)` BEFORE
  `pipeline.provision(...)` and stops on a blocked preview without
  ever calling `provision`.
* `_provision_create` passes ``confirmed=True`` on the provision
  call so the pipeline does not raise
  ``ProvisioningConfirmationRequired``.
* `ResourceProvisioningError` and arbitrary exceptions surface as
  ephemeral errors.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from views.settings.provision_resource import (
    ProvisionResourceView,
    _provision_create,
)


def _interaction(*, guild_id: int = 1):
    interaction = MagicMock()
    interaction.guild = MagicMock(id=guild_id)
    interaction.guild.id = guild_id
    interaction.user = MagicMock(id=7)
    interaction.message = MagicMock(id=100)
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


def _preview(allowed: bool = True, action: str = "create_new", warnings: tuple = ()):
    p = MagicMock()
    p.allowed = allowed
    p.action = action
    p.target_name = "new-channel"
    p.warnings = warnings
    return p


def _provision_result(
    *,
    outcome: str = "success",
    created: bool = True,
    resource_id: int = 12345,
    binding_written: bool = True,
    kind: str = "channel",
):
    r = MagicMock()
    r.outcome = outcome
    r.created = created
    r.resource_id = resource_id
    r.binding_written = binding_written
    r.kind = kind
    return r


def test_view_renders_use_existing_and_create_new_for_channel():
    view = ProvisionResourceView("logging", "mod_channel", "channel")
    labels = {c.label for c in view.children if isinstance(c, discord.ui.Button)}
    assert labels == {"Use existing", "Create new"}


def test_view_renders_only_create_new_for_unknown_kind():
    """An unknown ResourceKind value still exposes the create path; the
    use-existing path is hidden because there's no binding-edit widget
    for that kind.
    """
    view = ProvisionResourceView("admin", "audit_anchor", "totally_unknown")
    labels = [c.label for c in view.children if isinstance(c, discord.ui.Button)]
    assert "Create new" in labels
    assert "Use existing" not in labels


@pytest.mark.asyncio
async def test_provision_create_runs_preview_then_provision():
    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.preview = AsyncMock(return_value=_preview(allowed=True))
    pipeline_instance.provision = AsyncMock(return_value=_provision_result())
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    with patch(
        "services.resource_provisioning.ResourceProvisioningPipeline",
        pipeline_class,
    ):
        await _provision_create(interaction, "logging", "mod_channel", None)

    pipeline_instance.preview.assert_awaited_once()
    pipeline_instance.provision.assert_awaited_once()
    # The provision call must include confirmed=True so the pipeline
    # accepts the create path.
    assert pipeline_instance.provision.await_args.kwargs.get("confirmed") is True
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "Created" in msg
    assert "<#12345>" in msg


@pytest.mark.asyncio
async def test_provision_create_rejects_dm_context():
    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.preview = AsyncMock()
    pipeline_instance.provision = AsyncMock()
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    interaction.guild = None

    with patch(
        "services.resource_provisioning.ResourceProvisioningPipeline",
        pipeline_class,
    ):
        await _provision_create(interaction, "logging", "mod_channel", None)

    pipeline_instance.preview.assert_not_called()
    pipeline_instance.provision.assert_not_called()
    interaction.response.send_message.assert_awaited_once()
    assert "guild" in interaction.response.send_message.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_provision_create_stops_on_blocked_preview():
    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.preview = AsyncMock(
        return_value=_preview(allowed=False, warnings=("bot lacks manage_channels",)),
    )
    pipeline_instance.provision = AsyncMock()
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    with patch(
        "services.resource_provisioning.ResourceProvisioningPipeline",
        pipeline_class,
    ):
        await _provision_create(interaction, "logging", "mod_channel", None)

    pipeline_instance.preview.assert_awaited_once()
    pipeline_instance.provision.assert_not_called()
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "blocked" in msg.lower()
    assert "manage_channels" in msg


@pytest.mark.asyncio
async def test_provision_create_surfaces_pipeline_error_ephemerally():
    from services.resource_provisioning import UndeclaredResourceError

    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.preview = AsyncMock(
        side_effect=UndeclaredResourceError("no such requirement"),
    )
    pipeline_instance.provision = AsyncMock()
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    with patch(
        "services.resource_provisioning.ResourceProvisioningPipeline",
        pipeline_class,
    ):
        await _provision_create(interaction, "logging", "mod_channel", None)

    pipeline_instance.provision.assert_not_called()
    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "UndeclaredResourceError" in msg


@pytest.mark.asyncio
async def test_provision_create_surfaces_unexpected_error():
    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.preview = AsyncMock(return_value=_preview(allowed=True))
    pipeline_instance.provision = AsyncMock(side_effect=RuntimeError("boom"))
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    with patch(
        "services.resource_provisioning.ResourceProvisioningPipeline",
        pipeline_class,
    ):
        await _provision_create(interaction, "logging", "mod_channel", None)

    interaction.response.send_message.assert_awaited_once()
    msg = interaction.response.send_message.await_args.args[0]
    assert "Unexpected error" in msg
    assert "RuntimeError" in msg


@pytest.mark.asyncio
async def test_provision_create_reports_reused_resource():
    pipeline_class = MagicMock()
    pipeline_instance = MagicMock()
    pipeline_instance.preview = AsyncMock(
        return_value=_preview(allowed=True, action="reuse_existing"),
    )
    pipeline_instance.provision = AsyncMock(
        return_value=_provision_result(created=False),
    )
    pipeline_class.return_value = pipeline_instance

    interaction = _interaction()
    with patch(
        "services.resource_provisioning.ResourceProvisioningPipeline",
        pipeline_class,
    ):
        await _provision_create(interaction, "logging", "mod_channel", None)

    msg = interaction.response.send_message.await_args.args[0]
    assert "Reused" in msg
