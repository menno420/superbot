# Definition of Complete — games

> **Status:** `reference` — the completeness rubric for a **game** unit. Grounded in
> [`command-integration-standard`](../../building-roadmap/command-integration-standard.md) §
> "Game panel requirements" / "Testing requirements", [`hub-ui-standard`](../../building-roadmap/hub-ui-standard.md),
> and ADR-002 (game state is intentionally not restart-safe). System: [`README.md`](README.md).

A game is **complete** when it has every function it should, the right buttons in the right places,
it works as intended in every case, and it is the most convenient version of itself. This rubric
turns that into checkable items. Copy the template at the bottom into `units/<key>.md`, then tick
each box **or waive it with a one-line reason**. Every unticked, un-waived box is a **punch-list**
item; the unit cannot be `✔ certified` until the punch-list is empty and the owner signs off.

---

## A. Game-loop completeness — "all the functions"

- [ ] **Every game mode the concept implies exists** (e.g. solo-vs-house · head-to-head PvP ·
      tournament/lobby) and each is reachable.
- [ ] **Every standard action for this game exists** — benchmarked against a best-in-class version
      of the same game. Missing standard actions are listed explicitly (not silently absent).
- [ ] **The loop runs start → finish cleanly**: setup/deal → play → resolve → reward/payout, with a
      clear terminal result.
- [ ] **No dead-end or placeholder controls** — no "coming soon", no disabled-with-no-explanation,
      no button that errors or no-ops (`command-integration-standard` § "no dead-end views").
- [ ] **Rewards/XP are wired** through the correct service (game-XP / economy), not duplicated.

## B. UI & buttons — "the right buttons in the right places"

- [ ] **A game panel exists** summarizing the game and offering its modes (`command-integration-standard`
      § "Game panel requirements": choose mode · start · replay same mode · change mode · view rules ·
      back to panel · back to Help).
- [ ] **Every action has a control in the right place** — primary actions on the action view; mode
      selection on the panel; nothing buried or misplaced.
- [ ] **A "Rules / how to play" affordance** is reachable.
- [ ] **Return navigation everywhere** — back to the game panel and to Help; no trapped views.
- [ ] **Terminal state is visually correct** — finished hands/rounds disable or swap their controls;
      no stale clickable buttons after the game ends.
- [ ] **Embeds/copy are consistent** — titles, emojis, result text follow the house style; no
      debug/placeholder strings.

## C. Convenience — "the most convenient way"

- [ ] **No needless clicks** — common paths (start, replay, re-bet) are one obvious action.
- [ ] **Replay without retyping** — a "play again" / "rematch" affordance; the player never has to
      re-issue the command after each round (`command-integration-standard` § "Game flows should not
      require the user to retype commands").
- [ ] **Sensible defaults + presets** — bet/option pickers offer quick presets, not only free text.
- [ ] **Reachable the natural way** — its command(s) **and** the Games hub **and** Help all lead to it.

## D. Edge cases & lifecycle — "works as intended in every case"

- [ ] **Timeout** handled — idle views time out, disable controls, and clean up.
- [ ] **Expired / stale interaction** handled — callbacks `safe_defer`/guard against dead tokens.
- [ ] **Authority re-checked at callback time** — only the initiating player(s) can act; opening a
      panel does not authorize later callbacks.
- [ ] **Concurrency** handled — second player joining, double-click, racing resolution (settle-once).
- [ ] **Restart behavior is correct per ADR-002** — in-flight state need not survive restart, but
      **money is never lost** and stranded stakes are recovered/refunded.

## E. Money-safety integration (links the readiness axis)

- [ ] **Wagered/paid flows route through the audited seam** — solo via `economy_service`; two-party /
      paid-entry via `game_wager_workflow` (escrow-at-accept, idempotent settle/refund/payout).
- [ ] **No mint window** — stakes leave wallets atomically; replays/timeouts cannot double-pay.
- [ ] **Recovery paths exist** — crash / guild-removal refund or clear stranded game state.

## F. Wiring & discoverability

- [ ] **Registered in the subsystem registry** with correct `entry_points`, `parent_hub`,
      `hub_group`, and `capabilities`.
- [ ] **Discoverable in Help** (`command-integration-standard` § 2).
- [ ] **Settings exist where the game needs them** (e.g. entry fee, limits) and route through the
      settings pipeline.

## G. Tests & evidence (required for `✔ certified`)

- [ ] **Loop tests** — deal/play/resolve/payout covered for each mode.
- [ ] **Edge tests** — timeout, settle-once / double-resolution, recovery/refund.
- [ ] **Money tests** — escrow/settle/refund idempotency for paid modes.
- [ ] **Live walkthrough recorded** — `/verify-bot` boot + a scripted click-through of every mode,
      with screenshots, attached to the certificate.
- [ ] **Owner ✔** — the maintainer has played it and confirms "nothing left I'd add or move."

---

## Certificate template

Copy into `units/<registry-key>.md`:

```markdown
# <Game name> — completion certificate

> **Status:** `living-ledger` — per-unit completion certificate. System: [`../README.md`](../README.md).

> **Unit:** `<registry-key>` · **Type:** game · **Family:** <competitive|activity>
> **State:** ◐ assessed · **Assessed:** <date> · **Certified:** —
> Source: <cog> · <views/> · <service>

## Rubric (game)
A. Loop completeness — <tick/notes per item>
B. UI & buttons — …
C. Convenience — …
D. Edge cases & lifecycle — …
E. Money-safety — …
F. Wiring & discoverability — …
G. Tests & evidence — …

## Punch-list (open gaps → certify by clearing these)
1. …

## Evidence
- Tests: <paths>
- Walkthrough: <link / pending>
- Owner sign-off: <pending | ✔ date>
```
