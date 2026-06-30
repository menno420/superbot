# 2026-06-30 — Reaction-roles RSVP roster ("Who's in?")

> **Status:** `in-progress` — born-red card (Q-0133). Run type: manual · owner-directed.

**Branch:** `claude/reaction-roles-counter-bgxnyd` (restarted from `main` @ #1570 merge — the prior PR
for this branch already merged, so this is a fresh change).

## What I'm about to do (intentions)

Follow-on to the live sign-up counter (#1570): the owner approved the **RSVP roster** idea I flagged —
after "how many" the organiser's next question is "**who**". Because every menu option is a real role,
the roster is a free `role.members` read (the same primitive the counter uses) — no new storage.

Planned (additive, gated on the existing opt-in `show_counts` so only RSVP-style menus get it):
1. **`views/roles/role_menu_counter.py`** — `build_roster_embed(menu, options, guild)`: one field per
   option ("✅ Going · 12" + the members who hold it), member names truncated to fit Discord's field
   cap with a "+N more" tail; an empty option reads "—".
2. **`views/roles/role_menu_view.py`** — a persistent **`👥 Who's in?`** button
   (`role_menu:{menu_id}:roster`) added to the menu view **only when `show_counts` is on and the
   component budget allows** (≤25 total — a 25-role button menu has no room; RSVPs are small so this
   is a non-issue); its callback posts the roster **ephemerally** (visible only to the clicker).
3. Tests: roster embed lists holders + truncates a large option; the button is present only when
   counts are on + budget allows; persistence custom_id.

**Privacy note:** listing current holders of a *self-assigned, opt-in* role exposes nothing private —
role membership is already visible in Discord (member list / role mention). This is distinct from the
per-user *pickup history* the overhaul plan deliberately kept private (§9). Read-only; no DB writes.

Offline, contained, reversible, test-covered → self-merge on green (owner-directed).

## What shipped

_(filled in at close)_

## Context delta

_(filled in at close)_
