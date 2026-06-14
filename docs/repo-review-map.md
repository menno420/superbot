# SuperBot — Repo Review Map

> **Status:** `reference` — the **review/refactor partition** of the repo: how the
> codebase is divided into independently reviewable units so that, as the bot grows,
> each section stays manageable to review and refactor on its own.
>
> Companion to three path/contract docs — **don't duplicate them, partition over them**:
> - [`repo-navigation-map.md`](repo-navigation-map.md) — *where* code lives (path → purpose).
> - [`architecture.md`](architecture.md) — *layering* and invariants.
> - [`ownership.md`](ownership.md) — *who owns* each table/service/event.
>
> This file answers a different question than those: **"for a given change, what is
> the smallest self-contained unit I can review or refactor without dragging the rest
> of the repo in?"** Source code, merged PRs, and the three docs above win over this one.

---

## Why this exists

The codebase is large enough that "review the change" no longer has an obvious scope.
A reviewer needs to know, up front, **which bounded unit a change belongs to** and
**which contracts bound it** — so a review can be complete without reading the whole
tree, and a refactor can stay inside one unit instead of rippling everywhere.

This map was finalized from a maintainer proposal that grouped the repo into five
buckets (core bot · game data+scripts · infra/config · docs/agent · tests). That
five-way *coarse* partition is kept below as **Axis A**. But the coarse partition alone
puts all of `disbot/` (36 cog entry points, 141 services, six layers) into one bucket —
which is exactly the region that's hard to review as a blob. So the real foundation is
**Axis B**: inside the bot, the unit of independent review is the **vertical subsystem
slice**, and shared platform layers are reviewed against their layer contracts. The two
axes compose: Axis A tells you *which domain* a file is in; Axis B tells you *which
review unit* a bot change is.

---

## Axis A — Repo domains (coarse, top-level)

Every path in the repo belongs to exactly one domain. Use this to answer "what *kind*
of thing am I touching?" and "who is the natural reviewer?".

| # | Domain | Contains | Reviewer lens | Bounding contracts |
|---|---|---|---|---|
| **A1** | **Bot runtime** | `disbot/` — `bot1.py`, `config.py`, `guild_lifecycle.py`, `healthserver.py`, and the layers `assets/ cogs/ core/ data/ governance/ migrations/ services/ utils/ views/` | Does it run correctly in production? Layer boundaries held? | [`architecture.md`](architecture.md), [`ownership.md`](ownership.md), [`runtime_contracts.md`](runtime_contracts.md), `architecture_rules/*.yaml` |
| **A2** | **BTD6 data pipeline** | The *offline* half of BTD6: `scripts/{parse_gamedata,parse_bloonswiki,fetch_btd6_wiki_data,fetch_bloonswiki,explore_gamedata,btd6_gamedata_inventory,btd6_decode_inventory_report,btd6_patch_diff,btd6_probe,import_btd6_data_from_csv,seed_btd6_data,upload_btd6_data,gen_gear_placeholder_sprites}.py` + `data/btd6/` (CSVs) | Data fidelity / provenance; offline, never serves traffic | [`subsystems/btd6.md`](subsystems/btd6.md), [`decisions/006-btd6-data-provenance-ownership.md`](decisions/006-btd6-data-provenance-ownership.md) |
| **A3** | **Dev / CI / agent tooling** | `scripts/{check_architecture,check_docs,check_quality,context_map,wiring_map,new_subsystem,run_evals,setup_dev_env,claude_*}` + `tools/agent_context/` + `architecture_rules/` + root config (`pyproject.toml`, `requirements*.txt`, `.pre-commit-config.yaml`, `.python-version`, `Procfile`, `.mcp.json`, `.github/workflows/`) | Does the toolchain still enforce/scaffold/deploy correctly? | [`context-map-tooling.md`](context-map-tooling.md), `.claude/CLAUDE.md` § CI parity / CodeGraph, [`operations/production-deployment.md`](operations/production-deployment.md) |
| **A4** | **Docs & agent system** | `docs/` (incl. `docs/agent/` context compiler) + `.claude/` (CLAUDE.md, rules, skills, agents) + `.session-journal*.md` + `.sessions/` | Is it accurate, findable, non-duplicating? Reachable per `check_docs`? | [`AGENT_ORIENTATION.md`](AGENT_ORIENTATION.md), [`collaboration-model.md`](collaboration-model.md), `.claude/rules/context-compiler.md` |
| **A5** | **Tests** *(mirror axis, not a silo)* | `tests/` — `unit/` mirrors `disbot/`, plus `evals/` and `fixtures/` | Coverage of the unit under review | [`smoke-test-checklist.md`](smoke-test-checklist.md), `tests/unit/docs/` (doc-pins) |

**Two corrections to the original proposal, applied above and load-bearing:**

- **BTD6 is split across A1 and A2 on purpose.** Its *runtime* surface — `cogs/btd6_cog.py`,
  `btd6_events_cog`, `btd6_ops_cog`, `btd6_reference_cog`, `btd6_strategy_cog`,
  `paragon_cog`, `views/btd6/`, `services/btd6_ai_service.py`, and `utils/db/btd6_*.py` —
  lives in A1 and is reviewed as bot subsystems (Axis B). Only the *offline extraction/seed*
  scripts + raw CSVs are A2. Conflating the two (as "Game Data & Scripts") would put live
  command handlers in the same review bucket as a one-shot CSV parser.
- **A5 (tests) is a mirror, not an independent group.** A subsystem's tests are reviewed
  **with that subsystem** (Axis B), because `tests/unit/<area>/` deliberately mirrors the
  source tree. Listing tests as a standalone review group would split a change from its
  own coverage. `run_evals.py` is tooling (A3); the eval *cases* under `tests/evals/` are A5.

`disbot/data/` (static JSON like `general_content.json`) stays in **A1** — it is loaded by
the running bot and travels with its consuming subsystem slice, not with the A2 pipeline.

---

## Axis B — Review units inside the bot runtime (the actual foundation)

A1 is too big to review as one block. Inside it, there are exactly **two kinds of review
unit**. Every `disbot/` change is one or the other (occasionally both — see "mixed changes").

### B-slice — the vertical subsystem slice *(the default unit)*

A **slice** is one subsystem's full vertical: its cog entry point, private package, view
package, owning service/mutation path, DB module, mirrored tests, and any static data it
reads. This is what "independently manageable and reviewable" means in practice — a slice
can be reviewed and refactored on its own because the architecture forbids it from reaching
sideways into another slice (no cross-cog imports; cross-subsystem effects go through the
EventBus or a shared service).

A slice's exact paths are already enumerated — **do not restate them here**:

- The per-subsystem path set (cog · view package · service/mutation · DB module) is the
  **cheat sheet** in [`repo-navigation-map.md`](repo-navigation-map.md) § "Subsystem cheat sheet".
- For the seven areas with a **folio** ([`subsystems/`](subsystems/README.md)), the folio is
  the slice's review home: scope, binding rules, current state, and next candidates on one page.
- Ownership of each slice's tables/events is [`ownership.md`](ownership.md).

**Reviewing a B-slice change — the unit is self-contained if:**
1. It stays within that subsystem's `cogs/<name>*`, `views/<name>/`, owning service, and DB module.
2. It introduces no cross-cog import (`check_architecture.py` catches these).
3. All mutations go through the domain's audited `*_service.py` / `*_mutation.py` seam.
4. Its tests under `tests/unit/<area>/` move with it in the same PR.

### B-platform — the shared platform layers *(reviewed against layer contracts)*

Changes to code that *many* slices depend on are **not** slice-local and carry a higher
review bar. These are the shared layers, each its own review unit:

| Platform unit | Path | Review bar |
|---|---|---|
| Runtime core | `disbot/core/runtime/` (EventBus, session/panel managers, interaction_router, tasks, persistent_views, identity contract) | [`runtime_contracts.md`](runtime_contracts.md) — all sections; must not import cogs/services |
| Resources core | `disbot/core/resources/` | [`runtime_contracts.md`](runtime_contracts.md) |
| Governance | `disbot/governance/` | [`ownership.md`](ownership.md) INV-E; strict internal layer order |
| Shared utils / DB layer | `disbot/utils/` (esp. `utils/db/`, `settings_keys/`, the registries) | [`helper-policy.md`](helper-policy.md); `utils/db/` may import asyncpg only |
| Shared view primitives | `disbot/views/base.py`, `views/navigation.py`, `views/selectors/` | [`architecture.md`](architecture.md) view rules; no parallel nav/base module |
| Entry & lifecycle | `bot1.py`, `config.py`, `guild_lifecycle.py`, `healthserver.py`, `migrations/` | [`repo-navigation-map.md`](repo-navigation-map.md) entry rows; no subsystem logic here |

A B-platform change should be reviewed for **blast radius** (how many slices it touches),
not just local correctness — use `python3.10 scripts/context_map.py <file>` to see importers
before reviewing or refactoring one of these.

### Per-subsystem readiness maps (the first applied output)

The B-slice review unit has a concrete deliverable per area: a
**production-readiness map** that inventories the slice (cog · views · service · DB ·
migrations · external seams) and marks each item Done / Partial / Not Done with evidence.
The full set lives at
[`planning/production-readiness/`](planning/production-readiness/README.md) — one map per
subsystem, each linked from its [folio](subsystems/README.md). Open a slice's map for
*what's left*; open its folio for *the rules*.

---

## How to scope a review or refactor (decision guide)

```
What does the change touch?
├─ One subsystem's cog/views/service/db (+ its tests/data)  → B-slice. Review against the
│     subsystem's folio + cheat-sheet row. Stays in one slice = self-contained.
├─ core/ · governance/ · utils/ · views/base.py · entry files → B-platform. Review against
│     the layer contract + run context_map.py for blast radius. Higher bar.
├─ Offline BTD6 extraction/seed scripts or data/btd6 CSVs    → A2. Data-fidelity review;
│     no runtime impact until a seed/deploy step runs.
├─ scripts/check_* · tools/ · architecture_rules · CI · root config → A3. Toolchain review.
└─ docs/ · .claude/ · journal/sessions                       → A4. Accuracy + reachability.
```

Refactor corollary: **keep the slice the seam.** A refactor that has to reach across two
B-slices is a signal to route through the EventBus or a shared service instead — that keeps
both slices independently reviewable. A refactor that touches B-platform is a cross-cutting
change: scope it as its own PR, separate from any single slice's work.

---

## Relationship to the existing docs (no competing taxonomy)

This map is a **partition over** the existing structure, not a replacement for it:

- **Path lookup** ("which folder?") → [`repo-navigation-map.md`](repo-navigation-map.md).
- **Layering / invariants** ("may this import that?") → [`architecture.md`](architecture.md).
- **Ownership** ("who writes this table/event?") → [`ownership.md`](ownership.md).
- **Per-area working context** ("I'm building in area X") → [`subsystems/`](subsystems/README.md) folio.
- **Planning / roadmap scoping** ("what standing **sector** + horizon is this, and where's its live
  queue?") → [`repo-sector-map.md`](repo-sector-map.md) (the **S1–S5 planning sectors**) +
  [`roadmap.md`](roadmap.md) (the per-sector queues). **This is a different taxonomy from the one
  below** — *planning* coarsens *review*. The S→A mapping (S1↔A1-minus-BTD6, S2↔A1-BTD6+A2,
  S3↔A3, S4↔A4, S5↔A3-config+live-state) lives in `repo-sector-map.md` § "Two taxonomies"; route by
  the **question you're asking** (planning a roadmap → sector; scoping a PR review → review unit).
- **Review/refactor scoping** ("what's the self-contained unit for *this* change?") → **this file.**

When this file and any of those disagree, they win — and fix this file in the same PR.

---

## Updating this file

Update when the *partition* changes, not when individual files move:

- A new top-level repo directory appears → add/extend an Axis A row.
- A new shared platform layer is created (new `core/` or `utils/` sub-package many slices use) → add a B-platform row.
- The slice boundary changes (a subsystem is split, or cross-cutting wiring replaces a slice seam).

Do **not** update for: a new file inside an existing slice, a new command in an existing cog,
or a new individual doc/test. Those are covered by the navigation map and the folios.

When a change here touches the *partition* (a new top-level directory, a new standing body of work),
check whether it also shifts a **planning sector** in [`repo-sector-map.md`](repo-sector-map.md) — keep
the two maps' S↔A correspondence consistent so they don't grow into competing taxonomies.
