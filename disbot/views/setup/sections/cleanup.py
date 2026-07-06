"""Cleanup inheritance section — drafts per-scope cleanup levels.

Stages ``SetupOperation(kind="set_cleanup_policy", ...)`` drafts for
the server-wide level plus optional category and channel overrides.
The existing :mod:`governance.cleanup` resolver continues to be
authoritative at read time (``thread > channel > category > guild >
fallback``); the wizard only stages writes.

Levels map to ``cleanup_policies`` columns via
:mod:`services.cleanup_levels`; Final Review's dispatcher routes the
staged ``set_cleanup_policy`` op through
:func:`governance.writes.set_cleanup_policy_for_scope`, which writes
the policy row + governance audit row + emits
``audit.action_recorded`` in one transaction.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_draft, setup_session
from services.cleanup_levels import LEVELS
from services.cleanup_levels import columns_for_level as level_metadata
from services.setup_operations import SetupOperation
from services.setup_sections import REGISTRY, SetupSection
from views.base import BaseView

if TYPE_CHECKING:
    from views.setup.hub import SetupHubView

logger = logging.getLogger("bot.views.setup.sections.cleanup")

SLUG = "cleanup"


SCOPE_OPTIONS: list[discord.SelectOption] = [
    discord.SelectOption(
        label="Server default",
        value="guild",
        description="Cleanup level for every channel without an override.",
        emoji="🌐",
    ),
    discord.SelectOption(
        label="Category override",
        value="category",
        description="Override one category — channels in it inherit unless overridden.",
        emoji="📁",
    ),
    discord.SelectOption(
        label="Channel override",
        value="channel",
        description="Override one specific channel.",
        emoji="📡",
    ),
]


def _level_options() -> list[discord.SelectOption]:
    return [
        discord.SelectOption(
            label=name,
            value=name,
            description=(
                f"after={values['delete_after_seconds']}s · "
                f"invalid={'yes' if values['delete_invalid_commands'] else 'no'} · "
                f"failed={'yes' if values['delete_failed_commands'] else 'no'}"
            ),
        )
        for name, values in LEVELS.items()
    ]


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


def build_cleanup_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🧹 Cleanup inheritance",
        description=(
            "Configure cleanup behaviour at three scopes.  The resolver "
            "walks **thread → channel → category → server → default**, so "
            "channel overrides win over category overrides which win "
            "over the server default.  Each pick stages a "
            "`set_cleanup_policy` operation — Final review applies "
            "them all in order."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Levels",
        value=(
            "• **Off** — disabled (after=0s)\n"
            "• **Light** — delete invalid commands only (after=10s)\n"
            "• **Standard** — delete invalid + failed (after=5s)\n"
            "• **Strict** — delete invalid + failed (after=2s)"
        ),
        inline=False,
    )
    embed.set_footer(text="Pick a scope below, then pick a level for that scope.")
    return embed


# ---------------------------------------------------------------------------
# Level selects per scope
# ---------------------------------------------------------------------------


class _GuildLevelSelect(discord.ui.Select):
    """Guild-default level picker.  Drafts on pick."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick the server-wide level…",
            min_values=1,
            max_values=1,
            options=_level_options(),
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        level = self.values[0]
        await _stage_cleanup_policy(
            interaction,
            scope_kind="guild",
            scope_id=None,
            scope_name="guild",
            level=level,
        )


class _CategoryLevelSelect(discord.ui.Select):
    """Category-override picker — picks the level for one specific
    category id.  The caller pre-selected the category and stashed
    its id + name on the view.
    """

    def __init__(self, category_id: int, category_name: str) -> None:
        super().__init__(
            placeholder=f"Level for category {category_name}…",
            min_values=1,
            max_values=1,
            options=_level_options(),
        )
        self._category_id = category_id
        self._category_name = category_name

    async def callback(self, interaction: discord.Interaction) -> None:
        level = self.values[0]
        await _stage_cleanup_policy(
            interaction,
            scope_kind="category",
            scope_id=self._category_id,
            scope_name=self._category_name,
            level=level,
        )


class _ChannelLevelSelect(discord.ui.Select):
    def __init__(self, channel_id: int, channel_name: str) -> None:
        super().__init__(
            placeholder=f"Level for channel #{channel_name}…",
            min_values=1,
            max_values=1,
            options=_level_options(),
        )
        self._channel_id = channel_id
        self._channel_name = channel_name

    async def callback(self, interaction: discord.Interaction) -> None:
        level = self.values[0]
        await _stage_cleanup_policy(
            interaction,
            scope_kind="channel",
            scope_id=self._channel_id,
            scope_name=f"#{self._channel_name}",
            level=level,
        )


# ---------------------------------------------------------------------------
# Scope-picker view
# ---------------------------------------------------------------------------


class _ScopeSelect(discord.ui.Select):
    """Initial scope picker — guild / category / channel."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a scope to set cleanup for…",
            min_values=1,
            max_values=1,
            options=SCOPE_OPTIONS,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        scope = self.values[0]
        if scope == "guild":
            view = BaseView(interaction.user, public=False, timeout=120)
            view.add_item(_GuildLevelSelect())
            await interaction.response.send_message(
                "Pick the server-wide cleanup level:",
                view=view,
                ephemeral=True,
            )
            return
        if scope == "category":
            view = BaseView(interaction.user, public=False, timeout=120)
            view.add_item(_CategoryPickSelect())
            await interaction.response.send_message(
                "Pick a category to override:",
                view=view,
                ephemeral=True,
            )
            return
        if scope == "channel":
            view = BaseView(interaction.user, public=False, timeout=120)
            view.add_item(_ChannelPickSelect())
            await interaction.response.send_message(
                "Pick a channel to override:",
                view=view,
                ephemeral=True,
            )
            return


class _CategoryPickSelect(discord.ui.ChannelSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a category…",
            channel_types=[discord.ChannelType.category],
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        view = BaseView(interaction.user, public=False, timeout=120)
        view.add_item(_CategoryLevelSelect(picked.id, picked.name))
        await interaction.response.send_message(
            f"Pick the cleanup level for category **{picked.name}**:",
            view=view,
            ephemeral=True,
        )


class _ChannelPickSelect(discord.ui.ChannelSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a channel…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        view = BaseView(interaction.user, public=False, timeout=120)
        view.add_item(_ChannelLevelSelect(picked.id, picked.name))
        await interaction.response.send_message(
            f"Pick the cleanup level for #{picked.name}:",
            view=view,
            ephemeral=True,
        )


class _ProfileSelect(discord.ui.Select):
    """Batch picker: apply a named cleanup profile in one click.

    Stages every ``set_cleanup_policy`` op the profile's builder
    returns. The hub status badge then reflects RECOMMENDED for the
    cleanup section because every staged op carries
    ``metadata.source="cleanup_profile:<slug>"`` (recognised by the
    same status logic as the section-card recommended path —
    treated as customized, since the operator chose a non-default
    profile).
    """

    def __init__(self) -> None:
        from services.cleanup_profiles import PROFILES

        options = [
            discord.SelectOption(
                label=profile.display_name,
                value=profile.slug,
                description=profile.description[:100],
            )
            for profile in PROFILES.values()
        ]
        super().__init__(
            placeholder="Apply a cleanup profile (batch action)…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="cleanup_section_profile",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from services.cleanup_profiles import apply_profile, get_profile

        guild = interaction.guild
        if guild is None or interaction.guild_id is None:
            await interaction.response.send_message(
                "This can only be used in a server.",
                ephemeral=True,
            )
            return
        slug = self.values[0]
        profile = get_profile(slug)
        if profile is None:
            await interaction.response.send_message(
                f"Unknown cleanup profile `{slug}`.",
                ephemeral=True,
            )
            return
        try:
            ops = apply_profile(slug, guild)
        except Exception:
            logger.exception(
                "cleanup: apply_profile failed (slug=%s)",
                slug,
            )
            await interaction.response.send_message(
                "Could not build the cleanup profile — see logs.",
                ephemeral=True,
            )
            return
        if not ops:
            await interaction.response.send_message(
                f"Profile `{slug}` produced no operations.",
                ephemeral=True,
            )
            return

        staged = 0
        for op in ops:
            try:
                await setup_draft.append(
                    op,
                    guild_id=interaction.guild_id,
                    actor_id=interaction.user.id,
                    label=f"[profile:{slug}] cleanup.{op.target_kind}({op.target_name}) = {op.value}",
                    metadata={
                        "source": f"cleanup_profile:{slug}",
                        "confidence": "high",
                        "reason": f"Profile `{profile.display_name}`",
                        "risk": "low",
                        "rollback_note": (
                            "Re-stage with a different profile or delete "
                            "the cleanup_policies rows manually."
                        ),
                    },
                )
                staged += 1
            except Exception:
                logger.exception(
                    "cleanup: profile append failed (slug=%s, target=%s)",
                    slug,
                    op.target_id,
                )

        try:
            await setup_session.mark_in_progress(interaction.guild_id, step=SLUG)
        except Exception:
            logger.exception("cleanup: mark_in_progress failed (profile)")

        try:
            pending = await setup_draft.count(interaction.guild_id)
        except Exception:
            logger.exception("cleanup: setup_draft.count failed (profile)")
            pending = 0

        word = "operation" if staged == 1 else "operations"
        await interaction.response.send_message(
            f"✅ Staged **{staged} {word}** for profile "
            f"`{profile.display_name}`. Pending operations: **{pending}**.",
            ephemeral=True,
        )


class CleanupSectionView(BaseView):
    """Entry view — hosts the scope-picker dropdown + a profile-batch picker.

    The scope picker is the per-channel/category/guild manual path
    (already in the section card's Customize flow). The profile
    picker is the new "I just want safe defaults across many scopes"
    batch shortcut.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self.add_item(_ScopeSelect())
        self.add_item(_ProfileSelect())


# ---------------------------------------------------------------------------
# Draft staging
# ---------------------------------------------------------------------------


async def _stage_cleanup_policy(
    interaction: discord.Interaction,
    *,
    scope_kind: str,
    scope_id: int | None,
    scope_name: str,
    level: str,
) -> None:
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This can only be used in a server.",
            ephemeral=True,
        )
        return
    if level not in LEVELS:
        await interaction.response.send_message(
            f"Unknown level `{level}`.",
            ephemeral=True,
        )
        return

    op = SetupOperation(
        kind="set_cleanup_policy",
        subsystem="cleanup",
        target_id=scope_id,
        target_name=scope_name,
        target_kind=scope_kind,
        value=level,
        metadata={
            "source": "manual",
            "confidence": "high",
            "reason": (f"Operator chose `{level}` for {scope_kind} `{scope_name}`"),
            "risk": "low",
            "rollback_note": (
                f"Re-stage with a different level or "
                f"delete the cleanup_policies row for "
                f"({scope_kind}, {scope_id})"
            ),
        },
    )
    label = f"cleanup.{scope_kind}({scope_name}) = {level}"
    try:
        await setup_draft.append(
            op,
            guild_id=guild.id,
            actor_id=interaction.user.id,
            label=label,
        )
    except Exception:
        logger.exception("cleanup: setup_draft.append failed")
        await interaction.response.send_message(
            "Could not stage the cleanup policy — see logs.",
            ephemeral=True,
        )
        return

    try:
        await setup_session.mark_in_progress(guild.id, step=SLUG)
    except Exception:
        logger.exception("cleanup: mark_in_progress failed")

    try:
        pending = await setup_draft.count(guild.id)
    except Exception:
        logger.exception("cleanup: setup_draft.count failed")
        pending = 0

    await interaction.response.send_message(
        (f"✅ Staged for Final review: `{label}`.  Pending operations: **{pending}**."),
        ephemeral=True,
    )


# ---------------------------------------------------------------------------
# Section entry point
# ---------------------------------------------------------------------------


async def _customize_run(
    interaction: discord.Interaction,
    hub: SetupHubView | None,
) -> None:
    """Open the detailed cleanup picker (the card's Customize target)."""
    del hub
    guild = interaction.guild
    if guild is None:
        await interaction.response.send_message(
            "This can only be used in a server.",
            ephemeral=True,
        )
        return

    embed = build_cleanup_embed()
    view = CleanupSectionView(interaction.user)
    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True,
    )


async def _recommended_cleanup_ops(
    guild: discord.Guild,
) -> list[SetupOperation]:
    """Default cleanup recommendation: Light cleanup at guild scope.

    Light deletes invalid commands after 10s and leaves failed-command
    messages alone — a safe baseline for most servers.
    """
    return [
        SetupOperation(
            kind="set_cleanup_policy",
            subsystem="cleanup",
            binding_name=None,
            setting_name=None,
            target_id=guild.id,
            target_name=guild.name,
            target_kind="guild",
            value="Light",
        ),
    ]


async def run(interaction: discord.Interaction, hub: SetupHubView) -> None:
    """Cleanup section entry — shows the section card."""
    from views.setup.section_card import show

    detected = "Resolver walks thread → channel → category → server → default."
    # ``recommended_ops_builder`` is read from the registered
    # ``SetupSection`` field by ``section_card.show`` — no need to
    # pass it explicitly here.
    await show(
        interaction,
        hub=hub,
        section=REGISTRY.get(SLUG),  # type: ignore[arg-type]
        detected_state=detected,
        on_customize=_customize_run,
    )


async def _build_detail_embed(
    guild: discord.Guild,
    *,
    session: object = None,
    draft_rows: object = None,
) -> discord.Embed:
    """Wizard-native detail embed for the cleanup step."""
    del guild, session, draft_rows
    return build_cleanup_embed()


def _build_detail_view(
    author: discord.Member | discord.User,
    *,
    section: SetupSection,
    guild: discord.Guild,
    session: object = None,
) -> CleanupSectionView:
    """Wizard-native detail view for the cleanup step."""
    del section, guild, session
    return CleanupSectionView(author)


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Cleanup inheritance",
        style=discord.ButtonStyle.secondary,
        run=run,
        emoji="🧹",
        order=60,
        op_kinds=frozenset({"set_cleanup_policy"}),
        description_if_skipped=(
            "Cleanup stays at the current server default. Commands will not "
            "be aggressively deleted unless existing policies already say "
            "so. You can revisit cleanup later from `!settings`."
        ),
        # PR 3a: per-channel cleanup scopes are an advanced concern, not a
        # first-run essential — demoted to advanced-only (cog_routing already is).
        depths=frozenset({"advanced"}),
        recommended_ops_builder=_recommended_cleanup_ops,
        customize=_customize_run,
        detail_embed_builder=_build_detail_embed,
        detail_view_builder=_build_detail_view,
    ),
)


__all__ = [
    "CleanupSectionView",
    "LEVELS",
    "SLUG",
    "build_cleanup_embed",
    "level_metadata",
    "run",
]
