# 2026-06-24 — Startup command-tree auto-sync + post-unification docs cleanup

> **Status:** `in-progress`

## Goal (owner-directed, follow-up to #1419)

After the BTD6 unification (#1419) the maintainer said: *"you can finish up with
the auto sync, then end the session by cleaning up stale docs."* Two pieces:

1. **Startup command-tree auto-sync** — retire the manual `!syncslash` toil. The
   recurring pain (duplicate commands #1409, the big unification re-sync #1419)
   all trace to "remember to sync after a command change." Build a *safe* auto
   sync so a command change goes live on deploy with no manual step.
2. **Docs cleanup** — sweep the reference docs that still describe the old
   five-group BTD6 layout (flagged in the #1419 session log).

## Design — diff-gated, no storage, no false positives

`services/command_tree_sync.py`: on startup, fetch the live global commands from
Discord (`tree.fetch_commands()` — already used in `views/setup/sections/ai_setup`)
and compare the **set of qualified command paths** to the local tree. Call
`tree.sync()` **only** when they differ. Conservative on purpose — it compares
*paths* (add/remove/rename of commands + subcommands), not param/description
details, because Discord normalises option payloads and a fuller diff would
false-positive and re-sync every boot (the rate-limit risk). Param/description-
only changes still use manual `!syncslash`.

- Wired into the `on_ready` one-shot path (`bot1.py`, mirrors
  `_maybe_report_startup_health`) so it fires once per process, reconnect-safe.
- Kill-switch: `AUTO_SYNC_COMMANDS=0` (env; default on). Failures are non-fatal.
- Merging = deploying (Railway), so the next deploy auto-syncs the unified
  `/btd6` tree — the maintainer's `!syncslash global` step becomes optional.

## Status checklist
- [ ] `services/command_tree_sync.py` — path-diff + gated sync (+ kill-switch parse)
- [ ] `config.AUTO_SYNC_COMMANDS` env flag
- [ ] Wire one-shot into `bot1.py` `on_ready`
- [ ] Tests: path extraction (local + remote), disabled / unchanged / changed /
      fetch-fail / sync-fail
- [ ] Docs cleanup: command-map + platform-mapping + agent index + subsystems/btd6
- [ ] `check_quality --full` green + arch strict
- [ ] Flip card → auto-merge

## Notes
- Reliability header (Q-0105): the auto-sync is **unverified** — confirm it fires
  correctly across a few real deploys before fully trusting; kill-switch + the
  manual `!syncslash` remain. Delete the seam if it proves flaky.
