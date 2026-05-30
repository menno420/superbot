"""Embed builders for the ``!platform <subcommand>`` admin surface.

Extracted from ``cogs/diagnostic_cog.py`` to keep the cog under the
800-LOC fail threshold enforced by
``tests/unit/invariants/test_cog_size.py``.  Each builder is a pure
async (or sync) function that fetches its data (via
``services.diagnostics_service`` and/or ``utils.db.*``) and returns
a single :class:`discord.Embed` ready to send.  The cog methods
become thin wrappers that delegate here, and the
``_PlatformHubView`` panel reuses the same builders so its select
callbacks produce the same embed as the typed command.
"""

from __future__ import annotations

import datetime

import discord
from discord.ext import commands

from services.platform_consistency import (
    ConsistencyReport,
    SectionResult,
    SectionStatus,
)


async def build_resources_embed(guild: discord.Guild | None) -> discord.Embed:
    """Build the embed for ``!platform resources`` (Phase 2a)."""
    from services import diagnostics_service
    from utils.db import resource_cache

    snap = diagnostics_service.snapshot("resources")
    embed = discord.Embed(
        title="🧱 Resources",
        description=(
            f"package: `{snap['package']}`  ·  "
            f"kinds: {', '.join(f'`{k}`' for k in snap['kinds'])}"
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Submodules",
        value=", ".join(f"`{m}`" for m in snap["submodules"]),
        inline=False,
    )
    if guild is not None:
        try:
            histogram = await resource_cache.count_by_status(guild.id)
        except Exception as exc:  # noqa: BLE001 — DB outage shouldn't crash command
            embed.add_field(
                name="Cached status",
                value=f"❌ {exc}",
                inline=False,
            )
        else:
            if histogram:
                lines = [
                    f"`{status}` — {count}"
                    for status, count in sorted(histogram.items())
                ]
                embed.add_field(
                    name=f"Cached status (guild {guild.id})",
                    value="\n".join(lines),
                    inline=False,
                )
            else:
                embed.add_field(
                    name=f"Cached status (guild {guild.id})",
                    value="*(no cached rows)*",
                    inline=False,
                )
    return embed


async def build_bindings_embed(guild: discord.Guild | None) -> discord.Embed:
    """Build the embed for ``!platform bindings`` (Phase 2b)."""
    from services import diagnostics_service
    from utils.db import bindings as bindings_db

    snap = diagnostics_service.snapshot("bindings")
    embed = discord.Embed(
        title="🔗 Subsystem bindings",
        description=f"kinds: {', '.join(f'`{k}`' for k in snap['kinds'])}",
        color=discord.Color.blurple(),
    )
    dispatch_lines = [
        f"`{kind}` → `{validator}`"
        for kind, validator in sorted(snap["validator_dispatch"].items())
    ]
    embed.add_field(
        name="Validator dispatch",
        value="\n".join(dispatch_lines),
        inline=False,
    )
    if guild is not None:
        try:
            by_status = await bindings_db.count_by_status(guild.id)
            by_sub = await bindings_db.count_by_subsystem(guild.id)
        except Exception as exc:  # noqa: BLE001 — DB outage shouldn't crash command
            embed.add_field(
                name="Per-guild counts",
                value=f"❌ DB query failed: {exc}",
                inline=False,
            )
            return embed

        status_lines = (
            "\n".join(
                f"`{status}` — {count}" for status, count in sorted(by_status.items())
            )
            or "*(no bindings)*"
        )
        embed.add_field(
            name=f"Status (guild {guild.id})",
            value=status_lines,
            inline=False,
        )
        sub_lines = (
            "\n".join(f"`{sub}` — {count}" for sub, count in sorted(by_sub.items()))
            or "*(no bindings)*"
        )
        embed.add_field(
            name=f"By subsystem (guild {guild.id})",
            value=sub_lines,
            inline=False,
        )
    return embed


# ---------------------------------------------------------------------------
# Consistency embed — Phase 2 PR-10
# ---------------------------------------------------------------------------

_STATUS_COLOR: dict[SectionStatus, discord.Color] = {
    SectionStatus.CLEAN: discord.Color.green(),
    SectionStatus.WARNING: discord.Color.gold(),
    SectionStatus.FATAL: discord.Color.red(),
    SectionStatus.SKIPPED: discord.Color.light_grey(),
}

_STATUS_ICON: dict[SectionStatus, str] = {
    SectionStatus.CLEAN: "🟢",
    SectionStatus.WARNING: "🟡",
    SectionStatus.FATAL: "🔴",
    SectionStatus.SKIPPED: "⚪",
}

# Informational marker prefixed to the Setup readiness field value so
# operators do not read its WARNING as a runtime degradation.
_INFORMATIONAL_PREFIX = "ℹ️ Roadmap/informational — not a runtime health failure.\n"

# Soft cap for total embed size; leaves headroom under Discord's 6000.
_EMBED_SOFT_CAP = 5800
# Per-field value cap; leaves headroom under Discord's 1024.
_FIELD_VALUE_CAP = 1000
# Hard cap on field count (Discord's limit is 25; reserve one for
# truncation notes).
_FIELD_HARD_CAP = 24


def _format_field_value(section: SectionResult) -> str:
    lines: list[str] = []
    if section.informational:
        lines.append(_INFORMATIONAL_PREFIX.rstrip())
    lines.append(section.summary)
    for bullet in section.details[:3]:
        lines.append(f"• {bullet}")
    for action in section.suggested_actions[:2]:
        lines.append(f"→ {action}")
    value = "\n".join(lines)
    if len(value) > _FIELD_VALUE_CAP:
        value = value[: _FIELD_VALUE_CAP - 1] + "…"
    return value


def _estimated_embed_size(embed: discord.Embed) -> int:
    size = len(embed.title or "") + len(embed.description or "")
    if embed.footer and embed.footer.text:
        size += len(embed.footer.text)
    for field in embed.fields:
        size += len(field.name or "") + len(field.value or "")
    return size


def build_consistency_embed(report: ConsistencyReport) -> discord.Embed:
    """Render a ConsistencyReport as a single Discord embed.

    Bounds the rendered size to Discord's limits: per-field value
    capped at ~1000 chars with a truncation marker; total embed size
    bounded by collapsing the longest field, then dropping trailing
    SKIPPED/CLEAN fields and appending a `_truncated` note.  Hard cap
    of 24 fields.
    """
    overall = report.overall_status
    counts = {s: 0 for s in SectionStatus}
    informational_warnings = 0
    runtime_warnings = 0
    for section in report.sections:
        counts[section.status] = counts.get(section.status, 0) + 1
        if section.status == SectionStatus.WARNING:
            if section.informational:
                informational_warnings += 1
            else:
                runtime_warnings += 1

    generated = report.generated_at.strftime("%Y-%m-%d %H:%M:%SZ")
    embed = discord.Embed(
        title=f"🛡 Platform consistency · {overall.value.upper()}",
        description=(
            f"{counts[SectionStatus.CLEAN]} clean · "
            f"{counts[SectionStatus.WARNING]} warning · "
            f"{counts[SectionStatus.FATAL]} fatal · "
            f"{counts[SectionStatus.SKIPPED]} skipped · "
            f"generated {generated}"
        ),
        color=_STATUS_COLOR.get(overall, discord.Color.light_grey()),
    )

    sections_for_embed = list(report.sections[:_FIELD_HARD_CAP])
    for section in sections_for_embed:
        icon = _STATUS_ICON.get(section.status, "•")
        embed.add_field(
            name=f"{icon} {section.name}",
            value=_format_field_value(section),
            inline=False,
        )

    # Bounded-size guard: collapse longest field value to summary line
    # if the embed exceeds the soft cap.
    while _estimated_embed_size(embed) > _EMBED_SOFT_CAP and embed.fields:
        longest_idx = max(
            range(len(embed.fields)),
            key=lambda i: len(embed.fields[i].value or ""),
        )
        section = sections_for_embed[longest_idx]
        collapsed = section.summary
        if section.informational:
            collapsed = _INFORMATIONAL_PREFIX.rstrip() + "\n" + collapsed
        if len(collapsed) > _FIELD_VALUE_CAP:
            collapsed = collapsed[: _FIELD_VALUE_CAP - 1] + "…"
        if collapsed == embed.fields[longest_idx].value:
            break
        embed.set_field_at(
            longest_idx,
            name=embed.fields[longest_idx].name,
            value=collapsed,
            inline=False,
        )

    # Still over? Drop trailing SKIPPED/CLEAN runtime fields one by one.
    dropped = 0
    while _estimated_embed_size(embed) > _EMBED_SOFT_CAP and embed.fields:
        idx_to_drop: int | None = None
        for i in range(len(embed.fields) - 1, -1, -1):
            section = sections_for_embed[i]
            if not section.informational and section.status in (
                SectionStatus.CLEAN,
                SectionStatus.SKIPPED,
            ):
                idx_to_drop = i
                break
        if idx_to_drop is None:
            break
        embed.remove_field(idx_to_drop)
        sections_for_embed.pop(idx_to_drop)
        dropped += 1
    if dropped:
        embed.add_field(
            name="… truncated",
            value=f"{dropped} section(s) omitted to stay under embed limits.",
            inline=False,
        )

    embed.set_footer(
        text=(
            f"{runtime_warnings} runtime warning · "
            f"{informational_warnings} informational"
        ),
    )
    return embed


def build_schemas_embed() -> discord.Embed:
    """Build the embed for ``!platform schemas`` (Phase 1a)."""
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("schemas")
    embed = discord.Embed(
        title="📐 Subsystem schemas",
        description=(
            f"{snap['registered']} registered  ·  "
            f"bindings={snap['bindings_total']}  ·  "
            f"settings={snap['settings_total']}  ·  "
            f"resources={snap['resources_total']}"
        ),
        color=discord.Color.blurple(),
    )
    by_sub = snap.get("by_subsystem", {})
    if by_sub:
        lines = [
            f"`{name}` — b={info['bindings']} s={info['settings']} "
            f"r={info['resources']} v={info['version']}"
            for name, info in sorted(by_sub.items())
        ]
        embed.add_field(
            name="By subsystem",
            value="\n".join(lines)[:1024],
            inline=False,
        )
    else:
        embed.add_field(name="By subsystem", value="*(none)*", inline=False)
    return embed


def build_settings_registry_embed() -> discord.Embed:
    """Build the embed for ``!platform settings-registry`` (S1)."""
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("settings_registry")
    if snap.get("status") == "not_built":
        return discord.Embed(
            title="🗂️ Settings registry",
            description="*(not built — call settings_registry.build_registry())*",
            color=discord.Color.greyple(),
        )
    embed = discord.Embed(
        title="🗂️ Settings registry",
        description=(
            f"v{snap['version']}  ·  {snap['entry_count']} entries  ·  "
            f"{snap['subsystems']} subsystems  ·  "
            f"findings={snap['findings_total']}"
        ),
        color=discord.Color.blurple(),
    )
    by_sub = snap.get("by_subsystem", {})
    if by_sub:
        lines = [
            f"`{name}` — {count} setting(s)" for name, count in sorted(by_sub.items())
        ]
        embed.add_field(
            name="By subsystem",
            value="\n".join(lines)[:1024],
            inline=False,
        )
    else:
        embed.add_field(name="By subsystem", value="*(none)*", inline=False)
    findings = snap.get("findings", {})
    if findings and snap["findings_total"]:
        finding_lines = [
            f"`{key}`: {count}" for key, count in sorted(findings.items()) if count
        ]
        if finding_lines:
            embed.add_field(
                name="Findings",
                value="\n".join(finding_lines)[:1024],
                inline=False,
            )
    return embed


def build_customization_embed() -> discord.Embed:
    """Build the embed for ``!platform customization`` (S2)."""
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("customization_catalogue")
    if snap.get("status") == "not_built":
        return discord.Embed(
            title="🧭 Customization catalogue",
            description=(
                "*(not built — call customization_catalogue.build_catalogue(bot))*"
            ),
            color=discord.Color.greyple(),
        )
    embed = discord.Embed(
        title="🧭 Customization catalogue",
        description=(
            f"v{snap['version']}  ·  {snap['subsystem_count']} subsystems  ·  "
            f"{snap['panel_count']} panels  ·  "
            f"schemas={snap['subsystems_with_schema']}  ·  "
            f"help_hooks={snap['subsystems_with_help_hook']}  ·  "
            f"findings={snap['findings_total']}"
        ),
        color=discord.Color.blurple(),
    )
    panels_by_source = snap.get("panels_by_source") or {}
    if panels_by_source:
        lines = [
            f"`{src}` — {count}" for src, count in sorted(panels_by_source.items())
        ]
        embed.add_field(
            name="Panels by detection source",
            value="\n".join(lines)[:1024],
            inline=False,
        )
    findings = snap.get("findings") or {}
    if findings and snap.get("findings_total"):
        finding_lines = [
            f"`{key}`: {count}" for key, count in sorted(findings.items()) if count
        ]
        if finding_lines:
            embed.add_field(
                name="Findings",
                value="\n".join(finding_lines)[:1024],
                inline=False,
            )
    return embed


def build_provisioning_embed() -> discord.Embed:
    """Build the embed for ``!platform provisioning`` (S2.5)."""
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("resource_provisioning_catalogue")
    if snap.get("status") == "not_built":
        return discord.Embed(
            title="🧰 Resource provisioning catalogue",
            description=(
                "*(not built — call resource_provisioning_catalogue."
                "build_provisioning_catalogue())*"
            ),
            color=discord.Color.greyple(),
        )
    embed = discord.Embed(
        title="🧰 Resource provisioning catalogue",
        description=(
            f"v{snap['version']}  ·  {snap['option_count']} option(s)  ·  "
            f"{snap['subsystem_count']} subsystem(s)  ·  "
            f"findings={snap['findings_total']}"
        ),
        color=discord.Color.blurple(),
    )
    by_priority = snap.get("by_priority") or {}
    if by_priority:
        priority_order = {"required": 0, "recommended": 1, "optional": 2}
        lines = [
            f"`{p}` — {count}"
            for p, count in sorted(
                by_priority.items(),
                key=lambda kv: priority_order.get(kv[0], 99),
            )
        ]
        embed.add_field(
            name="By priority",
            value="\n".join(lines)[:1024],
            inline=True,
        )
    by_kind = snap.get("by_kind") or {}
    if by_kind:
        lines = [f"`{k}` — {count}" for k, count in sorted(by_kind.items())]
        embed.add_field(
            name="By kind",
            value="\n".join(lines)[:1024],
            inline=True,
        )
    by_subsystem = snap.get("by_subsystem") or {}
    if by_subsystem:
        lines = [
            f"`{name}` — {count} option(s)"
            for name, count in sorted(by_subsystem.items())
        ]
        embed.add_field(
            name="By subsystem",
            value="\n".join(lines)[:1024],
            inline=False,
        )
    findings = snap.get("findings") or {}
    if findings and snap.get("findings_total"):
        finding_lines = [
            f"`{key}`: {count}" for key, count in sorted(findings.items()) if count
        ]
        if finding_lines:
            embed.add_field(
                name="Findings",
                value="\n".join(finding_lines)[:1024],
                inline=False,
            )
    return embed


# ---------------------------------------------------------------------------
# Runtime / status group
# ---------------------------------------------------------------------------


def build_status_embed(bot: commands.Bot) -> discord.Embed:
    """Build the embed for ``!platform status``."""
    from core.runtime import tasks as runtime_tasks

    uptime_obj = getattr(bot, "uptime", None)
    uptime_s = (
        str(datetime.datetime.now(tz=datetime.timezone.utc) - uptime_obj)
        if uptime_obj
        else "n/a"
    )
    embed = discord.Embed(
        title="🛠 Platform status",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Uptime", value=uptime_s, inline=True)
    embed.add_field(name="Guilds", value=str(len(bot.guilds)), inline=True)
    embed.add_field(name="Cogs loaded", value=str(len(bot.cogs)), inline=True)
    embed.add_field(
        name="Managed tasks",
        value=str(runtime_tasks.count()),
        inline=True,
    )
    try:
        from services.governance_service import _FAILED_SUBSYSTEMS

        failed = ", ".join(sorted(_FAILED_SUBSYSTEMS)) or "none"
    except Exception:
        failed = "?"
    embed.add_field(name="Failed subsystems", value=failed, inline=False)
    return embed


_EMBED_FIELD_CAP = 24  # Discord hard limit is 25; reserve 1 for overflow note.


def build_runtime_embed() -> discord.Embed:
    """Build the embed for ``!platform runtime`` (snapshot_all roll-up)."""
    from services import diagnostics_service

    snap = diagnostics_service.snapshot_all()
    embed = discord.Embed(
        title="🛰 Runtime snapshot",
        description=f"{len(snap)} provider(s) registered.",
        color=discord.Color.blurple(),
    )
    names = sorted(snap)
    for name in names[:_EMBED_FIELD_CAP]:
        embed.add_field(
            name=name,
            value=_fmt_snapshot_value(snap[name]),
            inline=False,
        )
    if len(names) > _EMBED_FIELD_CAP:
        overflow = len(names) - _EMBED_FIELD_CAP
        embed.add_field(
            name=f"… {overflow} more provider(s) not shown",
            value="Use `!platform runtime` with a name filter to view them.",
            inline=False,
        )
    return embed


_LIFECYCLE_PHASE_COLORS: dict[str, discord.Color] = {
    "STARTING": discord.Color.gold(),
    "RUNNING": discord.Color.green(),
    "DRAINING": discord.Color.gold(),
    "SHUTTING_DOWN": discord.Color.dark_red(),
    "RESTARTING": discord.Color.dark_red(),
    "STOPPED": discord.Color.dark_red(),
    "FAILED_STARTUP": discord.Color.dark_red(),
}


def _fmt_lifecycle_event_metadata(event: dict[str, object]) -> str:
    """Render the close_executing / close_completed / close_timeout
    metadata payload as a compact ``[k=v k=v]`` suffix, or "" for
    events without renderable metadata.

    Kept here (not in :mod:`core.runtime.lifecycle`) because the
    formatting is presentation, not state.  Discord's per-field 1024
    char limit means we cannot afford full JSON dumps; this picks the
    keys operators actually care about during an incident.
    """
    name = str(event.get("name", ""))
    metadata = event.get("metadata") or {}
    if not isinstance(metadata, dict) or not metadata:
        return ""
    parts: list[str] = []
    kind = metadata.get("kind")
    if kind and name in {"close_executing", "close_completed", "close_timeout"}:
        parts.append(f"kind={kind}")
    if name == "close_completed":
        duration = metadata.get("duration_seconds")
        if isinstance(duration, (int, float)):
            parts.append(f"dur={float(duration):.2f}s")
    if name == "close_timeout":
        timeout = metadata.get("timeout_seconds")
        if isinstance(timeout, (int, float)):
            parts.append(f"timeout={float(timeout):.2f}s")
    return f" [{' '.join(parts)}]" if parts else ""


def build_lifecycle_embed() -> discord.Embed:
    """Build the embed for ``!platform lifecycle``.

    Renders the lifecycle service state machine — current phase, the
    pending shutdown/restart request if any (with grace remaining),
    and the most recent events from the ring buffer, newest first.
    The events include ``shutdown_requested`` / ``restart_requested``
    (intent), ``close_executing`` / ``close_completed`` /
    ``close_timeout`` (close-driver outcomes), and the ``phase:<NAME>``
    transitions, so operators get a one-screen view of what the
    lifecycle has done lately.  Metadata on the close outcomes (kind,
    close duration, timeout value) is rendered compactly inline.

    Falls back to a degraded embed if the ``lifecycle`` provider is
    not registered, matching the ``build_caches_embed`` pattern.
    """
    from services import diagnostics_service

    try:
        snap = diagnostics_service.snapshot("lifecycle")
    except KeyError:
        return discord.Embed(
            title="🔄 Lifecycle",
            description="Provider not registered.",
            color=discord.Color.greyple(),
        )

    phase = str(snap.get("phase", "unknown"))
    can_accept = bool(snap.get("can_accept_commands", False))
    description_parts = [
        f"Phase: **{phase}** · Accepting commands: **{can_accept}**",
    ]
    startup_observed = snap.get("startup_duration_observed")
    if isinstance(startup_observed, bool):
        description_parts.append(
            f"Startup observed: **{'yes' if startup_observed else 'no'}**",
        )
    embed = discord.Embed(
        title="🔄 Lifecycle",
        description=" · ".join(description_parts),
        color=_LIFECYCLE_PHASE_COLORS.get(phase, discord.Color.greyple()),
    )

    pending = snap.get("pending")
    if pending:
        remaining = snap.get("remaining_shutdown_seconds")
        remaining_part = (
            f" · grace remaining: **{remaining:.1f}s**"
            if isinstance(remaining, (int, float)) and remaining > 0
            else ""
        )
        embed.add_field(
            name="Pending request",
            value=(
                f"kind: `{pending.get('kind', '<unknown>')}`{remaining_part}\n"
                f"reason: `{pending.get('reason', '<unknown>')}`\n"
                f"actor: `{pending.get('actor', '<unknown>')}`"
            ),
            inline=False,
        )
    else:
        embed.add_field(name="Pending request", value="_none_", inline=False)

    events = list(snap.get("recent_events", []))
    if events:
        # Snapshot is oldest-first; render newest-first and cap at 10 so
        # the field fits Discord's 1024-char limit comfortably.
        lines: list[str] = []
        for event in reversed(events[-10:]):
            actor_part = f" by `{event['actor']}`" if event.get("actor") else ""
            reason_part = f" — {event['reason']}" if event.get("reason") else ""
            meta_part = _fmt_lifecycle_event_metadata(event)
            lines.append(
                f"• `{event.get('name', '?')}` @ "
                f"{event.get('phase', '?')}{actor_part}{reason_part}{meta_part}",
            )
        embed.add_field(
            name=f"Recent events ({len(events)})",
            value="\n".join(lines)[:1024],
            inline=False,
        )
    else:
        embed.add_field(
            name="Recent events",
            value="_none recorded_",
            inline=False,
        )

    return embed


def build_caches_embed() -> discord.Embed:
    """Build the embed for ``!platform caches``."""
    from services import diagnostics_service

    embed = discord.Embed(
        title="🧠 Cache snapshot",
        color=discord.Color.blurple(),
    )
    for name in ("guild_config", "governance_cache"):
        try:
            snap = diagnostics_service.snapshot(name)
        except KeyError:
            snap = {"_error": "provider not registered"}
        embed.add_field(
            name=name,
            value=_fmt_snapshot_value(snap),
            inline=False,
        )
    return embed


def build_locks_embed(prefix: str = "") -> discord.Embed:
    """Build the embed for ``!platform locks [prefix]``."""
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("scope_locks")
    by_prefix = dict(snap.get("by_prefix", {}))
    if prefix:
        by_prefix = {k: v for k, v in by_prefix.items() if k == prefix}
    embed = discord.Embed(
        title="🔒 Scope locks",
        description=(
            f"total: **{snap.get('total', 0)}**  ·  "
            f"held: **{snap.get('held', 0)}**"
            + (f"  ·  filter: `{prefix}`" if prefix else "")
        ),
        color=discord.Color.blurple(),
    )
    if by_prefix:
        lines = [f"`{k}` — {v}" for k, v in sorted(by_prefix.items())]
        embed.add_field(
            name="By prefix",
            value="\n".join(lines)[:1024],
            inline=False,
        )
    else:
        embed.add_field(
            name="By prefix",
            value="*(no locks matching filter)*" if prefix else "*(none)*",
            inline=False,
        )
    return embed


def build_tasks_embed() -> discord.Embed:
    """Build the embed for ``!platform tasks``."""
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("tasks")
    names = list(snap.get("names", []))
    embed = discord.Embed(
        title="🔁 Managed tasks",
        description=f"{snap.get('active_count', 0)} active",
        color=discord.Color.blurple(),
    )
    if names:
        embed.add_field(
            name="Names",
            value="\n".join(f"`{n}`" for n in names)[:1024],
            inline=False,
        )
    return embed


def build_views_embed() -> discord.Embed:
    """Build the embed for ``!platform views``."""
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("persistent_views")
    subsystems = list(snap.get("subsystems", []))
    embed = discord.Embed(
        title="🖼 Persistent views",
        description=f"{snap.get('registered_count', 0)} registered",
        color=discord.Color.blurple(),
    )
    if subsystems:
        embed.add_field(
            name="Subsystems",
            value=", ".join(f"`{s}`" for s in subsystems)[:1024],
            inline=False,
        )
    return embed


def build_slow_embed(limit: int = 10) -> discord.Embed:
    """Build the embed for ``!platform slow [limit]`` (S3.2 ring buffer)."""
    from core.runtime import slow_path_log

    entries = slow_path_log.snapshot()
    limit = max(1, min(limit, 25))
    recent = entries[-limit:]
    embed = discord.Embed(
        title="🐢 Slow path log",
        description=(
            f"**{len(entries)}** entries  ·  threshold: "
            f"`{slow_path_log.threshold_ms():.0f}ms`  ·  "
            f"capacity: `{slow_path_log.capacity()}`"
        ),
        color=discord.Color.blurple(),
    )
    if not recent:
        embed.add_field(
            name="No slow paths recorded",
            value=f"All observations under {slow_path_log.threshold_ms():.0f}ms.",
            inline=False,
        )
    else:
        embed.set_footer(text=f"Showing the {len(recent)} most recent.")
        for entry in reversed(recent):
            age_s = max(0.0, datetime.datetime.now().timestamp() - entry.timestamp)
            embed.add_field(
                name=f"{entry.kind}: {entry.name}",
                value=f"**{entry.duration_ms:.0f}ms**  ·  {age_s:.0f}s ago",
                inline=False,
            )
    return embed


async def build_sessions_embed(
    subsystem: str = "",
) -> tuple[discord.Embed | None, str | None]:
    """Build the embed for ``!platform sessions [subsystem]``.

    Returns ``(embed, None)`` on success or ``(None, error_str)`` if the
    DB query fails — callers preserve the existing error-surface
    behavior of the typed command by checking the second element.
    """
    from utils import db

    try:
        if subsystem:
            rows = await db.fetchall(
                "SELECT subsystem, COUNT(*) AS n FROM runtime_sessions "
                "WHERE subsystem=$1 GROUP BY subsystem",
                (subsystem,),
            )
        else:
            rows = await db.fetchall(
                "SELECT subsystem, COUNT(*) AS n FROM runtime_sessions "
                "GROUP BY subsystem ORDER BY n DESC",
                (),
            )
    except Exception as exc:  # noqa: BLE001 — surface DB outage to operator
        return None, f"❌ DB query failed: {exc}"
    embed = discord.Embed(
        title="🎫 Active sessions",
        description=(f"filter: `{subsystem}`" if subsystem else "all subsystems"),
        color=discord.Color.blurple(),
    )
    if rows:
        lines = [f"`{r['subsystem']}` — {r['n']}" for r in rows]
        embed.add_field(
            name="By subsystem",
            value="\n".join(lines)[:1024],
            inline=False,
        )
    else:
        embed.add_field(name="By subsystem", value="*(none)*", inline=False)
    return embed, None


# ---------------------------------------------------------------------------
# Validation group
# ---------------------------------------------------------------------------


async def build_anchors_embed() -> discord.Embed:
    """Build the embed for ``!platform anchors``."""
    from core.runtime import message_anchor_manager
    from utils import db

    stats = message_anchor_manager.last_restore_stats()
    embed = discord.Embed(
        title="📌 Panel anchors",
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Last restoration",
        value=(
            f"seen: **{stats['anchors_seen']}**  ·  "
            f"restored: **{stats['restored']}**  ·  "
            f"view_missing: **{stats['view_missing']}**  ·  "
            f"stale: **{stats['stale']}**"
        ),
        inline=False,
    )
    try:
        rows = await db.fetchall(
            "SELECT subsystem, COUNT(*) AS n FROM panel_anchors "
            "WHERE NOT is_stale GROUP BY subsystem ORDER BY n DESC",
            (),
        )
        if rows:
            lines = [f"`{r['subsystem']}` — {r['n']}" for r in rows]
            embed.add_field(
                name="Active anchors by subsystem",
                value="\n".join(lines)[:1024],
                inline=False,
            )
        else:
            embed.add_field(
                name="Active anchors by subsystem",
                value="none",
                inline=False,
            )
    except Exception as exc:  # noqa: BLE001 — DB outage shouldn't crash command
        embed.add_field(
            name="Active anchors by subsystem",
            value=f"DB query failed: {exc}",
            inline=False,
        )
    return embed


async def build_identity_embed(
    bot: commands.Bot,
    mode: str = "",
) -> discord.Embed:
    """Build the embed for ``!platform identity [--fix]``."""
    from utils.subsystem_registry import (
        apply_self_heal,
        summarize_findings,
        validate_identity_contract,
    )

    findings = await validate_identity_contract(bot)
    summary = summarize_findings(findings)
    total = summary["total"]
    fatal = summary["by_tier"]["fatal"]
    auto = summary["by_tier"]["auto_healable"]

    heal_requested = mode.strip() in ("--fix", "-f", "fix")
    heal_counts: dict[str, int] | None = None
    if heal_requested:
        heal_counts = await apply_self_heal(findings)

    if total == 0:
        color = discord.Color.green()
        desc = "All four identity surfaces agree."
    elif fatal:
        color = discord.Color.red()
        desc = (
            f"{total} finding(s) — **{fatal} fatal**, "
            f"{auto} auto-healable.  Fatal findings require operator "
            "review (likely a cog failed to load)."
        )
    else:
        color = discord.Color.orange()
        desc = f"{total} finding(s) — {auto} auto-healable."

    embed = discord.Embed(
        title="🪪 Identity contract",
        description=desc,
        color=color,
    )
    # Reserve 1 slot for the optional heal_counts field.
    bucket_cap = _EMBED_FIELD_CAP - (1 if heal_counts is not None else 0)
    shown = 0
    overflow_buckets = 0
    for bucket, items in findings.items():
        if not items:
            continue
        if shown >= bucket_cap:
            overflow_buckets += 1
            continue
        embed.add_field(
            name=f"{bucket} ({len(items)})",
            value="\n".join(items)[:1024],
            inline=False,
        )
        shown += 1
    if overflow_buckets:
        embed.add_field(
            name=f"… {overflow_buckets} more bucket(s) not shown",
            value="Run `!platform identity` to see the full report.",
            inline=False,
        )
    if heal_counts is not None:
        embed.add_field(
            name="Self-heal result",
            value=(
                f"router prefixes unregistered: "
                f"`{heal_counts['router_prefixes_unregistered']}` · "
                f"views unregistered: `{heal_counts['views_unregistered']}` · "
                f"anchors marked stale: "
                f"`{heal_counts['anchors_marked_stale']}` · "
                f"fatal-tier skipped: `{heal_counts['skipped_fatal']}`"
            ),
            inline=False,
        )
    return embed


# ---------------------------------------------------------------------------
# Catalogues group — additional inline embeds
# ---------------------------------------------------------------------------


def build_participation_schemas_embed() -> discord.Embed:
    """Build the embed for ``!platform participation-schemas`` (Phase 1b)."""
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("participation_schemas")
    embed = discord.Embed(
        title="🧑‍🤝‍🧑 Participation schemas",
        description=(
            f"{snap['registered']} registered  ·  "
            f"subs={snap['subscriptions_total']}  ·  "
            f"vis={snap['visibility_intents_total']}  ·  "
            f"notif={snap['notification_intents_total']}  ·  "
            f"prefs={snap['preferences_total']}"
        ),
        color=discord.Color.blurple(),
    )
    by_sub = snap.get("by_subsystem", {})
    if by_sub:
        lines = [
            f"`{name}` — s={info['subscriptions']} "
            f"v={info['visibility_intents']} "
            f"n={info['notification_intents']} "
            f"p={info['preferences']} v{info['version']}"
            for name, info in sorted(by_sub.items())
        ]
        embed.add_field(
            name="By subsystem",
            value="\n".join(lines)[:1024],
            inline=False,
        )
    else:
        embed.add_field(name="By subsystem", value="*(none)*", inline=False)
    return embed


def build_resource_requirements_embed() -> discord.Embed:
    """Build the embed for ``!platform resource-requirements`` (Phase 1c)."""
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("resource_requirements")
    embed = discord.Embed(
        title="🧱 Resource requirements",
        description=f"{len(snap)} requirement(s) declared",
        color=discord.Color.blurple(),
    )
    if snap:
        lines = [
            f"`{r['subsystem']}` {r['kind']}/{r['intent']} "
            f"({r['priority']})"
            + (f" → `{r['suggested_name']}`" if r["suggested_name"] else "")
            for r in snap
        ]
        embed.add_field(
            name="Requirements",
            value="\n".join(lines)[:1024],
            inline=False,
        )
    else:
        embed.add_field(name="Requirements", value="*(none)*", inline=False)
    return embed


# ---------------------------------------------------------------------------
# Resources / rollout group — additional inline embeds
# ---------------------------------------------------------------------------


async def build_flags_embed(guild: discord.Guild | None) -> discord.Embed:
    """Build the embed for ``!platform flags``.

    Resolves every declared flag with provenance for the supplied guild
    (when ``guild`` is None, falls back to the global resolver context).
    """
    from core.runtime import feature_flags
    from services import diagnostics_service

    snap = diagnostics_service.snapshot("feature_flags")
    guild_id = guild.id if guild else None
    operator_rows: list[str] = []
    internal_rows: list[str] = []
    for name in sorted(snap.get("by_name", {})):
        info = snap["by_name"][name]
        try:
            decision = await feature_flags.resolve_with_provenance(
                name,
                guild_id,
            )
            effective = "on" if decision.value else "off"
            source = decision.source
        except Exception as exc:  # noqa: BLE001 — diagnostics must not raise
            effective = "?"
            source = f"error:{type(exc).__name__}"
        label = info.get("label") or name
        row = (
            f"`{name}` — {label} · "
            f"default={info['default_value']} eff={effective} src={source}"
        )
        if info.get("audience") == "operator":
            operator_rows.append(row)
        else:
            internal_rows.append(row)
    by_audience = snap.get("by_audience", {})
    embed = discord.Embed(
        title="🚩 Feature flags",
        description=(
            f"{snap['declared_total']} declared "
            f"({by_audience.get('operator', 0)} operator · "
            f"{by_audience.get('internal', 0)} internal)  ·  "
            f"cache={snap.get('cache_size', 0)}  ·  "
            f"bootstrap_fallback={snap.get('bootstrap_fallback_count', 0)}"
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Operator flags",
        value=("\n".join(operator_rows)[:1024] if operator_rows else "*(none)*"),
        inline=False,
    )
    internal_value = (
        "_Migration & kill-switch gates — not user-facing features._\n"
        + "\n".join(internal_rows)
        if internal_rows
        else "*(none)*"
    )
    embed.add_field(
        name="Internal / platform gates",
        value=internal_value[:1024],
        inline=False,
    )
    return embed


async def build_migrations_embed(
    guild: discord.Guild | None,
) -> discord.Embed:
    """Build the embed for ``!platform migrations`` (Phase 2 PR-5)."""
    from utils.db import platform_migration_checkpoints as checkpoint_db

    counts = await checkpoint_db.count_by_status()
    guild_rows = (
        await checkpoint_db.list_checkpoints(guild_id=guild.id) if guild else []
    )
    embed = discord.Embed(
        title="🛠 Platform migrations",
        description=(
            "Generic logical-migration checkpoint table; first "
            "consumer is the binding backfill (Phase 2 PR-5)."
        ),
        color=discord.Color.gold(),
    )
    if counts:
        status_line = " · ".join(
            f"{status}={n}" for status, n in sorted(counts.items())
        )
        embed.add_field(name="Global counts", value=status_line, inline=False)
    else:
        embed.add_field(
            name="Global counts",
            value="*(no rows)*",
            inline=False,
        )
    if guild_rows:
        rows: list[str] = []
        for row in guild_rows[:20]:
            summary = row.get("summary_json") or {}
            inner_counts = summary.get("counts") if isinstance(summary, dict) else None
            count_str = (
                " ".join(f"{k}={v}" for k, v in sorted((inner_counts or {}).items()))
                if inner_counts
                else ""
            )
            rows.append(
                f"`{row['name']}` status={row['status']} v={row['version']} "
                f"{count_str}".strip(),
            )
        embed.add_field(
            name=(
                f"This guild ({len(guild_rows)} "
                f"row{'s' if len(guild_rows) != 1 else ''})"
            ),
            value="\n".join(rows)[:1024],
            inline=False,
        )
    else:
        embed.add_field(
            name="This guild",
            value="*(no checkpoints)*",
            inline=False,
        )
    return embed


# ---------------------------------------------------------------------------
# Snapshot value formatter (shared helper)
# ---------------------------------------------------------------------------


def _fmt_snapshot_value(value: object) -> str:
    """Format a diagnostics-snapshot value for embed display."""
    from cogs.diagnostic._helpers import _fmt_snapshot_value as _impl

    return _impl(value)


# ---------------------------------------------------------------------------
# Setup readiness (PR H)
# ---------------------------------------------------------------------------


def _render_health_findings(embed, report) -> None:
    """Add per-subsystem "Health · <sub>" fields for error/warn findings.

    Info-only findings stay in the description blurb; only actionable
    findings get their own field to keep the embed compact.
    """
    actionable = [f for f in report.health_findings if f.severity in ("error", "warn")]
    if not actionable:
        return
    by_sub: dict[str, list[str]] = {}
    for f in actionable:
        icon = "🔴" if f.severity == "error" else "🟡"
        by_sub.setdefault(f.subsystem, []).append(
            f"{icon} `{f.binding_name}` · {f.status} — {f.message}",
        )
    for subsystem in sorted(by_sub):
        value = "\n".join(by_sub[subsystem])
        # 1024-char field cap; truncate generously to avoid 400s.
        if len(value) > 1000:
            value = value[:997] + "..."
        embed.add_field(
            name=f"Health · {subsystem}",
            value=value,
            inline=False,
        )


async def build_setup_readiness_embed(
    guild_id: int,
    *,
    guild: discord.Guild | None = None,
) -> discord.Embed:
    """Render a per-guild setup-readiness inventory.

    Calls :func:`services.setup_readiness.collect`, then formats the
    per-subsystem counts + aggregate score into an embed. Subsystems
    with no declared config show as ``—``; populated subsystems show
    ``filled/declared`` for both bindings and settings plus a percent.

    When ``guild`` is provided, the embed also renders Phase 9d
    resource-health findings grouped by subsystem and a per-severity
    summary line.
    """
    from services import setup_readiness

    report = await setup_readiness.collect(guild_id, guild=guild)

    title_score = "—" if report.aggregate_score is None else f"{report.percentage}%"

    summary = report.health_summary
    health_blurb = ""
    if summary:
        health_blurb = (
            f" · health "
            f"`{summary.get('error', 0)} err`"
            f" `{summary.get('warn', 0)} warn`"
            f" `{summary.get('info', 0)} info`"
        )

    embed = discord.Embed(
        title=f"🛰 Setup Readiness — {title_score}",
        description=(
            f"**{report.bindings_bound}/{report.bindings_declared}** bindings · "
            f"**{report.settings_configured}/{report.settings_declared}** settings · "
            f"**{report.resources_declared}** resource declarations"
            f"{health_blurb}"
        ),
        color=discord.Color.blurple(),
    )

    _render_health_findings(embed, report)

    if not report.per_subsystem:
        embed.add_field(
            name="No subsystem schemas registered",
            value="`cog_load` did not call `subsystem_schema.register`.",
            inline=False,
        )
        return embed

    # Render each subsystem as one line; group up to ~15 per field so
    # we stay under the 1024-char per-field cap with operator-readable
    # wrapping.
    lines: list[str] = []
    for entry in report.per_subsystem:
        # entry.has_config is False iff bindings_declared == 0 AND
        # settings_declared == 0 — same case where score ends up None.
        # Treat both as "nothing to score" and surface the em-dash.
        if not entry.has_config or entry.score is None:
            score = "—"
        else:
            score = f"{round(entry.score * 100)}%"
        lines.append(
            f"`{entry.subsystem:<14}` "
            f"bindings {entry.bindings_bound}/{entry.bindings_declared} · "
            f"settings {entry.settings_configured}/{entry.settings_declared} · "
            f"resources {entry.resources_declared} · {score}",
        )

    # Chunk lines into ≤15 per field to stay comfortably under 1024.
    # Track total fields added so we never exceed Discord's 25-field cap.
    chunk_size = 15
    fields_used = len(embed.fields)
    for i in range(0, len(lines), chunk_size):
        if fields_used >= _EMBED_FIELD_CAP:
            remaining_lines = len(lines) - i
            embed.add_field(
                name=f"… {remaining_lines} more subsystem(s) not shown",
                value="Too many fields for one embed.",
                inline=False,
            )
            break
        chunk = lines[i : i + chunk_size]
        name = (
            f"Subsystems ({i + 1}–{i + len(chunk)})"
            if len(lines) > chunk_size
            else "Subsystems"
        )
        embed.add_field(name=name, value="\n".join(chunk), inline=False)
        fields_used += 1

    embed.set_footer(
        text=(
            "Read-only. Empty settings_keys (legacy KV) count as unconfigured. "
            "Subsystems with no declared config show — in the score column."
        ),
    )
    return embed


async def build_command_access_diagnostic_embed(
    *,
    ctx: commands.Context,
    target_channel: discord.abc.GuildChannel,
) -> discord.Embed:
    """Render the live command-access decision for ``target_channel``.

    Closes the "command vanished" debugging loop the command-access
    onboarding fix exists to fix: the operator can ask the bot
    directly "would `!bj` work here, and if not, why" and get a
    structured answer that names the mode, the source, the reason,
    and the recovery path.

    The probe runs the real resolver with a synthetic
    :class:`CommandAccessContext`, scoring the channel as if a
    non-bootstrap normal command (``blackjack``) were invoked there
    by the requesting operator.  This mirrors the most common
    operator-facing failure mode — the one that prompted the entire
    fix — instead of probing with a bootstrap command that would
    bypass the policy and tell us nothing.
    """
    from core.runtime.command_access import (
        AccessMode,
        CommandAccessContext,
        resolve_command_access,
    )
    from services.command_access_service import get_policy_snapshot

    guild = ctx.guild
    guild_id = guild.id if guild is not None else None
    snapshot = await get_policy_snapshot(guild_id) if guild_id is not None else None

    author = ctx.author
    perms = getattr(author, "guild_permissions", None)
    is_operator = bool(
        perms
        and (
            getattr(perms, "administrator", False)
            or getattr(perms, "manage_guild", False)
        ),
    )
    if hasattr(ctx.bot, "is_owner"):
        is_bot_owner = await ctx.bot.is_owner(author)
    else:
        is_bot_owner = False

    probe_ctx = CommandAccessContext(
        guild_id=guild_id,
        channel_id=target_channel.id,
        user_id=author.id,
        command_name="blackjack",  # synthetic non-bootstrap probe
        invocation_type="prefix",
        is_guild_operator=is_operator,
        is_bot_owner=bool(is_bot_owner),
        is_dm=guild is None,
    )
    decision = await resolve_command_access(probe_ctx)

    title_emoji = "✅" if decision.allowed else "🚫"
    embed = discord.Embed(
        title=f"{title_emoji} Command Access — {target_channel.mention}",
        color=discord.Color.green() if decision.allowed else discord.Color.red(),
    )

    if snapshot is None or snapshot.mode is None:
        embed.add_field(
            name="Configured mode",
            value="`all_channels` (default — no policy row in this guild)",
            inline=False,
        )
    else:
        embed.add_field(
            name="Configured mode",
            value=f"`{snapshot.mode}`",
            inline=False,
        )

    if snapshot is not None and snapshot.allowed_channels:
        listed = " ".join(f"<#{cid}>" for cid in sorted(snapshot.allowed_channels))
        if len(listed) > 950:
            head = " ".join(
                f"<#{cid}>" for cid in sorted(snapshot.allowed_channels)[:30]
            )
            listed = f"{head} … (+{len(snapshot.allowed_channels) - 30} more)"
        embed.add_field(
            name=f"Allowed channels ({len(snapshot.allowed_channels)})",
            value=listed,
            inline=False,
        )

    embed.add_field(
        name="Would a normal command run here?",
        value=("**Yes** — admitted." if decision.allowed else "**No** — denied."),
        inline=False,
    )
    embed.add_field(
        name="Decision details",
        value=(
            f"`reason`: {decision.reason.value}\n"
            f"`source`: {decision.source.value}\n"
            f"`effective_mode`: "
            f"{decision.mode.value if decision.mode is not None else 'n/a'}\n"
            f"`prefix_enabled`: yes\n"
            f"`slash_enabled`: yes  *(same admission chain)*"
        ),
        inline=False,
    )

    bootstrap_ctx = CommandAccessContext(
        guild_id=guild_id,
        channel_id=target_channel.id,
        user_id=author.id,
        command_name="setup",
        invocation_type="prefix",
        is_guild_operator=is_operator,
        is_bot_owner=bool(is_bot_owner),
        is_dm=guild is None,
    )
    bootstrap_decision = await resolve_command_access(bootstrap_ctx)
    embed.add_field(
        name="Bootstrap probe (`!setup` for this operator)",
        value=(
            "✅ allowed via `bootstrap_bypass`"
            if bootstrap_decision.allowed
            else f"🚫 denied — reason `{bootstrap_decision.reason.value}`"
        ),
        inline=False,
    )

    if decision.feedback is not None:
        embed.add_field(
            name="Operator-facing feedback (sent on real invocations)",
            value=decision.feedback,
            inline=False,
        )

    if decision.mode is AccessMode.DISABLED_EXCEPT_BOOTSTRAP:
        embed.add_field(
            name="Recovery",
            value=(
                "Open `!settings → Command access` to switch the mode, "
                "or run `!setup` to revisit onboarding."
            ),
            inline=False,
        )

    embed.set_footer(
        text=(
            "Probe was synthetic; no audit row was emitted.  "
            "Configure via `!settings → Command access`."
        ),
    )
    return embed


__all__ = [
    "build_anchors_embed",
    "build_bindings_embed",
    "build_caches_embed",
    "build_command_access_diagnostic_embed",
    "build_consistency_embed",
    "build_customization_embed",
    "build_flags_embed",
    "build_identity_embed",
    "build_lifecycle_embed",
    "build_locks_embed",
    "build_migrations_embed",
    "build_participation_schemas_embed",
    "build_provisioning_embed",
    "build_resource_requirements_embed",
    "build_resources_embed",
    "build_runtime_embed",
    "build_schemas_embed",
    "build_sessions_embed",
    "build_settings_registry_embed",
    "build_setup_readiness_embed",
    "build_slow_embed",
    "build_status_embed",
    "build_tasks_embed",
    "build_views_embed",
]
