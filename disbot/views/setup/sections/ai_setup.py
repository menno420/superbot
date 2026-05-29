"""AI setup section — Phase 6 of the setup-wizard plan.

Link-only step that points operators at the existing AI Platform
panel (``/aimenu``) and records the section as either acknowledged
or skipped.  The wizard does **not** write AI policy values from
here; a future PR may add a typed ``set_ai_policy`` operation, but
for now the contract is strict:

* Two buttons: **Open AI policy manager** + **Skip AI setup**.
* The "Open" button looks up ``/aimenu``'s slash-command id at
  runtime and emits a Discord ``</aimenu:id>`` mention so clicking
  it opens the AI panel in place.  When the id can't be resolved
  (sync delay, command renamed, etc.) the ephemeral reply falls
  back to the plain ``/aimenu`` text — the operator still knows
  what to run.
* On click of either button the section acknowledges via
  :func:`services.setup_session.ack_section` (Open) or
  :func:`services.setup_session.mark_section_skipped` (Skip) so the
  hub / wizard progress badge moves out of ``NOT_STARTED``.
* The section emits **zero** draft operations.  Final Review never
  consumes anything from here.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord

from services import setup_access, setup_session
from services.setup_sections import REGISTRY, SetupSection
from views.base import BaseView

if TYPE_CHECKING:
    pass

logger = logging.getLogger("bot.views.setup.sections.ai_setup")

SLUG = "ai_setup"

#: Slash-command name we deep-link to.  Defined as a constant so the
#: test suite + the fallback string + the lookup helper all agree on
#: the canonical name.
AI_POLICY_COMMAND_NAME = "aimenu"


async def resolve_ai_policy_link(interaction: discord.Interaction) -> str:
    """Return a clickable ``</aimenu:id>`` mention or fall back to text.

    Discord renders ``</name:id>`` as a clickable command suggestion;
    the ``id`` is the snowflake assigned at sync time.  We resolve it
    via ``interaction.client.tree.fetch_commands()`` (a Discord API
    call returning :class:`discord.app_commands.AppCommand`
    instances) and match by name.

    The fetch is cheap (one HTTP roundtrip) and called only when the
    operator presses the **Open AI policy manager** button — so the
    cost is acceptable without a cache.  When the fetch fails (rate
    limit, network blip), or the command isn't synced (just-deployed
    bot, dev environment), or the bot lacks AI commands entirely, we
    fall back to plain ``/aimenu`` text — the operator still knows
    what to type.
    """
    try:
        tree = getattr(interaction.client, "tree", None)
        if tree is None:
            return f"`/{AI_POLICY_COMMAND_NAME}`"
        # Try the global command set first; many deployments register
        # /aimenu globally.  If that comes back empty, fall through to
        # the guild-scoped set (interaction.guild may be None when
        # called from a DM context, but the wizard always runs in a
        # guild so the latter usually succeeds).
        commands = await tree.fetch_commands()
        for cmd in commands:
            if getattr(cmd, "name", None) == AI_POLICY_COMMAND_NAME:
                cmd_id = getattr(cmd, "id", None)
                if cmd_id is not None:
                    return f"</{AI_POLICY_COMMAND_NAME}:{cmd_id}>"
        if interaction.guild is not None:
            commands = await tree.fetch_commands(guild=interaction.guild)
            for cmd in commands:
                if getattr(cmd, "name", None) == AI_POLICY_COMMAND_NAME:
                    cmd_id = getattr(cmd, "id", None)
                    if cmd_id is not None:
                        return f"</{AI_POLICY_COMMAND_NAME}:{cmd_id}>"
    except Exception:
        logger.exception(
            "ai_setup: resolve_ai_policy_link fetch_commands failed",
        )
    return f"`/{AI_POLICY_COMMAND_NAME}`"


def build_ai_setup_embed(
    *,
    acknowledged: bool,
    skipped: bool,
) -> discord.Embed:
    """Render the AI-setup section card.

    Surfaces the section's purpose (link to AI Platform) and the
    current state — acknowledged, skipped, or pending.  Acknowledged
    state highlights green; skipped highlights yellow; pending uses
    the wizard's neutral blue.
    """
    if acknowledged:
        color = discord.Color.green()
        state = "✅ Acknowledged — AI panel opened from this step at least once."
    elif skipped:
        color = discord.Color.gold()
        state = "⚠️ Skipped — no AI policy actions taken from the wizard."
    else:
        color = discord.Color.blurple()
        state = "⬜ Not yet acknowledged."

    embed = discord.Embed(
        title="🤖 AI setup",
        description=(
            "SuperBot's AI features (response policy, providers, "
            "routing, retention) are managed in the dedicated AI "
            "Platform panel.  This step doesn't change AI policy — "
            "it just links you there and records that you've seen "
            "the option.\n\n"
            "Click **Open AI policy manager** to launch the panel "
            "(or run `/aimenu`).  Click **Skip AI setup** to leave "
            "the current policy untouched."
        ),
        color=color,
    )
    embed.add_field(name="State", value=state, inline=False)
    embed.add_field(
        name="What this step stages",
        value=(
            "_(nothing)_ — AI setup is link-only.  Final Review "
            "doesn't apply anything from this step."
        ),
        inline=False,
    )
    embed.set_footer(
        text="AI policy edits happen in the AI Platform panel, not the wizard.",
    )
    return embed


class AISetupView(BaseView):
    """Two-button picker: Open AI panel + Skip AI setup.

    Mutating callbacks (both buttons write to the session) re-check
    :func:`services.setup_access.can_apply_setup` against a fresh
    snapshot — same pattern as Phase 1's section card and Phase 3's
    wizard.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        acknowledged: bool,
        skipped: bool,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self.acknowledged = acknowledged
        self.skipped = skipped
        self._populate_buttons()

    def _populate_buttons(self) -> None:
        open_btn: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Open AI policy manager",
            style=(
                discord.ButtonStyle.success
                if self.acknowledged
                else discord.ButtonStyle.primary
            ),
            emoji="🤖",
            custom_id="setup_ai:open",
            row=0,
        )
        open_btn.callback = self._on_open  # type: ignore[method-assign]
        self.add_item(open_btn)

        skip_btn: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
            label="Skip AI setup",
            style=(
                discord.ButtonStyle.success
                if self.skipped
                else discord.ButtonStyle.secondary
            ),
            custom_id="setup_ai:skip",
            row=0,
        )
        skip_btn.callback = self._on_skip  # type: ignore[method-assign]
        self.add_item(skip_btn)

    async def _gate_apply(self, interaction: discord.Interaction) -> bool:
        member = interaction.user
        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Use this from inside the server.",
                ephemeral=True,
            )
            return False
        session = None
        guild_id = interaction.guild_id
        if guild_id is not None:
            try:
                session = await setup_session.resume_session(guild_id)
            except Exception:
                logger.exception("ai_setup._gate_apply: resume failed")
                session = None
        if not setup_access.can_apply_setup(member, session):
            await interaction.response.send_message(
                "Only the server owner or a delegated setup admin can "
                "acknowledge or skip the AI setup step.  Ask the owner "
                "to grant you `/setup-delegate`.",
                ephemeral=True,
            )
            return False
        return True

    async def _on_open(self, interaction: discord.Interaction) -> None:
        if not await self._gate_apply(interaction):
            return
        guild_id = interaction.guild_id
        if guild_id is None:
            await interaction.response.send_message(
                "AI setup requires a guild context.",
                ephemeral=True,
            )
            return
        link = await resolve_ai_policy_link(interaction)
        try:
            await setup_session.ack_section(guild_id, SLUG)
        except Exception:
            logger.exception("ai_setup._on_open: ack_section failed")
            # The ack is best-effort.  The operator still gets the
            # link — that's the primary deliverable of this button.
        self.acknowledged = True
        self.skipped = False
        self.clear_items()
        self._populate_buttons()
        embed = build_ai_setup_embed(acknowledged=True, skipped=False)
        await interaction.response.edit_message(embed=embed, view=self)
        await interaction.followup.send(
            f"🤖 Open the AI Platform panel: {link}\n\n"
            "AI policy changes happen in that panel — this step just "
            "linked you there and marked it acknowledged.",
            ephemeral=True,
        )

    async def _on_skip(self, interaction: discord.Interaction) -> None:
        if not await self._gate_apply(interaction):
            return
        guild_id = interaction.guild_id
        if guild_id is None:
            await interaction.response.send_message(
                "AI setup requires a guild context.",
                ephemeral=True,
            )
            return
        try:
            await setup_session.mark_section_skipped(guild_id, SLUG)
        except Exception:
            logger.exception("ai_setup._on_skip: mark_section_skipped failed")
            await interaction.response.send_message(
                "Could not record the skip — see logs.",
                ephemeral=True,
            )
            return
        self.acknowledged = False
        self.skipped = True
        self.clear_items()
        self._populate_buttons()
        embed = build_ai_setup_embed(acknowledged=False, skipped=True)
        await interaction.response.edit_message(embed=embed, view=self)


async def run(interaction: discord.Interaction, hub) -> None:
    """Section entry — opens the AI-setup picker ephemerally.

    The ``hub`` argument matches the registry's :class:`RunCallback`
    signature; this section never edits the hub message so the
    argument is unused.
    """
    del hub
    guild_id = interaction.guild_id
    if guild_id is None:
        await interaction.response.send_message(
            "AI setup must be opened inside the server.",
            ephemeral=True,
        )
        return
    try:
        session = await setup_session.resume_session(guild_id)
    except Exception:
        logger.exception("ai_setup.run: resume_session failed")
        session = None
    acknowledged = session is not None and SLUG in session.acknowledged_sections
    skipped = session is not None and SLUG in session.skipped_sections
    embed = build_ai_setup_embed(
        acknowledged=acknowledged,
        skipped=skipped,
    )
    view = AISetupView(
        interaction.user,
        acknowledged=acknowledged,
        skipped=skipped,
    )
    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True,
    )
    try:
        await setup_session.mark_in_progress(guild_id, step=SLUG)
    except Exception:
        logger.exception("ai_setup.run: mark_in_progress failed")


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="AI setup",
        style=discord.ButtonStyle.secondary,
        run=run,
        emoji="🤖",
        # Renders right after logging_presets (order 45) — both touch
        # operator-facing platform features, so neighbouring them in
        # the wizard keeps the step order intuitive.
        order=50,
        # Zero op_kinds — AI setup is link-only and stages nothing.
        op_kinds=frozenset(),
        description_if_skipped=(
            "SuperBot keeps the current AI policy and providers.  You "
            "can revisit `/aimenu` at any time."
        ),
        depths=frozenset({"standard", "advanced"}),
        # No recommended_ops_builder — AI setup has nothing to stage.
    ),
)


__all__ = [
    "AI_POLICY_COMMAND_NAME",
    "AISetupView",
    "SLUG",
    "build_ai_setup_embed",
    "resolve_ai_policy_link",
    "run",
]
