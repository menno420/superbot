"""Read-only ``/myprofile`` card — a schema-driven per-user profile view.

Composes the typed read accessors (:mod:`utils.user_config_accessors`) over
the per-user participation registry
(:func:`core.runtime.participation_schema.all_schemas`): one section per
registered subsystem showing the user's participation state, subscriptions,
preferences, and visibility — every value labelled with its declared default
(the Q-0058 "show the default" idiom). Schema-driven: a new subsystem that
registers a ``ParticipationSchema`` appears here with zero changes to this
file.

PR A is **read-only** — zero writes, no mutation imports (pinned by an AST
test). The owner-locked ephemeral :class:`ProfileHomeView` is the shell PR B
extends with the self-service toggles (each routed through the audited
``ParticipationMutationPipeline``). For now it carries a single read-only
**Refresh** button that re-renders from the accessors.

Layering: a view may import ``utils`` / ``core`` / ``services`` but **never**
``cogs`` (the hard rule). This module reads through the accessors + the
schema registry only.
"""

from __future__ import annotations

import discord

from core.runtime import participation_schema
from utils.subsystem_registry import SUBSYSTEMS
from utils.ui_constants import INFO_COLOR
from utils.user_config_accessors import (
    ParticipationState,
    VisibilityState,
    get_participation,
    get_preference,
    get_visibility,
    is_subscribed,
)
from views.base import BaseView

# Per-user preferences are stored under one flat key per (user, guild); we
# namespace each subsystem's preference by joining the subsystem name and the
# spec name with this separator so two subsystems can declare a preference of
# the same short name without colliding. PR B's write controls use the same
# key (see :func:`preference_key`).
PREFERENCE_KEY_SEP = "."

_PARTICIPATION_LABEL = {
    ParticipationState.OPTED_IN: "✅ opted in",
    ParticipationState.OPTED_OUT: "🚫 opted out",
    ParticipationState.NOT_SET: "—  not set (default)",
}

_VISIBILITY_LABEL = {
    VisibilityState.PUBLIC: "🌐 public",
    VisibilityState.HIDDEN: "🙈 hidden",
    VisibilityState.DEFAULT: "—  default",
}


def preference_key(subsystem: str, name: str) -> str:
    """The flat storage key for a subsystem's named preference.

    The single source of truth for the read (here) and the future write
    (PR B), so the two never drift apart.
    """
    return f"{subsystem}{PREFERENCE_KEY_SEP}{name}"


def _subsystem_display(subsystem: str) -> str:
    entry = SUBSYSTEMS.get(subsystem, {})
    emoji = entry.get("emoji", "•")
    name = entry.get("display_name", subsystem.replace("_", " ").title())
    return f"{emoji} {name}"


def _on_off(value: bool) -> str:
    return "on" if value else "off"


async def _subsystem_section(
    user_id: int,
    guild_id: int,
    subsystem: str,
    schema,
) -> str:
    """Render one subsystem's lines for the profile card."""
    lines: list[str] = []

    state = await get_participation(user_id, guild_id, subsystem)
    lines.append(f"**Participation:** {_PARTICIPATION_LABEL[state]}")

    for spec in schema.subscriptions:
        # A subscription requiring opt-in is effectively off until chosen,
        # regardless of its declared default_enabled.
        effective_default = spec.default_enabled and not spec.requires_optin
        enabled = await is_subscribed(
            user_id,
            guild_id,
            subsystem,
            spec.name,
            default=effective_default,
        )
        mark = "✅" if enabled else "⬜"
        lines.append(
            f"{mark} {spec.description}  *(default {_on_off(effective_default)})*",
        )

    for spec in schema.preference_specs:
        result = await get_preference(
            user_id,
            guild_id,
            preference_key(subsystem, spec.name),
            default=spec.default,
        )
        value = result.value if result.found else spec.default
        suffix = "" if result.found else "  *(default)*"
        lines.append(f"⚙️ {spec.description}: **{value}**{suffix}")

    if schema.visibility_intents:
        visibility = await get_visibility(user_id, guild_id, subsystem)
        lines.append(f"**Visibility:** {_VISIBILITY_LABEL[visibility]}")

    return "\n".join(lines)


async def build_profile_embed(
    user: discord.abc.User,
    guild_id: int,
) -> discord.Embed:
    """Compose the read-only profile card for ``user`` in ``guild_id``.

    Iterates the registered participation schemas alphabetically; each
    becomes one embed field. With no registrants (or an empty schema) the
    card renders an honest empty state rather than a blank embed.
    """
    embed = discord.Embed(
        title=f"👤 {user.display_name} — your profile",
        description=(
            "Your per-server participation, subscriptions, preferences, and "
            "visibility. Only you can see this card."
        ),
        color=INFO_COLOR,
    )
    embed.set_thumbnail(url=user.display_avatar.url)

    schemas = participation_schema.all_schemas()
    if not schemas:
        embed.add_field(
            name="No participation-aware features yet",
            value=(
                "No subsystem on this server has registered a per-user "
                "participation surface. Nothing to show — check back as "
                "features come online."
            ),
            inline=False,
        )
        return embed

    for subsystem in sorted(schemas):
        section = await _subsystem_section(
            user.id,
            guild_id,
            subsystem,
            schemas[subsystem],
        )
        embed.add_field(
            name=_subsystem_display(subsystem),
            value=section or "*(nothing to configure)*",
            inline=False,
        )

    embed.set_footer(text="Tap ⚙️ Manage settings to opt in/out and set preferences.")
    return embed


class ProfileHomeView(BaseView):
    """Owner-locked ephemeral profile card (read-only shell for PR B).

    Self-service authority is being yourself: the card is always scoped to
    the invoking user (no member parameter), so the owner-lock from
    :class:`BaseView` is the whole access model for PR A. PR B adds the
    write controls; until then the only control is a read-only refresh.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
    ) -> None:
        super().__init__(author)
        self._guild_id = guild_id

    async def render_embed(self) -> discord.Embed:
        return await build_profile_embed(self._author, self._guild_id)

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary)
    async def refresh(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=await self.render_embed(),
            view=self,
        )

    @discord.ui.button(label="⚙️ Manage settings", style=discord.ButtonStyle.primary)
    async def manage(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        """Open the self-service editor (PR B).

        Pure navigation — this card stays read-only (no mutation import); the
        editor module owns every write through the audited pipeline. The lazy
        import keeps the card builder's import surface mutation-free.
        """
        from views.profile.editor import ProfileEditorHomeView

        editor = ProfileEditorHomeView(self._author, self._guild_id)
        await interaction.response.edit_message(
            embed=editor.build_embed(),
            view=editor,
        )
