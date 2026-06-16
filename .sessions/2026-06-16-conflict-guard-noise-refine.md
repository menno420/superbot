# 2026-06-16 — refine pr-conflict-guard to cut per-PR noise

> **Status:** `complete` — owner-directed refinement; shipped in one push, auto-merges on green.

## Arc

After the conflict-guard hotfix (#966), the owner flagged that the guard — though now green — was
**noisy**: it ran on every PR's push and swept *all* open PRs each time, so every PR got an
unfamiliar `flag-conflicts` run + a `conflict-guard` status, and two parallel sessions (#963, #964)
spent effort investigating a red check that wasn't theirs. Owner chose (via AskUserQuestion) to
**refine to cut the noise**.

## Shipped (this PR)

- **`pr-conflict-guard.yml`** — a PR's **own** push (`pull_request`) now evaluates **only that PR**
  (one `gh pr view` + one status post); the all-PR **sweep** runs only on `push: main` + `schedule`
  (the moments a PR can *newly* become DIRTY because main moved). Same coverage, far less noise.
- Bash refactored into a `post()` helper, branching on `$EVENT`; errexit-safe (guarded, `exit 0`).
- Docs: corrected Q-0154 (real PR refs #965/#966 + this refinement; the conflict-guard token is
  `GITHUB_TOKEN`, not "the same token"; added the dogfooding tail) and the `autonomous-routines.md`
  conflict-guard row (scoped triggers).

**Verified locally** with a `gh` stub (6 cases): pull_request DIRTY→one red / CLEAN→one green /
UNKNOWN→skip-no-post; push sweep mixed states; empty list; and a failing post → warning, RC=0
(non-fatal). Confirms only the triggering PR is touched on its own push.

## Context delta

- **Discovered by hand:** GitHub Actions exposes `$GITHUB_EVENT_NAME` (+ the event payload via
  `${{ github.event.* }}`), so a workflow can cheaply branch "this PR vs sweep all" — the clean way
  to keep a guard's footprint proportional to the trigger.
- **Decision made alone:** kept the guard (refined) rather than removing it — the owner picked
  refine; the red-on-conflict signal stays, just quieter.
- **Flagged:** still UNVERIFIED against a real DIRTY PR end-to-end, but the stub test + the live
  green runs post-#966 cover the mechanics. Cosmetic stale red checks on PRs opened during the
  ~6-min #965 breakage clear on their next push.

## 📤 Run report

- **Did:** refined `pr-conflict-guard` so it only touches the triggering PR on its own push (sweep
  reserved for main-moves/schedule) — kills the cross-session noise · **Outcome:** shipped (auto-merges)
- **Shipped:** this PR — `pr-conflict-guard.yml` scope refinement + Q-0154/routines doc corrections
- **⚑ Owner decisions needed:** `none` (chosen via AskUserQuestion)
- **⚑ Owner manual steps:** `none`
- **↪ Next:** the mergeability keepers are settled; watch the first real behind/conflict case to
  confirm auto-update brings a behind PR forward and a DIRTY PR shows the red `conflict-guard`.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 3 (#959, #965, #966; this refinement auto-merges on green) |
| CI-red rounds | 0 in this PR (the #965 dogfood failure was fixed in #966; logic stub-tested here pre-push) |
| Repo-rule trips | 0 |
| New ideas contributed | 0 this follow-up (1 already this session) |
| Ideas groomed | 0 this follow-up |
