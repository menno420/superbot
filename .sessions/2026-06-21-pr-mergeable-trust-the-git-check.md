# Session — PR mergeability: trust the git check, not GitHub's `mergeable_state` (2026-06-21)

> **Status:** `complete`

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

## Verification

- `python3.10 scripts/check_pr_mergeable.py --strict` → reports CLEAN/CURRENT vs origin/main, exit 0
- `python3.10 -m pytest tests/unit/scripts/test_check_pr_mergeable.py` → 3 passed (+ git_merge_state 5)
- `python3.10 scripts/check_quality.py --check-only` → All checks passed ✓
- `pr-conflict-guard.yml` YAML re-validated; cron `*/30 * * * *`

## ⚑ Self-initiated

Owner-directed investigation ("why didn't the dirty-guard catch #1256"); the three deliverables are
the fix the owner greenlit ("any improvements are always welcome"). Promoted under Q-0172.

## 💡 Session idea

**A divergence guard: GitHub `mergeable_state` vs git ground truth.** This session proved GitHub can
report `dirty` while git merges clean. A tiny check (CI or local) that fetches GitHub's
`mergeable_state` for an open PR and compares it to `git_merge_state.py`'s verdict, warning when they
**disagree**, would turn "GitHub is lying again" from a per-session rediscovery into a named signal —
and would have flagged the #1256 false-dirty automatically. Pairs with `check_pr_mergeable.py` (which
gives the git truth); this measures GitHub's *unreliability* directly. (Dedup-checked `docs/ideas/` —
not present.)

## ⟲ Previous-session review

The previous session (repo-state-review-cleanup, #1256) delivered solid cleanups but caused this whole
detour twice: (1) it pushed before running `check_plan_homing.py`, so the homing regression only
surfaced in CI; (2) it trusted GitHub's `mergeable_state: dirty` and did a (harmless but unnecessary)
merge to "resolve" a conflict that git proves never existed. **Both are the same root lesson: verify
with the deterministic local tool, don't trust a remote/async signal.** The durable improvement is
this session's `check_pr_mergeable.py` + the journal entry; the system-level fix worth doing next is
folding `check_plan_homing` + `check_pr_mergeable` into the standard pre-PR sweep so neither gap can
recur silently.

## Documentation audit (Q-0104)

`check_current_state_ledger --strict` green; `check_docs --strict` green. No new owner *decision* to
route (this is owner-directed tooling under existing Q-0105/Q-0154/Q-0172). Journal updated; the
divergence-guard idea is captured above (not yet an idea file — small, may fold into the pre-PR sweep).
