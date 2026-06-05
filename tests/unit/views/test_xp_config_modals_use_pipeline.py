"""Regression tests for PR #5 — XP config modals use SettingsMutationPipeline.

Pre-PR-#5 the three XP config modals (range / cooldown / channel)
called ``db.set_setting`` directly and then manually invoked
``invalidate_xp_config``. PR #5 routes each write through
``services.settings_mutation.SettingsMutationPipeline`` so the
mutation lands with audit + per-key cache invalidation + event
emission; the modal still pokes ``invalidate_xp_config`` afterward
because the legacy composite ``XpConfig`` accessor is a separate
cache that the pipeline doesn't know about.

These tests pin the new contract by:

* Asserting the modals do not import ``db.set_setting``.
* Patching ``SettingsMutationPipeline.set_value`` and verifying each
  modal's ``on_submit`` calls it with the expected ``(subsystem,
  name, value)`` triple for valid inputs.
* Verifying ``invalidate_xp_config(guild.id)`` is called after a
  successful pipeline write so the legacy hot-path cache stays
  fresh.
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

    with patch(
        "services.settings_mutation.SettingsMutationPipeline",
        return_value=pipeline_instance,
    ), patch.object(
        xp_modals,
        "invalidate_xp_config",
    ) as invalidator:
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

    with patch(
        "services.settings_mutation.SettingsMutationPipeline",
    ) as pipeline_cls, patch.object(
        xp_modals,
        "invalidate_xp_config",
    ) as invalidator:
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

    with patch(
        "services.settings_mutation.SettingsMutationPipeline",
        return_value=pipeline_instance,
    ), patch.object(
        xp_modals,
        "invalidate_xp_config",
    ) as invalidator:
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

    with patch.object(
        xp_modals,
        "_set_xp_setting_via_pipeline",
        new=AsyncMock(return_value=True),
    ) as helper, patch.object(
        xp_modals,
        "safe_defer",
        new=AsyncMock(return_value=True),
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

    with patch.object(
        xp_modals,
        "_set_xp_setting_via_pipeline",
        new=AsyncMock(return_value=True),
    ) as helper, patch.object(
        xp_modals,
        "safe_defer",
        new=AsyncMock(return_value=True),
    ):
        await modal.on_submit(interaction)

    helper.assert_awaited_once()
    assert helper.await_args.args[1:] == ("xp_cooldown", 45)
    fake_view._rerender.assert_awaited_once()


@pytest.mark.asyncio
async def test_xp_channel_modal_writes_channel_string():
    from views.xp import modals as xp_modals

    fake_view = MagicMock()
    fake_view._rerender = AsyncMock()
    modal = xp_modals._XpChannelModal(fake_view)
    modal.channel_id = MagicMock()
    modal.channel_id.value = "1234567890"

    interaction = _modal_interaction()

    with patch.object(
        xp_modals,
        "_set_xp_setting_via_pipeline",
        new=AsyncMock(return_value=True),
    ) as helper, patch.object(
        xp_modals,
        "safe_defer",
        new=AsyncMock(return_value=True),
    ):
        await modal.on_submit(interaction)

    helper.assert_awaited_once()
    assert helper.await_args.args[1:] == ("xp_announce_channel", "1234567890")
    fake_view._rerender.assert_awaited_once()


@pytest.mark.asyncio
async def test_xp_channel_modal_writes_empty_string_to_clear():
    """Empty input clears the channel — passed through to the pipeline
    as ``""`` (the SettingSpec validator accepts empty).
    """
    from views.xp import modals as xp_modals

    fake_view = MagicMock()
    fake_view._rerender = AsyncMock()
    modal = xp_modals._XpChannelModal(fake_view)
    modal.channel_id = MagicMock()
    modal.channel_id.value = "  "

    interaction = _modal_interaction()

    with patch.object(
        xp_modals,
        "_set_xp_setting_via_pipeline",
        new=AsyncMock(return_value=True),
    ) as helper, patch.object(
        xp_modals,
        "safe_defer",
        new=AsyncMock(return_value=True),
    ):
        await modal.on_submit(interaction)

    helper.assert_awaited_once()
    assert helper.await_args.args[1:] == ("xp_announce_channel", "")


# ---------------------------------------------------------------------------
# SettingSpec presence (PR #5 schema addition)
# ---------------------------------------------------------------------------


def test_xp_announce_channel_settingspec_declared():
    """PR #5 added ``xp_announce_channel`` to ``XP_SETTINGS`` so the
    pipeline accepts writes for it. Pin the declaration and the
    validator's empty-or-numeric contract via the schema, not the
    modal.
    """
    from cogs.xp.schemas import XP_SETTINGS

    by_name = {spec.name: spec for spec in XP_SETTINGS}
    assert "xp_announce_channel" in by_name, (
        "xp_announce_channel must be declared as a SettingSpec — "
        "PR #5 promoted it from a direct-write to a pipeline-managed "
        "scalar."
    )
    spec = by_name["xp_announce_channel"]
    assert spec.value_type is str
    assert spec.default == ""
    assert spec.validator is not None
    # Empty is allowed.
    spec.validator("")
    # Numeric IDs are allowed.
    spec.validator("1234567890")
    # Non-numeric non-empty is rejected.
    with pytest.raises(ValueError):
        spec.validator("not-a-channel")
