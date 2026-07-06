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
quick spine.  Live steps: what kind of server is this (starter set) · greet new
members · set your moderators · block spam and bad links · choose a log channel
· reward active members · set up a help desk · where can people use commands
(+ the closing summary).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

import discord

from core.runtime.interaction_helpers import safe_defer, safe_edit, safe_followup
from core.runtime.persistent_views import PersistentView
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
            ServerTypeStep,
            GreetMembersStep,
            ModeratorsStep,
            BlockSpamStep,
            LogChannelStep,
            RewardActivityStep,
            HelpDeskStep,
            CommandChannelsStep,
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

    async def persist_progress(self) -> None:
        """Persist the flow position so a restart can revive it (migration 099).

        Called after every navigation move.  Best-effort: a DB hiccup must
        never break the wizard.  When the flow reaches the summary it is
        finished — clear the anchor and mark the session complete so the
        launcher reflects it and the on-ready resume sweep stops trying to
        revive a done flow.  Essential Setup is direct-apply, so only the *UI
        position* is stored here; the configuration is already saved.
        """
        from services import setup_session

        try:
            if self.done:
                await setup_session.clear_essential_anchor(self.guild.id)
                await setup_session.mark_complete(self.guild.id)
            else:
                await setup_session.set_essential_step(self.guild.id, self.index)
        except Exception:
            logger.exception(
                "essential setup: persist_progress failed (guild=%s)",
                getattr(self.guild, "id", None),
            )


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

    title = "this step"
    skip_label = "Skip this step"

    def __init__(self, flow: EssentialFlow) -> None:
        super().__init__(flow.author, public=False, timeout=600)
        self.flow = flow
        self.build_items()
        # Nav sits on the bottom row (4); each step's primary button uses row 3,
        # so "Save & continue" lands in the same place on every step regardless
        # of how many dropdowns the step has (the log step fills rows 0-2).
        if flow.index > 0:
            self.add_item(_BackButton(row=4))
        self.add_item(_SkipButton(row=4, label=self.skip_label))

    # --- subclass hooks ---
    def build_items(self) -> None:  # pragma: no cover - trivial in subclasses
        raise NotImplementedError

    def render(self) -> discord.Embed:  # pragma: no cover - trivial in subclasses
        raise NotImplementedError

    # --- navigation (shared) ---
    async def _show_current(self, interaction: discord.Interaction) -> None:
        view = self.flow.current_view()
        embed = view.render() if hasattr(view, "render") else None
        # ``safe_edit`` edits the wizard message in place whether or not the
        # step deferred first.  Resource-creating steps (log channel, reward
        # role) defer to beat Discord's 3-second interaction deadline, so the
        # navigation that runs after their slow work must not assume the
        # response is still un-acknowledged.
        await safe_edit(interaction, embed=embed, view=view)
        # Persist the new position so a bot restart can revive this message in
        # place at the right step (migration 099). Best-effort; never blocks nav.
        await self.flow.persist_progress()

    async def skip(self, interaction: discord.Interaction) -> None:
        self.flow.record_skipped(self.title)
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
# Step 0 — What kind of server is this?  (server-type starter set)
# ---------------------------------------------------------------------------
#
# The opening step makes the old metadata-only ``purpose`` section actually *do*
# something: you pick what kind of server you run and we instantly switch on a
# curated bundle of safe defaults for it (owner decision Q-C, 2026-06-24 —
# "fastest, nothing irreversible").
#
# Design decision — the direct-apply path (the plan flagged "presets are
# draft-only today; needs a design decision before building"): these starter
# sets are **pure settings bundles** applied through the same audited
# ``SettingsMutationPipeline`` every other spine step uses (``_set``).  They
# deliberately do **not** reuse the draft-only
# ``services.automation_templates.SERVER_PRESETS``, which bind channels and
# create roles/rules and so need operator picks plus a Final Review — the wrong
# shape for a one-tap, instant, fully-reversible starter.  Every value here is a
# channel-independent boolean/scalar, so picking a type never creates or binds
# anything and can be changed later from each feature's own panel.


@dataclass(frozen=True)
class _ServerTypePreset:
    """One server-type starter set — a bundle of safe, reversible settings."""

    key: str
    label: str
    emoji: str
    blurb: str  # one-line plain summary of what it switches on
    # (subsystem, setting-name, value), applied verbatim through ``_set``.
    settings: tuple[tuple[str, str, object], ...]
    # Key into ``_XP_RATES`` (resolved at apply time), or None to leave XP as-is.
    xp_rate: str | None = None


# The five starter sets.  Each uses only the channel-independent settings the
# other spine steps already write (automod toggles, moderation dm-on-action, the
# XP rate), so nothing here needs a channel/role pick or creates a resource.
_SERVER_TYPES: tuple[_ServerTypePreset, ...] = (
    _ServerTypePreset(
        key="community",
        label="Community",
        emoji="💬",
        blurb="balanced spam protection, members told why they're actioned, steady XP",
        settings=(
            ("automod", "enabled", True),
            ("automod", "spam_enabled", True),
            ("automod", "invites_enabled", True),
            ("automod", "caps_enabled", False),
            ("automod", "mentions_enabled", True),
            ("moderation", "dm_on_action", True),
        ),
        xp_rate="standard",
    ),
    _ServerTypePreset(
        key="gaming",
        label="Gaming",
        emoji="🎮",
        blurb="spam & mass-ping protection (invite links allowed), faster XP",
        settings=(
            ("automod", "enabled", True),
            ("automod", "spam_enabled", True),
            ("automod", "invites_enabled", False),
            ("automod", "caps_enabled", False),
            ("automod", "mentions_enabled", True),
            ("moderation", "dm_on_action", True),
        ),
        xp_rate="active",
    ),
    _ServerTypePreset(
        key="support",
        label="Support / Help desk",
        emoji="🛟",
        blurb="strict protection on everything, members told why, relaxed XP",
        settings=(
            ("automod", "enabled", True),
            ("automod", "spam_enabled", True),
            ("automod", "invites_enabled", True),
            ("automod", "caps_enabled", True),
            ("automod", "mentions_enabled", True),
            ("moderation", "dm_on_action", True),
        ),
        xp_rate="relaxed",
    ),
    _ServerTypePreset(
        key="creator",
        label="Creator / Content",
        emoji="🎨",
        blurb="balanced spam protection, members told why, steady XP",
        settings=(
            ("automod", "enabled", True),
            ("automod", "spam_enabled", True),
            ("automod", "invites_enabled", True),
            ("automod", "caps_enabled", False),
            ("automod", "mentions_enabled", True),
            ("moderation", "dm_on_action", True),
        ),
        xp_rate="standard",
    ),
    _ServerTypePreset(
        key="exploring",
        label="Just exploring",
        emoji="🧭",
        blurb="just basic spam protection — set everything else up yourself",
        settings=(
            ("automod", "enabled", True),
            ("automod", "spam_enabled", True),
        ),
        xp_rate=None,
    ),
)


def _server_type(key: str) -> _ServerTypePreset | None:
    for preset in _SERVER_TYPES:
        if preset.key == key:
            return preset
    return None


class _ServerTypeSelect(discord.ui.Select):  # type: ignore[type-arg]
    def __init__(self, current: str | None) -> None:
        options = [
            discord.SelectOption(
                label=preset.label,
                value=preset.key,
                emoji=preset.emoji,
                description=preset.blurb[:100],
                default=preset.key == current,
            )
            for preset in _SERVER_TYPES
        ]
        super().__init__(
            placeholder="What kind of server is this?",
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ServerTypeStep = self.view  # type: ignore[assignment]
        view.server_type = self.values[0]
        await interaction.response.edit_message(embed=view.render(), view=view)


class _ServerTypeSaveButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="Save & continue",
            emoji="✨",
            style=discord.ButtonStyle.success,
            row=3,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ServerTypeStep = self.view  # type: ignore[assignment]
        await view.apply(interaction)


class ServerTypeStep(_StepView):
    title = "What kind of server is this?"
    skip_label = "Skip — set things up myself"

    def __init__(self, flow: EssentialFlow) -> None:
        self.server_type: str | None = None
        super().__init__(flow)

    def build_items(self) -> None:
        self.add_item(_ServerTypeSelect(self.server_type))
        self.add_item(_ServerTypeSaveButton())

    def render(self) -> discord.Embed:
        embed = discord.Embed(
            title="✨ What kind of server is this?",
            description=(
                "Pick the closest match and we'll switch on a set of safe, "
                "sensible defaults right away — you can change any of it later. "
                "We won't create or delete anything; this just turns on a few "
                "settings to get you started.\n\n"
                "Then press **Save & continue**."
            ),
            color=discord.Color.blurple(),
        )
        if self.server_type:
            preset = _server_type(self.server_type)
            if preset is not None:
                embed.add_field(
                    name="Starter set",
                    value=f"{preset.emoji} **{preset.label}** — {preset.blurb}",
                    inline=False,
                )
        else:
            embed.add_field(
                name="Starter set",
                value="_pick one above_",
                inline=False,
            )
        embed.set_footer(text=self.flow.step_counter())
        return embed

    async def apply(self, interaction: discord.Interaction) -> None:
        if self.server_type is None:
            await interaction.response.send_message(
                "Pick the kind of server you run first — or press Skip.",
                ephemeral=True,
            )
            return
        preset = _server_type(self.server_type)
        if preset is None:  # defensive — the picker only offers known keys
            await interaction.response.send_message(
                "That server type isn't available — please pick another.",
                ephemeral=True,
            )
            return
        try:
            for subsystem, name, value in preset.settings:
                await self._set(subsystem, name, value)
            if preset.xp_rate is not None:
                _label, xp_min, xp_max, cooldown = _XP_RATES[preset.xp_rate]
                await self._set("xp", "xp_min", xp_min)
                await self._set("xp", "xp_max", xp_max)
                await self._set("xp", "xp_cooldown", cooldown)
        except Exception:
            logger.exception("essential setup: server-type step apply failed")
            await interaction.response.send_message(
                "Something went wrong applying the starter set — please try again.",
                ephemeral=True,
            )
            return
        await self.complete(
            interaction,
            f"{preset.emoji} {preset.label} starter set on · {preset.blurb}",
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
            label="Save & continue",
            emoji="👋",
            style=discord.ButtonStyle.success,
            row=3,
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
                "**Save & continue**."
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
            label="Save & continue",
            emoji="🛡️",
            style=discord.ButtonStyle.success,
            row=3,
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


class _SpamFilterSelect(discord.ui.Select):  # type: ignore[type-arg]
    def __init__(self, selected: set[str]) -> None:
        options = [
            discord.SelectOption(label=label, value=key, default=key in selected)
            for key, label in _SPAM_FILTERS
        ]
        super().__init__(
            placeholder="What should I clean up? (all on by default)",
            min_values=0,
            max_values=len(options),
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: BlockSpamStep = self.view  # type: ignore[assignment]
        view.filters = set(self.values)
        view.refresh_items()
        await interaction.response.edit_message(embed=view.render(), view=view)


class _SpamSaveButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="Save & continue",
            emoji="🧹",
            style=discord.ButtonStyle.success,
            row=3,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: BlockSpamStep = self.view  # type: ignore[assignment]
        await view.apply(interaction)


class BlockSpamStep(_StepView):
    title = "Block spam and bad links"
    skip_label = "Skip spam protection"

    def __init__(self, flow: EssentialFlow) -> None:
        self.filters: set[str] = {key for key, _ in _SPAM_FILTERS}
        super().__init__(flow)

    def build_items(self) -> None:
        self.refresh_items()

    def refresh_items(self) -> None:
        for child in list(self.children):
            if isinstance(child, (_SpamFilterSelect, _SpamSaveButton)):
                self.remove_item(child)
        self.add_item(_SpamFilterSelect(self.filters))
        self.add_item(_SpamSaveButton())

    def render(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🧹 {self.title}",
            description=(
                "Automatically clean up the noise so you don't have to. "
                "Everything is on by default — untick anything you want to "
                "allow, then press **Save & continue**."
            ),
            color=discord.Color.blurple(),
        )
        for key, label in _SPAM_FILTERS:
            embed.add_field(
                name=label,
                value="On" if key in self.filters else "Off",
                inline=True,
            )
        embed.set_footer(text=self.flow.step_counter())
        return embed

    async def apply(self, interaction: discord.Interaction) -> None:
        try:
            await self._set("automod", "enabled", True)
            for key, _ in _SPAM_FILTERS:
                await self._set("automod", key, key in self.filters)
        except Exception:
            logger.exception("essential setup: block-spam step apply failed")
            await interaction.response.send_message(
                "Something went wrong turning on protection — please try again.",
                ephemeral=True,
            )
            return
        on_labels = [label for key, label in _SPAM_FILTERS if key in self.filters]
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


class _ChannelNamesModal(discord.ui.Modal, title="Name the new channels"):  # type: ignore[call-arg]
    """Optional: type custom names for the channel(s) we auto-create."""

    mod_name = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Moderation log channel name",
        required=False,
        max_length=90,
    )
    activity_name = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Activity log channel name",
        required=False,
        max_length=90,
    )

    def __init__(self, view: LogChannelStep) -> None:
        super().__init__()
        self._view = view
        self.mod_name.default = view.mod_channel_name or _NEW_MOD_CHANNEL_NAME
        self.activity_name.default = (
            view.activity_channel_name or _NEW_ACTIVITY_CHANNEL_NAME
        )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self._view.mod_channel_name = self.mod_name.value.strip() or None
        self._view.activity_channel_name = self.activity_name.value.strip() or None
        self._view.refresh_items()
        await interaction.response.edit_message(
            embed=self._view.render(),
            view=self._view,
        )


class _NameChannelsButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="✏️ Name the new channel(s)",
            style=discord.ButtonStyle.secondary,
            row=3,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: LogChannelStep = self.view  # type: ignore[assignment]
        await interaction.response.send_modal(_ChannelNamesModal(view))


class _LogSaveButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="Save & continue",
            emoji="📋",
            style=discord.ButtonStyle.success,
            row=3,
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
        # Optional custom names for channels we auto-create (None = default).
        self.mod_channel_name: str | None = None
        self.activity_channel_name: str | None = None
        super().__init__(flow)

    def build_items(self) -> None:
        self.refresh_items()

    def refresh_items(self) -> None:
        """(Re)build the controls from current state (rows 0/1/2/3).

        Rebuilt on every interaction so the multi-select reflects ``activity``;
        the channel pickers reset visually but the chosen ids persist on the
        view and are shown in the embed.
        """
        for child in list(self.children):
            if isinstance(
                child,
                (
                    _ActivityTypeSelect,
                    _LogChannelPicker,
                    _NameChannelsButton,
                    _LogSaveButton,
                ),
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
        self.add_item(_NameChannelsButton())
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
                f"**#{_NEW_ACTIVITY_CHANNEL_NAME}** — or tap ✏️ to name it). "
                "Then press **Save & continue**."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Moderation log",
            value=self._where(
                self.mod_channel_id,
                self.mod_channel_name or _NEW_MOD_CHANNEL_NAME,
            ),
            inline=False,
        )
        if self.activity:
            picked = ", ".join(
                label for flag, label, _ in _ACTIVITY_TYPES if flag in self.activity
            )
            activity_where = self._where(
                self.activity_channel_id,
                self.activity_channel_name or _NEW_ACTIVITY_CHANNEL_NAME,
            )
            embed.add_field(
                name="Activity log",
                value=f"{activity_where}\n_Logging: {picked}_",
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
        # Creating up to two channels + writing the logging settings/bindings
        # runs well past Discord's 3-second interaction-token deadline, so
        # acknowledge the click FIRST.  Without this the channels are created
        # but the final navigation edit 404s ("This interaction failed") — and
        # because the create already happened, every retry leaks another
        # #mod-log / #server-log pair (the reported "keeps building logging
        # channels and says the step failed" bug).
        if not await safe_defer(interaction):
            return
        created: list[str] = []
        mod_name = self.mod_channel_name or _NEW_MOD_CHANNEL_NAME
        activity_name = self.activity_channel_name or _NEW_ACTIVITY_CHANNEL_NAME
        # Moderation log is the always-on baseline — resolve (or create) it.
        mod_id = self.mod_channel_id
        if mod_id is None:
            mod_id = await self._create_channel(interaction, mod_name)
            if mod_id is None:
                return  # creation failed; error already surfaced
            created.append(mod_name)
        # Activity log only when at least one activity category is ticked.
        activity_id: int | None = None
        if self.activity:
            activity_id = self.activity_channel_id
            if activity_id is None:
                activity_id = await self._create_channel(interaction, activity_name)
                if activity_id is None:
                    return
                created.append(activity_name)
        try:
            await self._set("logging", "enabled", True)
            await self._bind("mod_channel", mod_id)
            for flag, _, _ in _ACTIVITY_TYPES:
                await self._set("logging", flag, flag in self.activity)
            if activity_id is not None:
                await self._bind("events_channel", activity_id)
        except Exception:
            logger.exception("essential setup: log-channel step apply failed")
            await safe_followup(
                interaction,
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
            await safe_followup(
                interaction,
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
# Step 5 — Reward active members  (xp rate + level/time role rewards)
# ---------------------------------------------------------------------------
#
# Two screens in one step (an internal ``phase``).  Screen 1: pick an XP rate
# (or keep the current one) and which role rewards to switch on (level-up and/or
# time-in-server — both/one/none).  Screen 2 (only when a reward is on): choose
# the reward role — recommended (auto-create @Regular) / create one you name /
# reuse an existing role.  On Save: set the XP rate scalars through the audited
# Settings pipeline, then call ``role_automation.set_xp_threshold`` /
# ``set_time_threshold`` (the existing direct-apply audited paths) on the role,
# auto-creating it via ``RoleLifecycleService`` when asked.  Every service is
# lazy-imported per the setup-view no-top-level-pipeline-import convention.  XP
# itself is always on (no guild enable; per-user opt-out lives in participation),
# so this step tunes the *reward experience* — it does not switch XP on.

# XP rate presets: key -> (operator label, xp_min, xp_max, cooldown_seconds).
# "standard" mirrors the schema defaults (15/25/60).
_XP_RATES: dict[str, tuple[str, int, int, int]] = {
    "relaxed": ("Relaxed — slower leveling", 10, 15, 120),
    "standard": ("Standard — balanced", 15, 25, 60),
    "active": ("Active — faster leveling", 20, 40, 30),
}
# Reward triggers: key -> operator label.
_REWARD_TYPES: list[tuple[str, str]] = [
    ("level", "When members reach a level"),
    ("time", "When members stay a while"),
]
# How to source the reward role: key -> operator label.
_ROLE_SOURCES: list[tuple[str, str]] = [
    ("recommended", "Recommended — make a @Regular role"),
    ("create", "Create a role I name"),
    ("existing", "Use a role I already have"),
]
_SUGGESTED_ROLE_NAMES: tuple[str, ...] = (
    "Regular",
    "Member",
    "Trusted",
    "Veteran",
    "Active",
    "VIP",
)
_DEFAULT_ROLE_NAME = "Regular"
_DEFAULT_LEVEL = 10
_DEFAULT_DAYS = 30


class _XpRateSelect(discord.ui.Select):  # type: ignore[type-arg]
    def __init__(self, current: str) -> None:
        options = [
            discord.SelectOption(
                label="Keep current XP rate",
                value="keep",
                default=current == "keep",
            ),
            *[
                discord.SelectOption(label=spec[0], value=key, default=current == key)
                for key, spec in _XP_RATES.items()
            ],
        ]
        super().__init__(
            placeholder="How fast should members earn XP?",
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: RewardActivityStep = self.view  # type: ignore[assignment]
        view.xp_rate = self.values[0]
        view.refresh_items()
        await interaction.response.edit_message(embed=view.render(), view=view)


class _RewardTypeSelect(discord.ui.Select):  # type: ignore[type-arg]
    def __init__(self, selected: set[str]) -> None:
        options = [
            discord.SelectOption(label=label, value=key, default=key in selected)
            for key, label in _REWARD_TYPES
        ]
        super().__init__(
            placeholder="Give a role as a reward for… (optional)",
            min_values=0,
            max_values=len(options),
            options=options,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: RewardActivityStep = self.view  # type: ignore[assignment]
        view.rewards = set(self.values)
        view.refresh_items()
        await interaction.response.edit_message(embed=view.render(), view=view)


class _RewardNextButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self, has_rewards: bool) -> None:
        super().__init__(
            label="Next" if has_rewards else "Save & continue",
            emoji="🏅",
            style=discord.ButtonStyle.success,
            row=3,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: RewardActivityStep = self.view  # type: ignore[assignment]
        await view.on_next(interaction)


class _RoleSourceSelect(discord.ui.Select):  # type: ignore[type-arg]
    def __init__(self, current: str) -> None:
        options = [
            discord.SelectOption(label=label, value=key, default=key == current)
            for key, label in _ROLE_SOURCES
        ]
        super().__init__(
            placeholder="Where should the reward role come from?",
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: RewardActivityStep = self.view  # type: ignore[assignment]
        view.role_source = self.values[0]
        view.refresh_items()
        await interaction.response.edit_message(embed=view.render(), view=view)


class _RoleNameSelect(discord.ui.Select):  # type: ignore[type-arg]
    def __init__(self, current: str | None) -> None:
        options = [
            discord.SelectOption(label=name, value=name, default=name == current)
            for name in _SUGGESTED_ROLE_NAMES
        ]
        super().__init__(placeholder="Name for the new role…", options=options, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        view: RewardActivityStep = self.view  # type: ignore[assignment]
        view.new_role_name = self.values[0]
        view.refresh_items()
        await interaction.response.edit_message(embed=view.render(), view=view)


class _RewardRoleSelect(discord.ui.RoleSelect):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick the role to grant…",
            min_values=0,
            max_values=1,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: RewardActivityStep = self.view  # type: ignore[assignment]
        if self.values:
            view.existing_role_id = self.values[0].id
            view.existing_role_name = self.values[0].name
        else:
            view.existing_role_id = None
            view.existing_role_name = None
        view.refresh_items()
        await interaction.response.edit_message(embed=view.render(), view=view)


class _RoleNameModal(discord.ui.Modal, title="Name the reward role"):  # type: ignore[call-arg]
    """Optional: type a custom name for the role we create."""

    role_name = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Role name",
        required=False,
        max_length=90,
    )

    def __init__(self, view: RewardActivityStep) -> None:
        super().__init__()
        self._view = view
        self.role_name.default = view.new_role_name or _DEFAULT_ROLE_NAME

    async def on_submit(self, interaction: discord.Interaction) -> None:
        self._view.new_role_name = self.role_name.value.strip() or None
        self._view.role_source = "create"
        self._view.refresh_items()
        await interaction.response.edit_message(
            embed=self._view.render(),
            view=self._view,
        )


class _TypeRoleNameButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="✏️ Type a name",
            style=discord.ButtonStyle.secondary,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: RewardActivityStep = self.view  # type: ignore[assignment]
        await interaction.response.send_modal(_RoleNameModal(view))


class _RewardSaveButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="Save & continue",
            emoji="🏅",
            style=discord.ButtonStyle.success,
            row=3,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: RewardActivityStep = self.view  # type: ignore[assignment]
        await view.apply(interaction)


class RewardActivityStep(_StepView):
    title = "Reward active members"
    skip_label = "Skip rewards"

    def __init__(self, flow: EssentialFlow) -> None:
        self.phase: str = "config"  # "config" | "roles"
        self.xp_rate: str = "keep"
        self.rewards: set[str] = set()
        self.role_source: str = "recommended"
        self.new_role_name: str | None = None
        self.existing_role_id: int | None = None
        self.existing_role_name: str | None = None
        super().__init__(flow)

    def build_items(self) -> None:
        self.refresh_items()

    def refresh_items(self) -> None:
        """(Re)build the controls for the current phase (rows 0/1/2)."""
        own = (
            _XpRateSelect,
            _RewardTypeSelect,
            _RewardNextButton,
            _RoleSourceSelect,
            _RoleNameSelect,
            _TypeRoleNameButton,
            _RewardRoleSelect,
            _RewardSaveButton,
        )
        for child in list(self.children):
            if isinstance(child, own):
                self.remove_item(child)
        if self.phase == "config":
            self.add_item(_XpRateSelect(self.xp_rate))
            self.add_item(_RewardTypeSelect(self.rewards))
            self.add_item(_RewardNextButton(bool(self.rewards)))
        else:
            self.add_item(_RoleSourceSelect(self.role_source))
            if self.role_source == "create":
                self.add_item(_RoleNameSelect(self.new_role_name))
                self.add_item(_TypeRoleNameButton())
            elif self.role_source == "existing":
                self.add_item(_RewardRoleSelect())
            self.add_item(_RewardSaveButton())

    async def go_back(self, interaction: discord.Interaction) -> None:
        # Screen 2 "Back" returns to screen 1; screen 1 "Back" leaves the step.
        if self.phase == "roles":
            self.phase = "config"
            self.refresh_items()
            await safe_edit(interaction, embed=self.render(), view=self)
        else:
            await super().go_back(interaction)

    def render(self) -> discord.Embed:
        return self._render_config() if self.phase == "config" else self._render_roles()

    def _render_config(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🏅 {self.title}",
            description=(
                "Members earn XP as they chat and level up. Choose how fast XP "
                "comes in, and — if you like — give members a role when they "
                "reach a level or stay a while.\n\n"
                "Pick what you want, then press **Next**."
            ),
            color=discord.Color.blurple(),
        )
        rate = "Keep current" if self.xp_rate == "keep" else _XP_RATES[self.xp_rate][0]
        embed.add_field(name="XP rate", value=rate, inline=False)
        if self.rewards:
            picked = ", ".join(
                label for key, label in _REWARD_TYPES if key in self.rewards
            )
            embed.add_field(name="Give a reward role", value=picked, inline=False)
        else:
            embed.add_field(
                name="Give a reward role",
                value="_off — no role rewards_",
                inline=False,
            )
        embed.set_footer(text=self.flow.step_counter())
        return embed

    def _render_roles(self) -> discord.Embed:
        embed = discord.Embed(
            title="🏅 Choose the reward role",
            description=(
                "Which role should members earn?\n"
                "• **Recommended** — we make a fresh **@Regular**\n"
                "• **Create a role I name** — pick a name, we make it\n"
                "• **Use a role I already have** — choose one below"
            ),
            color=discord.Color.blurple(),
        )
        if self.role_source == "existing":
            role = (
                f"<@&{self.existing_role_id}>"
                if self.existing_role_id
                else "_pick one below_"
            )
        elif self.role_source == "create":
            role = f"a new **@{self.new_role_name or _DEFAULT_ROLE_NAME}**"
        else:
            role = f"a new **@{_DEFAULT_ROLE_NAME}**"
        embed.add_field(name="Reward role", value=role, inline=False)
        triggers = []
        if "level" in self.rewards:
            triggers.append(f"at level {_DEFAULT_LEVEL}")
        if "time" in self.rewards:
            triggers.append(f"after {_DEFAULT_DAYS} days")
        embed.add_field(name="Granted", value=" and ".join(triggers), inline=False)
        embed.set_footer(text=self.flow.step_counter())
        return embed

    async def on_next(self, interaction: discord.Interaction) -> None:
        if not self.rewards:
            # No role rewards — apply the XP rate (if changed) and finish.
            # XP-rate writes can run past the 3s deadline, so acknowledge first
            # (same deadline reasoning as LogChannelStep.apply).
            if not await safe_defer(interaction):
                return
            await self._apply_and_complete(
                interaction,
                role_id=None,
                role_name=None,
                created=False,
            )
            return
        # Instant in-memory screen swap — no slow work, so no defer needed.
        self.phase = "roles"
        self.refresh_items()
        await safe_edit(interaction, embed=self.render(), view=self)

    async def apply(self, interaction: discord.Interaction) -> None:
        # Screen 2 "Save" — creating a role + writing the XP rate and reward
        # thresholds runs past Discord's 3-second deadline, so acknowledge
        # first (mirrors LogChannelStep.apply; without it a created role would
        # be orphaned on the "interaction failed" retry).
        if not await safe_defer(interaction):
            return
        # Resolve the reward role, then apply everything.
        role_id, role_name, created = await self._resolve_role(interaction)
        if role_id is None:
            return  # error already surfaced
        await self._apply_and_complete(
            interaction,
            role_id=role_id,
            role_name=role_name,
            created=created,
        )

    async def _apply_and_complete(
        self,
        interaction: discord.Interaction,
        *,
        role_id: int | None,
        role_name: str | None,
        created: bool,
    ) -> None:
        try:
            if self.xp_rate != "keep":
                _label, xp_min, xp_max, cooldown = _XP_RATES[self.xp_rate]
                await self._set("xp", "xp_min", xp_min)
                await self._set("xp", "xp_max", xp_max)
                await self._set("xp", "xp_cooldown", cooldown)
            if self.rewards and role_id is not None and role_name is not None:
                await self._set_rewards(role_id, role_name)
        except Exception:
            logger.exception("essential setup: reward step apply failed")
            await safe_followup(
                interaction,
                "Something went wrong saving rewards — please try again.",
                ephemeral=True,
            )
            return
        await self.complete(interaction, self._summary(role_id, created))

    async def _resolve_role(
        self,
        interaction: discord.Interaction,
    ) -> tuple[int | None, str | None, bool]:
        """Resolve the reward role to (id, name, created?), or (None, …) on error."""
        if self.role_source == "existing":
            if self.existing_role_id is None:
                await safe_followup(
                    interaction,
                    "Pick a role to grant, or switch to **Recommended** to make one.",
                    ephemeral=True,
                )
                return None, None, False
            return self.existing_role_id, self.existing_role_name, False
        name = (
            self.new_role_name
            if self.role_source == "create" and self.new_role_name
            else _DEFAULT_ROLE_NAME
        )
        created_id = await self._create_role(interaction, name)
        if created_id is None:
            return None, None, False
        return created_id, name, True

    async def _create_role(
        self,
        interaction: discord.Interaction,
        name: str,
    ) -> int | None:
        """Create the reward role through the audited role-lifecycle creator."""
        from services.role_lifecycle_service import (
            RoleLifecycleRequest,
            RoleLifecycleService,
        )

        result = await RoleLifecycleService().apply(
            self.flow.guild,
            RoleLifecycleRequest(operation="create", name=name),
            self.flow.author,
            confirmed=True,
        )
        if not result.applied:
            logger.warning(
                "essential setup: reward role create failed (guild=%s): %s",
                self.flow.guild.id,
                result.first_error,
            )
            await safe_followup(
                interaction,
                "Couldn't make the role — please reuse an existing one instead.",
                ephemeral=True,
            )
            return None
        return result.applied[0].target_id

    async def _set_rewards(self, role_id: int, role_name: str) -> None:
        """Set the level / time role rewards through ``role_automation`` (the
        existing direct-apply audited path).  Lazy-imported per the setup-view
        convention.
        """
        from services import role_automation

        if "level" in self.rewards:
            await role_automation.set_xp_threshold(
                guild_id=self.flow.guild.id,
                role_id=role_id,
                role_name=role_name,
                level=_DEFAULT_LEVEL,
                actor_id=self.flow.author.id,
            )
        if "time" in self.rewards:
            await role_automation.set_time_threshold(
                guild_id=self.flow.guild.id,
                role_id=role_id,
                role_name=role_name,
                days=_DEFAULT_DAYS,
                actor_id=self.flow.author.id,
            )

    def _summary(self, role_id: int | None, created: bool) -> str:
        parts: list[str] = []
        if self.xp_rate != "keep":
            parts.append(
                f"XP rate {_XP_RATES[self.xp_rate][0].split(' — ')[0].lower()}",
            )
        if self.rewards and role_id is not None:
            triggers = []
            if "level" in self.rewards:
                triggers.append(f"level {_DEFAULT_LEVEL}")
            if "time" in self.rewards:
                triggers.append(f"{_DEFAULT_DAYS} days")
            verb = "new role" if created else "role"
            parts.append(f"{verb} <@&{role_id}> at {' / '.join(triggers)}")
        if not parts:
            return "Rewards: no changes"
        return "Rewards on · " + " · ".join(parts)


# ---------------------------------------------------------------------------
# Step 6 — Set up a help desk  (tickets)
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
            label="Save & continue",
            emoji="🎫",
            style=discord.ButtonStyle.success,
            row=3,
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
                "Then press **Save & continue**."
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
# Step 7 — Where can people use commands?  (command-access scope)
# ---------------------------------------------------------------------------
#
# The enforced "where does the bot listen" control, surfaced in plain language.
# Backed by the audited Command Access seam (``services.command_access_service``)
# — the same per-server policy ``!settings`` edits and the runtime command gate
# reads — so a choice here takes effect immediately for *both* prefix and slash
# commands.  Three plain outcomes map to the three stored modes:
#   • "Anywhere on the server"        → ``all_channels`` (the default)
#   • "Only in channels I choose"     → ``selected_channels`` (+ an allow-list)
#   • "Off for members — admins only" → ``disabled_except_bootstrap``
# Adding this step also makes the bot's own "enable them via ``!setup``" /
# "update Command Access in ``!settings``" denial messages true — before it,
# ``!setup`` had no command-access step at all.  ``command_access_service`` is
# lazy-imported inside ``apply`` (setup views must not import mutation services
# at module top level) and takes ``actor_type="admin"`` — the wizard entry is
# already administrator-gated, and the service rejects a "user" actor here.

# (stored mode, operator label, one-line plain description).
_CMD_ACCESS_CHOICES: list[tuple[str, str, str]] = [
    (
        "all_channels",
        "Anywhere on the server",
        "Members can use commands in every channel.",
    ),
    (
        "selected_channels",
        "Only in channels I choose",
        "Commands work only in the channels you pick below.",
    ),
    (
        "disabled_except_bootstrap",
        "Off for members — admins only",
        "Members can't use commands; you keep admin access for setup.",
    ),
]
_CMD_ACCESS_LABELS: dict[str, str] = {
    mode: label for mode, label, _ in _CMD_ACCESS_CHOICES
}


class _CmdAccessModeSelect(discord.ui.Select):  # type: ignore[type-arg]
    def __init__(self, current: str) -> None:
        options = [
            discord.SelectOption(
                label=label,
                value=mode,
                description=desc,
                default=mode == current,
            )
            for mode, label, desc in _CMD_ACCESS_CHOICES
        ]
        super().__init__(
            placeholder="Where can people use commands?",
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: CommandChannelsStep = self.view  # type: ignore[assignment]
        view.mode = self.values[0]
        view.refresh_items()
        await interaction.response.edit_message(embed=view.render(), view=view)


class _CmdAccessChannelSelect(discord.ui.ChannelSelect):  # type: ignore[type-arg]
    """Shown only in the "only in channels I choose" mode — the allow-list."""

    def __init__(self) -> None:
        super().__init__(
            placeholder="Pick the channels where commands should work…",
            channel_types=[discord.ChannelType.text],
            min_values=0,
            max_values=25,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: CommandChannelsStep = self.view  # type: ignore[assignment]
        view.channel_ids = [c.id for c in self.values]
        view.refresh_items()
        await interaction.response.edit_message(embed=view.render(), view=view)


class _CmdAccessSaveButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="Save & continue",
            emoji="🚪",
            style=discord.ButtonStyle.success,
            row=3,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: CommandChannelsStep = self.view  # type: ignore[assignment]
        await view.apply(interaction)


class CommandChannelsStep(_StepView):
    title = "Where can people use commands?"
    skip_label = "Skip — leave as is"

    def __init__(self, flow: EssentialFlow) -> None:
        self.mode: str = "all_channels"
        self.channel_ids: list[int] = []
        super().__init__(flow)

    def build_items(self) -> None:
        self.refresh_items()

    def refresh_items(self) -> None:
        """(Re)build the mode picker + (only when limiting) the channel picker."""
        for child in list(self.children):
            if isinstance(
                child,
                (_CmdAccessModeSelect, _CmdAccessChannelSelect, _CmdAccessSaveButton),
            ):
                self.remove_item(child)
        self.add_item(_CmdAccessModeSelect(self.mode))
        if self.mode == "selected_channels":
            self.add_item(_CmdAccessChannelSelect())
        self.add_item(_CmdAccessSaveButton())

    def render(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🚪 {self.title}",
            description=(
                "Choose where members can use the bot's commands. By default "
                "they work everywhere — you can keep that, limit them to a few "
                "channels, or turn them off for everyone but admins.\n\n"
                "Pick one below, then press **Save & continue**."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Setting",
            value=_CMD_ACCESS_LABELS.get(self.mode, self.mode),
            inline=False,
        )
        if self.mode == "selected_channels":
            if self.channel_ids:
                where = ", ".join(f"<#{cid}>" for cid in self.channel_ids)
            else:
                where = "_pick at least one channel above_"
            embed.add_field(name="Allowed channels", value=where, inline=False)
        embed.set_footer(text=self.flow.step_counter())
        return embed

    async def apply(self, interaction: discord.Interaction) -> None:
        if self.mode == "selected_channels" and not self.channel_ids:
            await interaction.response.send_message(
                "Pick at least one channel where commands should work — or "
                "choose **Anywhere on the server**.",
                ephemeral=True,
            )
            return
        try:
            from services.command_access_service import set_policy

            await set_policy(
                guild_id=self.flow.guild.id,
                mode=self.mode,
                channel_ids=(
                    self.channel_ids if self.mode == "selected_channels" else None
                ),
                actor_id=self.flow.author.id,
            )
        except Exception:
            logger.exception("essential setup: command-channels step apply failed")
            await interaction.response.send_message(
                "Something went wrong saving where commands work — please try again.",
                ephemeral=True,
            )
            return
        await self.complete(interaction, self._summary())

    def _summary(self) -> str:
        if self.mode == "selected_channels":
            count = len(self.channel_ids)
            if count == 1:
                return f"Commands limited to <#{self.channel_ids[0]}>"
            return f"Commands limited to {count} channels"
        if self.mode == "disabled_except_bootstrap":
            return "Commands off for members (admins keep access)"
        return "Commands available in every channel"


# ---------------------------------------------------------------------------
# Extras menu — optional features the spine doesn't cover
# ---------------------------------------------------------------------------
#
# Plan §5 "off-spine": the spine handles the universal essentials; everything
# else the bot can do is offered here as a one-tap menu of extras you skipped
# (reachable from the "All done" summary).  Each extra is surfaced with what it
# does and the exact command to open its full setup — the discoverability win
# the consolidation audit asked for — rather than re-implementing every
# feature's config inside the spine (a much larger per-feature effort that would
# duplicate the existing panels).  Native giveaways are intentionally absent:
# that feature isn't built yet, so listing a command would mislead.


@dataclass(frozen=True)
class _Extra:
    """One optional feature shown in the extras menu."""

    emoji: str
    label: str
    blurb: str  # one plain line of what it does
    command: str  # the command that opens its full setup


_EXTRAS: tuple[_Extra, ...] = (
    _Extra(
        "🏆",
        "Hall of Fame",
        "pin the messages your members love the most",
        "!starboard",
    ),
    _Extra(
        "🔢",
        "Live member counts",
        "show member and online counts right in your channel list",
        "!counters",
    ),
    _Extra(
        "🛡️",
        "Raid & new-account protection",
        "slow down raids and hold brand-new accounts for a look",
        "!security",
    ),
    _Extra(
        "🖼️",
        "Image filtering",
        "catch unwanted images automatically",
        "!imagemod",
    ),
    _Extra(
        "🙏",
        "Thanks & Karma",
        "let members thank each other and build up reputation",
        "!karma",
    ),
    _Extra(
        "🤖",
        "AI helper",
        "let members ask the bot questions in plain language",
        "!aimenu",
    ),
    _Extra(
        "🎭",
        "Reaction roles",
        "let members pick their own roles by reacting",
        "!reactroles",
    ),
)


def build_extras_embed() -> discord.Embed:
    """Render the one-screen extras menu (kept here so its copy stays plain)."""
    embed = discord.Embed(
        title="✨ More you can set up",
        description=(
            "These are all optional — turn on any that fit your server. "
            "Run the command shown under each one to set it up."
        ),
        color=discord.Color.blurple(),
    )
    for extra in _EXTRAS:
        embed.add_field(
            name=f"{extra.emoji} {extra.label}",
            value=f"{extra.blurb}\nOpen with `{extra.command}`",
            inline=False,
        )
    return embed


# ---------------------------------------------------------------------------
# Check my setup — a plain-language health check
# ---------------------------------------------------------------------------
#
# Plan §3: the read-only scan / readiness / diagnostics steps move *out* of the
# completion path into one optional "Check my setup" button.  It reads the same
# data the advanced diagnostics use (``services.setup_readiness.collect``) but
# renders it in outcome language — a "how set up are you" headline plus a
# ✅ / ➖ list of the essentials — with none of the bindings/settings vocabulary
# the raw diagnostics embed exposes.

#: Essentials shown in the health check, mapped to plain operator-facing labels.
_CHECK_ESSENTIALS: tuple[tuple[str, str], ...] = (
    ("welcome", "Greeting new members"),
    ("moderation", "Moderator tools"),
    ("automod", "Spam & bad-link protection"),
    ("logging", "Activity logging"),
    ("xp", "Member rewards"),
    ("ticket", "Help desk"),
)


async def build_check_setup_embed(guild: discord.Guild) -> discord.Embed:
    """Render the "Check my setup" health embed (plain language, no jargon)."""
    from services import setup_readiness

    report = await setup_readiness.collect(guild.id, guild=guild)
    by_name = {sr.subsystem: sr for sr in report.per_subsystem}

    lines: list[str] = []
    done = 0
    for key, label in _CHECK_ESSENTIALS:
        sr = by_name.get(key)
        configured = sr is not None and (sr.bindings_bound + sr.settings_configured) > 0
        if configured:
            done += 1
        lines.append(f"{'✅' if configured else '➖'} {label}")

    total = len(_CHECK_ESSENTIALS)
    if done == total:
        headline = "🎉 Everything essential is set up — nice work!"
        color = discord.Color.green()
    elif done == 0:
        headline = "Nothing essential is set up yet — run setup to get started."
        color = discord.Color.orange()
    else:
        headline = f"You've set up **{done} of {total}** essentials so far."
        color = discord.Color.blurple()

    embed = discord.Embed(
        title="🔎 How set up are you?",
        description=headline,
        color=color,
    )
    embed.add_field(name="Essentials", value="\n".join(lines), inline=False)
    if done < total:
        embed.add_field(
            name="Want to finish the rest?",
            value=(
                "Run setup again any time — each step saves the moment you "
                "press its button, so you only do what's left."
            ),
            inline=False,
        )
    return embed


class _ExtrasMenuButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="More to set up",
            emoji="✨",
            style=discord.ButtonStyle.primary,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: EssentialSummaryView = self.view  # type: ignore[assignment]
        extras = ExtrasMenuView(view.flow)
        await interaction.response.edit_message(embed=extras.render(), view=extras)


class _CheckSetupButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="Check my setup",
            emoji="🔎",
            style=discord.ButtonStyle.secondary,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(_NOT_IN_SERVER, ephemeral=True)
            return
        embed = await build_check_setup_embed(guild)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class _BackToSummaryButton(discord.ui.Button):  # type: ignore[type-arg]
    def __init__(self) -> None:
        super().__init__(
            label="Back",
            emoji="◀",
            style=discord.ButtonStyle.secondary,
            row=1,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view: ExtrasMenuView = self.view  # type: ignore[assignment]
        summary = EssentialSummaryView(view.flow)
        await interaction.response.edit_message(embed=summary.render(), view=summary)


class ExtrasMenuView(BaseView):
    """The optional-extras menu, opened from the "All done" summary."""

    def __init__(self, flow: EssentialFlow) -> None:
        super().__init__(flow.author, public=False, timeout=600)
        self.flow = flow
        self.add_item(_BackToSummaryButton())

    def render(self) -> discord.Embed:
        return build_extras_embed()


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
        self.add_item(_ExtrasMenuButton())
        self.add_item(_CheckSetupButton())

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
        embed.add_field(
            name="What next?",
            value=(
                "✨ **More to set up** — optional extras like a Hall of Fame, "
                "reaction roles, or an AI helper.\n"
                "🔎 **Check my setup** — a quick look at what's on and what isn't."
            ),
            inline=False,
        )
        return embed


# ---------------------------------------------------------------------------
# Restart revive — a persistent one-button view that resumes an interrupted flow
# ---------------------------------------------------------------------------
#
# The step views above are short-lived in-memory ``BaseView``s, so after a bot
# restart the wizard message's buttons are dead.  Essential Setup is
# direct-apply, so no configuration is lost — only the live message.  This view
# is the persistent bridge: the launcher cog registers one instance at
# ``cog_load`` and its ``on_ready`` sweep edits each interrupted flow message to
# show this button; clicking it rebuilds the flow at the saved step (migration
# 099) and hands control back to the live wizard.


class EssentialSetupResumeView(PersistentView):
    """Persistent one-button view that revives an interrupted Essential Setup flow.

    Extends :class:`PersistentView` (``timeout=None`` + restart-safe routing) so
    its static-``custom_id`` button keeps working after a bot restart.  It has no
    ``SUBSYSTEM`` and opts out of the standard Help/Back nav — it is a
    single-purpose resume prompt, gated to setup admins in the callback.  The
    launcher cog registers one instance at ``cog_load`` and its ``on_ready``
    sweep edits each interrupted flow message to show this button.
    """

    STANDARD_NAV = False

    @discord.ui.button(
        label="Resume setup",
        emoji="▶",
        style=discord.ButtonStyle.success,
        custom_id="essential_setup:resume",
    )
    async def _resume_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,  # type: ignore[type-arg]
    ) -> None:
        del button
        await self.resume(interaction)

    async def resume(self, interaction: discord.Interaction) -> None:
        """Rebuild the flow at the saved step and hand control back to the wizard."""
        guild = interaction.guild
        member = interaction.user
        if guild is None or not isinstance(member, discord.Member):
            await interaction.response.send_message(_NOT_IN_SERVER, ephemeral=True)
            return

        from services import setup_access, setup_session

        try:
            session = await setup_session.resume_session(guild.id)
        except Exception:
            logger.exception("essential_setup resume: resume_session failed")
            session = None
        if not setup_access.is_setup_admin(member, session):
            await interaction.response.send_message(
                "Only the server owner, an administrator, or a delegated setup "
                "admin can resume setup.",
                ephemeral=True,
            )
            return

        # Rebuild the in-memory flow at the saved step and hand the message back
        # to the live wizard. Clamp defensively in case the step count changed.
        flow = EssentialFlow(member, guild)
        step = session.essential_step if session is not None else None
        if step is not None:
            flow.index = max(0, min(step, flow.total))
        view = flow.current_view()
        embed = view.render() if hasattr(view, "render") else None
        await interaction.response.edit_message(embed=embed, view=view)


def build_resume_message(
    session: object | None,
) -> tuple[discord.Embed, EssentialSetupResumeView]:
    """Embed + view the on-ready sweep edits an interrupted flow message to.

    Tells the operator the bot restarted (so the wizard paused) and offers the
    Resume button that continues from the saved step.  ``session`` is the
    :class:`services.setup_session.SetupSession` (typed loosely so this view
    module needn't import the service at module scope).
    """
    raw_step = getattr(session, "essential_step", None)
    human_step = (raw_step or 0) + 1
    embed = discord.Embed(
        title="⏸️ Setup paused",
        description=(
            "I restarted while you were setting things up, so this wizard "
            "paused for a moment. **Nothing you saved was lost** — each step is "
            "saved the instant you press its button.\n\n"
            f"Click **Resume setup** to pick up where you left off (step "
            f"{human_step})."
        ),
        color=discord.Color.blurple(),
    )
    return embed, EssentialSetupResumeView()


async def revive_essential_flows(bot: object) -> None:
    """Revive every guild's interrupted Essential Setup message in place.

    The on-ready sweep called from the setup cog: edits each in-flight flow
    message to show the persistent Resume button so the operator can pick up
    where they left off after a restart (migration 099).  Per-guild failures are
    isolated.  ``bot`` is the ``commands.Bot`` (typed loosely so this view module
    needn't import the commands extension).  Lives here (not in the cog) so the
    cog stays under its LOC ceiling.
    """
    for guild in list(getattr(bot, "guilds", [])):
        try:
            await revive_one_essential_flow(guild)
        except Exception:
            logger.exception(
                "essential_setup: revive failed for guild=%s",
                getattr(guild, "id", None),
            )


async def revive_one_essential_flow(guild: discord.Guild) -> bool:
    """Edit one guild's in-flight Essential Setup message to show Resume.

    Returns ``True`` when the message was revived; ``False`` when there is no
    in-flight flow, the ids are missing, or the message can't be fetched.  A
    vanished message clears the anchor so the sweep stops retrying it.
    """
    from services import setup_session

    session = await setup_session.resume_session(guild.id)
    if session is None:
        return False
    if session.essential_message_id is None or session.setup_channel_id is None:
        return False

    channel = guild.get_channel(session.setup_channel_id)
    if not isinstance(channel, (discord.TextChannel, discord.Thread)):
        return False

    try:
        message = await channel.fetch_message(session.essential_message_id)
    except discord.NotFound:
        logger.info(
            "essential_setup revive: message %s in guild %d is gone; clearing.",
            session.essential_message_id,
            guild.id,
        )
        await setup_session.clear_essential_anchor(guild.id)
        return False
    except discord.Forbidden:
        logger.warning(
            "essential_setup revive: cannot fetch flow in guild=%d.",
            guild.id,
        )
        return False
    except discord.HTTPException as exc:
        logger.warning(
            "essential_setup revive: HTTP error fetching flow in guild=%d: %s",
            guild.id,
            exc,
        )
        return False

    embed, view = build_resume_message(session)
    try:
        await message.edit(embed=embed, view=view)
    except discord.HTTPException as exc:
        logger.warning(
            "essential_setup revive: edit failed in guild=%d: %s",
            guild.id,
            exc,
        )
        return False
    return True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


_NOT_IN_SERVER = "This can only be used in a server."
_NOT_ADMIN = "Only a server admin can run setup."

#: Shown when the bot can't make a private setup channel (no Manage Channels)
#: and Essential Setup falls back to the invoking channel.
_NO_CHANNEL_HINT = (
    "ℹ️ I couldn't make a private setup channel (I need the **Manage Channels** "
    "permission), so I've opened setup right here instead."
)


def _first_embed(flow: EssentialFlow) -> discord.Embed:
    return flow.current_view().render()  # type: ignore[attr-defined,no-any-return]


async def open_essential_setup_in_setup_channel(
    guild: discord.Guild,
    member: discord.Member,
) -> tuple[discord.TextChannel | None, discord.Message | None, str]:
    """Post the Essential Setup flow into the private ``#superbot-setup`` channel.

    Mirrors :func:`views.setup.wizard.open_setup_workspace`'s contract so the
    ``!setup`` / ``/setup`` commands and the on-join launcher share one shape.
    Returns ``(channel, message, reason)`` with ``reason`` one of:

    * ``"ok"`` — flow posted; ``channel`` + ``message`` are set.
    * ``"no_channel"`` — bot lacks Manage Channels (or Discord refused the
      create); caller should fall back to the invoking channel.
    * ``"post_failed"`` — channel resolved but the flow couldn't be posted.

    The flow is a fresh, author-bound :class:`EssentialFlow` for ``member``;
    navigation edits that message in place, so — unlike the advanced wizard's
    persistent anchor — no session row or cross-restart persistence is needed.

    Imports are lazy: setup view files keep their service imports inside the
    call body (consistent with ``_StepView._set`` and the no-top-level-pipeline
    invariant), and it lets tests patch ``ensure_setup_channel`` at its source.
    """
    from services import setup_session
    from services.setup_channel import ensure_setup_channel

    try:
        session = await setup_session.resume_session(guild.id)
    except Exception:
        logger.exception("essential_setup: resume_session failed (guild=%d)", guild.id)
        session = None

    channel, _was_created = await ensure_setup_channel(
        guild,
        existing_channel_id=(session.setup_channel_id if session is not None else None),
        session=session,
    )
    if channel is None:
        return None, None, "no_channel"

    flow = EssentialFlow(member, guild)
    try:
        message = await channel.send(embed=_first_embed(flow), view=flow.current_view())
    except discord.HTTPException as exc:
        logger.warning(
            "essential_setup: failed to post flow in #%s (guild=%d): %s",
            getattr(channel, "name", "?"),
            guild.id,
            exc,
        )
        return channel, None, "post_failed"

    # Record the flow's anchor (message id + step 0) and mark the session
    # in-progress so the on-ready sweep can revive this message in place after a
    # restart (migration 099). Best-effort: the live flow works without it; only
    # cross-restart resume depends on it. The channel is the persisted
    # ``setup_channel_id``, so the sweep re-fetches the message from there.
    try:
        await setup_session.set_essential_anchor(guild.id, message.id, 0)
        await setup_session.mark_in_progress(guild.id)
    except Exception:
        logger.exception(
            "essential_setup: set_essential_anchor failed (guild=%d)",
            guild.id,
        )
    return channel, message, "ok"


async def open_essential_setup(interaction: discord.Interaction) -> None:
    """Open the Essential Setup flow from a slash command. Admin-gated.

    Posts the flow into the private ``#superbot-setup`` channel and replies with
    an ephemeral pointer; falls back to opening it in the invoking channel when
    the bot can't make the private channel (no Manage Channels).
    """
    guild = interaction.guild
    member = interaction.user
    if guild is None or not isinstance(member, discord.Member):
        await interaction.response.send_message(_NOT_IN_SERVER, ephemeral=True)
        return
    from views.base import member_is_admin

    if not member_is_admin(member):
        await interaction.response.send_message(_NOT_ADMIN, ephemeral=True)
        return

    channel, message, reason = await open_essential_setup_in_setup_channel(
        guild,
        member,
    )
    if reason == "ok" and channel is not None and message is not None:
        await interaction.response.send_message(
            f"✅ Setup is ready in {channel.mention} — [open it]({message.jump_url}).",
            ephemeral=True,
        )
        return

    # Fall back to the invoking channel so setup still works without the
    # Manage Channels permission.
    flow = EssentialFlow(member, guild)
    await interaction.response.send_message(
        content=(_NO_CHANNEL_HINT if reason == "no_channel" else None),
        embed=_first_embed(flow),
        view=flow.current_view(),
    )


async def open_essential_setup_prefix(ctx: object) -> None:
    """Open the Essential Setup flow from a prefix command. Admin-gated.

    Posts the flow into the private ``#superbot-setup`` channel and replies in
    the invoking channel with a pointer; falls back to opening it inline when
    the bot can't make the private channel.

    ``ctx`` is a ``commands.Context`` (typed loosely so this view module does
    not import the ``commands`` extension).
    """
    guild = getattr(ctx, "guild", None)
    member = getattr(ctx, "author", None)
    send = ctx.send  # type: ignore[attr-defined]
    if guild is None or not isinstance(member, discord.Member):
        await send(_NOT_IN_SERVER)
        return
    from views.base import member_is_admin

    if not member_is_admin(member):
        await send(_NOT_ADMIN)
        return

    channel, message, reason = await open_essential_setup_in_setup_channel(
        guild,
        member,
    )
    if reason == "ok" and channel is not None and message is not None:
        await send(
            f"✅ Setup is ready in {channel.mention} — {message.jump_url}",
        )
        return

    flow = EssentialFlow(member, guild)
    if reason == "no_channel":
        await send(_NO_CHANNEL_HINT)
    await send(embed=_first_embed(flow), view=flow.current_view())
