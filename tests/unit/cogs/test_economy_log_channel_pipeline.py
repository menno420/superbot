"""Regression tests — economy_cog log-channel writes use the binding lane.

The economy log channel is a Discord-resource pointer.  PR #6 first
routed its writes through ``SettingsMutationPipeline`` (the scalar
``economy_log_channel``); the P0-3 pointer-lane convergence (arc PR 2)
then **retired that scalar** and moved the channel into the binding lane
(``economy.log_channel``).  ``cogs/economy_cog.py`` now writes it via
``services.binding_mutation.BindingMutationPipeline`` from three sites:

* ``on_ready`` listener (``_ensure_log_channel`` → existing channel found)
* ``on_guild_join`` listener (``_ensure_log_channel`` → newly created)
* ``!setlogchannel`` admin command

System-triggered paths pass ``actor=None`` + ``actor_type='system'``; the
admin command passes the invoking member.  ``_ensure_log_channel``'s
"already configured?" check reads binding-first via
``config_arbitration.get_economy_log_channel``.

These tests pin the contract by:

* Asserting the cog module does not reference ``db.set_setting``.
* Patching the binding pipeline and verifying each call site invokes
  ``set_binding`` with the expected ``(subsystem, binding_name, kind,
  target_id, actor, actor_type)`` shape.
* Asserting the ``economy_log_channel`` scalar SettingSpec is retired
  and the ``economy.log_channel`` binding is its replacement home.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from core.runtime.subsystem_schema import BindingKind

_COG_PATH = (
    Path(__file__).resolve().parents[3] / "disbot" / "cogs" / "economy_cog.py"
)


# ---------------------------------------------------------------------------
# AST-level: no db.set_setting references survive in the cog
# ---------------------------------------------------------------------------


def test_economy_cog_does_not_reference_db_set_setting():
    """``cogs/economy_cog.py`` must not write settings directly — the log
    channel is a binding now, and there is no other scalar write.
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
# Helper-level: _record_log_channel hits the binding pipeline with the
# right shape
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_record_log_channel_binds_for_admin_writes():
    from cogs.economy_cog import EconomyCog

    cog = EconomyCog(MagicMock())
    guild = MagicMock(spec=discord.Guild)
    guild.id = 99
    actor = MagicMock(spec=discord.Member)
    actor.id = 7

    pipeline = MagicMock()
    pipeline.set_binding = AsyncMock(return_value=MagicMock())

    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=pipeline,
    ):
        await cog._record_log_channel(guild, "1234567890", actor=actor)

    pipeline.set_binding.assert_awaited_once_with(
        guild,
        "economy",
        "log_channel",
        BindingKind.CHANNEL,
        1234567890,
        actor,
        actor_type="user",
    )


@pytest.mark.asyncio
async def test_record_log_channel_uses_system_actor_type_for_listeners():
    """The listener-triggered paths (on_ready / on_guild_join via
    ``_ensure_log_channel``) call ``_record_log_channel`` with
    ``actor=None`` + ``actor_type='system'`` so the binding pipeline's
    capability check is bypassed via the system bucket.
    """
    from cogs.economy_cog import EconomyCog

    cog = EconomyCog(MagicMock())
    guild = MagicMock(spec=discord.Guild)
    guild.id = 99

    pipeline = MagicMock()
    pipeline.set_binding = AsyncMock(return_value=MagicMock())

    with patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=pipeline,
    ):
        await cog._record_log_channel(
            guild,
            "555",
            actor=None,
            actor_type="system",
        )

    pipeline.set_binding.assert_awaited_once_with(
        guild,
        "economy",
        "log_channel",
        BindingKind.CHANNEL,
        555,
        None,
        actor_type="system",
    )


# ---------------------------------------------------------------------------
# Listener path: _ensure_log_channel reads binding-first, then routes an
# existing-channel pickup through the binding pipeline
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_ensure_log_channel_existing_routes_through_binding():
    """When the guild has no configured log channel (binding-first read
    returns nothing) but a #economy-log already exists,
    ``_ensure_log_channel`` binds its id via the pipeline (system actor).
    """
    from cogs import economy_cog

    cog = economy_cog.EconomyCog(MagicMock())
    guild = MagicMock(spec=discord.Guild)
    guild.id = 42

    existing = MagicMock()
    existing.id = 12345

    pipeline = MagicMock()
    pipeline.set_binding = AsyncMock(return_value=MagicMock())

    with patch(
        "core.runtime.config_arbitration.get_economy_log_channel",
        new=AsyncMock(return_value=SimpleNamespace(value=None)),
    ), patch.object(
        economy_cog.resources,
        "resolve_channel",
        return_value=existing,
    ), patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=pipeline,
    ):
        await cog._ensure_log_channel(guild)

    pipeline.set_binding.assert_awaited_once()
    call = pipeline.set_binding.await_args
    assert call.args[1:5] == ("economy", "log_channel", BindingKind.CHANNEL, 12345)
    assert call.kwargs.get("actor_type") == "system"


@pytest.mark.asyncio
async def test_ensure_log_channel_skips_when_already_bound():
    """A guild that already has the channel bound (and present) is left
    alone — no re-create, no re-bind.
    """
    from cogs import economy_cog

    cog = economy_cog.EconomyCog(MagicMock())
    guild = MagicMock(spec=discord.Guild)
    guild.id = 42
    guild.get_channel = MagicMock(return_value=MagicMock())  # channel present

    pipeline = MagicMock()
    pipeline.set_binding = AsyncMock()

    with patch(
        "core.runtime.config_arbitration.get_economy_log_channel",
        new=AsyncMock(return_value=SimpleNamespace(value=98765)),
    ), patch.object(
        economy_cog.resources,
        "resolve_channel",
    ) as resolve_channel, patch(
        "services.binding_mutation.BindingMutationPipeline",
        return_value=pipeline,
    ):
        await cog._ensure_log_channel(guild)

    guild.get_channel.assert_called_once_with(98765)
    resolve_channel.assert_not_called()
    pipeline.set_binding.assert_not_called()


# ---------------------------------------------------------------------------
# SettingSpec retirement (P0-3 arc PR 2)
# ---------------------------------------------------------------------------


def test_economy_log_channel_settingspec_retired():
    """P0-3 arc PR 2 retired the ``economy_log_channel`` scalar SettingSpec;
    the log channel lives in the binding lane now (``economy.log_channel``).
    """
    from cogs.economy.schemas import ECONOMY_BINDINGS, ECONOMY_SETTINGS

    assert "economy_log_channel" not in {spec.name for spec in ECONOMY_SETTINGS}, (
        "economy_log_channel scalar SettingSpec must be retired — the log "
        "channel lives in the binding lane now (P0-3)."
    )
    assert "log_channel" in {b.name for b in ECONOMY_BINDINGS}
