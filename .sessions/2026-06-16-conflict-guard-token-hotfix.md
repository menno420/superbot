# 2026-06-16 — hotfix: pr-conflict-guard token + bash-errexit safety

> **Status:** `complete` — hotfix, shipped in one push; PR auto-merges on green.

## Arc

PR #965 merged the two PR-mergeability-keeper workflows, but the `flag-conflicts` job **failed on its
own PR** (dogfooding caught it) — and because that check is non-required, #965 merged anyway, putting
the **broken `pr-conflict-guard.yml` live on main**. Root cause from the job log: GitHub runs `run:`
steps with `bash -e`, and `gh api POST /statuses/...` was failing — `ROUTINE_PAT` is scoped for
Issues/PRs/Contents but **not `statuses: write`**, so the post 403'd and the errexit shell killed the
step.

## Fix (this PR)

- **Token:** `pr-conflict-guard` now uses the default **`GITHUB_TOKEN`** (which the workflow's
  `permissions: statuses: write` block grants), not `ROUTINE_PAT`. The guard posts no main commits, so
  it needs no PAT attribution. (`pr-auto-update` keeps `ROUTINE_PAT` — it needs Contents+PR write for
  `update-branch` and PAT attribution for the cadence; that scope it does have.)
- **Errexit safety:** capture the PR list first (`|| true`), guard each status post with `if/else`
  (warn, don't die), and `exit 0` — a non-required *visibility* job must never red-flag a PR on a
  single post hiccup.
- Doc: corrected the `autonomous-routines.md` token line (it wrongly said both use `ROUTINE_PAT`).

## Context delta

- **Discovered by hand:** (1) GitHub Actions `run:` defaults to `bash -e`, so `set -uo pipefail`
  leaves errexit ON — an unguarded failing command kills the step. (2) `ROUTINE_PAT` ≠ all-scopes:
  it lacks commit-status write. Both now documented at the call sites + the routines doc.
- **Decision made alone:** ship as a fast hotfix PR (the broken workflow is live on main and
  red-noises other PRs) rather than waiting — bugs-first, and I introduced it.
- **Flagged:** still UNVERIFIED end-to-end until a real DIRTY PR shows the red status; but the
  token+errexit fix addresses the exact observed 403/exit-1.

## 📤 Run report

- **Did:** fixed the `pr-conflict-guard` workflow (wrong token + errexit) that #965 shipped broken to
  main · **Outcome:** shipped (auto-merges on green)
- **Shipped:** this PR — `pr-conflict-guard.yml` token→GITHUB_TOKEN + hardened; doc correction
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none` (GITHUB_TOKEN has the needed scope via the workflow permissions
  block; nothing to configure)
- **↪ Next:** watch the first real behind/conflict case to confirm both keepers fire correctly.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 2 (#959, #965; this hotfix auto-merges on green) |
| CI-red rounds | 1 real (the #965 `flag-conflicts` dogfood failure — root-caused from the job log + fixed here) |
| Repo-rule trips | 0 |
| New ideas contributed | 0 this hotfix (1 already this session) |
| Ideas groomed | 0 this hotfix |
