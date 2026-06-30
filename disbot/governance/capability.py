"""Capability-native authority resolution for mutation pipelines (ADR-005 A1).

The settings / binding / resource-provisioning mutation pipelines delegate their
authority check here instead of hard-coding an administrator-tier floor.  An
actor is authorized for a mutation when it holds the capability the spec
declares (``SettingSpec.capability_required`` / ``BindingSpec.capability_required``).

Policy (v1):

* ``system`` / ``backfill`` actors bypass the check (scripted ops, migrations).
* ``setup_delegate`` (Q-0098) — a member the server owner delegated *apply*
  authority to via ``/setup-delegate``.  Authorized at the floor like
  ``system`` / ``backfill``, but unlike them it is **not** a blind
  short-circuit: it must still be a member of the target guild and stays
  subject to the revoke overlay.  It is minted only by
  :func:`services.setup_operations.apply_operations`, which re-verifies the live
  delegation (``setup_access.can_apply_setup``) before doing so — so the
  delegation itself is the floor.  An AST fence
  (``tests/unit/invariants/test_setup_delegate_actor_boundary.py``) keeps the
  ``"setup_delegate"`` token confined to this authority contract.
* An actor that is not a member of the **target** guild is denied (authority is
  bound to the write target, so privilege in guild A cannot authorize a write to
  guild B).
* The required tier is the **administrator floor** — the same floor the pipelines
  enforced before ADR-005, now keyed on the declared capability so a future
  per-capability matrix can slot in without touching the pipelines.  An empty
  capability resolves to this same floor (NOT "no auth").
* A per-guild **revoke-only** overlay: an explicit ``False`` row in
  ``capability_execution_overrides`` (read via :mod:`governance.execution`) turns
  an otherwise-allowed actor OFF for that capability.  An explicit ``True`` never
  *grants* a below-floor actor — that would be privilege escalation via a
  guild-config row.

Layer: governance → utils / core only.  No services, views, or cogs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from config import is_platform_owner
from utils.visibility_rules import get_member_visibility_tier, is_tier_sufficient

logger = logging.getLogger("bot.governance.capability")

# The administrator floor preserved from the pre-ADR-005 pipelines.  v1 keeps a
# single floor for every capability; a future capability -> tier matrix would
# replace this constant with a lookup.
_DEFAULT_REQUIRED_TIER = "administrator"

__all__ = ["CapabilityDecision", "actor_holds_capability"]


@dataclass(frozen=True)
class CapabilityDecision:
    """Result of a capability authority check.

    ``required_tier`` is empty for the system/backfill bypass; ``member_tier`` is
    ``None`` whenever no tier was computed (bypass or non-member context).
    """

    allowed: bool
    capability: str
    required_tier: str
    member_tier: str | None
    reason: str


async def actor_holds_capability(
    actor: Any,
    guild: Any,
    capability: str,
    *,
    actor_type: str = "user",
) -> CapabilityDecision:
    """Resolve whether ``actor`` may perform a mutation requiring ``capability``.

    See the module docstring for the v1 policy.  ``guild`` is the **target** guild
    of the write; a non-system actor must be a member of it.  It may be ``None``
    only for the ``system`` / ``backfill`` bypass.
    """
    # 1. Scripted / migration bypass — never dereferences actor or guild.
    if actor_type in ("system", "backfill"):
        return CapabilityDecision(
            allowed=True,
            capability=capability,
            required_tier="",
            member_tier=None,
            reason=f"{actor_type} actor bypasses the capability check",
        )

    # 2. Must be a member of the TARGET guild.  Binding authority to the write
    #    target (not merely any guild the actor belongs to) stops a member who is
    #    privileged in guild A from authorizing a write to guild B.
    actor_guild = getattr(actor, "guild", None)
    if (
        actor is None
        or actor_guild is None
        or guild is None
        or getattr(actor_guild, "id", None) != getattr(guild, "id", None)
    ):
        return CapabilityDecision(
            allowed=False,
            capability=capability,
            required_tier=_DEFAULT_REQUIRED_TIER,
            member_tier=None,
            reason=(
                "mutation requires a guild-member actor in the target guild "
                f"(actor_type={actor_type!r})"
            ),
        )

    actor_id = getattr(actor, "id", None)

    # 2b. Platform-owner override.  The configured bot owner
    #     (config.BOT_OWNER_USER_ID / PermissionTier.PLATFORM_OWNER) holds full
    #     bot-configuration authority in any guild they are a member of, even
    #     without Discord permissions there, so they can always set the bot up
    #     correctly.  Placed AFTER the step-2 membership check so it composes
    #     with the "authority bound to the write target" invariant (no
    #     cross-guild escalation) and BEFORE the revoke overlay so a guild
    #     cannot revoke the platform owner's authority.
    if is_platform_owner(actor_id):
        return CapabilityDecision(
            allowed=True,
            capability=capability,
            required_tier=_DEFAULT_REQUIRED_TIER,
            member_tier="owner",
            reason=(
                f"platform owner {actor_id!r} override for "
                f"capability={capability or '(default)'!r} "
                "(config.BOT_OWNER_USER_ID)"
            ),
        )

    # 3. Authority floor, keyed on the declared capability.  Tier is computed
    #    against the target guild's owner (actor_guild.id == guild.id here).
    guild_owner_id = getattr(guild, "owner_id", 0) or 0
    member_tier = get_member_visibility_tier(actor, guild_owner_id)
    if actor_type == "setup_delegate":
        # Q-0098 — Setup-delegate apply authority.  The server owner delegated
        # apply authority to this (possibly NON-administrator) member.  Only
        # services.setup_operations.apply_operations mints this actor_type, and
        # only after re-verifying setup_access.can_apply_setup() against a fresh
        # SetupSession at apply time — so the delegation itself satisfies the
        # floor, exactly as system/backfill satisfy it by being scripted ops.
        # This is deliberately NOT the step-1 short-circuit: a delegate must
        # still be a member of the target guild (step 2) and stays subject to
        # the revoke-only overlay (step 4).  The tier is still computed so the
        # audit reason names who actually applied.
        allowed = True
    else:
        allowed = is_tier_sufficient(member_tier, _DEFAULT_REQUIRED_TIER)

    # 4. Revoke-only per-guild overlay (declared capabilities only).  An explicit
    #    disable flips allow -> deny; an explicit enable is NOT used to grant a
    #    below-floor actor (no privilege escalation via guild config).  This
    #    applies to a setup_delegate too: an owner can revoke a capability from a
    #    delegate just as from any member.
    if capability and guild is not None:
        try:
            from governance.execution import get_capability_override

            override = await get_capability_override(guild.id, capability)
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("capability override read failed (%s); ignoring", exc)
            override = None
        if override is False:
            allowed = False

    if allowed and actor_type == "setup_delegate":
        reason = (
            f"delegated setup admin {actor_id!r} (tier={member_tier!r}) "
            f"authorized for capability={capability or '(default)'!r} via "
            f"setup-delegate apply authority (Q-0098)"
        )
    elif allowed:
        reason = (
            f"member {actor_id!r} (tier={member_tier!r}) authorized for "
            f"capability={capability or '(default)'!r}"
        )
    elif actor_type == "setup_delegate":
        reason = (
            f"delegated setup admin {actor_id!r} (tier={member_tier!r}) REVOKED "
            f"for capability={capability or '(default)'!r}"
        )
    else:
        reason = (
            f"member {actor_id!r} (tier={member_tier!r}) requires at least "
            f"{_DEFAULT_REQUIRED_TIER!r} for capability={capability or '(default)'!r}"
        )
    return CapabilityDecision(
        allowed=allowed,
        capability=capability,
        required_tier=_DEFAULT_REQUIRED_TIER,
        member_tier=member_tier,
        reason=reason,
    )
