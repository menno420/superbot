"""AI natural-language policy resolver — M2 single chokepoint.

Returns a typed :class:`PolicyDecision` answering "should we reply?"
for a single message. Pure resolver: no DB writes, no I/O beyond the
DB reads it has to do, no gateway calls. Callers feed the decision
into the rest of the natural-language stage.

Precedence (must match the binding decision in the refined plan):

    guild baseline (ai_guild_policy)
        → category override (ai_category_policy)
        → channel override (ai_channel_policy)
        → role eligibility + min-level adjustment (ai_role_policy)
        → per-message cooldown / fresh-user allowance
        → final PolicyDecision

Rules:

* Channel ``mode='disabled'`` and category ``mode='disabled'`` always
  win — they explicitly forbid role-based lowering.
* Explicit role deny wins over any other allow.
* Among allowed roles, the most permissive ``min_level_override``
  wins (i.e. the smallest configured floor).
* No per-user policy table in this initiative.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from typing import Any

from core.runtime.ai.contracts import PolicyDenialReason
from utils.db import ai as ai_db

logger = logging.getLogger("bot.services.ai_natural_language_policy")


# ---------------------------------------------------------------------------
# Inputs / outputs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MessageContext:
    """Minimal context the resolver needs about an inbound message."""

    guild_id: int
    channel_id: int
    category_id: int | None
    user_id: int
    user_level: int
    user_role_ids: tuple[int, ...]
    is_mention: bool
    is_fresh_user: bool


@dataclass(frozen=True)
class PolicyDecision:
    """Result of policy resolution.

    ``allowed`` is the sole signal callers need to decide whether to
    proceed. ``reason_code`` is always populated — successful
    decisions carry the sentinel ``PolicyDenialReason.NONE`` so the
    audit row's NOT NULL column stays meaningful without overloading.

    ``precedence_trace`` is populated only when :func:`resolve` is
    called with ``dry_run=True`` (PR4B). It records each precedence
    step that influenced the decision so the admin preview UI can
    show "why" without re-implementing the resolver. Live decisions
    leave it empty so the production audit / payload size stays flat.
    """

    allowed: bool
    reason_code: PolicyDenialReason
    effective_min_level: int
    effective_cooldown: int
    instruction_profile_ids: tuple[int, ...] = ()
    policy_snapshot_hash: str = ""
    extra: dict[str, Any] = field(default_factory=dict)
    precedence_trace: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# Cached read of the per-guild policy bundle
# ---------------------------------------------------------------------------


_CACHE: dict[int, tuple[int, dict[str, Any]]] = {}


def invalidate(guild_id: int) -> None:
    """Drop the cached bundle for ``guild_id``.

    The mutation services call this after every write so the next
    resolve sees the new state. The ``generation`` counter on
    ``ai_guild_policy`` is the underlying source of truth — even
    without manual invalidation a fresh read would notice the bump.
    """
    _CACHE.pop(guild_id, None)


def _reset_for_tests() -> None:
    _CACHE.clear()


async def _load_bundle(guild_id: int) -> dict[str, Any]:
    """Load (with cache) the four tables relevant to one guild."""
    policy = await ai_db.get_guild_policy(guild_id)
    generation = (policy or {}).get("generation", 0)

    cached = _CACHE.get(guild_id)
    if cached is not None and cached[0] == generation and policy is not None:
        return cached[1]

    channel = await ai_db.list_channel_policies(guild_id)
    category = await ai_db.list_category_policies(guild_id)
    role = await ai_db.list_role_policies(guild_id)

    bundle = {
        "policy": policy or {},
        "channel": {row["channel_id"]: row for row in channel},
        "category": {row["category_id"]: row for row in category},
        "role": {row["role_id"]: row for row in role},
    }
    if policy is not None:
        _CACHE[guild_id] = (generation, bundle)
    return bundle


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


async def resolve(
    ctx: MessageContext,
    *,
    dry_run: bool = False,
) -> PolicyDecision:
    """Run the precedence rule for ``ctx`` and return the decision.

    When ``dry_run=True`` (PR4B), the decision's ``precedence_trace``
    is populated with a step-by-step record of each level that
    influenced the outcome. Live behavior is otherwise identical:
    ``resolve`` is a pure read with no side effects on cooldown
    state or audit (those live in the caller's stage), so a dry-run
    is safe to call from an admin preview UI without disturbing
    production resolution state.
    """
    trace: list[str] | None = [] if dry_run else None
    bundle = await _load_bundle(ctx.guild_id)
    policy = bundle["policy"]

    if not policy:
        # No row yet → guild has never configured AI; deny by default
        # so an unconfigured deployment never silently starts replying.
        if trace is not None:
            trace.append("guild: no ai_guild_policy row → deny GUILD_NOT_CONFIGURED")
        return PolicyDecision(
            allowed=False,
            reason_code=PolicyDenialReason.GUILD_NOT_CONFIGURED,
            effective_min_level=2,
            effective_cooldown=30,
            policy_snapshot_hash=_hash({"missing": True}),
            precedence_trace=tuple(trace or ()),
        )

    if not policy.get("enabled"):
        if trace is not None:
            trace.append("guild: enabled=false → deny AI_GLOBALLY_DISABLED")
        return _deny(
            policy,
            reason=PolicyDenialReason.AI_GLOBALLY_DISABLED,
            min_level=int(policy.get("minimum_level_default", 2)),
            cooldown=int(policy.get("cooldown_seconds", 30)),
            trace=trace,
        )

    if not policy.get("natural_language_enabled"):
        if trace is not None:
            trace.append(
                "guild: natural_language_enabled=false → deny AI_NL_DISABLED_FOR_GUILD",
            )
        return _deny(
            policy,
            reason=PolicyDenialReason.AI_NL_DISABLED_FOR_GUILD,
            min_level=int(policy.get("minimum_level_default", 2)),
            cooldown=int(policy.get("cooldown_seconds", 30)),
            trace=trace,
        )

    # Start with guild baseline.
    min_level = int(policy.get("minimum_level_default", 2))
    cooldown = int(policy.get("cooldown_seconds", 30))
    profile_ids: list[int] = []
    if policy.get("guild_instruction_profile_id"):
        profile_ids.append(int(policy["guild_instruction_profile_id"]))
    if trace is not None:
        trace.append(
            f"guild: baseline min_level={min_level} cooldown={cooldown}s",
        )

    # Category override.
    cat_row = bundle["category"].get(ctx.category_id) if ctx.category_id else None
    if cat_row:
        if cat_row["mode"] == "disabled":
            if trace is not None:
                trace.append(
                    f"category {ctx.category_id}: mode=disabled → deny CATEGORY_DISABLED",
                )
            return _deny(
                policy,
                reason=PolicyDenialReason.CATEGORY_DISABLED,
                min_level=min_level,
                cooldown=cooldown,
                profile_ids=profile_ids,
                trace=trace,
            )
        if cat_row.get("min_level") is not None:
            min_level = int(cat_row["min_level"])
        if cat_row.get("cooldown_seconds") is not None:
            cooldown = int(cat_row["cooldown_seconds"])
        if cat_row.get("instruction_profile_id"):
            profile_ids.append(int(cat_row["instruction_profile_id"]))
        if trace is not None:
            trace.append(
                f"category {ctx.category_id}: mode={cat_row['mode']} "
                f"min_level={min_level} cooldown={cooldown}s",
            )
    elif trace is not None and ctx.category_id is not None:
        trace.append(f"category {ctx.category_id}: no override (inherit)")

    # Channel override.
    chan_row = bundle["channel"].get(ctx.channel_id)
    if chan_row:
        if chan_row["mode"] == "disabled":
            if trace is not None:
                trace.append(
                    f"channel {ctx.channel_id}: mode=disabled → deny CHANNEL_DISABLED",
                )
            return _deny(
                policy,
                reason=PolicyDenialReason.CHANNEL_DISABLED,
                min_level=min_level,
                cooldown=cooldown,
                profile_ids=profile_ids,
                trace=trace,
            )
        if chan_row["mode"] == "mention_only" and not ctx.is_mention:
            if trace is not None:
                trace.append(
                    f"channel {ctx.channel_id}: mode=mention_only and "
                    "is_mention=false → deny NO_MENTION_REQUIRED",
                )
            return _deny(
                policy,
                reason=PolicyDenialReason.NO_MENTION_REQUIRED,
                min_level=min_level,
                cooldown=cooldown,
                profile_ids=profile_ids,
                trace=trace,
            )
        if chan_row.get("min_level") is not None:
            min_level = int(chan_row["min_level"])
        if chan_row.get("cooldown_seconds") is not None:
            cooldown = int(chan_row["cooldown_seconds"])
        if chan_row.get("instruction_profile_id"):
            profile_ids.append(int(chan_row["instruction_profile_id"]))
        if trace is not None:
            trace.append(
                f"channel {ctx.channel_id}: mode={chan_row['mode']} "
                f"min_level={min_level} cooldown={cooldown}s",
            )
    elif trace is not None:
        trace.append(f"channel {ctx.channel_id}: no override (inherit)")

    # Role eligibility.
    role_decision = _resolve_role(bundle["role"], ctx.user_role_ids)
    if role_decision["denied"]:
        if trace is not None:
            trace.append("role: explicit deny → deny ROLE_DENIED")
        return _deny(
            policy,
            reason=PolicyDenialReason.ROLE_DENIED,
            min_level=min_level,
            cooldown=cooldown,
            profile_ids=profile_ids,
            trace=trace,
        )

    if role_decision["override_min_level"] is not None:
        candidate = int(role_decision["override_min_level"])
        min_level = min(min_level, candidate)
        if trace is not None:
            trace.append(
                f"role: most-permissive override → min_level={min_level}",
            )

    bypass_cooldown = role_decision["bypass_cooldown"]
    effective_cooldown = 0 if bypass_cooldown else cooldown
    if trace is not None and bypass_cooldown:
        trace.append("role: bypass_cooldown=true → effective_cooldown=0s")

    # Per-user level check (XP / fresh-user allowance).
    if ctx.user_level < min_level:
        if (
            ctx.is_fresh_user
            and ctx.is_mention
            and policy.get("fresh_user_mention_allowance", 0) > 0
        ):
            if trace is not None:
                trace.append(
                    f"user: level={ctx.user_level} < min={min_level} "
                    "BUT fresh-user mention allowance → allowed",
                )
        else:
            if trace is not None:
                trace.append(
                    f"user: level={ctx.user_level} < min={min_level} → "
                    "deny BELOW_MIN_LEVEL",
                )
            return _deny(
                policy,
                reason=PolicyDenialReason.BELOW_MIN_LEVEL,
                min_level=min_level,
                cooldown=effective_cooldown,
                profile_ids=profile_ids,
                trace=trace,
            )
    elif trace is not None:
        trace.append(
            f"user: level={ctx.user_level} ≥ min={min_level} → allowed",
        )

    snapshot = _hash(
        {
            "g": policy.get("generation", 0),
            "min": min_level,
            "cd": effective_cooldown,
            "profiles": profile_ids,
            "allowed": True,
        },
    )
    if trace is not None:
        trace.append(
            f"final: allowed min_level={min_level} cooldown={effective_cooldown}s",
        )
    return PolicyDecision(
        allowed=True,
        reason_code=PolicyDenialReason.NONE,
        effective_min_level=min_level,
        effective_cooldown=effective_cooldown,
        instruction_profile_ids=tuple(profile_ids),
        policy_snapshot_hash=snapshot,
        precedence_trace=tuple(trace or ()),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _deny(
    policy: dict[str, Any],
    *,
    reason: PolicyDenialReason,
    min_level: int,
    cooldown: int,
    profile_ids: list[int] | None = None,
    trace: list[str] | None = None,
) -> PolicyDecision:
    return PolicyDecision(
        allowed=False,
        reason_code=reason,
        effective_min_level=int(min_level),
        effective_cooldown=int(cooldown),
        instruction_profile_ids=tuple(profile_ids or ()),
        policy_snapshot_hash=_hash(
            {"g": policy.get("generation", 0), "deny": reason.value},
        ),
        precedence_trace=tuple(trace or ()),
    )


def _resolve_role(
    role_table: dict[int, dict[str, Any]],
    user_role_ids: tuple[int, ...],
) -> dict[str, Any]:
    """Aggregate the user's roles into a single decision.

    Returns ``{denied, override_min_level, bypass_cooldown}``. Any
    explicit ``deny`` short-circuits. Among ``allow`` rows we collect
    the smallest ``min_level_override`` (most permissive) and OR the
    ``bypass_cooldown`` flags. ``inherit`` rows have no effect.
    """
    denied = False
    override: int | None = None
    bypass = False
    for role_id in user_role_ids:
        row = role_table.get(role_id)
        if not row:
            continue
        if row["decision"] == "deny":
            denied = True
            break
        if row["decision"] == "allow":
            if row.get("min_level_override") is not None:
                candidate = int(row["min_level_override"])
                override = candidate if override is None else min(override, candidate)
            if row.get("bypass_cooldown"):
                bypass = True
    return {
        "denied": denied,
        "override_min_level": override,
        "bypass_cooldown": bypass,
    }


def _hash(obj: Any) -> str:
    """Stable short hash for the audit snapshot column."""
    blob = json.dumps(obj, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


__all__ = [
    "MessageContext",
    "PolicyDecision",
    "invalidate",
    "resolve",
]
