# 2026-07-08 — Settings ledger Phase 1 (captured from the owner's recording)

> **Status:** `complete`

**Scope:** owner-directed — store the per-repo settings so future sessions read state, not guess.
Docs-only. Executes Phase 1 of `docs/planning/per-repo-settings-state-ledger-2026-07-08.md`.

## What happened
- Owner sent a screen recording of the `superbot-next` General settings. The session has no video
  tooling, so I **pip-installed `imageio-ffmpeg`** (a bundled ffmpeg) and extracted 16 frames
  (1 fps) to the scratchpad, then read them as images — solving the "can't watch mp4" gap.
- Captured the verified General settings into `docs/operations/repo-settings-state.md`: Public,
  `main`, all merge methods, **auto-merge ON**, **auto-delete head branches ON**, etc.
- Marked what the recording did NOT show (Rules / required checks) as confirm-per-repo, seeded from
  session context (superbot: Code Quality + CodeQL required; superbot-next: step-8 ruleset).
- Folded in the auto-mode capability facts (the walls + the API-bypass finding) so the ledger is
  the one-stop "what's true about these repos."

## Provenance / reliability header (per Q-0105)
`imageio-ffmpeg` added 2026-07-08 as a **dev-only** frame extractor for reading a screen recording.
Unverified convenience tool — **delete if unused across sessions**; not a runtime dep, not pinned
in `requirements.txt`.

## ⚑ Owner action / next
- Confirm the Rules/required-checks rows per repo (not in the recording); confirm substrate-kit +
  superbot General rows match. Then Phase 2 (generator script) can auto-maintain the readable rows.

## ⚑ Self-initiated
None beyond the owner-directed capture.
