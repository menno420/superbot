# Extension-taxonomy crosswalk + thin architecture atlas — plan

> **Status:** `plan` — cross-check source before extending. Born from the owner-uploaded
> architecture-atlas review ([capture](../ideas/architecture-atlas-and-structure-review-2026-06-16.md),
> PR #957) and the owner's **Q-0151** answer (2026-06-16: *"I agree with your recommendations, and the
> readme is not required but not off limits"*). PR 1 (the crosswalk) is **shipped** in this plan's own
> session; PR 2 (the atlas) is sequenced below.

## Why

The review's strongest genuinely-new finding: SuperBot loads **43** extensions but registers **33**
subsystems, and the **10** non-1:1 extensions had no role classification anywhere. The review's
flagship "per-file dashboard" was already ~80% shipped as `scripts/context_map.py`, so the additive
work is narrow: (1) classify the extensions, (2) optionally compose the scattered generators into one
provenance-stamped index.

## PR 1 — extension-type taxonomy crosswalk · SHIPPED (this session)

A read-only, CI-enforced crosswalk. **No runtime change.**

- **`architecture_rules/extension_roles.yaml`** — the curated editorial overlay. Classifies all 43
  extensions into one of 8 roles (`product_subsystem` · `hub` · `shared_platform` · `maintenance` ·
  `operational_adapter` · `bootstrap` · `specialized_surface` · `lab`) + the backing subsystem for the
  10 non-1:1 ones.
- **`scripts/extension_crosswalk.py`** — AST-joins `config.INITIAL_EXTENSIONS` +
  `subsystem_registry.SUBSYSTEMS` + the overlay. `--write` regenerates the doc; `--check` is the guard;
  bare run previews. No imports/env (CI-safe).
- **`docs/architecture/extension-taxonomy-crosswalk.md`** — generated, committed, `NOT SOURCE OF TRUTH` + provenance.
- **`tests/unit/scripts/test_extension_crosswalk.py`** — runs `--check` (the CI enforcement seam) +
  proves the guard catches an unclassified extension / a bad `backs`.

### Design decision: overlay, not a registry field (owner-approved)

My original Q-0151c phrasing suggested a `role` field on the subsystem registry (a
`REGISTRY_SCHEMA_VERSION` bump). **We chose the curated overlay instead** because:
1. A role like *bootstrap* / *operational_adapter* is a **human review label**, not runtime metadata —
   it must not bloat the deep-frozen registry that governance resolves against.
2. The 10 most-interesting extensions **have no registry entry at all** (that's the whole point), so a
   registry field couldn't classify them anyway.
3. Lower risk: the overlay + generator are disposable tooling (Q-0105); nothing in the bot runtime
   depends on them. This matches the review's own "small curated overlay for what you can't safely
   infer" recommendation.

The CI **enforcement** the owner asked for is delivered by the test running `--check` (every extension
must be classified), so "CI-enforced" is satisfied without touching runtime.

## PR 2 — thin unified atlas · SHIPPED (PR #960)

Built as planned: **`scripts/atlas.py`** (composer) + the down-payment **role line in
`scripts/context_map.py`** + the curated companion **[`docs/architecture/repo-atlas.md`](../architecture/repo-atlas.md)**
+ **`tests/unit/scripts/test_atlas.py`** (the coherence-guard enforcement seam). Body not committed
(Q-0151a); `--check` delegates classification to `extension_crosswalk.check()` and adds the
extension-file-exists + orphan smoke checks. Not CI-wired (ask-first, like `dispatch_menu`).

### Original PR 2 design (for reference)

The review's surviving second idea, as a **companion** to `AGENT_ORIENTATION.md` (owner's Q-0151a
choice — not a replacement; orientation stays the curated reading-order router). A thin
`scripts/atlas.py` that **composes the existing generators as libraries** (never re-implements them):
`context_map` (per-file role/imports/blast-radius/tests/docs), `wiring_map` (EventBus), `review_scope`
(review unit), and **this PR's role data** — into one repo-wide, provenance-stamped index.

- **Provenance:** unlike the crosswalk (committed → deterministic, no timestamp), the atlas index
  carries commit SHA + timestamp and is **CI-`--check` + on-demand generate, body NOT committed**
  (owner's Q-0151a choice) — so a volatile provenance header is fine and it adds no committed
  drift surface.
- **Dependency:** consumes PR 1's `role`/`backs` data, which is why it sequences after.
- **Reuse gate (do-not-duplicate):** must import `context_map` / `wiring_map` / `review_scope` as
  modules. If a needed fact isn't already produced by one of them, add it *there*, not in the atlas.
- **Overlap to resolve:** the agent context-pack system (`tools/agent_context/`) already produces
  per-area packs; the atlas is repo-wide and file-indexed. Confirm the two stay complementary (packs =
  curated per-area reading context; atlas = generated repo-wide fact index) before building.

## Out of scope / explicitly deferred
- **Root README** (Q-0151b) — owner: *not required but not off limits*. Optional 5-line pointer-only
  README if a public GitHub landing page is wanted later; otherwise the deliberate "no root README"
  posture (`repo-navigation-map.md`) stands. Not built here.
- **Boundary-debt burndown** (review Option B) — already ticketed in `architecture_rules/layers.yaml`
  (`arch-fix-11/13`); execution lane, tracked separately.
