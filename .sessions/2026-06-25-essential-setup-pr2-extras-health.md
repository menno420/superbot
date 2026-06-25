# Session — 2026-06-25 · Essential Setup PR 2 — extras menu + "Check my setup"

> **Status:** `in-progress` — building. Run type: routine · dispatch.

## What I'm about to do

Empty-fire dispatch run. The bug-book root-fix backlog is gated (BUG-0009 newest-towers is
data-gated; BUG-0019 #1 is an owner design fork), so I take the explicit S1 ▶-next plan slice:
**Essential Setup wizard restructure — PR 2** (the marquee S1 arc, plan
`docs/planning/setup-wizard-restructure-plan-2026-06-24.md` §7). PR 2 = the **Extras menu** (the
optional features the spine doesn't cover — each surfaced with its setup command) + the single
**"Check my setup"** plain-language health button, both wired into the "All done" summary.

Scope: additive, no new cog/command. New plain-language views in `disbot/views/setup/essential_setup.py`
(jargon-guard-clean — the file is not in the baseline, so new copy must be plain). Tests in
`tests/unit/views/setup/`.

