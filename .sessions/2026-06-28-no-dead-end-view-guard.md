# 2026-06-28 — No-dead-end terminal-view arch guard (friction→guard)

> **Status:** `complete`

**Run type:** routine · dispatch

## What I'm about to do

Empty-fire dispatch. S1's ▶ Next-startable (offline) names: *"build the 'no-dead-end' arch guard
so the trapped-view bug class is caught automatically instead of per-assessment."* The completion-first
posture (Q-0209) keeps re-finding the same dead-end bug one game at a time (Fishing #1521, Deathmatch
+ RPS PvP #1527). This is the textbook friction→guard case (Q-0194): enforce, don't exhort.

**The slice:** a conservative warn-tier rule in `scripts/check_architecture.py` that flags a game
view's **terminal handler** (a method calling `self.stop()`) that re-renders / posts a terminal message
without swapping to a nav-carrying view (no other `*View(...)` constructed in the handler body). Scoped
to game-view dirs, allowlist-driven (same shape as `baseview_inheritance`), starts as warning. Verified
clean (or known-small) against the current fixed fleet, with unit tests pinning both the flagged
anti-pattern and the allowed swap pattern.

Offline / self-mergeable on green; checker guard ships free per CLAUDE.md.

## What shipped (PR #1529)

The **`no_dead_end` arch guard** — a warn-tier rule in `scripts/check_architecture.py`
(`check_no_dead_end_terminal_views`) that flags a **game-view terminal handler** (a method calling
`self.stop()`) which renders a terminal message but neither **swaps** to a freshly-constructed
`*View` nor **delegates** to another awaited coroutine. That heuristic — "stop + render + no swap +
no delegate" — isolates the real trapped-view dead-end from the legitimate launcher/transition cases.

- **Config + allowlist** in `architecture_rules/canonical_helpers.yaml` (`no_dead_end` block): scoped
  to game-view dirs (`views/rps|blackjack|casino|fishing|games/`), `ClassName.method` exemptions for
  the 4 genuine pre-game **invite** decline/timeout handlers (`_ChallengeView` / `_RpsPvpChallengeView`),
  with a documented kill-switch (delete the block + checker if it proves noisy — Q-0105).
- **Clean on the current (fixed) fleet:** the refined heuristic yielded exactly the 4 invite-closer
  findings, all allowlisted → 0 unexplained warnings (`by check` shows no `no_dead_end`). Going forward,
  a new game whose *resolve* path forgets to swap to a result view gets flagged automatically.
- **+7 tests** (`tests/unit/scripts/test_check_architecture.py`): flags the trapped terminal handler
  (fails against the pre-guard world), and does NOT flag a view swap, a coroutine delegation, an
  allowlisted `Class.method`, a non-game dir, a handler that never `stop()`s, or an unconfigured rule.
- **Wired into the completion rubric** ("No dead-end controls" line, `rubric-game.md`) as a partial
  enforcement backstop; idea file re-badged `historical` (shipped); S1 sector ▶ Next + recently-shipped
  de-staled.

CI mirror green: `check_quality --full` (ruff/black/isort/mypy + 12,975 tests pass) + `check_docs
--strict` + `check_consistency`; `check_architecture --mode strict` exit 0. Self-merged on green
(small, contained, additive checker/docs — `CLASS: feature`/tooling, self-initiated Q-0172; guards
ship free per CLAUDE.md).

## 📤 Run report

- **Did:** built the no-dead-end terminal-view arch guard, the named S1 ▶ Next offline-startable item
  (a friction→guard enforcement for the recurring trapped-view bug class) · **Outcome:** shipped
- **Shipped:** #1529 — `no_dead_end` rule + config/allowlist + 7 tests + rubric/idea/S1 docs.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (checker/docs only — no runtime/deploy/data step)
- **⚑ Self-initiated:** yes — empty-fire dispatch; built the S1-named ▶ Next offline guard (grounded in
  the live queue + the captured idea) → shipped without a dispatch/owner ask (Q-0172). Tooling guard,
  free to ship per CLAUDE.md.
- **↪ Next:** S1 ▶ Next offline-startable now = **feature-completion assessments** (assess the remaining
  unassessed games — Mining [big read], Casino, Creatures — one cert each under
  `planning/feature-completion/units/`), or the next fishing offline successor (a rare *material* feeding
  a new craft target, or the rod-ladder recipe-browser UI). All pure + self-mergeable.

## 💡 Session idea (Q-0089)

**Graduate the `no_dead_end` guard from warn → error once the fleet stays clean for a few sessions,**
and **broaden its scope beyond `views/games|rps|...` to all interactive views** — the trapped-view
class isn't unique to games (a settings wizard or a paginator can dead-end too). The guard is built
conservatively today (game dirs, warn-tier) precisely so it can graduate; capturing the graduation
path now means a later session doesn't have to re-derive the heuristic's safety record. (Genuine new
idea, not filler — it's the natural lifecycle of a warn-tier guard per the `baseview_inheritance`
precedent, which is still warn-tier.) → route to `docs/ideas/` if a later session picks it up.

## ⟲ Previous-session review (Q-0102)

The previous run (#1518, the fishing "pearl" drop) was clean, well-scoped, and correctly self-merged —
and notably its own Q-0102 note already articulated the right lesson ("a ▶ Next pointer should name the
*not-yet-built* successor, not the just-shipped feature") and then *honoured it* by leaving a genuinely
not-yet-built handoff. That handoff is exactly why this run could start instantly. **One improvement to
the system it surfaces:** the S1 ▶ Next block now carries *two* parallel offline tracks (feature-completion
assessments **and** the fishing craft-successor chain), and an empty-fire dispatch has to read the whole
block to pick. A tiny win would be a single explicit "**pick this next**" pointer at the top of the S1 ▶
Next list (the dispatch-menu already resolves *a* pick, but the sector file itself buries it) — so the
human-readable handoff and the machine `dispatch_menu --unattended` pick never diverge. Captured as a
candidate, not built (the dispatch_menu resolver already covers the machine half).

## Doc audit (Q-0104)

`check_current_state_ledger --strict` not newly affected (no merged-PR ledger change this run — #1529
is this session's own PR, reconciled at merge by convention). New tooling reachable: the guard is
documented in the rubric + the idea file + the S1 sector. No owner decisions to route. No drift spotted.
