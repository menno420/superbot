"""RecentChangesView — recent rows from the settings audit log (S5).

Read-only view over the ``settings_mutation_audit`` table populated
by :class:`services.settings_mutation.SettingsMutationPipeline`
(S4).  Up to 10 most recent rows for the calling guild are
rendered.

Gracefully degrades when:

* The migration has not been applied yet (no table) — the view
  reports the table as absent rather than raising.
* The pipeline has never been called — the table exists but is
  empty.  The view renders an empty-state message.
"""

from __future__ import annotations

import logging

import discord

from views.base import HubView

logger = logging.getLogger("bot.views.settings.audit_view")


_RECENT_LIMIT = 10


async def build_audit_embed(
    interaction: discord.Interaction,
) -> discord.Embed:
    embed = discord.Embed(
        title="🕒 Recent settings changes",
        description=(
            "Most recent rows from `settings_mutation_audit` (S4).  "
            "Until the S6 edit flow lands, this table is populated only "
            "by REPL or scripted writes; production cogs still call "
            "`db.set_setting` directly (allowlisted per the AST invariant).\n"
            "_Read-only · S5._"
        ),
        color=discord.Color.blurple(),
    )

    guild_id = interaction.guild_id
    if guild_id is None:
        embed.add_field(
            name="Result",
            value="*Run this from within a guild — DM has no audit history.*",
            inline=False,
        )
        return embed

    try:
        from utils.db import settings_audit

        rows = await settings_audit.list_recent_for_guild(
            guild_id,
            limit=_RECENT_LIMIT,
        )
    except Exception as exc:  # noqa: BLE001 — soft-fail; usually missing table
        logger.warning(
            "RecentChangesView: settings_audit query raised %s",
            exc,
            exc_info=True,
        )
        embed.add_field(
            name="Audit table",
            value=(
                f"*Could not read `settings_mutation_audit` — "
                f"`{type(exc).__name__}: {exc!s:.100}`.  "
                "Migration 029 may not have been applied yet.*"
            ),
            inline=False,
        )
        return embed

    if not rows:
        embed.add_field(
            name="Result",
            value="*No audit rows for this guild yet.*",
            inline=False,
        )
        return embed

    lines: list[str] = []
    for row in rows:
        ts = row.get("at")
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%SZ") if ts is not None else "—"
        prev = row.get("prev_value_raw")
        new = row.get("new_value_raw")
        actor = row.get("actor_id")
        actor_type = row.get("actor_type", "user")
        lines.append(
            f"`{ts_str}` `{row['subsystem']}.{row['name']}` "
            f"= `{new!r}` (was `{prev!r}`) "
            f"by `{actor_type}` `{actor}`",
        )
    embed.add_field(
        name=f"Last {len(rows)} change(s)",
        value="\n".join(lines)[:1024],
        inline=False,
    )
    embed.set_footer(text=f"settings_mutation_audit · guild_id={guild_id}")
    return embed


class _BackToHubButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Back to Hub",
            style=discord.ButtonStyle.secondary,
            emoji="↩",
            custom_id="settings_audit.back",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from views.settings.hub import SettingsHubView

        view = SettingsHubView(interaction.user)
        await interaction.response.edit_message(
            embed=SettingsHubView.build_embed(),
            view=view,
        )


class RecentChangesView(HubView):
    """Read-only diagnostic panel rendering the last N audit rows."""

    def __init__(self, author) -> None:
        super().__init__(author)
        self.add_item(_BackToHubButton())


__all__ = ["RecentChangesView", "build_audit_embed"]
