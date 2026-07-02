# Simulation-driven design — structure is discovered, not decided (2026-07-02)

> **Status:** `plan` — **owner-directed standing rule** (owner, in-session, 2026-07-02; this doc is the
> provenance). Feeds the Phase-2 rebuild design and is a candidate **portable substrate-kit capability**.
> Companion to [`fresh-rebuild-strategy-2026-07-02.md`](fresh-rebuild-strategy-2026-07-02.md) §4.

## The rule

Any design decision with **(a) a combinatorial arrangement** and **(b) a measurable objective** —
*grouping, ordering, layout* — is decided by running it through a **simulator that searches the space
and returns the empirically-best arrangement**, not by intuition or an agent "just deciding." This is a
**standing, first-class step** for every existing and new feature, gated by a *sim-reviewed-or-exempt*
check before the feature is called done — not an occasional trick.

**Origin — already proven in-repo** (this generalizes three one-offs into a rule):
- The **BTD6 menu-layout simulator** (#1617 — owner picked Layout B off it).
- The **reaction-roles slim-builder layout-sim** (#1612/#1613/#1615 — after the 14-button builder felt dense).
- `tools/sim/claim_layout_sim.py` — measured **98% vs 0% conflict** and *decided* the per-file claim architecture.

## Why the rebuild unlocks it (the manifest synergy)

The rule is only cheap when structure is **declarative data**. The rebuild's manifest grammar
(Panel/Action/Setting/Binding/… specs — strategy §4/§6.1) makes panels, commands, and settings *data*,
so a simulator can reorder/regroup and score candidates mechanically. **The manifest is the search
space; the simulator is the search.** Hand-coded structure can't be optimized this way; a manifest can.
Design-by-simulation and the manifest grammar are two halves of one mechanism — so **the manifest must
be designed *to be simulated over* from day one** (a Phase-2 design requirement).

## Guardrails (the rule fails without these)

1. **Trigger threshold.** Simulate decisions with a *real* combinatorial space + measurable objective
   (a 12-button hub, a 40-setting group, the module tree). Not a 2-button panel. The rule must state
   *when* it applies, or it drowns everything in ceremony.
2. **Explicit, data-grounded objective — the hard part.** A simulator is only as good as its cost
   function; a *guessed* objective produces a **confidently-wrong** layout. Ground the weights in real
   signal (usage frequency, co-occurrence, the call graph), not vibes. **This is the one way it fails.**
3. **Keep the simulator.** It operates on the manifest, so it's re-runnable; when a feature changes,
   *re-optimize* instead of re-guess. This is what makes it a standing practice, not a one-off.
4. **Deterministic + auditable.** The sim is deterministic and records *why* the winning arrangement
   won (matches the repo's observability/auditability principle).

## Per-domain mechanisms

| Domain | The sim optimizes | Objective (minimize) | Engine status |
|---|---|---|---|
| **Buttons / panels** | row & sub-panel layout under Discord's 5-row / 25-component cap | clicks-to-action + group cohesion + safe destructive placement | ✅ **built** (BTD6 Layout B; reaction-roles slim builder) |
| **Commands** | hub/category grouping + help order + names | navigation depth + semantic cohesion + **zero collisions** | ⚙️ manifest-driven; the namespace guard is the collision half |
| **Settings** | settings-hub grouping + order + primary-vs-advanced | co-edit distance + dependency order + edit frequency | ⚙️ manifest-driven (feeds off the harvest settings model) |
| **File ordering** | module/dir clustering — where code lives | cross-boundary coupling ↓ / cohesion ↑, within the layer rules | ✅ **engine exists** — CodeGraph community detection |
| **AI answers** | info ordering/grouping in a response | reader cost (lead-with-the-outcome) + fact grouping | ⚙️ eval-driven (`evals/` corpus); fuzzier, rubric-scored |
| *(general)* | any arrangement with a measurable objective | the stated objective | build when the trigger threshold is met |

## File-ordering simulator — already has an answer today

CodeGraph community detection on the call/import graph **is** the file-ordering simulator's engine, and
it already reports **`drift: 48%` / `modularity: 0.4712` / 2148 communities** in every session-start
banner — i.e. the current file grouping is ~48% off the graph-optimal clustering. `mcp__codegraph__communities`
gives the per-module detail (which files' graph-community disagrees with their directory). **This is the
rule working today with zero new tooling** — the file-ordering pass can run first, as the proof of concept.

## Where it lives

- **Phase-2 rebuild design:** a core principle + a **sim-reviewed-or-exempt gate** before a feature is
  done; the manifest grammar designed to be simulated over.
- **Portable substrate-kit capability:** the kit ships the design-simulator scaffold + the rule — same
  "the memory system discovers the right structure" family as the namespace-guard and golden-harness
  (strategy §5.3).
- **Current repo:** an owner-directed rule (this doc is the provenance; for binding-`CLAUDE.md` promotion
  it would still be routed as a rule proposal per the working agreement).

## Next

- Fold into the **Phase-2 design brief** as a core requirement (manifest designed to be simulated over).
- Build the per-domain simulators as the manifest grammar lands (buttons/commands/settings from the
  manifest; AI-answers from the eval corpus).
- Run the **file-ordering sim** (CodeGraph communities) as the first concrete pass — the engine exists.
