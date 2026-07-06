# 2026-07-06 — AST guard: check_audit_seam (audit-seam coverage checker)

> **Status:** `in-progress` — born-red card (Q-0133). Building `scripts/check_audit_seam.py`:
> per-function reachability guard flagging a function that performs a state-mutation write
> signal whose success path never reaches `emit_audit_action`. Warn-first + `architecture_rules/`
> allowlist, wired **continue-on-error** in `code-quality.yml` (zero merge-gate risk, Q-0239 G4).
> Will flip to `complete` as the deliberate final step.

## What this session is doing

Continuing the CI-setup arc (`docs/planning/ci-followups-handoff-2026-07-05.md` item #5, first AST
guard). Building the audit-seam coverage checker from the calibrated spec
(`docs/ideas/audit-seam-coverage-checker-2026-07-05.md`) — the naive `*_mutation.py` module scope is
~42% false-positive, so this is **per-function** reachability, repo-wide, warn-only.

Would have caught 3–4 of the 8 #1728 "save-fixes" bugs (admin-cog runtime mutations, security
direct `channel.edit`, `!cleanuphistory` bypassing the audited seam).

_(Enders — idea/review/grooming/docs-audit — filled in at close, then this badge flips to `complete`.)_
