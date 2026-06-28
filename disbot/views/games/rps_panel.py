"""RPS hub panel — PR 4 (playable launcher).

PR 4 converted the panel from router-only embeds into an actionable
launcher that opens real game flows. The buttons reuse the existing
view hierarchy under :mod:`views.rps` and the tournament code in
:mod:`cogs.rps_tournament_cog` — no duplicate engine logic lives
here.

Layout:

* Row 0: ▶ Quick Play | 💰 Bet Match | 👤 Challenge Player
* Row 1: 🏆 Tournament | 📖 Rules

Tournament behavior:

* Admin (``guild_permissions.administrator``) sees an "Open
  Registration" button that calls the cog's existing registration
  flow (default settings: no role, no entry fee).
* Non-admin sees a "Join Tournament" button when registration is
  active, otherwise a status embed.
"""

from __future__ import annotations

import logging

import discord

from utils.ui_constants import GAME_COLOR
from views.base import HubView, interaction_is_admin
from views.games.common import BackToPanelButton
from views.navigation import BackTarget, attach_back_target
from views.rps import _RpsPvpChallengeView, _RpsView

logger = logging.getLogger("bot.views.games.rps_panel")

# Bet presets shown in the Bet Match sub-view. Keep small — Discord
# button rows cap at five components and we leave room for Custom +
# Back.
_BET_PRESETS: tuple[int, ...] = (10, 25, 50, 100)


# ---------------------------------------------------------------------------
# Embed builders
# ---------------------------------------------------------------------------


def build_rps_overview_embed() -> discord.Embed:
    embed = discord.Embed(
        title="✂️ Rock Paper Scissors",
        description=(
            "Pick a button to start playing. Quick Play is a free "
            "round vs the bot; Bet Match lets you stake 🪙 coins; "
            "Challenge Player opens a PvP challenge; Tournament runs "
            "the bracketed competition."
        ),
        color=GAME_COLOR,
    )
    embed.set_footer(text="Only you can interact with this panel.")
    return embed


def build_rps_solo_embed(bet: int) -> discord.Embed:
    from views.rps._helpers import _FREE_WIN

    bet_str = f"**{bet}** 🪙" if bet else f"Free play (win = +{_FREE_WIN} 🪙)"
    return discord.Embed(
        title="✂️ Rock · Paper · Scissors",
        description=f"Bet: {bet_str}\nChoose your move!",
        color=GAME_COLOR,
    )


def build_rps_challenge_embed(opponent: discord.Member, bet: int) -> discord.Embed:
    bet_str = f"**{bet}** 🪙" if bet else "free play"
    return discord.Embed(
        title="✂️ RPS Challenge!",
        description=(
            f"Challenging {opponent.mention} to Rock Paper Scissors "
            f"({bet_str}).\n{opponent.mention}, do you accept?"
        ),
        color=GAME_COLOR,
    )


def build_rps_bet_preset_embed() -> discord.Embed:
    return discord.Embed(
        title="✂️ RPS — Bet Match",
        description=(
            "Choose a bet amount, then play a single round vs the bot. "
            "Win pays you the bet; lose debits the bet (overdraft "
            "allowed)."
        ),
        color=GAME_COLOR,
    )


def build_rps_challenge_picker_embed() -> discord.Embed:
    return discord.Embed(
        title="✂️ RPS — Challenge Player",
        description=(
            "Pick the player you want to challenge. They'll see an "
            "Accept / Decline prompt."
        ),
        color=GAME_COLOR,
    )


def build_rps_tournament_status_embed(
    *,
    is_admin: bool,
    registration_active: bool,
    tournament_active: bool,
    player_count: int,
) -> discord.Embed:
    if tournament_active:
        return discord.Embed(
            title="🏆 RPS Tournament — In Progress",
            description=(
                f"A tournament is currently running with "
                f"**{player_count}** registered players. The bracket "
                "is being played in dedicated match channels."
            ),
            color=GAME_COLOR,
        )
    if registration_active:
        return discord.Embed(
            title="🏆 RPS Tournament — Registration Open",
            description=(
                f"Registration is open. **{player_count}** player(s) "
                "have joined so far. Click **Join Tournament** below "
                "to sign up."
            ),
            color=GAME_COLOR,
        )
    if is_admin:
        return discord.Embed(
            title="🏆 RPS Tournament — Setup",
            description=(
                "No tournament is active. Click **Open Registration** "
                "to start a new tournament with default settings "
                "(no role mention, no entry fee, classic mode, "
                "best-of-3)."
            ),
            color=GAME_COLOR,
        )
    return discord.Embed(
        title="🏆 RPS Tournament — Idle",
        description=(
            "No tournament is currently active. An admin can start "
            "one with `!rpsregister`."
        ),
        color=GAME_COLOR,
    )


def build_rps_rules_embed() -> discord.Embed:
    embed = discord.Embed(
        title="✂️ Rock Paper Scissors — Rules",
        description=(
            "Rock crushes Scissors, Scissors cut Paper, Paper covers "
            "Rock. Identical throws are a draw."
        ),
        color=GAME_COLOR,
    )
    embed.add_field(
        name="Best-of (tournament)",
        value=(
            "Tournament matches default to best-of-3 with a "
            "configurable round count via `!rpssettings`."
        ),
        inline=False,
    )
    embed.add_field(
        name="Stakes",
        value=(
            "Stakes matches debit both sides at match start; the "
            "winner takes the combined pot."
        ),
        inline=False,
    )
    embed.add_field(
        name="Timeouts & forfeits",
        value=(
            "You have a short window to lock in your move. Run out of "
            "time and you **forfeit** the round — in a stakes match the "
            "pot goes to your opponent. If **neither** player picks, it's "
            "a draw and stakes are refunded."
        ),
        inline=False,
    )
    return embed


# ---------------------------------------------------------------------------
# Sub-views
# ---------------------------------------------------------------------------


def _spawn_solo_view(
    interaction: discord.Interaction,
    bet: int,
) -> _RpsView:
    """Construct the playable solo ``_RpsView`` from an interaction."""
    return _RpsView(
        interaction.user,  # type: ignore[arg-type]
        interaction.guild_id or 0,
        bet,
    )


class _RpsBetPresetView(HubView):
    """Bet-preset picker: 10/25/50/100/Custom + Back."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        back_target: BackTarget | None = None,
    ) -> None:
        super().__init__(author)
        for preset in _BET_PRESETS:
            self.add_item(_RpsBetPresetButton(preset))
        self.add_item(_RpsBetCustomButton())
        self.add_item(_make_rps_back_button(grandparent=back_target))
        if back_target is not None:
            attach_back_target(self, back_target)


class _RpsBetPresetButton(discord.ui.Button):
    def __init__(self, bet: int) -> None:
        super().__init__(
            label=f"{bet} 🪙",
            style=discord.ButtonStyle.primary,
            custom_id=f"rps_panel:bet:{bet}",
            row=0,
        )
        self._bet = bet

    async def callback(self, interaction: discord.Interaction) -> None:
        view = _spawn_solo_view(interaction, self._bet)
        await interaction.response.edit_message(
            embed=build_rps_solo_embed(self._bet),
            view=view,
        )
        view.message = interaction.message


class _RpsBetCustomButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Custom",
            style=discord.ButtonStyle.secondary,
            custom_id="rps_panel:bet:custom",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_modal(_RpsCustomBetModal())


class _RpsCustomBetModal(discord.ui.Modal, title="Custom Bet"):
    bet_input: discord.ui.TextInput = discord.ui.TextInput(
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
        view = _spawn_solo_view(interaction, bet)
        await interaction.response.edit_message(
            embed=build_rps_solo_embed(bet),
            view=view,
        )
        view.message = interaction.message


class _RpsChallengeSelectView(HubView):
    """User-select picker for PvP challenge target."""

    def __init__(
        self,
        author: discord.Member | discord.User,
        back_target: BackTarget | None = None,
    ) -> None:
        super().__init__(author)
        self.add_item(_RpsOpponentSelect())
        self.add_item(_make_rps_back_button(grandparent=back_target))
        if back_target is not None:
            attach_back_target(self, back_target)


class _RpsOpponentSelect(discord.ui.UserSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose an opponent…",
            min_values=1,
            max_values=1,
            custom_id="rps_panel:opponent_select",
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
        if opponent.id == interaction.user.id:
            await interaction.response.send_message(
                "You can't challenge yourself.",
                ephemeral=True,
            )
            return
        if opponent.bot:
            await interaction.response.send_message(
                "You can't PvP-challenge a bot — use Quick Play instead.",
                ephemeral=True,
            )
            return
        challenger = interaction.user
        bet = 0  # PvP bet picker deferred to a future PR
        challenge_view = _RpsPvpChallengeView(
            challenger,  # type: ignore[arg-type]
            opponent,
            interaction.guild_id or 0,
            bet,
        )
        await interaction.response.edit_message(
            embed=build_rps_challenge_embed(opponent, bet),
            view=challenge_view,
        )
        challenge_view.message = interaction.message


class _RpsTournamentSubView(HubView):
    """Tournament sub-panel: admin sees Open Registration, users see
    Join when registration is active.
    """

    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        is_admin: bool,
        registration_active: bool,
        tournament_active: bool,
        back_target: BackTarget | None = None,
    ) -> None:
        super().__init__(author)
        if registration_active and not tournament_active:
            self.add_item(_RpsTournamentJoinButton())
        elif is_admin and not tournament_active:
            self.add_item(_RpsTournamentStartButton())
        elif is_admin and tournament_active:
            self.add_item(_RpsTournamentMatchupButton())
        self.add_item(_make_rps_back_button(grandparent=back_target))
        if back_target is not None:
            attach_back_target(self, back_target)


class _RpsTournamentStartButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="🏆 Open Registration",
            style=discord.ButtonStyle.primary,
            custom_id="rps_panel:tournament:open",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        cog = _resolve_rps_cog(interaction)
        if cog is None:
            await interaction.response.send_message(
                "RPS cog is not loaded — registration cannot start.",
                ephemeral=True,
            )
            return
        if cog.tournament_active or cog.registration_active:
            await interaction.response.send_message(
                "A tournament or registration is already active.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            "Opening tournament registration in this channel — use "
            "`!rpsregister @role <entry_fee>` for custom settings.",
            ephemeral=True,
        )
        from core.runtime.interaction_helpers import help_ctx_shim

        ctx = help_ctx_shim(interaction)
        await cog.rps_register(ctx)


class _RpsTournamentJoinButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="✅ Join Tournament",
            style=discord.ButtonStyle.success,
            custom_id="rps_panel:tournament:join",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        cog = _resolve_rps_cog(interaction)
        if cog is None or not cog.registration_active:
            await interaction.response.send_message(
                "Registration is no longer open.",
                ephemeral=True,
            )
            return
        ok = await cog.try_register_player(
            interaction.user,
            interaction.guild_id or 0,
        )
        if ok:
            await interaction.response.send_message(
                f"✅ Registered! ({len(cog.players)} player(s) so far)",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Could not register — you may already be registered "
                "or short on coins for the entry fee.",
                ephemeral=True,
            )


class _RpsTournamentMatchupButton(discord.ui.Button):
    """Admin-only: open a member picker to manually pair two registered players
    (exposes the ``!rpsmatchup`` command from the panel).
    """

    def __init__(self) -> None:
        super().__init__(
            label="⚔️ Create Matchup",
            style=discord.ButtonStyle.primary,
            custom_id="rps_panel:tournament:matchup",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "Creating matchups is admin-only.",
                ephemeral=True,
            )
            return
        cog = _resolve_rps_cog(interaction)
        if cog is None or not cog.tournament_active:
            await interaction.response.send_message(
                "No tournament is active — start one before creating matchups.",
                ephemeral=True,
            )
            return
        view = HubView(interaction.user)  # invoker-locked ephemeral picker
        view.add_item(_RpsMatchupSelect())
        await interaction.response.send_message(
            "Pick the two registered players to match up:",
            view=view,
            ephemeral=True,
        )


class _RpsMatchupSelect(discord.ui.UserSelect):
    def __init__(self) -> None:
        super().__init__(
            placeholder="Choose two registered players…",
            min_values=2,
            max_values=2,
            custom_id="rps_panel:tournament:matchup_select",
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction_is_admin(interaction):
            await interaction.response.send_message(
                "Creating matchups is admin-only.",
                ephemeral=True,
            )
            return
        cog = _resolve_rps_cog(interaction)
        if cog is None or not cog.tournament_active:
            await interaction.response.send_message(
                "Tournament is no longer active.",
                ephemeral=True,
            )
            return
        picks = [m for m in self.values if isinstance(m, discord.Member)]
        if len(picks) != 2 or picks[0].id == picks[1].id:
            await interaction.response.send_message(
                "Pick two different server members.",
                ephemeral=True,
            )
            return
        player1, player2 = picks
        if player1 not in cog.players or player2 not in cog.players:
            await interaction.response.send_message(
                "Both players must be registered in the tournament.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"Creating a match: {player1.mention} vs {player2.mention}…",
            ephemeral=True,
        )
        from core.runtime.interaction_helpers import help_ctx_shim

        ctx = help_ctx_shim(interaction)
        await cog.rps_matchup(ctx, player1, player2)


def _make_rps_back_button(
    grandparent: BackTarget | None = None,
) -> BackToPanelButton:
    """Return a fresh "◀ Back to RPS" button for any RPS sub-view.

    Thin wrapper over the shared :class:`BackToPanelButton` helper —
    PR 7 extracted this back-button pattern from three sites in this
    file into ``views.games.common`` so other game panels can adopt
    the same shape.
    """
    return BackToPanelButton(
        label="◀ Back to RPS",
        custom_id="rps_panel:back",
        panel_builder=RPSPanelView,
        overview_builder=build_rps_overview_embed,
        grandparent=grandparent,
    )


def _resolve_rps_cog(interaction: discord.Interaction):
    """Look up the RPS cog instance via the subsystem-registry mapping.

    Routes through ``cogs.help_cog._cog_for_subsystem`` so the lookup
    survives the PR-3 class rename (``RPSTournamentCog`` →
    ``RockPaperScissorsCog``) without hardcoding either string.
    """
    from cogs.help_cog import _cog_for_subsystem

    return _cog_for_subsystem(interaction.client, "rps_tournament")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Main panel view
# ---------------------------------------------------------------------------


class RPSPanelView(HubView):
    """Actionable RPS hub (PR 4).

    Five direct buttons that open real flows. Engine logic lives in
    :mod:`views.rps` and :mod:`cogs.rps_tournament_cog`; this view is
    a launcher only.
    """

    SUBSYSTEM = "rps_tournament"

    def __init__(self, author: discord.Member | discord.User) -> None:
        super().__init__(author)

    @discord.ui.button(
        label="▶ Quick Play",
        style=discord.ButtonStyle.success,
        custom_id="rps_panel:quick_play",
        row=0,
    )
    async def btn_quick_play(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        view = _spawn_solo_view(interaction, 0)
        await interaction.response.edit_message(
            embed=build_rps_solo_embed(0),
            view=view,
        )
        view.message = interaction.message

    @discord.ui.button(
        label="💰 Bet Match",
        style=discord.ButtonStyle.primary,
        custom_id="rps_panel:bet_match",
        row=0,
    )
    async def btn_bet_match(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        back_target: BackTarget | None = getattr(self, "_back_target", None)
        bet_view = _RpsBetPresetView(interaction.user, back_target=back_target)
        await interaction.response.edit_message(
            embed=build_rps_bet_preset_embed(),
            view=bet_view,
        )

    @discord.ui.button(
        label="👤 Challenge Player",
        style=discord.ButtonStyle.primary,
        custom_id="rps_panel:challenge",
        row=0,
    )
    async def btn_challenge(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        back_target: BackTarget | None = getattr(self, "_back_target", None)
        select_view = _RpsChallengeSelectView(interaction.user, back_target=back_target)
        await interaction.response.edit_message(
            embed=build_rps_challenge_picker_embed(),
            view=select_view,
        )

    @discord.ui.button(
        label="🏆 Tournament",
        style=discord.ButtonStyle.primary,
        custom_id="rps_panel:tournament",
        row=1,
    )
    async def btn_tournament(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        cog = _resolve_rps_cog(interaction)
        is_admin = interaction_is_admin(interaction)
        registration_active = bool(getattr(cog, "registration_active", False))
        tournament_active = bool(getattr(cog, "tournament_active", False))
        player_count = len(getattr(cog, "players", []) or [])
        back_target: BackTarget | None = getattr(self, "_back_target", None)
        sub_view = _RpsTournamentSubView(
            interaction.user,
            is_admin=is_admin,
            registration_active=registration_active,
            tournament_active=tournament_active,
            back_target=back_target,
        )
        await interaction.response.edit_message(
            embed=build_rps_tournament_status_embed(
                is_admin=is_admin,
                registration_active=registration_active,
                tournament_active=tournament_active,
                player_count=player_count,
            ),
            view=sub_view,
        )

    @discord.ui.button(
        label="📖 Rules",
        style=discord.ButtonStyle.secondary,
        custom_id="rps_panel:rules",
        row=1,
    )
    async def btn_rules(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await interaction.response.edit_message(
            embed=build_rps_rules_embed(),
            view=self,
        )


__all__ = [
    "RPSPanelView",
    "build_rps_overview_embed",
    "build_rps_rules_embed",
]
