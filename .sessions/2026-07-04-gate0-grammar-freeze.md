# 2026-07-04 — Gate-0 grammar-freeze + Phase-B L0 build-order

> **Status:** `in-progress`

**About to do:** Execute the Gate-0 grammar-freeze brief
(`docs/planning/rebuild-gate0-grammar-freeze-opus-brief-2026-07-04.md`) — a CONSOLIDATE + RATIFY +
PLAN session (docs/spec only, no code). Six deliverables landing under
`docs/analysis/rebuild-discovery/foundations/gate-0/`:

1. **The frozen L0 grammar** — fold all 87 pinned primitives (18 attach-point groups) into one
   authoritative manifest-grammar spec, each field verified against its owning spec's §3 (Q-0120).
2. **The amendment registry** (prerequisite, built first) — `rebuild-amendments.yml` + uniqueness
   checker; enumerate G-9…G-24 collision-free.
3. **Close the pending cross-spec wiring** — `ActorRef.member_tier` (RC-12), spec-02 absorption of
   04's authority contracts (RC-2/3/4/5/12/13/14/15), `WorkflowContext.test_mode` (07),
   `ChannelEmitter` egress port (RC-21).
4. **Resolve the register** — freeze the 19 RATIFY-DEFAULT rows; render the 12 OWNER-ONLY rows + L-21
   into an owner-decision packet.
5. **Design the L-24 presentation riders** to buildable depth — alt_text, locale seam,
   allowed_mentions policy, ModalSpec (G-10), bundled fonts.
6. **The Phase-B L0 build-order plan** — the 16-step sequence (S0–S15).

Plus: front-matter README; mark the ratified/retired rows in the design/ question-register +
retirement-coverage-map (V-3 continuity).

**Method:** grounded from the harvested work-list (`docs/planning/rebuild-gate0-worklist-2026-07-04.md`);
orchestrated via a Gate-0 consolidation workflow (amendment registry first → per-group fold →
specialized deliverables → adversarial-completeness critic → ratification-readiness pass).
Consolidate + ratify, never redesign; owner-only rows rendered, never decided (source wins, Q-0120).

<!-- Close-out (arc / shipped / findings / Context delta / run report / telemetry) written as the
     deliberate final step; badge flips to `complete` last. -->
