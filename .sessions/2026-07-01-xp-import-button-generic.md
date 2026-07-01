# 2026-07-01 — XP import: button entry + generic framing (follow-up)

> **Status:** `in-progress` — born-red card; flips to `complete` as the final step.

## Arc

Follow-up to the merged #1607 (XP/level migration via level-up channel scan). Owner feedback:

1. **Make it a button**, not only the `!xpimport` command.
2. **Drop the Arcane-centric framing** so it doesn't feel single-bot — but keep explaining that
   it works by reading another bot's **dedicated level-up channel**.

## Scope (this PR)

- Move the channel scan out of the cog into `services/xp_migration.scan_channel(...)` so the command
  **and** the new button share one implementation.
- New `XpImportSetupView` (native channel picker + source-format picker, defaulting to Arcane but
  clearly one of several) → scans → the existing `XpImportView` preview/confirm.
- Add a **"📥 Import from another bot"** button to the admin XP config panel (`!xpconfig`).
- Generalize all user-facing copy to "another bot" + a clear "reads its dedicated level-up channel"
  explanation; Arcane/MEE6 become listed *examples*, not the headline.
- Update `docs/operations/xp-migration.md`; tests for the moved scan + setup flow.

_(Enders filled at close.)_
