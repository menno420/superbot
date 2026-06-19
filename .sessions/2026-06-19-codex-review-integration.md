# 2026-06-19 — Codex review integration (routine fix-first + Hermes 6H pr-check skill)

> **Status:** `in-progress`

## Intent (born-red)

Lane B5 of the ultracode fleet (owner-directed, **Q-0174**). Ship the two unbuilt parts of
`docs/planning/codex-review-integration-plan-2026-06-17.md`:

- **Part A** — add a first-priority "check Codex first, verified" step to the **dispatch** and
  **reconciliation** routine prompts: before taking new work, scan the few most-recent merged/open
  PRs for unresolved Codex/bot review comments, apply the plan's "real bug" bar, fix the
  verified-real ones first.
- **Part B** — a new Hermes skill `superbot-pr-check`, self-scheduled every 6H (`0 */6 * * *`),
  that lists open+recent PRs, applies the bar, and **opens a GitHub issue** for each real bug
  (issue-only — NO dispatch/merge authority).

This card flips to `complete` as the deliberate last step (Q-0133).
