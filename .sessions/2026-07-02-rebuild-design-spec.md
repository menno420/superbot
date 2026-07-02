# 2026-07-02 — Rebuild design spec: the "one picture" (docs-only, owner-gate deliverable)

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed · ultracode.
> Docs-only (no `disbot/` code); `check_docs --strict` ✓, ledger ✓ (benign newest-merge lag only). PR #1635.
> Scope: **the Phase-2 rebuild DESIGN SPEC** — the owner-gate deliverable before any Phase-3 new-repo code.

**Branch:** `claude/superbot-rebuild-design-spec-de4mh7`

## What I'm about to do (intentions — as declared born-red)

Produce the comprehensive from-scratch rebuild **design spec** for SuperBot at
`docs/planning/rebuild-design-spec-2026-07-02.md`, grounded in the verified preserve map
(`codex-preserve-map-synthesis-2026-07-02.md`, §1 corrections binding) + the strategy + the
simulation-driven-design standing rule, via a judge-panel multi-agent workflow, honoring the three
binding constraints (ActionSpec rename · extend-not-recreate shipped types · §5 backward-compat).

## What shipped

**[`docs/planning/rebuild-design-spec-2026-07-02.md`](../docs/planning/rebuild-design-spec-2026-07-02.md)**
(~15,900 words, sections 0–10) — the one picture:

- **Architecture (§1):** `sb/` kernel-engines + manifest-declared domains; no hand-written views/cogs
  layers; a layer table with two zero-tolerance rules (kernel never imports domains; `kernel/ai` never
  imports upward — the `gateway.py:51` break class dies at the root by relocating misfiled
  `services/metrics.py` to `kernel/observability`); complexity budget; lazy-import ban.
- **Manifest grammar (§2):** field-level specs for all core primitives, **extending the shipped types
  verbatim-field-first**; every field classified **semantic / arrangement / objective** so the
  simulator's write surface is machine-derived; hybrid format (Python frozen dataclasses → canonical
  JSON snapshot → sim-owned layout lock overlays); the escape-hatch three-tier regime; the six-part
  simulability contract (incl. the arrangement-invariance CI test and the encoded sim-gate thresholds).
- **Central namespace (§3):** declaring-is-reserving over a **derived** index (two-phase: import-local
  → CI incl. merge-tree → boot pre-connect), `legacy_reservations.json` as the machine-readable
  backward-compat core, tombstones (bare `ActionSpec`), the `g1:` versioned dynamic custom-id scheme,
  and the AST symbol-shadowing companion (kills Q-0211/BUG-0030/Q-0200 structurally).
- **Settings model (§4):** `SettingSpec` as the only declaration path (no public raw-KV API); the
  four-valued `activation` axis reconciling **safe-default-ON** with no-silent-auto-create and the
  image-moderation opt-in gate (compiler-forced `off_until_opt_in` on `external_side_effects`, itself
  verified by an egress-reachability check); AI's typed policy folded in; KV→binding route-truth +
  alias map.
- **Data + compat (§5):** fresh migration chain + one-time importer with owner-reviewed dry-run
  reconciliation (carry-the-chain specified as the trip-wired fallback); explicit disposition of all
  nine §5 hazard classes.
- **Control plane (§6):** rulesets + OIDC from day one; six named required gates incl. `golden-parity`
  (red-until-parity, one-way green) and `check_compat_frozen` (owner-sign-off amendments).
- **Docs (§7):** regenerated binding docs, provenance-separated, ≤7,000-word orientation budget with a
  checker. **All ten open questions decided (§8)**; K0–K10 kernel order + seven-band port order + the
  first three simulator passes (§9); risks + the explicit owner-ratification list (§10).

**Supporting doc homing:** planning README index entry (top of the rebuild table) · handoff §D marked
✅ RAN with pointer + **new §E paste-ready external full-tier review prompt** · strategy §3 Phase-2
marked produced · vision-idea lifecycle pointer → owner gate · current-state S3 ▶ owner-gate item ·
**Q-0166 drift-fix**: correction note added to the preserve-map synthesis (its 3 own citation errors,
source-verified: pipeline paths, EventBus home, and its PARTIAL-3 verdict being itself wrong —
the governance event trio IS subscribed at `core/runtime/__init__.py:181–183`).

## Method + verification (the judge panel)

One `Workflow` run (`wf_54816468-d48`, 13 agents, ~2.2M tokens, ~92 min): **4 independent designs**
(clean-slate-ideal / minimal-migration-risk / manifest-grammar-maximal on Fable 5 + unconstrained
Opus 4.8) → **independent judges** (constraint-compliance + coherence/simulability lenses scored;
the Opus migration-risk judge died on a StructuredOutput retry cap — its lens was re-covered by the
review round) → **Fable synthesis** → **4-reviewer adversarial round**: Opus 4.8 `max` · mechanical
§5 compat verifier · simulability red-team · **a live non-Claude review via the OpenAI API
(`gpt-5.4-mini` — strongest available to this key; §E hands the owner a full-tier prompt)** →
reviser re-verified **all 24 findings against live source** and applied them (2 blockers: ADMIN-floor
scope over-extension → the two-lane authority model; sim/`parent_hub` custom-id hazard → hub-keyed
frozen routing constants). I then independently re-verified the load-bearing claims myself before
installing (pipeline paths, EventBus, governance subscribers, the 8 `ai:*` custom_ids, migration 032's
CHECK at :87–88, 43 `SUBSYSTEMS` keys at :58, `metrics.py:18`, `visibility_rules.py:21`) — all ✓.

## Context delta

- **The judge panel earns its cost on owner-gate deliverables.** The adversarial round found 2
  genuine blockers the (already excellent) synthesis would have shipped — including one that would
  have let a simulator rewrite compat-frozen custom_ids. For this deliverable class, review depth is
  not optional polish.
- **The evidence docs themselves had verified errors** (3 citation errors + 1 wrong verification
  verdict in the preserve-map synthesis). Q-0120 discipline — re-verify against source at every hop,
  including *your own briefing materials* — is what caught them.
- **A non-Claude review is actually runnable in-session:** `OPENAI_API_KEY` is present in agent
  containers and works through the proxy; only mini-tier models are available to this key
  (`gpt-5.4-mini`), so the full-tier external pass stays an owner step (handoff §E).
- **Graceful degradation matters in orchestration:** losing 1 of 3 judges did not sink the run
  because the review round independently re-covered the lost lens; design fan-outs should always
  have a later stage able to absorb an earlier stage's casualty.

## 🛠 Friction → guard

Two frictions, both already covered by existing guard classes — no new hook/CI needed, one proposal:
(1) the judge death was a harness-level StructuredOutput retry cap (outside repo control; mitigated
by lens overlap, noted in the session idea); (2) the briefing-doc citation drift was caught by the
Q-0120 verify-at-every-hop discipline and is now fixed at the source doc (correction note). Proposal
routed via the ⟲ improvement below rather than a new checker: verification passes should record the
exact command per verdict, making re-verification one paste.

## 💡 Session idea (Q-0089)

**[`judge-panel-as-saved-workflow-2026-07-02.md`](../docs/ideas/judge-panel-as-saved-workflow-2026-07-02.md)**
— encode this session's proven judge-panel method (forced-diverse designs + cross-model design →
lens-diverse judges → synthesis → multi-lens adversarial review incl. the live GPT leg →
source-verifying reviser) as one saved, parameterized workflow, so every future owner-gate-grade
deliverable (Phase-3 spine designs, harness architecture) reuses it instead of re-authoring ~200
lines of orchestration. Worth having because the method demonstrably beat single-pass synthesis
*this session* (2 blockers caught) and the harness quirks (graceful judge loss, schema-forced
outputs, OpenAI leg through the proxy) are now known-good and shouldn't be re-discovered.

## ⟲ Previous-session review (Q-0102)

Previous session (#1634, substrate-kit-planning-review): **excellent** — its 4-agent Q-0120
verification of the Codex maps (48/59 confirmed, corrections made binding) is precisely what made
this session's evidence trustworthy enough to design from; the fold into one synthesis doc was the
right call. What it missed: it introduced three citation errors of its own (mutation-pipeline paths
attributed to `settings_mutation.py`, EventBus placed at `utils/events.py`) and one verification
verdict that was itself wrong (PARTIAL-3: the governance event trio *is* subscribed) — errors in the
*verifier's* output, the exact class Q-0120 warns about, caught here only because every hop
re-verified. **Concrete system improvement:** verification passes should stamp each verdict with the
exact command used (`grep -n "bus.on" core/runtime/__init__.py`-style provenance), so the next
session re-runs the check in seconds instead of re-deriving it — a one-line convention for
verification fleets, and a candidate substrate-kit template convention (fits strategy §5.3's
"provenance-separate-from-rule").

## 📤 Run report

- **Did:** produced the Phase-2 rebuild design spec via a Fable-5 judge-panel workflow + homed all
  rebuild-thread docs to point at it · **Outcome:** shipped
- **Shipped:** #1635 — `rebuild-design-spec-2026-07-02.md` + index/pointer updates + synthesis-doc
  correction note + session idea
- **Run type:** `manual` (owner-directed, ultracode)
- **⚑ Owner decisions needed:** **THE owner gate** — approve
  [`rebuild-design-spec-2026-07-02.md`](../docs/planning/rebuild-design-spec-2026-07-02.md)
  (§10.2 lists exactly what approval ratifies; §10.1 the risks). Optional first: run the handoff §E
  external full-tier review prompt in Codex/ChatGPT.
- **⚑ Owner manual steps:** none mechanical (the gate is a decision; §E is optional)
- **⚑ Self-initiated:** none (owner-directed task; the idea file is capture, not a build)
- **↪ Next:** the owner gate blocks Phase 3; meanwhile Phases 0 / 0.5 / 1 / 2.5 stay agent-buildable
  (see current-state S3 ▶ — Phase 0.5 golden-harness + telemetry capture is the highest-value
  parallel start).
