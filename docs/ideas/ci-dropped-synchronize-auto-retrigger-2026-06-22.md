# Idea: auto-re-trigger Code Quality when GitHub drops the `pull_request: synchronize` event

> **Status:** `ideas` — captured 2026-06-22; **BUILDING same day (PR #1288)** — promoted to
> implementation under Q-0172/Q-0195. Class: CI / control-plane reliability. Root-cause guard.
> **Subsystem:** none — agent-workflow/CI, not a bot subsystem (explicit tag stops the slug heuristic
> cross-matching a bot subsystem; see `idea-subsystem-tag-on-ideas-2026-06-19.md`).
> **Owner-endorsed** in-session (2026-06-22): "Yes that's a good idea." Promotable to a plan/build
> at any time (Q-0172).
> Provenance: surfaced live while diagnosing PR #1283 sitting `mergeable_state: blocked` with the
> required **Code Quality** check stuck "waiting".

## The problem

On a `claude/*` PR branch, `code-quality.yml` runs **only** via `pull_request: synchronize` — its
`push` trigger is `branches: [main]`-only. The morning of 2026-06-22 fixed the *cancellation* race
(`#1275`, `concurrency: cancel-in-progress: false`). But a **distinct** failure mode remains: GitHub
can **drop the `synchronize` event delivery itself**. Observed on PR #1283 — a push updated the PR
head (the `push`-triggered codex workflow ran on the new SHA), but **no `code-quality` run was ever
created** for that head. The required check then has no result → `mergeable_state: blocked` →
auto-merge waits indefinitely, with nothing red to notice (the failure webhook never fires because no
run failed — there simply is no run).

This is not the cancellation bug and is not fixed by the cancellation fix: it is missing *event
delivery*, not a cancelled run. The manual remedy is to push an empty commit to regenerate the event
— which is exactly the toil this idea automates.

## The proposed guard

A small watcher that detects "PR head has no `code-quality` run N minutes after its last push" and
regenerates the trigger. Two viable mechanisms (pick at plan time):

1. **Scheduled reconciler workflow** (`schedule:` every ~5–10 min, or `workflow_run` after the
   push-triggered job): enumerate open `claude/*` PRs via the API; for each head SHA, check whether a
   `code-quality` check run exists; if absent for > threshold and the PR is non-draft + auto-merge
   armed, **push an empty commit** (or re-request the check) to regenerate `synchronize`. Stdlib /
   `gh`-free REST is already available (`check_loop_health.py` pattern).
2. **A `repository_dispatch` / `workflow_dispatch` re-kick** invoked by the same watcher, if a
   no-op commit is undesirable.

Guard rails: only act on `claude/*` non-draft PRs; cap re-kicks (e.g. ≤ 2 per head) so a genuinely
failing/queued run is never thrashed; skip PRs labelled `do-not-automerge` / `needs-hermes-review`;
log each re-kick. Q-0105 disposable header + "delete if it proves noisy".

## Why it's worth having

This is the **last** strand of the recurring "CI didn't run on my latest commit" problem
(cancellation = fixed #1275; *dropped delivery* = this). It converts a silent indefinite stall — the
worst kind, because no webhook fires — into a self-healing one, removing a manual empty-commit step
the owner and agents keep performing. Pairs with the control-plane health tooling
(`scripts/check_loop_health.py`).

## Routing

Sector **S5** (operations / control-plane) with an **S3** mechanism flavour (it's an in-repo
workflow guard). Relates: `.github/workflows/code-quality.yml` (the `concurrency` comment documents
the cancellation half) · `#1275`/`#1278` (the cancellation fix + the disproven "synchronize doesn't
re-fire" journal claim) · `executor-chain-trigger-via-workflow-2026-06-15.md` (a sibling
event-reliability idea, but for the autonomous-loop trigger, not PR CI).
