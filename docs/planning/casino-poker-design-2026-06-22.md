# Casino subsystem — design + first game (Texas Hold'em poker)

> **Status:** `plan` — design record + shipped-v1 notes. Owner-directed
> ("card games like poker, playable in a group, each player gets their own
> auto-updating ephemeral message; lean towards a Casino panel under Games";
> 2026-06-22). Source wins over this doc.

## The ask

> "Card game subsystem that includes games like poker and should be playable in
> a group, every player should get their own auto updating ephemeral message so
> multiple players can play and react at the same time… a 'casino' panel linked
> under games, so it can also include other games like roulette… research which
> games would be playable in discord… maybe run a simulator… surprise me."

Two hard parts: (1) **which** games, and (2) the **per-player auto-updating
ephemeral** group mechanic, which nothing in the bot did before.

## Research — which games fit Discord (simulator)

`tools/sim/casino_games_sim.py` scores candidates on the axes that actually
decide Discord fit — group support, benefit from *private* per-player views,
simultaneity, latency-safety (Discord's edit→render→click round-trip makes
sub-second reflex games unfair — see `fishing_minigame_sim.py`), decision depth,
and implementation cost. Result:

| Game | Score | Verdict |
|---|---|---|
| **Texas Hold'em poker** | **20** | Marquee. High on *every* axis; the one game that justifies the per-player ephemeral framework. |
| Blackjack (multiplayer table) | 18 | Great second game — reuse the existing blackjack engine; everyone vs the dealer. |
| Roulette | 17 | Cheapest add once the table framework exists (public board, no private hands). |
| Five-card draw | 17 | Private hands + betting, but the draw step adds UI for less payoff than Hold'em. |
| Liar's dice | 17 | Private dice + bluffing — a possible later surprise. |
| Baccarat / War | ≤14 | Near-zero decisions; pure variance. Filler at best. |

The same sim **Monte-Carlo-validates the shipped engine**: thousands of random
all-in hands conserve chips every time, and 7-card showdown hand frequencies
match known poker odds (pair ~44%, two pair ~24%, flush ~3%, full house ~2.5%,
quads ~0.16%, straight flush ~0.04%).

## The per-player auto-updating ephemeral mechanic

A Discord **ephemeral** message can only be edited through the interaction
(webhook) token that created it. So:

1. A player presses **Join** → the bot sends them an *ephemeral* seat panel and
   keeps the returned `discord.InteractionMessage` handle.
2. Whenever shared state changes (any player acts), the table **re-renders and
   edits every seat's stored handle** plus the public spectator message — so
   each player's private view updates live in response to others' actions.
3. A seat's handle is refreshed from its owner's own action interactions; the
   webhook token lives ~15 min and a hand is far shorter, so a session never
   hits the limit. A per-turn idle clock (90 s) auto-checks/folds an AFK seat so
   one absent player can't stall the table.

This is the reusable core: a future **roulette** is the same "shared table +
per-player ephemeral" pattern with a wheel instead of cards.

## Architecture (layering)

```
utils/cards/                  pure 52-card primitives (Card/Deck, ordered ranks)   ← shared
utils/poker/evaluate.py       pure hand evaluation (best 5-of-7, comparable score)
utils/poker/engine.py         pure Texas Hold'em state machine (blinds, betting,
                              all-ins, SIDE POTS, showdown) — Discord-free, tested
views/casino/poker_table.py   the per-player ephemeral table + broadcast + turns
views/casino/hub.py           the Casino navigation hub (Games-hub child)
cogs/casino_cog.py            commands (!casino, !poker), help hook
```

The pure layers carry the correctness risk and are fully unit-tested; the view
layer is a thin renderer. `services → views` is never crossed (no service is
involved — v1 is play-chips only). Blackjack's card helpers stay
blackjack-specific; the new `utils/cards` + `utils/poker` are the shared,
*rankable* model poker needs.

## Money (deliberate v1 scope)

v1 uses **table play-chips**: every seat starts at 1000, blinds 5/10, chips
never leave the table. Real-coin buy-ins are intentionally **out of v1** —
a multi-party pot needs N-party escrow through `game_wager_workflow` (the same
money-safety seam mining/PvP use), which is a follow-up, not a first cut. This
also keeps the feature inside the "free for everyone, no pay-to-win" mission
(Q-0190) trivially. In-flight table state is in-memory and **not restart-safe by
design** (ADR-002), exactly like blackjack/RPS.

## Where it lives in the UI

`Games hub → 🎰 Casino → 🃏 New Poker Table`, plus typed `!casino` / `!poker`.
Roulette is a disabled "coming soon" tile in the Casino hub.

## Follow-ups (not in v1)

1. **Real-coin buy-in/cash-out** via N-party escrow (`game_wager_workflow`) +
   game-XP award on table finish. Highest-value next slice; money-safety-gated.
2. **Roulette** on the same table framework (public board, no private hands).
3. **Multiplayer blackjack table** (reuse `blackjack_engine`, everyone vs dealer).
4. **Custom raise amount** via a modal (v1 offers min / pot / all-in quick bets).
5. Promote the generic "shared table + per-player ephemeral broadcaster" out of
   `poker_table.py` into a reusable `views/casino/table.py` on the rule of three
   (when roulette + blackjack-table both need it).
6. Optional bot opponents so a solo player can practice.
