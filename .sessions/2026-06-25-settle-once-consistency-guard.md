# 2026-06-25 — settle-once money-safety CI guard (check_consistency Rule 6)

> **Status:** `complete`
> **Run type:** routine · dispatch
> **Branch:** `claude/funny-franklin-ry0ygk` · **PR:** #1454

## What I did

Scheduled dispatch fire, no work order → advance the next plan slice. The survey found the
headline ▶ items across every sector **gated**: Project Moon PR 2 (the AI grounding wiring) and
absence-guard **Layer B** are both deliberately deferred for a **Q-0086 runtime walk** (gated AI
hot path — the previous run's explicit, well-reasoned deferral, which I respected); setup **PR 3b**
needs live-bot verification; BTD6 decode items 3–4 are demand-driven / owner; BUG-0009's remaining
slice is external-data-gated. This matches `current-state.md`'s own "honest caveat." Per **Q-0172**
(idea→plan→ship is open when the queue is thin), I promoted a clean, decided-lane, **fully
offline-verifiable** idea and built it.

**Built — `check_consistency.py` Rule 6 (`settle_once_adoption`), warn-first (PR #1454):**
promotes [`ideas/settle-once-architecture-guard-2026-06-24.md`](../docs/ideas/settle-once-architecture-guard-2026-06-24.md).
A **wager-settling site** — a call to `game_wager_workflow.settle_pvp` / `refund_pvp` (which pay
out / refund the escrowed pot) — must adopt the settle-once guard:

- its **enclosing class** mixes in `SettleOnceMixin` or calls `claim_settlement()` (the RPS PvP
  view shape), **or**
- its **enclosing function** calls `claim_settlement()` (the blackjack module-level `_settle(state)`
  shape, where the claim is `state.claim_settlement()`).

A settle site with neither is flagged — the BUG-0013 double-settlement footgun (a finishing button
*and* `on_timeout`, or two players' callbacks, racing into a second payout). It **mechanizes the
by-hand review** that found BUG-0013 + three more sites (the `SettleOnceMixin` adopters, #1444/#1445)
for a **money-safety class**.

Conservative on purpose (the idea's prescribed posture): the **money leg only** (`settle_pvp` /
`refund_pvp`). The fuzzier "posts a terminal result reachable from `on_timeout`" leg is deferred —
too false-positive-prone for a warn-clean rule. **Warn-first** (`severity="warning"`) so it **cannot
redden CI** (`--mode strict` only fails on `error` findings); graduates to `error` once it soaks
clean a few sessions. Scopes `views/` + `services/` (a state object like `blackjack_state._PvPState`
lives in `services/`); `game_wager_workflow` only *defines* the helpers (never calls them) so it is
never matched.

Also fixed **roadmap drift on sight** (Q-0166): the S1 `Now` line listed `▶ games P0-1 wager
money-safety` as a startable item, but P0-1 **shipped #748** — corrected to mark it ✅ #748 plus the
settle-once guard layer (#1444/#1445 + #1454).

## Verification

- `python3.10 scripts/check_consistency.py --graduation` → `settle_once_adoption  [warning]
  findings=0 → ELIGIBLE` (runs clean: both wager-settle callers already adopt the guard).
- `python3.10 -m pytest tests/unit/scripts/test_check_consistency.py -q` → **64 passed** (11 new
  Rule-6 tests: unguarded-flag · class-mixin-clean · sibling-claim-clean · module-fn-clean ·
  refund_pvp · definition-only-out-of-scope · services-scope · allowlist · registry · live-tree-clean).
- `python3.10 scripts/check_quality.py --check-only` → **All checks passed** (incl. `check_consistency`
  strict + `check_docs`).
- `python3.10 scripts/check_current_state_ledger.py --strict` → exit 0 (benign newest-merge lag only).

No `disbot/` runtime touched (a script + its test + docs), so mypy/runtime are unaffected.

## Handoff (the continuation is current-state ▶ Next action)

The unattended-clean queue is thin right now — the high-value next slices are **owner-attended**:

- **Project Moon PR 2** — `AITask.PROJMOON_ANSWER` + a thin `projmoon_context_service` + route on
  `has_limbus_context` into `core/runtime/ai/natural_language_stage.py`, reusing the BTD6
  tag/cap/provenance render + the faithfulness guard. **Wants a Q-0086 runtime walk** — prose-grounding
  faithfulness is the plan's "hardest correctness risk" and shouldn't ship unverified. House anchors in
  [`planning/project-moon-knowledge-domain-plan-2026-06-21.md`](../docs/planning/project-moon-knowledge-domain-plan-2026-06-21.md) §5/§8.
- **Setup PR 3b** (rework the Advanced draft→Final-Review editor, Q-E) — heavier, needs live-bot verification.
- **Absence-guard Layer B** — design-for-review, needs prod creds.

**Clean unattended next:** graduate `card_engine_helper_duplication` (added #1396, 2026-06-24) and
this `settle_once_adoption` rule to `error` once each has soaked clean a couple more sessions (check
`check_consistency.py --graduation`); then wire into `code-quality.yml`. Or the next BTD6 offline
grounding-floor addition.

## 💡 Session idea (Q-0089)

**A `--graduation --json` mode + a "soak counter" for `check_consistency.py`.** Today a rule's
graduation gate is "stay clean a couple more sessions," but *how many sessions it has been clean* is
tracked only in human memory / the registry comment. A tiny soak-counter (the rule records the PR
number it was added at; `--graduation` prints `clean for N merges since #added`) turns "has it soaked
enough?" from a judgment call into a number — and `--json` lets the dispatch/reconciliation routine
auto-surface ELIGIBLE-and-soaked rules as a ready-to-graduate nudge. Genuinely useful: it closes the
loop on the warn-first→error lifecycle the linter already models but currently leaves to memory.
Dedup-greped `docs/ideas/` — adjacent is the `--graduation` tracker itself (#1060, already built) and
`success-metric-alignment-*`; no soak-counter idea exists. *(Captured here; not filed as a separate
idea doc — small, lives in this log per the Q-0089 "substantial ones get a file" bar.)*

## ⟲ Previous-session review (Q-0102)

The previous run (Project Moon Limbus PR 1, #1453) did the **scoping** exactly right: it shipped a
safe, fully-offline vertical (committed *patch-stable* structural data only) and **deliberately
deferred** the fragile exact-number ingest *and* the AI-hot-path grounding wiring to a Q-0086 runtime
walk — naming the deferral in both the session log and the plan's progress note. That clean,
explicit handoff is precisely why this run could orient fast and respect the boundary rather than
re-deriving it. One thing it could improve: it left the continuation only in its own log + the plan's
inline note, not in the S1 `current-state` ▶ startable as a *gated* tag — so a scheduled unattended
fire reads "Project Moon PR 2" as startable when it actually needs the owner. **System improvement
this surfaces:** the per-sector ▶ startable lists should carry the same `▶/⛔/👤` gate tags the
roadmap `Now` lines already use, so a *gated* next-slice is visibly gated at the dispatch-resolution
point — not just in prose a routine has to read closely. (I applied the spirit of this in my handoff
above by tagging each next slice with its gate; promoting that to a convention on the S-files is the
durable fix — a candidate for the S3/S4 sector-map tooling.)

## 📋 Doc audit (Q-0104)

`check_current_state_ledger --strict` exit 0 (benign lag), `check_docs --strict` clean. New work is
recorded in its durable homes: the idea doc carries a **Built** banner (PR #1454), the roadmap drift
is fixed, the rule's provenance + reliability + graduation posture live in the registry comment +
docstring (Q-0105 convention). No owner decision was made (the rule promotion is self-initiated per
the standing Q-0172 lane, not a new decision), so the question router needs no entry. PR #1454 is a
benign newer-than-marker merge the next reconciliation pass will record.

## 📤 Run report

- **Did:** built a warn-first money-safety CI guard (settle-once adoption) mechanizing the by-hand
  double-settlement review · **Outcome:** shipped
- **Shipped:** #1454 — `check_consistency.py` Rule 6 `settle_once_adoption` + 11 tests + idea-built
  banner + roadmap drift fix
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** promoted `ideas/settle-once-architecture-guard-2026-06-24.md` → built as
  `check_consistency.py` Rule 6 (no dispatch/owner ask; Q-0172 lane)
- **↪ Next:** the high-value slices (Project Moon PR 2 · setup PR 3b · absence-guard Layer B) are
  owner-attended (Q-0086 runtime walk / live-bot / prod creds); clean unattended next = graduate the
  two warn-first consistency rules once soaked, or the next BTD6 offline grounding-floor addition.
