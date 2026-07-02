# New-bot capability audit — the fleet substrate

> **Status:** `reference`. Prepared 2026-07-02 as the shared foundation for a multi-agent audit that
> **maps, reconsiders, simulates, optimizes, and ecosystem-benchmarks every capability intended for the
> new bot** — so the rebuild is durable *and* the repo becomes a rich reference corpus the next bot can
> draw from. The new-bot-capability-audit pass is its technical spine. Read [`BRIEF.md`](./BRIEF.md) first.

## The mandate (owner, 2026-07-02) — three axes, five verbs

Every capability meant for the new bot gets **MAP → RECONSIDER → SIMULATE → OPTIMIZE → BENCHMARK**, across:

- **Axis 1 — what we have** (43 subsystems) → reconsider + optimize (Lanes A–D)
- **Axis 2 — what we planned** (`docs/planning/` + `docs/ideas/`) → reconsider for the new bot (Lane E)
- **Axis 3 — what the ecosystem has that we don't** (known Discord bots) → catalog + document (Lane F)

The durability question ("can the §2 grammar express it all?") is the spine; the goal is the **capability
corpus** — is it optimal, what's missing, what should the next bot be.

## The pipeline

```
   [PREP — this dir]                 [FLEET — 6 lanes]                        [CAPSTONE]
   ground truth + contract    A–D  Axis 1  2× Opus + 1× Sonnet ultracode
   + partition + scaffolds ─► E    Axis 2  Codex/Opus (plans/ideas)      ─►  final Fable 5:
   + handoff prompts          F    Axis 3  deep-research (ecosystem)          verdict + corpus/roadmap
```

1. **PREP (this directory).** Ground-truth dumps, the shared mandate/method/schema contract, the
   partition, per-lane scaffolds (Axis-1 surface inventories pre-extracted), and copy-paste
   [handoff prompts](./HANDOFF-PROMPTS.md) for every session.
2. **FLEET.** Six lanes (see [`PARTITION.md`](./PARTITION.md)): A–D audit the shipped subsystems, E the
   planned/ideated surface, F benchmarks against known bots. Each writes its lane file / findings.
3. **CAPSTONE.** A final Fable 5 session ([`FINAL-REVIEW-HANDOFF.md`](./FINAL-REVIEW-HANDOFF.md)) verifies
   the findings against source, rules the grammar **GO / GO-with-amendments / NO-GO**, and produces the
   **prioritized new-bot capability roadmap** (keep/improve/merge/drop/add + deferred known-options).

## Files

| File | What |
|---|---|
| [`BRIEF.md`](./BRIEF.md) | The binding contract: the 3-axis mandate, method, per-capability schema, guardrails, exit bar. |
| [`PARTITION.md`](./PARTITION.md) | 43 subsystems × Lanes A–D + E (plans/ideas) + F (ecosystem) + G (L0 foundations) + model→lane. |
| [`HANDOFF-PROMPTS.md`](./HANDOFF-PROMPTS.md) | Copy-paste startup prompts for all 7 lanes + the capstone. |
| [`FINAL-REVIEW-HANDOFF.md`](./FINAL-REVIEW-HANDOFF.md) | Startup context for the capstone Fable 5 review. |
| `ground-truth/command-surface.json` | All 271 commands (name/aliases/kind/perm/cog/line). |
| `ground-truth/subsystems.json` | The 43 subsystems + capabilities/entry_points/hub. |
| Axis-1 lanes: [`A`](./lanes/lane-A-governance.md) · [`B`](./lanes/lane-B-economy.md) · [`C`](./lanes/lane-C-games.md) · [`D`](./lanes/lane-D-knowledge-platform.md) | **Pre-filled** surface inventories (271 units extracted), judgment columns blank — the fleet completes them. |
| [`lanes/lane-E-plans-ideas.md`](./lanes/lane-E-plans-ideas.md) | Axis-2 forward-capability ledger (Lane E agent fills). |
| [`lanes/lane-G-foundations.md`](./lanes/lane-G-foundations.md) | **L0** foundations / runtime-skeleton audit (Lane G agent fills). |
| [`findings/`](./findings/README.md) | Lane F ecosystem benchmark + the capstone's `FINAL-REVIEW.md` + `NEW-BOT-BUILD-PLAN.md`. |

## Why this shape (the lessons baked in)

- **Extract mechanically, judge with agents.** Ground-truth inventories are a script/scaffold job; the
  fleet spends its budget on reconsider/optimize/benchmark, not re-deriving facts.
- **One schema so N reviews compose, not overlap.** Every lane (any provider) fills the same shape →
  the capstone merges instead of reconciling divergent prose.
- **Provider diversity as verification.** The capstone verifies cross-agent verdicts against source
  (Q-0120) — the spike already caught cross-agent maps mis-reading source 4×.
- **Disjoint lanes.** Axis-1 lanes are file-disjoint by subsystem; E and F are cross-cutting research
  lanes that reference A–D.

This extends [`../codex-preserve-map-synthesis-2026-07-02.md`](../codex-preserve-map-synthesis-2026-07-02.md)
(the structural preserve-map) with its grammar-expressiveness + optimization + ecosystem layers, and the
[grammar spike](../../../../tools/grammar_spike/RESULTS.md) (3 subsystems → all 43 + planned + ecosystem).
