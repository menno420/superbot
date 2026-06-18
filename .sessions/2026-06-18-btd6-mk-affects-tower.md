# 2026-06-18 — BTD6 "which MK affects <tower>" — class-wide MK + routing

> **Status:** `complete`
> Owner-live follow-up to #1035/#1037. Two real misses from new #general screenshots.

**PR:** #1038 — list class-wide MK + fix the sniper routing miss.
**Branch:** `claude/zen-wright-77q0ru` (reset onto main after #1037 merged).

## What I'm about to do / did

The owner posted new screenshots: the improved glue-gunner MK reply (from #1035) still
"fails to correctly mention the MK that affects the glue gunner," and "Which MK affects the
sniper" got **refused**. Both verified at source.

### 1. Content — list the class-wide MK that affect the tower
The #1035 reply only listed name-matching MK and pointed at the tab. The owner wants the
tab-wide points that actually affect the tower (Come On Everybody!) *listed*. Added
`btd6_data_service.monkey_knowledge_class_wide(category)` — MK in the tower's class tab whose
description carries an explicit **class-scope phrase** ("all Primary towers", "Military
Monkeys"). This is deliberately stricter than "names no tower": that looser test wrongly
caught tower-specific points the name index missed (Icy Chill → Ice Monkey, Charged Chinooks →
Heli) and power/economy points (Targeted Pineapples, More Cash). The reply now has two labelled
sections — "Names the <tower>" + "Class-wide <Tab> — buffs every <Tab> tower" — and is framed
"Monkey Knowledge that affects the <tower>".
  - Glue Gunner → 6 named + Come On Everybody! (Primary class-wide).
  - Sniper → 3 named + Advanced Logistics / Elite Military Training / Military Conscription.

### 2. Routing — "which MK affects the sniper" was refused
Root cause: the task router classified it `GENERAL_NL_ANSWER`, so the deterministic MK floor
(which only runs on the `BTD6_ANSWER` route) was skipped → the model answered → the grounding
guard blocked it → refusal. Single-word tower aliases (`sniper`, `boomerang`, `glue`) are
deliberately dropped from the entity matcher as too collision-prone, so only multi-word names
("glue gunner", "sniper monkey") routed BTD6. Added `_looks_like_mk_tower_question`: an MK cue
(`monkey knowledge`/`mk`) + a tower alias (including the dropped single-word ones, ≥4 chars)
routes BTD6. The MK cue gates it, so "is mk11 a good game" / "do you like the sniper rifle in
cod" stay GENERAL.

Also reconciled the living ledger (#1037).

## Verification

- `python3.10 scripts/check_quality.py --full` → green (10498 passed, 38 skipped).
- `python3.10 scripts/check_architecture.py --mode strict` → 0 errors.
- New tests: `test_btd6_mk_reference` (class-wide relation + reply sections + honest-empty),
  `test_ai_task_router_btd6_natural` (MK-tower routing + conservatism).

## 💡 Session idea

**Idea:** a small router↔floor parity check — for each deterministic BTD6 floor builder, assert a
representative trigger phrase also classifies `BTD6_ANSWER` (so the floor is actually reachable).
**Why:** this exact bug was a *routing/floor mismatch* — the floor fired when called directly but
the router never sent the message to it. A parity test catches "floor exists but is unreachable"
as a class, which the existing floor-exclusivity test (which calls builders directly) can't see.

## ⟲ Previous-session review

The #1035 fix (tab-note disclosure) was a half-measure: it *explained* the omission rather than
*fixing* it, and it never questioned whether the question even reached the floor — so the sniper
routing miss sat undiscovered until the owner re-tested. The lesson (captured as the session
idea): when a deterministic floor "isn't answering," check **reachability** (does the router send
it there?) before assuming the builder is wrong — a builder that passes its own unit test can
still be dead on the live path. Codex (#1037) and the owner (this PR) are jointly doing the
independent-reviewer job the system intends.

## 📤 Run report

- **Did:** listed class-wide MK in the "affects <tower>" answer + fixed the single-word-alias MK
  routing miss + ledger reconcile · **Outcome:** shipped, CI green
- **Run type:** manual (owner-live)
- **⚑ Self-initiated:** none (owner-reported misses; ledger reconcile is on-sight)
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none (no data reseed — pure code/grounding/routing)
- **↪ Next:** optional router↔floor reachability parity test (session idea)
