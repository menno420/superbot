# Idea — Audit-log catch-up on reconnect (gap-free logging across restarts)

> **Status:** `ideas` · raised 2026-07-01 (server event logging v2 session) · lane: logging
> · size: M · risk: low-medium (read-only audit-log fetch + dedup)

## The gap

Server event logging v2 (this session) added `on_audit_log_entry_create`, so SuperBot now
logs bans/kicks/channel/role/server changes by anyone — **while the gateway is connected.**
But every gateway-based logger has one blind spot: **downtime.** During a restart, a deploy
(Railway redeploys `worker` on every merge — Q-0193), or a network blip, the gateway is
disconnected and those `on_audit_log_entry_create` events are **never delivered**. A ban that
happens in that window is silently missing from the log — exactly the kind of gap the owner
would notice when comparing against a hosted bot (Dyno) that has catch-up infrastructure.

## The idea

On `on_ready` / `on_resume`, for each guild where an audit-log category is enabled, fetch the
**recent audit log** (`guild.audit_logs(after=<last-seen>)`) and replay any entries newer than
the last one we logged, then post them through the same `log_audit_entry` path. Persist a small
per-guild high-water mark (last audit-log entry id we posted) so:

* on reconnect we only replay the gap, not the whole log;
* we never double-post an entry the live gateway already delivered (dedup by entry id).

## Why it's worth having

* Makes the moderation/server log **gap-free across deploys** — and deploys are frequent
  (every merge). Without it, the busiest logging window (right after a change ships) is exactly
  when events can be missed.
* Small, contained, read-only (needs only the View Audit Log permission the v2 layer already
  requires); the high-water mark is one KV row per guild.
* Directly strengthens the feature this session shipped rather than adding surface area.

## Sketch / open questions

* Storage: a `logging.audit_log_high_water` per-guild setting (last posted entry id), or a tiny
  table. Reuse the settings KV to avoid a migration.
* Bound the replay (e.g. last N / last M minutes) so a long outage doesn't flood the channel —
  `log()` the truncation if the gap exceeds the bound (no-silent-caps rule).
* Rate-limit the backfill post loop so a large gap doesn't hit Discord's send limits.
* Interaction with `bot.get_guild` timing on cold start (guild cache must be populated first).
