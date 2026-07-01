# 2026-07-01 — Server event logging v2: Discord audit-log integration (Dyno parity)

> **Status:** `in-progress` — born-red card (Q-0133). Run type: manual · owner-directed.
> Do not merge until this flips to `complete`.

**Branch:** `claude/modest-knuth-5syw7s` (from `main` @ #1621).

## What I'm about to do (intentions)

The owner reported that SuperBot's server logging "catches other things than Dyno" despite
having the right settings/bindings enabled. Investigation confirmed the root cause is a
**coverage gap, not a misconfig**:

- **No Discord audit-log integration at all** — `grep on_audit_log_entry_create` returns zero
  hits. SuperBot only logs a moderation action when it was performed *through SuperBot's own
  commands* (the internal `moderation.action_taken` bus event, `moderation_service.py:226`). A
  ban/kick/timeout/channel-edit/role-change done via Discord's UI or another bot (Dyno) is
  **never logged**. `docs/server-logging.md:328` admits actor attribution "needs audit-log
  integration and is a phase-2 enhancement" — never built.
- **Only 5 gateway listeners exist** (`logging_cog.py:138-211`): message delete/edit, member
  join/leave, member role-update. No listeners for bans, channels, server-roles, voice,
  invites, emojis, server settings. Intents are already sufficient (`Intents.default()`).
- Passive listeners drop bot-authored events, and message delete/edit fire only for *cached*
  messages (old/uncached deletes → nothing logged).

Owner chose "build the full v2 (all 3 PRs)" — full parity this session.

**Plan (one branch, logical commits):**
1. **Audit-log layer** — `on_audit_log_entry_create` listener + `log_audit_entry` handler +
   `AuditLogAction`→embed map. New opt-in categories (`moderation` / `channels` / `server`) +
   repurpose `roles` to the audit-log path (actor attribution). Surface View-Audit-Log
   permission in `!logging status`.
2. **Passive completeness** — raw message delete/edit + bounded in-memory message cache;
   `voice` category (`on_voice_state_update`).
3. **Config UX + tests + docs** — SettingSpecs + panel/status for the new categories; extend
   ignore lists to audit actor/target; `server-logging.md` → v2; full test coverage.

All new behaviour behind the existing off-by-default master + per-category gating, so no guild
changes until opted in.

## What shipped

_(filled in at close)_
