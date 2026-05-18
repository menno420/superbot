"""Embed builders for the ``!platform <subcommand>`` admin surface.

Extracted from ``cogs/diagnostic_cog.py`` to keep the cog under the
800-LOC fail threshold enforced by
``tests/unit/invariants/test_cog_size.py``.  Each builder is a pure
async function that fetches its data (via ``services.diagnostics_service``
and/or ``utils.db.*``) and returns a single :class:`discord.Embed`
ready to send.  The cog methods become thin wrappers that delegate
here.

Phase 2a + 2b + 2.10 builders covered:

* :func:`build_resources_embed`     — ``!platform resources``
* :func:`build_bindings_embed`      — ``!platform bindings``
* :func:`build_consistency_embed`   — ``!platform consistency``

Earlier-phase platform commands stay inline in the cog for now.  When
the next batch of platform commands lands and pushes the cog back
toward the ceiling, those should migrate here too.
"""

from __future__ import annotations

import discord

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


__all__ = [
    "build_bindings_embed",
    "build_consistency_embed",
    "build_customization_embed",
    "build_provisioning_embed",
    "build_resources_embed",
    "build_schemas_embed",
    "build_settings_registry_embed",
]
