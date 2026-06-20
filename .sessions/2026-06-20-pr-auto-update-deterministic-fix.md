# 2026-06-20 — pr-auto-update: deterministic behind-detection (same async race as the conflict guard)

> **Status:** `complete`

## Arc

Follow-on to the conflict-guard fix (#1187). The owner asked whether a session-start "branch behind
main" warning would help the parallel-session case — it wouldn't (point-in-time, can't see a
conflict another session introduces after start). That pointed at the workflow that's *supposed* to
handle the parallel case proactively: `pr-auto-update.yml`. Owner: *"verify it works... and implement
any improvements, but don't just assume — back up claims with evidence or logic."*

## Root cause (evidence-backed)

`pr-auto-update.yml` selected PRs with `mergeStateStatus == "BEHIND"` — GitHub's **asynchronously
computed** mergeability field. Evidence it's broken:

1. **In-repo documented behavior:** `pr-conflict-guard.yml`'s header records that after `push:main`
   every open PR is briefly `UNKNOWN` (the query triggers recomputation) — the #1104 miss.
2. **Identical structure, zero mitigation:** pr-auto-update uses the *same field* on the *same
   `push:main` trigger* but, unlike the (old) conflict-guard, had **no poll/wait** — its `gh pr
   list` was the first action.
3. **Observed timing:** a real run (job `82516312071`, 21:12:47→48) **completed in ~1 second** —
   far faster than GitHub's async mergeability settles. So a PR made freshly-behind by the
   triggering merge is still `UNKNOWN` at query time → fails `== "BEHIND"` → silently skipped → the
   branch sits behind+green (the #959 stall the workflow exists to prevent).

(Honest gap: I did not find a single historical log line showing a *named* behind PR being skipped —
that needs per-instant PR-state history I don't have cheaply — but the mechanism is identical to the
proven conflict-guard race, and #3 makes the skip structurally near-certain whenever a behind PR
exists at trigger time.)

## Fix (this PR)

Compute behind-ness **deterministically with git** instead of reading the async field:
a PR is behind iff **current main is NOT an ancestor of its head** (`git merge-base --is-ancestor`).
No async field, no race — mirrors the #1187 conflict-guard fix.

- Added `actions/checkout` (fetch-depth 0); dropped `mergeStateStatus` from the `gh pr list` query.
- Per PR: fetch `refs/pull/N/head`; if main is an ancestor → up to date, skip; else → `update-branch`
  (succeeds only on a clean merge; a real conflict fails and is left to pr-conflict-guard).
- Kept everything else: `push:main` trigger, claude/* + non-draft + carve-out filters, ROUTINE_PAT.

## Verification

- **Live demonstration of the deterministic test:** when #1187 merged mid-session, `origin/main`
  moved to `592a1ad` and this branch's HEAD immediately tested `is-ancestor=FALSE` → correctly
  "behind"; a current branch tests TRUE → "up to date". So the test flags a branch the instant main
  moves — exactly the parallel case, with no async dependency.
- YAML parses; `bash -n` clean on the embedded run script.

## Shipped (PR #1188)

- `.github/workflows/pr-auto-update.yml` — behind-detection rewritten from async
  `mergeStateStatus == "BEHIND"` to deterministic `git merge-base --is-ancestor`; added
  `actions/checkout`. Reliably brings freshly-behind claude/* PRs forward when main moves.

## The two-layer parallel-session story (now both deterministic)

| Layer | Workflow | Trigger | Was (async, flaky) | Now (deterministic) |
|---|---|---|---|---|
| **Prevent** (bring behind branches forward) | `pr-auto-update.yml` | `push:main` | `mergeStateStatus == BEHIND` | `git merge-base --is-ancestor` (#1188) |
| **Detect** (flag true conflicts red) | `pr-conflict-guard.yml` | `push:main` · `pull_request` | `mergeStateStatus` poll (30s cap) | `git merge-tree --write-tree` (#1187) |

A parallel merge now: auto-update walks behind PRs forward (clean ones re-test → auto-merge);
genuinely-conflicting ones fail update-branch and conflict-guard turns them red. Neither depends on
GitHub's async mergeability anymore.

## Decisions made alone

- Attempt `update-branch` on any not-up-to-date PR and let the API reject conflicts (failure →
  conflict-guard flags), rather than pre-classifying clean-vs-conflict with an extra `merge-tree`.
  Simpler, one fewer git op; the only cost is a harmless 422 + warning on a conflicting PR, which
  conflict-guard already surfaces. Reversible.

## Flagged for maintainer

- **UNVERIFIED until the next real BEHIND PR** confirms it auto-updates within seconds of a main
  push (Q-0105 note is in the workflow header). Detection logic is proven locally + by the live
  is-ancestor demo, but the full path (checkout → fetch head → update-branch via ROUTINE_PAT) only
  exercises on a live behind PR.

## 💡 Session idea (Q-0089)

**Grep the rest of `.github/workflows/` for `mergeStateStatus` / `.mergeable` and convert every
remaining consumer to the git-deterministic pattern (or document why async is acceptable there).**
This async field has now caused the same flake in **two** workflows (conflict-guard, auto-update);
treating it as a known-hazardous API and sweeping for other uses would pre-empt the third instance
instead of waiting for it to bite. Pairs with the #1187 idea (a temp-repo smoke test for
workflow-logic) — together they'd make the meta-workflow guards regression-proof. Lane = tooling.
(Captured, not built — a quick grep this run found only these two as live consumers; a dedicated
sweep + a shared `scripts/gh_merge_state.sh` helper would be the durable form.)

## ⟲ Previous-session review (Q-0102)

The #1187 conflict-guard fix was correct, but it **stopped one layer short**: it fixed *detection*
of conflicts while leaving the *prevention* workflow (auto-update) sitting on the identical async
bug — so a behind-but-clean PR would still rot green, just without a red flag (because it's not a
conflict, conflict-guard correctly says nothing). The owner's "would session-start help in parallel?"
question is what surfaced the second half. **Lesson:** when you root-cause a shared failure mode
(here: trusting `mergeStateStatus` on `push:main`), immediately grep for *every* place that pattern
lives rather than fixing the one instance in front of you — which is exactly this session's Q-0089
idea. **System improvement:** that "fix the class, not the instance" check belongs as a habit at the
end of any bug fix; the Q-0089 sweep idea operationalizes it for this specific hazard.

## 📤 Run report

- **Did:** found + fixed the same async race in pr-auto-update (the prevention half of the
  parallel-session loop) · **Outcome:** shipped
- **Shipped:** #1188 — `pr-auto-update.yml` deterministic behind-detection
- **Run type:** `manual · owner-directed bug fix (bugs-first, evidence-required)`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** verify auto-update fires on the next real BEHIND PR (UNVERIFIED)
- **⚑ Self-initiated:** none (owner directed: verify + improve with evidence)
- **↪ Next:** the Q-0089 sweep (other `mergeStateStatus` consumers) + the #1187 workflow-logic
  smoke-test harness would close the class for good; both captured, neither built.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs this session-step | 1 (#1188, CI-config fix, auto-merge on green) |
| Runtime (`disbot/`) code changed | 0 |
| Root cause | async `mergeStateStatus == BEHIND` on push:main (no wait) → deterministic git ancestry |
| Files changed | 1 (`.github/workflows/pr-auto-update.yml`) |
| Evidence gathered | in-repo #1104 doc · ~1s run-time from job 82516312071 · live is-ancestor demo |
| Local validation | YAML + `bash -n` + is-ancestor TRUE/FALSE cases |
| CI-red rounds | 1 (by-design born-red session gate only) |
| New ideas contributed | 1 (sweep all `mergeStateStatus` workflow consumers) |
