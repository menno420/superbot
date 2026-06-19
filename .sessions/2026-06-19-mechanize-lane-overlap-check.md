# 2026-06-19 — Mechanize the fleet overlap-check (`check_lane_overlap.py`)

> **Status:** `complete`

Gives teeth to the fleet's #1137 *procedural* overlap rule (the #1133/#1128 duplicate-work lesson): a
script the orchestrator runs, so overlap-detection no longer depends on someone remembering the step.

## What was done
- **`scripts/check_lane_overlap.py`** — given a lane's scope (files/dirs/globs), scans recent commits and
  flags any whose files overlap → *"this scope already shipped recently — drop/re-scope before dispatch."*
  **Dogfood-verified:** `check_lane_overlap.py scripts/check_consistency.py` flags the #1128
  consistency-linter-cog-scope commit — i.e. it *would have caught the #1133 duplicate before dispatch.*
  Advisory; `--strict` to gate. Covers the recently-MERGED half (local git) and is explicit that the
  OPEN-PR half still needs `list_pull_requests`.
- Wired into **`ultracode-fleet-plan` rule #7** (the rule now points at the script).
- CI-clean via `check_quality.py --check-only` (trusted over a bare `black --check` that disagreed — the
  CI-mirror rule earned its keep this session).

## Decisions recorded
None new — tooling that operationalizes the existing #1137 rule #7 / the CLAUDE.md "scan open PRs before
starting" rule. No router Q needed.

## Left open / next session
Graduate to `--strict` as a real dispatch gate once it's proven false-positive-free across a few fleet runs.

## 💡 Session idea
Teach `check_lane_overlap` to also accept a **planning-doc** and auto-extract its `disbot/` scope (the way
`check_plan_code_drift` already extracts named symbols), so the orchestrator can pass a plan instead of
enumerating files by hand.

## ⟲ Previous-session review
The #1137 fleet session correctly root-caused the #1133/#1128 collision and shipped the rule — but stopped
at *"MUST run the check,"* a step the incident itself proved can be skipped under pressure. This session
mechanized it. The durable improvement (the whole day's through-line): **pair every new procedural "MUST do
X" rule with a script that does X**, so the guard doesn't lean on memory.
