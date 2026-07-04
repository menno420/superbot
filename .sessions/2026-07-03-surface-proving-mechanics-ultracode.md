# 2026-07-03 — Surface + proving foundations audit (PROMPT B, ultracode)

> **Status:** `complete` — PR #1691. Ran PROMPT B of the foundational-mechanics ultracode brief
> (`docs/planning/rebuild-foundational-mechanics-ultracode-brief-2026-07-03.md`, owner ruling
> Q-0236) — a **docs-only** brainstorm/audit of the **presentation/UX + verification** foundation of
> the SuperBot rebuild. No `disbot/` code, no bot launch. A parallel session ran PROMPT A
> (runtime/logic).

## What shipped (PR #1691)

1. **The deliverable** —
   [`docs/analysis/rebuild-discovery/foundations/presentation-verification-mechanics-2026-07-03.md`](../docs/analysis/rebuild-discovery/foundations/presentation-verification-mechanics-2026-07-03.md):
   - **46 mechanics** audited (the 12 named in the brief — hub topology, navigation engine, panel
     rendering, card engine, media generation, presets+template primitive, help projection, result
     grammar, "did you mean" rendering, the critical-review rubric itself, the correctness oracle,
     the layout-success simulator — **+ 34 surfaced by the completeness loop**). Each entry:
     how-now (with `file:line`) · options considered (2–3 alternatives from leading bots/frameworks
     + a pressure-test of our decision) · recommendation · handoff seam to Session A.
   - **220 verified issues** scored by the 10-class critical-review rubric (dominant classes:
     `verification-hole` 48, `ux-contract-gap` 48, `missing-standard` 32, `forgotten-capability`
     26), a synthesis-ranked top-42 ledger + a full per-mechanic ledger, and **87 owner-gated flags
     (surfaced, not decided)** — 14 distilled decision prompts at the top.
   - **Headline finding:** the presentation foundation is **engine-rich, grammar-thin, oracle-empty**
     — most render *engines* already ship (stronger than the plan assumes), but the declarative
     *grammar* the rebuild is named after (CardTemplateSpec, WorkflowResult render, one-description
     manifest, template=named-draft) is undesigned, and the *proving* half (oracles) is absent in
     nearly every mechanic. Top three owner gates: restart-safe Back-path storage (blocks 4
     mechanics); the hide-vs-disable contract collision (plan's "hidden=off" reverses shipped
     Q-0055/HLP-4); the admin/moderation gating model (shipped bot *hides* admin — opposite of the
     decided visible-gated node).
   - **Method:** an ultracode **workflow** — one finder per mechanic → **adversarial-verify vs
     shipped source** (Q-0120; it caught a finder that emitted placeholder output and reconstructed
     the real analysis) → completeness-critic loop (3 lenses, to its round cap) → synthesis.
     **108 subagents · 195 CONFIRMED + 25 REVISED − 3 REJECTED · ~9.0M tokens · 2,276 tool calls.**
     2 mechanics lost to a schema-retry-cap failure (noted honestly in the appendix, no silent
     truncation).
2. **Reachability + provenance:** linked the deliverable (and a placeholder for Session A's report)
   from the brief's new "Deliverables" section; `check_docs --strict` green.
3. **Session idea** (Q-0089): `docs/ideas/ultracode-audit-consolidation-stage-2026-07-03.md` +
   README index entry.

## ⚑ Self-initiated

None beyond the assigned task. The work was owner-directed (Q-0236, PROMPT B verbatim); the one new
idea (consolidation stage) is a *capture*, not a self-initiated implementation. All owner-gated calls
in the report are **flagged, not decided**, per the brief.

## 💡 Session idea (Q-0089)

**A consolidation/dedup stage for the ultracode multi-agent audit pattern** —
[`docs/ideas/ultracode-audit-consolidation-stage-2026-07-03.md`](../docs/ideas/ultracode-audit-consolidation-stage-2026-07-03.md).
Directly observed this session: the completeness-critic loop grew the inventory to 46 mechanics but
its only dedup was exact-name matching, so several genuine near-duplicates slipped through (e.g.
`live-view-timeout` ≈ `graceful-component-expiry`; three framings of the nav-reachability oracle) and
the synthesis had to untangle them by hand. The idea adds the completeness-critic's **missing twin** —
a semantic-cluster *consolidation* stage between the loop and synthesis ("what did we say twice?" vs
"what did we forget?") — so the inventory (and its headline count) is honest by construction and the
loop can terminate on "nothing *semantically* new" instead of "no new *name*." Reusable for any
fan-out→completeness workflow; worth folding into the brief's shared method.

## ⟲ Previous-session review (Q-0102)

**Reviewed:** `.sessions/2026-07-03-foundational-mechanics-ultracode-brief.md` (PR #1688) — my direct
predecessor, which *prepared* the very brief I executed.

- **Did well:** a genuinely parallel-safe two-session design — disjoint scope with an explicit
  boundary in each prompt, own claim files, own report files, own PRs — held perfectly under real
  parallel execution (zero collision with Session A). Web-researching what an ultracode/workflow
  session can actually do *before* writing the prompts made both prompts encode a real quality
  pattern (fan-out → adversarial-verify → completeness-loop → synthesize) rather than a vague "go
  audit." The shared-method paragraph transferred cleanly into a runnable workflow.
- **What it missed / the concrete system improvement:** the brief's shared method specified the
  *completeness* half of the loop but not its dual — **consolidation**. Executing it, the loop
  over-produced near-duplicate mechanics that only exact-name dedup let through, inflating the
  mechanic count and pushing extra untangling onto synthesis and (downstream) the Stage-2 walk. The
  durable improvement is to add a semantic **consolidation/dedup stage** to the reusable audit
  pattern (this session's Q-0089 idea) — the completeness-critic always needs its twin. A second,
  milder friction worth a future owner look: the born-red session gate emits a `failure`
  check-conclusion, so every GitHub branch-auto-update against a moving `main` fires a "CI failed"
  webhook that reads as alarming but is the intended hold — a `neutral` conclusion for the
  gate-only case would cut the noise (owner-gated CI-config change → route, don't self-apply).

## 📋 Doc audit (Q-0104)

- `check_docs.py --strict` → **green** (deliverable reachable via the brief; idea indexed).
- `check_current_state_ledger.py --strict` → **green** (only benign newest-merge lag beyond marker
  #1680, which the next reconciliation pass records — not drift).
- No new **owner decisions** made this session (the audit *flags* owner-gated items, it does not
  decide them), so no router entry is owed; Q-0236 already homes this work. Nothing important is
  stranded in chat — the report, the idea, and this log are the durable homes.
- Claim file `docs/owner/claims/claude__ultracode-surface-proving-icqb5b.md` deleted at close.
