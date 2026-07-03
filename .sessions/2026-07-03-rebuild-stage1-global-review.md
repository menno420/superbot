# 2026-07-03 — Rebuild Phase A · Stage 1: the global plan review (owner-live)

> **Status:** `complete` — PR #1679. Owner-led **Stage-1 global review** of the frozen
> BUILD-PLAN (first of the owner's three Phase-A review stages), run live in-chat, then folded
> into the repo. Mid-session the owner escalated the model (Opus 4.8 → **Fable 5 max**)
> specifically to review + lock the generalization standard with higher reasoning — the
> escalated pass re-audited the whole dependency table (found 2 more inversions beyond the one
> caught live) and sharpened the standard (leaf-handlers, per-domain engines, schema-growth
> guardrail, seam-first reconciliation). Docs-only; no `disbot/` code, no new-repo code.

## What shipped (all in PR #1679)

1. **[`docs/planning/rebuild-stage1-global-review-2026-07-03.md`](../docs/planning/rebuild-stage1-global-review-2026-07-03.md)**
   — the Phase-A companion decisions log #1:
   - **S-1** the engine/declaration/seam standard (Q-0219): one engine per domain; steering by
     explicit declarations in 3 tiers (params → composition → named handler seam); handlers are
     leaves; no call-site-identity steering; the **second-consumer rule** + **seam-first** ("plug-
     and-play ready" = seam discipline); the **schema-growth guardrail** (anti-inner-platform).
   - **S-2** foundation-before-consumer ordering (Q-0220): engine-class deps always port before
     their first consumer; peer-class deps may ship as declared-seam deferrals.
   - **The order audit:** walked every §1.1 dependency cell against §2 orderings — 3 inversions:
     welcome←card-engine, welcome←role (both fixed by re-homing welcome to L1c after the card
     engine, as its acceptance test), deathmatch/explore←mining (seam deferrals; mining-last
     stands). Layer skeleton otherwise verified sound.
   - **Gate-0 deltas D-1…D-6:** card engine promoted (5+ consumers, image-source seam day one);
     **NEW media-generation capability** (Q-0221 — prompt→image, L4 adapter, quota/cache/kill-
     switch/default-OFF, D&D story game to known-options only); **3-phase container-first
     cutover** (Q-0222 — CUT-1 container-only live testing with per-command `verified_live`
     sign-off registry + guild allowlist + single-instance lock; CUT-2 manifest-driven selective
     import with full-coverage disposition report + mandatory Import-mapping plan-template
     section; CUT-3 token swap + rollback window); **substrate-kit pre-bootstrap gate** (Q-0223);
     **per-subsystem triage** (return not automatic); one canonical L-vocabulary (K↔L crosswalk).
2. **Router Q-0219…Q-0223** — the five owner rulings with verbatim-quote provenance.
3. **Phase-doc update** — `rebuild-planning-phase-2026-07-03.md` now maps owner Stages 1/2/3 onto
   Phase A and marks Stage 1 done; planning README homes the new log (plan-homing green).
4. **State corrections:** the strategy doc's substrate-kit "~45–55%" is stale — verified today:
   nervous system + hooks + real mode branching shipped in #1649, **422 kit tests green** (ran
   them), packaging present; honest state ~90–95% with the named D-4 tail. Container facts
   verified: test-bot token (Galaxy Bot) + `DATABASE_URL` live → CUT-1 has zero setup.
5. **Grooming (Q-0015):** `substrate-kit-review-followups-2026-07-02.md` follow-up #1 promoted →
   scheduled as pre-bootstrap-gate item ① (annotated in place, pickup-ready).

## 💡 Session idea (Q-0089)

**[`rebuild-schema-growth-ledger-2026-07-03.md`](../docs/ideas/rebuild-schema-growth-ledger-2026-07-03.md)**
— enforce the Q-0219 schema-growth guardrail mechanically: every grammar field addition mints a
same-PR ledger entry naming the ≥2 consumers that justified it (else: handler), CI-diffed. Worth
having because the inner-platform effect creeps one innocent field at a time — this makes each
step a reviewed decision and gives every field a durable "why" (the plan→manifest→code
durability chain applied to the grammar itself). Routed to the Gate-0/K2 grammar plan.

## ⟲ Previous-session review (Q-0102)

Previous: **#1674/#1677 capability-audit capstone.** Genuinely excellent — froze a single
dependency-ordered reference from 6 lanes, independently re-verified Lane E (catching ≥17
stale-badge files), and shipped the staleness checker as a Q-0194 guard. **Miss:** it *carried*
the strategy doc's substrate-kit "~45–55%" figure into its own §4.4 numeric-drift list (as the
399/407/422 test-count drift) without re-measuring the headline completeness % against #1649's
shipped tree — today the owner said he'd been "led to believe it was already complete," and the
truth (~90–95%, short named tail) sat in neither doc. **Workflow improvement:** completion-%
claims about fast-moving components should carry a commit/PR anchor (`as of #NNNN`) the way
parity numbers do — and `check_plan_staleness.py` could flag any un-anchored `NN%` figure in a
`plan`-badged doc whose subject path has newer merges. Cheap rule, kills the exact drift class
that misled the owner twice in one week (once optimistic, once pessimistic).

## Docs audit (Q-0104)

- `check_current_state_ledger.py --strict` ✓ (entry #1679 added; see close-out run below)
- `check_docs --strict` ✓ · `check_plan_homing` ✓ (new log homed in planning README)
- New owner decisions → router Q-0219…Q-0223 ✓; idea indexed in ideas README ✓
- Chat-only residue check: the owner's "we can already boot in the test server" fact is durable
  in Q-0222/D-3 (rails + zero-setup note); nothing else chat-only.

## ⚑ Self-initiated

None — every promotion this session was owner-directed live in-chat (the five Q-blocks record
the directives). The session idea + grooming annotation are the standing Q-0089/Q-0015 enders.

## For the next session (Stage 2 — the subsystem walk)

Agenda = decisions log §6: per-subsystem exact command surface (271 commands: keep/merge/drop/
rename + final names), slash-vs-prefix kind, naming conventions for K1, hub topology, concrete
outperform lists, **D-5 triage verdict per row**, method/seam vocabulary as S-1 applications;
plus the two still-open Phase-A uncertainties (ModerationActionSpec spot-check, G-22 staging
lanes). Suggested shape: walk by L-layer bands (operator spine first), one band per sitting,
owner present.
