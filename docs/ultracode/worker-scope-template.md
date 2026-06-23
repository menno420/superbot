# Ultracode — worker scope template

> **Status:** `reference` — the **paste-in worker prompt** a future Ultracode *coordinator* fills
> out per unit and hands to each Phase-1 worker agent. It encodes the
> [shared-dependency / ownership map](shared-dependency-ownership-map.md) § 2 unit-class contract +
> the [collision matrix](conflict-matrix.md) into one bounded prompt. Source + merged PRs win.
>
> Modeled on the per-agent templates already proven in
> [`ultracode-fleet-plan-2026-06-19.md`](../planning/ultracode-fleet-plan-2026-06-19.md) and
> [`consolidation-fleet-plan-2026-06-23.md`](../planning/consolidation-fleet-plan-2026-06-23.md) —
> generalized so it works for any fleet, not just one task.

---

## Coordinator pre-flight (run ONCE before dispatching the fleet)

The #1133/#1128 lesson — the claim ledger is necessary but **insufficient**:

```bash
# per lane scope, BEFORE spawning workers:
python3.10 scripts/check_lane_overlap.py <unit file globs...>
```
…and via GitHub MCP: `list_pull_requests(state=open)` **and** recently-merged — drop/re-scope any
unit whose files are already in flight or just shipped. Then build Phase 0 (the shared rails every
worker converges on) and confirm it is green on `main` before fan-out.

---

## The per-worker prompt (fill the `<...>` and paste)

```
You are ONE worker agent in a parallel Ultracode fleet. Read
docs/ultracode/shared-dependency-ownership-map.md first.

ASSIGNED UNIT: <unit name>  (parallel-safety rating: <green|yellow|orange>)
SECTOR / HUB:  <S1..S5 / parent hub or folio>

ALLOWED FILES (edit ONLY these — your exclusive set):
  - cogs/<x>_cog.py  (+ cogs/<x>/ if it exists)
  - views/<x>/
  - services/<x>_*.py   (your owned domain services only)
  - utils/<x>/ , utils/db/<x>.py , utils/settings_keys/<x>.py
  - tests/unit/**/<x>*    (your slice's mirrored tests, in the SAME PR)

READ-ONLY SHARED FILES (you may import/call, never edit):
  - views/base.py , views/navigation.py        (UI primitives)
  - services/economy_service.py / xp_service.py / game_xp_service.py /
    moderation_service.py / settings_mutation.py / audit_events.py   (call via their
    public signature; these are sole-writers — never inline a write)
  - utils/db/pool.py , utils/db/<other-table>.py   (read other tables, never write them)
  - core/runtime/*    (call the runtime contract; never change it)

FORBIDDEN (the held set — coordinator-owned; touching one is an automatic stop):
  - disbot/migrations/   (need a table? STOP and ask the coordinator for the next number)
  - views/base.py , views/navigation.py , utils/db/pool.py ,
    core/runtime/subsystem_schema.py , core/events.py , bot1.py , config.py ,
    utils/subsystem_registry.py , utils/hub_registry.py , views/hub_children.py ,
    governance/** , services/help_*.py , services/server_logging.py , services/settings_mutation.py
  - the `order` int of any message-pipeline stage (edit your stage's body only)
  - any OTHER unit's files ; the shared ledgers (current-state.md, current-state/*.md)
  - .claude/CLAUDE.md , .claude/settings.json   (owner-only, Q-0106)

ACTIVE GATES (do not cross): <e.g. AI feature-expansion gate / BTD6 gate / none>.
Off-limits always: ADR-001 (no Redis), ADR-002 (game state not restart-safe — don't "fix" it),
Q-0190 (no feature-gating monetization), services/→views/ imports (zero tolerance).

TASK: <the one specific change for this unit>.

RULES OF ENGAGEMENT:
  1. Claim your lane: create docs/owner/claims/<branch>.md (one bullet), delete it at close.
  2. Born-red session card: first commit creates .sessions/<date>-<slug>.md with
     `> **Status:** `in-progress``. LEAVE IT RED — the coordinator flips/merges (Phase 2).
  3. One unit = one PR. Do not widen scope past your ALLOWED FILES.
  4. Green before handoff (both must pass):
       python3.10 scripts/check_quality.py --full
       python3.10 scripts/check_architecture.py --mode strict
  5. Flag self-initiated work on the run-report ⚑ line (Q-0172).
  6. If a correct fix REQUIRES editing a FORBIDDEN file → STOP and report to the coordinator;
     do not work around the held set.

STOP CONDITIONS (surface to the coordinator instead of proceeding):
  - the fix needs a migration, or any held-set / cross-unit file;
  - your unit's rating is orange/red and the change touches the shared service, not just the cog;
  - the change is irreversible/external/owner-gated, or the goal is genuinely ambiguous.

OUTPUT:
  - the PR (born-red), green on both checks, scoped to ALLOWED FILES only;
  - a .sessions/ log with the Context-delta + run-report footer;
  - report your PR number to the coordinator and END (do not self-merge).
```

---

## Coordinator Phase-2 checklist (per worker PR)

- [ ] Diff touches **only** the unit's ALLOWED FILES (no held-set, no cross-unit leak).
- [ ] Both checks green **on the latest `main` head** (rebase/re-run if an earlier unit moved a
      shared-but-allowed file — should be none if the partition held).
- [ ] Fix any miss yourself (you are the convergence reviewer), then flip the session card to a ready
      token and merge. File-disjoint units merge in **any order**.
- [ ] After the fleet lands: reconcile `current-state.md` + the sector files, GC the claim files,
      and (if the run was a convergence refactor) graduate the relevant linter rule to `error`.
