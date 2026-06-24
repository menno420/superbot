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
quick spine.  This first installment ships the flow framework + the two
highest-value steps (greet new members · set moderators) + the summary; the
remaining steps (block spam · log channel · rewards · help desk) are mechanical
follow-ons on this same pattern.
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
