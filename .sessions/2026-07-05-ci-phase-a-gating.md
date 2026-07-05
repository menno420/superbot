# 2026-07-05 — CI Phase-A: make the should-gate invariants actually block merges

> **Status:** `in-progress` — born-red gate (Q-0133). Held until the gating additions are verified
> green (each check passes on main today) and the deliverable lands.

## What this session is doing (born-red declaration)

Follow-on to the CI-setup redesign (PR #1737, merged). The owner directed: *"use your own judgment to
find out what should prevent merges completely and build the safe parts."*

Judgment on what **should** hard-block a merge but doesn't today → build it **safely** by adding it to
the **already-required `code-quality` context** (no branch-protection change, fully reversible):

1. **`check_architecture --mode strict`** — layer-boundary violations (the #1 gap; only a local Stop
   hook enforces it today, so a violation can reach `main` if the hook is skipped). Green on `main`
   (exit 0, warnings only). Runs in the deps block (needs PyYAML).
2. **`check_tool_pins`** — formatter-pin drift across the 3 pin files (reached `main` in #1315;
   advisory-only today). Green; pure stdlib.
3. **`check_workflow_concurrency`** — merge-relevant workflows must not cancel a head run (the #1275
   race); shipped advisory in #1737. Pure stdlib; green once codeql is flipped.
4. **`codeql.yml` → `cancel-in-progress: false`** — fixes the latent head-run-cancellation on PR refs
   (what check_workflow_concurrency flags today) and is the prerequisite for the future CodeQL
   merge-protection ruleset.

Deliberately NOT this session (needs its own care / owner toggle): the branch-protection required-context
swap, the ruff tree-wide reformat, the `ci.yml`/`web-ci.yml` restructure, the `check_ci_coverage` fix,
and `check_session_slug_unique` as a gate (its `origin/main` dependency needs CI-context verification).
Those remain the proposals in router Q-0238 (C) / Q-0239.
