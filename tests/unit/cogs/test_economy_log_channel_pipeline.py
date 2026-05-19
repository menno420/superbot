"""Regression tests for PR #6 — economy_cog log-channel writes use the pipeline.

Pre-PR-#6 ``cogs/economy_cog.py`` wrote ``ECONOMY_LOG_CHANNEL`` via
``db.set_setting`` from three sites:

* ``on_ready`` listener (``_ensure_log_channel`` → existing channel found)
* ``on_guild_join`` listener (``_ensure_log_channel`` → newly created)
* ``!setlogchannel`` admin command

PR #6 routes all three through ``services.settings_mutation.
SettingsMutationPipeline`` via the new ``_record_log_channel`` helper.
System-triggered paths pass ``actor=None`` + ``actor_type='system'``;
the admin command passes the invoking member.

These tests pin the new contract by:

* Asserting the cog module no longer references ``db.set_setting``.
* Patching the pipeline class and verifying each call site invokes
  it with the expected ``(subsystem, name, value, actor_type)`` shape.
* Asserting the ``economy_log_channel`` SettingSpec is declared with
  the empty-or-numeric validator.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

_COG_PATH = (
    Path(__file__).resolve().parents[3] / "disbot" / "cogs" / "economy_cog.py"
)


# ---------------------------------------------------------------------------
# AST-level: no db.set_setting references survive in the cog
# ---------------------------------------------------------------------------


def test_economy_cog_does_not_reference_db_set_setting():
    """``cogs/economy_cog.py`` is removed from the no-direct-writes
    allowlist in PR #6; the AST scan now enforces it.
    """
    source = _COG_PATH.read_text()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "set_setting":
            raise AssertionError(
                f"cogs/economy_cog.py still references set_setting at line "
                f"{node.lineno}",
            )


def test_economy_cog_exports_record_helper():
    cog_module = importlib.import_module("cogs.economy_cog")
    klass = cog_module.EconomyCog
    assert hasattr(klass, "_record_log_channel")


# ---------------------------------------------------------------------------
# Helper-level: _record_log_channel hits the pipeline with the right shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_log_channel_uses_pipeline_for_admin_writes():
    from cogs.economy_cog import EconomyCog

    cog = EconomyCog(MagicMock())
    guild = MagicMock(spec=discord.Guild)
    guild.id = 99
    actor = MagicMock(spec=discord.Member)
    actor.id = 7

    pipeline_instance = MagicMock()
    pipeline_instance.set_value = AsyncMock(return_value=MagicMock())

    with patch(
        "services.settings_mutation.SettingsMutationPipeline",
        return_value=pipeline_instance,
    ):
        await cog._record_log_channel(guild, "1234567890", actor=actor)

    pipeline_instance.set_value.assert_awaited_once_with(
        guild,
        "economy",
        "economy_log_channel",
        "1234567890",
        actor,
        actor_type="user",
    )


@pytest.mark.asyncio
async def test_record_log_channel_uses_system_actor_type_for_listeners():
    """The two listener-triggered paths (on_ready / on_guild_join via
    ``_ensure_log_channel``) call ``_record_log_channel`` with
    ``actor=None`` + ``actor_type='system'`` so the pipeline's
    administrator-tier check is bypassed via the system bucket.
    """
    from cogs.economy_cog import EconomyCog

    cog = EconomyCog(MagicMock())
    guild = MagicMock(spec=discord.Guild)
    guild.id = 99

    pipeline_instance = MagicMock()
    pipeline_instance.set_value = AsyncMock(return_value=MagicMock())

    with patch(
        "services.settings_mutation.SettingsMutationPipeline",
        return_value=pipeline_instance,
    ):
        await cog._record_log_channel(
            guild,
            "555",
            actor=None,
            actor_type="system",
        )

    pipeline_instance.set_value.assert_awaited_once_with(
        guild,
        "economy",
        "economy_log_channel",
        "555",
        None,
        actor_type="system",
    )


# ---------------------------------------------------------------------------
# Listener path: _ensure_log_channel routes existing-channel pickup through
# the pipeline
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_log_channel_existing_routes_through_pipeline():
    """When ``resources.resolve_channel`` finds an existing
    #economy-log, ``_ensure_log_channel`` records its id via the
    pipeline (not ``db.set_setting``).
    """
    from cogs import economy_cog

    cog = economy_cog.EconomyCog(MagicMock())
    guild = MagicMock(spec=discord.Guild)
    guild.id = 42

    existing = MagicMock()
    existing.id = 12345

    pipeline_instance = MagicMock()
    pipeline_instance.set_value = AsyncMock(return_value=MagicMock())

    with patch.object(
        economy_cog.resources,
        "resolve_settings_channel",
        new=AsyncMock(return_value=None),
    ), patch.object(
        economy_cog.resources,
        "resolve_channel",
        return_value=existing,
    ), patch(
        "services.settings_mutation.SettingsMutationPipeline",
        return_value=pipeline_instance,
    ):
        await cog._ensure_log_channel(guild)

    pipeline_instance.set_value.assert_awaited_once()
    call = pipeline_instance.set_value.await_args
    assert call.args[1:4] == ("economy", "economy_log_channel", "12345")
    assert call.kwargs.get("actor_type") == "system"


# ---------------------------------------------------------------------------
# SettingSpec presence (PR #6 schema addition)
# ---------------------------------------------------------------------------


def test_economy_log_channel_settingspec_declared():
    """PR #6 added ``economy_log_channel`` to ``ECONOMY_SETTINGS`` so the
    pipeline accepts writes for it.  Pin the spec shape and validator.
    """
    from cogs.economy.schemas import ECONOMY_SETTINGS

    by_name = {spec.name: spec for spec in ECONOMY_SETTINGS}
    assert "economy_log_channel" in by_name, (
        "economy_log_channel must be declared as a SettingSpec — "
        "PR #6 promoted it from a direct-write to a pipeline-managed "
        "scalar."
    )
    spec = by_name["economy_log_channel"]
    assert spec.value_type is str
    assert spec.default == ""
    assert spec.validator is not None
    # Empty is allowed (clears the channel).
    spec.validator("")
    # Numeric IDs are allowed.
    spec.validator("1234567890")
    # Non-numeric non-empty is rejected.
    with pytest.raises(ValueError):
        spec.validator("not-a-channel")
