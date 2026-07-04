# 2026-07-01 — XP import: button entry + generic framing (follow-up)

> **Status:** `complete`

**Run type:** `manual`

## Arc

Follow-up to the merged #1607 (XP/level migration via level-up channel scan). Owner feedback:

1. **Make it a button**, not only the `!xpimport` command.
2. **Drop the Arcane-centric framing** so it doesn't feel single-bot — but keep explaining it works
   by reading another bot's **dedicated level-up channel**.

## What shipped (PR #1610)

- **Shared scan** — moved the channel scan out of the cog into
  `services/xp_migration.scan_channel(guild, channel, fmt, limit)`, so the `!xpimport` command **and**
  the new button share one implementation (removed the cog's private `_scan_channel`).
- **Button + setup view** — a **"📥 Import from another bot"** button on the admin XP config panel
  (`!xpconfig`) opens `XpImportSetupView`: a native **channel picker** + a **"which bot" picker**
  (Arcane / MEE6 / SuperBot / Generic, defaulting to Arcane but clearly one of several) → **🔍 Scan** →
  the existing `XpImportView` preview/confirm.
- **Generic framing** — command help, the `!xpimport help` embed, and the panels now lead with "import
  from another bot" and explain the **dedicated level-up channel** requirement; Arcane/MEE6 are listed
  as *examples*, not the headline.
- **Docs** — `docs/operations/xp-migration.md` now leads generic + documents both the button and command
  paths. **Tests (+3)** for `scan_channel` (reduce-to-max / skip-non-bot / Forbidden→None / name-fallback).
- Local CI mirror GREEN; arch strict 0 errors.

## Decisions made alone (ratify)

- The button lives on **`!xpconfig`** (the admin XP surface), not the user-facing XP hub — import is an
  admin action.
- Kept **Arcane as the default** source in both the command and the picker (it's the live need), but the
  picker shows all four bots so it never *feels* single-bot.
- `scan_channel` lives in the **service** layer (it does Discord `history` I/O on a passed-in channel) —
  consistent with `role_automation.apply` doing Discord writes from a service; keeps one scan impl.
- The channel picker filters to **text channels**; the command path (any-channel converter) is the
  fallback for an unusual channel type.

## Flagged for maintainer (known limits)

- **Not live-verified** (no Discord in the sandbox) — the button click-through (ChannelSelect → Scan →
  preview → Apply) especially wants a real run. **Owner manual step.**
- The channel picker only lists **text** channels. If a server's level-up channel is an Announcement/News
  channel, use the command form `!xpimport <bot> #channel` instead (it accepts any channel).

## 🛠 Friction → guard (Q-0194)

- **None new this run.** Clean build on top of #1607; the existing guards did their job — ruff's
  unused-import rule caught the imports left dangling by moving `_scan_channel` out of the cog (removed
  `resources`/`ScanPlan`/`_SCAN_SAMPLE_LIMIT`), and the full mirror is the standing black/mypy/pytest gate.
  No footgun worth a new checker surfaced; not inventing one (Q-0089 honesty bar).

## 💡 Session idea (Q-0089)

**Import dry-run / undo.** The import is raise-only + idempotent, but a *mis-scoped* run (wrong channel
or a format matching noise) can still over-grant levels to the wrong members. Record the pre-import
`(user_id, xp)` for each raised member as one reversible batch (keyed by the import's audit
`mutation_id`) so an operator can **undo the last import**. Turns "safe from data loss" into "safe from
mistakes" for a bulk write. Not in the backlog yet (dedup-grepped); distinct from last session's
auto-detect idea (now routed into the bot-migration-assistant doc).

## ⟲ Previous-session review (Q-0102)

Reviewed **#1607** (the migration feature itself) — comprehensive, well-tested, merged clean on first
CI, and it *correctly anticipated* the rapid-push CI-drop risk in its own review. **The improvement it
proves (system):** #1607 shipped **command-only**, and the very first owner reply was "is this a button?"
— i.e. an agent's sense of "complete" (a working command + tests + docs) diverged from the owner's, who
navigates by **UI**. The durable lesson for user-facing features: **ship the discoverable entry point
(button / hub tile) in the *same* PR as the command**, not as a command-first v1 that predictably needs a
follow-up. Command-first is fine for operator/CI tooling; for a *member/operator-facing feature* the
button is part of "done." Worth adding to the command-integration standard as a soft rule.

## Doc audit (Q-0104)

No new commands (xpimport already ledgered in #1607) or settings keys → command/setting dashboard data
unchanged; the only generated-artifact delta is the `updates` feed picking up this session card, which is
regenerated as the final step. `docs/operations/xp-migration.md` updated + still reachable (ownership.md
link). `check_docs --strict` / `check_current_state_ledger --strict` run at close. No chat-only owner
decisions beyond the ratify list. Not adding to current-state Recently-shipped (merged-PRs-only).

## 📤 Run report

- **Did:** added a **button** entry point for XP import (on `!xpconfig`) and re-framed the whole feature
  generically ("import from another bot" + a dedicated level-up channel), keeping Arcane as one supported
  format · **Outcome:** shipped (local mirror green, auto-merge armed; awaiting CI)
- **Shipped:** #1610 — `services/xp_migration.py` (shared `scan_channel`) · `views/xp/import_panel.py`
  (`XpImportSetupView`) · `views/xp/config_panel.py` (button) · `cogs/xp_cog.py` (generic copy) · docs + tests.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none.
- **⚑ Owner manual steps:** **live-verify** — `!xpconfig` → **📥 Import from another bot** → pick the
  level-up channel + bot → Scan → Apply (needs Read Message History in that channel). Sandbox can't reach Discord.
- **⚑ Self-initiated:** none — both changes are the owner's direct feedback on #1607.
- **↪ Next:** live-verify the button flow; optional follow-ons still open — MEE6 direct-API importer
  (seam ready), the auto-detect idea (now in `ideas/bot-migration-assistant-2026-06-24.md`), and the
  import dry-run/undo idea above.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (auto-merge armed; awaiting CI) |
| CI-red rounds | 1 born-red (expected); local mirror green first pass |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (import dry-run/undo) |
| Ideas groomed | 1 (auto-detect → routed into bot-migration-assistant) |
