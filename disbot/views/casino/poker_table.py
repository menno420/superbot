"""Multiplayer Texas Hold'em table — the per-player auto-updating ephemeral UI.

This is the marquee mechanic the owner asked for: a *group* card game where
**every seated player gets their own private, auto-updating ephemeral message**,
so multiple people play the same table and react at the same time.

How the per-player ephemeral broadcast works
---------------------------------------------
A Discord ephemeral message can only be edited through the interaction (webhook)
token that created it.  So when a player **Joins**, we send them an ephemeral
seat panel and keep the returned :class:`discord.InteractionMessage` handle.
Whenever the shared game state changes — *any* player acts — we re-render and
:meth:`edit` **every** seat's stored handle plus the public spectator message.
That is what makes each player's private view update live in response to other
players' actions.

The handle's webhook token lives ~15 minutes; a hand is far shorter, and we
refresh a seat's handle from its owner's own action interactions, so a normal
session never hits the limit.

Layering
--------
The pure game (deal / bet / side pots / showdown) lives in
``utils.poker.engine`` — Discord-free and unit-tested.  This module is only the
renderer + the broadcast plumbing + turn management.  v1 uses **table
play-chips** (everyone starts equal), not the real economy, so no money seam is
involved.  In-flight table state is in-memory and not restart-safe by design
(ADR-002), exactly like blackjack/RPS.
"""

from __future__ import annotations

import asyncio
import logging

import discord

from core.runtime.interaction_helpers import safe_defer
from utils.cards import Card
from utils.poker.engine import Action, Player, PokerError, PokerGame
from utils.ui_constants import GAME_COLOR

logger = logging.getLogger("bot.views.casino.poker")

# --------------------------------------------------------------------------- #
# Table tuning (play-chips — no real economy involved in v1).
# --------------------------------------------------------------------------- #
MAX_SEATS = 8
MIN_PLAYERS = 2
START_STACK = 1000
SMALL_BLIND = 5
BIG_BLIND = 10
TURN_SECONDS = 90  # auto-check/fold an idle player so one AFK seat can't stall
LOBBY_TIMEOUT = 600
GAME_TIMEOUT = 1800

# One active table per channel keeps the UX unambiguous (mirrors the in-memory
# game registries blackjack/RPS use; ADR-002 — not restart-safe by design).
_tables: dict[int, PokerTable] = {}


def get_table(channel_id: int) -> PokerTable | None:
    return _tables.get(channel_id)


async def launch_table(
    bot: discord.Client,
    channel: discord.abc.Messageable,
    channel_id: int,
    host: discord.abc.User,
) -> PokerTable | None:
    """Create a poker table in ``channel`` and post its public lobby message.

    Returns the new table, or ``None`` if one is already open in this channel
    (one active table per channel keeps the UX unambiguous).
    """
    existing = _tables.get(channel_id)
    if existing is not None and not existing.ended:
        return None
    table = PokerTable(bot, channel, channel_id, host)
    _tables[channel_id] = table
    message = await channel.send(
        embed=table._lobby_public_embed(),
        view=PokerLobbyView(table),
    )
    table.public_message = message
    return table


def _fmt_card(card: Card) -> str:
    return f"`{card}`"


def _fmt_cards(cards: list[Card]) -> str:
    return " ".join(_fmt_card(c) for c in cards) if cards else "—"


def _board_str(board: list[Card]) -> str:
    shown = _fmt_cards(board)
    placeholders = "🂠 " * (5 - len(board))
    return f"{shown} {placeholders}".strip()


# --------------------------------------------------------------------------- #
# The table session
# --------------------------------------------------------------------------- #


class PokerTable:
    """One poker table in a channel: lobby → hands → teardown.

    Owns the public lobby/spectator message, every seat's private ephemeral
    message handle, the pure :class:`PokerGame`, and the per-turn idle clock.
    """

    def __init__(
        self,
        bot: discord.Client,
        channel: discord.abc.Messageable,
        channel_id: int,
        host: discord.abc.User,
    ) -> None:
        self.bot = bot
        self.channel = channel
        self.channel_id = channel_id
        self.host = host
        # Lobby seating order (user objects) until the game starts.
        self.seated: list[discord.abc.User] = [host]
        self.user_by_id: dict[int, discord.abc.User] = {host.id: host}
        self.messages: dict[int, discord.InteractionMessage] = {}
        self.game: PokerGame | None = None
        self.public_message: discord.Message | None = None
        self.started = False
        self.ended = False
        self._turn_token = 0
        self._turn_task: asyncio.Task[None] | None = None

    # --------------------------------------------------------------- lobby ops

    def is_seated(self, user_id: int) -> bool:
        return user_id in self.user_by_id

    async def add_player(self, interaction: discord.Interaction) -> None:
        user = interaction.user
        if self.started:
            await interaction.response.send_message(
                "This table has already started — wait for the next one.",
                ephemeral=True,
            )
            return
        if self.is_seated(user.id):
            await interaction.response.send_message(
                "You're already seated at this table.",
                ephemeral=True,
            )
            return
        if len(self.seated) >= MAX_SEATS:
            await interaction.response.send_message(
                f"This table is full ({MAX_SEATS} seats).",
                ephemeral=True,
            )
            return

        self.seated.append(user)
        self.user_by_id[user.id] = user
        embed = self._lobby_seat_embed(user.id)
        await interaction.response.send_message(
            embed=embed,
            view=SeatLobbyView(self),
            ephemeral=True,
        )
        try:
            self.messages[user.id] = await interaction.original_response()
        except discord.HTTPException:
            logger.warning("poker: could not capture seat handle for %s", user.id)
        await self._refresh_public()

    async def remove_player(self, interaction: discord.Interaction) -> None:
        user = interaction.user
        if self.started:
            await interaction.response.send_message(
                "The hand is in progress — you can fold, but you can't leave mid-hand.",
                ephemeral=True,
            )
            return
        if not self.is_seated(user.id):
            await interaction.response.send_message(
                "You're not seated at this table.",
                ephemeral=True,
            )
            return
        self.seated = [u for u in self.seated if u.id != user.id]
        self.user_by_id.pop(user.id, None)
        self.messages.pop(user.id, None)
        await interaction.response.edit_message(
            content="You left the table. 👋",
            embed=None,
            view=None,
        )
        await self._refresh_public()

    async def cancel(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.host.id:
            await interaction.response.send_message(
                "Only the host can close this table.",
                ephemeral=True,
            )
            return
        await self._teardown("The host closed the table.")
        await safe_defer(interaction)

    # --------------------------------------------------------------- game flow

    async def start(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.host.id:
            await interaction.response.send_message(
                "Only the host can start the table.",
                ephemeral=True,
            )
            return
        if len(self.seated) < MIN_PLAYERS:
            await interaction.response.send_message(
                f"Need at least {MIN_PLAYERS} players to start.",
                ephemeral=True,
            )
            return
        await safe_defer(interaction)
        self.started = True
        players = [
            Player(user_id=u.id, name=_display_name(u), stack=START_STACK)
            for u in self.seated
        ]
        self.game = PokerGame(
            players,
            small_blind=SMALL_BLIND,
            big_blind=BIG_BLIND,
            button=0,
        )
        self.game.begin_hand()
        self._schedule_turn()
        await self._broadcast()

    async def deal_next_hand(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.host.id:
            await interaction.response.send_message(
                "Only the host can deal the next hand.",
                ephemeral=True,
            )
            return
        if self.game is None:
            await safe_defer(interaction)
            return
        funded = [p for p in self.game.players if p.stack > 0]
        if len(funded) < MIN_PLAYERS:
            await safe_defer(interaction)
            await self._teardown(
                (
                    f"🏆 **{funded[0].name}** wins the table with all the chips!"
                    if funded
                    else "The table is out of chips."
                ),
            )
            return
        await safe_defer(interaction)
        try:
            self.game.begin_hand()
        except PokerError:
            await self._teardown("Not enough funded players to continue.")
            return
        self._schedule_turn()
        await self._broadcast()

    async def handle_action(
        self,
        interaction: discord.Interaction,
        action: Action,
        *,
        raise_to: int | None = None,
    ) -> None:
        if self.game is None or self.ended:
            await interaction.response.send_message(
                "This table is no longer active.",
                ephemeral=True,
            )
            return
        current = self.game.current_player
        if current is None or current.user_id != interaction.user.id:
            await interaction.response.send_message(
                "It's not your turn.",
                ephemeral=True,
            )
            return
        await safe_defer(interaction)
        # Refresh this seat's webhook handle from the live interaction so its
        # ephemeral stays editable for the rest of the session.
        try:
            self.messages[interaction.user.id] = await interaction.original_response()
        except discord.HTTPException:
            pass
        try:
            self.game.act(action, raise_to=raise_to)
        except PokerError as exc:
            await interaction.followup.send(f"⚠️ {exc}", ephemeral=True)
            return
        await self._advance_after_state_change()

    async def _advance_after_state_change(self) -> None:
        if self.game is not None and self.game.is_hand_over:
            self._cancel_turn()
            await self._broadcast()
        else:
            self._schedule_turn()
            await self._broadcast()

    # ----------------------------------------------------------- turn timer

    def _schedule_turn(self) -> None:
        self._turn_token += 1
        token = self._turn_token
        self._cancel_turn()
        if self.game is not None and self.game.current_player is not None:
            self._turn_task = self.bot.loop.create_task(self._turn_timeout(token))

    def _cancel_turn(self) -> None:
        if self._turn_task is not None and not self._turn_task.done():
            self._turn_task.cancel()
        self._turn_task = None

    async def _turn_timeout(self, token: int) -> None:
        try:
            await asyncio.sleep(TURN_SECONDS)
            if token != self._turn_token or self.ended or self.game is None:
                return
            current = self.game.current_player
            if current is None:
                return
            actions = self.game.legal_actions()
            # Idle players check when free, otherwise fold — never lose chips to AFK.
            if "check" in actions:
                self.game.act(Action.CHECK)
            else:
                self.game.act(Action.FOLD)
            self.game.log.append(f"⏳ {current.name} timed out.")
            await self._advance_after_state_change()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 — a timer must never crash the loop
            logger.warning("poker: turn-timeout handler failed", exc_info=True)

    # ----------------------------------------------------------- broadcast

    async def _broadcast(self) -> None:
        """Re-render and push every seat's ephemeral + the public board."""
        if self.game is None:
            return
        for player in self.game.players:
            handle = self.messages.get(player.user_id)
            if handle is None:
                continue
            embed = self._seat_embed(player.user_id)
            view = self._seat_view(player.user_id)
            try:
                await handle.edit(embed=embed, view=view)
            except discord.HTTPException:
                logger.warning("poker: seat edit failed for %s", player.user_id)
        await self._refresh_public()

    async def _refresh_public(self) -> None:
        embed = self._public_embed()
        view = self._public_view()
        try:
            if self.public_message is not None:
                await self.public_message.edit(embed=embed, view=view)
        except discord.HTTPException:
            logger.warning("poker: public board edit failed")

    async def _teardown(self, reason: str) -> None:
        if self.ended:
            return
        self.ended = True
        self._cancel_turn()
        _tables.pop(self.channel_id, None)
        embed = discord.Embed(
            title="♠ Poker Table — closed",
            description=reason,
            color=GAME_COLOR,
        )
        try:
            if self.public_message is not None:
                await self.public_message.edit(embed=embed, view=None)
        except discord.HTTPException:
            pass
        # Drop the action buttons from each seat panel.
        for handle in self.messages.values():
            try:
                await handle.edit(view=None)
            except discord.HTTPException:
                pass

    # ----------------------------------------------------------- rendering

    def _name(self, user_id: int) -> str:
        user = self.user_by_id.get(user_id)
        return _display_name(user) if user is not None else f"Player {user_id}"

    def _lobby_seat_embed(self, user_id: int) -> discord.Embed:
        embed = discord.Embed(
            title="♠ You're seated!",
            description=(
                "You've joined the poker table. When the host starts, your "
                "private hand will appear **right here** in this message and "
                "update live as everyone plays.\n\n"
                f"Everyone starts with **{START_STACK}** chips. "
                f"Blinds are {SMALL_BLIND}/{BIG_BLIND}."
            ),
            color=GAME_COLOR,
        )
        embed.set_footer(text="Texas Hold'em · play-chips")
        return embed

    def _seat_embed(self, user_id: int) -> discord.Embed:
        game = self.game
        if game is None:
            return discord.Embed(title="♠ Poker", color=GAME_COLOR)
        player = next(p for p in game.players if p.user_id == user_id)
        is_turn = (
            game.current_player is not None
            and game.current_player.user_id == user_id
            and not game.is_hand_over
        )
        title = "🟢 Your Hand — your turn!" if is_turn else "♠ Your Hand"
        embed = discord.Embed(title=title, color=GAME_COLOR)
        hole = "🃏 *folded*" if player.folded else _fmt_cards(player.hole)
        embed.add_field(name="Your cards", value=hole, inline=False)
        embed.add_field(name="Board", value=_board_str(game.board), inline=False)
        embed.add_field(name="💰 Pot", value=str(game.pot_total), inline=True)
        embed.add_field(name="🪙 Your stack", value=str(player.stack), inline=True)
        if player.all_in:
            embed.add_field(name="Status", value="**ALL-IN**", inline=True)
        elif not game.is_hand_over and not player.folded:
            idx = game.players.index(player)
            embed.add_field(name="To call", value=str(game.to_call(idx)), inline=True)

        if game.is_hand_over:
            embed.add_field(name="Result", value=self._results_text(), inline=False)
        else:
            turn_name = game.current_player.name if game.current_player else "—"
            embed.add_field(
                name="Turn",
                value="**Your turn!**" if is_turn else f"Waiting for **{turn_name}**…",
                inline=False,
            )
        log_tail = "\n".join(game.log[-4:]) if game.log else "—"
        embed.add_field(name="Recent action", value=log_tail, inline=False)
        embed.set_footer(text=f"Blinds {SMALL_BLIND}/{BIG_BLIND} · Texas Hold'em")
        return embed

    def _public_embed(self) -> discord.Embed:
        if not self.started or self.game is None:
            return self._lobby_public_embed()
        game = self.game
        embed = discord.Embed(title="♠ Poker Table", color=GAME_COLOR)
        embed.add_field(name="Board", value=_board_str(game.board), inline=False)
        embed.add_field(name="💰 Pot", value=str(game.pot_total), inline=True)
        embed.add_field(name="Hand #", value=str(game.hand_number), inline=True)

        lines = []
        for i, p in enumerate(game.players):
            marker = "🔘" if i == game.button else "▫️"
            if game.is_hand_over:
                status = ""
            elif p.folded:
                status = " — *folded*"
            elif p.all_in:
                status = " — **all-in**"
            elif (
                game.current_player is not None
                and game.current_player.user_id == p.user_id
            ):
                status = " — 🟢 to act"
            else:
                status = ""
            lines.append(f"{marker} **{p.name}** · {p.stack} chips{status}")
        embed.add_field(name="Players", value="\n".join(lines), inline=False)

        if game.is_hand_over:
            embed.add_field(name="🏆 Result", value=self._results_text(), inline=False)
            embed.set_footer(
                text="Host: press “Deal next hand”. Hands aren't restart-safe.",
            )
        else:
            embed.set_footer(
                text="Your private hand is in your ephemeral message above.",
            )
        return embed

    def _lobby_public_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="♠ Poker Table — open!",
            description=(
                "**Texas Hold'em**, group play. Press **Join** to take a seat — "
                "you'll get a private hand that updates live as everyone plays.\n\n"
                f"Buy-in: **{START_STACK}** play-chips · Blinds {SMALL_BLIND}/{BIG_BLIND} · "
                f"up to {MAX_SEATS} seats."
            ),
            color=GAME_COLOR,
        )
        seat_lines = [
            f"{'👑 ' if u.id == self.host.id else '• '}{_display_name(u)}"
            for u in self.seated
        ]
        embed.add_field(
            name=f"Seated ({len(self.seated)}/{MAX_SEATS})",
            value="\n".join(seat_lines) or "—",
            inline=False,
        )
        embed.set_footer(text=f"Host {_display_name(self.host)} starts when ready.")
        return embed

    def _results_text(self) -> str:
        game = self.game
        if game is None or not game.results:
            return "—"
        parts = []
        for res in game.results:
            name = self._name(res.user_id)
            if res.hand_label:
                parts.append(f"**{name}** +{res.amount} ({res.hand_label})")
            else:
                parts.append(f"**{name}** +{res.amount}")
        return "\n".join(parts)

    # ----------------------------------------------------------- view builders

    def _public_view(self) -> discord.ui.View | None:
        if self.ended:
            return None
        if self.game is not None and self.game.is_hand_over:
            return PokerEndView(self)
        return None

    def _seat_view(self, user_id: int) -> discord.ui.View | None:
        game = self.game
        if game is None or game.is_hand_over:
            return None
        is_turn = (
            game.current_player is not None and game.current_player.user_id == user_id
        )
        if not is_turn:
            return None
        return PokerSeatView(self, user_id)


def _display_name(user: discord.abc.User | None) -> str:
    if user is None:
        return "Player"
    return getattr(user, "display_name", None) or user.name


# --------------------------------------------------------------------------- #
# Views (game-state lifecycle → extend discord.ui.View directly, per the
# views/base.py doctrine for specialised game views).
# --------------------------------------------------------------------------- #


class PokerLobbyView(discord.ui.View):
    """Public lobby controls on the channel message: Join / Leave / Start / Close."""

    def __init__(self, table: PokerTable) -> None:
        super().__init__(timeout=LOBBY_TIMEOUT)
        self.table = table

    @discord.ui.button(label="Join", style=discord.ButtonStyle.success, emoji="🪑")
    async def join(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await self.table.add_player(interaction)

    @discord.ui.button(label="Leave", style=discord.ButtonStyle.secondary, emoji="🚪")
    async def leave(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await self.table.remove_player(interaction)

    @discord.ui.button(label="Start", style=discord.ButtonStyle.primary, emoji="▶️")
    async def start(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await self.table.start(interaction)

    @discord.ui.button(label="Close", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def close(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await self.table.cancel(interaction)


class SeatLobbyView(discord.ui.View):
    """The ephemeral seat panel shown while waiting in the lobby (Leave only)."""

    def __init__(self, table: PokerTable) -> None:
        super().__init__(timeout=LOBBY_TIMEOUT)
        self.table = table

    @discord.ui.button(
        label="Leave seat",
        style=discord.ButtonStyle.secondary,
        emoji="🚪",
    )
    async def leave(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await self.table.remove_player(interaction)


class PokerEndView(discord.ui.View):
    """Public host controls shown after a hand finishes."""

    def __init__(self, table: PokerTable) -> None:
        super().__init__(timeout=GAME_TIMEOUT)
        self.table = table

    @discord.ui.button(
        label="Deal next hand",
        style=discord.ButtonStyle.success,
        emoji="🃏",
    )
    async def next_hand(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        await self.table.deal_next_hand(interaction)

    @discord.ui.button(label="End table", style=discord.ButtonStyle.danger, emoji="🛑")
    async def end(
        self,
        interaction: discord.Interaction,
        _button: discord.ui.Button,
    ) -> None:
        if interaction.user.id != self.table.host.id:
            await interaction.response.send_message(
                "Only the host can end the table.",
                ephemeral=True,
            )
            return
        await self.table._teardown("The host ended the table. Thanks for playing! 🎉")
        await safe_defer(interaction)


class _ActionButton(discord.ui.Button):
    def __init__(
        self,
        table: PokerTable,
        action: Action,
        label: str,
        style: discord.ButtonStyle,
        *,
        raise_to: int | None = None,
        emoji: str | None = None,
    ) -> None:
        super().__init__(label=label, style=style, emoji=emoji)
        self._table = table
        self._action = action
        self._raise_to = raise_to

    async def callback(self, interaction: discord.Interaction) -> None:
        await self._table.handle_action(
            interaction,
            self._action,
            raise_to=self._raise_to,
        )


class PokerSeatView(discord.ui.View):
    """The in-hand action panel — built dynamically from the legal actions.

    Restricted to the seat owner; only ever attached to the message of the
    player whose turn it is, so its buttons map exactly to that player's options.
    """

    def __init__(self, table: PokerTable, user_id: int) -> None:
        super().__init__(timeout=GAME_TIMEOUT)
        self.table = table
        self.user_id = user_id
        self._build()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                "This isn't your seat.",
                ephemeral=True,
            )
            return False
        return True

    def _build(self) -> None:
        game = self.table.game
        if game is None:
            return
        actions = game.legal_actions()
        self.add_item(
            _ActionButton(
                self.table,
                Action.FOLD,
                "Fold",
                discord.ButtonStyle.danger,
                emoji="🏳️",
            ),
        )
        if "check" in actions:
            self.add_item(
                _ActionButton(
                    self.table,
                    Action.CHECK,
                    "Check",
                    discord.ButtonStyle.secondary,
                    emoji="✅",
                ),
            )
        if "call" in actions:
            amount = int(actions["call"])  # type: ignore[call-overload]
            self.add_item(
                _ActionButton(
                    self.table,
                    Action.CALL,
                    f"Call {amount}",
                    discord.ButtonStyle.primary,
                    emoji="📞",
                ),
            )
        raise_spec = actions.get("raise")
        if isinstance(raise_spec, dict):
            lo = int(raise_spec["min"])
            hi = int(raise_spec["max"])
            pot_raise = min(max(lo, game.pot_total), hi)
            verb = "Bet" if game.current_bet == 0 else "Raise to"
            self.add_item(
                _ActionButton(
                    self.table,
                    Action.RAISE,
                    f"{verb} {lo}",
                    discord.ButtonStyle.success,
                    raise_to=lo,
                    emoji="⬆️",
                ),
            )
            if pot_raise > lo:
                self.add_item(
                    _ActionButton(
                        self.table,
                        Action.RAISE,
                        f"{verb} {pot_raise} (pot)",
                        discord.ButtonStyle.success,
                        raise_to=pot_raise,
                        emoji="🔥",
                    ),
                )
            if hi > pot_raise:
                self.add_item(
                    _ActionButton(
                        self.table,
                        Action.RAISE,
                        f"All-in {hi}",
                        discord.ButtonStyle.success,
                        raise_to=hi,
                        emoji="💥",
                    ),
                )
