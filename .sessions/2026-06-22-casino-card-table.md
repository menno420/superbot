# 2026-06-22 — Casino subsystem: multiplayer card-game table framework + Texas Hold'em poker

> **Status:** `in-progress`

## What I'm about to do

Owner-directed (asleep, "surprise me"): stand up a **Casino** subsystem under the Games hub
that supports **group card games** where every player gets their **own auto-updating ephemeral
message** so multiple people play the same table at once.

Plan for this session:
1. **Research + simulation** — a stdlib `tools/sim/casino_games_sim.py` evaluating which
   casino/card games play well in Discord (interaction style, group fit) + a design doc.
2. **Reusable primitives** — `utils/cards/` (Card/Deck/Rank/Suit, pure + tested) and
   `utils/poker/` (hand evaluation + comparison, pure + tested). Blackjack's engine is
   blackjack-specific; poker needs a real, shared, rankable card model.
3. **Table-session framework** — `services/casino/table_session.py`: a game-agnostic
   multiplayer table that holds shared state + a per-player ephemeral message registry and
   re-renders every seated player's private view on each state change (the marquee mechanic).
4. **First game — Texas Hold'em poker** on the framework: pure betting/pot engine (tested) +
   the per-player ephemeral view layer.
5. **Casino hub** registered under Games (`!casino`) so roulette/other games dock in later.

Money: v1 poker uses **table play-chips** (everyone starts equal), not real economy coins —
real-coin multi-party pots need N-party escrow (a money-safety follow-up, kept out of v1 on
purpose). Respects ADR-002 (in-flight state not restart-safe).
