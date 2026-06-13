# 2026-06-13 — Hardening P0-3 settings pointer-lane convergence (foundation)

> **Status:** `complete`

**PR:** #777 (`claude/vigilant-noether-sgtduq`) — opened ready at first push.
**Band:** the carried hardening spine's slot 7 (the safety/community band 4–6 closed
last session). P0-3 = settings pointer-lane convergence + Setup authority.

## Context

Continuation prompt: "continue where the last session ended." #775 (welcome/counters)
closed the safety/community band; the live band-queue item was **P0-3 settings
convergence** (Q-0098 answered → unblocked). Open-PR check first: #771 (stale parallel
ledger PR — its #765/#767/#769 entries are already in main), #766 (ideas), #704 (owner
screenshots) — none claimed the lane.

## The key framing — foundation PR, not the full retirement

The settings readiness map's "Recommended next session" is explicit: a **docs + tests
planning session without immediately changing production behavior**. Pointer *retirement*
(deleting editable scalar pointers) is genuinely risky — it needs binding-first reads +
migration + rollback proven first. So this session shipped the **foundation slice** (the
contained, behavior-preserving parts) + the plan that sequences the risky arc PRs.

## What shipped (behavior-preserving)

1. **Root-cause backfill fix** (`services/binding_backfill.py`) — the map's High "Required
   #2": the governance trusted/moderator role pointers targeted a `(governance, *)` binding
   with **no schema home** (`governance` is a *reserved* capability namespace, not a feature
   subsystem — minting one trips the identity-contract validator), so every guild got a
   permanent `BLOCKED_NO_SCHEMA`. **Reframed**: split honest `MIGRATED_KEYS` (xp, economy —
   homed) from new `DEFERRED_KEYS` (governance roles — home TBD). Added `moderator_tier_role_id`
   for symmetry. Arbitration already falls back to legacy for an UNRESOLVED binding → zero
   runtime change. Updated the 3 backfill tests that codified the old broken 3-key state.
2. **Two parity invariants** (P1-3, the "stays-fixed" layer):
   - `test_backfill_target_declaration_parity` — migrated targets are declared bindings
     (kind-matched); deferred targets are not (forces graduation when homed); no key in both.
   - `test_pointer_lane_ledger` — **the ratchet**: every channel/role pointer setting is in
     exactly one ledger bucket; a NEW unledgered pointer fails CI.
3. **`scripts/settings_lane_matrix.py`** — the map's rec-#1 machine-readable lane inventory
   (settings/bindings/resources/backfill/arbitration reads + pointer disposition; `--json`).
   Ground truth: **65 settings / 17 bindings** (the dated map said 36/13).
4. **Plan** (`docs/planning/settings-pointer-lane-convergence-plan-2026-06-13.md`) — the four
   pointer-family migration order, the **delegated-Setup apply contract** (Q-0098 — a bounded
   `setup_delegate` non-escalating actor_type + AST fence + audit, designed against the real
   `can_apply_setup` vs `actor_holds_capability` floor mismatch), the smoke checklist, arc
   sequencing.
5. **Router Q-0119 (OPEN)** — where the governance role-pointer bindings live
   (reserved-schema path / re-home under moderation / permanent exception). Recommend (a).

## Verification

`check_quality --full` green (9303 passed, 34 skipped) · `check_architecture --mode strict`
0 errors · `check_docs --strict` clean. The black↔ruff COM812 dance bit the Write-created
script again (the hook fixes Edits, not Writes) — ruff `--fix` + black settled it; plus an
ERA001 false-positive on a tuple-shaped comment (reworded to prose).

## 💡 Session idea (Q-0089)

**Readiness/audit maps should cite a regeneration command, not freeze inventory counts.**
The matrix tool revealed the settings readiness map — **one day old** — was already wrong on
its headline numbers (claimed 36 settings / 13 bindings; reality is 65 / 17, because #774
logging + #775 welcome/counters landed after the audit). Every `production-readiness/*` map
embeds frozen counts that rot the moment a feature ships, yet agents read them as ground
truth. Idea: a convention (enforceable by a `check_docs` soft rule) that audit/readiness docs
which state an inventory count must reference the `scripts/*_matrix.py` (or
`command_surface_dump.py`) regeneration command beside it, so the count is *citable + 
reproducible* rather than a silent lie. This is the "source-wins / one-fact-one-home"
principle applied to the readiness maps themselves — the class of doc most prone to fast rot.
Captured fresh as [`ideas/readiness-maps-cite-regen-command-2026-06-13.md`](../docs/ideas/readiness-maps-cite-regen-command-2026-06-13.md)
(dedup-grepped `docs/ideas/` — no existing capture).

## ⟲ Previous-session review (Q-0102) — welcome v1 + server counters (#775)

**Did well:** the hub-less new-subsystem call was genuinely well-reasoned — it correctly saw
that the Community hub renders *every* `parent_hub=="community"` child with no tier filter, so
parenting admin-config features there would dump operator config into the user hub, and chose
hub-less + Help-hook discoverability instead. It ran `new_subsystem.py check` and caught the
whole cascade; 65 tests; live boot verified. Solid, careful work.

**Missed / could improve (verified, not a guess):** it stored five Discord channel/role IDs
(`welcome.channel`, `welcome.entry_role`, `counters.{total,humans,bots}_channel`) as **scalar
`SettingSpec`s with `input_hint="channel"/"role"`** — not as `BindingSpec`s. That re-introduces
the exact pointer-in-the-wrong-lane anti-pattern the P0-3 hardening track exists to fix, adding
**five new orphan pointers** to the lane debt in a single PR. It went unnoticed because there
was no guard at authoring or CI time — `new_subsystem.py check` validates the registry cascade
but says nothing about the binding-vs-scalar lane choice for a resource pointer.

**Concrete system improvement (initiated here):** I built `test_pointer_lane_ledger` this
session — the CI ratchet that now **fails if a new channel/role pointer-as-scalar is added
without being ledgered**, so the #775 recurrence is caught automatically. The forward idea
above (regen-cited maps) is distinct; the *next* natural step is the authoring-time version —
a PostToolUse nudge on schema files that flags `input_hint="channel"/"role"` and points at the
binding lane (noted in the plan as a follow-up, not built here).

## Docs audit (Q-0104)

`check_current_state_ledger --strict` — will be clean once #777 merges (entry added; the
Recently-shipped ratchet sits at 20/20). `check_docs --strict` clean (the plan is reachable
from the hardening roadmap + settings map; Q-0119 routed). New owner-relevant item: **Q-0119**
recorded in the router (OPEN — the only new decision surfaced; Q-0098 was already answered).
No reconciliation pass due (next at #780; #777 < #780). The convergence plan is the durable
home for the migration order + delegated-apply design + smoke checklist — nothing important
left only in chat.
