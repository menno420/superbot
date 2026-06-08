"""Server-management hub status — read-only health-badge composer (PR14).

The unified Server Management Hub (``!servermanagement`` / ``/server-management``)
is a **navigation** surface: one button per specialised manager (moderation,
channels, roles, cleanup, setup) plus a compact, read-only health summary so an
operator sees *what needs attention* before clicking in.

This module owns only the **badge composition** — it does **not** mutate, render
Discord components, or re-implement any detector.  It *composes* the existing
read-only signals:

* moderation capability — :func:`utils.moderation_feasibility.evaluate_moderation_readiness`
* role-management capability — :func:`utils.role_feasibility.manageable_roles`
* channel-management capability — ``guild.me.guild_permissions.manage_channels``
* per-guild config health — :func:`services.setup_diagnostics.collect_setup_diagnostics`
* setup completeness — :func:`services.setup_readiness.collect`

It lives in ``services/`` (not in the view) for the same reason
:mod:`services.setup_diagnostics` does: the model is UI-agnostic, so the future
web companion (owner intent Q-0002 — Discord-first, keep read models reusable)
can render the same :class:`HubStatus` without change.

**Fail-safe by contract.** Every badge is best-effort: a detector that raises is
logged and degrades that badge to *unknown* (``❓``) — one broken signal can
never blank the hub or break its render.  ``collect_hub_status`` therefore never
raises.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    from services.setup_diagnostics import SetupDiagnosticsReport

logger = logging.getLogger("bot.services.server_management_hub")

# ---------------------------------------------------------------------------
# Glyphs — the at-a-glance status vocabulary (one column per manager).
# ---------------------------------------------------------------------------

GLYPH_HEALTHY = "🟢"  # works / nothing needs attention
GLYPH_ATTENTION = "🟡"  # usable but something is incomplete / degraded
GLYPH_BLOCKED = "⛔"  # the bot cannot act here until a Discord-side fix
GLYPH_UNKNOWN = "❓"  # a detector failed — surfaced honestly, not hidden

# Manager keys — stable identifiers shared with the view's button custom_ids.
MOD = "moderation"
CHANNELS = "channels"
ROLES = "roles"
CLEANUP = "cleanup"
SETUP = "setup"

# Setup-completeness threshold above which setup reads as healthy.
_SETUP_HEALTHY_PCT = 80


@dataclass(frozen=True)
class ManagerBadge:
    """A read-only health summary for one manager in the hub.

    ``key`` matches the manager's button custom_id suffix; ``emoji`` + ``label``
    are display metadata; ``glyph`` is one of the ``GLYPH_*`` constants and
    ``summary`` is the one-line operator-facing explanation.
    """

    key: str
    emoji: str
    label: str
    glyph: str
    summary: str


@dataclass(frozen=True)
class HubStatus:
    """Composed, render-ready status snapshot for one guild's hub."""

    guild_id: int
    badges: tuple[ManagerBadge, ...]
    overall_glyph: str
    overall_summary: str


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def collect_hub_status(guild: discord.Guild) -> HubStatus:
    """Compose every manager badge + an overall config-health line for *guild*.

    Read-only and **never raises**: each badge is built fail-safe, and the
    cross-cutting config-health collector (:mod:`services.setup_diagnostics`)
    is itself fail-safe.  The cost is paid only on open / explicit refresh —
    the view caches nothing across button clicks.
    """
    # One fail-safe diagnostics pass feeds both the cleanup badge and the
    # overall line, so we don't fan out to the detectors twice.
    report = await _safe_collect_diagnostics(guild)
    setup_pct = await _safe_setup_percentage(guild)

    badges = (
        _moderation_badge(guild),
        _channels_badge(guild),
        _roles_badge(guild),
        _cleanup_badge(report),
        _setup_badge(setup_pct, report),
    )
    overall_glyph, overall_summary = _overall(report)
    return HubStatus(
        guild_id=guild.id,
        badges=badges,
        overall_glyph=overall_glyph,
        overall_summary=overall_summary,
    )


# ---------------------------------------------------------------------------
# Per-manager badge builders (each fail-safe — never raises)
# ---------------------------------------------------------------------------


def _moderation_badge(guild: discord.Guild) -> ManagerBadge:
    """Can the bot ban / kick / timeout in this guild?"""
    try:
        from utils.moderation_feasibility import evaluate_moderation_readiness

        readiness = evaluate_moderation_readiness(guild)
        if readiness.fully_capable:
            glyph, summary = GLYPH_HEALTHY, "Can ban, kick and timeout members"
        else:
            missing = readiness.missing_permissions()
            if missing:
                glyph, summary = GLYPH_ATTENTION, f"Missing: {', '.join(missing)}"
            else:
                # All perms present but the bot's top role is at the bottom.
                glyph = GLYPH_ATTENTION
                summary = "Bot's role is at the bottom — actions may be limited"
    except Exception:
        logger.exception("server_management_hub: moderation badge failed")
        glyph, summary = GLYPH_UNKNOWN, "Readiness check unavailable"
    return ManagerBadge(MOD, "🛡️", "Moderation", glyph, summary)


def _channels_badge(guild: discord.Guild) -> ManagerBadge:
    """Does the bot hold Manage Channels?"""
    try:
        me = guild.me
        can_manage = bool(me is not None and me.guild_permissions.manage_channels)
        if can_manage:
            glyph, summary = (
                GLYPH_HEALTHY,
                "Can create, rename, move and delete channels",
            )
        else:
            glyph, summary = GLYPH_BLOCKED, "Missing Manage Channels permission"
    except Exception:
        logger.exception("server_management_hub: channels badge failed")
        glyph, summary = GLYPH_UNKNOWN, "Permission check unavailable"
    return ManagerBadge(CHANNELS, "📺", "Channels", glyph, summary)


def _roles_badge(guild: discord.Guild) -> ManagerBadge:
    """Can the bot manage roles, and how many of them?"""
    try:
        from utils.role_feasibility import manageable_roles

        me = guild.me
        if me is None or not me.guild_permissions.manage_roles:
            glyph, summary = GLYPH_BLOCKED, "Missing Manage Roles permission"
        else:
            manageable, _excluded = manageable_roles(guild.roles, bot_member=me)
            total = len(guild.roles)
            if manageable:
                glyph = GLYPH_HEALTHY
                summary = f"Can manage {len(manageable)} of {total} roles"
            else:
                glyph = GLYPH_ATTENTION
                summary = "No roles are below the bot — move its role higher"
    except Exception:
        logger.exception("server_management_hub: roles badge failed")
        glyph, summary = GLYPH_UNKNOWN, "Role feasibility check unavailable"
    return ManagerBadge(ROLES, "🎭", "Roles", glyph, summary)


def _cleanup_badge(report: SetupDiagnosticsReport | None) -> ManagerBadge:
    """Derive cleanup health from the (fail-safe) diagnostics report.

    Tolerant by design: we filter findings whose ``subsystem`` names cleanup
    rather than asserting an exact taxonomy string, so a future rename in the
    detector degrades the *glyph* (never correctness — this is an advisory
    badge).
    """
    try:
        if report is None:
            glyph, summary = GLYPH_UNKNOWN, "Diagnostics unavailable"
        else:
            cleanup_findings = [
                f
                for f in report.findings
                if "cleanup" in (getattr(f, "subsystem", "") or "").lower()
            ]
            glyph, summary = _worst_glyph(
                cleanup_findings,
                healthy_summary="No cleanup-policy issues detected",
            )
    except Exception:
        logger.exception("server_management_hub: cleanup badge failed")
        glyph, summary = GLYPH_UNKNOWN, "Diagnostics unavailable"
    return ManagerBadge(CLEANUP, "🧹", "Cleanup", glyph, summary)


def _setup_badge(
    percentage: int | None,
    report: SetupDiagnosticsReport | None,
) -> ManagerBadge:
    """How complete is setup, and does anything block it?"""
    try:
        # A blocker outranks a completeness percentage.
        if report is not None and report.counts.get("blocker", 0) > 0:
            return ManagerBadge(
                SETUP,
                "🧩",
                "Setup",
                GLYPH_BLOCKED,
                "Setup has blocking issues",
            )
        if percentage is None:
            glyph, summary = GLYPH_UNKNOWN, "Readiness unavailable"
        elif percentage >= _SETUP_HEALTHY_PCT:
            glyph, summary = GLYPH_HEALTHY, f"{percentage}% configured"
        elif percentage > 0:
            glyph, summary = GLYPH_ATTENTION, f"{percentage}% configured — more to do"
        else:
            glyph, summary = GLYPH_ATTENTION, "Not configured yet — run setup"
    except Exception:
        logger.exception("server_management_hub: setup badge failed")
        glyph, summary = GLYPH_UNKNOWN, "Readiness unavailable"
    return ManagerBadge(SETUP, "🧩", "Setup", glyph, summary)


# ---------------------------------------------------------------------------
# Overall config-health line
# ---------------------------------------------------------------------------


def _overall(report: SetupDiagnosticsReport | None) -> tuple[str, str]:
    """Cross-cutting "what needs attention?" summary from the diagnostics report."""
    if report is None:
        return GLYPH_UNKNOWN, "Configuration health check unavailable"
    try:
        counts = report.counts
        blockers = counts.get("blocker", 0)
        warnings = counts.get("warning", 0)
        advisories = counts.get("advisory", 0)
        if report.is_healthy:
            return GLYPH_HEALTHY, "No configuration issues need attention"
        parts: list[str] = []
        if blockers:
            parts.append(f"{blockers} blocker{'s' if blockers != 1 else ''}")
        if warnings:
            parts.append(f"{warnings} warning{'s' if warnings != 1 else ''}")
        if advisories:
            parts.append(f"{advisories} advisor{'ies' if advisories != 1 else 'y'}")
        glyph = GLYPH_BLOCKED if blockers else GLYPH_ATTENTION
        return glyph, ", ".join(parts) if parts else "Needs attention"
    except Exception:
        logger.exception("server_management_hub: overall summary failed")
        return GLYPH_UNKNOWN, "Configuration health check unavailable"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _safe_collect_diagnostics(
    guild: discord.Guild,
) -> SetupDiagnosticsReport | None:
    """Run the diagnostics collector, returning ``None`` if it is unavailable."""
    try:
        from services import setup_diagnostics

        return await setup_diagnostics.collect_setup_diagnostics(guild)
    except Exception:
        logger.exception("server_management_hub: setup_diagnostics failed")
        return None


async def _safe_setup_percentage(guild: discord.Guild) -> int | None:
    """Return the setup-readiness percentage, or ``None`` if unavailable.

    Calls ``collect(guild_id)`` **without** the ``guild`` kwarg on purpose: the
    health view is owned by the diagnostics report above, and passing ``guild``
    would re-run ``resource_health.inspect`` a second time.
    """
    try:
        from services import setup_readiness

        report = await setup_readiness.collect(guild.id)
        return int(report.percentage)
    except Exception:
        logger.exception("server_management_hub: setup_readiness failed")
        return None


def _worst_glyph(findings: list, *, healthy_summary: str) -> tuple[str, str]:
    """Map the worst severity among *findings* to a (glyph, summary) pair."""
    severities = {getattr(f, "severity", "") for f in findings}
    if "blocker" in severities:
        return GLYPH_BLOCKED, _count_summary(findings)
    if severities & {"warning", "advisory"}:
        return GLYPH_ATTENTION, _count_summary(findings)
    return GLYPH_HEALTHY, healthy_summary


def _count_summary(findings: list) -> str:
    n = len(findings)
    return f"{n} issue{'s' if n != 1 else ''} need{'s' if n == 1 else ''} attention"
