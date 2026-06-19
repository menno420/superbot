# Safety & Community — one operator landing

> **Status:** `ideas` — captured 2026-06-13 (Q-0089 session idea, from the welcome+counters
> slot-6 session). Not a plan; not approved. Source + merged PRs win.
> **Subsystem:** moderation, automod, security, logging, welcome, counters — the safety lane operator landing.

## The gap

The safety/community lane (Q-0108–Q-0112) is **one platform** in the
[family plan](../planning/safety-community-family-plan-2026-06-13.md), but its subsystems
are deliberately **scattered** across the hub graph for good per-feature reasons:

| subsystem | shipped | placement |
|---|---|---|
| automod | #772 | `parent_hub="moderation"` |
| server logging (events) | #774 | extends `logging` (→ moderation hub) |
| welcome | #775 | **hub-less** (admin-tier; Help hook + `!settings`) |
| counters | #775 | **hub-less** (admin-tier; Help hook + `!settings`) |
| image moderation | next band | (will reuse automod panel) |
| security tiers 1+2 | next band | (TBD) |

Going hub-less for welcome/counters was the right call for the **user-facing** Community
hub (its child list has no tier filter — see `views/community/hub.py` — so admin config
parented there would show to everyone). But the side effect is that the **operator** now
has no single front door to the automated safety+community layer the plan promises as
"one platform." To answer "what's protecting/greeting my server, and what's on?" an admin
must already know to run `!automod`, `!logging`, `!welcome`, `!counters` separately.

## The idea

A read-only **operator landing** for the whole lane — either a `!safety` (or
`!community-ops`) command, or a Settings supergroup — that lists every lane subsystem with:

- its **master-flag state** (🟢/⚫, read from each `*_config.load_policy`),
- a one-line "what it does",
- a jump button to that subsystem's `!settings` group.

It composes entirely from the existing `SubsystemSchema` registry + the per-subsystem
`load_policy` read models — **zero new mutation path, zero new state**. A natural
`build_help_menu_view`-style panel.

## Why I believe in it

- It closes the one real cost of the hub-less decision (operator discoverability) without
  reintroducing the user-hub-clutter problem.
- It makes the "one platform" framing true at the UI, not just in the plan.
- It is genuinely cheap (read-only aggregation over registries that already exist) and
  gets *more* valuable as image-mod + security land (6 subsystems is past the point where
  "just remember the four commands" works).

## Sequencing

After the lane's remaining build slices (image-mod, security tiers 1+2) — the landing
wants the full set to aggregate. Until then it is a small, self-contained panel PR. Route
through the normal grooming lane; no owner decision needed (read-only, no new product
direction — it surfaces already-approved features).
