# 2026-06-21 — Reaction roles: clean up dead bindings

> **Status:** `in-progress` — born-red HOLD (Q-0133). Owner-directed (screenshots: a stale
> `💀❤️😘 → (deleted role)` binding that should not remain). Q-0191 → merge on green. Fresh branch.

> **Run type:** `manual`

## What I'm about to do

Owner reported leftover cruft in the Reaction Roles panel: an old pre-#1234 binding
(`1518271910256054385 · 💀❤️😘 → (deleted role 1515523817881993439)`) whose role was deleted. They
want it gone. (The modal placeholder `💀 ❤️ 😘` is a *good* preview and **stays** — no change there.)

- `services/reaction_role_service.py` — `prune_dead_bindings(guild, *, actor_id)`: removes every emoji
  binding whose role no longer resolves (audited via `unbind_emoji`), returns the removed rows.
- `views/roles/reaction_panel.py` — a **🧹 Clean up** button (row 1) that prunes + reports + re-renders,
  and a build_embed hint ("⚠️ N binding(s) point to a deleted role — tap 🧹 Clean up") so the cruft is
  self-explanatory and one tap from gone. Root cause (concatenated-emoji creation) was already fixed by
  #1234; this clears existing dead rows.

Verify: `check_quality.py --full` + `check_architecture.py --mode strict`.
