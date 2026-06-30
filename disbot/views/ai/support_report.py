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
    # Canonical admin gate — honours the platform owner (config.BOT_OWNER_USER_ID).
    from views.base import member_is_admin

    return member_is_admin(user)


async def build_support_report_draft(
    *,
    guild_id: int,
    bot_user_id: int | None,
) -> str:
    """Return a fenced markdown code block summarising recent audit
    rows for the guild.

    Every line uses only the columns ``ai_decision_audit`` already
    holds: no message content, no DMs, no user identifiers beyond
    the user ids already in the audit row.
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
    lines.append("# fields below come ONLY from ai_decision_audit; no message text.")
    lines.append("")
    if not rows:
        lines.append("(no recent audit rows for this guild)")
    else:
        for r in rows:
            lines.append(
                f"- decision={r.get('decision')} reason={r.get('reason_code')} "
                f"task={r.get('task') or '—'} route={r.get('route') or '—'} "
                f"provider={r.get('provider') or '—'} model={r.get('model') or '—'}",
            )
    lines.append("```")
    return "\n".join(lines)


async def build_support_report_embed(
    *,
    guild_id: int,
    bot_user_id: int | None,
) -> discord.Embed:
    """Wrap :func:`build_support_report_draft` in an explanatory embed."""
    draft = await build_support_report_draft(
        guild_id=guild_id,
        bot_user_id=bot_user_id,
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
