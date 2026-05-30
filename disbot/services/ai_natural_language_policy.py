"""AI natural-language policy resolver — M2 single chokepoint.

Returns a typed :class:`PolicyDecision` answering "should we reply?"
for a single message. Pure resolver: no DB writes, no I/O beyond the
DB reads it has to do, no gateway calls. Callers feed the decision
into the rest of the natural-language stage.

Precedence (most-specific-wins for mode; chain for value inheritance):

    guild AI hard gate (ai_guild_policy.enabled)
        → channel explicit mode (ai_channel_policy.mode)
        → category explicit mode (ai_category_policy.mode)
        → guild natural-language baseline (natural_language_enabled)
        → role policy (ai_role_policy)
        → level gate
        → (cooldown gate — enforced by the caller's stage)

Rules:

* ``ai_guild_policy.enabled=false`` is the only hard kill switch — no
  scoped override can resurrect AI when AI itself is disabled.
* Channel explicit mode wins over category explicit mode. Category
  wins over the guild natural-language baseline.
* ``mode='inherit'`` (and any missing row) means "no opinion at this
  scope" — fall through to the next layer. Param values
  (min_level/cooldown/profile) at an ``inherit`` scope still apply if
  set, preserving the existing value-inheritance chain.
* ``mode='disabled'`` at the selected scope denies with the
  source-specific reason (CHANNEL_DISABLED / CATEGORY_DISABLED /
  AI_NL_DISABLED_FOR_GUILD).
* ``mode='mention_only'`` at the selected scope requires a mention,
  regardless of which scope sourced it (channel or category).
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
from typing import Any, Literal

from core.runtime.ai.contracts import PolicyDenialReason
from services import ai_permission_service
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

    ``effective_mode`` and ``effective_source`` carry the typed mode
    decision that won the most-specific-wins selection. They are
    empty strings on the early-return paths
    (``GUILD_NOT_CONFIGURED``, ``AI_GLOBALLY_DISABLED``) where no
    effective policy is computed.

    ``precedence_trace`` is populated only when :func:`resolve` is
    called with ``dry_run=True``. It records each precedence step that
    influenced the decision so the admin preview UI can show "why"
    without re-implementing the resolver. Live decisions leave it
    empty so the production audit / payload size stays flat.
    """

    allowed: bool
    reason_code: PolicyDenialReason
    effective_min_level: int
    effective_cooldown: int
    effective_mode: str = ""
    effective_source: str = ""
    instruction_profile_ids: tuple[int, ...] = ()
    policy_snapshot_hash: str = ""
    extra: dict[str, Any] = field(default_factory=dict)
    precedence_trace: tuple[str, ...] = ()
    # True when the allow relied on the fresh-user mention allowance (the
    # asker was below the level floor). The stage consumes one unit of the
    # allowance only when it actually sends a reply, so the budget is spent
    # per delivered reply rather than per attempt.
    used_fresh_allowance: bool = False


@dataclass(frozen=True)
class _EffectivePolicy:
    """Resolver-private selection result.

    Captures the winning mode and the merged value-inheritance chain
    so the mode/role/level gates downstream do not need to re-walk
    the layers.
    """

    source: Literal["channel", "category", "guild"]
    mode: Literal["always_reply", "mention_only", "disabled"]
    min_level: int
    cooldown_seconds: int
    instruction_profile_ids: tuple[int, ...]


_DISABLED_REASON_BY_SOURCE: dict[str, PolicyDenialReason] = {
    "channel": PolicyDenialReason.CHANNEL_DISABLED,
    "category": PolicyDenialReason.CATEGORY_DISABLED,
    "guild": PolicyDenialReason.AI_NL_DISABLED_FOR_GUILD,
}


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

    When ``dry_run=True``, the decision's ``precedence_trace`` is
    populated with a step-by-step record of each level that influenced
    the outcome. Live behavior is otherwise identical: ``resolve`` is
    a pure read with no side effects on cooldown state or audit
    (those live in the caller's stage), so a dry-run is safe to call
    from an admin preview UI without disturbing production resolution
    state.
    """
    trace: list[str] | None = [] if dry_run else None
    bundle = await _load_bundle(ctx.guild_id)
    policy = bundle["policy"]

    if not policy:
        # No row yet → guild has never configured AI; deny by default
        # so an unconfigured deployment never silently starts replying.
        if trace is not None:
            trace.append(
                "guild_ai_gate: no ai_guild_policy row → deny GUILD_NOT_CONFIGURED",
            )
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
            trace.append("guild_ai_gate: AI enabled=false → deny AI_GLOBALLY_DISABLED")
        return _deny(
            policy,
            reason=PolicyDenialReason.AI_GLOBALLY_DISABLED,
            min_level=int(policy.get("minimum_level_default", 2)),
            cooldown=int(policy.get("cooldown_seconds", 30)),
            trace=trace,
        )

    if trace is not None:
        trace.append("guild_ai_gate: AI enabled=true")

    # ---- Phase A: accumulate params (guild → category → channel) ----
    # Mode votes are captured separately so most-specific-wins can pick
    # without conflating "no opinion" with explicit modes.
    min_level = int(policy.get("minimum_level_default", 2))
    cooldown = int(policy.get("cooldown_seconds", 30))
    profile_ids: list[int] = []
    if policy.get("guild_instruction_profile_id"):
        profile_ids.append(int(policy["guild_instruction_profile_id"]))

    cat_row = bundle["category"].get(ctx.category_id) if ctx.category_id else None
    cat_mode: str | None = None
    if cat_row:
        row_mode = cat_row.get("mode")
        if row_mode and row_mode != "inherit":
            cat_mode = row_mode
        if cat_row.get("min_level") is not None:
            min_level = int(cat_row["min_level"])
        if cat_row.get("cooldown_seconds") is not None:
            cooldown = int(cat_row["cooldown_seconds"])
        if cat_row.get("instruction_profile_id"):
            profile_ids.append(int(cat_row["instruction_profile_id"]))
        if trace is not None:
            trace.append(
                f"category_policy: mode={row_mode or 'inherit'} "
                f"min_level={min_level} cooldown={cooldown}s",
            )
    elif trace is not None and ctx.category_id is not None:
        trace.append(f"category_policy: no row for {ctx.category_id} (inherit)")

    chan_row = bundle["channel"].get(ctx.channel_id)
    chan_mode: str | None = None
    if chan_row:
        row_mode = chan_row.get("mode")
        if row_mode and row_mode != "inherit":
            chan_mode = row_mode
        if chan_row.get("min_level") is not None:
            min_level = int(chan_row["min_level"])
        if chan_row.get("cooldown_seconds") is not None:
            cooldown = int(chan_row["cooldown_seconds"])
        if chan_row.get("instruction_profile_id"):
            profile_ids.append(int(chan_row["instruction_profile_id"]))
        if trace is not None:
            trace.append(
                f"channel_policy: mode={row_mode or 'inherit'} "
                f"min_level={min_level} cooldown={cooldown}s",
            )
    elif trace is not None:
        trace.append(f"channel_policy: no row for {ctx.channel_id} (inherit)")

    # ---- Phase B: select effective policy (most-specific-wins for mode) ----
    nl_enabled = bool(policy.get("natural_language_enabled"))
    baseline_mode: Literal["always_reply", "disabled"] = (
        "always_reply" if nl_enabled else "disabled"
    )
    if trace is not None:
        trace.append(
            f"guild_baseline: natural_language_enabled={nl_enabled} → "
            f"baseline mode={baseline_mode}",
        )

    effective: _EffectivePolicy
    if chan_mode is not None:
        effective = _EffectivePolicy(
            source="channel",
            mode=chan_mode,  # type: ignore[arg-type]
            min_level=min_level,
            cooldown_seconds=cooldown,
            instruction_profile_ids=tuple(profile_ids),
        )
    elif cat_mode is not None:
        effective = _EffectivePolicy(
            source="category",
            mode=cat_mode,  # type: ignore[arg-type]
            min_level=min_level,
            cooldown_seconds=cooldown,
            instruction_profile_ids=tuple(profile_ids),
        )
    else:
        effective = _EffectivePolicy(
            source="guild",
            mode=baseline_mode,
            min_level=min_level,
            cooldown_seconds=cooldown,
            instruction_profile_ids=tuple(profile_ids),
        )

    if trace is not None:
        trace.append(
            f"effective_policy: source={effective.source} mode={effective.mode} "
            f"min_level={effective.min_level} cooldown={effective.cooldown_seconds}s",
        )

    # ---- Mode gate ----
    if effective.mode == "disabled":
        reason = _DISABLED_REASON_BY_SOURCE[effective.source]
        if trace is not None:
            trace.append(f"mode_gate: mode=disabled → deny {reason.name}")
        return _deny(
            policy,
            reason=reason,
            min_level=effective.min_level,
            cooldown=effective.cooldown_seconds,
            profile_ids=list(effective.instruction_profile_ids),
            effective_mode=effective.mode,
            effective_source=effective.source,
            trace=trace,
        )
    if effective.mode == "mention_only" and not ctx.is_mention:
        if trace is not None:
            trace.append(
                "mode_gate: mode=mention_only and is_mention=false → "
                "deny NO_MENTION_REQUIRED",
            )
        return _deny(
            policy,
            reason=PolicyDenialReason.NO_MENTION_REQUIRED,
            min_level=effective.min_level,
            cooldown=effective.cooldown_seconds,
            profile_ids=list(effective.instruction_profile_ids),
            effective_mode=effective.mode,
            effective_source=effective.source,
            trace=trace,
        )
    if trace is not None:
        trace.append("mode_gate: allowed")

    # ---- Role gate ----
    role_decision = _resolve_role(bundle["role"], ctx.user_role_ids)
    if role_decision["denied"]:
        if trace is not None:
            trace.append("role_gate: explicit deny → deny ROLE_DENIED")
        return _deny(
            policy,
            reason=PolicyDenialReason.ROLE_DENIED,
            min_level=effective.min_level,
            cooldown=effective.cooldown_seconds,
            profile_ids=list(effective.instruction_profile_ids),
            effective_mode=effective.mode,
            effective_source=effective.source,
            trace=trace,
        )

    gated_min_level = effective.min_level
    if role_decision["override_min_level"] is not None:
        candidate = int(role_decision["override_min_level"])
        gated_min_level = min(gated_min_level, candidate)
        if trace is not None:
            trace.append(
                f"role_gate: most-permissive override → min_level={gated_min_level}",
            )
    elif trace is not None:
        trace.append("role_gate: allowed")

    bypass_cooldown = role_decision["bypass_cooldown"]
    effective_cooldown = 0 if bypass_cooldown else effective.cooldown_seconds
    if trace is not None and bypass_cooldown:
        trace.append("role_gate: bypass_cooldown=true → effective_cooldown=0s")

    # ---- Level gate (XP / fresh-user allowance) ----
    used_fresh_allowance = False
    if ctx.user_level < gated_min_level:
        allowance = int(policy.get("fresh_user_mention_allowance", 0) or 0)
        # The allowance is a finite per-user budget, not a permanent
        # bypass: check what remains (a pure in-process read) so a fresh
        # user gets at most ``allowance`` replies before the level floor
        # applies again. The stage decrements it on a delivered reply.
        remaining = ai_permission_service.fresh_allowance_remaining(
            ctx.guild_id,
            ctx.user_id,
            allowance,
        )
        if ctx.is_fresh_user and ctx.is_mention and remaining > 0:
            used_fresh_allowance = True
            if trace is not None:
                trace.append(
                    f"level_gate: level={ctx.user_level} < min={gated_min_level} "
                    f"BUT fresh-user mention allowance ({remaining} left) → allowed",
                )
        else:
            if trace is not None:
                trace.append(
                    f"level_gate: level={ctx.user_level} < min={gated_min_level} → "
                    "deny BELOW_MIN_LEVEL",
                )
            return _deny(
                policy,
                reason=PolicyDenialReason.BELOW_MIN_LEVEL,
                min_level=gated_min_level,
                cooldown=effective_cooldown,
                profile_ids=list(effective.instruction_profile_ids),
                effective_mode=effective.mode,
                effective_source=effective.source,
                trace=trace,
            )
    elif trace is not None:
        trace.append(
            f"level_gate: level={ctx.user_level} ≥ min={gated_min_level} → allowed",
        )

    snapshot = _hash(
        {
            "g": policy.get("generation", 0),
            "min": gated_min_level,
            "cd": effective_cooldown,
            "profiles": list(effective.instruction_profile_ids),
            "allowed": True,
        },
    )
    if trace is not None:
        trace.append(
            f"final_decision: allowed min_level={gated_min_level} "
            f"cooldown={effective_cooldown}s",
        )
    return PolicyDecision(
        allowed=True,
        reason_code=PolicyDenialReason.NONE,
        effective_min_level=gated_min_level,
        effective_cooldown=effective_cooldown,
        effective_mode=effective.mode,
        effective_source=effective.source,
        instruction_profile_ids=effective.instruction_profile_ids,
        policy_snapshot_hash=snapshot,
        precedence_trace=tuple(trace or ()),
        used_fresh_allowance=used_fresh_allowance,
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
    effective_mode: str = "",
    effective_source: str = "",
    trace: list[str] | None = None,
) -> PolicyDecision:
    return PolicyDecision(
        allowed=False,
        reason_code=reason,
        effective_min_level=int(min_level),
        effective_cooldown=int(cooldown),
        effective_mode=effective_mode,
        effective_source=effective_source,
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
