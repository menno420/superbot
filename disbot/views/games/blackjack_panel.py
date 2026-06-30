"""Blackjack hub panel — PR 5 (playable launcher).

PR 5 converted the panel from router-only embeds into an actionable
launcher that spawns real Blackjack games. The buttons reuse the
existing ``BlackjackView``, ``_ChallengeView``, and
``_TournRegistrationView`` via the action helpers in
:mod:`cogs.blackjack.actions` — no duplicate game state lives here.

Layout:

* Row 0: ▶ Solo Free Play | 💰 Solo Bet | 👤 Challenge Player
* Row 1: 🏆 Tournament | 📊 Status | 📖 Rules

Tournament behaviour:

* Admin (``guild_permissions.administrator``) sees an "Open
  Registration" button that spawns a tournament with default
  parameters (entry_fee=0, rounds=5, 5-minute window) and emits the
  ✅ react.
* Non-admin sees an existing-tournament status if one is open,
  otherwise a "no tournament" embed.
"""

from __future__ import annotations

import logging

import discord

from cogs.blackjack.actions import (
    build_blackjack_challenge_view,
    commit_solo_blackjack,
    get_active_tournament,
    open_blackjack_tournament,
    start_solo_blackjack,
)
from utils.ui_constants import GAME_COLOR
from views.base import HubView
from views.blackjack.embeds import _tourn_embed
from views.games.common import BackToPanelButton
from views.navigation import BackTarget, attach_back_target

logger = logging.getLogger("bot.views.games.blackjack_panel")

# Bet presets shown in the Solo Bet sub-view. Mirrors the RPS panel
# layout (PR 4) so the cross-game UX is consistent.
_BET_PRESETS: tuple[int, ...] = (10, 25, 50, 100)


# ---------------------------------------------------------------------------
# Embed builders
# ---------------------------------------------------------------------------


def build_blackjack_overview_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🃏 Blackjack",
        description=(
            "Classic 21 — Solo Free Play is no-stakes vs the dealer; "
            "Solo Bet stakes 🪙 coins; Challenge Player opens a PvP "
            "match; Tournament runs the multi-round bracket."
        ),
        color=GAME_COLOR,
    )
    embed.set_footer(text="Only you can interact with this panel.")
    return embed


def build_blackjack_bet_preset_embed() -> discord.Embed:
    return discord.Embed(
        title="🃏 Blackjack — Solo Bet",
        description=(
            "Choose a bet amount, then play vs the dealer. Win pays "
            "the bet (or 1.5× on natural blackjack); lose debits the "
            "bet."
        ),
        color=GAME_COLOR,
    )


def build_blackjack_challenge_picker_embed() -> discord.Embed:
    return discord.Embed(
        title="🃏 Blackjack — Challenge Player",
        description=(
            "Pick the player you want to challenge, then choose a stake. "
            "They'll see an Accept / Decline prompt."
        ),
        color=GAME_COLOR,
    )


def build_blackjack_challenge_bet_embed(opponent: discord.Member) -> discord.Embed:
    return discord.Embed(
        title="🃏 Blackjack — Challenge Bet",
        description=(
            f"Choose the stake for your challenge against {opponent.mention}. "
            "Free play is no-stakes; a bet escrows coins from both players at "
            "accept and pays the winner."
        ),
        color=GAME_COLOR,
    )


def build_blackjack_tournament_overview_embed(
    *,
    is_admin: bool,
    has_active: bool,
) -> discord.Embed:
    if has_active:
        return discord.Embed(
            title="🏆 Blackjack Tournament — Active",
            description=(
                "A tournament is already registered in this server. "
                "Use **Status** to see registered players and round "
                "progress."
            ),
            color=GAME_COLOR,
        )
    if is_admin:
        return discord.Embed(
            title="🏆 Blackjack Tournament — Setup",
            description=(
                "Click **Open Registration** to start a new tournament "
                "with default settings (no entry fee, 5 rounds, "
                "5-minute registration window). Use `!bjtournament "
                "<entry_fee> <rounds> <mins>` for custom parameters."
            ),
            color=GAME_COLOR,
        )
    return discord.Embed(
        title="🏆 Blackjack Tournament — Idle",
        description=(
            "No tournament is currently registered. An admin can "
            "start one with `!bjtournament`."
        ),
        color=GAME_COLOR,
    )


def build_blackjack_rules_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🃏 Blackjack — Rules",
        description=(
            "Each player is dealt two cards; reach 21 (or as close as "
            "possible without busting) to beat the dealer."
        ),
        color=GAME_COLOR,
    )
    embed.add_field(
        name="Card values",
        value=(
            "• Number cards = face value (2–10)\n"
            "• Face cards (J/Q/K) = 10\n"
            "• Ace = 1 or 11, whichever is best for the hand"
        ),
        inline=False,
    )
    embed.add_field(
        name="Actions",
        value=(
            "• **Hit** — draw another card\n"
            "• **Stand** — keep the current hand\n"
            "• **Double** — double your bet and take exactly one card\n"
            "• Bust at >21 — the other side wins automatically"
        ),
        inline=False,
    )
    embed.add_field(
        name="Outcomes",
        value=(
            "• Natural blackjack (A + 10-value, two cards) pays 1.5× "
            "the bet\n"
            "• Tie returns the bet"
        ),
        inline=False,
    )
    return embed


# ---------------------------------------------------------------------------
# Sub-views
# ---------------------------------------------------------------------------


class _BlackjackBetPresetView(HubView):
    """Bet-preset picker: 10/25/50/100/Custom + Back."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        back_target: BackTarget | None = None,
    ) -> None:
        super().__init__(author)
        for preset in _BET_PRESETS:
            self.add_item(_BlackjackBetPresetButton(preset))
        self.add_item(_BlackjackBetCustomButton())
        self.add_item(_make_blackjack_back_button(grandparent=back_target))
        if back_target is not None:
            attach_back_target(self, back_target)


class _BlackjackBetPresetButton(discord.ui.Button):
    def __init__(self, bet: int) -> None:
        super().__init__(
            label=f"{bet} 🪙",
            style=discord.ButtonStyle.primary,
            custom_id=f"blackjack_panel:bet:{bet}",
            row=0,
        )
        self._bet = bet

    async def callback(self, interaction: discord.Interaction) -> None:
        await _spawn_solo(interaction, self._bet)


class _BlackjackBetCustomButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Custom",
            style=discord.ButtonStyle.secondary,
            custom_id="blackjack_panel:bet:custom",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(_BlackjackCustomBetModal())


class _BlackjackCustomBetModal(discord.ui.Modal, title="Custom Bet"):
    bet_input: discord.ui.TextInput = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Bet (🪙 coins)",
        placeholder="Enter a positive integer (or 0 for free play)",
        required=True,
        max_length=10,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw = (self.bet_input.value or "").strip()
        try:
            bet = int(raw)
        except ValueError:
            await interaction.response.send_message(
                "Bet must be an integer.",
                ephemeral=True,
            )
            return
        if bet < 0:
            await interaction.response.send_message(
                "Bet must be 0 or positive.",
                ephemeral=True,
            )
            return
        await _spawn_solo(interaction, bet)


async def _spawn_solo(interaction: discord.Interaction, bet: int) -> None:
    """Shared Solo Free / Solo Bet / Custom spawn path."""
    if interaction.guild is None or interaction.channel is None:
        await interaction.response.send_message(
            "Blackjack can only be started in a server channel.",
            ephemeral=True,
        )
        return
    result = await start_solo_blackjack(
        interaction.user,  # type: ignore[arg-type]
        interaction.guild,
        interaction.channel,  # type: ignore[arg-type]
        bet,
    )
    if result.ephemeral_message:
        await interaction.response.send_message(
            result.ephemeral_message,
            ephemeral=True,
        )
        return
    if result.embed is None:
        # Defensive: helper guaranteed (ephemeral_message OR embed),
        # but the type annotations leave embed Optional. Surface a
        # generic ephemeral rather than crashing.
        await interaction.response.send_message(
            "Could not start the game — please retry.",
            ephemeral=True,
        )
        return
    if result.view is None:
        # Natural-blackjack auto-payout: no playable hand, but still attach
        # a result view so Play again and Back remain reachable.
        from views.blackjack.solo_view import _BlackjackSoloResultView

        result_view = _BlackjackSoloResultView(
            interaction.user.id,
            interaction.guild_id or 0,
            bet,
            None,
        )
        await interaction.response.edit_message(embed=result.embed, view=result_view)
        result_view.message = interaction.message
        return
    await interaction.response.edit_message(
        embed=result.embed,
        view=result.view,
    )
    if interaction.message is not None and result.game is not None:
        await commit_solo_blackjack(result.view, interaction.message)


class _BlackjackChallengeSelectView(HubView):
    def __init__(
        self,
        author: discord.Member | discord.User,
        back_target: BackTarget | None = None,
    ) -> None:
        super().__init__(author)
        self.add_item(_BlackjackOpponentSelect())
        self.add_item(_make_blackjack_back_button(grandparent=back_target))
        if back_target is not None:
            attach_back_target(self, back_target)


class _BlackjackOpponentSelect(discord.ui.UserSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose an opponent…",
            min_values=1,
            max_values=1,
            custom_id="blackjack_panel:opponent_select",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        opponent = self.values[0]
        if not isinstance(opponent, discord.Member):
            await interaction.response.send_message(
                "Opponent must be a server member.",
                ephemeral=True,
            )
            return
        challenger = interaction.user
        if not isinstance(challenger, discord.Member):
            await interaction.response.send_message(
                "Challenger must be a server member.",
                ephemeral=True,
            )
            return
        # Validate the target before showing a stake picker — surface the
        # same "can't challenge yourself / a bot" copy as the challenge
        # builder, so the picker only appears for a playable opponent.
        if opponent.id == challenger.id:
            await interaction.response.send_message(
                "You can't challenge yourself.",
                ephemeral=True,
            )
            return
        if opponent.bot:
            await interaction.response.send_message(
                "You can't challenge a bot to PvP.",
                ephemeral=True,
            )
            return
        back_target: BackTarget | None = getattr(self.view, "_back_target", None)
        await interaction.response.edit_message(
            embed=build_blackjack_challenge_bet_embed(opponent),
            view=_BlackjackChallengeBetView(
                challenger,
                opponent,
                back_target=back_target,
            ),
        )


class _BlackjackChallengeBetView(HubView):
    """PvP stake picker shown after an opponent is selected.

    Free play + 10/25/50/100 presets + Custom, mirroring the Solo Bet
    picker so the cross-mode UX is consistent. Closes the panel's
    command-only PvP gap — "Challenge Player" used to start every PvP
    match at bet=0.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        opponent: discord.Member,
        back_target: BackTarget | None = None,
    ) -> None:
        super().__init__(author)
        self.add_item(_BlackjackChallengeBetButton(opponent, 0, label="Free play"))
        for preset in _BET_PRESETS:
            self.add_item(_BlackjackChallengeBetButton(opponent, preset))
        self.add_item(_BlackjackChallengeCustomBetButton(opponent))
        self.add_item(_make_blackjack_back_button(grandparent=back_target))
        if back_target is not None:
            attach_back_target(self, back_target)


class _BlackjackChallengeBetButton(discord.ui.Button):
    def __init__(
        self,
        opponent: discord.Member,
        bet: int,
        *,
        label: str | None = None,
        row: int = 0,
    ) -> None:
        super().__init__(
            label=label or f"{bet} 🪙",
            style=(
                discord.ButtonStyle.success if bet == 0 else discord.ButtonStyle.primary
            ),
            custom_id=f"blackjack_panel:challenge_bet:{bet}",
            row=row,
        )
        self._opponent = opponent
        self._bet = bet

    async def callback(self, interaction: discord.Interaction) -> None:
        await _spawn_pvp(interaction, self._opponent, self._bet)


class _BlackjackChallengeCustomBetButton(discord.ui.Button):
    def __init__(self, opponent: discord.Member, *, row: int = 1) -> None:
        super().__init__(
            label="Custom",
            style=discord.ButtonStyle.secondary,
            custom_id="blackjack_panel:challenge_bet:custom",
            row=row,
        )
        self._opponent = opponent

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(
            _BlackjackChallengeCustomBetModal(self._opponent),
        )


class _BlackjackChallengeCustomBetModal(discord.ui.Modal, title="Custom Challenge Bet"):
    bet_input: discord.ui.TextInput = discord.ui.TextInput(  # type: ignore[var-annotated]
        label="Bet (🪙 coins)",
        placeholder="Enter a positive integer (or 0 for free play)",
        required=True,
        max_length=10,
    )

    def __init__(self, opponent: discord.Member) -> None:
        super().__init__()
        self._opponent = opponent

    async def on_submit(self, interaction: discord.Interaction) -> None:
        raw = (self.bet_input.value or "").strip()
        try:
            bet = int(raw)
        except ValueError:
            await interaction.response.send_message(
                "Bet must be an integer.",
                ephemeral=True,
            )
            return
        if bet < 0:
            await interaction.response.send_message(
                "Bet must be 0 or positive.",
                ephemeral=True,
            )
            return
        await _spawn_pvp(interaction, self._opponent, bet)


async def _spawn_pvp(
    interaction: discord.Interaction,
    opponent: discord.Member,
    bet: int,
) -> None:
    """Shared PvP-challenge spawn path for the panel's preset/custom bets."""
    challenger = interaction.user
    if not isinstance(challenger, discord.Member):
        await interaction.response.send_message(
            "Challenger must be a server member.",
            ephemeral=True,
        )
        return
    embed, view, error = build_blackjack_challenge_view(
        challenger,
        opponent,
        interaction.guild_id or 0,
        bet,
    )
    if error or view is None:
        await interaction.response.send_message(
            error or "Could not start challenge.",
            ephemeral=True,
        )
        return
    await interaction.response.edit_message(embed=embed, view=view)
    view.message = interaction.message


class _BlackjackTournamentSubView(HubView):
    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        is_admin: bool,
        has_active: bool,
        back_target: BackTarget | None = None,
    ) -> None:
        super().__init__(author)
        if is_admin and not has_active:
            self.add_item(_BlackjackTournamentOpenButton())
        self.add_item(_make_blackjack_back_button(grandparent=back_target))
        if back_target is not None:
            attach_back_target(self, back_target)


class _BlackjackTournamentOpenButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="🏆 Open Registration",
            style=discord.ButtonStyle.primary,
            custom_id="blackjack_panel:tournament:open",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or interaction.channel is None:
            await interaction.response.send_message(
                "Tournament can only be started in a server channel.",
                ephemeral=True,
            )
            return
        result = await open_blackjack_tournament(
            interaction.user,  # type: ignore[arg-type]
            interaction.guild,
            interaction.channel,  # type: ignore[arg-type]
            interaction.client,  # type: ignore[arg-type]
        )
        if result.ephemeral_message:
            await interaction.response.send_message(
                result.ephemeral_message,
                ephemeral=True,
            )
            return
        if result.embed is None or result.view is None or result.tournament is None:
            # Defensive: helper guarantees (ephemeral OR full tuple) but
            # mypy can't see that. Fall back to ephemeral so the panel
            # never crashes.
            await interaction.response.send_message(
                "Could not open registration — please retry.",
                ephemeral=True,
            )
            return
        await interaction.response.edit_message(
            embed=result.embed,
            view=result.view,
        )
        if interaction.message is not None:
            try:
                await interaction.message.add_reaction("✅")
            except Exception as exc:  # noqa: BLE001 — reaction is optional
                logger.debug(
                    "blackjack panel: add_reaction failed: %s",
                    exc,
                )
            result.tournament.reg_message = interaction.message


def _make_blackjack_back_button(
    grandparent: BackTarget | None = None,
) -> BackToPanelButton:
    """Return a fresh "◀ Back to Blackjack" button for any Blackjack
    sub-view. Follow-up to PR 7 — Blackjack now uses the shared
    helper from ``views.games.common`` alongside RPS.
    """
    return BackToPanelButton(
        label="◀ Back to Blackjack",
        custom_id="blackjack_panel:back",
        panel_builder=BlackjackPanelView,
        overview_builder=build_blackjack_overview_embed,
        grandparent=grandparent,
    )


# ---------------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------------


class BlackjackPanelView(HubView):
    """Actionable Blackjack hub (PR 5).

    Six direct buttons: Solo Free Play, Solo Bet, Challenge Player,
    Tournament, Status, Rules. Engine logic lives in
    :mod:`cogs.blackjack.actions` and :mod:`views.blackjack`; this
    view is a launcher only.
    """

    SUBSYSTEM = "blackjack"

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)

    @discord.ui.button(
        label="▶ Solo Free Play",
        style=discord.ButtonStyle.success,
        custom_id="blackjack_panel:solo_free",
        row=0,
    )
    async def btn_solo_free(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await _spawn_solo(interaction, 0)

    @discord.ui.button(
        label="💰 Solo Bet",
        style=discord.ButtonStyle.primary,
        custom_id="blackjack_panel:solo_bet",
        row=0,
    )
    async def btn_solo_bet(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        back_target: BackTarget | None = getattr(self, "_back_target", None)
        await interaction.response.edit_message(
            embed=build_blackjack_bet_preset_embed(),
            view=_BlackjackBetPresetView(interaction.user, back_target=back_target),
        )

    @discord.ui.button(
        label="👤 Challenge Player",
        style=discord.ButtonStyle.primary,
        custom_id="blackjack_panel:challenge",
        row=0,
    )
    async def btn_challenge(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        back_target: BackTarget | None = getattr(self, "_back_target", None)
        await interaction.response.edit_message(
            embed=build_blackjack_challenge_picker_embed(),
            view=_BlackjackChallengeSelectView(
                interaction.user,
                back_target=back_target,
            ),
        )

    @discord.ui.button(
        label="🏆 Tournament",
        style=discord.ButtonStyle.primary,
        custom_id="blackjack_panel:tournament",
        row=1,
    )
    async def btn_tournament(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        from views.base import member_is_admin

        is_admin = member_is_admin(interaction.user)
        guild_id = interaction.guild_id or 0
        has_active = get_active_tournament(guild_id) is not None
        back_target: BackTarget | None = getattr(self, "_back_target", None)
        await interaction.response.edit_message(
            embed=build_blackjack_tournament_overview_embed(
                is_admin=is_admin,
                has_active=has_active,
            ),
            view=_BlackjackTournamentSubView(
                interaction.user,
                is_admin=is_admin,
                has_active=has_active,
                back_target=back_target,
            ),
        )

    @discord.ui.button(
        label="📊 Status",
        style=discord.ButtonStyle.secondary,
        custom_id="blackjack_panel:status",
        row=1,
    )
    async def btn_status(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        guild_id = interaction.guild_id or 0
        tourn = get_active_tournament(guild_id)
        if tourn is None:
            await interaction.response.send_message(
                "No active Blackjack tournament in this server.",
                ephemeral=True,
            )
            return
        await interaction.response.edit_message(
            embed=_tourn_embed(tourn),
            view=self,
        )

    @discord.ui.button(
        label="📖 Rules",
        style=discord.ButtonStyle.secondary,
        custom_id="blackjack_panel:rules",
        row=1,
    )
    async def btn_rules(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=build_blackjack_rules_embed(),
            view=self,
        )


__all__ = [
    "BlackjackPanelView",
    "build_blackjack_overview_embed",
    "build_blackjack_rules_embed",
]
