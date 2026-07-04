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
import logging
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from services.health_contracts import HealthSnapshot
from services.platform_consistency import (
    ConsistencyReport,
    SectionResult,
    SectionStatus,
)

if TYPE_CHECKING:
    from governance.models import CleanupPolicy, GovernanceSnapshot
    from services.binding_backfill import ApplyResult, DryRunSummary


logger = logging.getLogger("bot.services.diagnostic_embeds")


# ---------------------------------------------------------------------------
# Operator explainers (IL-1 / IL-2 / IL-3) — read-only diagnostics that reuse
# existing governance read models + the task_outcome_total metric.  No new
# governance / preview / monitor system (Ideas Lab D1/D2): IL-1/IL-2 take a
# pre-resolved snapshot/policy and just render it; IL-3 reads the existing
# managed-task counter.
# ---------------------------------------------------------------------------


def governance_context_for(ctx: commands.Context, target: object):
    """Build a GovernanceContext for an arbitrary channel/thread (IL-1/IL-2).

    Mirrors ``GovernanceContext.from_ctx`` but for a user-selected ``target``
    instead of ``ctx.channel``, keeping the invoker's member/roles so the
    explainer answers "can *I* use this here?".  Lives here (not in the cog)
    so the cog stays under the 800-LOC ceiling; the two ``!platform`` explainer
    commands import it lazily.
    """
    from governance.models import GovernanceContext

    if isinstance(target, discord.Thread):
        thread_id = target.id
        channel_id = target.parent_id
        category_id = getattr(target.parent, "category_id", None)
    else:
        thread_id = None
        channel_id = getattr(target, "id", None)
        category_id = getattr(target, "category_id", None)
    member = ctx.author
    return GovernanceContext(
        guild_id=ctx.guild.id,
        channel_id=channel_id,
        category_id=category_id,
        thread_id=thread_id,
        member=member if isinstance(member, discord.Member) else None,
        role_ids={r.id for r in getattr(member, "roles", [])},
    )


def _capped(items: list[str], *, empty: str = "*(none)*", cap: int = 1000) -> str:
    if not items:
        return empty
    out = ", ".join(items)
    return out if len(out) <= cap else out[: cap - 1] + "…"


def build_access_explainer_embed(
    target_label: str,
    snapshot: GovernanceSnapshot,
) -> discord.Embed:
    """IL-1 — "can I use this here?" explainer over a GovernanceSnapshot.

    Pure renderer: the caller resolves the snapshot (async, thread-aware) and
    passes it in.  Validates RC-2 in production (a thread and its parent yield
    different snapshots).
    """
    embed = discord.Embed(
        title="🔎 Access — what's usable here",
        description=(
            f"Governance visibility for **{target_label}** "
            f"(your member tier: `{snapshot.member_tier}`)."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name=f"✅ Visible ({len(snapshot.visible_subsystems)})",
        value=_capped(sorted(f"`{s}`" for s in snapshot.visible_subsystems)),
        inline=False,
    )
    embed.add_field(
        name=f"🚫 Denied ({len(snapshot.denied_subsystems)})",
        value=_capped(sorted(f"`{s}`" for s in snapshot.denied_subsystems)),
        inline=False,
    )
    if snapshot.dependency_blocks:
        blocks = [
            f"`{name}` ← needs {', '.join(f'`{d}`' for d in sorted(deps))}"
            for name, deps in sorted(snapshot.dependency_blocks.items())
        ]
        embed.add_field(name="⛓ Dependency blocks", value=_capped(blocks), inline=False)
    prov = [
        f"`{name}` → {src.value}"
        for name, src in sorted(snapshot.scope_provenance.items())
    ]
    if prov:
        embed.add_field(name="📍 Resolved from", value=_capped(prov), inline=False)
    cp = snapshot.cleanup_policy
    embed.add_field(
        name="🧹 Cleanup here",
        value=(
            f"delete: `{cp.delete_message}` · after: `{cp.delete_after_seconds}s` "
            f"· feedback: `{cp.send_feedback}` · from: `{cp.resolved_from.value}`"
        ),
        inline=False,
    )
    embed.set_footer(text="Read-only · reflects your roles in the selected location")
    return embed


def build_cleanup_preview_embed(
    target_label: str,
    policy: CleanupPolicy,
    *,
    is_thread: bool,
    valid_cleanup_scopes: frozenset[str],
) -> discord.Embed:
    """IL-2 — dry-run preview of the cleanup policy that WOULD apply here.

    Reuses the read model (``resolve_cleanup_policy`` → ``CleanupPolicy``) and
    the canonical cleanup-scope set; makes no writes.  There is no existing
    resolved-policy renderer to reuse (the setup-wizard ``build_cleanup_embed``
    is a static info page), so this follows the standard ``_platform_embeds``
    idiom rather than introducing a second resolver/read model.
    """
    embed = discord.Embed(
        title="🧹 Cleanup preview (dry run)",
        description=(
            f"Resolved cleanup policy for **{target_label}** — no changes made."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Delete message", value=f"`{policy.delete_message}`")
    embed.add_field(name="Delete after", value=f"`{policy.delete_after_seconds}s`")
    embed.add_field(name="Send feedback", value=f"`{policy.send_feedback}`")
    embed.add_field(
        name="Resolved from",
        value=f"`{policy.resolved_from.value}`",
        inline=False,
    )
    embed.add_field(
        name="Cleanup write scopes",
        value=(
            ", ".join(f"`{s}`" for s in sorted(valid_cleanup_scopes))
            + " — `thread` is **not** a cleanup scope (RC-5)"
        ),
        inline=False,
    )
    if is_thread:
        embed.add_field(
            name="ℹ️ Thread note",
            value=(
                "This is a thread: cleanup resolves via the **parent channel**, "
                "and a thread-scoped cleanup write is rejected before the DB."
            ),
            inline=False,
        )
    embed.set_footer(text="Read-only dry run · no cleanup policy was written")
    return embed


def read_counting_save_outcomes(guild_id: int | None = None) -> dict[str, int] | None:
    """IL-3 read helper — sum ``task_outcome_total`` for counting:save tasks.

    Surfaces the EXISTING managed-task metric (RC-15 made counting save failures
    observable through it) — not a new monitor (Ideas Lab D2).  Returns
    ``{"ok", "error", "cancelled"}`` (process-lifetime counts), or ``None`` when
    ``prometheus_client`` is unavailable (the counter is a silent no-op then).
    """
    from services import metrics

    if not metrics.PROMETHEUS_AVAILABLE:
        return None
    prefix = "counting:save:"
    want = f"counting:save:{guild_id}" if guild_id is not None else None
    totals = {"ok": 0, "error": 0, "cancelled": 0}
    for family in metrics.task_outcome_total.collect():
        for sample in family.samples:
            if sample.name.endswith("_created"):
                continue
            name = sample.labels.get("name", "")
            outcome = sample.labels.get("outcome", "")
            if want is not None:
                if name != want:
                    continue
            elif not name.startswith(prefix):
                continue
            if outcome in totals:
                totals[outcome] += int(sample.value)
    return totals


def build_counting_health_embed(
    guild_id: int,
    guild_outcomes: dict[str, int] | None,
    global_outcomes: dict[str, int] | None,
) -> discord.Embed:
    """IL-3 — render counting persistence health from task_outcome_total reads."""
    embed = discord.Embed(
        title="🔢 Counting persistence health",
        color=discord.Color.blurple(),
    )
    if global_outcomes is None:
        embed.description = (
            "⚠️ `prometheus_client` is not installed — task metrics are no-ops, "
            "so save-outcome counts are unavailable. Failures still log at ERROR "
            "via the managed-task layer (RC-15)."
        )
        return embed

    def _line(o: dict[str, int]) -> str:
        return (
            f"ok: `{o.get('ok', 0)}` · error: `{o.get('error', 0)}` · "
            f"cancelled: `{o.get('cancelled', 0)}`"
        )

    embed.add_field(
        name=f"This guild ({guild_id})",
        value=_line(guild_outcomes or {}),
        inline=False,
    )
    embed.add_field(
        name="All guilds (this process)",
        value=_line(global_outcomes),
        inline=False,
    )
    errors = (guild_outcomes or {}).get("error", 0) or global_outcomes.get("error", 0)
    if errors:
        embed.color = discord.Color.orange()
        embed.add_field(
            name="Verdict",
            value=(
                "⚠️ counting save errors observed — a guild may have lost count "
                "progress. Check ERROR logs (`bot` logger) for the traceback "
                "(RC-15 routes these through the managed-task done-callback)."
            ),
            inline=False,
        )
    else:
        embed.add_field(
            name="Verdict",
            value="✅ no save errors observed",
            inline=False,
        )
    embed.set_footer(text="Counts are since process start (in-memory metric)")
    return embed


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


def build_consistency_pages(report: ConsistencyReport) -> list[discord.Embed]:
    """Render a ConsistencyReport across one *or more* embeds (punch #2).

    Unlike :func:`build_consistency_embed` (which collapses then *drops*
    trailing sections to fit a single embed), this keeps **every** section
    reachable by chunking them across pages: sections are packed greedily so
    each page stays under ``_EMBED_SOFT_CAP`` and ``_FIELD_HARD_CAP`` fields.
    A ``Page i/N`` line is added to the footer only when there is more than
    one page; a report that fits one embed returns ``[single_embed]``.
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
    description = (
        f"{counts[SectionStatus.CLEAN]} clean · "
        f"{counts[SectionStatus.WARNING]} warning · "
        f"{counts[SectionStatus.FATAL]} fatal · "
        f"{counts[SectionStatus.SKIPPED]} skipped · "
        f"generated {generated}"
    )
    base_footer = (
        f"{runtime_warnings} runtime warning · "
        f"{informational_warnings} informational"
    )

    # Pre-format every section value once, then greedily pack into pages.
    rendered = [(section, _format_field_value(section)) for section in report.sections]
    base_size = len(description) + len(base_footer) + 40  # title + headroom
    pages_sections: list[list[tuple[SectionResult, str]]] = []
    current: list[tuple[SectionResult, str]] = []
    current_size = base_size
    for section, value in rendered:
        field_size = len(section.name) + len(value) + 4
        over_size = current and current_size + field_size > _EMBED_SOFT_CAP
        over_fields = len(current) >= _FIELD_HARD_CAP
        if over_size or over_fields:
            pages_sections.append(current)
            current = []
            current_size = base_size
        current.append((section, value))
        current_size += field_size
    if current:
        pages_sections.append(current)
    if not pages_sections:  # no sections at all — still emit one summary page
        pages_sections.append([])

    page_count = len(pages_sections)
    color = _STATUS_COLOR.get(overall, discord.Color.light_grey())
    pages: list[discord.Embed] = []
    for page_no, page in enumerate(pages_sections, start=1):
        embed = discord.Embed(
            title=f"🛡 Platform consistency · {overall.value.upper()}",
            description=description,
            color=color,
        )
        for section, value in page:
            icon = _STATUS_ICON.get(section.status, "•")
            embed.add_field(name=f"{icon} {section.name}", value=value, inline=False)
        footer = base_footer
        if page_count > 1:
            footer = f"Page {page_no}/{page_count} · {footer}"
        embed.set_footer(text=footer)
        pages.append(embed)
    return pages


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


async def build_settings_registry_embed(
    guild: discord.Guild | None = None,
) -> discord.Embed:
    """Build the embed for ``!platform settings-registry`` (S1).

    The header shows catalogue counts + findings. When a ``guild`` is
    supplied, each subsystem's current per-guild values + provenance are
    listed too (reusing
    :func:`services.settings_resolution.resolve_batch`), so the command
    answers "what is actually configured here" — not just "what settings
    exist".
    """
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
    if guild is not None and by_sub:
        # Per-guild current values + provenance, one field per subsystem.
        from services.settings_resolution import resolve_batch

        for subsystem in sorted(by_sub):
            if len(embed.fields) >= 23:  # leave room for the findings field
                break
            try:
                resolutions = await resolve_batch(guild.id, subsystem)
            except Exception as exc:  # noqa: BLE001 — diagnostics must not raise
                embed.add_field(
                    name=subsystem,
                    value=f"*(resolve error: {type(exc).__name__})*",
                    inline=False,
                )
                continue
            lines = [
                f"`{res.name}` = `{res.value}` (src={res.provenance}"
                f"{'' if res.valid else ' ⚠️invalid'})"
                for res in resolutions
            ]
            embed.add_field(
                name=subsystem,
                value=("\n".join(lines)[:1024] if lines else "*(no scalar settings)*"),
                inline=False,
            )
    elif by_sub:
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


async def build_setting_detail_embed(
    guild: discord.Guild | None,
    subsystem: str,
    name: str,
) -> discord.Embed:
    """Build the embed for ``!platform setting <subsystem> <name>``.

    The scalar-settings analogue of the feature-flag detail surface:
    shows the resolved value, its provenance (``default`` vs
    ``legacy_kv``), the declared default, validity, the raw stored
    string, and any resolver diagnostics. Reuses
    :func:`services.settings_resolution.resolve_setting` so value
    interpretation stays centralised — this is a pure read.
    """
    from services.settings_resolution import resolve_setting

    guild_id = guild.id if guild else 0
    resolution = await resolve_setting(guild_id, subsystem, name)
    if resolution is None:
        return discord.Embed(
            title="⚙️ Unknown setting",
            description=(
                f"No declared setting `{subsystem}.{name}`. "
                "Use `!platform settings-registry` to list what exists."
            ),
            color=discord.Color.red(),
        )
    embed = discord.Embed(
        title=f"⚙️ {subsystem}.{name}",
        color=(discord.Color.blurple() if resolution.valid else discord.Color.orange()),
    )
    embed.add_field(name="Value", value=f"`{resolution.value}`", inline=True)
    embed.add_field(
        name="Provenance",
        value=f"`{resolution.provenance}`",
        inline=True,
    )
    embed.add_field(name="Default", value=f"`{resolution.default}`", inline=True)
    embed.add_field(
        name="Valid",
        value="`yes`" if resolution.valid else "`no — using default`",
        inline=True,
    )
    raw_display = "*(none)*" if resolution.raw is None else f"`{resolution.raw}`"
    embed.add_field(name="Raw KV", value=raw_display[:1024], inline=True)
    if resolution.diagnostics:
        embed.add_field(
            name="Diagnostics",
            value="\n".join(resolution.diagnostics)[:1024],
            inline=False,
        )
    embed.set_footer(
        text=(
            "default = no KV row / spec default · legacy_kv = a stored value "
            "drove this (invalid rows fall back to the declared default)."
        ),
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


# --- !platform health (deterministic operational health) -------------------

_HEALTH_STATUS_EMOJI = {
    "healthy": "🟢",
    "degraded": "🟡",
    "critical": "🔴",
    "unknown": "⚪",
}
_HEALTH_STATUS_COLOR = {
    "healthy": discord.Color.green(),
    "degraded": discord.Color.gold(),
    "critical": discord.Color.red(),
    "unknown": discord.Color.light_grey(),
}
_FINDING_EMOJI = {
    "info": "ℹ️",
    "warning": "⚠️",
    "error": "⛔",
    "critical": "🔴",
}
_HEALTH_FINDINGS_SHOWN = 8
_HEALTH_FIELD_CAP = 1000


def _health_block(lines: list[str]) -> str:
    """Join ``lines`` into one bounded field value."""
    block = "\n".join(lines)
    if len(block) > _HEALTH_FIELD_CAP:
        block = block[: _HEALTH_FIELD_CAP - 1].rstrip() + "…"
    return block or "*(none)*"


def _render_health_embed(
    snapshot: HealthSnapshot,
    *,
    title: str,
    drilldown: str,
) -> discord.Embed:
    """Render an already-projected snapshot into a bounded embed.

    Shared by ``build_health_embed`` and ``build_startup_health_embed`` —
    the snapshot is audience-projected + redacted by
    ``services.health_snapshot_service`` before it reaches here; this only
    renders and bounds it (it never re-fetches or widens).
    """
    from core.runtime.interaction_helpers import clamp_embed

    status = snapshot.status.value
    description = (
        f"{_HEALTH_STATUS_EMOJI.get(status, '⚪')} **{status.upper()}** — "
        f"{snapshot.summary}"
    )
    if snapshot.partial:
        description += "\n*(partial — some checks timed out or were unavailable)*"
    embed = discord.Embed(
        title=title,
        description=description,
        color=_HEALTH_STATUS_COLOR.get(status, discord.Color.light_grey()),
        timestamp=snapshot.generated_at,
    )

    sub_lines = [
        f"{_HEALTH_STATUS_EMOJI.get(s.status.value, '⚪')} **{s.name}**"
        f"{' ⏳' if s.stale else ''} — {s.summary}"
        for s in snapshot.subsystems
    ]
    embed.add_field(
        name="Subsystems",
        value=_health_block(sub_lines),
        inline=False,
    )

    if snapshot.findings:
        finding_lines = [
            f"{_FINDING_EMOJI.get(f.severity.value, '•')} {f.message}"
            + (f" (×{f.occurrence_count})" if f.occurrence_count > 1 else "")
            for f in snapshot.findings[:_HEALTH_FINDINGS_SHOWN]
        ]
        embed.add_field(
            name=f"Findings ({len(snapshot.findings)})",
            value=_health_block(finding_lines),
            inline=False,
        )

    audience = (
        snapshot.redaction_audience.value
        if snapshot.redaction_audience is not None
        else "n/a"
    )
    embed.set_footer(
        text=(
            f"snapshot {snapshot.snapshot_id} · {audience} · deterministic "
            f"(AI not involved) · {drilldown}"
        ),
    )
    return clamp_embed(embed)


def build_health_embed(snapshot: HealthSnapshot) -> discord.Embed:
    """Render ``!platform health`` (live operational health)."""
    return _render_health_embed(
        snapshot,
        title="🩺 Bot health",
        drilldown="drill down: !platform runtime / lifecycle / tasks / consistency",
    )


def build_startup_health_embed(snapshot: HealthSnapshot) -> discord.Embed:
    """Render ``!platform startup`` (the settled-startup health report)."""
    return _render_health_embed(
        snapshot,
        title="🚀 Startup health",
        drilldown="settled-startup snapshot · !platform health for live state",
    )


def _finding_line(row: dict, *, is_owner: bool) -> str:
    """Render one persistent-finding row as a display line.

    Owner-only hints (``file_hint``) are appended only when ``is_owner``.
    Shared by the single-embed and paginated renders so they never diverge.
    """
    sev = str(row.get("severity", "info"))
    count = int(row.get("occurrence_count", 1) or 1)
    count_suffix = f" (×{count})" if count > 1 else ""
    line = (
        f"{_FINDING_EMOJI.get(sev, '•')} `{row.get('status', 'open')}` "
        f"**{row.get('category', '?')}** — {row.get('message', '')}{count_suffix}"
    )
    if is_owner and row.get("file_hint"):
        line += f"\n  ↳ {row['file_hint']}"
    return line


def build_findings_embed(
    rows: list[dict],
    *,
    status: str,
    counts: dict,
    is_owner: bool = False,
) -> discord.Embed:
    """Render persistent operational-health findings (``!platform findings``, PR6).

    ``rows`` are DB records (already scrubbed of secrets/IDs at record time);
    owner-only hints (file/provider) are shown only when ``is_owner``. Unlike
    the live health embed, these persist across restarts with an accumulating
    occurrence count.
    """
    from core.runtime.interaction_helpers import clamp_embed

    total = sum(int(v) for v in counts.values()) if counts else 0
    summary = (
        f"open {counts.get('open', 0)} · resolved {counts.get('resolved', 0)} · "
        f"ignored {counts.get('ignored', 0)} · {total} total"
    )
    embed = discord.Embed(
        title=f"🩺 Health findings — {status}",
        description=summary,
        color=discord.Color.orange() if rows else discord.Color.green(),
        timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
    )
    if not rows:
        embed.add_field(name="Findings", value="*(none)*", inline=False)
        return clamp_embed(embed)

    lines = [
        _finding_line(row, is_owner=is_owner) for row in rows[:_HEALTH_FINDINGS_SHOWN]
    ]
    embed.add_field(
        name=f"Findings ({len(rows)} shown)",
        value=_health_block(lines),
        inline=False,
    )
    embed.set_footer(
        text=(
            "persistent findings · recurrence survives restarts · "
            f"{'owner view' if is_owner else 'admin view (redacted)'}"
        ),
    )
    return clamp_embed(embed)


# Rows rendered per findings page when paginating (punch #2). Matches the
# single-embed `_HEALTH_FINDINGS_SHOWN` ceiling so each page block stays
# comfortably under Discord's per-field 1024-char limit.
_FINDINGS_PER_PAGE = _HEALTH_FINDINGS_SHOWN


def build_findings_pages(
    rows: list[dict],
    *,
    status: str,
    counts: dict,
    is_owner: bool = False,
) -> list[discord.Embed]:
    """Render persistent findings across one *or more* embeds (punch #2).

    Unlike :func:`build_findings_embed` (which shows only the first
    ``_HEALTH_FINDINGS_SHOWN`` rows), this chunks **all** ``rows`` into
    pages of ``_FINDINGS_PER_PAGE`` so dense output stays reachable via the
    paginator. With 0–``_FINDINGS_PER_PAGE`` rows the result is a single
    page identical in spirit to the legacy embed; a ``Page i/N`` footer is
    added only when there is more than one page.
    """
    if len(rows) <= _FINDINGS_PER_PAGE:
        return [
            build_findings_embed(rows, status=status, counts=counts, is_owner=is_owner),
        ]

    from core.runtime.interaction_helpers import clamp_embed

    total = sum(int(v) for v in counts.values()) if counts else 0
    summary = (
        f"open {counts.get('open', 0)} · resolved {counts.get('resolved', 0)} · "
        f"ignored {counts.get('ignored', 0)} · {total} total"
    )
    chunks = [
        rows[i : i + _FINDINGS_PER_PAGE]
        for i in range(0, len(rows), _FINDINGS_PER_PAGE)
    ]
    page_count = len(chunks)
    view_label = "owner view" if is_owner else "admin view (redacted)"
    pages: list[discord.Embed] = []
    for page_no, chunk in enumerate(chunks, start=1):
        embed = discord.Embed(
            title=f"🩺 Health findings — {status}",
            description=summary,
            color=discord.Color.orange(),
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        lines = [_finding_line(row, is_owner=is_owner) for row in chunk]
        embed.add_field(
            name=f"Findings ({len(rows)} total)",
            value=_health_block(lines),
            inline=False,
        )
        embed.set_footer(
            text=(
                f"Page {page_no}/{page_count} · persistent findings · "
                f"recurrence survives restarts · {view_label}"
            ),
        )
        pages.append(clamp_embed(embed))
    return pages


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


def _fmt_age(ts: object) -> str:
    """Render a UTC timestamp as a compact '<n>s/m/h/d ago', or '—'."""
    if not isinstance(ts, datetime.datetime):
        return "—"
    now = datetime.datetime.now(datetime.timezone.utc)
    when = ts if ts.tzinfo is not None else ts.replace(tzinfo=datetime.timezone.utc)
    delta = (now - when).total_seconds()
    if delta < 0:
        return "0s ago"
    for unit, size in (("d", 86400), ("h", 3600), ("m", 60)):
        if delta >= size:
            return f"{delta / size:.1f}{unit} ago"
    return f"{delta:.0f}s ago"


def _fmt_until(ts: object) -> str:
    """Render a future UTC timestamp as a compact 'in <n>s/m/h/d', or '—'."""
    if not isinstance(ts, datetime.datetime):
        return "—"
    now = datetime.datetime.now(datetime.timezone.utc)
    when = ts if ts.tzinfo is not None else ts.replace(tzinfo=datetime.timezone.utc)
    delta = (when - now).total_seconds()
    if delta <= 0:
        return "now"
    for unit, size in (("d", 86400), ("h", 3600), ("m", 60)):
        if delta >= size:
            return f"in {delta / size:.1f}{unit}"
    return f"in {delta:.0f}s"


async def build_media_embed() -> discord.Embed:
    """Build the embed for ``!platform media`` — content-free media diagnostics.

    Surfaces credential presence (Y/N, never the value), provider-request
    outcome counters, cache size/age/expiry counts, and the last physical-purge
    outcome.  P0-2 / Q-0099 follow-up: no descriptions, transcripts, titles, AI
    summaries, raw provider bodies, or video IDs ever appear here — only counts,
    ages, statuses, and bounded outcome categories.
    """
    import os

    from services import video_reference_cache_service, youtube_diagnostics

    embed = discord.Embed(
        title="🎬 Media (YouTube) diagnostics",
        description=(
            "Content-free operator view — counts, ages, and outcome "
            "categories only (no provider content)."
        ),
        color=discord.Color.blurple(),
    )

    # Credential presence — presence only, never the value.
    has_key = bool(os.getenv("YOUTUBE_API_KEY"))
    embed.add_field(
        name="Credential",
        value=f"`YOUTUBE_API_KEY` {'✅ present' if has_key else '❌ absent'}",
        inline=False,
    )

    # Provider-request outcome counters (process-local; reset on restart).
    counters = youtube_diagnostics.provider_outcome_counters()
    total_requests = sum(counters.values())
    counter_lines = [
        f"`{name}` — {counters[name]}" for name in youtube_diagnostics.PROVIDER_OUTCOMES
    ]
    embed.add_field(
        name=f"Provider requests (this process) — {total_requests} total",
        value="\n".join(counter_lines),
        inline=False,
    )

    # Cache health (DB aggregate, content-free).
    try:
        health = await video_reference_cache_service.cache_health()
    except Exception as exc:  # noqa: BLE001 — degrade, don't blank the page
        embed.add_field(
            name="Cache",
            value=f"*(unavailable: {type(exc).__name__})*",
            inline=False,
        )
    else:
        embed.add_field(
            name="Cache rows",
            value=(
                f"total **{health.total_rows}** · live **{health.live_rows}** · "
                f"expired **{health.expired_rows}**\n"
                f"ok **{health.ok_rows}** · error **{health.error_rows}** · "
                f"with-transcript **{health.with_transcript_rows}**"
            ),
            inline=False,
        )
        embed.add_field(
            name="Cache age / expiry",
            value=(
                f"oldest fetched {_fmt_age(health.oldest_fetched_at)} · "
                f"newest {_fmt_age(health.newest_fetched_at)}\n"
                f"next expiry {_fmt_until(health.next_expiry_at)}"
            ),
            inline=False,
        )

    # Last physical-purge outcome.
    last_purge = youtube_diagnostics.last_purge_snapshot()
    if last_purge is None:
        purge_value = "*(no purge run this process yet)*"
    else:
        status = "✅ ok" if last_purge["ok"] else "❌ failed"
        purge_value = (
            f"{status} · removed **{last_purge['rows']}** row(s) · "
            f"{_fmt_age(datetime.datetime.fromisoformat(str(last_purge['at'])))}"
        )
    embed.add_field(name="Last purge", value=purge_value, inline=False)
    return embed


async def build_economy_flow_embed(
    guild_id: int,
    *,
    days: int | None = None,
) -> discord.Embed:
    """Build the embed for ``!platform economy [days]`` — faucet/sink view.

    Aggregates the ``economy_audit_log`` already written on every coin
    movement into a per-guild faucet (mint) vs. sink (drain) summary over a
    time window: coins minted, coins drained, net flow, the minted:drained
    ratio with an inflating/draining/balanced verdict, and the per-reason
    breakdown.  Content-free — counts and coin totals only, no user IDs and
    no per-user rows (the read model aggregates ``user_id`` away).
    """
    from services import economy_flow_service

    report = await economy_flow_service.build_flow_report(guild_id, days=days)

    verdict_colors = {
        "inflating ⚠": discord.Color.orange(),
        "draining": discord.Color.blue(),
        "balanced": discord.Color.green(),
        "no activity": discord.Color.light_grey(),
    }
    embed = discord.Embed(
        title="💰 Economy faucet / sink",
        description=(
            f"Net coin flow over **{report.window_label}** "
            "(aggregated from the economy audit ledger — counts and totals "
            "only, no per-user data)."
        ),
        color=verdict_colors.get(report.verdict, discord.Color.blurple()),
    )

    ratio_text = f"{report.ratio:.2f}×" if report.ratio is not None else "—"
    net_sign = "+" if report.net >= 0 else "−"
    embed.add_field(
        name="Summary",
        value=(
            f"minted **{report.total_minted:,}** · "
            f"drained **{report.total_drained:,}**\n"
            f"net **{net_sign}{abs(report.net):,}** · "
            f"mint:drain **{ratio_text}** · "
            f"verdict **{report.verdict}**"
        ),
        inline=False,
    )

    embed.add_field(
        name=f"🟢 Faucets (mint) — {len(report.faucets)}",
        value=_format_flow_rows(report.faucets) or "*(none this window)*",
        inline=False,
    )
    embed.add_field(
        name=f"🔴 Sinks (drain) — {len(report.sinks)}",
        value=_format_flow_rows(report.sinks) or "*(none this window)*",
        inline=False,
    )
    embed.set_footer(
        text="Classified by the sign of each reason's net delta — "
        "new reasons are sorted automatically.",
    )
    return embed


def _format_flow_rows(rows, limit: int = 12) -> str:
    """Render up to *limit* ``ReasonFlow`` rows as ``reason — ±net (n moves)``."""
    lines = []
    for row in rows[:limit]:
        sign = "+" if row.net >= 0 else "−"
        lines.append(
            f"`{row.reason}` — {sign}{abs(row.net):,} ({row.movements:,} moves)",
        )
    if len(rows) > limit:
        lines.append(f"… and {len(rows) - limit} more")
    return "\n".join(lines)


# Eight block glyphs for the dependency-free sparkline (low → high). A signed
# series is mapped over its full min..max range so the zero line sits where the
# data crosses it — no external charting lib, content-free.
_SPARK_BLOCKS = "▁▂▃▄▅▆▇█"


def _sparkline(values: list[int]) -> str:
    """Render ``values`` as a unicode block sparkline (empty string if none).

    Scaled across the series' own min..max so flat data renders as one mid
    glyph rather than dividing by zero. Pure text — safe in an embed field.
    """
    if not values:
        return ""
    lo, hi = min(values), max(values)
    span = hi - lo
    if span == 0:
        return _SPARK_BLOCKS[len(_SPARK_BLOCKS) // 2] * len(values)
    last = len(_SPARK_BLOCKS) - 1
    return "".join(_SPARK_BLOCKS[round((v - lo) / span * last)] for v in values)


async def build_economy_trend_embed(
    guild_id: int,
    *,
    days: int | None = None,
) -> discord.Embed:
    """Build the embed for ``!platform economytrend [days]`` — per-day flow trend.

    The time-series companion to :func:`build_economy_flow_embed`: instead of one
    window aggregate it shows the **daily** minted / drained / net series (a
    net-flow sparkline + a recent per-day table) plus a rising/falling/steady
    read, so an operator can see whether the economy is inflating *over time*,
    not just at one snapshot.  Content-free — coin totals and counts only, no
    per-user data (the read model aggregates ``user_id`` away).
    """
    from services import economy_flow_service

    ts = await economy_flow_service.build_flow_timeseries(guild_id, days=days)

    verdict_colors = {
        "inflating ⚠": discord.Color.orange(),
        "draining": discord.Color.blue(),
        "balanced": discord.Color.green(),
        "no activity": discord.Color.light_grey(),
    }
    embed = discord.Embed(
        title="📈 Economy flow trend",
        description=(
            f"Per-day coin flow over **{ts.window_label}** "
            "(aggregated from the economy audit ledger — counts and totals "
            "only, no per-user data)."
        ),
        color=verdict_colors.get(ts.verdict, discord.Color.blurple()),
    )

    if not ts.days:
        embed.add_field(
            name="No activity",
            value="*(no coin movements recorded for this window)*",
            inline=False,
        )
        return embed

    ratio_text = f"{ts.ratio:.2f}×" if ts.ratio is not None else "—"
    net_sign = "+" if ts.net >= 0 else "−"
    embed.add_field(
        name="Summary",
        value=(
            f"minted **{ts.total_minted:,}** · "
            f"drained **{ts.total_drained:,}**\n"
            f"net **{net_sign}{abs(ts.net):,}** · "
            f"mint:drain **{ratio_text}** · "
            f"verdict **{ts.verdict}** · "
            f"trend **{ts.trend}**"
        ),
        inline=False,
    )
    embed.add_field(
        name=f"Net per day ({len(ts.days)} day{'s' if len(ts.days) != 1 else ''})",
        value=f"`{_sparkline([d.net for d in ts.days])}`",
        inline=False,
    )
    embed.add_field(
        name="Recent days",
        value=_format_day_rows(ts.days),
        inline=False,
    )
    embed.set_footer(
        text="Trend = first-half vs second-half mean daily net flow.",
    )
    return embed


def _format_day_rows(days, limit: int = 14) -> str:
    """Render the most recent *limit* ``DayFlow`` rows, newest first."""
    recent = days[-limit:]
    lines = []
    for d in reversed(recent):
        net_sign = "+" if d.net >= 0 else "−"
        lines.append(
            f"`{d.day.isoformat()}` "
            f"🟢 {d.minted:,} · 🔴 {d.drained:,} · "
            f"net {net_sign}{abs(d.net):,} ({d.movements:,})",
        )
    if len(days) > limit:
        lines.append(f"… and {len(days) - limit} earlier day(s)")
    return "\n".join(lines)


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
    from utils.db import sessions as sessions_db

    try:
        rows = await sessions_db.count_sessions_by_subsystem(subsystem or None)
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
    from utils.db import anchors as anchors_db

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
        rows = await anchors_db.count_active_anchors_by_subsystem()
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
    from services.diagnostic_helpers import _fmt_snapshot_value as _impl

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


async def _render_ticket_readiness(embed: discord.Embed, guild_id: int) -> None:
    """Append a Support-Tickets readiness line to the readiness embed.

    Bespoke on purpose: ticket config lives in its own table
    (``services.ticket_service``), not the schema-declared settings the
    aggregate readiness score reads, so tickets never appear in the
    score-driven per-subsystem list. This dedicated line both grades them
    (enabled / not set up) and doubles as a discovery nudge toward the
    Support Tickets setup step. Best-effort: a read failure is logged and
    the line is simply omitted — readiness must never fail on this add-on.
    """
    if len(embed.fields) >= _EMBED_FIELD_CAP:
        return
    from services import ticket_service

    try:
        cfg = await ticket_service.get_config(guild_id)
    except Exception:
        logger.exception("readiness: ticket config read failed (guild=%d)", guild_id)
        return

    if cfg is None or not cfg.is_set_up:
        value = (
            "🔴 **Not set up** — members can't open support tickets yet. Enable "
            "them in the **Support Tickets** setup step (`!setup`) or run "
            "`!ticketsetup @StaffRole [#log]`."
        )
    else:
        log_state = "on" if cfg.log_channel_id else "off"
        value = (
            f"🟢 **Enabled** · staff role set · transcript log {log_state} · "
            f"max {cfg.max_open_per_user} open per member"
        )
    embed.add_field(name="🎫 Support Tickets", value=value, inline=False)


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
    await _render_ticket_readiness(embed, guild_id)

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


def build_backfill_dryrun_embed(summary: DryRunSummary) -> discord.Embed:
    """Render ``!platform backfill`` (dry run) — what *would* be written.

    Pure renderer over a :class:`services.binding_backfill.DryRunSummary`
    (fields are already stringified / scrubbed). The operator reviews this,
    then runs ``!platform backfill apply`` to write the ``candidate_valid`` rows.
    """
    writable = summary.counts.get("candidate_valid", 0)
    embed = discord.Embed(
        title="🧩 Binding backfill — dry run",
        description=(
            f"**{writable}** legacy pointer(s) ready to migrate into binding rows."
            if writable
            else "Nothing to migrate — no `candidate_valid` legacy pointers."
        ),
        color=discord.Color.gold() if writable else discord.Color.green(),
    )
    counts_line = (
        ", ".join(f"{k}={v}" for k, v in sorted(summary.counts.items()) if v)
        or "*(no candidates)*"
    )
    embed.add_field(name="Classification counts", value=counts_line, inline=False)
    lines = [
        f"`{c.legacy_key}` → **{c.subsystem}.{c.binding_name}** — {c.classification}"
        + (f" (target {c.legacy_target_id})" if c.legacy_target_id else "")
        for c in summary.candidates[:12]
    ]
    embed.add_field(
        name="Candidates",
        value=_capped(lines, empty="*(none)*"),
        inline=False,
    )
    embed.set_footer(
        text="Run `!platform backfill apply` to write the candidate_valid rows "
        "(idempotent + audited).",
    )
    return embed


def build_backfill_apply_embed(result: ApplyResult) -> discord.Embed:
    """Render ``!platform backfill apply`` — the write-phase outcome.

    Pure renderer over a :class:`services.binding_backfill.ApplyResult`.
    """
    failed = result.is_failure
    written = result.write_status_counts.get("written", 0)
    embed = discord.Embed(
        title="🧩 Binding backfill — " + ("failed" if failed else "applied"),
        description=(
            f"⚠️ Backfill completed with failures — {written} written; see below."
            if failed
            else f"✅ Backfill complete — {written} binding row(s) written."
        ),
        color=discord.Color.red() if failed else discord.Color.green(),
    )
    status_line = (
        ", ".join(
            f"{k}={v}" for k, v in sorted(result.write_status_counts.items()) if v
        )
        or "*(no writes)*"
    )
    embed.add_field(name="Write status", value=status_line, inline=False)
    write_lines = [
        f"`{w.legacy_key}` — {w.write_status}" + (f" ⚠️ {w.error}" if w.error else "")
        for w in result.writes[:12]
    ]
    embed.add_field(
        name="Writes",
        value=_capped(write_lines, empty="*(none)*"),
        inline=False,
    )
    if result.error:
        embed.add_field(name="Error", value=str(result.error)[:1000], inline=False)
    embed.set_footer(text="Re-running is idempotent — already-bound rows are skipped.")
    return embed


__all__ = [
    "build_anchors_embed",
    "build_backfill_apply_embed",
    "build_backfill_dryrun_embed",
    "build_bindings_embed",
    "build_caches_embed",
    "build_command_access_diagnostic_embed",
    "build_consistency_embed",
    "build_consistency_pages",
    "build_customization_embed",
    "build_economy_flow_embed",
    "build_findings_pages",
    "build_flags_embed",
    "build_health_embed",
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
    "build_setting_detail_embed",
    "build_settings_registry_embed",
    "build_setup_readiness_embed",
    "build_slow_embed",
    "build_startup_health_embed",
    "build_status_embed",
    "build_tasks_embed",
    "build_views_embed",
]
