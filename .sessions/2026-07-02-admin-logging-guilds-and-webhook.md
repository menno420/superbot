# 2026-07-02 — Admin/logging guilds idea + Railway alerts webhook restored

> **Status:** `in-progress` — born-red (Q-0133). Run type: manual · owner-directed.
> Scope: idea capture (docs) + one additive, reversible execution under Q-0213 (recreate the
> owner's accidentally-deleted Railway webhook channel: Discord channel + webhook in the test
> guild via Galaxy Bot, Railway project webhook via API; webhook token never printed).

**Branch:** `claude/superbot-rebuild-design-spec-de4mh7` (restarted from `main` @ #1642 merged).

## What I'm about to do (intentions)

Owner idea (in-chat): a **dedicated admin guild** (manage every server's bot settings from one
place) + a **dedicated central-logging guild** (logging from all servers + the platform/Railway
webhooks); he had a Railway webhook channel in his test server and accidentally deleted it.

1. **Restore the lost piece now:** `#railway-alerts` channel in MineSnakeBotTest (Galaxy Bot holds
   full perms there, verified) + Discord webhook + Railway project webhook pointed at it —
   verified by read-back; it fires naturally on this session's own merge-deploy.
2. **Capture the two-guild architecture** as a structured idea (cross-guild admin panel building
   on Q-0212 + the rebuild's PanelContext; central logging with the ops-vs-member-content privacy
   split flagged as the owner decision; the alerts channel's final home = the future admin guild).
