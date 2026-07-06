# 2026-07-06 — Rebuild consolidation: one canonical plan + foundational-completeness (Fable 5 Ultracode brief §3)

> **Status:** `complete`
> **Branch:** `claude/superbot-rebuild-phase-2.5-qk07s7` · **PR:** #1770
> **Brief:** `docs/planning/rebuild-newrepo-start-fable5-ultracode-brief-2026-07-06.md` §3 (now stamped ✅ EXECUTED)
> **Decision model:** decide-and-flag (Q-0240, `docs/owner/agent-decision-authority.md`)

## What happened

Executed the brief's two goals — finalize the new-repo start METHOD + consolidate the scattered
rebuild plan into ONE correctly-layered source of truth — via a 7-lane Ultracode source-verification
fan-out (substrate-kit · AI seam · automation · K0–K10 walk · plans/gates census · simulators ·
test infra; ~750K sub-agent tokens, every key fact `path:line`-cited) with synthesis, taxonomy, and
all decisions kept in the coordinator.

**Shipped (docs-only + one CI fix):**
- **`docs/planning/rebuild-canonical-plan-2026-07-06.md`** (deliverables A+B+E): corrected
  foundational taxonomy (Gate-0 K-numbering canonized — resolves Gate-V C-5; **K10 = AI invocation
  kernel** with a domain-registered task registry replacing the `AITask` enum + the grounded-answer
  engine hoisted; **automation = the K5+K9+K7 spread**, no new band; **verification = defined layer
  V** with a named build step; settings-engine / panel-runtime / findings-engine landing steps
  added), the reconciled phase arc (both vocabularies retired as aliases), the de-overloaded gate
  list (**G1** owner go/no-go sitting · **G2** Phase-2.5 A/B; ~14-gate census pruned), a **17-step
  start sequence** with owner-gated steps marked, the **flag-for-gate list F-1…F-5** (data
  contract; 12 Gate-0 rows + L-21 pre-filled — only Q-D5 diverges from the shipped default; taxonomy
  corrections; two-lane test-guild driver; Phase-2.5 pass bar), and the **decisions log D-1…D-21**.
- **`rebuild-test-guild-design-2026-07-06.md`** (C): 9 zones / ~40 channels refined against the
  live cog roster, per-zone exercise/proof map, CUT-1/band mapping, and the **two-lane fidelity
  model** — grounded in the lane-5 finding that `parity/` already drives the full real command
  pipeline in-process (the gap is live-tier only), and that the wire-level idea is
  **contradicted by source** (author.bot at `ext/commands/bot.py:1413` + `message_pipeline.py:279`;
  interactions structurally closed; user-account automation = ToS-banned).
- **`rebuild-phase-2.5-procedure-2026-07-06.md`** (D): the never-run gate made runnable —
  cold operationalized, 4-task paired-arm protocol, 3 primary measures, judge rubric, pass bar
  (F-5), artifact home. Prereq surfaced: **kit tail ① (Q-0223) verified still unshipped** — the
  brief's "ONE open kit item" framing corrected (D-14).
- Supersede banners (link-don't-delete) on planning-phase / strategy §3 / parallel-execution /
  design-spec (in-part, grammar-precedence declared) / next-session-priority / the brief; planning
  README homing; S3 sector ▶ pointer re-aimed at the canonical plan.
- **Bugs-first:** fixed the dead advisory CI step (`check_session_slug_unique.py` invoked with a
  nonexistent `--strict` → argparse exit 2 on every PR run) + shipped the enforcing guard
  (`tests/unit/scripts/test_workflow_script_flags.py`, workflow↔script flag parity, Q-0194);
  fixed the #1716 "uniqueness checker" ledger drift on sight (Q-0166).

**Verification:** `check_docs --strict` ✓ · `check_current_state_ledger.py --strict` ✓ (benign
newest-merge lag only — the #1770 recon routine's band) · new flag-parity test 2/2 green under
python3.10 · slug-unique checker runs clean post-fix. The recon pass due at #1770 was left to the
routine per Q-0124.

**⚑ Self-initiated:** the CI slug-checker fix + flag-parity guard (bugs-first); the #1716 ledger
drift fix (Q-0166); the supersede-banner web + README/S3 re-pointing (consolidation follow-through);
the wire-level idea disposition note; the Q-D15 N=7d and L-21 goldens-fresh pre-fills (decided, not
asked — flagged in F-2 for veto). Everything else was the owner-directed brief.

## 💡 Session idea (Q-0089)

[`docs/ideas/supersede-banner-integrity-checker-2026-07-06.md`](../docs/ideas/supersede-banner-integrity-checker-2026-07-06.md)
— a warn-first checker enforcing the supersede web this session built by hand (banner's successor
resolves + links back; superseded docs can't keep a `plan` badge). Worth having because the
canonical plan is only "the single source of truth" while the losers verifiably point at it — and
the design-spec header staying stale 4 days after Gate-0 proves the class recurs.

## ⟲ Previous-session review (Q-0102)

The previous session (#1769, Q-0240 decide-and-flag + brief revision) did the load-bearing thing
right: it converted a vague "let Fable decide" instinct into a precise, reusable authority model
with a table of decision shapes — this session leaned on it constantly and never once needed to
route a call. What it missed: the brief asserted exhaustive state in prose ("the ONE open kit item
is the A/B") that was already false at writing time (Q-0223's tail ① predates it by 3 days).
**Workflow improvement:** launch briefs should state *where to verify* a state claim (the checker,
the router Q, the source file) rather than asserting the state itself — the same
provenance-separate-from-rule principle the rebuild applies to binding docs, applied to prompts.
This session's brief did it right for anchors and wrong for state claims; the lane fan-out caught
it, but only because the brief also said "verify against live source."

## Documentation audit (Q-0104)

Checkers run (above). New docs reachable: canonical plan + companions homed in
`docs/planning/README.md` (top of the rebuild table); idea indexed in `docs/ideas/README.md`;
S3 sector points at the new ▶ steps. Decisions durably homed: all 21 in the canonical plan §8
(the artifact's own decisions log per Q-0240), none owner-made this session so no router additions.
Nothing captured only in chat: lane evidence is summarized with citations in the canonical plan
§10 + companions; scratchpad working-memory contains nothing not reflected in the shipped docs.
Claim file deleted at close.
