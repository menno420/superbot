# 2026-06-23 — U3b: casino + cleanup `edit_in_place` tail

> **Status:** `in-progress`

Ultracode Phase-1 worker. Unit **U3b** (parallel-safety: yellow). Branch
`claude/u3b-casino-cleanup-tail` off `origin/main`.

## Scope
Drive the 3 remaining `edit_in_place` consistency findings in casino + cleanup to 0
(by in-place fix **or** by flagging genuine new-message cases for the coordinator to
allowlist in Phase 2):

- `disbot/views/casino/hub.py:95`  `CasinoHubView.new_poker`
- `disbot/views/casino/hub.py:112` `CasinoHubView.roulette`
- `disbot/views/cleanup/policy_panel.py:765` `CleanupPolicyPanelView.btn_remove`

## What's about to happen
Read the three callbacks against live source, classify each as fix-in-place vs.
genuine-new-message, and either convert or flag to the coordinator. `consistency_exceptions.yml`
is coordinator-owned — workers never edit it; genuine new-message cases are STOPped and
reported.

> Born red — leave red. The coordinator flips/merges in Phase 2.
