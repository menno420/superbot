# 2026-06-19 — BUG-0018 root-fix: stop `site.json` hard-equality test reddening on idea-doc churn

> **Status:** `in-progress`

## What I'm about to do

Dispatch run, no work order → bugs-first. BUG-0018 (bug book) is recorded **FIXED (immediate)**
but with a **root-fix RECOMMENDED** and left open as a recurring trap: the hard byte-equality test
`test_committed_site_json_matches_a_fresh_build` compares `commands[]` in full, but
`commands[].linked_ideas` **and** `commands[].status` are derived from `docs/ideas/` (+ the bug
book), which churns far more often than `site.json` is regenerated. So every idea-doc PR silently
drifts `site.json` and reddens `main` between regenerations.

Implementing the documented recommendation (a): exclude the high-churn **idea/bug-derived** command
fields (`linked_ideas`, `status`) from the **hard** equality assertion — the stable command fields
(name/aliases/category/cooldown/permissions/usage/description/use_cases/examples/notes) stay pinned —
and rely on the already-existing **warn-only** generated-artifact freshness umbrella
(`check_generated_artifacts_fresh.py`, #1027) for the structural identity of those derived fields.
This is a test-contract change only — no producer/runtime change.
