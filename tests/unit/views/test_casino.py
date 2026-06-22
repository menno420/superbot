"""Tests for the Casino subsystem wiring + poker-table rendering.

The pure game logic is covered in tests/unit/utils/test_poker_*; here we cover
the Discord-facing seams that don't need a live client: registry wiring, the
hub panel builder, and the table's embed/view renderers (driven with lightweight
fake users so no Discord connection is required).
"""

from __future__ import annotations

from types import SimpleNamespace

from utils.poker.engine import Player, PokerGame
from utils.subsystem_registry import SUBSYSTEMS
from views.casino import build_casino_hub_panel
from views.casino.hub import CasinoHubView
from views.casino.poker_table import PokerSeatView, PokerTable
from views.games.hub import discover_game_children


def _user(uid: int, name: str) -> SimpleNamespace:
    return SimpleNamespace(id=uid, display_name=name, name=name.lower())


def test_casino_registered_under_games() -> None:
    meta = SUBSYSTEMS["casino"]
    assert meta["parent_hub"] == "games"
    assert meta["hub_group"] == "competitive"
    assert "poker" in meta["entry_points"]
    names = [name for name, _ in discover_game_children()]
    assert "casino" in names


def test_build_casino_hub_panel() -> None:
    author = _user(1, "Alice")
    embed, view = build_casino_hub_panel(author)
    assert "Casino" in (embed.title or "")
    assert isinstance(view, CasinoHubView)


def _seated_table() -> PokerTable:
    host = _user(1, "Alice")
    table = PokerTable(bot=None, channel=None, channel_id=10, host=host)  # type: ignore[arg-type]
    bob = _user(2, "Bob")
    table.seated.append(bob)
    table.user_by_id[bob.id] = bob
    return table


def test_lobby_public_embed_before_start() -> None:
    table = _seated_table()
    embed = table._public_embed()
    assert "open" in (embed.title or "").lower()
    # Both seated players appear in the lobby list.
    rendered = " ".join(f.value for f in embed.fields)
    assert "Alice" in rendered and "Bob" in rendered


def test_in_game_embeds_render() -> None:
    table = _seated_table()
    table.game = PokerGame(
        [Player(1, "Alice", 1000), Player(2, "Bob", 1000)],
        small_blind=5,
        big_blind=10,
        button=0,
    )
    table.game.begin_hand()
    table.started = True

    public = table._public_embed()
    assert public.title == "♠ Poker Table"
    field_names = {f.name for f in public.fields}
    assert "Board" in field_names and "Players" in field_names

    # The seat embed shows the player's two private hole cards.
    seat = table._seat_embed(1)
    cards_field = next(f for f in seat.fields if f.name == "Your cards")
    assert cards_field.value.count("`") == 4  # two `card` codes => four backticks


def test_seat_view_only_for_current_player() -> None:
    table = _seated_table()
    table.game = PokerGame(
        [Player(1, "Alice", 1000), Player(2, "Bob", 1000)],
        small_blind=5,
        big_blind=10,
        button=0,
    )
    table.game.begin_hand()
    table.started = True
    current = table.game.current_player
    assert current is not None
    other_id = 2 if current.user_id == 1 else 1
    assert isinstance(table._seat_view(current.user_id), PokerSeatView)
    assert table._seat_view(other_id) is None
