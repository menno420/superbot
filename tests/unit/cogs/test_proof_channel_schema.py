"""Proof-channel declaration slice (Settings Phase 2 — Batch 4 pointer tail).

Pins the audit §4 promotion: the subsystem declares its channel as a
**binding** + an OPTIONAL **resource requirement** (it used to resolve a
channel literally named "proof" with no declared config at all), and the
cog's read path is **binding-first with the name lookup as fallback** —
the Q-0064 / ``btd6.version_announce_channel`` pattern.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.proof_channel.schemas import (
    PROOF_CHANNEL_CONFIG_SCHEMA,
    register_schemas,
)
from cogs.proof_channel_cog import ProofChannelCog
from core.runtime import settings_registry
from core.runtime import subsystem_schema as schema_mod
from core.runtime.resource_specs import ProvisioningPriority
from core.runtime.subsystem_schema import BindingKind


@pytest.fixture(autouse=True)
def _isolated_schema_state():
    saved = schema_mod.all_schemas()
    schema_mod._reset_for_tests()
    settings_registry._reset_for_tests()
    yield
    schema_mod._reset_for_tests()
    for schema in saved.values():
        schema_mod.register(schema)
    settings_registry._reset_for_tests()


# ---------------------------------------------------------------------------
# Schema declaration
# ---------------------------------------------------------------------------


def test_schema_declares_channel_binding_and_optional_resource():
    binding = PROOF_CHANNEL_CONFIG_SCHEMA.bindings[0]
    assert binding.name == "proof_channel"
    assert binding.kind is BindingKind.CHANNEL
    assert binding.required is False

    requirement = PROOF_CHANNEL_CONFIG_SCHEMA.resource_requirements[0]
    assert requirement.intent == "proof"
    assert requirement.binding_name == "proof_channel"
    # OPTIONAL: prize sessions are niche — a missing channel must stay
    # info-only in readiness, never a warning.
    assert requirement.provisioning.priority is ProvisioningPriority.OPTIONAL
    assert requirement.provisioning.suggested_name == "proof"


def test_register_schemas_is_idempotent():
    register_schemas()
    register_schemas()
    assert "proof_channel" in schema_mod.all_schemas()


def test_binding_capability_is_declared_in_registry():
    """The identity contract warns on schema capabilities missing from the
    SUBSYSTEMS registry — pin that ours is declared."""
    from utils.subsystem_registry import SUBSYSTEMS

    cap = PROOF_CHANNEL_CONFIG_SCHEMA.bindings[0].capability_required
    assert cap == "proof_channel.settings.configure"
    assert cap in SUBSYSTEMS["proof_channel"]["capabilities"]


def test_proof_channel_becomes_actionable_settings_group():
    """With a binding declared, the Settings hub's §6 inclusion rule picks
    the subsystem up (it was excluded as schema-less before this slice)."""
    from services.customization_catalogue import actionable_settings_groups

    register_schemas()
    assert "proof_channel" in {g.subsystem for g in actionable_settings_groups()}


# ---------------------------------------------------------------------------
# Binding-first read path
# ---------------------------------------------------------------------------


def _guild(channel: object = None) -> MagicMock:
    guild = MagicMock()
    guild.id = 99
    guild.get_channel = MagicMock(return_value=channel)
    return guild


def _cog() -> ProofChannelCog:
    return ProofChannelCog(bot=MagicMock())


@pytest.mark.asyncio
async def test_bound_channel_wins_over_name_lookup():
    bound = MagicMock(spec=discord.TextChannel)
    guild = _guild(channel=bound)
    with (
        patch(
            "core.runtime.bindings.get_binding",
            AsyncMock(return_value=MagicMock(target_id=555)),
        ),
        patch(
            "cogs.proof_channel_cog.resources.resolve_channel",
        ) as name_lookup,
    ):
        result = await _cog().get_proof_channel(guild)

    assert result is bound
    guild.get_channel.assert_called_once_with(555)
    name_lookup.assert_not_called()


@pytest.mark.asyncio
async def test_unbound_slot_falls_back_to_name_lookup():
    fallback = MagicMock(spec=discord.TextChannel)
    guild = _guild()
    with (
        patch(
            "core.runtime.bindings.get_binding",
            AsyncMock(return_value=MagicMock(target_id=None)),
        ),
        patch(
            "cogs.proof_channel_cog.resources.resolve_channel",
            return_value=fallback,
        ) as name_lookup,
    ):
        result = await _cog().get_proof_channel(guild)

    assert result is fallback
    name_lookup.assert_called_once_with(guild, name="proof")


@pytest.mark.asyncio
async def test_binding_read_failure_degrades_to_name_lookup():
    fallback = MagicMock(spec=discord.TextChannel)
    guild = _guild()
    with (
        patch(
            "core.runtime.bindings.get_binding",
            AsyncMock(side_effect=RuntimeError("db down")),
        ),
        patch(
            "cogs.proof_channel_cog.resources.resolve_channel",
            return_value=fallback,
        ),
    ):
        result = await _cog().get_proof_channel(guild)

    assert result is fallback


@pytest.mark.asyncio
async def test_bound_but_deleted_channel_falls_back():
    fallback = MagicMock(spec=discord.TextChannel)
    guild = _guild(channel=None)  # bound id no longer resolves
    with (
        patch(
            "core.runtime.bindings.get_binding",
            AsyncMock(return_value=MagicMock(target_id=555)),
        ),
        patch(
            "cogs.proof_channel_cog.resources.resolve_channel",
            return_value=fallback,
        ),
    ):
        result = await _cog().get_proof_channel(guild)

    assert result is fallback
