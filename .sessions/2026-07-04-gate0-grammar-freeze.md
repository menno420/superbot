# 2026-07-04 — Gate-0 grammar-freeze + Phase-B L0 build-order

> **Status:** `complete`

## Arc

Executed the owner-directed Gate-0 grammar-freeze brief
(`docs/planning/rebuild-gate0-grammar-freeze-opus-brief-2026-07-04.md`) — a CONSOLIDATE + RATIFY + PLAN
session (docs/spec only, no code). Orchestrated a fan-out workflow (amendment registry first → 17
per-group fold agents + 5 specialized deliverable agents → grammar assembly → a 6-lens
adversarial-completeness + ratification-readiness critic with a fix round → V-3 continuity), then
closed the surviving critic gaps by hand against source (Q-0120). Landed the six deliverables + the
front-matter README under `docs/analysis/rebuild-discovery/foundations/gate-0/`.

## Shipped (PR #1716)

- **`gate-0/frozen-l0-grammar.md`** — 87 primitives across 18 attach-point groups folded into one
  manifest-grammar spec, every field verified against its owning spec §3 (6 mis-cites corrected).
- **`gate-0/amendment-registry.md`** + **`docs/planning/rebuild-amendments.yml`** — the collision-free
  minting authority (G-1…G-24); this fold flips **G-10 `ModalFormSpec` → in-spec**, the rest stay
  `pending-gate-0`.
- **`gate-0/cross-spec-wiring.md`** — the four pending absorptions closed (`ActorRef.member_tier` RC-12,
  the spec-02 absorption of 04's authority contracts RC-2/3/4/5/13/14/15, `WorkflowContext.test_mode`,
  `ChannelEmitter` egress-port RC-21).
- **`gate-0/register-resolution.md`** (19 RATIFY-DEFAULT frozen) + **`gate-0/owner-decision-packet.md`**
  (12 OWNER-ONLY + L-21 rendered owner-consumable, data-loss four grouped up top).
- **`gate-0/l24-presentation-riders.md`** (alt_text · locale seam · allowed_mentions × TrustLevel ·
  ModalSpec/G-10 · bundled fonts) + **`gate-0/phase-b-l0-build-order.md`** (16 steps S0–S15).
- **`gate-0/README.md`** — the owner's front-matter entry point.
- Continuity: `design/question-register.md` + `design/retirement-coverage-map.md` Gate-0-disposition
  appends (V-3, 0 evaporations) + a `design/README.md` §6 "EXECUTED" pointer.

## Findings

- **6 mis-cites corrected against source (Q-0120)** — the load-bearing ones: `WorkflowContext.test_mode`
  owner is spec **07 §3.2**, not "06 §12" (06 only flags the seam); the `PredicateRef` registered-form
  JSON shape is owned by shared-vocab §7.4, not spec 02 (which under-specifies it as prose).
- **The critic caught a Q-0120 false-green in the amendment checker itself**: `G-10`'s `spec_ref`
  pointed at a non-existent path (`gate-0/L-24-riders`), and `check_amendments._resolves` false-greened
  it (its regex matched an incidental "§6"). Corrected the ref to the resolvable `l24-presentation-riders.md §4`.
- **Buildability gaps closed by hand** (round-2 ratification-readiness): the D-5 `essential` tag had no
  concrete type → pinned `essential: bool = False`; `ChannelEmitter.send` returned an undefined
  `EmitResult` → pinned `EmitResult{delivered, error_class, reason}` reusing the frozen `outcomes.py`
  leaf; the dense verdict dataclasses (`AuthorityDecision`/`ChannelAccessDecision`), `ConfigSpec`,
  `mirrors`, `cooldown` were folded as field-name sets → decomposed to full typed shapes from source.
- **check_docs badge trip** — two agents invented non-canonical badges (`owner-consumable`, `frozen`);
  corrected to `reference`. All checks green after.

## Context delta

- **Needed but not pointed to.** The exact per-field *types* of the dense spec dataclasses
  (`AuthorityDecision`, `ChannelAccessDecision`, `ConfigSpec`, …) live only inside the strand specs'
  fenced code blocks (e.g. 04 §3.3 lines 173–183) — nothing summarizes them. The work-list Part-1 rows
  carried the *field-name set* but not the typed shape, so the fold reproduced name-lists and I had to
  re-type them against the source code blocks. A per-spec "dataclass field-shape index" would have
  routed this directly.
- **Pointed to but didn't need.** design-spec §9 (the K0–K10 build order) and the 14 specs' §11 were
  near-redundant confirmation — the work-list Part 3 already carried the grounded 16-step sequence; the
  specs were a spot-verify, not a primary read.
- **Discovered by hand.** The `check_docs` badge allowlist (`archive/audit/binding/historical/ideas/
  living-ledger/owner-guidance/plan/reference` only — `frozen`/`owner-consumable` are NOT valid) is
  discoverable only by running the checker or reading its source; doc-authoring agents don't know it up
  front.
- **Decisions made alone.** (a) pinned `essential: bool = False` over a `tags: frozenset[str]` (14 §2.A
  defines exactly one tag); (b) pinned `EmitResult` as a distinct minimal envelope over the outcomes
  leaf rather than reusing the dispatch `Result`; (c) pinned `mirrors: str = ""`, `cooldown:
  CooldownSpec | None = None`; (d) flipped **only G-10** in-spec (the L-24 `ModalSpec`), left
  G-9/G-11…G-24 `pending-gate-0`; (e) homed the four wiring closures in `cross-spec-wiring.md` and kept
  the 14 strand specs frozen (no rewrite). All are source-faithful consolidation defaults, not owner
  rulings — but the owner should consciously ratify (d) especially (whether ModalSpec is "designed" or
  still pending).
- **Flagged for maintainer.** The register does not fully close until the owner rules the **12
  owner-only rows + L-21** (`owner-decision-packet.md`). The `IntentPosture=DEGRADE` default stays
  owner-pending (F-3/PG-2, `required=True` floor holds). The G-10 in-spec flip is the one judgment call
  that could reasonably revert if the owner considers `ModalSpec` still design-pending.
- **One docs/tooling change that would have most helped.** A pre-write badge validator (or a documented
  allowed-badge list in the doc-authoring guidance) — so agents pick a valid `check_docs` badge the
  first time instead of tripping the strict check.

## 💡 Session idea (Q-0089)

**A "spec field-shape index" generator** — a small tool that extracts every `@dataclass`/enum field
shape (name · type · default) from the design specs' fenced code blocks into a per-spec typed index.
*Why I believe in it:* the entire Gate-0 fold, and every downstream Phase-B builder, re-derives
dataclass shapes from spec code blocks by hand; a harvested typed index turns that into a lookup and
kills the exact name-list-not-typed gap that cost this session a re-typing pass. Distinct from the
existing work-list (which summarizes to field-name sets). Dedup-checked `docs/ideas/` + roadmap — no
existing entry. Log-recorded here; promote to a `docs/ideas/` file in the next grooming pass (kept out
of this PR to stay Gate-0-focused).

## ⟲ Previous-session review (Q-0102)

The prep session (#1713) produced the Gate-0 brief + the grounded work-list. **Did well:** the
per-`## GROUP N` anchoring with per-field type/default/role/retires made the fold a *verify-not-
rediscover* task — exactly the leverage the brief intended, and the reason 38 agents ran with 0 errors.
**Could improve:** the harvest summarized dense dataclasses to *field-name sets* (`{allowed, lane, …}`)
rather than typed shapes, which propagated into the fold and required a post-hoc re-typing pass against
source. **System improvement it surfaces:** a harvest that touches a spec dataclass should preserve the
*typed* field shape, not just the name set — the "spec field-shape index" idea above is the concrete
form. This is the internal mirror of the independent-reviewer loop: each session sharpening the tooling
the next inherits.

## 🛠 Friction → guard

1. **Workflow parse error** (a missing `)` closing `parallel(` cost two failed launches) → **guard
   shipped this session (technique):** validate the workflow script with `node --check` wrapped in an
   `async function` stub *before* invoking Workflow (catches top-level-return-legal-but-brace-wrong).
   Reusable; recorded here for the next orchestration session.
2. **Invalid-badge trip** (agents wrote `frozen`/`owner-consumable`) → the *enforcing* guard already
   exists (`check_docs --strict` fails on it, and it caught this pre-push). The residual friction is
   agents not knowing the allowed set up front — a **docs-authoring** note (free to ship) rather than a
   new checker; folded into the Context-delta "one change" above for a future grooming pass.

## Gates / state

- **No code, no runtime surface** — docs/spec only; the fresh-repo `sb/` package does not exist.
- **Owner-gated, not decided here:** the 12 owner-only rows + L-21; the `IntentPosture=DEGRADE` default
  (F-3/PG-2). Rendered, never ruled.
- Verification: `check_docs --strict` ✓, `check_quality --check-only` ✓ (docs/consistency/artifacts),
  `check_current_state_ledger --strict` ✓ (6 newer PRs = benign lag), `rebuild-amendments.yml` parses ✓.

## 📤 Run report

- **Did:** Executed the Gate-0 grammar-freeze — consolidated the 14 foundational-design specs into one
  frozen L0 grammar + amendment registry + owner packet + 16-step L0 build order. · **Outcome:** shipped
- **Shipped:** #1716 — 7 gate-0 deliverables + `rebuild-amendments.yml` + 2 design/ continuity appends + a README pointer
- **Run type:** `manual` (owner-directed brief dispatch)
- **⚑ Owner decisions needed:** the **12 OWNER-ONLY register rows + L-21** in
  `gate-0/owner-decision-packet.md` (the Gate-0 ratification sitting) — load-bearing: **Q-D5** (intent
  DEGRADE vs fail-closed, F-3/PG-2), **Q-D8/13/14/15** (data-loss), **Q-D16/17/18/20** (narrow bindings
  Q-0213/Q-0105/Q-0233). Plus a light confirm on the **G-10 `ModalFormSpec` in-spec flip**.
- **⚑ Owner manual steps:** none (docs-only; no deploy, no data step)
- **⚑ Self-initiated:** none (owner-directed brief; every pin was within the dispatched consolidation scope)
- **↪ Next:** the owner's Gate-0 ratification sitting (rule the 12 + L-21) → the deferred new-repo
  bootstrap → the Phase-B L0 build against the frozen grammar; Stage-2 runs in parallel against the frozen contracts.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (PR #1716 — auto-merges on green) |
| CI-red rounds | 0 real (born-red session gate is by-design; the badge trip was caught locally pre-push) |
| Repo-rule trips | 1 (check_docs badge allowlist — caught locally, fixed) |
| New ideas contributed | 1 (spec field-shape index generator) |
| Ideas groomed | 0 (single large owner-directed deliverable; grooming deferred with note) |
