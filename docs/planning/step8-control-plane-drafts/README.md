# Step-8 phase-1 control-plane drafts — durability stash (2026-07-08)

This directory is a **durability stash** of the rebuild step-8 phase-1
control-plane drafts for **menno420/superbot-next**. It exists only so the
drafts survive outside a single session's scratchpad.

- **Source of truth:** the canonical rebuild plan + the design spec §6 — not
  these files.
- **Status:** drafts pending **phase-2** (rebase onto the adopted
  superbot-next skeleton). They target the future superbot-next repository,
  not superbot.
- **Never merge this directory into superbot `main`.** It is parked under
  `docs/planning/` deliberately so the workflow YAMLs inside are inert
  (GitHub only executes workflows at `.github/workflows/` at repo root) —
  even an accidental merge could never install anything here.

## Layout

- `repo/` — mirrors the future superbot-next tree (workflows, gate runners,
  gate configs, parity manifests, tests, docs).
- `meta/` — control-plane material that is not repo files: branch ruleset
  (`ruleset.json`), repo settings checklist, token posture, `DECISIONS.md`,
  and `OWNER-ACTIONS.md`.
