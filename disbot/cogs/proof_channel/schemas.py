"""Proof-channel SubsystemSchema (Settings Phase 2 — Batch 4 pointer tail).

The settings audit §4 classified proof_channel "Setup/binding candidate;
command-managed — resource pointers documented for promotion but no
schema. Add binding/resource declarations before exposing." Before this
schema the cog resolved its channel **by the literal name** ``"proof"``
(`resources.resolve_channel(guild, name="proof")`) — invisible to the
binding/provisioning catalogues, setup readiness, and the Settings hub,
and unusable for any guild whose proof channel is named differently.

This declares the missing configuration (the Q-0064 / BTD6
``version_announce_channel`` pattern):

* **Binding** ``proof_channel`` — the channel prize-claim sessions
  manage. When bound it takes precedence; the name-based ``#proof``
  lookup stays as the compatibility fallback (read path:
  ``ProofChannelCog.get_proof_channel``). Write-path convergence is
  settings Phase 3 territory, as with every other legacy pointer lane.
* **Resource requirement** ``proof`` — OPTIONAL priority: prize
  sessions are a niche feature, so a missing channel is info-only in
  readiness, never a warning.
"""

from __future__ import annotations

from core.runtime.resource_specs import (
    ProvisioningHint,
    ProvisioningPriority,
    ResourceKind,
    ResourceRequirement,
)
from core.runtime.subsystem_schema import (
    BindingKind,
    BindingSpec,
    SubsystemSchema,
)

_CAPABILITY = "proof_channel.settings.configure"


PROOF_CHANNEL_BINDINGS: tuple[BindingSpec, ...] = (
    BindingSpec(
        name="proof_channel",
        kind=BindingKind.CHANNEL,
        required=False,
        hint=(
            "Channel used for prize-claim sessions (`+prize` / `timedprize` "
            "lock it to the winner). When bound it takes precedence over "
            "the legacy lookup of a channel literally named `proof`."
        ),
        capability_required=_CAPABILITY,
    ),
)


PROOF_CHANNEL_RESOURCE_REQUIREMENTS: tuple[ResourceRequirement, ...] = (
    ResourceRequirement(
        kind=ResourceKind.CHANNEL,
        intent="proof",
        provisioning=ProvisioningHint(
            priority=ProvisioningPriority.OPTIONAL,
            suggested_name="proof",
        ),
        binding_name="proof_channel",
        description=(
            "Channel where winners post proof and prize-claim sessions "
            "grant exclusive access. Optional — only guilds running "
            "prize events need it."
        ),
    ),
)


PROOF_CHANNEL_CONFIG_SCHEMA = SubsystemSchema(
    subsystem="proof_channel",
    bindings=PROOF_CHANNEL_BINDINGS,
    resource_requirements=PROOF_CHANNEL_RESOURCE_REQUIREMENTS,
    version=1,
)


def register_schemas() -> None:
    """Register the proof-channel subsystem schema. Idempotent."""
    from core.runtime import subsystem_schema

    subsystem_schema.register(PROOF_CHANNEL_CONFIG_SCHEMA)


__all__ = [
    "PROOF_CHANNEL_BINDINGS",
    "PROOF_CHANNEL_CONFIG_SCHEMA",
    "PROOF_CHANNEL_RESOURCE_REQUIREMENTS",
    "register_schemas",
]
