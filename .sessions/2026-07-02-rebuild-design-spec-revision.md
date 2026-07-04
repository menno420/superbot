# 2026-07-02 — Rebuild design spec: external-review revision (plain-language + verified gap-fixes)

> **Status:** `complete` — ready to merge (Q-0133). Run type: manual · owner-directed.
> Docs-only; `check_docs --strict` ✓, ledger ✓ (benign newest-merge lag only). PR #1637.
> Scope: revision of `docs/planning/rebuild-design-spec-2026-07-02.md` (merged #1635) folding in the
> owner's **two external GPT review sessions** (the handoff §E seam, now exercised and closed).

**Branch:** `claude/superbot-rebuild-design-spec-de4mh7` (restarted from `main` @ #1636; #1635 merged).

## What I'm about to do (intentions — as declared born-red)

Fold the two owner-run GPT reviews into the spec per Q-0120 (verify each finding; adopt what holds,
decline with reasons what doesn't). Owner-endorsed headline: a plain-language summary.

## What shipped

All in `docs/planning/rebuild-design-spec-2026-07-02.md` (now ~1,790 lines):

- **Plain-language summary** (new, before §0) — what/why/what-changes/what-you're-approving in
  non-engineer language, with a one-glance build-flow block and a reader's guide. The owner-gate
  artifact now opens at the owner's altitude.
- **Table of contents** (anchor-linked, GitHub-slug-verified) + **§11 Glossary** (26 terms, each
  linking its defining section) + **§8 decision quick-table** (10 rows).
- **§6: the dashboard/control-surface contract** — the FastAPI dashboard is a *client* of the same
  audited workflow lanes over one versioned control API, never a second write path; contract is a
  required K7/K8-entry deliverable. (Review 2's one genuinely-new architectural gap — verified real:
  the spec never addressed the dashboard.)
- **§10.3 (new): pre-cutover operational contracts + deliberate non-goals** — SLO set, rate/quota
  budgets, DR-beyond-rollback-window runbook, per-store retention/deletion inventory (rides the
  existing `StoreSpec.retention` field); non-goals: no vector DB in phase 1 (pgvector-first if
  ever), no durable-execution engine, no external agent framework for the platform loop, no model
  pinning in a design doc.
- **§5.2:** importer mismatch classes are machine-readable with hard stop-codes (6 classes); the
  fallback trip-wire keys on stop-codes. **§5.4:** the shadow-window **compat scoreboard**
  (unknown-custom_id hits, alias residue, payload diffs, importer residue, parity status) with
  scoreboard-line cutover-exit criteria. **§5.1:** AI conversation/approval state is session-class
  (two-layer memory split made explicit). **§10.1 risk 2:** canary subsystem per engine family +
  per-renderer-family runtime kill-switch. **§9.2 band 6:** outer-ring framing (AI/ingestion never
  hold the platform hostage). **§9.3 pass 3:** low-confidence dense-panel sims defer to the legacy
  layout via `Exempt` — never a parity gate.
- **Header "Revision" note** recording the round + the declined items; handoff §E marked ✅ ran;
  planning-README row updated (rev. 2).

## Finding-by-finding disposition (Q-0120)

**Review 1 (readability):** (1) plain-language summary — **adopted** (owner-endorsed). (2) glossary —
**adopted** (§11). (3) separate normative/rationale — **declined**: house planning-doc style argues
its case inline; the *new repo's generated* docs do separate provenance from rule (§7) — that's
where the principle lands. (4) move `file:line` cites to footnotes — **declined**: the citations are
the Q-0120 verification substrate (each is re-checkable in place); burying them optimizes prose over
trust. (5) tables/diagrams for long lists — **partially adopted**: layer model was already a table;
added the §8 quick-table + the build-flow block (plain ASCII — zero mermaid exists in house docs, so
render-anywhere formatting wins). (6) decision summary table — **adopted** (§8). (7) formatting
consistency — no specific defect named; spot-checked, no change. (8) split the doc — **declined**
(link churn on a merged, widely-pointed-at artifact); **TOC adopted** instead.

**Review 2 (deep research; endorses the design, "approve with sharpening"):** two-stage/ring
execution — **already largely in §9** (kernel → operator bands → AI last); adopted the explicit
ring sentence. Platform-vs-AI workflow split — already structural (`kernel/ai` no-upward-imports);
adopted the session-state layering note (§5.1). Vector-search deferral — **adopted** as a §10.3
non-goal. Dashboard API contract — **adopted** (§6; the one true gap). SLO/rate-limit/DR/privacy —
**adopted** as §10.3 named deliverables (not solved in-doc). Canary + kill-switch — **adopted**
(§10.1). Importer stop-codes — **adopted** (§5.2). Compat scoreboard — **adopted** (§5.4).
Pre-parity sim restraint — **adopted** as the §9.3 confidence-fallback line (its stronger form —
skip pass 3 entirely — declined: the sim gate + owner ratification already bound it). "Manifest
budget" (max handler refs/subsystem) — **declined**: §2.9's counted+ratcheted tier-3 regime enforces
the same pressure without an arbitrary constant. Compile-time Discord caps — **already in §2.3**
(review missed it; no change). Framework adoptions (LangGraph/Temporal/Agents SDK) + model/hosting/
vector cost tables — **not folded**: the review itself concludes the application-owned baseline is
right and Temporal is "not for phase one"; models/hosting are `TaskProfileSpec`/ops data, wrong
altitude for the design spec (non-goals now say so explicitly).

## Context delta

- **The approving reader defines the document's opening altitude.** The spec was verified, coherent —
  and immediately bounced for missing a plain-language layer. Audience is a spec requirement, not
  polish (→ the session idea).
- **External reviews earn their keep on *gaps*, not corrections:** both GPT rounds found zero factual
  errors (the judge-panel + verification held) — their value was the unaddressed dashboard contract
  and the implicit-ops-contracts list. Cross-family review finds blind spots, not bugs.
- **A green checker beats my inference:** the `funny-franklin` claim looked stale (#1626 merged from
  that branch) but `check_stale_claims` says not stale — its scope may span further PRs; left for
  the recon sweep rather than overriding the tool (the same Q-0120 humility, pointed at myself).

## 🛠 Friction → guard

The friction: an owner-gate artifact shipped without its audience layer, costing a full revision PR.
Cheapest enforcing prevention = a checker rule (`owner-gate` badge ⇒ `## Plain-language summary`
heading) — **routed as the Q-0089 idea below rather than shipped now** because it needs the badge
convention decided first (one consumer today); the idea file specs the ~10-line `check_docs` rule so
the next session can ship it as a turn-key.

## 💡 Session idea (Q-0089)

**[`owner-gate-docs-plain-language-rule-2026-07-02.md`](../docs/ideas/owner-gate-docs-plain-language-rule-2026-07-02.md)**
— owner-gate deliverables must open with a plain-language summary, backed by a small `check_docs`
rule keyed on an `owner-gate` status token; portable into the substrate-kit's doc templates. Worth
having because this exact miss just cost a revision PR and it recurs structurally (agents write for
the reviewer they imagine, not the owner who approves).

## ⟲ Previous-session review (Q-0102)

Previous session (#1635, the design-spec judge panel): the panel + adversarial round delivered —
zero factual defects survived into either external review, and the §E handoff prompt meant the
owner could commission exactly the review the process wanted. What it missed: **audience** — it
optimized for the skeptical staff engineer (correctly, for content) but never asked "can the
person who must approve this read it?", which was the very first human feedback. **Concrete system
improvement:** the plain-language rule above; more generally, owner-gate deliverables should carry
an explicit audience check in their definition-of-done (the substrate-kit's template layer is the
durable home for that).

## 📤 Run report

- **Did:** folded the owner's two external GPT reviews into the design spec (plain-language summary,
  TOC, glossary, decision table + 9 verified gap-fixes; 5 items declined with recorded reasons) ·
  **Outcome:** shipped
- **Shipped:** #1637 — spec revision + handoff §E closure + README row + 1 idea
- **Run type:** `manual` (owner-directed)
- **⚑ Owner decisions needed:** **the owner gate stands** — approve
  [`rebuild-design-spec-2026-07-02.md`](../docs/planning/rebuild-design-spec-2026-07-02.md) (start
  at its new plain-language summary; §10.2 = what approval means, now incl. §10.3's ops contracts)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (owner-directed revision; idea file is capture)
- **↪ Next:** the owner gate blocks Phase 3; Phases 0 / 0.5 / 1 / 2.5 stay agent-buildable
  (current-state S3 ▶) — Phase 0.5 golden-harness + telemetry capture remains the best parallel start.
