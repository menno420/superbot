"""Server purpose section — Phase 4 of the setup-wizard plan.

Asks the operator a single question: **what is this server for?**.
The answer is persisted on :class:`SetupSession.purpose` and used by
downstream recommended-ops builders (logging presets, AI setup link
copy, cleanup defaults, …) to bias their suggestions.

Architecture invariants:

* Purpose is **session metadata, not a setup mutation.**  The section
  emits zero :class:`SetupOperation` records.  Final Review never
  consumes purpose.
* Writes happen outside Final Review via
  :func:`services.setup_session.set_purpose`.  No
  :func:`setup_operations.apply_operations` call.
* Progress flows ``NOT_STARTED → CUSTOMIZED → APPLIED`` via
  :func:`services.setup_session.ack_section` once a purpose is
  picked, mirroring what the link-only AI section will do in Phase 6.
* Purpose **never** writes guild config, AI policy, or any subsystem
  setting on its own.  Builders that want to read it do so via the
  Phase 2 :func:`call_recommended_ops_builder` adapter.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import discord

from services import setup_access, setup_session
from services.setup_sections import REGISTRY, SetupSection
from views.base import BaseView

logger = logging.getLogger("bot.views.setup.sections.purpose")

SLUG = "purpose"


@dataclass(frozen=True)
class PurposeOption:
    """Operator-facing label + persisted slug for one purpose choice."""

    slug: str  # matches utils.db.setup_session.KNOWN_PURPOSES
    label: str
    description: str
    emoji: str | None = None


#: Visible button order in the picker.  Slugs match
#: ``utils.db.setup_session.KNOWN_PURPOSES``; the order is what the
#: operator sees in the section card.
PURPOSE_OPTIONS: tuple[PurposeOption, ...] = (
    PurposeOption(
        slug="community",
        label="Community",
        description="Hangout / general-chat server.  Mild moderation; "
        "lightweight cleanup defaults.",
        emoji="👥",
    ),
    PurposeOption(
        slug="gaming_btd6",
        label="Gaming / BTD6",
        description="Game-focused server — BTD6 strategies, towers, "
        "race coordination.",
        emoji="🎮",
    ),
    PurposeOption(
        slug="support",
        label="Support",
        description="Help-desk / question-answering server.  Encourages "
        "thread-per-question patterns and link-rich AI replies.",
        emoji="🛟",
    ),
    PurposeOption(
        slug="moderation",
        label="Moderation",
        description="Moderation-heavy server.  Strict cleanup defaults; "
        "audit-logging biased toward retention.",
        emoji="🛡",
    ),
    PurposeOption(
        slug="ai_helper",
        label="AI helper",
        description="Server centred on AI / `!ai` chat with SuperBot.  "
        "Bias AI-policy suggestions and tighter routing.",
        emoji="🤖",
    ),
    PurposeOption(
        slug="testing_private",
        label="Testing / private",
        description="Private test or staging server.  Skip strict defaults; "
        "fewer guardrails.",
        emoji="🧪",
    ),
    PurposeOption(
        slug="mixed",
        label="Mixed",
        description="More than one of the above.  Neutral defaults; pick "
        "specific sections individually.",
        emoji="🌀",
    ),
)


_OPTIONS_BY_SLUG: dict[str, PurposeOption] = {opt.slug: opt for opt in PURPOSE_OPTIONS}


def get_option(slug: str | None) -> PurposeOption | None:
    """Return the :class:`PurposeOption` matching ``slug`` or ``None``.

    Public so other modules (the wizard, section builders) can render
    purpose-dependent copy without re-implementing the lookup.
    """
    if slug is None:
        return None
    return _OPTIONS_BY_SLUG.get(slug)


def build_purpose_embed(session_purpose: str | None) -> discord.Embed:
    """Render the Purpose-section card embed.

    Lists every :class:`PurposeOption` with its label, emoji, and
    one-line description; highlights the current pick if any.
    """
    embed = discord.Embed(
        title="🎯 Server purpose",
        description=(
            "Pick the single best description of this server.  Your "
            "answer biases the wizard's later recommendations — it "
            "does **not** stage any setup operation by itself, and "
            "you can revisit this step at any time."
        ),
        color=discord.Color.blurple(),
    )

    current = get_option(session_purpose)
    embed.add_field(
        name="Current pick",
        value=(
            f"{current.emoji or '•'} **{current.label}** — {current.description}"
            if current is not None
            else "_(no purpose chosen yet)_"
        ),
        inline=False,
    )

    bullet_lines = []
    for opt in PURPOSE_OPTIONS:
        bullet = f"{opt.emoji or '•'} **{opt.label}** — {opt.description}"
        bullet_lines.append(bullet)
    embed.add_field(
        name="Options",
        value="\n".join(bullet_lines),
        inline=False,
    )
    embed.set_footer(
        text=(
            "Purpose stages zero operations.  Final Review never "
            "consumes this — it is metadata only."
        ),
    )
    return embed


class PurposePickerView(BaseView):
    """Single-pick view: seven buttons, one per :class:`PurposeOption`.

    Every mutating button re-checks
    :func:`services.setup_access.can_apply_setup` against the live
    session.  Picking a purpose calls
    :func:`services.setup_session.set_purpose` and acknowledges the
    section via :func:`services.setup_session.ack_section`, then
    re-renders the embed with the new highlight.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        session_purpose: str | None,
        timeout: int = 300,
    ) -> None:
        super().__init__(author, public=False, timeout=timeout)
        self.session_purpose = session_purpose
        self._populate_buttons()

    def _populate_buttons(self) -> None:
        # Discord allows max 5 buttons per row; seven options need
        # two rows.  Row 0 = first four; row 1 = remaining three.
        for idx, opt in enumerate(PURPOSE_OPTIONS):
            row = 0 if idx < 4 else 1
            highlight = opt.slug == self.session_purpose
            button: discord.ui.Button = discord.ui.Button(  # type: ignore[var-annotated]
                label=opt.label,
                style=(
                    discord.ButtonStyle.success
                    if highlight
                    else discord.ButtonStyle.secondary
                ),
                emoji=opt.emoji,
                custom_id=f"setup_purpose:{opt.slug}",
                row=row,
            )
            button.callback = self._make_callback(opt)  # type: ignore[method-assign]
            self.add_item(button)

    def _make_callback(self, option: PurposeOption):
        async def _callback(interaction: discord.Interaction) -> None:
            if not await self._gate_apply(interaction):
                return
            guild_id = interaction.guild_id
            if guild_id is None:
                await interaction.response.send_message(
                    "This can only be used in a server.",
                    ephemeral=True,
                )
                return
            try:
                await setup_session.set_purpose(guild_id, option.slug)
            except Exception:
                logger.exception(
                    "purpose: set_purpose failed (slug=%s)",
                    option.slug,
                )
                await interaction.response.send_message(
                    "Could not save the purpose choice — see logs.",
                    ephemeral=True,
                )
                return
            try:
                await setup_session.ack_section(guild_id, SLUG)
            except Exception:
                logger.exception(
                    "purpose: ack_section failed (slug=%s)",
                    option.slug,
                )

            self.session_purpose = option.slug
            # Repaint the embed with the new highlight.
            self.clear_items()
            self._populate_buttons()
            embed = build_purpose_embed(option.slug)
            await interaction.response.edit_message(embed=embed, view=self)

        return _callback

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
                logger.exception("purpose._gate_apply: resume failed")
                session = None
        if not setup_access.can_apply_setup(member, session):
            await interaction.response.send_message(
                "Only the server owner or a delegated setup admin can "
                "set the server purpose.  Ask the owner to grant you "
                "`/setup-delegate`.",
                ephemeral=True,
            )
            return False
        return True


async def run(interaction: discord.Interaction, hub) -> None:
    """Section entry point.  Posts the picker as an ephemeral panel.

    The ``hub`` argument matches the registry's :class:`RunCallback`
    signature; it is unused here because the picker doesn't need
    back-button refresh access to the hub.
    """
    del hub
    guild_id = interaction.guild_id
    if guild_id is None:
        await interaction.response.send_message(
            "Purpose picker must be opened inside the server.",
            ephemeral=True,
        )
        return
    try:
        session = await setup_session.resume_session(guild_id)
    except Exception:
        logger.exception("purpose.run: resume_session failed")
        session = None
    current_purpose = session.purpose if session is not None else None
    embed = build_purpose_embed(current_purpose)
    view = PurposePickerView(
        interaction.user,
        session_purpose=current_purpose,
    )
    await interaction.response.send_message(
        embed=embed,
        view=view,
        ephemeral=True,
    )
    try:
        await setup_session.mark_in_progress(guild_id, step=SLUG)
    except Exception:
        logger.exception("purpose.run: mark_in_progress failed")


REGISTRY.register(
    SetupSection(
        slug=SLUG,
        label="Server purpose",
        style=discord.ButtonStyle.primary,
        run=run,
        emoji="🎯",
        # Render first so operators see the orienting question before
        # anything else.  Production sections use multiples of 10
        # starting at ~10; pick 5 to keep purpose at the top.
        order=5,
        # Zero op_kinds — Purpose stages no draft operations.
        op_kinds=frozenset(),
        description_if_skipped=(
            "The wizard continues with neutral defaults; specific "
            "sections still pick safe values, just without the "
            "purpose-based bias."
        ),
        depths=frozenset({"quick", "standard", "advanced"}),
        # No recommended_ops_builder — purpose has nothing to stage.
    ),
)


__all__ = [
    "PURPOSE_OPTIONS",
    "PurposeOption",
    "PurposePickerView",
    "SLUG",
    "build_purpose_embed",
    "get_option",
    "run",
]
