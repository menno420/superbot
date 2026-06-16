# Session — myprofile PR B: self-service writes (first UI consumer of ParticipationMutationPipeline)

> **Status:** `in-progress`

## What I'm about to do

The live ▶ NEXT (current-state) is **myprofile PR B — self-service writes**: the first UI consumer of
`ParticipationMutationPipeline` (shipped but unexercised since migrations 027/028). PR A (#938) shipped
the read-only card (`views/profile/profile_view.py` + `/myprofile`/`!myprofile`). PR B adds the write
controls — each action exactly one audited pipeline call, re-render from accessors — following the
shipped Help-editor stack pattern (`views/help/editor.py`).

Plan: `docs/planning/myprofile-foundation-plan-2026-06-10.md` §4.2.

Scope:
- New `disbot/views/profile/editor.py` — owner-locked ephemeral editor stack:
  `ProfileEditorHomeView` (subsystem picker) → `ProfileSubsystemEditorView` (participation opt-in/out ·
  subscription toggles · visibility toggle · preference editors: bool→toggle, enum→select, int/str→modal).
- `profile_view.py`: a read-only `⚙️ Manage settings` navigation button on `ProfileHomeView`
  (lazily opens the editor — keeps the card builder mutation-free, PR A's AST invariant intact).
- Tests: one-call-per-action mock-spy, typed-error copy, unauthorized path pinned, editor writes
  ONLY through the pipeline (AST pin).

Keeps green: `check_quality --full`, `check_architecture --mode strict`, the PR A profile suite.
