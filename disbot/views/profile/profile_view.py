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

import io
from dataclasses import dataclass

import discord

from core.runtime import participation_schema
from utils.profile_render import render_profile_card
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

# The hero-image attachment filename; the embed references it via
# ``attachment://`` so the rendered card sits at the top of the profile card.
_CARD_FILENAME = "profile.png"

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
) -> tuple[str, ParticipationState]:
    """Render one subsystem's lines + return its participation state.

    Returning the state lets :func:`_gather_profile` tally engagement for the
    hero card in the **same** DB pass that builds the embed — no second round
    of ``get_participation`` calls.
    """
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

    return "\n".join(lines), state


@dataclass(frozen=True)
class ProfileSummary:
    """Headline engagement numbers for the hero card (one DB pass).

    *features* is how many participation-aware subsystems exist on the server;
    *opted_in* is how many the viewer has explicitly opted into.
    """

    features: int
    opted_in: int


async def _gather_profile(
    user: discord.abc.User,
    guild_id: int,
) -> tuple[discord.Embed, ProfileSummary]:
    """Build the profile embed and engagement summary in a single pass.

    The single data-gathering seam: :func:`build_profile_embed` (which keeps
    its embed-only signature for callers/tests) and :func:`build_profile_card`
    (which also needs the tally for the rendered card) both route through here,
    so the embed and the card can never disagree and the participation lookups
    run once.
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
        return embed, ProfileSummary(features=0, opted_in=0)

    opted_in = 0
    for subsystem in sorted(schemas):
        section, state = await _subsystem_section(
            user.id,
            guild_id,
            subsystem,
            schemas[subsystem],
        )
        if state == ParticipationState.OPTED_IN:
            opted_in += 1
        embed.add_field(
            name=_subsystem_display(subsystem),
            value=section or "*(nothing to configure)*",
            inline=False,
        )

    embed.set_footer(text="Tap ⚙️ Manage settings to opt in/out and set preferences.")
    return embed, ProfileSummary(features=len(schemas), opted_in=opted_in)


async def build_profile_embed(
    user: discord.abc.User,
    guild_id: int,
) -> discord.Embed:
    """Compose the read-only profile card for ``user`` in ``guild_id``.

    Iterates the registered participation schemas alphabetically; each
    becomes one embed field. With no registrants (or an empty schema) the
    card renders an honest empty state rather than a blank embed.
    """
    embed, _summary = await _gather_profile(user, guild_id)
    return embed


async def build_profile_card(
    user: discord.abc.User,
    guild_id: int,
) -> tuple[discord.Embed, discord.File | None]:
    """The embed plus a rendered hero-card image attachment (or ``None``).

    The image-as-screen upgrade: the same schema-driven embed gains a designed
    hero card (avatar disc + name, feature/opt-in stat panels, an engagement
    progress bar) on the themeable card engine. When Pillow is unavailable the
    renderer returns ``None`` and we keep the embed exactly as before — the
    card is strictly additive, never a regression.
    """
    embed, summary = await _gather_profile(user, guild_id)

    progress = (
        ("Profile engagement", summary.opted_in / summary.features)
        if summary.features
        else None
    )
    png = render_profile_card(
        display_name=user.display_name,
        subtitle="Your server profile",
        stats=[
            ("Features", str(summary.features)),
            ("Opted in", f"{summary.opted_in}/{summary.features}"),
        ],
        progress=progress,
        footer="SuperBot · /myprofile",
    )
    if png is None:
        return embed, None

    embed.set_image(url=f"attachment://{_CARD_FILENAME}")
    return embed, discord.File(io.BytesIO(png), filename=_CARD_FILENAME)


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

    async def render_card(self) -> tuple[discord.Embed, discord.File | None]:
        """Embed + hero-card image attachment (``None`` file = render fallback)."""
        return await build_profile_card(self._author, self._guild_id)

    @discord.ui.button(label="🔄 Refresh", style=discord.ButtonStyle.secondary)
    async def refresh(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        embed, file = await self.render_card()
        # ``attachments`` must be set explicitly on edit: pass the freshly
        # rendered card, or an empty list to drop any prior image when the
        # renderer is unavailable.
        await interaction.response.edit_message(
            embed=embed,
            view=self,
            attachments=[file] if file is not None else [],
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
        # The editor has no hero image, so clear the card explicitly — otherwise
        # Discord keeps the prior attachment and the profile card lingers as a
        # stray image under the settings panel (same contract as ``refresh``).
        await interaction.response.edit_message(
            embed=editor.build_embed(),
            view=editor,
            attachments=[],
        )
