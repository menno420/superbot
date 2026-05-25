"""AI readiness scan — operator-facing chain check.

Answers the question "why doesn't the AI reply in this guild / channel?"
by walking the full chain from provider configuration through resolver
decision and bot permissions. Returns a typed
:class:`AIReadinessReport` of :class:`AIReadinessFinding` records — a
shape that mirrors :class:`services.resource_health.ResourceHealthFinding`
so operators do not learn a new vocabulary.

**Non-mutating invariant.** This module is read orchestration only. It
must not mutate settings, append memory, write audit rows, invalidate
caches, or call AI providers. The pin-test
``tests/unit/services/test_ai_readonly_invariants.py`` enforces this by
AST scan. The resolver dry-run path is explicitly safe to call from
here because :func:`ai_natural_language_policy.resolve` is a pure read
even on the production path.

Status values:

* ``ok``      — the link is healthy.
* ``info``    — informational only; no operator action required.
* ``warn``    — best-effort issue; AI may degrade.
* ``error``   — blocker; AI will not reply for this guild/channel.
* ``skipped`` — the check could not run (e.g. no channel reference,
                no bot member in cache). Operator sees the reason.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import discord

from services import (
    ai_config_projection_service,
    ai_diagnostics_service,
    ai_natural_language_policy,
)

logger = logging.getLogger("bot.services.ai_readiness")


STATUS_OK = "ok"
STATUS_INFO = "info"
STATUS_WARN = "warn"
STATUS_ERROR = "error"
STATUS_SKIPPED = "skipped"

STATUS_CODES: frozenset[str] = frozenset(
    {STATUS_OK, STATUS_INFO, STATUS_WARN, STATUS_ERROR, STATUS_SKIPPED},
)


@dataclass(frozen=True)
class AIReadinessFinding:
    """One verdict for one readiness link.

    ``name`` is a stable check identifier (``provider_configured``,
    ``ai_enabled``, ``nl_enabled_or_scoped``, ``resolver_decision``,
    ``bot_permissions``, ``memory_status``, ``recent_denials``).
    ``status`` is one of the :data:`STATUS_CODES`. ``detail`` is the
    one-line human-readable explanation operators see.
    """

    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class AIReadinessReport:
    """The full readiness scan for a guild (optionally scoped to a channel)."""

    guild_id: int
    channel_id: int | None
    findings: tuple[AIReadinessFinding, ...]
    summary: str


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def scan(
    guild_id: int,
    *,
    bot: Any,
    channel: Any = None,
) -> AIReadinessReport:
    """Walk the readiness chain and return the report.

    ``bot`` is required so the scan can resolve the guild + bot-member
    for permission probes. ``channel`` is optional — when present the
    scan runs the resolver dry-run and the bot-permission probe against
    it; when absent those two links return ``status='skipped'`` with
    the reason in ``detail``.

    Findings are emitted in fixed order: provider → ai_enabled →
    nl_or_scoped → resolver → permissions → memory → recent_denials.
    """
    snapshot = await ai_config_projection_service.build_snapshot(
        guild_id,
        bot=bot,
    )

    channel_id = getattr(channel, "id", None) if channel is not None else None

    findings: list[AIReadinessFinding] = []
    findings.append(_check_provider_configured(snapshot.provider))
    findings.append(_check_ai_enabled(snapshot.policy))
    findings.append(_check_nl_or_scoped(snapshot.policy))
    findings.append(await _check_resolver_decision(guild_id, channel))
    findings.append(_check_bot_permissions(channel, snapshot.memory.scan_enabled))
    findings.append(_check_memory_status(snapshot.memory))
    findings.append(_check_recent_denials(snapshot.audit))

    summary = _summarise(findings)
    return AIReadinessReport(
        guild_id=guild_id,
        channel_id=channel_id,
        findings=tuple(findings),
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Individual link checks
# ---------------------------------------------------------------------------


def _check_provider_configured(
    provider: ai_config_projection_service.ProviderSnapshot,
) -> AIReadinessFinding:
    """Gateway has a default provider declared and is not in error state."""
    if not provider.default_provider:
        return AIReadinessFinding(
            name="provider_configured",
            status=STATUS_ERROR,
            detail="No default provider configured for the AI gateway.",
        )
    if provider.degraded:
        return AIReadinessFinding(
            name="provider_configured",
            status=STATUS_WARN,
            detail=(
                f"Gateway is degraded "
                f"(last error: {provider.last_error_type or 'unknown'}); "
                f"replies will fall back to the deterministic provider."
            ),
        )
    return AIReadinessFinding(
        name="provider_configured",
        status=STATUS_OK,
        detail=f"Default provider: {provider.default_provider}.",
    )


def _check_ai_enabled(
    policy: ai_config_projection_service.PolicySnapshot,
) -> AIReadinessFinding:
    """Master switch (``ai_guild_policy.enabled``) — hard gate."""
    if policy.enabled is None:
        return AIReadinessFinding(
            name="ai_enabled",
            status=STATUS_ERROR,
            detail=(
                "No typed AI policy row exists for this guild. "
                "Set `ai.enabled` via `!settings` to create one."
            ),
        )
    if not policy.enabled:
        return AIReadinessFinding(
            name="ai_enabled",
            status=STATUS_ERROR,
            detail="AI master switch is OFF (`ai_guild_policy.enabled=false`).",
        )
    return AIReadinessFinding(
        name="ai_enabled",
        status=STATUS_OK,
        detail="AI master switch is ON.",
    )


def _check_nl_or_scoped(
    policy: ai_config_projection_service.PolicySnapshot,
) -> AIReadinessFinding:
    """At least one of: NL baseline enabled, or a scoped override exists."""
    nl = bool(policy.natural_language_enabled)
    scoped = (
        policy.channel_override_count
        + policy.category_override_count
        + policy.role_override_count
    )
    if nl and scoped == 0:
        return AIReadinessFinding(
            name="nl_enabled_or_scoped",
            status=STATUS_OK,
            detail="Natural-language baseline is enabled (replies everywhere by default).",
        )
    if nl and scoped > 0:
        return AIReadinessFinding(
            name="nl_enabled_or_scoped",
            status=STATUS_OK,
            detail=(
                f"Natural-language baseline ON; "
                f"{scoped} scoped override(s) refine per-channel/category/role."
            ),
        )
    if scoped > 0:
        return AIReadinessFinding(
            name="nl_enabled_or_scoped",
            status=STATUS_OK,
            detail=(
                f"Natural-language baseline OFF; "
                f"{scoped} scoped override(s) enable AI in specific scopes."
            ),
        )
    return AIReadinessFinding(
        name="nl_enabled_or_scoped",
        status=STATUS_WARN,
        detail=(
            "Natural-language baseline is OFF and no scoped overrides exist. "
            "AI will not reply to messages unless mentioned in a scope that "
            "explicitly allows it."
        ),
    )


async def _check_resolver_decision(
    guild_id: int,
    channel: Any,
) -> AIReadinessFinding:
    """Dry-run the resolver against ``channel``; reports the effective outcome."""
    if channel is None:
        return AIReadinessFinding(
            name="resolver_decision",
            status=STATUS_SKIPPED,
            detail="No channel reference — pass one to dry-run the resolver.",
        )
    channel_id = getattr(channel, "id", None)
    if channel_id is None:
        return AIReadinessFinding(
            name="resolver_decision",
            status=STATUS_SKIPPED,
            detail="Channel reference lacks an id.",
        )
    category = getattr(channel, "category", None)
    category_id = getattr(category, "id", None) if category is not None else None
    bot_member = getattr(getattr(channel, "guild", None), "me", None)
    bot_user_id = getattr(bot_member, "id", None) if bot_member is not None else None

    ctx = ai_natural_language_policy.MessageContext(
        guild_id=guild_id,
        channel_id=int(channel_id),
        category_id=int(category_id) if category_id is not None else None,
        # The dry-run uses the bot itself as a stand-in for the user
        # because readiness is about "is the channel even reachable?"
        # not about a specific member. Level + role probes still run
        # because the policy gate would deny on them too.
        user_id=int(bot_user_id) if bot_user_id is not None else 0,
        user_level=100,
        user_role_ids=(),
        is_mention=False,
        is_fresh_user=False,
    )
    try:
        decision = await ai_natural_language_policy.resolve(ctx, dry_run=True)
    except Exception as exc:
        logger.exception(
            "ai_readiness: resolver dry-run failed for guild=%d channel=%s",
            guild_id,
            channel_id,
        )
        return AIReadinessFinding(
            name="resolver_decision",
            status=STATUS_WARN,
            detail=f"Resolver dry-run failed: {type(exc).__name__}.",
        )
    if decision.allowed:
        return AIReadinessFinding(
            name="resolver_decision",
            status=STATUS_OK,
            detail=(
                f"Channel resolves to {decision.effective_mode or 'allow'} "
                f"(source: {decision.effective_source or 'guild'})."
            ),
        )
    reason = getattr(decision.reason_code, "name", str(decision.reason_code))
    return AIReadinessFinding(
        name="resolver_decision",
        status=STATUS_WARN,
        detail=(
            f"Channel would deny with reason {reason} "
            f"(source: {decision.effective_source or 'guild'})."
        ),
    )


def _check_bot_permissions(channel: Any, scan_enabled: bool) -> AIReadinessFinding:
    """Bot must view + send messages in the channel; read_history iff scan."""
    if channel is None:
        return AIReadinessFinding(
            name="bot_permissions",
            status=STATUS_SKIPPED,
            detail="No channel reference — pass one to probe send permissions.",
        )
    guild = getattr(channel, "guild", None)
    bot_member = getattr(guild, "me", None) if guild is not None else None
    if bot_member is None:
        return AIReadinessFinding(
            name="bot_permissions",
            status=STATUS_SKIPPED,
            detail="Bot member is not in the guild cache; cannot probe permissions.",
        )
    if not isinstance(
        channel,
        (
            discord.TextChannel,
            discord.VoiceChannel,
            discord.StageChannel,
            discord.Thread,
        ),
    ):
        return AIReadinessFinding(
            name="bot_permissions",
            status=STATUS_SKIPPED,
            detail=(
                f"Channel reference is a {type(channel).__name__}; "
                "AI replies only fire in text-capable channels."
            ),
        )
    try:
        perms = channel.permissions_for(bot_member)
    except Exception as exc:
        return AIReadinessFinding(
            name="bot_permissions",
            status=STATUS_WARN,
            detail=f"Permission probe failed: {type(exc).__name__}.",
        )
    missing: list[str] = []
    if not perms.view_channel:
        missing.append("view_channel")
    if not perms.send_messages:
        missing.append("send_messages")
    if scan_enabled and not perms.read_message_history:
        missing.append("read_message_history")
    if missing:
        return AIReadinessFinding(
            name="bot_permissions",
            status=STATUS_ERROR,
            detail=(f"Bot lacks permissions in this channel: {', '.join(missing)}."),
        )
    return AIReadinessFinding(
        name="bot_permissions",
        status=STATUS_OK,
        detail="Bot can view, send, and (if scan enabled) read history.",
    )


def _check_memory_status(
    memory: ai_config_projection_service.MemorySnapshot,
) -> AIReadinessFinding:
    """Informational summary of memory mode + cache occupancy."""
    if memory.window_minutes <= 0:
        mode = f"Minimal — {memory.min_floor_turns} turn floor"
    else:
        mode = f"{memory.window_minutes} min window"
    scan = "scan on" if memory.scan_enabled else "scan off"
    return AIReadinessFinding(
        name="memory_status",
        status=STATUS_INFO,
        detail=(
            f"Memory: {mode}, {scan}. "
            f"Cache: {memory.cached_channel_count} channel(s), "
            f"{memory.cached_total_turns} turn(s)."
        ),
    )


def _check_recent_denials(
    audit: ai_config_projection_service.AuditSnapshot,
) -> AIReadinessFinding:
    """Count recent denied/degraded/errored audit rows."""
    if audit.recent_total == 0:
        return AIReadinessFinding(
            name="recent_denials",
            status=STATUS_INFO,
            detail="No decisions audited yet for this guild.",
        )
    bad = (
        audit.by_decision.get("denied", 0)
        + audit.by_decision.get("degraded", 0)
        + audit.by_decision.get("errored", 0)
    )
    if bad == 0:
        return AIReadinessFinding(
            name="recent_denials",
            status=STATUS_OK,
            detail=(f"No denials/errors in the last {audit.recent_total} decisions."),
        )
    return AIReadinessFinding(
        name="recent_denials",
        status=STATUS_WARN,
        detail=(
            f"{bad} of last {audit.recent_total} decisions denied/degraded/errored. "
            "Run `!ai why-no-response` for details."
        ),
    )


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def _summarise(findings: list[AIReadinessFinding]) -> str:
    """One-line health string for the AIConfigSnapshot.readiness_summary."""
    if any(f.status == STATUS_ERROR for f in findings):
        first_error = next(f for f in findings if f.status == STATUS_ERROR)
        return f"Not ready: {first_error.detail}"
    if any(f.status == STATUS_WARN for f in findings):
        warn_count = sum(1 for f in findings if f.status == STATUS_WARN)
        first_warn = next(f for f in findings if f.status == STATUS_WARN)
        if warn_count == 1:
            return f"Ready with caveat: {first_warn.detail}"
        return f"Ready with {warn_count} caveats; first: {first_warn.detail}"
    return "Ready"


# Re-export the diagnostics snapshot helper for callers that just want
# the provider/health view without running the full chain. This keeps
# the readiness scan as the canonical entry point.
def diagnostics() -> dict[str, object]:
    """Shortcut: gateway diagnostics snapshot (no provider call)."""
    return ai_diagnostics_service.snapshot_for_cog()


__all__ = [
    "AIReadinessFinding",
    "AIReadinessReport",
    "STATUS_CODES",
    "STATUS_ERROR",
    "STATUS_INFO",
    "STATUS_OK",
    "STATUS_SKIPPED",
    "STATUS_WARN",
    "diagnostics",
    "scan",
]
