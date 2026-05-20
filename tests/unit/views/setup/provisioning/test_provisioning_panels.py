"""Track 3 PR 7 — provisioning UI adapter tests.

Pins:

* No direct DB writes from view methods.
* No direct ``guild.create_*`` calls.
* The Apply click on the preview panel transitions to a
  :class:`ConfirmPanelView` and only the confirm panel's ``run``
  invokes ``pipeline.provision``.
* Cancel marks the panel cancelled without invoking the pipeline.
* Disallowed previews (``preview.allowed=False``) disable the Apply
  button.
* The confirm panel surfaces pipeline failures as
  ``status="errored"`` without re-raising.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.resource_provisioning import ProvisioningPreview, ProvisioningRequest


def _request() -> ProvisioningRequest:
    return ProvisioningRequest(
        subsystem="logging",
        binding_name="mod_channel",
        mode="create",
        custom_name="bot-mod-log",
    )


def _allowed_preview() -> ProvisioningPreview:
    return ProvisioningPreview(
        allowed=True,
        action="create",
        target_name="bot-mod-log",
        warnings=(),
    )


def _blocked_preview() -> ProvisioningPreview:
    return ProvisioningPreview(
        allowed=False,
        action="blocked",
        target_name="",
        warnings=("missing perms",),
    )


def _author():
    """Return a stand-in author with the attributes ``BaseView`` reads."""
    member = MagicMock()
    member.id = 99
    return member


# ---------------------------------------------------------------------------
# build_preview_embed
# ---------------------------------------------------------------------------


def test_build_preview_embed_renders_allowed_preview():
    from views.setup.provisioning.preview_panel import build_preview_embed

    embed = build_preview_embed(_request(), _allowed_preview())
    rendered = embed.description or ""
    assert "logging.mod_channel" in (embed.title or "")
    assert "create" in rendered
    assert "bot-mod-log" in rendered
    # No warnings → no Warnings field.
    assert not any(f.name == "Warnings" for f in embed.fields)


def test_build_preview_embed_surfaces_warnings_when_blocked():
    from views.setup.provisioning.preview_panel import build_preview_embed

    embed = build_preview_embed(_request(), _blocked_preview())
    warnings_field = next(
        (f for f in embed.fields if f.name == "Warnings"),
        None,
    )
    assert warnings_field is not None
    assert "missing perms" in (warnings_field.value or "")


# ---------------------------------------------------------------------------
# PreviewPanelView — Apply / Cancel routing
# ---------------------------------------------------------------------------


def test_preview_panel_view_disables_apply_when_blocked():
    import discord

    from views.setup.provisioning.preview_panel import PreviewPanelView

    view = PreviewPanelView(
        _author(),
        request=_request(),
        preview=_blocked_preview(),
    )
    apply_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == "Apply"
    )
    assert apply_btn.disabled is True
    # Cancel is always enabled.
    cancel_btn = next(
        c
        for c in view.children
        if isinstance(c, discord.ui.Button) and c.label == "Cancel"
    )
    assert cancel_btn.disabled is False


@pytest.mark.asyncio
async def test_preview_panel_cancel_marks_cancelled_and_does_not_call_pipeline():
    from views.setup.provisioning.preview_panel import PreviewPanelView

    pipeline = MagicMock()
    pipeline.preview = AsyncMock()
    pipeline.provision = AsyncMock()

    view = PreviewPanelView(
        _author(),
        request=_request(),
        preview=_allowed_preview(),
        pipeline=pipeline,
    )

    interaction = MagicMock()
    interaction.response = MagicMock()
    interaction.response.edit_message = AsyncMock()

    # Invoke the Cancel button callback directly.
    await view._cancel.callback(interaction)

    assert view.cancelled is True
    pipeline.provision.assert_not_awaited()
    interaction.response.edit_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_preview_panel_apply_transitions_to_confirm_and_triggers_pipeline():
    from views.setup.provisioning import confirm_panel as confirm_mod
    from views.setup.provisioning.preview_panel import PreviewPanelView

    pipeline = MagicMock()
    pipeline.provision = AsyncMock(
        return_value=MagicMock(
            mutation_id="m1",
            outcome="success",
            created=True,
            resource_id=42,
            binding_written=True,
            audit_id=1,
        ),
    )

    view = PreviewPanelView(
        _author(),
        request=_request(),
        preview=_allowed_preview(),
        pipeline=pipeline,
    )

    guild = MagicMock()
    interaction = MagicMock()
    interaction.guild = guild
    interaction.user = _author()
    interaction.message = MagicMock(id=7)
    interaction.followup = MagicMock()
    interaction.followup.edit_message = AsyncMock()

    transition_mock = AsyncMock()
    with patch(
        "views.navigation.transition_to",
        transition_mock,
    ):
        await view._apply.callback(interaction)

    # The view marked itself confirmed and transitioned to a confirm
    # panel via the shared navigation helper.
    assert view.confirmed is True
    transition_mock.assert_awaited_once()
    transitioned_view = transition_mock.await_args.kwargs["view"]
    assert isinstance(transitioned_view, confirm_mod.ConfirmPanelView)
    # The confirm view ran the pipeline call exactly once.
    pipeline.provision.assert_awaited_once()
    call = pipeline.provision.await_args
    assert call.args[0] is guild
    assert call.args[1] is view.request
    assert call.kwargs["confirmed"] is True


@pytest.mark.asyncio
async def test_preview_panel_apply_refuses_without_guild():
    from views.setup.provisioning.preview_panel import PreviewPanelView

    pipeline = MagicMock()
    pipeline.provision = AsyncMock()

    view = PreviewPanelView(
        _author(),
        request=_request(),
        preview=_allowed_preview(),
        pipeline=pipeline,
    )

    interaction = MagicMock()
    interaction.guild = None
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()

    await view._apply.callback(interaction)

    interaction.response.send_message.assert_awaited_once()
    pipeline.provision.assert_not_awaited()


# ---------------------------------------------------------------------------
# ConfirmPanelView — outcome rendering + failure isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_confirm_panel_runs_pipeline_and_renders_success_embed():
    from views.setup.provisioning.confirm_panel import ConfirmPanelView

    pipeline = MagicMock()
    pipeline.provision = AsyncMock(
        return_value=MagicMock(
            mutation_id="m1",
            outcome="success",
            created=True,
            resource_id=42,
            binding_written=True,
            audit_id=1,
        ),
    )

    view = ConfirmPanelView(
        _author(),
        request=_request(),
        pipeline=pipeline,
    )

    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.user = _author()
    interaction.message = MagicMock(id=7)
    interaction.followup = MagicMock()
    interaction.followup.edit_message = AsyncMock()

    await view.run(interaction)

    pipeline.provision.assert_awaited_once()
    interaction.followup.edit_message.assert_awaited_once()
    embed = interaction.followup.edit_message.await_args.kwargs["embed"]
    # The success outcome appears in the title.
    assert "success" in (embed.title or "")
    # The result's mutation_id rendered into an embed field.
    rendered = "\n".join((f.value or "") for f in embed.fields)
    assert "m1" in rendered


@pytest.mark.asyncio
async def test_confirm_panel_surfaces_pipeline_exception_without_propagating():
    from views.setup.provisioning.confirm_panel import ConfirmPanelView

    pipeline = MagicMock()
    pipeline.provision = AsyncMock(side_effect=RuntimeError("db down"))

    view = ConfirmPanelView(
        _author(),
        request=_request(),
        pipeline=pipeline,
    )

    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.user = _author()
    interaction.message = MagicMock(id=7)
    interaction.followup = MagicMock()
    interaction.followup.edit_message = AsyncMock()

    # Must not raise.
    await view.run(interaction)

    pipeline.provision.assert_awaited_once()
    interaction.followup.edit_message.assert_awaited_once()
    embed = interaction.followup.edit_message.await_args.kwargs["embed"]
    assert "errored" in (embed.title or "")
    rendered = "\n".join(f.value or "" for f in embed.fields)
    assert "db down" in rendered


@pytest.mark.asyncio
async def test_confirm_panel_refuses_without_guild():
    from views.setup.provisioning.confirm_panel import ConfirmPanelView

    pipeline = MagicMock()
    pipeline.provision = AsyncMock()

    view = ConfirmPanelView(
        _author(),
        request=_request(),
        pipeline=pipeline,
    )

    interaction = MagicMock()
    interaction.guild = None
    interaction.user = _author()
    interaction.message = MagicMock(id=7)
    interaction.followup = MagicMock()
    interaction.followup.edit_message = AsyncMock()

    await view.run(interaction)

    pipeline.provision.assert_not_awaited()
    embed = interaction.followup.edit_message.await_args.kwargs["embed"]
    assert "errored" in (embed.title or "")


# ---------------------------------------------------------------------------
# Module invariants
# ---------------------------------------------------------------------------


def _module_text(module_name: str) -> str:
    import importlib

    mod = importlib.import_module(module_name)
    src = mod.__file__
    assert src is not None
    with open(src, encoding="utf-8") as fh:
        return fh.read()


@pytest.mark.parametrize(
    "module_name",
    [
        "views.setup.provisioning.preview_panel",
        "views.setup.provisioning.confirm_panel",
    ],
)
def test_panel_module_has_no_db_write_imports(module_name):
    text = _module_text(module_name)
    # The view layer must never reach into the DB directly. Allowed
    # path: through services (which call utils.db).
    forbidden = ("from utils.db import", "import utils.db")
    for needle in forbidden:
        assert needle not in text, (
            f"{module_name} must not import utils.db; route writes through "
            "services.resource_provisioning."
        )


@pytest.mark.parametrize(
    "module_name",
    [
        "views.setup.provisioning.preview_panel",
        "views.setup.provisioning.confirm_panel",
    ],
)
def test_panel_module_has_no_direct_discord_create_calls(module_name):
    text = _module_text(module_name)
    forbidden = (
        "guild.create_text_channel",
        "guild.create_voice_channel",
        "guild.create_role",
        "guild.create_category",
        "create_text_channel(",
        "create_role(",
        "create_category(",
    )
    for needle in forbidden:
        assert needle not in text, (
            f"{module_name} must not call {needle}; route through "
            "services.resource_provisioning.ResourceProvisioningPipeline."
        )
