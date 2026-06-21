# Session — PR mergeability: trust the git check, not GitHub's `mergeable_state` (2026-06-21)

> **Status:** `in-progress`

Owner asked why the `dirty`-PR guard didn't fire on #1256, after ~5 sessions hardening it.

**Root-cause finding (diagnosed on #1256):** the conflict-guard was *correct* — `git merge-tree`
(the deterministic helper the #1187/#1191 fix uses) confirms #1256's heads `b21ce9d` and `cacc633`
**both merge CLEANLY** with main, and the `push:main` sweep log shows `#1256 CLEAN -> success`.
GitHub's `mergeable_state: dirty` was a **false/stale report** — a symptom of the same remote-exec
**push-gotcha**: a push to an existing PR branch intermittently fails to register, so (a)
`pull_request`-triggered workflows (Code Quality *and* conflict-guard) skip the new head, and (b)
GitHub leaves its async mergeability stale, sometimes showing a phantom `dirty`. The guard reads
real git and keeps saying CLEAN; **GitHub's signal is the unreliable one** — which is why it looked
intermittent across sessions.

**Fixes this session (owner: "any improvements are always welcome"):**

1. **`scripts/check_pr_mergeable.py`** (+ test) — a one-command, stdlib, git-based check of the
   *current branch vs `origin/main`*, reusing `git_merge_state.py`. Reports CLEAN/DIRTY + behind
   state with no dependence on GitHub firing anything — the truth source an agent can trust.
2. **Journal entry** — GitHub `mergeable_state` is unreliable in this env (false-dirty); trust the
   git check / the `conflict-guard` status; the push-gotcha intermittently disables `pull_request`
   CI. Stops the recurring wild-goose-chase.
3. **`pr-conflict-guard.yml`** — tighten the schedule backstop (3h → 30min) so a *real* conflict
   introduced by a PR-branch push (whose `pull_request` trigger may not fire) is caught quickly,
   since `push:main` only covers the "main moved" case.

No runtime `disbot/` code.
