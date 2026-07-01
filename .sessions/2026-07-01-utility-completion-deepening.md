# 2026-07-01 — Utility completion-first deepening

> **Status:** `in-progress`

**Run type:** routine · dispatch (empty fire — advancing the S1 completion-first ▶ Next queue)

## What I'm about to do

Clear the offline punch-list on the **Utility** completion certificate (`◐ assessed`,
`docs/planning/feature-completion/units/utility.md`) to move it toward `✔`:

1. **Punch #1 — resolve `utility.tool.ping`** (declared capability, unimplemented). The user-facing
   `!ping` today is *admin-tier* (an alias of diagnostic's `!latency`), so ordinary members have no
   ping — the exact gap. Give Utility a real **user-tier `!ping`** (round-trip + WS latency) and
   re-home the `ping` alias off diagnostic's `latency` (diagnostic keeps admin `!latency`). Update
   both registry `entry_points` (diagnostic `ping`→`latency`; utility gains `ping`).
   **Collision-checked first (BUG-0030 lesson): `ping` currently only exists as diagnostic's alias;
   removing it frees the name for utility's user-tier command.**
2. **Punch #4 — best-in-class commands:** add `!botinfo` (uptime/guilds/latency/version) and
   `!membercount` (humans/bots/total) — the named missing Carl-bot/MEE6 parity commands
   (roleinfo/channelinfo/userinfo already exist).
3. **Punch #2/#3 — command-behavior + authority tests:** cover the previously-untested command paths
   (info/avatar/poll/remind/invite/clear + the new ping/botinfo/membercount), incl. the `clear`
   (manage_messages) / `invite` (create_instant_invite) authority enforcement.

Contained, offline, reversible. Full CI mirror green (incl. the BUG-0030 boot-smoke + extension-integrity
collision guards) before flipping the card to complete.
