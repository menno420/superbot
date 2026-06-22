# 2026-06-22 — CI dropped-`synchronize` auto-re-trigger watchdog

> **Status:** `complete` — owner-endorsed follow-up to the Q-0195 session. Builds the captured
> idea (`docs/ideas/ci-dropped-synchronize-auto-retrigger-2026-06-22.md`): a scheduled watchdog that
> re-kicks `code-quality` when a `claude/*` PR head has **no** run — the *silent* CI stall (GitHub
> drops the `pull_request: synchronize` event → no run → no failure webhook → auto-merge waits
> forever). Owner-directed in-session ("Yes go ahead") → merge on green; no `needs-hermes-review`.

> **Run type:** `manual · owner-directed`

## Why

PR #1283 sat blocked because GitHub dropped the `synchronize` event and `code-quality` never ran on
the head. The cancellation race was already fixed (#1275, `cancel-in-progress: false`); this is the
*distinct* dropped-delivery failure mode. Manual remedy was an empty commit — this automates it.

## What shipped

- **`code-quality.yml`** — added a `workflow_dispatch` trigger (its docs-detector already treats a
  dispatch as "base unavailable → run full CI"), so the watchdog can re-kick it.
- **`.github/workflows/ci-rerun-watchdog.yml`** — schedule (`*/12`) + manual; lists open `claude/*`
  non-draft, non-carved PRs (same scoping as `pr-auto-update.yml`) and dispatches `code-quality` on
  any head with no run past a grace window, via `ROUTINE_PAT` (so the dispatch isn't recursion-guard
  suppressed). Presence-check is a natural cap → no loop.
- **`scripts/check_ci_coverage.py`** (+5 tests) — pure detection (`missing_required_check` /
  `past_grace` / `should_rekick` / `find_uncovered`, injectable fetch), gh-backed I/O, report-only by
  default, `--rekick` dispatches, defensive `--max-rekicks` cap. SKIP-degrades without gh. Q-0105
  disposable header.
- Idea doc → `BUILDING (PR #1288)`; S5 sector live-state note.

**Mechanism choice:** `workflow_dispatch` (not a PAT empty-commit push). It produces a real
`code-quality` check on the branch head that satisfies the required check for a same-repo PR, with no
commit churn. The presence check caps re-kicks structurally.

> **⚑ Self-initiated:** none — owner-endorsed + owner-directed in-session ("Yes go ahead"); merge on
> green, no `needs-hermes-review`.

## ⟲ Previous-session review

The previous session (the Q-0195 state-file restructure, this same chat) did well to make the
decision **simulation-driven** rather than asserted, and to capture the dropped-`synchronize` idea
when it bit us live. What it could have done better: it pushed **three times in quick succession**
(re-trigger → merge → idea), which forced the concurrency queue to serialize ~6-min runs and made the
"is CI stuck?" picture harder to read — batching those (CLAUDE.md's "don't re-push on every commit")
would have been cleaner. **System improvement this surfaces:** the very guard built this session is
the durable fix for the *silent* half of that pain; the *self-inflicted* half (push-batching) is
already a rule, just not enforced — a future lightweight guard could warn when a `claude/*` branch
gets >N pushes within M minutes.

## 💡 Session idea

**Idea — extend `check_ci_coverage.py` to also flag a head whose ONLY checks are stuck `queued` for
> T minutes** (not just *missing* runs). A run that registers but never gets a runner (GitHub
capacity / stuck queue) is a sibling silent-stall the current presence-check treats as "covered." A
follow-up could detect "all required checks queued, none started, head older than T" and re-kick the
same way. Small, reuses the same plumbing. (Dedup-checked `docs/ideas/` — not present; distinct from
the dropped-event case this PR handles.)
