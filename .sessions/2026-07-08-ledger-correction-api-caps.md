# 2026-07-08 — Ledger correction: new repos are bare + full API capability map

> **Status:** `complete`

**Scope:** owner clarified only `superbot` has rules/branch-protection/Actions/workflows — the new
repos are bare. Correct the settings ledger, and fold in the API-capability tests run this session.
Docs-only. No `disbot/` changes.

## What shipped
- **Ledger correction** (`docs/operations/repo-settings-state.md`): the Rules / automation rows for
  `substrate-kit` + `superbot-next` now read **none yet (bare)**, not "per step-8 ruleset" (that was
  the *planned* config, not applied — my premature seed). Added a Workflows/Actions row.
- **Full API capability map** (ledger + probe-report addendum extension): confirmed first-hand this
  session that the GitHub Contents API allows an autonomous session to **create / update / delete**
  files — including `.github/workflows/*` (no `workflow`-scope block; `substrate-kit` `4d17832c`
  created, `586e8f1c` deleted). So the whole file/content layer is agent-doable; only repo settings
  (rulesets, branch protection, required checks, secrets/PATs) are owner-only → new-repo build is
  ~90% agent-doable. Git-ref *rewrite* walls (force-push, branch-delete) are unaffected (untested via
  Git Refs API; `test/permprobe-0708` preserved).

## ⚑ Self-initiated
Correction + capability capture from an owner-directed test; drift-fix discipline. No unprompted scope.

## ⚑ Owner action / next
- Still owner-only for the new repos: rulesets/required-checks, `ROUTINE_PAT` secret. Agent-doable:
  the full CI/tooling file tree (adopting from substrate-kit). Awaiting owner's go to scope that task.
