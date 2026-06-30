# 2026-06-30 — Cleanup history filters + age gate + panel authority test (completion-first deepening)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What this run is about to do
Empty-fire dispatch advancing the S1 completion-first arc (Q-0209). The **Cleanup** completion
certificate (`docs/planning/feature-completion/units/cleanup.md`) lists four offline punch-list
items; this run closes the buildable deepening ones:

- **#2 — History content-type filters** — add `embeds` / `links` / `attachments` sweep modes to
  `!cleanuphistory` for Carl-bot/MEE6/Dyno parity.
- **#3 — History age filter** — an `older:<duration>` gate composable with any mode.
- **#1 — Panel authority-recheck test** — pin that `interaction_is_admin()` gates the
  policy-apply callback (today covered only via the pipeline backstop).

#4 (configurable spam window) is left for a follow-up: making it a *real* setting needs a
config-input widget, not just a constant rename — recorded honestly in the cert. #5/#6 (live
walkthrough + owner ✔) stay owner-gated.

PR opens born-red; flips to `complete` as the final step.
