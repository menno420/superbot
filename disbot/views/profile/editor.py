"""Self-service profile editor — ``/myprofile`` write controls (myprofile PR B).

The first UI consumer of :class:`services.participation_mutation.ParticipationMutationPipeline`
(shipped with migrations 027/028 but unexercised until now). Mirrors the shipped
Help-editor stack (:mod:`views.help.editor`):

* **Writes only through the pipeline** — one audited mutation call per editor
  action; the views never touch ``utils.db.user_participation`` directly. An
  AST test pins this.
* **Self-scoped authority** — the viewer IS the subject (no member parameter),
  so the :class:`views.base.BaseView` owner-lock is the whole access model; the
  pipeline re-validates ``actor_id == user_id`` on every write anyway.
* **Re-render from the accessors** — after a successful write the pipeline
  invalidates the user-config cache, so the immediate re-read is truthful (the
  editor-stack pattern).

Flow: :class:`ProfileEditorHomeView` (pick a subsystem) →
:class:`ProfileSubsystemEditorView` (toggle participation / subscriptions /
visibility / preferences for that subsystem).

Layering: a view may import ``utils`` / ``core`` / ``services`` but **never**
``cogs`` (the hard rule). This module reads through the accessors + schema
registry and writes through the participation mutation service only.
"""

from __future__ import annotations

import logging

import discord

from core.runtime import participation_schema
from core.runtime.participation_schema import (
    ParticipationSchema,
    PreferenceSpec,
    PreferenceValueType,
)
from services.participation_mutation import (
    ParticipationMutationError,
    ParticipationMutationPipeline,
    UnauthorizedParticipationMutationError,
)
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
from views.profile.profile_view import (
    _subsystem_display,
    _subsystem_section,
    preference_key,
)

logger = logging.getLogger("bot.views.profile.editor")

_FOOTER = "Only you can see and change this — changes apply immediately."

# One pipeline instance is stateless (create-per-mutation is also fine); reuse it.
_PIPELINE = ParticipationMutationPipeline()


# ---------------------------------------------------------------------------
# Shared write helper — one audited call per action, then re-render in place.
# ---------------------------------------------------------------------------


async def _guarded(
    interaction: discord.Interaction,
    view: ProfileSubsystemEditorView,
    coro,
) -> None:
    """Await one pipeline mutation, then re-render the subsystem editor.

    A typed :class:`ParticipationMutationError` surfaces as ephemeral copy and
    leaves the panel untouched (never a crash). On success the re-read is
    truthful because the pipeline invalidated the user-config cache.
    """
    try:
        await coro
    except UnauthorizedParticipationMutationError:
        await interaction.response.send_message(
            "❌ You can only change your own profile.",
            ephemeral=True,
        )
        return
    except ParticipationMutationError as exc:
        await interaction.response.send_message(f"❌ {exc}", ephemeral=True)
        return
    refreshed = await ProfileSubsystemEditorView.create(
        view._author,
        view._guild_id,
        view._subsystem,
    )
    await interaction.response.edit_message(
        embed=await refreshed.build_embed(),
        view=refreshed,
    )


# ---------------------------------------------------------------------------
# Editor home — pick a subsystem to manage
# ---------------------------------------------------------------------------


class _SubsystemSelect(discord.ui.Select):
    """Pick which registered subsystem to manage."""

    def __init__(self, subsystems: list[str]) -> None:
        options = [
            discord.SelectOption(
                label=_subsystem_display(name)[:100],
                value=name,
            )
            for name in subsystems
        ] or [discord.SelectOption(label="(nothing to manage)", value="-")]
        super().__init__(placeholder="Pick a feature to manage…", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        from core.runtime.interaction_helpers import safe_defer

        view: ProfileEditorHomeView = self.view  # type: ignore[assignment]
        value = self.values[0]
        if value == "-":
            await safe_defer(interaction)
            return
        editor = await ProfileSubsystemEditorView.create(
            view._author,
            view._guild_id,
            value,
        )
        await interaction.response.edit_message(
            embed=await editor.build_embed(),
            view=editor,
        )


class ProfileEditorHomeView(BaseView):
    """Owner-locked ephemeral landing for the self-service editor."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
    ) -> None:
        super().__init__(author)
        self._guild_id = guild_id
        subsystems = participation_schema.registered_subsystems()
        if subsystems:
            self.add_item(_SubsystemSelect(subsystems))

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="⚙️ Manage your profile",
            description=(
                "Pick a feature below to opt in or out, toggle subscriptions and "
                "visibility, or change preferences. Every change is yours alone."
            ),
            color=INFO_COLOR,
        )
        if not participation_schema.registered_subsystems():
            embed.add_field(
                name="Nothing to manage yet",
                value=(
                    "No feature on this server has a per-user surface to "
                    "configure. Check back as features come online."
                ),
                inline=False,
            )
        embed.set_footer(text=_FOOTER)
        return embed

    @discord.ui.button(label="◀ Back to card", style=discord.ButtonStyle.secondary)
    async def back_to_card(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        from views.profile.profile_view import ProfileHomeView, build_profile_card

        card = ProfileHomeView(self._author, self._guild_id)
        # Re-render the full hero card and re-attach it, mirroring
        # ``ProfileHomeView.refresh`` — going back to the card must restore its
        # designed image, not return a plain embed (and never leave a stray
        # attachment). ``build_profile_card`` returns ``file is None`` on a
        # Pillow-less host, where ``attachments=[]`` keeps the embed-only state.
        embed, file = await build_profile_card(self._author, self._guild_id)
        await interaction.response.edit_message(
            embed=embed,
            view=card,
            attachments=[file] if file is not None else [],
        )


# ---------------------------------------------------------------------------
# Subsystem editor — the actual write controls for one subsystem
# ---------------------------------------------------------------------------


class ProfileSubsystemEditorView(BaseView):
    """Toggle one subsystem's participation, subscriptions, visibility, prefs.

    Built via :meth:`create` (async) so the control labels reflect the user's
    current state; each control is one audited pipeline call.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        guild_id: int,
        subsystem: str,
        schema: ParticipationSchema,
        *,
        participation: ParticipationState,
        visibility: VisibilityState,
    ) -> None:
        super().__init__(author)
        self._guild_id = guild_id
        self._subsystem = subsystem
        self._schema = schema
        self._participation = participation
        self._visibility = visibility
        self._build_controls()

    @classmethod
    async def create(
        cls,
        author: discord.Member | discord.User,
        guild_id: int,
        subsystem: str,
    ) -> ProfileSubsystemEditorView:
        """Read current state and assemble the view with accurate labels."""
        schema = participation_schema.get_schema(subsystem)
        if schema is None:
            schema = ParticipationSchema(subsystem=subsystem)
        participation = await get_participation(author.id, guild_id, subsystem)
        visibility = await get_visibility(author.id, guild_id, subsystem)
        return cls(
            author,
            guild_id,
            subsystem,
            schema,
            participation=participation,
            visibility=visibility,
        )

    # -- control assembly ------------------------------------------------

    def _build_controls(self) -> None:
        # Row 0: participation opt-in / opt-out.
        opted_in = self._participation is ParticipationState.OPTED_IN
        part_btn = discord.ui.Button(  # type: ignore[var-annotated]
            label="🚫 Opt out" if opted_in else "✅ Opt in",
            style=(
                discord.ButtonStyle.secondary
                if opted_in
                else discord.ButtonStyle.success
            ),
            row=0,
        )
        part_btn.callback = self._toggle_participation  # type: ignore[method-assign]
        self.add_item(part_btn)

        # Row 0: visibility (only if the subsystem declares visibility surfaces).
        if self._schema.visibility_intents:
            hidden = self._visibility is VisibilityState.HIDDEN
            vis_btn = discord.ui.Button(  # type: ignore[var-annotated]
                label="🌐 Make visible" if hidden else "🙈 Hide me",
                style=discord.ButtonStyle.secondary,
                row=0,
            )
            vis_btn.callback = self._toggle_visibility  # type: ignore[method-assign]
            self.add_item(vis_btn)

        # Row 1: subscriptions select (toggle on pick).
        if self._schema.subscriptions:
            self.add_item(_SubscriptionSelect(self._schema))

        # Row 2: preferences select (route by type on pick).
        if self._schema.preference_specs:
            self.add_item(_PreferenceSelect(self._schema))

        # Row 3: back.
        back = discord.ui.Button(  # type: ignore[var-annotated]
            label="◀ Back",
            style=discord.ButtonStyle.secondary,
            row=3,
        )
        back.callback = self._back  # type: ignore[method-assign]
        self.add_item(back)

    async def build_embed(self) -> discord.Embed:
        """One subsystem's current state — reuses the read-only card section."""
        section = await _subsystem_section(
            self._author.id,
            self._guild_id,
            self._subsystem,
            self._schema,
        )
        embed = discord.Embed(
            title=f"⚙️ {_subsystem_display(self._subsystem)}",
            description=section or "*(nothing to configure)*",
            color=INFO_COLOR,
        )
        embed.set_footer(text=_FOOTER)
        return embed

    # -- callbacks -------------------------------------------------------

    async def _toggle_participation(self, interaction: discord.Interaction) -> None:
        new_state = (
            "opted_out"
            if self._participation is ParticipationState.OPTED_IN
            else "opted_in"
        )
        await _guarded(
            interaction,
            self,
            _PIPELINE.set_participation(
                user_id=self._author.id,
                guild_id=self._guild_id,
                subsystem=self._subsystem,
                state=new_state,
                actor_id=self._author.id,
            ),
        )

    async def _toggle_visibility(self, interaction: discord.Interaction) -> None:
        new_visibility = (
            "public" if self._visibility is VisibilityState.HIDDEN else "hidden"
        )
        await _guarded(
            interaction,
            self,
            _PIPELINE.set_visibility(
                user_id=self._author.id,
                guild_id=self._guild_id,
                subsystem=self._subsystem,
                visibility=new_visibility,
                actor_id=self._author.id,
            ),
        )

    async def _back(self, interaction: discord.Interaction) -> None:
        home = ProfileEditorHomeView(self._author, self._guild_id)
        await interaction.response.edit_message(
            embed=home.build_embed(),
            view=home,
        )


# ---------------------------------------------------------------------------
# Subscription select — pick a subscription to flip on/off
# ---------------------------------------------------------------------------


class _SubscriptionSelect(discord.ui.Select):
    """One option per :class:`SubscriptionSpec`; selecting flips its state."""

    def __init__(self, schema: ParticipationSchema) -> None:
        self._schema = schema
        options = [
            discord.SelectOption(
                label=spec.description[:100],
                value=spec.name,
                description=f"toggle this subscription · {spec.name}"[:100],
            )
            for spec in schema.subscriptions
        ]
        super().__init__(
            placeholder="Toggle a subscription…",
            options=options,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ProfileSubsystemEditorView = self.view  # type: ignore[assignment]
        name = self.values[0]
        spec = next(
            (s for s in self._schema.subscriptions if s.name == name),
            None,
        )
        if spec is None:
            from core.runtime.interaction_helpers import safe_defer

            await safe_defer(interaction)
            return
        effective_default = spec.default_enabled and not spec.requires_optin
        current = await is_subscribed(
            view._author.id,
            view._guild_id,
            view._subsystem,
            spec.name,
            default=effective_default,
        )
        await _guarded(
            interaction,
            view,
            _PIPELINE.set_subscription(
                user_id=view._author.id,
                guild_id=view._guild_id,
                subsystem=view._subsystem,
                topic=spec.name,
                enabled=not current,
                actor_id=view._author.id,
            ),
        )


# ---------------------------------------------------------------------------
# Preference select — pick a preference, then edit it by its type
# ---------------------------------------------------------------------------


class _PreferenceSelect(discord.ui.Select):
    """Pick a preference; routes to the right editor for its value type."""

    def __init__(self, schema: ParticipationSchema) -> None:
        self._schema = schema
        options = [
            discord.SelectOption(
                label=spec.description[:100],
                value=spec.name,
                description=f"{spec.value_type.value} preference · {spec.name}"[:100],
            )
            for spec in schema.preference_specs
        ]
        super().__init__(
            placeholder="Change a preference…",
            options=options,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ProfileSubsystemEditorView = self.view  # type: ignore[assignment]
        name = self.values[0]
        spec = next(
            (s for s in self._schema.preference_specs if s.name == name),
            None,
        )
        if spec is None:
            from core.runtime.interaction_helpers import safe_defer

            await safe_defer(interaction)
            return

        key = preference_key(view._subsystem, spec.name)

        if spec.value_type is PreferenceValueType.BOOL:
            result = await get_preference(
                view._author.id,
                view._guild_id,
                key,
                default=spec.default,
            )
            current = bool(result.value if result.found else spec.default)
            await _guarded(
                interaction,
                view,
                _PIPELINE.set_preference(
                    user_id=view._author.id,
                    guild_id=view._guild_id,
                    key=key,
                    value=not current,
                    actor_id=view._author.id,
                ),
            )
            return

        if spec.value_type is PreferenceValueType.ENUM:
            chooser = _PreferenceEnumView(view, spec)
            await interaction.response.edit_message(
                embed=chooser.build_embed(),
                view=chooser,
            )
            return

        # STRING / INT / FLOAT → free-text modal.
        await interaction.response.send_modal(_PreferenceModal(view, spec))


# ---------------------------------------------------------------------------
# Enum preference chooser — a select of the spec's allowed values
# ---------------------------------------------------------------------------


class _EnumValueSelect(discord.ui.Select):
    def __init__(self, spec: PreferenceSpec) -> None:
        self._spec = spec
        options = [
            discord.SelectOption(label=str(value)[:100], value=str(value))
            for value in spec.allowed_values
        ] or [discord.SelectOption(label="(no choices)", value="-")]
        super().__init__(placeholder=f"Pick a {spec.description}…", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        chooser: _PreferenceEnumView = self.view  # type: ignore[assignment]
        editor = chooser._editor
        chosen = self.values[0]
        if chosen == "-":
            from core.runtime.interaction_helpers import safe_defer

            await safe_defer(interaction)
            return
        await _guarded(
            interaction,
            editor,
            _PIPELINE.set_preference(
                user_id=editor._author.id,
                guild_id=editor._guild_id,
                key=preference_key(editor._subsystem, self._spec.name),
                value=chosen,
                actor_id=editor._author.id,
            ),
        )


class _PreferenceEnumView(BaseView):
    """Transient owner-locked chooser for an enum preference."""

    def __init__(
        self,
        editor: ProfileSubsystemEditorView,
        spec: PreferenceSpec,
    ) -> None:
        super().__init__(editor._author)
        self._editor = editor
        self._spec = spec
        self.add_item(_EnumValueSelect(spec))

    def build_embed(self) -> discord.Embed:
        return discord.Embed(
            title=f"⚙️ {self._spec.description}",
            description=(
                f"Pick a value for **{self._spec.description}** "
                f"(default: `{self._spec.default}`)."
            ),
            color=INFO_COLOR,
        )

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.secondary, row=1)
    async def back(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        refreshed = await ProfileSubsystemEditorView.create(
            self._editor._author,
            self._editor._guild_id,
            self._editor._subsystem,
        )
        await interaction.response.edit_message(
            embed=await refreshed.build_embed(),
            view=refreshed,
        )


# ---------------------------------------------------------------------------
# Free-text preference modal (STRING / INT / FLOAT)
# ---------------------------------------------------------------------------


def _coerce_preference(spec: PreferenceSpec, raw: str):
    """Coerce modal text to the spec's value type, raising ``ValueError``."""
    if spec.value_type is PreferenceValueType.INT:
        return int(raw)
    if spec.value_type is PreferenceValueType.FLOAT:
        return float(raw)
    return raw  # STRING


class _PreferenceModal(discord.ui.Modal):  # type: ignore[call-arg]
    """A single text input for a string/int/float preference."""

    def __init__(
        self,
        editor: ProfileSubsystemEditorView,
        spec: PreferenceSpec,
    ) -> None:
        super().__init__(title=f"Set {spec.description}"[:45])
        self._editor = editor
        self._spec = spec
        self._field: discord.ui.TextInput = discord.ui.TextInput(  # type: ignore[type-arg]
            label=spec.description[:45],
            default=str(spec.default),
            max_length=200,
        )
        self.add_item(self._field)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            value = _coerce_preference(self._spec, self._field.value)
        except ValueError:
            await interaction.response.send_message(
                f"❌ `{self._field.value}` is not a valid "
                f"{self._spec.value_type.value} value.",
                ephemeral=True,
            )
            return
        await _guarded(
            interaction,
            self._editor,
            _PIPELINE.set_preference(
                user_id=self._editor._author.id,
                guild_id=self._editor._guild_id,
                key=preference_key(self._editor._subsystem, self._spec.name),
                value=value,
                actor_id=self._editor._author.id,
            ),
        )


__all__ = [
    "ProfileEditorHomeView",
    "ProfileSubsystemEditorView",
]
