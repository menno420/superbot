# 2026-07-05 — CI Phase-A: make the should-gate invariants actually block merges

> **Status:** `complete` — deliberate final flip (born-red gate, Q-0133). All three promoted checks
> verified green on `main` first; `check_workflow_concurrency` green after the codeql flip; unit tests
> 8/8; `check_docs --strict` + `check_quality --check-only` green; both edited workflow YAMLs parse.

## What this session did

Follow-on to the CI-setup redesign (PR #1737, merged). Owner directive: *"use your own judgment to find
out what should prevent merges completely and build the safe parts."*

Judgment on what **should** hard-block a merge but didn't → built it **safely** by adding it to the
**already-required `code-quality` context** (no branch-protection change, fully reversible; each verified
green on `main` first so no existing PR is newly blocked).

## Shipped (PR #1739)

- **`code-quality.yml`** — three checks promoted to **hard merge gates**:
  - `check_architecture --mode strict` (deps block) — the #1 gap: layer-boundary violations were only
    caught by a local Stop hook, so a `services/→views/` (zero-tolerance) import could reach `main` if the
    hook was skipped. Now blocks.
  - `check_tool_pins` (always-run) — formatter-pin drift (reached `main` in #1315; was red-only). Now blocks.
  - `check_workflow_concurrency` (always-run) — merge-relevant workflows can't cancel a head run (#1275);
    was advisory (#1737). Now blocks.
- **`codeql.yml`** — `cancel-in-progress: false` (was `${{ github.ref != 'refs/heads/main' }}`, which
  cancelled CodeQL on PR refs). Fixes the latent head-run-drop + is the prerequisite for the future CodeQL
  merge-protection ruleset. This is what `check_workflow_concurrency` flagged — now green.
- **`test_check_workflow_concurrency.py`** — the ground-truth test (which asserted codeql *was* flagged)
  updated to the post-fix invariant: every merge-relevant workflow is now safe → the guard's own gate.
- **Docs** — design-doc Phase-A marked (A1 + gating half of A6/A7 shipped); the what-runs-where map's §2b
  moved the three from "coverage the gate doesn't enforce" to ✅ GATING, and the codeql row to `cancel:false`.

## Deliberately NOT this session (still proposed — router Q-0238 (C) / Q-0239)

The branch-protection required-context swap (`code-quality`→`ci-gate`); the ruff tree-wide reformat; the
`ci.yml`/`web-ci.yml`/`pr-freshness.yml` restructure; the `check_ci_coverage` self-silencing fix; and
`check_session_slug_unique` as a gate (its `origin/main` compare needs CI-context verification before it
can hard-block — deferred so it can't false-block every PR).

## 🛠 Friction → guard (Q-0194)

Fixing `codeql.yml` broke my own ground-truth unit test (it was anchored to codeql being *broken*). Guard:
rewrote it to assert the *post-fix* invariant (all merge-relevant workflows safe), so it now doubles as a
regression test — and the same assertion runs as a required CI step, so a reintroduced cancel can't slip
past both.

## ⟲ Previous-session review (Q-0102)

Previous session = the #1737 CI-redesign (this conversation's first PR). **Strong:** exhaustive,
adversarially-verified design + the what-runs-where map. **What it could have done better:** it left the
*entire* execution as owner-gated proposals — including the safe-additive half that needed no sign-off —
so the owner had to explicitly say "build the safe parts." **Improvement (applied this session):** a design
session should *itself* build (or immediately follow with) the clearly-safe, verified-green, reversible
slice rather than proposing 100% of it, given the standing "act on contained/reversible" directive
(Q-0129). This session is that correction — it turned three proposals into shipped gates.

## 💡 Session idea (Q-0089)

**A "does the gate actually block?" meta-test.** This session verified each promoted check passes on a
clean tree — but nothing proves it would *fail* on a real violation *in the CI context* (a gate that
silently no-ops is worse than none — the Q-0120 false-green class). Idea: a tiny test (or a
`workflow_dispatch` self-test) that runs each gating checker against a **known-bad fixture** (e.g. a
fixture workflow with `cancel-in-progress: true`, a fixture module with a `services/→views/` import) and
asserts it exits non-zero — proving the gate bites, not just that it's quiet. Cheap, and it closes the
"is the guard load-bearing or decorative?" question for every gate we add.

## 🧹 Grooming (Q-0015)

Advanced the CI-redesign migration itself: moved three checks from the design's "should-gate" list to
shipped gates (Phase-A partial), and updated both living docs to match — so the next session sees an
accurate gate map, not a stale "these don't gate yet."

## 📋 Docs audit (Q-0104)

Design doc + what-runs-where map updated to the new reality (both edited in lockstep with the workflow
change, no drift). `check_docs --strict` green. No new owner decision (this executes within the already-
recorded Q-0239 Phase-A envelope; the owner directed it in-session). No merged PR to ledger this session
(own PR in flight; next reconciliation folds #1737 + #1739).

## 📤 Run report

- **Did:** promoted `check_architecture`/`check_tool_pins`/`check_workflow_concurrency` to hard gates in
  the required `code-quality` context; flipped `codeql.yml` to `cancel:false`; updated the guard's test +
  both design docs. · **Outcome:** shipped
- **Shipped:** #1739 — 2 workflow edits · 1 test update · 2 doc updates (no `disbot/` runtime change).
- **Run type:** `manual` (owner-directed — "build the safe parts").
- **⚑ Owner decisions needed:** none new — this is the safe-additive Phase-A half of the already-surfaced
  Q-0239. The remaining owner-gated items (CodeQL ruleset, required-context swap, workflow deletions,
  settings.json rewires) stay in Q-0238 (C) / Q-0239.
- **⚑ Owner manual steps:** none. (Merging = deploying, but this changes only CI config, not the running
  bot — nothing to verify in prod.)
- **⚑ Self-initiated:** the specific gate set + the codeql flip were my judgment call within the owner's
  "build the safe parts" directive.
- **↪ Next:** the remaining Phase-A (ruff migration, `ci.yml`/`web-ci.yml` alongside-builds,
  `check_ci_coverage` fix) + owner ratification of the Phase-B config items.
