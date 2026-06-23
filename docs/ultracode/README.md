# Ultracode — parallel-refactor coordination substrate

> **Status:** `reference` — the home for the **task-independent** map an Ultracode *coordinator*
> reads before dispatching a fleet of agents at a large parallel refactor, so workers don't make
> conflicting edits. It **operationalizes** [`repo-review-map.md`](../repo-review-map.md) (the
> review/refactor partition) by adding the parallel-safety dimension on top — it is **not** a
> competing taxonomy, **not** a path inventory, and **not** a refactor plan. Source + merged PRs win.

## What "Ultracode" is

One **coordinator** session spawns up to ~16 **worker** agents, each with a strict per-unit prompt,
checks their work, fixes misses, and merges at the end. That only preserves the architecture if three
things hold: **(1)** the shared pattern every worker converges on already exists (Phase 0), **(2)**
the work is partitioned into **file-disjoint** units so two workers never touch one file, and **(3)**
machine-checkable gates are the reviewer, not human attention. This directory is the durable map that
makes (2) decidable — *which units are file-disjoint, which surfaces are shared-held, and what the
touch policy is for each.*

The two proven task-specific runs — the
[2026-06-19 boundary-debt fleet](../planning/ultracode-fleet-plan-2026-06-19.md) and the
[2026-06-23 consolidation fleet](../planning/consolidation-fleet-plan-2026-06-23.md) — are *plans*
(dated, one-task rosters). This map is the **reference** they are instances of: it generalizes their
held set + rules-of-engagement + merge protocol so the *next* fleet, on any task, starts from a
verified partition instead of re-deriving one.

## The documents

| Doc | What it answers |
|---|---|
| **[shared-dependency-ownership-map.md](shared-dependency-ownership-map.md)** | The main map: status/trust model, the 6 unit classes + their contracts, the shared platform surfaces (held set, ranked by blast radius), the runtime wiring (events / pipeline / DB ownership / registries), and the **parallel-safety rating for all 54 cogs** (🟢/🟡/🟠/🔴). |
| **[conflict-matrix.md](conflict-matrix.md)** | The collision table: for each shared file/service/event/registry, who depends on it, the conflict type, who may edit it, and whether it must be serial. *"Can unit A and unit B run in parallel?"* |
| **[worker-scope-template.md](worker-scope-template.md)** | The paste-in worker prompt a coordinator fills per unit (allowed / read-only / forbidden files, gates, checks, stop conditions, born-red rule). |
| **[report-reconciliation-2026-06-23.md](report-reconciliation-2026-06-23.md)** | How the seeding ZIP-based verification report was checked against live source (Confirmed / Corrected / Stale / Unsupported / New). |

## The unit classes in one screen

| Class | Rating | Worker autonomy |
|---|---|---|
| Independent vertical slice | 🟢 green / 🟡 yellow | edits its own cog/views/service/db/tests; runs with a claim only (green) or claim + narrow scope (yellow) |
| Shared platform unit | 🔴 red | coordinator-owned; workers read-only (base views, runtime core, pool, registries, sole-writer services) |
| Serial migration / schema unit | 🔴 red | one migration at the coordinator-assigned number — collision is otherwise guaranteed |
| Tooling / docs unit | 🟢/🟡 | `scripts/` · `.github/` · `docs/` · `.claude/skills/` — file-disjoint from runtime |
| Blocked / gated unit | 🔴 red | do not dispatch (AI/BTD6 expansion gate, owner-gated product lanes, ADR off-limits) |
| Unsafe / unknown unit | ⚠️ | resolve the unknown (parametrized events, doc-lag) before rating |

**The one rule:** two agents must never edit the same file. Everything else is how to make that true.

## How this fits the existing maps (no competing taxonomy)

- **Paths** ("which folder?") → [`repo-navigation-map.md`](../repo-navigation-map.md).
- **Layering** ("may this import that?") → [`architecture.md`](../architecture.md).
- **Ownership** ("who writes this table/event?") → [`ownership.md`](../ownership.md).
- **Review/refactor unit** ("what's the self-contained unit for *this* change?") →
  [`repo-review-map.md`](../repo-review-map.md).
- **Parallel-refactor coordination** ("which units run in parallel; what's the touch policy?") →
  **this directory.** It is the operational extension of `repo-review-map.md`'s B-slice / B-platform
  distinction.

When this map and any of those disagree, **they win** — fix this map in the same PR.

## Before dispatching a fleet

This is a dated snapshot. Re-verify (map § "Reverify before an Ultracode run"): `list_pull_requests`
(open + merged) **and** `scripts/check_lane_overlap.py <scope>` per lane (the claim ledger alone is
insufficient — #1133/#1128), `scripts/wiring_map.py --check`, and that no new migration moved the
next free number.
