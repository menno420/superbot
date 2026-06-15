# Mining Phase 2 — Forge / Vault / Home structures + skill-tree wiring

> **Status:** `in-progress`
> **PR opens:** docs-only session declaration.
> **Followed by:** a dispatched build/verify slice to Claude Code.

## Why this now

PR 884 shipped the Vault stash slice and the turn-key structures/skill-tree plan.
This PR is the **next concrete slice** — the Forge/Vault/Home structures + skill-tree
wiring the plan calls "V16 Phase2" (owner asset paths + anchor tuning).

## Planned scope

1. Forge / Vault / Home projection — owner asset paths + anchor tuning.
2. Skill-tree wiring onto the existing `game_xp` substrate.
3. Smoke tests + docs update for the new slice.

## Non-goals

No new data model migrations. No UI rewrite.
