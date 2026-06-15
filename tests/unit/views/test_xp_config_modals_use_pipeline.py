"""Regression tests for the XP config modal write paths.

The **range / cooldown** modals write through
``services.settings_mutation.SettingsMutationPipeline`` (PR #5) so the
mutation lands with audit + per-key cache invalidation + event
emission; the modal still pokes ``invalidate_xp_config`` afterward
because the legacy composite ``XpConfig`` accessor is a separate
cache that the pipeline doesn't know about.

The **channel** modal moved to
``services.binding_mutation.BindingMutationPipeline`` in the P0-3
pointer-lane convergence (arc PR 2): the ``xp_announce_channel``
scalar SettingSpec was retired and the announce channel now lives in
the binding lane (``xp.announce_channel``).  An empty input clears the
binding; a numeric ID sets it.  The modal still pokes
``invalidate_xp_config`` so the on_message hot-path cache re-reads the
(binding-first) channel.

These tests pin the contract by:

* Asserting the modals do not import ``db.set_setting``.
* Patching the pipeline / helper and verifying each modal's
  ``on_submit`` drives it with the expected arguments for valid inputs.
* Verifying ``invalidate_xp_config(guild.id)`` is called after a
  successful write so the legacy hot-path cache stays fresh.
* Verifying validation failures stay ephemeral (no pipeline call,
  no cache poke) for non-numeric / non-positive inputs.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_MODALS_PATH = (
    Path(__file__).resolve().parents[3] / "disbot" / "views" / "xp" / "modals.py"
)


# ---------------------------------------------------------------------------
# AST-level: no db.set_setting references survive in the modals module
# ---------------------------------------------------------------------------


def test_modals_module_does_not_reference_db_set_setting():
    """``views/xp/modals.py`` has been removed from the no-direct-writes
    invariant allowlist; it must not call ``db.set_setting`` directly.
    """
    source = _MODALS_PATH.read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "set_setting":
            raise AssertionError(
                f"views/xp/modals.py still references set_setting at line "
                f"{node.lineno}",
            )


def test_modals_module_imports_pipeline_helper():
    """The module-level helper that wraps the pipeline must be present
    (function name is the stable contract every modal calls).
    """
    modals = importlib.import_module("views.xp.modals")
    assert hasattr(modals, "_set_xp_setting_via_pipeline")


# ---------------------------------------------------------------------------
# Helper-level: _set_xp_setting_via_pipeline calls the pipeline + invalidator
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_helper_calls_pipeline_and_invalidates_legacy_cache():
    from views.xp import modals as xp_modals

    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 99
    interaction.user = MagicMock()
    interaction.response.send_message = AsyncMock()

    pipeline_instance = MagicMock()
    pipeline_instance.set_value = AsyncMock(return_value=MagicMock())

    with (
        patch(
            "services.settings_mutation.SettingsMutationPipeline",
            return_value=pipeline_instance,
        ),
        patch.object(
            xp_modals,
            "invalidate_xp_config",
        ) as invalidator,
    ):
        ok = await xp_modals._set_xp_setting_via_pipeline(interaction, "xp_min", 17)

    assert ok is True
    pipeline_instance.set_value.assert_awaited_once_with(
        interaction.guild,
        "xp",
        "xp_min",
        17,
        interaction.user,
    )
    invalidator.assert_called_once_with(99)


@pytest.mark.asyncio
async def test_helper_returns_false_without_invalidating_on_dm():
    """No guild context → ephemeral error, no pipeline call, no
    cache invalidation.
    """
    from views.xp import modals as xp_modals

    interaction = MagicMock()
    interaction.guild = None
    interaction.response.send_message = AsyncMock()

    with (
        patch(
            "services.settings_mutation.SettingsMutationPipeline",
        ) as pipeline_cls,
        patch.object(
            xp_modals,
            "invalidate_xp_config",
        ) as invalidator,
    ):
        ok = await xp_modals._set_xp_setting_via_pipeline(interaction, "xp_min", 17)

    assert ok is False
    pipeline_cls.assert_not_called()
    invalidator.assert_not_called()
    interaction.response.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_helper_surfaces_validation_error_as_ephemeral():
    from services.settings_mutation import SettingsValidationError
    from views.xp import modals as xp_modals

    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 99
    interaction.user = MagicMock()
    interaction.response.send_message = AsyncMock()

    pipeline_instance = MagicMock()
    pipeline_instance.set_value = AsyncMock(
        side_effect=SettingsValidationError("expected positive int, got -3"),
    )

    with (
        patch(
            "services.settings_mutation.SettingsMutationPipeline",
            return_value=pipeline_instance,
        ),
        patch.object(
            xp_modals,
            "invalidate_xp_config",
        ) as invalidator,
    ):
        ok = await xp_modals._set_xp_setting_via_pipeline(interaction, "xp_min", -3)

    assert ok is False
    interaction.response.send_message.assert_awaited_once()
    sent = interaction.response.send_message.await_args
    assert sent.kwargs.get("ephemeral") is True
    invalidator.assert_not_called()


# ---------------------------------------------------------------------------
# Modal-level: each on_submit drives the helper with the right (name, value)
# ---------------------------------------------------------------------------


def _modal_interaction() -> MagicMock:
    interaction = MagicMock()
    interaction.guild = MagicMock()
    interaction.guild.id = 99
    interaction.user = MagicMock()
    interaction.response.send_message = AsyncMock()
    return interaction


@pytest.mark.asyncio
async def test_xp_range_modal_writes_min_and_max():
    from views.xp import modals as xp_modals

    fake_view = MagicMock()
    fake_view._rerender = AsyncMock()

    modal = xp_modals._XpRangeModal(fake_view)
    modal.xp_min = MagicMock()
    modal.xp_min.value = "12"
    modal.xp_max = MagicMock()
    modal.xp_max.value = "28"

    interaction = _modal_interaction()

    with (
        patch.object(
            xp_modals,
            "_set_xp_setting_via_pipeline",
            new=AsyncMock(return_value=True),
        ) as helper,
        patch.object(
            xp_modals,
            "safe_defer",
            new=AsyncMock(return_value=True),
        ),
    ):
        await modal.on_submit(interaction)

    calls = [call.args[1:] for call in helper.await_args_list]
    assert calls == [
        ("xp_min", 12),
        ("xp_max", 28),
    ]
    fake_view._rerender.assert_awaited_once()


@pytest.mark.asyncio
async def test_xp_range_modal_rejects_max_less_than_min():
    """Range coherence check stays in the modal; it short-circuits
    before the first pipeline call.
    """
    from views.xp import modals as xp_modals

    modal = xp_modals._XpRangeModal(MagicMock())
    modal.xp_min = MagicMock()
    modal.xp_min.value = "30"
    modal.xp_max = MagicMock()
    modal.xp_max.value = "10"

    interaction = _modal_interaction()

    with patch.object(
        xp_modals,
        "_set_xp_setting_via_pipeline",
        new=AsyncMock(return_value=True),
    ) as helper:
        await modal.on_submit(interaction)

    helper.assert_not_called()
    interaction.response.send_message.assert_awaited_once()
    sent = interaction.response.send_message.await_args
    assert sent.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_xp_cooldown_modal_writes_cooldown():
    from views.xp import modals as xp_modals

    fake_view = MagicMock()
    fake_view._rerender = AsyncMock()
    modal = xp_modals._XpCooldownModal(fake_view)
    modal.seconds = MagicMock()
    modal.seconds.value = "45"

    interaction = _modal_interaction()

    with (
        patch.object(
            xp_modals,
            "_set_xp_setting_via_pipeline",
            new=AsyncMock(return_value=True),
        ) as helper,
        patch.object(
            xp_modals,
            "safe_defer",
            new=AsyncMock(return_value=True),
        ),
    ):
        await modal.on_submit(interaction)

    helper.assert_awaited_once()
    assert helper.await_args.args[1:] == ("xp_cooldown", 45)
    fake_view._rerender.assert_awaited_once()


@pytest.mark.asyncio
async def test_xp_channel_modal_drives_binding_helper():
    """The channel modal passes its raw input to the binding helper
    (which validates + sets/clears the xp.announce_channel binding).
    """
    from views.xp import modals as xp_modals

    fake_view = MagicMock()
    fake_view._rerender = AsyncMock()
    modal = xp_modals._XpChannelModal(fake_view)
    modal.channel_id = MagicMock()
    modal.channel_id.value = "1234567890"

    interaction = _modal_interaction()

    with (
        patch.object(
            xp_modals,
            "_set_xp_announce_channel_via_binding",
            new=AsyncMock(return_value=True),
        ) as helper,
        patch.object(
            xp_modals,
            "safe_defer",
            new=AsyncMock(return_value=True),
        ),
    ):
        await modal.on_submit(interaction)

    helper.assert_awaited_once()
    assert helper.await_args.args[1] == "1234567890"
    fake_view._rerender.assert_awaited_once()


# ---------------------------------------------------------------------------
# Channel binding helper (_set_xp_announce_channel_via_binding) — P0-3
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_announce_helper_sets_binding_for_numeric_input():
    from core.runtime.subsystem_schema import BindingKind
    from views.xp import modals as xp_modals

    interaction = _modal_interaction()
    pipeline = MagicMock()
    pipeline.set_binding = AsyncMock(return_value=MagicMock())
    pipeline.clear_binding = AsyncMock(return_value=MagicMock())

    with (
        patch(
            "services.binding_mutation.BindingMutationPipeline",
            return_value=pipeline,
        ),
        patch.object(xp_modals, "invalidate_xp_config") as inv,
    ):
        ok = await xp_modals._set_xp_announce_channel_via_binding(
            interaction,
            " 1234567890 ",
        )

    assert ok is True
    pipeline.set_binding.assert_awaited_once_with(
        interaction.guild,
        "xp",
        "announce_channel",
        BindingKind.CHANNEL,
        1234567890,
        interaction.user,
    )
    pipeline.clear_binding.assert_not_called()
    inv.assert_called_once_with(99)


@pytest.mark.asyncio
async def test_announce_helper_clears_binding_on_blank_input():
    from core.runtime.subsystem_schema import BindingKind
    from views.xp import modals as xp_modals

    interaction = _modal_interaction()
    pipeline = MagicMock()
    pipeline.set_binding = AsyncMock(return_value=MagicMock())
    pipeline.clear_binding = AsyncMock(return_value=MagicMock())

    with (
        patch(
            "services.binding_mutation.BindingMutationPipeline",
            return_value=pipeline,
        ),
        patch.object(xp_modals, "invalidate_xp_config") as inv,
    ):
        ok = await xp_modals._set_xp_announce_channel_via_binding(interaction, "   ")

    assert ok is True
    pipeline.clear_binding.assert_awaited_once_with(
        interaction.guild,
        "xp",
        "announce_channel",
        BindingKind.CHANNEL,
        interaction.user,
    )
    pipeline.set_binding.assert_not_called()
    inv.assert_called_once_with(99)


@pytest.mark.asyncio
async def test_announce_helper_rejects_non_numeric_without_writing():
    from views.xp import modals as xp_modals

    interaction = _modal_interaction()
    pipeline = MagicMock()
    pipeline.set_binding = AsyncMock()
    pipeline.clear_binding = AsyncMock()

    with (
        patch(
            "services.binding_mutation.BindingMutationPipeline",
            return_value=pipeline,
        ),
        patch.object(xp_modals, "invalidate_xp_config") as inv,
    ):
        ok = await xp_modals._set_xp_announce_channel_via_binding(
            interaction,
            "not-a-channel",
        )

    assert ok is False
    pipeline.set_binding.assert_not_called()
    pipeline.clear_binding.assert_not_called()
    inv.assert_not_called()
    sent = interaction.response.send_message.await_args
    assert sent.kwargs.get("ephemeral") is True


@pytest.mark.asyncio
async def test_announce_helper_returns_false_on_dm():
    from views.xp import modals as xp_modals

    interaction = MagicMock()
    interaction.guild = None
    interaction.response.send_message = AsyncMock()

    with (
        patch(
            "services.binding_mutation.BindingMutationPipeline",
        ) as pipeline_cls,
        patch.object(xp_modals, "invalidate_xp_config") as inv,
    ):
        ok = await xp_modals._set_xp_announce_channel_via_binding(interaction, "123")

    assert ok is False
    pipeline_cls.assert_not_called()
    inv.assert_not_called()
    interaction.response.send_message.assert_awaited_once()


# ---------------------------------------------------------------------------
# SettingSpec retirement (P0-3 arc PR 2)
# ---------------------------------------------------------------------------


def test_xp_announce_channel_settingspec_retired():
    """P0-3 arc PR 2 retired the ``xp_announce_channel`` scalar SettingSpec;
    the announce channel is a binding now (``xp.announce_channel``).  Pin
    that the scalar is gone and the binding is its replacement home.
    """
    from cogs.xp.schemas import XP_BINDINGS, XP_SETTINGS

    assert "xp_announce_channel" not in {spec.name for spec in XP_SETTINGS}, (
        "xp_announce_channel scalar SettingSpec must be retired — the "
        "announce channel lives in the binding lane now (P0-3)."
    )
    assert "announce_channel" in {b.name for b in XP_BINDINGS}
