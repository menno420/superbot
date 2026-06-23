# Idea — `check_worker_pr_scope.py` (ultracode coordinator scope guard)

> **Status:** `ideas` — capture only, not approval, not a plan. Source + binding contracts win.
> **Subsystem:** none (cross-cutting — agent workflow / ultracode tooling).

## Provenance

Surfaced by the **2026-06-23 ultracode consolidation fleet** (coordinator PR #1375). The fleet's safety
property is that workers are **file-disjoint** — two agents never edit the same file (the one rule in
`docs/ultracode/`). In Phase 2 the coordinator verified that property *by hand* on all 4 worker PRs
(`git diff --stat` against each unit's declared ALLOWED globs). That manual check is exactly the kind of
load-bearing review that should be mechanized.

## The idea

A small `scripts/check_worker_pr_scope.py`:

- **Input:** a PR number (or a branch + base) **and** the unit's declared ALLOWED file globs (from the
  filled-in `docs/ultracode/worker-scope-template.md`).
- **Check:** every path in the PR diff matches at least one ALLOWED glob; exit nonzero (listing the
  leaked paths) on any file outside the set. Optionally also assert none of the held-set files (map § 4)
  are touched.
- **Use:** the coordinator runs it once per worker PR in Phase 2 instead of eyeballing `git diff --stat`.

## Why it's worth having

- Turns the "diff touches only allowed files" review (done 4× manually this session) into one command —
  the file-disjoint guarantee becomes **un-missable**, not dependent on coordinator attention.
- Catches a worker that quietly widened its scope (the failure mode that breaks parallel safety and
  causes merge-time conflicts) *before* merge, with a precise punch list.
- Pairs naturally with the existing `check_lane_overlap.py` (pre-dispatch overlap) — this is the
  **post-work** half of the same discipline.

## Notes / open questions

- The ALLOWED globs are currently free-text in the worker prompt; a machine-checkable form would want them
  in a small structured block (YAML front-matter on the worker's claim file, or a `--allow` arg list).
- Disposable per the Q-0105 kill-switch convention if it proves noisy across a few ultracode runs.
