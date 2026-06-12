# Wager / money-flow map — generated trace of game coin paths

> **Status:** `ideas`. **Not a plan, not approved.** Capture of the Q-0089 session
> idea from the P0-1 wager-money-safety session (PR #748). Source code + the binding
> contracts win over this file. Quick-win / read-only tooling lane.

## The gap (lived this session)

The single biggest cost of the P0-1 session was **hand-tracing where game money moves**.
A wagered PvP path touches **four files per game** — challenge-accept (escrow), play-resolve
(settle/refund), plus the tournament entry/payout split living in *yet another* pair of files
— and the tournament fee debit was hidden in `utils/tournaments.deduct_fees`, a shared helper
named nothing like "money". None of these adjacencies appear in any folio; the only way to
find them was grep + read. The session-log reflection flagged this as **"needed but not
pointed to."**

Now that P0-1 has converged every wagered move onto `services/game_wager_workflow.py`, the
flow is *finally* greppable from one seam — which makes it cheap to **generate** the map a
future "touch a wager path" session needs as a lookup instead of an archaeology dig.

## The idea

A read-only, offline **`scripts/wager_flow_map.py`** (mirroring `command_surface_dump.py` /
the AST-fence pattern) that, without a live bot:

1. Finds every call site of the `game_wager_workflow` ops (`open_pvp_wager`, `settle_pvp`,
   `refund_pvp`, `enter_tournament`, `payout_tournament`, `recover_escrow`) across
   `views/` + `cogs/`.
2. Finds every `*_escrow` / entry `game_state` subsystem constant and where it is written
   / settled / recovered.
3. Emits a per-game **accept → escrow → settle/refund** and **entry → payout** map
   (file:line for each leg), with a `--json` mode.

It doubles as the **human-readable companion to the AST fence**
(`test_game_wager_write_boundary`): the fence says "no money leaks *out* of the workflow";
the map says "here is the money that flows *through* it." A drift mode (`--check`) could
even assert every escrow subsystem has a matching settle **and** a recovery path — catching
a future game that escrows but forgets to refund.

## Why it's worth having

- Turns the most expensive part of this session (manual money-flow tracing) into a one-command
  lookup for the next.
- Pure read-only AST — no runtime, no bot, CI-safe; the disposable-guard discipline (Q-0105)
  applies.
- Naturally extends to **mining** (which has the same `*_workflow` seam) for a unified
  "where does the economy move?" map.

## Lane / routing

Quick-win, read-only tooling — **not auto-promoted**. Build it the next time a wager/economy
path is touched (the context is cheapest then), or as a standalone grooming slice. Dedup-checked
`docs/ideas/`: `command_surface_dump` (commands, not money), `review-unit-tagging` (review
partition), the mining brainstorm + games folio (features) — none cover a money-flow map.
