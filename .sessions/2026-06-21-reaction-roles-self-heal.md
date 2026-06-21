# 2026-06-21 — Reaction roles: listener self-heal for dead bindings

> **Status:** `in-progress` — born-red HOLD (Q-0133). Owner-accepted continuation (offered at #1248
> close; owner said "continue"). Q-0191 → merge on green. Fresh branch.

> **Run type:** `manual`

## What I'm about to do

The #1248 manual 🧹 Clean up button removes bindings whose role was deleted. This makes that cleanup
**automatic**: when a member reacts (or un-reacts) on a binding whose role no longer resolves, the
binding is removed on the spot, so dead config self-heals without anyone opening the panel.

- `services/reaction_role_service.py` — `_self_heal_dead_binding(guild, message_id, emoji, role_id)`
  removes a binding whose role is gone (audited as a **`system`** action) and is called early in
  `handle_reaction_add` / `handle_reaction_remove`. Threaded an `actor_type` param through
  `unbind_emoji` / `_emit` so the automatic cleanup is distinguishable from an operator removal.
  Safe because discord.py fully caches roles → `resolve_role` returning `None` means genuinely deleted.

## Note (owner clarification, this session)

Corrected my own framing: Railway has **always** auto-deployed `worker` on merge — the recent change
(Q-0193 / #1247) was only *removing the wrong "merge ≠ deploy" line from CLAUDE.md*, not a behaviour
change. Merged = deployed. (No "restart it yourself" guidance.)

Verify: `check_quality.py --full` + `check_architecture.py --mode strict`.
