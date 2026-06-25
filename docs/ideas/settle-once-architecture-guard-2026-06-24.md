# A `check_architecture` rule: settling game paths must adopt `SettleOnceMixin`

> **Status:** `ideas` — **money leg BUILT** (2026-06-25 dispatch run, PR #1454). Not approval.
> Source code and the binding contracts win.
> **Subsystem:** none — an agent-tooling / CI-invariant idea (touches no bot subsystem at runtime).

> **▶ Built (2026-06-25 dispatch run, PR #1454):** the **money leg** shipped as
> `check_consistency.py` **Rule 6 (`settle_once_adoption`)** — a call to
> `game_wager_workflow.settle_pvp` / `refund_pvp` must adopt the settle-once guard (enclosing
> class mixes in `SettleOnceMixin` / calls `claim_settlement()`, or the enclosing function calls
> `claim_settlement()` — the blackjack module-level-settle shape). **Warn-first** (the posture
> §"Open / cautions" prescribed — the mixin is young), runs clean today (both callers adopt),
> scopes `views/` + `services/`. The **broader leg** below ("…*or otherwise posts a terminal
> result*" reachable from `on_timeout`/a second trigger) is **deliberately deferred** — static
> "settles via a result message reachable from `on_timeout`" detection is false-positive-prone,
> and a warn-clean rule must stay precise (the §"Open / cautions" conservatism). Revisit once the
> money leg graduates to `error` and the mixin has more adopters to key the structural leg on.

> **Provenance:** session idea (Q-0089) from the settle-once terminal-guard dispatch run
> (2026-06-24, PRs #1444 + #1445). That run found the cross-game double-settlement class by **reading
> four game views by hand** (RPS PvP, deathmatch bot-duel, blackjack PvP, plus the BUG-0013 challenge
> view) and adopting the new `SettleOnceMixin` (`disbot/utils/terminal_guard.py`) in each. The manual
> hunt is the part worth mechanizing.

## The gap

The double-settlement class is structural and recurring: a game view (or game state object) whose
**settlement path** — it posts a result, or calls `game_wager_workflow.settle_pvp` / `refund_pvp`, or
records a terminal result — is reachable from **more than one trigger** (a finishing button *and*
`on_timeout`, or two players' finish callbacks). Without a single atomic claim, a racy second entry
double-posts and re-settles. BUG-0013 was one instance; the 2026-06-24 run found three more. Nothing
*prevents the next one* — a new game added next month repeats the pattern, and only a careful reviewer
catches it.

## The idea

A `scripts/check_architecture.py` rule (or a standalone Q-0105 disposable guard) that flags a
`discord.ui.View` subclass **or** a game state object when:

1. it (or a method it owns) calls a wager-settle helper (`settle_pvp` / `refund_pvp`) or otherwise
   posts a terminal result, **and**
2. that settling method is reachable from `on_timeout` *or* a second trigger (a button callback, a
   `on_finish` callback), **and**
3. the class does **not** mix in `SettleOnceMixin` / call `claim_settlement()` on its settling path.

The CI ratchet form of the by-hand review the run just did. Same shape as the existing
`select_option_truncation` consistency rule (a structural footgun caught statically).

## Why it's worth having

- Turns "an agent noticed it" into "CI enforces it" for a money-safety class.
- The target primitive now **exists and has proven itself** across three adopters (RPS, deathmatch,
  blackjack) — so the rule has a concrete, stable thing to require, not a hypothetical.

## Open / cautions

- Static reachability of "settling method called from `on_timeout`" is the hard part — an AST rule may
  need to be conservative (warn, allowlist) to avoid false positives on views that settle but are
  single-trigger by construction.
- **Build only after the mixin earns a couple more sessions of trust** (its own Q-0105 kill-switch
  posture) — a guard that hard-fails CI on a still-young convention is premature. Warn-first first.
- Dedup-checked `docs/ideas/` (2026-06-24): no existing settle-once / terminal-guard / double-settle
  idea. Adjacent but distinct: `ultracode-worker-pr-scope-guard-2026-06-23.md` (a *diff-scope* guard,
  not a runtime-safety one).
