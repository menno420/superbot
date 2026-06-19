# 2026-06-19 — Fix the pr-conflict-guard UNKNOWN-mergeability race

> **Status:** `complete`

## Arc

Follow-on bug fix from the website-split session (#1104). The owner asked why the conflict guard
(`pr-conflict-guard.yml`, Q-0154) didn't turn #1104 red when it became conflicted. Root-caused it from
the guard's own job log and fixed the race.

## Root cause (proven, not theorized)

When #1105 merged to `main` (12:34), the guard's `push: main` sweep ran **4 seconds later** and logged:

```
#1104 mergeability not computed yet -> skip
#1074 CLEAN -> success
```

GitHub computes a PR's mergeability **asynchronously** — the instant `main` moves, every open PR's merge
state is invalidated to `UNKNOWN` until GitHub recomputes it (a *query* is what triggers the compute). The
guard's only real-time "main moved" trigger is `push: main`, which fires seconds after the merge — so it
queried #1104, saw `UNKNOWN`, hit its `UNKNOWN|"") -> skip` branch, and **never posted the red status**.
`#1074` was correct only because its mergeability was already cached (it hadn't just changed).

Backstops couldn't save it: the `pull_request` trigger can't run on a conflicted PR (no merge ref — same
reason Code Quality didn't run), and the `schedule` is every 3h while the conflict was resolved in ~5 min.
So it's a **latent timing race**, not a regression — it "worked" before only when a dirty PR sat long
enough for a later sweep/schedule to re-check it after mergeability settled.

## Fix (`pr-conflict-guard.yml`)

Added a `resolve_state()` poller: when a PR reports `UNKNOWN`, re-query `gh pr view ... mergeStateStatus`
up to 10× at 3s intervals (≤30s) until it settles, instead of skipping. Applied in both the `push`/
`schedule` sweep (per-PR) and the `pull_request` path. `post()` is unchanged — a still-`UNKNOWN` PR after
30s still skips (fail-safe; never false-flags). Non-required visibility status, so the change can't break
merges. Header provenance updated; YAML validated.

## Context delta

- The compounding insight for the agent network: a **conflicted PR runs *no* `pull_request` workflows**
  (GitHub needs a merge ref), so any conflict check must live on `push: main` / `schedule` — and on
  `push: main` it MUST poll through the async-mergeability `UNKNOWN` window or it misses the common case.
- This pairs with the website-split session's lesson: when CI doesn't start on a PR, check
  `mergeable_state` **first** (a `dirty` PR silently blocks `pull_request` CI) before theorizing about
  token/trigger issues.

## Verification

- `python3.10 -c "import yaml; yaml.safe_load(open('.github/workflows/pr-conflict-guard.yml'))"` → OK.
- Full runtime verification needs the next real DIRTY PR to confirm the red `conflict-guard` status now
  appears within ~30s of the conflicting merge (noted in the workflow header; the guard stays Q-0105
  "unverified / disposable" until then).

## 📤 Run report

- **Did:** root-caused (from the guard's job log) why `pr-conflict-guard` didn't flag #1104 red, and fixed
  the async-mergeability `UNKNOWN`-skip race with a bounded poll. · **Outcome:** shipped.
- **Run type:** `manual` (owner question → discovered bug → fix).
- **⚑ Self-initiated:** the fix — a contained, reversible bug fix to a non-required visibility workflow,
  acted on per "bugs first / act on contained reversible fixes." Flagged here for review.
- **↪ Next:** confirm on the next real conflicted PR that the red status appears; otherwise none.
