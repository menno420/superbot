"""Tools & Workflows write UI — pick an orchestration profile per scope.

Three scopes (guild / channel / category), each a two-or-one step flow that
ends in a ``discord.ui.Select`` of the built-in orchestration presets. Choosing
one calls the audited :mod:`services.ai_orchestration_mutation` seam, which
enforces the admin gate, validates the key against the built-in presets,
invalidates the resolver cache, and emits ``ai.orchestration.*_changed``.

A ``Select`` (not a modal) is the right control here: the valid values are a
fixed, known list of presets, and a modal cannot contain a select. Each preset
option carries its label + a truncated description so operators choose by intent
without learning the underlying tool-choice / budget knobs.
"""

from __future__ import annotations

import logging

import discord

from services import ai_orchestration_presets

logger = logging.getLogger("bot.views.ai.tools.scope_view")

_VIEW_TIMEOUT_SECONDS = 180

# Sentinel option value meaning "remove the override at this scope" (inherit the
# next layer). Distinct from any preset key.
_CLEAR_VALUE = "__inherit__"


def _profile_options(*, include_clear: bool) -> list[discord.SelectOption]:
    """Build the preset Select options (+ an optional clear/inherit option)."""
    options: list[discord.SelectOption] = []
    for profile in ai_orchestration_presets.all_presets():
        options.append(
            discord.SelectOption(
                label=profile.label[:100],
                value=profile.key,
                description=profile.description[:100],
            ),
        )
    if include_clear:
        options.append(
            discord.SelectOption(
                label="Clear (inherit)",
                value=_CLEAR_VALUE,
                description="Remove this scope's profile; inherit the next layer.",
            ),
        )
    return options


class _ProfileSelect(discord.ui.Select):
    """Select one orchestration preset and write it to the chosen scope."""

    def __init__(self, *, scope: str, target_id: int | None, target_label: str) -> None:
        # ``scope`` is "guild" | "channel" | "category"; ``target_id`` is the
        # channel/category id (None for guild). Channel/category may clear.
        self._scope = scope
        self._target_id = target_id
        self._target_label = target_label
        super().__init__(
            placeholder="Pick an orchestration profile…",
            min_values=1,
            max_values=1,
            options=_profile_options(include_clear=scope != "guild"),
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        from services import ai_orchestration_mutation as mut

        if interaction.guild is None:
            await interaction.response.send_message(
                "❌ This requires a guild context.",
                ephemeral=True,
            )
            return

        chosen = self.values[0]
        profile_key: str | None = None if chosen == _CLEAR_VALUE else chosen

        try:
            if self._scope == "guild":
                result = await mut.set_guild_orchestration(
                    interaction.guild.id,
                    profile_key=profile_key,
                    actor=interaction.user,
                )
            elif self._scope == "channel":
                result = await mut.set_channel_orchestration(
                    interaction.guild.id,
                    int(self._target_id),  # type: ignore[arg-type]
                    profile_key=profile_key,
                    actor=interaction.user,
                )
            else:  # category
                result = await mut.set_category_orchestration(
                    interaction.guild.id,
                    int(self._target_id),  # type: ignore[arg-type]
                    profile_key=profile_key,
                    actor=interaction.user,
                )
        except mut.AIOrchestrationMutationError as exc:
            await interaction.response.send_message(
                f"❌ {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return
        except Exception as exc:  # noqa: BLE001 — defensive
            logger.exception(
                "tools scope_view: mutation raised for scope=%s target=%s",
                self._scope,
                self._target_id,
            )
            await interaction.response.send_message(
                f"❌ Unexpected error: {type(exc).__name__}: {exc}",
                ephemeral=True,
            )
            return

        if profile_key is None:
            verb = f"Cleared the orchestration profile for {self._target_label}"
        else:
            verb = (
                f"Set **{profile_key}** as the orchestration profile for "
                f"{self._target_label}"
            )
        await interaction.response.edit_message(
            content=f"✅ {verb} (generation {result.generation}).",
            view=None,
        )


class _ProfileChoiceView(discord.ui.View):
    """Ephemeral one-select view that writes a profile to a resolved target."""

    def __init__(self, *, scope: str, target_id: int | None, target_label: str) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT_SECONDS)
        self.add_item(
            _ProfileSelect(
                scope=scope,
                target_id=target_id,
                target_label=target_label,
            ),
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await _require_admin(interaction)


class GuildToolsProfileView(discord.ui.View):
    """Ephemeral view: pick the guild-default orchestration profile."""

    def __init__(self) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT_SECONDS)
        self.add_item(
            _ProfileSelect(scope="guild", target_id=None, target_label="the guild"),
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await _require_admin(interaction)


class _ChannelPickSelect(discord.ui.ChannelSelect):
    """Pick a text channel, then choose its orchestration profile."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a channel to configure…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        label = getattr(picked, "mention", None) or f"<#{picked.id}>"
        await interaction.response.send_message(
            f"Pick an orchestration profile for {label}.",
            view=_ProfileChoiceView(
                scope="channel",
                target_id=picked.id,
                target_label=label,
            ),
            ephemeral=True,
        )


class ChannelToolsSelectView(discord.ui.View):
    """Ephemeral channel picker for the channel-scope orchestration flow."""

    def __init__(self) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT_SECONDS)
        self.add_item(_ChannelPickSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await _require_admin(interaction)


class _CategoryPickSelect(discord.ui.ChannelSelect):
    """Pick a category, then choose its orchestration profile."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick a category to configure…",
            channel_types=[discord.ChannelType.category],
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        picked = self.values[0]
        label = f"category **{getattr(picked, 'name', picked.id)}**"
        await interaction.response.send_message(
            f"Pick an orchestration profile for {label}.",
            view=_ProfileChoiceView(
                scope="category",
                target_id=picked.id,
                target_label=label,
            ),
            ephemeral=True,
        )


class CategoryToolsSelectView(discord.ui.View):
    """Ephemeral category picker for the category-scope orchestration flow."""

    def __init__(self) -> None:
        super().__init__(timeout=_VIEW_TIMEOUT_SECONDS)
        self.add_item(_CategoryPickSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return await _require_admin(interaction)


async def _require_admin(interaction: discord.Interaction) -> bool:
    """Shared admin gate for every transient Tools & Workflows view.

    Honours the configured platform owner (config.BOT_OWNER_USER_ID).
    """
    from views.base import interaction_is_admin

    if not interaction_is_admin(interaction):
        await interaction.response.send_message(
            "❌ Administrator permission required.",
            ephemeral=True,
        )
        return False
    return True


__all__ = [
    "CategoryToolsSelectView",
    "ChannelToolsSelectView",
    "GuildToolsProfileView",
]
