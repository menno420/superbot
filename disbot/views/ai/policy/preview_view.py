"""Preview / dry-run policy resolver view.

When an admin clicks ``Preview`` in the policy chooser, this view
asks them to pick a channel, then shows what
:func:`services.ai_natural_language_policy.resolve` would decide for
their own user identity in that channel — once with ``is_mention=True``
and once with ``is_mention=False`` — using the dry-run mode that
:class:`PolicyDecision.precedence_trace` exposes.

Dry-run mode:

* Same resolution rules as the live path — guaranteed, since dry-run
  toggles only the trace bookkeeping; the decision logic is identical.
* Returns the precedence_trace explaining each step that fired plus
  the typed ``effective_mode`` / ``effective_source`` fields, which the
  embed renders as a one-line summary above the trace bullets.
* Pure read: never touches cooldown state, never writes audit. Safe
  to call from a UI without disturbing production.
"""

from __future__ import annotations

import logging
from typing import Any

import discord

from core.runtime.ai.contracts import PolicyDenialReason

logger = logging.getLogger("bot.views.ai.policy.preview_view")

_VIEW_TIMEOUT_SECONDS = 300
_PANEL_COLOR = discord.Color.blurple()

# Reasons that signal the guild has not yet configured AI or has the
# hard kill switch on — these are "red" because no scoped override can
# resurrect AI in these cases.
_HARD_KILL_REASONS = frozenset(
    {
        PolicyDenialReason.AI_GLOBALLY_DISABLED,
        PolicyDenialReason.GUILD_NOT_CONFIGURED,
    },
)

# Reasons sourced from the guild NL baseline — admins can override these
# per channel/category, so the embed flags them as "amber" baseline state
# rather than the red hard-kill state.
_BASELINE_DISABLED_REASONS = frozenset(
    {PolicyDenialReason.AI_NL_DISABLED_FOR_GUILD},
)


async def build_effective_policy_embed(
    *,
    guild: discord.Guild,
    member: Any,
    channel: Any,
    snapshot: Any = None,
    title: str = "AI policy preview",
) -> discord.Embed:
    """Run ``resolve(dry_run=True)`` twice (with/without mention) and
    render both decisions in one embed.

    Reused by:

    * the policy-chooser **Preview** button (still labelled
      ``Effective policy`` after PR-2; the channel-select picks a
      target channel and renders this same embed).
    * the ``!ai policy [#channel]`` prefix command + slash twin.

    ``snapshot`` is the optional :class:`AIConfigSnapshot` from
    :mod:`services.ai_config_projection_service`. When supplied, the
    embed adds an ancillary footer line listing override counts +
    provider/model. The resolved precedence still comes from the
    resolver dry-run — the snapshot is never used to compute "is the
    channel reachable?".
    """
    from services import ai_natural_language_policy as nlp
    from services import xp_service

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
        title=title,
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
        verdict = _render_verdict(decision)
        effective_summary = _render_effective_summary(decision)
        trace_lines = "\n".join(f"· {step}" for step in decision.precedence_trace)
        body = f"{verdict}\n{effective_summary}\n{trace_lines}"
        # Discord field value cap is 1024; truncate the trace if needed.
        if len(body) > 1024:
            body = body[:1020] + "\n…"
        embed.add_field(name=label, value=body, inline=False)

    if snapshot is not None:
        _attach_ancillary_field(embed, snapshot)

    embed.set_footer(text="dry_run=True · administrator-only")
    return embed


async def _build_preview_embed(
    interaction: discord.Interaction,
    channel: Any,
) -> discord.Embed:
    """Back-compat shim — adapts the original interaction-coupled
    signature to :func:`build_effective_policy_embed`.

    Retained so existing tests + internal callers continue to work.
    New code should call :func:`build_effective_policy_embed` directly
    with the explicit ``guild`` / ``member`` keyword arguments.
    """
    guild = interaction.guild
    if guild is None:
        raise RuntimeError("preview_view requires a guild context")
    return await build_effective_policy_embed(
        guild=guild,
        member=interaction.user,
        channel=channel,
    )


def _attach_ancillary_field(embed: discord.Embed, snapshot: Any) -> None:
    """Add an "Overrides + provider" field sourced from the snapshot.

    The snapshot is read-only orchestration; this helper renders the
    counts and provider/model without re-querying any DB. Resolver
    precedence comes from the dry-run above, never from the snapshot.
    """
    policy = getattr(snapshot, "policy", None)
    provider = getattr(snapshot, "provider", None)
    if policy is None and provider is None:
        return
    parts: list[str] = []
    if policy is not None:
        parts.append(
            f"Overrides: {policy.channel_override_count} channel · "
            f"{policy.category_override_count} category · "
            f"{policy.role_override_count} role",
        )
        model = getattr(policy, "default_model", None) or "—"
        provider_name = (
            getattr(policy, "default_provider", None)
            or (getattr(provider, "default_provider", None) if provider else None)
            or "—"
        )
        parts.append(f"Provider: `{provider_name}` · model: `{model}`")
    elif provider is not None:
        parts.append(
            f"Provider: `{getattr(provider, 'default_provider', None) or '—'}`",
        )
    embed.add_field(
        name="Context",
        value="\n".join(parts) or "—",
        inline=False,
    )


def _render_verdict(decision: Any) -> str:
    """Render the one-line verdict, distinguishing hard kill from baseline."""
    if decision.allowed:
        return "✅ **allowed**"
    reason = decision.reason_code
    if reason in _HARD_KILL_REASONS:
        marker = "⛔"
        label = "hard-disabled"
    elif reason in _BASELINE_DISABLED_REASONS:
        marker = "🟡"
        label = "baseline-denied (override-able)"
    else:
        marker = "❌"
        label = "denied"
    return f"{marker} **{label}** · `{reason.value}`"


def _render_effective_summary(decision: Any) -> str:
    """Render the compact effective-policy line for the embed."""
    source = decision.effective_source or "—"
    mode = decision.effective_mode or "—"
    return (
        f"effective: source=`{source}` mode=`{mode}` · "
        f"min_level=`{decision.effective_min_level}` · "
        f"cooldown=`{decision.effective_cooldown}s`"
    )


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

        embed = await build_effective_policy_embed(
            guild=interaction.guild,
            member=interaction.user,
            channel=channel,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class PreviewChannelSelectView(discord.ui.View):
    """Ephemeral channel-picker that runs the dry-run preview."""

    def __init__(self) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT_SECONDS)
        self.add_item(_PreviewChannelSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Canonical admin gate — honours the platform owner (Q-0212).
        from views.base import interaction_is_admin

        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "❌ Administrator permission required.",
                ephemeral=True,
            )
            return False
        return True


__all__ = [
    "PreviewChannelSelectView",
    "build_effective_policy_embed",
]
