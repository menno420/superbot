# 2026-06-23 — Ultracode shared-dependency / ownership map

> **Status:** `complete` — the durable parallel-safety map is shipped (PR #1374), verified, and the
> seeding report reconciled. Born-red → flipped as the deliberate final step (Q-0133).

> **Run type:** `manual` (owner-directed session prompt; "ultracode" mapping request)

## Arc — what shipped

Created **`docs/ultracode/`** — the task-independent map an Ultracode *coordinator* reads before
dispatching a parallel refactor fleet, so workers don't collide. It **operationalizes**
`repo-review-map.md` (Axis B: B-slice vs B-platform) with a parallel-safety rating + held-set touch
policy; it is **not** a competing taxonomy and **not** a path inventory (links to the existing homes).
Mapping + verification + docs only — no refactor, no runtime code moved.

- `shared-dependency-ownership-map.md` — status/trust model, the 6 unit classes + contracts, the
  shared platform surfaces (held set **ranked by blast radius**: migrations · `views/base.py` 145 ·
  `utils/db/pool.py` 64 · `subsystem_schema.py` 51 · `navigation.py` 42 · EventBus 36 · `SUBSYSTEMS`
  29 · `config.py` load-order · `bot1.py` · governance), the runtime wiring (27 events / 10 pipeline
  stages / sole-writer DB ownership / registries), and the **parallel-safety rating for all 54 cogs**.
- `conflict-matrix.md` — the collision table (structural surfaces, mutation paths, registry routes,
  event contracts, clusters, in-flight overlaps).
- `worker-scope-template.md` — the paste-in per-worker prompt (allowed / read-only / forbidden files,
  gates, checks, stop conditions, born-red rule) + coordinator pre-flight + Phase-2 checklist.
- `report-reconciliation-2026-06-23.md` — Confirmed / Corrected / Stale / Unsupported / New verdict on
  the seeding ZIP-based report.
- `README.md` — entry point + unit-class contracts.
- Backlinks: `AGENT_ORIENTATION.md` (reading-route row 7b), `repo-review-map.md` (Relationship §),
  `repo-navigation-map.md` (header).

**Method:** four read-only mapping agents (source topology · shared platform · runtime/ownership/DB
wiring · docs/current-state/backlinks) over live source; coordinator (this session) synthesized + was
the only doc editor.

**Report reconciliation headline:** all file counts **exact** except `architecture_rules` (5→**7**);
held-set logic + sole-writer ownership + the `audit.action_recorded` invisible coupling **confirmed**;
subsystem inventory **stale 36→54 cogs** (41 registered); `active-work.md` + `needs-hermes-review`
**retired** (Q-0195/Q-0197) so the map states the current truth; governance dual-home **resolved**
(`disbot/governance/` impl + `services/governance_service.py` shim).

## Decisions made alone (ratify if you disagree)

1. **Created `docs/ultracode/` as a new docs subdirectory** rather than folding the map into
   `repo-review-map.md` or the dated planning fleet docs. Rationale: it's a durable `reference` (the
   fleet plans are dated `plan`s — different lifecycle), matches existing "ultracode" naming, and keeps
   `repo-review-map.md` focused. Reversible (a directory + backlinks). Matches the prompt's preferred
   shape.
2. **Rated all 54 cogs 🟢/🟡/🟠/🔴** — a coordinator's *starting partition*, explicitly marked not a
   guarantee (a worker that widens scope downgrades its own rating).
3. **Did NOT fully reconcile the stale cheat-sheet / `ownership.md` tables this session** — flagged as a
   follow-up (and captured as an idea) to keep scope contained and avoid a half-done edit in another
   doc's home.

## Context delta

- **Needed but not pointed to:** (a) the two prior fleet plans
  (`planning/ultracode-fleet-plan-2026-06-19.md`, `consolidation-fleet-plan-2026-06-23.md`) — found by
  grepping `docs/` for "ultracode|fleet", not via any orientation route (there was no "parallel
  refactor" route until I added row 7b). (b) **EventBus lives at `disbot/core/events.py`**, not
  `core/runtime/event_bus.py` — the report guessed wrong and no doc states the path crisply. (c) the
  `repo-navigation-map.md` cheat-sheet table is the per-subsystem path home **but is stale**.
- **Pointed to but didn't need:** `docs/codegraph-usage.md` (orientation step 4) — for a
  mapping/docs session, `git ls-files` + `scripts/context_map.py` + `scripts/wiring_map.py` carried the
  verification; CodeGraph's symbol tools weren't load-bearing here.
- **Discovered by hand:** the **governance dual-home** (`disbot/governance/` is the impl;
  `services/governance_service.py` is a thin legacy re-export shim — no doc states the relationship);
  `resolution.py` is actually `resolver.py`; the **10 message-pipeline stage orders** (only in the
  module docstring + per-cog `*_STAGE_ORDER` constants); the **18-cog inventory drift** + the
  `ownership.md` table lag for the 5 newer subsystems.

## 💡 Session idea (Q-0089)

**`check_subsystem_inventory_homed` — a warn-first ratchet guard** asserting every `*_cog.py` /
`SUBSYSTEMS` key is present in the canonical inventory + `ownership.md` tables (the proven 3-file shape:
script + ratchet test + exceptions yml). It closes the exact drift this session hit — 18 shipped cogs
missing from the cheat-sheet table, 5 sole-writer services missing from `ownership.md` — **at the
root**, instead of waiting for a reconciliation pass to notice. Genuinely distinct from
`check_docs._INVENTORY_COUNT_RE` (count-only) and `new_subsystem.py`'s checker (loader/role gaps).
Captured: [`ideas/subsystem-inventory-homed-guard-2026-06-23.md`](../docs/ideas/subsystem-inventory-homed-guard-2026-06-23.md).

## ⟲ Previous-session review (Q-0102)

**Previous: the Phase-0 completion session (#1371, `phase0-completion.md`).** What it did well: it
correctly *split shipped vs specced honestly* — it shipped `discover_hub_children` + the consolidation
fleet plan, but **refused to ship a no-op settings-orphan guard** when it found
`build_catalogue(None)` is blind offline, spec-ing the turn-key approach instead. That discipline
(don't ship an inaccurate guard to look complete) is exactly the bar the consolidation audit is
enforcing — a strong predecessor. What it could have done better: its fleet plan's "never edit
`active-work.md`" line was **already stale** (Q-0195 retired it the day before) — a reminder that even
a same-week plan inherits drift; my map corrects it. **System improvement it surfaces (initiated, not
asked):** the previous session itself proposed codifying the "new guard = script + ratchet test +
exceptions yml" 3-file shape as a `/new-guard` skill. My session independently hit the *same* pattern
(my Q-0089 idea is precisely that 3-file shape). **Two sessions converging on the same skill is the
signal to build it** — a `/new-guard` skill would have made both the settings-orphan guard and my
inventory guard fill-in-the-blanks. Worth promoting from "idea" to a `.claude/skills/` slice next time
a guard is built (owner-gated for the skill file; the pattern itself is free to template).

## 📋 Doc audit (Q-0104)

Everything from this session is in a durable home: the 5 ultracode docs (committed, reachable —
`check_docs --strict` ✓, the README is a reachability root + links every sibling); the backlinks in the
3 structural reading-route docs; the verified drift list in the reconciliation doc § 2–3 + map § 7; the
new idea + grooming cross-link in `docs/ideas/`. **No new owner *decision*** (the session executed the
owner's mapping prompt; the one structural default — `docs/ultracode/` — is logged above for
ratification), so **no router entry owed**. Reconciliation marker untouched (no merged-PR ledger edit;
this PR is folded by the next pass). `check_current_state_ledger --strict` ✓ · `check_docs --strict` ✓
· 70 docs-pin tests ✓. Deliberately did **not** edit the volatile sector ledgers (S1/S4) — the map is
discoverable via the structural docs; a ledger pointer would be restatement drift (one-fact-one-home).

## 🛠 Friction → guard

The four mapping agents independently re-derived the **same 54-vs-36 cog count + the stale inventory
tables** — i.e. the repo had no machine guard that a shipped cog is homed in its inventory docs, so the
drift was invisible until a human-scale mapping pass found it. **Guard shipped this session:** the
drift is now captured as a concrete buildable guard idea (`subsystem-inventory-homed-guard`) + an
enumerated verified delta (reconciliation doc) + a grooming convergence note tying it to the
`new-subsystem-followup-tracker` idea (one tooling slice satisfies both). The guard *script* itself is
the buildable follow-up; this session shipped the durable capture + evidence so it can't evaporate.

## 📤 Run report

- **Did:** created the durable `docs/ultracode/` shared-dependency / ownership map + reconciled the
  seeding ZIP-based report against live source · **Outcome:** shipped
- **Shipped:** #1374 — ultracode parallel-safety map (5 docs) + 3 discoverability backlinks
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none (the structural default `docs/ultracode/` is logged under
  "Decisions made alone" for optional ratification — not a blocker)
- **⚑ Owner manual steps:** none (docs-only; a merge auto-deploys but changes no runtime)
- **⚑ Self-initiated:** none — the map was the owner-directed prompt; the Q-0089 idea + Q-0015 grooming
  are standing session enders, not unprompted builds
- **↪ Next:** reconcile the two lagging inventory tables (`ownership.md` + the `repo-navigation-map.md`
  cheat-sheet) using the verified 18-cog / 5-service delta in the reconciliation doc § 2–3 — a
  docs-only slice; *or* dispatch the consolidation fleet (U1 AI-panel / U2 roles) using the new map +
  worker-scope template.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1374 — auto-merge armed, merges on green) |
| CI-red rounds | 0 real (the born-red session gate is by-design, not a failure; `check_docs --strict` passed first try) |
| Repo-rule trips | 0 (arch N/A — docs-only) |
| New ideas contributed | 1 (`subsystem-inventory-homed-guard`) |
| Ideas groomed | 1 (`new-subsystem-followup-tracker` — cross-linked + advanced with verified evidence) |
