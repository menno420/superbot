"""Essential Setup — the plain-language, one-action-per-step setup spine.

The rebuilt setup experience the maintainer asked for: a short, linear,
button/dropdown-only flow that needs **zero Discord/bot knowledge**, uses **no
jargon**, and where **every step applies immediately** (the direct lane — owner
decision Q-A, 2026-06-24: "save each step instantly").  Each step is one
complete action that actually finishes a piece of setup; nothing is "staged"
for a later Final Review.

Design (plan ``docs/planning/setup-wizard-restructure-plan-2026-06-24.md`` §5):

* **Linear** — one screen at a time, with *Save & continue* / *Skip* / *Back*
  and a "Step X of N" counter.  No grid of buttons.
* **Direct-apply** — each step writes through its existing **audited** service
  (``SettingsMutationPipeline`` / ``moderation`` / ``welcome`` settings), so the
  change is live the instant you press the button.  No new mutation primitives.
* **Plain language** — the operator never reads "guild", "binding", "draft",
  "operation".  (Enforced by ``scripts/check_setup_copy.py``.)

This module is **additive** — the existing wizard (``views/setup/wizard.py``)
is untouched and remains the full/advanced path; Essential Setup is the new
quick spine.  Live steps: greet new members · set your moderators · block spam
and bad links · choose a log channel · set up a help desk (+ the closing
summary).  Remaining follow-ons on this same pattern: reward activity (xp +
auto-role) and the server-type starter preset.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from views.base import BaseView

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Flow state
# ---------------------------------------------------------------------------


class EssentialFlow:
    """Ordered list of steps + where the operator is in it.

    Holds no Discord objects beyond the author + guild; each step view is built
    fresh from the flow when the operator moves, so there is no stale-component
    state to manage.
    """

    def __init__(
        self,
        author: discord.Member,
        guild: discord.Guild,
    ) -> None:
        self.author = author
        self.guild = guild
        self.index = 0
        self.applied: list[str] = []
        self.skipped: list[str] = []
        # Step factories, in order. Add new steps here as they are built.
        self._steps: list[Callable[[EssentialFlow], _StepView]] = [
            GreetMembersStep,
            ModeratorsStep,
            BlockSpamStep,
            LogChannelStep,
            HelpDeskStep,
        ]

    @property
    def total(self) -> int:
        return len(self._steps)

    @property
    def done(self) -> bool:
        return self.index >= self.total

    def current_view(self) -> BaseView:
        if self.done:
            return EssentialSummaryView(self)
        return self._steps[self.index](self)

    def step_counter(self) -> str:
        return f"Step {self.index + 1} of {self.total}"

    def advance(self) -> None:
        self.index += 1

    def back(self) -> None:
        if self.index > 0:
            self.index -= 1

    def record_applied(self, line: str) -> None:
        self.applied.append(line)

    def record_skipped(self, line: str) -> None:
        self.skipped.append(line)


# ---------------------------------------------------------------------------
# Nav buttons (shared)
# ---------------------------------------------------------------------------


class _BackButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self, row: int) -> None:
        super().__init__(label="Back", style=discord.ButtonStyle.secondary, row=row)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: _StepView = self.view  # type: ignore[assignment]
        await view.go_back(interaction)


class _SkipButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self, row: int, label: str) -> None:
        super().__init__(label=label, style=discord.ButtonStyle.secondary, row=row)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: _StepView = self.view  # type: ignore[assignment]
        await view.skip(interaction)


# ---------------------------------------------------------------------------
# Step base
# ---------------------------------------------------------------------------


class _StepView(BaseView):
    """One step. Subclasses add their pickers + a Save button and a render()."""

    skip_label = "Skip this step"

    def __init__(self, flow: EssentialFlow) -> None:
        super().__init__(flow.author, public=False, timeout=600)
        self.flow = flow
        self.build_items()
        if flow.index > 0:
            self.add_item(_BackButton(row=3))
        self.add_item(_SkipButton(row=3, label=self.skip_label))

    # --- subclass hooks ---
    def build_items(self) -> None:  # pragma: no cover - trivial in subclasses
        raise NotImplementedError

    def render(self) -> discord.Embed:  # pragma: no cover - trivial in subclasses
        raise NotImplementedError

    # --- navigation (shared) ---
    async def _show_current(self, interaction: discord.Interaction) -> None:
        view = self.flow.current_view()
        embed = view.render() if hasattr(view, "render") else None
        await interaction.response.edit_message(embed=embed, view=view)

    async def skip(self, interaction: discord.Interaction) -> None:
        self.flow.advance()
        await self._show_current(interaction)

    async def go_back(self, interaction: discord.Interaction) -> None:
        self.flow.back()
        await self._show_current(interaction)

    async def complete(
        self,
        interaction: discord.Interaction,
        summary_line: str,
    ) -> None:
        """Record the applied change and advance to the next step."""
        self.flow.record_applied(summary_line)
        self.flow.advance()
        await self._show_current(interaction)

    async def _set(self, subsystem: str, name: str, value: object) -> None:
        """Apply one setting immediately through the audited pipeline.

        Imported lazily: setup view files must not import concrete mutation
        pipelines at module top level (``test_setup_operations_invariants``).
        """
        from services.settings_mutation import SettingsMutationPipeline

        await SettingsMutationPipeline().set_value(
            self.flow.guild,
            subsystem,
            name,
            value,
            self.flow.author,
            actor_type="user",
        )


# ---------------------------------------------------------------------------
# Step 1 — Greet new members  (welcome)
# ---------------------------------------------------------------------------


class _WelcomeChannelSelect(discord.ui.ChannelSelect):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            placeholder="Where should the welcome message appear?",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: GreetMembersStep = self.view  # type: ignore[assignment]
        view.channel_id = self.values[0].id
        await interaction.response.edit_message(embed=view.render(), view=view)


class _EntryRoleSelect(discord.ui.RoleSelect):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            placeholder="Give newcomers a role (optional)…",
            min_values=0,
            max_values=1,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: GreetMembersStep = self.view  # type: ignore[assignment]
        view.entry_role_id = self.values[0].id if self.values else None
        await interaction.response.edit_message(embed=view.render(), view=view)


class _GreetSaveButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="Turn on greetings",
            emoji="👋",
            style=discord.ButtonStyle.success,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: GreetMembersStep = self.view  # type: ignore[assignment]
        await view.apply(interaction)


class GreetMembersStep(_StepView):
    title = "Greet new members"
    skip_label = "Skip greetings"

    def __init__(self, flow: EssentialFlow) -> None:
        self.channel_id: int | None = None
        self.entry_role_id: int | None = None
        super().__init__(flow)

    def build_items(self) -> None:
        self.add_item(_WelcomeChannelSelect())
        self.add_item(_EntryRoleSelect())
        self.add_item(_GreetSaveButton())

    def render(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"👋 {self.title}",
            description=(
                "Send a friendly message when someone joins, and (if you like) "
                "give every newcomer a role automatically.\n\n"
                "Pick a channel for the welcome message below, then press "
                "**Turn on greetings**."
            ),
            color=discord.Color.blurple(),
        )
        chan = f"<#{self.channel_id}>" if self.channel_id else "_not chosen yet_"
        role = f"<@&{self.entry_role_id}>" if self.entry_role_id else "_none_"
        embed.add_field(name="Welcome message channel", value=chan, inline=False)
        embed.add_field(name="Role for newcomers", value=role, inline=False)
        embed.set_footer(text=self.flow.step_counter())
        return embed

    async def apply(self, interaction: discord.Interaction) -> None:
        if self.channel_id is None:
            await interaction.response.send_message(
                "Pick a **channel** for the welcome message first.",
                ephemeral=True,
            )
            return
        try:
            await self._set("welcome", "enabled", True)
            await self._set("welcome", "join_enabled", True)
            await self._set("welcome", "channel", str(self.channel_id))
            if self.entry_role_id is not None:
                await self._set("welcome", "entry_role", str(self.entry_role_id))
        except Exception:
            logger.exception("essential setup: greet step apply failed")
            await interaction.response.send_message(
                "Something went wrong turning on greetings — please try again.",
                ephemeral=True,
            )
            return
        line = f"Greetings on, posting in <#{self.channel_id}>"
        if self.entry_role_id is not None:
            line += f" · newcomers get <@&{self.entry_role_id}>"
        await self.complete(interaction, line)


# ---------------------------------------------------------------------------
# Step 2 — Set moderators  (governance / moderation defaults)
# ---------------------------------------------------------------------------


class _ModRoleSelect(discord.ui.RoleSelect):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            placeholder="Which role can warn and remove people?",
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ModeratorsStep = self.view  # type: ignore[assignment]
        view.mod_role_id = self.values[0].id
        await interaction.response.edit_message(embed=view.render(), view=view)


class _DmToggleButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self, on: bool) -> None:
        super().__init__(
            label=("Tell members why: ON" if on else "Tell members why: OFF"),
            style=(
                discord.ButtonStyle.success if on else discord.ButtonStyle.secondary
            ),
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ModeratorsStep = self.view  # type: ignore[assignment]
        view.dm_on = not view.dm_on
        view.refresh_items()
        await interaction.response.edit_message(embed=view.render(), view=view)


class _ModSaveButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="Save moderators",
            emoji="🛡️",
            style=discord.ButtonStyle.success,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ModeratorsStep = self.view  # type: ignore[assignment]
        await view.apply(interaction)


class ModeratorsStep(_StepView):
    title = "Set your moderators"
    skip_label = "Skip moderators"

    def __init__(self, flow: EssentialFlow) -> None:
        self.mod_role_id: int | None = None
        self.dm_on: bool = True
        super().__init__(flow)

    def build_items(self) -> None:
        self.refresh_items()

    def refresh_items(self) -> None:
        """(Re)build the row-0/1/2 controls — used after the DM toggle flips."""
        for child in list(self.children):
            if isinstance(child, (_ModRoleSelect, _DmToggleButton, _ModSaveButton)):
                self.remove_item(child)
        self.add_item(_ModRoleSelect())
        self.add_item(_DmToggleButton(self.dm_on))
        self.add_item(_ModSaveButton())

    def render(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🛡️ {self.title}",
            description=(
                "Choose the role for people who can warn and remove others. "
                "We'll use safe defaults for everything else.\n\n"
                "“Tell members why” sends someone a short note when they're "
                "warned or removed, so they know what happened."
            ),
            color=discord.Color.blurple(),
        )
        role = f"<@&{self.mod_role_id}>" if self.mod_role_id else "_not chosen yet_"
        embed.add_field(name="Moderator role", value=role, inline=False)
        embed.add_field(
            name="Tell members why",
            value="On" if self.dm_on else "Off",
            inline=False,
        )
        embed.set_footer(text=self.flow.step_counter())
        return embed

    async def apply(self, interaction: discord.Interaction) -> None:
        if self.mod_role_id is None:
            await interaction.response.send_message(
                "Pick a **moderator role** first.",
                ephemeral=True,
            )
            return
        try:
            await self._set("moderation", "moderator_role", str(self.mod_role_id))
            await self._set("moderation", "dm_on_action", self.dm_on)
        except Exception:
            logger.exception("essential setup: moderators step apply failed")
            await interaction.response.send_message(
                "Something went wrong saving your moderators — please try again.",
                ephemeral=True,
            )
            return
        await self.complete(
            interaction,
            f"Moderator role set to <@&{self.mod_role_id}>"
            + (" · members told why" if self.dm_on else ""),
        )


# ---------------------------------------------------------------------------
# Step 3 — Block spam and bad links  (automod)
# ---------------------------------------------------------------------------

# (setting name, operator-facing label)
_SPAM_FILTERS: list[tuple[str, str]] = [
    ("spam_enabled", "Repeated spam"),
    ("invites_enabled", "Invite links"),
    ("caps_enabled", "ALL-CAPS shouting"),
    ("mentions_enabled", "Mass pings"),
]


class _FilterToggle(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self, key: str, label: str, on: bool, row: int) -> None:
        super().__init__(
            label=f"{label}: {'ON' if on else 'OFF'}",
            style=(
                discord.ButtonStyle.success if on else discord.ButtonStyle.secondary
            ),
            row=row,
        )
        self._key = key

    async def callback(self, interaction: discord.Interaction) -> None:
        view: BlockSpamStep = self.view  # type: ignore[assignment]
        view.filters[self._key] = not view.filters[self._key]
        view.refresh_items()
        await interaction.response.edit_message(embed=view.render(), view=view)


class _SpamSaveButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="Turn on protection",
            emoji="🧹",
            style=discord.ButtonStyle.success,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: BlockSpamStep = self.view  # type: ignore[assignment]
        await view.apply(interaction)


class BlockSpamStep(_StepView):
    title = "Block spam and bad links"
    skip_label = "Skip spam protection"

    def __init__(self, flow: EssentialFlow) -> None:
        self.filters: dict[str, bool] = {key: True for key, _ in _SPAM_FILTERS}
        super().__init__(flow)

    def build_items(self) -> None:
        self.refresh_items()

    def refresh_items(self) -> None:
        for child in list(self.children):
            if isinstance(child, (_FilterToggle, _SpamSaveButton)):
                self.remove_item(child)
        for i, (key, label) in enumerate(_SPAM_FILTERS):
            self.add_item(_FilterToggle(key, label, self.filters[key], row=i // 2))
        self.add_item(_SpamSaveButton())

    def render(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🧹 {self.title}",
            description=(
                "Automatically clean up the noise so you don't have to. "
                "Everything below is on by default — tap any to turn it off, "
                "then press **Turn on protection**."
            ),
            color=discord.Color.blurple(),
        )
        for key, label in _SPAM_FILTERS:
            embed.add_field(
                name=label,
                value="On" if self.filters[key] else "Off",
                inline=True,
            )
        embed.set_footer(text=self.flow.step_counter())
        return embed

    async def apply(self, interaction: discord.Interaction) -> None:
        try:
            await self._set("automod", "enabled", True)
            for key, _ in _SPAM_FILTERS:
                await self._set("automod", key, self.filters[key])
        except Exception:
            logger.exception("essential setup: block-spam step apply failed")
            await interaction.response.send_message(
                "Something went wrong turning on protection — please try again.",
                ephemeral=True,
            )
            return
        on_labels = [label for key, label in _SPAM_FILTERS if self.filters[key]]
        line = "Spam protection on"
        if on_labels:
            line += " · " + ", ".join(on_labels).lower()
        await self.complete(interaction, line)


# ---------------------------------------------------------------------------
# Step 4 — Choose a log channel  (logging: enable + bind mod & activity channels)
# ---------------------------------------------------------------------------
#
# Two channels (owner decision, 2026-06-24, superseding the moderation-only
# Q-0202): a **moderation log** — always on, ``logging.mod_channel``, the
# catch-all every route falls back to — and an optional **activity log**
# (``logging.events_channel``) for the server-activity categories the operator
# ticks in a quick multi-select (members joining/leaving, role changes, message
# edits/deletions — each its own ``*_enabled`` flag).  Leave a channel empty and
# we auto-create it (#mod-log / #server-log), so accepting the defaults is one
# tap.  Every write goes through the audited Settings + Binding pipelines
# (lazy-imported per the setup-view no-top-level-pipeline-import invariant).

# Plain-language default names for the channels we offer to create.
_NEW_MOD_CHANNEL_NAME = "mod-log"
_NEW_ACTIVITY_CHANNEL_NAME = "server-log"

# Optional server-activity categories: (logging flag, operator label, default-on).
# Message logging defaults OFF — it exposes edited/deleted content (a privacy
# trade-off the schema warns about); the privacy-safe two default on.
_ACTIVITY_TYPES: list[tuple[str, str, bool]] = [
    ("members_enabled", "Members joining & leaving", True),
    ("roles_enabled", "Role changes", True),
    ("messages_enabled", "Message edits & deletions", False),
]
_DEFAULT_ACTIVITY: set[str] = {flag for flag, _, on in _ACTIVITY_TYPES if on}


class _ActivityTypeSelect(discord.ui.Select):  # type: ignore[type-arg]
    def __init__(self, selected: set[str]) -> None:
        options = [
            discord.SelectOption(
                label=label,
                value=flag,
                default=flag in selected,
                description=(
                    "Shows the content members edited or deleted"
                    if flag == "messages_enabled"
                    else None
                ),
            )
            for flag, label, _ in _ACTIVITY_TYPES
        ]
        super().__init__(
            placeholder="What should the activity channel log?",
            min_values=0,
            max_values=len(options),
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: LogChannelStep = self.view  # type: ignore[assignment]
        view.activity = set(self.values)
        view.refresh_items()
        await interaction.response.edit_message(embed=view.render(), view=view)


class _LogChannelPicker(discord.ui.ChannelSelect):  # type: ignore[type-arg]
    """One channel picker, reused for both the moderation and activity slots."""

    def __init__(self, *, target: str, placeholder: str, row: int) -> None:
        self.target = target  # "mod" | "activity"
        super().__init__(
            placeholder=placeholder,
            channel_types=[discord.ChannelType.text],
            min_values=0,
            max_values=1,
            row=row,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: LogChannelStep = self.view  # type: ignore[assignment]
        chosen = self.values[0].id if self.values else None
        if self.target == "mod":
            view.mod_channel_id = chosen
        else:
            view.activity_channel_id = chosen
        view.refresh_items()
        await interaction.response.edit_message(embed=view.render(), view=view)


class _LogSaveButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="Save logging",
            emoji="📋",
            style=discord.ButtonStyle.success,
            row=4,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: LogChannelStep = self.view  # type: ignore[assignment]
        await view.apply(interaction)


class LogChannelStep(_StepView):
    title = "Choose a log channel"
    skip_label = "Skip logging"

    def __init__(self, flow: EssentialFlow) -> None:
        self.mod_channel_id: int | None = None
        self.activity_channel_id: int | None = None
        self.activity: set[str] = set(_DEFAULT_ACTIVITY)
        super().__init__(flow)

    def build_items(self) -> None:
        self.refresh_items()

    def refresh_items(self) -> None:
        """(Re)build the controls from current state (rows 0/1/2/4).

        Rebuilt on every interaction so the multi-select reflects ``activity``;
        the channel pickers reset visually but the chosen ids persist on the
        view and are shown in the embed.
        """
        for child in list(self.children):
            if isinstance(
                child,
                (_ActivityTypeSelect, _LogChannelPicker, _LogSaveButton),
            ):
                self.remove_item(child)
        self.add_item(_ActivityTypeSelect(self.activity))
        self.add_item(
            _LogChannelPicker(
                target="mod",
                placeholder="Moderation log channel (or leave empty)…",
                row=1,
            ),
        )
        self.add_item(
            _LogChannelPicker(
                target="activity",
                placeholder="Activity log channel (or leave empty)…",
                row=2,
            ),
        )
        self.add_item(_LogSaveButton())

    def render(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"📋 {self.title}",
            description=(
                "Keep a tidy record of what happens on your server, in two "
                "channels:\n"
                "• a **moderation log** — warnings, timeouts, kicks and bans\n"
                "• an **activity log** — the things you tick below\n\n"
                "Pick a channel for each, or leave one empty and we'll make it "
                f"for you (**#{_NEW_MOD_CHANNEL_NAME}** / "
                f"**#{_NEW_ACTIVITY_CHANNEL_NAME}**). Then press **Save logging**."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Moderation log",
            value=self._where(self.mod_channel_id, _NEW_MOD_CHANNEL_NAME),
            inline=False,
        )
        if self.activity:
            picked = ", ".join(
                label for flag, label, _ in _ACTIVITY_TYPES if flag in self.activity
            )
            embed.add_field(
                name="Activity log",
                value=(
                    f"{self._where(self.activity_channel_id, _NEW_ACTIVITY_CHANNEL_NAME)}\n"
                    f"_Logging: {picked}_"
                ),
                inline=False,
            )
        else:
            embed.add_field(
                name="Activity log",
                value="_off — tick any activity above to turn it on_",
                inline=False,
            )
        embed.set_footer(text=self.flow.step_counter())
        return embed

    @staticmethod
    def _where(channel_id: int | None, default_name: str) -> str:
        if channel_id:
            return f"<#{channel_id}>"
        return f"a new **#{default_name}** channel"

    async def apply(self, interaction: discord.Interaction) -> None:
        created: list[str] = []
        # Moderation log is the always-on baseline — resolve (or create) it.
        mod_id = self.mod_channel_id
        if mod_id is None:
            mod_id = await self._create_channel(interaction, _NEW_MOD_CHANNEL_NAME)
            if mod_id is None:
                return  # creation failed; error already surfaced
            created.append(_NEW_MOD_CHANNEL_NAME)
        # Activity log only when at least one activity category is ticked.
        activity_id: int | None = None
        if self.activity:
            activity_id = self.activity_channel_id
            if activity_id is None:
                activity_id = await self._create_channel(
                    interaction,
                    _NEW_ACTIVITY_CHANNEL_NAME,
                )
                if activity_id is None:
                    return
                created.append(_NEW_ACTIVITY_CHANNEL_NAME)
        try:
            await self._set("logging", "enabled", True)
            await self._bind("mod_channel", mod_id)
            for flag, _, _ in _ACTIVITY_TYPES:
                await self._set("logging", flag, flag in self.activity)
            if activity_id is not None:
                await self._bind("events_channel", activity_id)
        except Exception:
            logger.exception("essential setup: log-channel step apply failed")
            await interaction.response.send_message(
                "Something went wrong saving your log channels — please try again.",
                ephemeral=True,
            )
            return
        await self.complete(interaction, self._summary(mod_id, activity_id, created))

    def _summary(
        self,
        mod_id: int,
        activity_id: int | None,
        created: list[str],
    ) -> str:
        parts = [f"moderation → <#{mod_id}>"]
        if activity_id is not None:
            picked = ", ".join(
                label for flag, label, _ in _ACTIVITY_TYPES if flag in self.activity
            ).lower()
            parts.append(f"activity ({picked}) → <#{activity_id}>")
        line = "Logging on · " + " · ".join(parts)
        if created:
            line += " · created " + ", ".join(f"#{name}" for name in created)
        return line

    async def _create_channel(
        self,
        interaction: discord.Interaction,
        name: str,
    ) -> int | None:
        """Create *name* through the audited lifecycle creator.

        Returns the new channel's id, or ``None`` after surfacing an error (the
        caller then stops without writing anything).  ``ChannelLifecycleService``
        is imported lazily to match the setup-view convention (services /
        pipelines are not imported at module top level here).
        """
        from services.channel_lifecycle_service import ChannelLifecycleService

        result = await ChannelLifecycleService().create_channels(
            self.flow.guild,
            [name],
            self.flow.author,
        )
        if not result.applied:
            logger.warning(
                "essential setup: log channel %r create failed (guild=%s): %s",
                name,
                self.flow.guild.id,
                result.first_error,
            )
            await interaction.response.send_message(
                "Couldn't make a channel — please pick existing ones instead.",
                ephemeral=True,
            )
            return None
        return result.applied[0].target_id

    async def _bind(self, binding_name: str, channel_id: int) -> None:
        """Bind ``logging.<binding_name>`` to *channel_id* through the audited
        write path.

        ``BindingMutationPipeline`` is on the setup-view no-top-level-import list
        (``test_setup_operations_invariants``), so it — and ``BindingKind`` — are
        imported lazily here, exactly like ``_set`` does for settings.
        """
        from core.runtime.subsystem_schema import BindingKind
        from services.binding_mutation import BindingMutationPipeline

        await BindingMutationPipeline().set_binding(
            self.flow.guild,
            "logging",
            binding_name,
            BindingKind.CHANNEL,
            channel_id,
            self.flow.author,
            actor_type="user",
        )


# ---------------------------------------------------------------------------
# Step 5 — Set up a help desk  (tickets)
# ---------------------------------------------------------------------------


class _StaffRoleSelect(discord.ui.RoleSelect):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            placeholder="Who answers support requests? (staff role)",
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: HelpDeskStep = self.view  # type: ignore[assignment]
        view.staff_role_id = self.values[0].id
        await interaction.response.edit_message(embed=view.render(), view=view)


class _TranscriptChannelSelect(discord.ui.ChannelSelect):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            placeholder="Where to save closed-request logs? (optional)",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: HelpDeskStep = self.view  # type: ignore[assignment]
        view.log_channel_id = self.values[0].id
        await interaction.response.edit_message(embed=view.render(), view=view)


class _HelpDeskSaveButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="Turn on the help desk",
            emoji="🎫",
            style=discord.ButtonStyle.success,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: HelpDeskStep = self.view  # type: ignore[assignment]
        await view.apply(interaction)


class HelpDeskStep(_StepView):
    title = "Set up a help desk"
    skip_label = "Skip help desk"

    def __init__(self, flow: EssentialFlow) -> None:
        self.staff_role_id: int | None = None
        self.log_channel_id: int | None = None
        super().__init__(flow)

    def build_items(self) -> None:
        self.add_item(_StaffRoleSelect())
        self.add_item(_TranscriptChannelSelect())
        self.add_item(_HelpDeskSaveButton())

    def render(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🎫 {self.title}",
            description=(
                "Let members open a private request that only your staff can "
                "see. Pick who should answer them; we set up the rest.\n\n"
                "Then press **Turn on the help desk**."
            ),
            color=discord.Color.blurple(),
        )
        staff = (
            f"<@&{self.staff_role_id}>" if self.staff_role_id else "_not chosen yet_"
        )
        log = f"<#{self.log_channel_id}>" if self.log_channel_id else "_none_"
        embed.add_field(name="Who answers requests", value=staff, inline=False)
        embed.add_field(name="Save chat logs to", value=log, inline=False)
        embed.set_footer(text=self.flow.step_counter())
        return embed

    async def apply(self, interaction: discord.Interaction) -> None:
        if self.staff_role_id is None:
            await interaction.response.send_message(
                "Pick a **staff role** first — it's who can see and answer requests.",
                ephemeral=True,
            )
            return
        try:
            from services import ticket_mutation

            await ticket_mutation.update_config(
                self.flow.guild.id,
                self.flow.author.id,
                enabled=True,
                staff_role_id=self.staff_role_id,
                log_channel_id=self.log_channel_id,
            )
        except Exception:
            logger.exception("essential setup: help-desk step apply failed")
            await interaction.response.send_message(
                "Something went wrong setting up the help desk — please try again.",
                ephemeral=True,
            )
            return
        await self.complete(
            interaction,
            f"Help desk on, answered by <@&{self.staff_role_id}>",
        )


# ---------------------------------------------------------------------------
# Summary (after the last step)
# ---------------------------------------------------------------------------


class _FinishButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="All done",
            emoji="✅",
            style=discord.ButtonStyle.success,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: EssentialSummaryView = self.view  # type: ignore[assignment]
        for child in view.children:
            child.disabled = True  # type: ignore[attr-defined]
        await interaction.response.edit_message(embed=view.render(), view=view)


class EssentialSummaryView(BaseView):
    """Closing screen — a plain-language recap of what was switched on."""

    def __init__(self, flow: EssentialFlow) -> None:
        super().__init__(flow.author, public=False, timeout=600)
        self.flow = flow
        self.add_item(_FinishButton())

    def render(self) -> discord.Embed:
        embed = discord.Embed(
            title="✅ Setup complete",
            description="Here's what you switched on. You can change any of it later.",
            color=discord.Color.green(),
        )
        if self.flow.applied:
            embed.add_field(
                name="Turned on",
                value="\n".join(f"• {line}" for line in self.flow.applied),
                inline=False,
            )
        else:
            embed.description = (
                "You skipped every step — nothing was changed. "
                "Run setup again any time."
            )
        if self.flow.skipped:
            embed.add_field(
                name="Skipped (you can do these later)",
                value="\n".join(f"• {line}" for line in self.flow.skipped),
                inline=False,
            )
        return embed


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


_NOT_IN_SERVER = "This can only be used in a server."
_NOT_ADMIN = "Only a server admin can run setup."


def _first_embed(flow: EssentialFlow) -> discord.Embed:
    return flow.current_view().render()  # type: ignore[attr-defined,no-any-return]


async def open_essential_setup(interaction: discord.Interaction) -> None:
    """Open the Essential Setup flow from a slash command. Admin-gated."""
    guild = interaction.guild
    member = interaction.user
    if guild is None or not isinstance(member, discord.Member):
        await interaction.response.send_message(_NOT_IN_SERVER, ephemeral=True)
        return
    if not member.guild_permissions.administrator:
        await interaction.response.send_message(_NOT_ADMIN, ephemeral=True)
        return
    flow = EssentialFlow(member, guild)
    await interaction.response.send_message(
        embed=_first_embed(flow),
        view=flow.current_view(),
    )


async def open_essential_setup_prefix(ctx: object) -> None:
    """Open the Essential Setup flow from a prefix command. Admin-gated.

    ``ctx`` is a ``commands.Context`` (typed loosely so this view module does
    not import the ``commands`` extension).
    """
    guild = getattr(ctx, "guild", None)
    member = getattr(ctx, "author", None)
    send = ctx.send  # type: ignore[attr-defined]
    if guild is None or not isinstance(member, discord.Member):
        await send(_NOT_IN_SERVER)
        return
    if not member.guild_permissions.administrator:
        await send(_NOT_ADMIN)
        return
    flow = EssentialFlow(member, guild)
    await send(embed=_first_embed(flow), view=flow.current_view())
