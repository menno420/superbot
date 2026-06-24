# 2026-06-24 — Route `!syncslash global` through the diff-gated auto-sync helper

> **Status:** `complete`

## Goal (dispatch run, self-initiated idea→ship promotion, Q-0172)

Empty scheduled fire → advance a real plan slice. Promoted the **previous
session's Q-0089 session idea** (`.sessions/2026-06-24-command-tree-auto-sync.md`),
which survives the sniff test: **route the manual `!syncslash global` through the
new diff-gated `command_tree_sync.auto_sync_if_changed`** instead of an
unconditional `tree.sync()`.

## What shipped (PR #1426)

**Slice 1 — gated `!syncslash global` (runtime + tests).**
- `!syncslash global` now flows through `command_tree_sync.auto_sync_if_changed`
  (the same helper the #1424 startup auto-sync uses): fetch live global commands,
  diff command *paths* vs the local tree, and only `tree.sync()` when they differ.
  Reports the `+N added / -M removed` diff (with a short path preview) or a clean
  "already in sync — nothing to do".
- New **`force`** modifier (`!syncslash global force`) → the old unconditional
  `tree.sync()`, for parameter/description-only edits the conservative path-diff
  deliberately misses. This **retires the last unconditional global sync** — one
  implementation, one place to reason about Discord's global-sync rate limit.
- The `guild` / `clear` scopes (guild-local `copy_global_to` / `clear`) are
  unrelated and untouched.
- **Decomposition:** extracted the global-sync logic + operator-message rendering
  to `cogs/admin/_slash_sync.py` (`run_global_sync` / `format_sync_diff`), matching
  the `cog_manager.py` pattern, to keep `admin_cog.py` under the S4.6 800-LOC
  ceiling (the cog was already at ~787 LOC; inlining would have broken the
  `test_cog_size_under_fail_threshold` invariant — caught locally, fixed at the
  root rather than bumping the ceiling). Cog now 788 LOC.

**Slice 2 — operator docs.** `docs/operations/production-deployment.md` "How code
reaches production" now documents that **slash-command propagation is automatic**
(#1424) — no manual `!syncslash` post-deploy — with the gated manual command +
`force` escape as the backstop. (Outside the active docs-reconciliation claim's
scope: that claim covers `current-state*.md` + `planning/` + `ideas/` + dashboard.)

## Status checklist
- [x] `cogs/admin/_slash_sync.py` — gated `run_global_sync` + `format_sync_diff`
- [x] `admin_cog.sync_slash_commands` — `force` modifier, thin call, under 800 LOC
- [x] Tests (23): both branches + every SyncOutcome reason (synced/unchanged/
      fetch_failed/sync_failed) + the `force` unconditional path + its HTTP failure
- [x] `docs/operations/production-deployment.md` auto-sync note
- [x] `check_quality --full` green (12441 passed) + arch strict (0 errors) + lint/docs
- [x] Flip card → auto-merge

## Handoff / continuation (next dispatch)
This slice is **self-contained and complete** — no remaining sub-step. The active
queue is unchanged; pick the next S1 ▶ startable item (current-state/S1-bot.md):
Project Moon runtime PR 1, botsite React-SPA migration PR 2, or the visual
card-engine H3 tail (rank/profile hub panels reached via Help). Note: the
setup-wizard spine (PR #1425) merged this session; its remaining spine steps
(block spam · log channel · rewards · help desk · server-type preset) are
turn-key follow-ons on the `essential_setup.py` pattern.

## 💡 Session idea (Q-0089)
**A `!slashes diff` subcommand (read-only) that prints the live-vs-local command
path delta without syncing.** The gated `auto_sync_if_changed` already computes
`added`/`removed`; a pure read-only diff view (no `tree.sync()`) would let an
operator *see* whether a deploy propagated correctly before deciding to `force`,
and would make the "is the tree in sync?" question answerable without the
side-effect-bearing `!syncslash`. Small — it reuses `_local_paths`/`_remote_paths`
+ `format_sync_diff`. Worth an idea file if it survives next session's sniff test.

## ⟲ Previous-session review (Q-0102)
Previous in-chain: #1424 (startup command-tree auto-sync). **Did well:** it
shipped the diff-gated helper *and* flagged the manual-sync unification as a clean
Q-0089 idea — which is exactly why this session could pick it up turn-key (the
idea→ship loop working as designed). **Could improve:** #1424 left the manual
`!syncslash global` doing an unconditional `tree.sync()` while introducing a gated
helper right next to it — a one-session inconsistency where the obviously-better
shape was already in hand. **System improvement:** when a PR introduces a "safe"
helper that an *existing* command duplicates unsafely, prefer routing the existing
command through it **in the same PR** when it's small (this was ~60 LOC) — the
"capture as an idea for next session" path is correct for bigger lifts, but a tiny
adjacent unification is cheaper to finish than to hand off. (Counter-weight: the
born-red/claim machinery makes a same-session follow-up cheap, so this is a soft
preference, not a rule.)

## 📝 Doc audit (Q-0104)
- `check_quality --full` green; `check_architecture --mode strict` 0 errors.
- The auto-sync/`force` behaviour is documented in two durable homes: the
  `_slash_sync.py` module docstring + `docs/operations/production-deployment.md`.
- Owner decision: none — this is a self-initiated idea→ship promotion (Q-0172),
  flagged below; no new router Q.
- Ledger: PR #1426 in-flight; `current-state.md` is under the active
  `claude-jolly-johnson` reconciliation claim, so this session does not edit it
  (its next pass records #1425/#1426). `check_current_state_ledger --strict` shows
  only benign newest-merge lag.

## 📤 Run report
- **Run type:** routine · dispatch
- **What:** gated `!syncslash global` (diff-aware, + `force` escape) + the
  auto-sync deployment-doc note; PR #1426.
- **⚑ Self-initiated (Q-0172):** promoted the previous run's Q-0089 idea
  (manual-sync unification) to a build with no dispatch/owner ask — reversible,
  flagged for owner review.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none
