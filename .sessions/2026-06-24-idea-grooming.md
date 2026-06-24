# Session — 2026-06-24 · idea grooming (settle-once run, slice 3)

> **Status:** `complete` — docs-only. Two ideas promoted into `docs/ideas/` + indexed. The standing
> grooming/idea-ender (Q-0015 / Q-0089) for this dispatch run, after the two-PR settle-once arc
> (#1444/#1445) merged. PR for this slice.

**Trigger:** continuation of the settle-once dispatch run. With the main correctness arc shipped and
merged, capacity remained, so I executed the standing **backlog-grooming + new-idea enders** as a small
contained slice rather than leaving them only as session-log flags.

## What shipped

- **`docs/ideas/askuserquestion-preview-for-design-forks-2026-06-24.md`** — *grooming move* (Q-0015):
  rescued the `AskUserQuestion` per-option `preview` idea out of `.sessions/2026-06-24-setup-log-channel-rework.md`,
  where it was stranded (a strong idea a session log can't surface to grooming). It proposes rendering a
  mockup of each option's resulting UX for design/UX forks — motivated by the same-day #1429→#1432 setup
  rework.
- **`docs/ideas/settle-once-architecture-guard-2026-06-24.md`** — *new idea* (Q-0089): a
  `check_architecture` rule flagging a game view/state object whose settlement path is reachable from >1
  trigger but doesn't adopt `SettleOnceMixin` — the CI ratchet form of the by-hand double-settle hunt
  this run did across four views.
- Both indexed in `docs/ideas/README.md` (the 2026-06-24 block). Dedup-checked before writing — neither
  existed.

## ✅ Verification

`check_docs --strict` green (both new files reachable from the README index). Docs-only — no `disbot/`
code, no test impact.

## 💡 Session idea (Q-0089)

Covered by the deliverable itself: the **settle-once architecture guard** is this session's new idea
(now a backlog file, not just a log flag — which is exactly the anti-stranding behaviour the *other*
promoted idea is about). Meta-note worth keeping: this slice is the answer to its own
previous-session-review finding — *don't let a good idea die in the log it was born in* — applied in the
same run that surfaced it.

## ⟲ Previous-session review (Q-0102)

Previous: this run's **slice 2** (`2026-06-24-blackjack-settle-once.md`, PR #1445). **Did well:** caught
the `services → views` layering trap *before* writing code and relocated the mixin to `utils/` at the
root (helper-policy-correct), rather than hacking a local flag onto `_PvPState` — and named the residual
(blackjack tournament) instead of silently skipping it. **Missed:** nothing in the slice itself; its own
review already nailed the real lesson (choose a shared primitive's home by its *eventual* adopter set,
not the first one). **System improvement this run as a whole surfaced:** strong session ideas kept
needing rescue from logs across all three slices — the durable fix is the grooming discipline I just
executed *plus* the standing reminder that an idea worth having is worth a `docs/ideas/` file the same
session, not a log line a later grooming pass has to find. (No rule change proposed — Q-0089/Q-0015
already mandate this; the gap was execution, which this slice closes.)

## 📋 Doc audit (Q-0104)

Two new idea files + index entries; `check_docs --strict` green. No `current-state.md` ledger entry (the
ledger keys off merged code PRs; an idea-grooming docs PR is picked up by the next reconciliation pass).
No owner decision. No binding-doc change.

## 📤 Run report

- **Run type:** routine · dispatch
- **What shipped this slice:** a docs-only idea-grooming PR — 2 ideas promoted into `docs/ideas/` +
  indexed. (This dispatch run also shipped #1444 + #1445, the settle-once correctness arc.)
- **⚑ Self-initiated:** yes — the standing grooming + new-idea enders (Q-0015 / Q-0089), no dispatch/owner
  ask. Docs-only, fully reversible.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
- **Bug-book:** unchanged.
- **Remarks:** end of this dispatch run — three slices total (#1444 correctness, #1445 correctness, this
  docs grooming). Handing off at a clean boundary; the next dispatch's startable work is the unchanged S1
  queue (Project Moon runtime PR 1 · botsite React migration PR 2) per `current-state/S1-bot.md`.
