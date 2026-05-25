"""Support-report draft view (PR-H).

Read-only aggregator: composes a copy-pasteable code-block draft
from the most recent ``ai_decision_audit`` rows for the caller's
guild plus the bot's identifiers. **No outbound delivery of any
kind** — the operator copies the block into whatever support channel
they use (email, ticket, GitHub issue, etc.).

The draft contains only fields already present in
``ai_decision_audit``. Message bodies are never included; the
audit table holds the join key (``message_id``) only, so privacy is
preserved by construction.
"""

from __future__ import annotations

import logging
import platform
import sys
from typing import Any

import discord

logger = logging.getLogger("bot.views.ai.support_report")


_MAX_AUDIT_ROWS_IN_REPORT = 10


def _admin(user: Any) -> bool:
    perms = getattr(user, "guild_permissions", None)
    return perms is not None and getattr(perms, "administrator", False)


async def build_support_report_draft(
    *,
    guild_id: int,
    bot_user_id: int | None,
    snapshot: Any = None,
) -> str:
    """Return a fenced markdown code block summarising recent audit
    rows for the guild.

    Every line uses only the columns ``ai_decision_audit`` already
    holds: no message content, no DMs, no user identifiers beyond
    the user ids already in the audit row.

    ``snapshot`` is the optional :class:`AIConfigSnapshot` from
    :mod:`services.ai_config_projection_service`. When supplied, the
    draft header adds operator-readable provider / model / memory /
    projection-drift lines so the report is self-contained without
    requiring the recipient to re-query the runtime. The audit-row
    body is unchanged either way.
    """
    from services import ai_decision_audit_service

    rows = await ai_decision_audit_service.query(guild_id, limit=50)
    rows = rows[:_MAX_AUDIT_ROWS_IN_REPORT]

    lines: list[str] = []
    lines.append("```")
    lines.append("# SuperBot AI support report (draft — copy-paste only)")
    lines.append(f"# guild_id: {guild_id}")
    if bot_user_id is not None:
        lines.append(f"# bot_user_id: {bot_user_id}")
    lines.append(f"# python: {sys.version.split()[0]} on {platform.system()}")
    lines.extend(_snapshot_header_lines(snapshot))
    lines.append("# fields below come ONLY from ai_decision_audit; no message text.")
    lines.append("")
    if not rows:
        lines.append("(no recent audit rows for this guild)")
    else:
        for r in rows:
            eff_source = r.get("effective_source") or "—"
            eff_mode = r.get("effective_mode") or "—"
            lines.append(
                f"- decision={r.get('decision')} reason={r.get('reason_code')} "
                f"task={r.get('task') or '—'} route={r.get('route') or '—'} "
                f"provider={r.get('provider') or '—'} model={r.get('model') or '—'} "
                f"effective={eff_source}/{eff_mode}",
            )
    lines.append("```")
    return "\n".join(lines)


def _snapshot_header_lines(snapshot: Any) -> list[str]:
    """Header lines sourced from the snapshot. Empty when no snapshot.

    Renders provider / model / memory mode / projection drift status
    as ``# key: value`` lines that fit inside the draft's existing
    comment block. All fields tolerate ``None`` and render ``—`` per
    the snapshot's general contract.
    """
    if snapshot is None:
        return []
    out: list[str] = []
    provider = getattr(snapshot, "provider", None)
    policy = getattr(snapshot, "policy", None)
    memory = getattr(snapshot, "memory", None)
    projection = getattr(snapshot, "projection", None)
    if provider is not None:
        provider_name = (
            getattr(policy, "default_provider", None)
            or getattr(provider, "default_provider", None)
            or "—"
        )
        model = getattr(policy, "default_model", None) or "—"
        out.append(f"# provider: {provider_name}")
        out.append(f"# model: {model}")
        if getattr(provider, "degraded", False):
            out.append(
                f"# gateway: degraded "
                f"(last_error={provider.last_error_type or 'unknown'})",
            )
    if memory is not None:
        mode = (
            f"minimal ({memory.min_floor_turns}-turn floor)"
            if memory.window_minutes <= 0
            else f"{memory.window_minutes} min"
        )
        out.append(
            f"# memory: {mode}, scan={'on' if memory.scan_enabled else 'off'}",
        )
    drift_count = (
        int(getattr(projection, "drift_count", 0) or 0) if projection is not None else 0
    )
    if drift_count:
        out.append(
            f"# projection_drift: {drift_count} field(s) disagree with typed policy",
        )
    return out


async def build_support_report_embed(
    *,
    guild_id: int,
    bot_user_id: int | None,
    snapshot: Any = None,
) -> discord.Embed:
    """Wrap :func:`build_support_report_draft` in an explanatory embed."""
    draft = await build_support_report_draft(
        guild_id=guild_id,
        bot_user_id=bot_user_id,
        snapshot=snapshot,
    )
    embed = discord.Embed(
        title="📋 AI Support report — draft",
        description=(
            "Copy the code block below into your support channel. "
            "**This bot does NOT send anything outbound** — you must "
            "paste it yourself wherever support requests are handled."
        ),
        color=discord.Color.blurple(),
    )
    # Discord field values cap at 1024 chars; the draft is bounded
    # by _MAX_AUDIT_ROWS_IN_REPORT but we still defensively truncate.
    body = draft if len(draft) <= 1000 else draft[:999] + "…\n```"
    embed.add_field(name="Draft", value=body, inline=False)
    embed.set_footer(
        text=(
            "Privacy: no message text is included — only audit rows. "
            "No network egress on this code path."
        ),
    )
    return embed


__all__ = [
    "build_support_report_draft",
    "build_support_report_embed",
]
