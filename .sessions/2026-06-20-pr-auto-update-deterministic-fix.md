# 2026-06-20 — pr-auto-update: deterministic behind-detection (same async race as the conflict guard)

> **Status:** `in-progress`

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

## Shipped

_(filled at close)_
