# 2026-07-07 — Rebuild FINAL review (Fable 5, ultracode) + Projects-EAP repo prep

> **Status:** `complete`
> **Branch:** `claude/superbot-rebuild-final-review-nezu89` · **PR:** #1778 (+ fix PRs #1781, #1782 — both merged→deployed)
> **Brief:** `docs/planning/rebuild-final-review-fable5-ultracode-brief-2026-07-07.md` (§3 mandate A–H, Q-0241)

## What happened (close-out)

The full A–H mandate executed; deliverables:

1. **The A–H report** — [`docs/planning/rebuild-final-review-report-2026-07-07.md`](../docs/planning/rebuild-final-review-report-2026-07-07.md):
   candid verdict (**plan ready — the new repo can start now; zero blocking work ahead of §5
   step 6**), per-step readiness table (ground-truth-verified), the single biggest risk (layer V
   is the least-built part now that the human gates are retired), and the decisions log
   (O-1…O-7 recommendations decided-and-flagged, R-1…R-11).
2. **Canonical plan §11 amendments A-1…A-11** + surgical row updates (steps 2/3 ✅, cutover
   steps 15–17 restated as reaction windows with the honest CUT-3 reversibility justification,
   D-17 role_menu correction, step-11 harness/oracle decomposition + `check_sim_gate` contract
   pointer, K2/K7/K8 row pointers).
3. **Coverage hunt (15-agent fan-out):** brief's 4 suspected misses → 3 already landed (recorded,
   Q-0120), 1 confirmed thin (wizard → A-9); new finds folded: WebhookReporter operator-alert
   sink + redaction obligation, role_grants expiry, session_gc TTL, media purge named, hermes
   `/dispatch` disposition (A-8/A-11).
4. **Stale-prose sweep:** 20 stale-live owner-gate sites fixed across 6 live docs (owner-briefing
   amendment banner + 5 in-line, ultracode-handoff banner + 4, phase-2.5-procedure 3,
   S3-ai-memory 4, planning/README 3, design-spec banner 1); superseded/frozen docs deliberately
   untouched. Companion C's interaction-token constraint **validated against official Discord
   docs + frozen** (Ed25519 webhook signatures; no cross-app invocation endpoint).
5. **Projects-EAP product review** (owner-sendable) —
   [`docs/planning/projects-eap-product-review-2026-07-07.md`](../docs/planning/projects-eap-product-review-2026-07-07.md),
   grounded in this repo's hand-rolled equivalents; cross-cutting normal-Claude-Code feedback
   separated (7 items, incl. two incidents from this session).
6. **Phase-2.5 G2 close-out (H1):** the adopt-renders-what-it-knows kit fix (new
   `engine/derive.py` provisional-slot derivation; UNRENDERED banner + `render --live` strip;
   vendored `bootstrap.py` fixing the staged-hook paths; `run_session` no longer clobbers derived
   values; 432/432 kit tests; dist regenerated; live-smoked cold) + the **T2/T4 re-run pair**
   with scripted M1 + independent judge → results + honest verdict in the
   [G2 report's §5 addendum](../docs/planning/phase-2.5-cold-start-report-2026-07-07.md).
7. **Live-bot fixes (H2, verify-first):** **#1781 merged** — settle-once retrofits (deathmatch
   `_DuelView`, blackjack free-tourney, **+ the RPS free-tourney race found during
   verification**) + Rule-6 widening + 12 regressions; **#1782 merged** — `!pay`/`!transfer`
   wiring (NOT `give`, Q-0211) live-exercised against real Postgres. Cleanup/slowmode/greeting/
   teardown items verified already fixed by #1728 (recorded, no action).
8. **Ledgers updated:** current-state hub (+#1781/#1782 entry, S3 row → "create superbot-next
   next", ratchet trim to archive), S3 sector top entry, roadmap §S3, planning README rows.

**⚑ Self-initiated:** the RPS free-tournament fix (same class, found while verifying blackjack);
the `SettleOnceMixin.rearm_settlement()` seam; canonical-plan §11 A-2…A-11 fold-ins (Q-0172
promotions); the D-17 correction (Q-0166 fix-on-sight); the owner-briefing amendment banner;
`!pay` shipped ungated (kill-switch path named in #1782). All reversible; veto list in the
report's decisions log.

**💡 Session idea (Q-0089):**
[`docs/ideas/substrate-kit-auto-drafted-handoff-2026-07-07.md`](../docs/ideas/substrate-kit-auto-drafted-handoff-2026-07-07.md)
— the A/B measured the same write-back failure twice (sessions with rendered ledgers still record
nothing); make the kit's session-close **auto-draft** the handoff card from evidence (git diff +
test state) so the agent edits a draft instead of authoring from memory. Indexed in the ideas
README.

**⟲ Previous-session review (Q-0102):** #1777 (the brief prep) fixed the live-ledger drift
proactively and its ranked re-verify checklist made this session's fan-out trivially plannable —
genuinely good prep. Its miss: the brief asserted "no landing anywhere" for health/media/hermes
without grepping the walk rows — two of the four named gaps were already explicitly landed, and
this session spent a lane re-verifying claims the brief could have pre-graded. **Workflow
improvement:** briefs should tag each factual claim with its evidence tier (verified-at-source vs
suspected-from-memory), the same discipline the Gate-V ledgers use — downstream sessions then
re-verify only the `suspected` tier. (Genuine, not filler: it cost real agent-time this session.)

**🛠 Friction → guard (Q-0194):** (1) python-heredoc bulk edits bypass the PostToolUse auto-format
hook → format drift reached a commit, caught only by the mirror — journal Rule added (run `ruff
format` on touched files after script-driven edits). (2) The Workflow orchestration tool failed
twice on permission-stream errors in this unattended session → not repo-guardable (platform);
recorded as Projects-EAP review §9 item 3 + this line. (3) The artifact-freshness gate caught the
missing dashboard regeneration for `!pay` — the guard worked; nothing to add.

**Backlog grooming (Q-0015):** over-satisfied this session — ten `docs/ideas/rebuild-*` entries
were moved down their lifecycle in one pass (2 folded-now, 3 folded-partially, 2 already-covered,
2 deferred-with-reason, 1 idea→shipped [layout-sim → step 11 harness]); no additional single-idea
move forced on top.

**Docs audit (Q-0104):** `check_docs --strict` ✓ · `check_current_state_ledger --strict` ✓ (benign
newest-merge lag only) · new owner decisions: none made BY the owner this session (agent decisions
flagged per Q-0240 in the report; nothing to route to the router — the O-1…O-7 recommendations
live in the report and are pointered from the plan's §11).

**Next session:** execute canonical §5 step 6 — **create `superbot-next`** — then steps 7–8
(bootstrap the kit — now proven cold; control plane). Watch step 11 (the risk named in the
report). The G2 re-run addendum carries the honest continuity caveat: read it before claiming
kit value in the new repo.
