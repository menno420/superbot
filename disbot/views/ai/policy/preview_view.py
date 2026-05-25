"""Preview / dry-run policy resolver view (PR4B).

When an admin clicks ``Preview`` in the policy chooser, this view
asks them to pick a channel, then shows what
:func:`services.ai_natural_language_policy.resolve` would decide for
their own user identity in that channel — once with ``is_mention=True``
and once with ``is_mention=False`` — using the dry-run mode that
:class:`PolicyDecision.precedence_trace` exposes.

Dry-run mode (PR4B):

* Same resolution rules as the live path — guaranteed, since dry-run
  toggles only the trace bookkeeping; the decision logic is identical.
* Returns the precedence_trace explaining each step that fired.
* Pure read: never touches cooldown state, never writes audit. Safe
  to call from a UI without disturbing production.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

logger = logging.getLogger("bot.views.ai.policy.preview_view")

_VIEW_TIMEOUT_SECONDS = 300
_PANEL_COLOR = discord.Color.blurple()


async def _build_preview_embed(
    interaction: discord.Interaction,
    channel: Any,
) -> discord.Embed:
    """Run resolve(dry_run=True) twice (with/without mention) and
    render both decisions in one embed.
    """
    from services import ai_natural_language_policy as nlp
    from services import xp_service

    guild = interaction.guild
    member = interaction.user
    if guild is None:
        # Caller is supposed to have checked; defensive fallback so
        # we never deref None at .id below.
        raise RuntimeError("preview_view requires a guild context")

    record = None
    try:
        record = await xp_service.get_user_record(guild.id, int(member.id))
    except Exception as exc:  # noqa: BLE001 — XP read is best-effort here
        logger.debug("preview_view: xp lookup failed (%s)", exc)
    user_level = int(getattr(record, "level", 0) or 0)
    is_fresh_user = record is None

    role_ids = tuple(
        int(r.id) for r in getattr(member, "roles", ()) if r.id != guild.id
    )
    category_id = getattr(channel, "category_id", None)
    if category_id is not None:
        category_id = int(category_id)

    embed = discord.Embed(
        title="AI policy preview",
        description=(
            f"Resolving for {getattr(channel, 'mention', f'<#{channel.id}>')} "
            f"as {member.mention} (level `{user_level}`, "
            f"{len(role_ids)} role(s)).\n"
            "_Dry-run only — no cooldown is touched, no audit is written._"
        ),
        color=_PANEL_COLOR,
    )

    for label, is_mention in (
        ("Without mention", False),
        ("With @mention", True),
    ):
        ctx = nlp.MessageContext(
            guild_id=int(guild.id),
            channel_id=int(channel.id),
            category_id=category_id,
            user_id=int(member.id),
            user_level=user_level,
            user_role_ids=role_ids,
            is_mention=is_mention,
            is_fresh_user=is_fresh_user,
        )
        decision = await nlp.resolve(ctx, dry_run=True)
        verdict = (
            "✅ **allowed**"
            if decision.allowed
            else f"❌ **denied** · `{decision.reason_code.value}`"
        )
        trace_lines = "\n".join(f"· {step}" for step in decision.precedence_trace)
        body = (
            f"{verdict}\n"
            f"min_level=`{decision.effective_min_level}` · "
            f"cooldown=`{decision.effective_cooldown}s`\n"
            f"{trace_lines}"
        )
        # Discord field value cap is 1024; truncate the trace if needed.
        if len(body) > 1024:
            body = body[:1020] + "\n…"
        embed.add_field(name=label, value=body, inline=False)

    embed.set_footer(text="dry_run=True · administrator-only")
    return embed


class _PreviewChannelSelect(discord.ui.ChannelSelect):
    """Pick a channel to preview the resolver against."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a channel to preview…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ Preview requires a guild context.",
                ephemeral=True,
            )
            return
        # Promote AppCommandChannel → full GuildChannel where possible
        # so role/category context is accurate.
        from core.runtime import guild_resources

        channel: Any = picked
        full = guild_resources.resolve_channel(
            interaction.guild,
            channel_id=picked.id,
            kind="text",
        )
        if full is not None:
            channel = full

        embed = await _build_preview_embed(interaction, channel)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class PreviewChannelSelectView(discord.ui.View):
    """Ephemeral channel-picker that runs the dry-run preview."""

    def __init__(self) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT_SECONDS)
        self.add_item(_PreviewChannelSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        perms = getattr(interaction.user, "guild_permissions", None)
        if perms is None or not getattr(perms, "administrator", False):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return False
        return True


__all__ = [
    "PreviewChannelSelectView",
    "_build_preview_embed",
]
