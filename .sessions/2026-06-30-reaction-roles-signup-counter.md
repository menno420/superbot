# 2026-06-30 — Reaction-roles live sign-up counter (S1 deepening)

> **Status:** `in-progress` — born-red card (Q-0133). Run type: manual · owner-directed.

**Branch:** `claude/reaction-roles-counter-bgxnyd`.

## What I'm about to do (intentions)

Owner request (Discord screenshots): an event organiser wants members to press a button to signal
"I'm in" for an event (e.g. *"see how many people are planning to get 15K stars"*) — and wants a
**counter that keeps track of how many people pressed the button**, visible on the message itself
(the value-add over native emoji reactions, which only count anonymously and don't persist a role).

The reaction-roles arc is already Carl-bot-mature (role *menus* with buttons/dropdowns, audited
seam, restart re-attach). There is an *operator-only* cumulative pickup tally
(`role_menu_pickup_stats`, in Diagnostics) — that is **not** what's asked for. The ask is a
**member-facing live headcount** on the public menu.

Planned (additive, opt-in, default off → byte-identical for every existing menu):
1. **Migration 102** — `role_menus.show_counts BOOLEAN NOT NULL DEFAULT FALSE`.
2. **`utils/db/role_menus.py`** — thread `show_counts` through `create_menu` / `update_menu`.
3. **`services/reaction_role_service.py`** — thread `show_counts` through the audited
   `create_menu` / `update_menu`; surface it in the audit `_summarize`.
4. **`views/roles/role_menu_counter.py`** (new) — `collect_counts(guild, role_ids)` (one pass over
   `guild.members` → per-role counts + a distinct-member total, no double count), `format_count`,
   and a **debounced** `schedule_count_refresh(message, menu_id)` (trailing-edge, ~2.5 s → at most
   one message edit per window per message; rate-limit-safe; counts re-read live at edit time).
5. **`views/roles/role_menu_view.py`** — `build_menu_embed` renders the per-role count + total when
   `show_counts`; the button/select callbacks schedule a debounced refresh after a successful change.
6. **`views/roles/role_menu_builder.py`** — a **📊 Counts** toggle (row 2) + the preview "Counts:
   on/off" line + thread `show_counts` through Post/Save + `from_menu`.
7. Tests for each layer (counter one-pass math + debounce coalescing, embed rendering, service
   threading, builder toggle).

**Semantics decision (made alone, reversible):** the counter shows **current holders** of each role
(`guild.members` ∩ role), not a cumulative press tally — for an RSVP it must drop when someone
un-signs or leaves, and a live membership count is self-correcting (never drifts). The bot already
runs the members intent + startup chunking, so the count is accurate.

Offline, contained, reversible, test-covered → self-merge on green (owner-directed, Q-0191/Q-0113).
No external surface; no data backfill (new column defaults off).

## What shipped

_(filled in at close)_

## Context delta

_(filled in at close)_
