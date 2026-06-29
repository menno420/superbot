# 2026-06-29 — Best-in-class operator command gaps (slowmode · topic · roleinfo)

> **Status:** `in-progress`

**Run type:** routine · dispatch

## What I'm about to do

Empty-fire scheduled dispatch (no work order). Acting on the live **S1 ▶ Next** offline-startable
completion-first deepening picks, specifically the assessment punch-list's named *"best-in-class command
gaps (channel slowmode/topic, utility roleinfo/channelinfo)"*. `channelinfo` already exists
(`channel_cog`); the genuine gaps are **`!slowmode`**, **`!topic`**, and **`!roleinfo`**.

**The slices (aim 2–3, self-mergeable on green):**

- **Slice 1 — `!slowmode` + `!topic`** (channel-edit commands). Both are channel *mutations*, so they
  ship through the audited `ChannelLifecycleService` seam (two new REVERSIBLE operations
  `set_slowmode` / `set_topic`, request fields, `_apply_one`/`_summary` branches) — same pattern as
  `rename`, so each fires the audit companion + `channel.lifecycle_changed` event. Cog commands gated by
  `is_admin_or_owner`, matching the existing channel ops.
- **Slice 2 — `!roleinfo <role>`** (read-only role detail card in `role_cog`): members count, color,
  position, mentionable/hoisted, key permissions, created date. No seam needed (read-only).

Each slice is contained, additive, offline-unit-tested → self-merge on green per CLAUDE.md.

## What shipped

_(filled at session close)_
