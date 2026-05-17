"""RPS rules engine — pure functions, no cog state (S4.4 extraction).

Extracted from ``cogs/rps_tournament_cog.py`` so the rules table and
the win-determination logic live separately from the orchestration
state (players, scores, channels, brackets) that remains on the cog.

The four game modes (classic, lizard_spock, chess, elemental) and
their alias / win-condition tables are static; lifting them to module
level removes a per-cog dict-rebuild on every reload and lets the
rules be tested without a fully-initialised cog.

Public surface:

    MOVE_ALIASES     — alias → canonical-move lookups (closed dict)
    GAME_MODES       — mode-name → canonical-move-list
    WIN_CONDITIONS   — mode-name → {move → list-of-moves-it-beats}
    normalize_move   — alias → canonical move within a mode (sync, pure)
    determine_winner — (m1, m2, mode) → 0 tie / 1 m1 / 2 m2 (sync, pure)
"""

from __future__ import annotations

MOVE_ALIASES: dict[str, list[str]] = {
    "rock": ["rock", "stone", "pebble", "boulder", "🪨", "🤜", "✊"],
    "paper": ["paper", "sheet", "page", "📄", "📰", "✋"],
    "scissors": ["scissors", "shears", "✂️", "✌️"],
    "lizard": ["lizard", "🦎"],
    "spock": ["spock", "🖖"],
    "pawn": ["pawn", "♟️"],
    "knight": ["knight", "horse", "♞"],
    "queen": ["queen", "♛"],
    "fire": ["fire", "flame", "🔥"],
    "water": ["water", "💧", "🌊"],
    "grass": ["grass", "leaf", "🌿", "🍃"],
}

GAME_MODES: dict[str, list[str]] = {
    "classic": ["rock", "paper", "scissors"],
    "lizard_spock": ["rock", "paper", "scissors", "lizard", "spock"],
    "chess": ["pawn", "knight", "queen"],
    "elemental": ["fire", "water", "grass"],
}

WIN_CONDITIONS: dict[str, dict[str, list[str]]] = {
    "classic": {"rock": ["scissors"], "paper": ["rock"], "scissors": ["paper"]},
    "lizard_spock": {
        "rock": ["scissors", "lizard"],
        "paper": ["rock", "spock"],
        "scissors": ["paper", "lizard"],
        "lizard": ["spock", "paper"],
        "spock": ["scissors", "rock"],
    },
    "chess": {"pawn": ["knight"], "knight": ["queen"], "queen": ["pawn"]},
    "elemental": {"fire": ["grass"], "water": ["fire"], "grass": ["water"]},
}


def normalize_move(input_move: str, mode: str) -> str | None:
    """Resolve an alias to the canonical move under *mode*, or return None.

    Examples:
        >>> normalize_move("rock", "classic")
        'rock'
        >>> normalize_move("🪨", "classic")
        'rock'
        >>> normalize_move("lizard", "classic")  # not in classic mode
        >>> normalize_move("lizard", "lizard_spock")
        'lizard'
    """
    for move, aliases in MOVE_ALIASES.items():
        if input_move in aliases and move in GAME_MODES[mode]:
            return move
    return None


def determine_winner(move1: str, move2: str, mode: str) -> int:
    """Return 0 (tie), 1 (move1 wins), or 2 (move2 wins) under *mode*.

    Assumes both moves are already canonical (post-normalize_move) and
    that *mode* exists in WIN_CONDITIONS.  Callers route invalid moves
    away before reaching this function.
    """
    if move1 == move2:
        return 0
    if move2 in WIN_CONDITIONS[mode][move1]:
        return 1
    return 2
