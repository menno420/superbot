# 2026-07-10 — Verifying the 3 Codex review PRs (#1940/#1941/#1942)

> **Status:** `complete`
> **PR:** #1943 · branch `claude/gpt-5-6-sol-eval-er1kcq` (rebuilt post-#1938)

**Goal (owner-directed, live):** thoroughly review the three Codex review PRs,
improve their findings where necessary, and give my own review of Codex's
performance and of the projects work itself.

## What shipped

- **Verification addenda pushed to all three Codex branches** (+ badge/reachability
  fixes so they pass check_docs): #1941 — all evidence confirmed at superbot-next
  HEAD, 3/3 tests reproduced, **its "only residual" claim corrected with the missed
  `moderation.timeout` compensation gap** (full EFFECT-leg sweep); #1942 — 5/15
  claims re-verified by second method, all exact, one verdict-precision note;
  #1940 — all sampled evidence verbatim-real, **stale lane-overlap row corrected**
  (superbot #1919 `--remote` predated the audit by ~9.5h). Auto-merge armed on all
  three.
- **`docs/eap/codex-review-round-verification-2026-07-10.md`** — scores (run 2:
  trust 2/2/2 vs run 1's fabrication), lane upgrade (evidence-cited review passes
  approved; universal-negatives still get swept), and my independent program
  assessment (superbot-next engineering strong; reversibility labels overpromise;
  fleet doctrine outruns enforcement; report drift is the main fabrication surface).
- **Trust ledger row 2** appended.
- Repos added + cloned for verification: superbot-next, fleet-manager,
  superbot-games (add_repo flow per the cross-repo EAP verification pointer;
  each verified with its own CI interpreter — superbot-next under py3.11).

## Session enders

- **💡 Session idea (Q-0089):** superbot-next invariant test — every non-optional,
  non-irreversible EFFECT leg that follows a DB leg must declare a compensator
  (would have caught both `end_access` and `timeout` at authoring time; the
  enforce-don't-exhort pattern applied to the workflow engine). Routed in the
  verification doc §4 for the superbot-next lane; dedup: no such invariant in
  its tests/unit/interaction/test_handler_kit.py family.
- **⟲ Previous-session review (Q-0102):** the #1938 scoring session was solid on
  evidence but scored P2–P6 without re-running Codex's claimed test commands
  (it verified diffs/docs, not executions); this session closed that gap by
  reproducing every claimed command. Improvement: the eval doc's rubric should
  say "trust score requires re-running at least one claimed command" — cheap
  and it operationalizes the P4 axis.
- **📋 Docs audit (Q-0104):** check_docs --strict ✓ on all four touched branches;
  ledger check pending merge (benign lag only). New docs reachable (eap README ×3,
  audits README, owner README ledger row). Nothing chat-only: scores, corrections,
  and the program assessment all live in the verification doc + addenda.
- **🧹 Grooming (Q-0015):** folded into the deliverable — three external review
  artifacts moved from unverified → verified-and-merging, and the trust ledger
  (yesterday's idea) received its second data row, proving the instrument.
- **⚑ Self-initiated:** corrections/addenda written directly onto the three
  Codex PR branches (contained, reversible, evidence-cited); auto-merge armed
  on them per the standing merge doctrine.
