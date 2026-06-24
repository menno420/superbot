# 2026-06-24 — Startup command-tree auto-sync + post-unification docs cleanup

> **Status:** `complete`

## Goal (owner-directed, follow-up to #1419)

After the BTD6 unification (#1419) the maintainer said: *"you can finish up with
the auto sync, then end the session by cleaning up stale docs."*

## What shipped (PR #1424)

**1. Diff-gated startup command auto-sync** — `services/command_tree_sync.py`:
on boot, fetch the live global commands from Discord (`tree.fetch_commands()`)
and compare the **set of qualified command paths** to the local tree; call
`tree.sync()` **only** when they differ. Conservative by design — compares
command *paths* (add/remove/rename of commands + subcommands), not
param/description details, because Discord normalises option payloads and a
fuller diff would false-positive and re-sync every boot (the rate-limit risk).

- Wired into `bot1.on_ready` as a reconnect-safe one-shot (mirrors
  `_maybe_report_startup_health`), spawned via the task supervisor.
- Kill-switch `AUTO_SYNC_COMMANDS=0` (config; default on). Every failure path is
  non-fatal — it can't crash startup.
- Result: a command change goes live on the next deploy with no manual
  `!syncslash`. Manual `!syncslash` stays for instant guild refresh.
- 23 service tests (path extraction vs the real unified tree + the fetched
  model; disabled / unchanged / changed / fetch-fail / sync-fail).

**2. Docs cleanup** — swept the reference docs still describing the old
five-group BTD6 layout: `docs/subsystems/btd6.md` (the binding area doc) and
`docs/setup-platform/settings-customization-command-map.md` (the five BTD6
sub-sections → unified `/btd6 …` + hidden-alias notes). Regenerated
`docs/operations/env-vars.md` (the new flag) + dashboard artifacts.

## Status checklist
- [x] `services/command_tree_sync.py` — path-diff + gated sync + kill-switch
- [x] `config.AUTO_SYNC_COMMANDS` env flag
- [x] Wire one-shot into `bot1.on_ready`
- [x] Tests (23) — all outcome branches + real-tree path extraction
- [x] Docs cleanup (subsystems/btd6 + command-map; env-vars + artifacts regen)
- [x] `check_quality --full` green (12428 passed) + arch strict (0 errors)
- [x] Flip card → auto-merge

## Scope notes (deliberately deferred, flagged not orphaned)
- `docs/agent/index.yml` source_roots stay valid as-is (the `cogs/btd6/` package
  entry already covers `_unified.py`); not re-pack'd to avoid churn for no gain.
- `docs/planning/platform-mapping-a-user-surface.md` left untouched — under
  another active claim (`claude-jolly-johnson`, docs reconciliation band).
- `docs/operations/production-deployment.md` still frames `!syncslash` as the
  post-deploy step; once this PR is live, auto-sync handles propagation — a small
  runbook update is the natural next touch (noted, not done here to bound scope).

## 💡 Session idea (Q-0089)
**Make the manual `!syncslash` reuse `command_tree_sync.auto_sync_if_changed`.**
Right now `admin_cog.sync_slash_commands` does an *unconditional* `tree.sync()`,
while the new startup path is diff-gated. Routing the manual command through the
same gated helper (with an explicit `--force` escape for "sync anyway") would
give one implementation, one place to reason about rate limits, and a
`!syncslash` that can *report the live-vs-local diff* before acting. Small,
contained, and it retires the last unconditional sync. Worth an idea file if it
survives next session's sniff test.

## ⟲ Previous-session review (Q-0102)
Previous in-chain: the #1419 unification. **Did well:** comprehensive and green
in one pass, and it caught + fixed a real latent bug (the dashboard scanner was
blind to module-level command trees) rather than just working around it.
**Missed / could improve:** the PR *body* was written before the implementation
shape settled (it said `cogs/btd6/_commands/` — a dir — but the build landed as
`_unified.py`, a file), so the body needed a post-open correction. **System
improvement:** when opening the born-red PR *first* (the right call for the
in-flight signal), keep the body's "How" section deliberately high-level until
the approach is locked, then fill specifics at flip-to-complete — avoids a
published-then-corrected description. Minor, but it's a clean rule.

## 📝 Doc audit (Q-0104)
- `check_quality --full` green; `check_architecture --mode strict` 0 errors.
- New env var `AUTO_SYNC_COMMANDS` is in its durable home (`config.py` +
  generated `docs/operations/env-vars.md`); the kill-switch + reliability header
  are in the service docstring.
- Owner decision: this PR executes an in-chat owner directive ("finish up with
  the auto sync, then clean stale docs") — no new router Q needed.
- Ledger: PR #1424 in-flight; #1419 just merged — both recorded by the next
  reconciliation pass (the `claude-jolly-johnson` claim owns current-state, so
  this session does not edit it). `check_current_state_ledger --strict` shows
  only benign newest-merge lag, not drift.
