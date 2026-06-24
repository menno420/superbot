# Session — 2026-06-24 · Essential Setup survives restart (revive in place)

> **Status:** `in-progress` — making the new setup wizard survive a bot restart.

**Trigger:** Owner — "the setup wizard seems to not survive restart, can you fix this?" Follow-on to
the logging-step fix (#1439, merged). Owner chose (AskUserQuestion) the **revive-in-place** option:
after a restart, the in-channel wizard message itself shows a **Resume** button and continues from
the exact step.

## Why it dies today

`EssentialFlow` holds all state in memory; the step views are non-persistent `BaseView`s (timeout
600s, dynamic custom_ids). On restart the in-memory views are gone, so the wizard message's buttons
"interaction failed". (The **launcher** message already survives — it's a persistent view re-bound on
`on_ready`; the in-channel Essential Setup flow never adopted that pattern.) Essential Setup is
**direct-apply**, so no *configuration* is lost on restart — only the wizard's position + live buttons.

## Design (revive in place — mirrors the launcher's `_resume_launchers`)

- **Migration 099** — `setup_session.essential_message_id BIGINT` + `essential_step INTEGER` (nullable;
  the wizard message + its step). Channel reuses `setup_channel_id`.
- **DB/service** — primitives + `SetupSession` fields + `set_essential_anchor` / `set_essential_step` /
  `clear_essential_anchor` wrappers.
- **`EssentialSetupResumeView`** (persistent, `timeout=None`, static custom_id, admin-gated) — on click
  rebuilds the flow at `essential_step` and edits the message back to the live step view.
- **Persist on post + on every move**; **clear + `mark_complete`** when the flow reaches the summary.
- **`SetupCog`** — register the resume view at `cog_load`; `on_ready` sweep (`_resume_essential_flows`)
  edits each in-progress essential message to show the Resume view (the launcher pattern, for the
  in-channel wizard message).

## ⚑ Self-initiated: NO — owner-directed feature; owner picked the revive-in-place depth via
AskUserQuestion.
