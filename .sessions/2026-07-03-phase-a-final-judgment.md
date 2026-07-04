# 2026-07-03 — Phase-A final judgment (Fable-5 ultracode)

> **Status:** `complete`

**Run type:** owner-directed (the Fable-5 capstone prompt from
`docs/planning/rebuild-phase-a-final-review-fable5-brief-2026-07-03.md`). **PR #1701.** Docs-only.

**Did:** sat as the final independent judge over everything 2026-07-03 produced — the Phase-A
freeze (Q-0219…Q-0236), foundations audits A (#1690) + B (#1691), the two prod fixes (#1693), and
the owner's 5 Codex reviews (found on unmerged `codex/*` branches, all dated 07-03 ~20:25).
Deliverable: **`docs/analysis/rebuild-discovery/foundations/final-judgment-fable5-2026-07-03.md`**
— verdict **GO-with-amendments**, a 25-row master reconciled ledger, re-prioritization, 17
still-missing gaps, the #1693 judgment, and a ~58-item owner queue tiered to **7 Tier-1 rows**.

**Method:** read every input directly in-session; verified both #1693 fixes line-by-line inline;
then a 37-agent workflow (~2.9M tokens): 16 adversarial verifiers over the top claim clusters
(**14 CONFIRMED / 2 PARTIAL / 0 REFUTED**), 7 stress agents over the frozen decisions (**7×
HOLDS-WITH-FLAGS, 0 CHALLENGED**), 2 ledger deep-ingesters, and a 4-round×3-lens completeness-critic
loop (31 raw misses; round cap hit while still producing — noted honestly in the doc).

**Headline findings a follow-up session should act on:**
- **RPS tournament still forfeits entry fees on a version bump** — same class #1693 fixed for
  blackjack, live at `disbot/cogs/rps_tournament/_persistence.py:104-115`, latent until an
  `RPS_TOURNAMENT_VERSION` bump. Verdict blocker V-1: one small PR, same pattern as #1693.
- #1693's drain gate covers pipeline stages only — prefix commands (`process_commands`),
  interactions, and non-message listeners still double-fire during deploy overlap; the durable fix
  stays the queued idempotency-keys owner decision.
- Novel foundation gaps: panel buttons bypass C-1 entirely (no cooldown field on PanelActionSpec);
  the shipped draft store is a per-guild singleton that makes the C-2 "10 D&D channels" example
  unrepresentable; CUT-1 has no data-plane rail while prod `DATABASE_URL` is ambient in agent
  containers; rollback destroys all post-cutover data; the Discord verification/intent-approval
  growth gate is absent from all planning.

**⚑ Self-initiated:** none beyond the directed scope — the deliverable, the two docs-check fixes on
the draft (badge + orphan link), the Q-0015 groom, and the Q-0089 idea below are all inside the
session's mandate. No new plans or implementations were promoted.

**Grooming (Q-0015):** appended the prior-art correction to
`docs/ideas/rebuild-layout-success-simulator-2026-07-03.md` — `claim_layout_sim` is a git-merge
simulation, not a UX sim (stress finding); scoped the unification to the real four + flagged the
corpus Goodhart loop.

**💡 Session idea (Q-0089):** `docs/ideas/fleet-structured-output-placeholder-guard-2026-07-03.md`
— reject placeholder strings (`test`, `t/e/f`, `TODO`) in required evidence fields of fleet
structured outputs with one retry. Genuine: schema-valid placeholder junk shipped twice in one day
(audit A row 221, audit B's three §8 rows) and only the capstone pass caught it.

**⟲ Previous-session review (Q-0102):** the prep session (#1700) wrote a precise, launchable brief —
the input inventory matched reality and the verbatim-prompt pattern worked cleanly. Its one miss:
it said the 5 Codex reviews would be "pasted into the session, or committed under docs/" — they
were actually sitting on **unmerged `codex/*` branches**, which cost this session a discovery
detour. **System improvement:** prep briefs for capstone sessions should pin the exact location of
external-agent artifacts (branch names, or a rule that the owner lands Codex branches before the
capstone launches); more generally, a `codex/*`-branch sweep belongs in the reconciliation
routine's disposition step so external reviews can't sit unmerged and invisible.

**Post-flip CI fix (drift on sight, Q-0166):** the final head failed
`test_check_plan_homing::test_live_repo_plans_are_all_homed` — **pre-existing from #1700**, which
landed the Fable-5 brief as a `plan`-badged doc homed on no routing doc (main carried the latent
red; this PR merely inherited it). Fixed the checker's own intended way: the brief's work has now
shipped, so it is rebadged `historical` in place with a delivered-pointer to the judgment doc.
Open question for the next reconciliation pass: how #1700 merged with that test red — worth
checking whether auto-merge fired on a stale green head (if so, that's a real enforcement gap in
the Q-0123 merge path, router-DISCUSS material).

**Docs audit (Q-0104):** `check_docs --strict` clean; `check_current_state_ledger --strict` clean
(this PR's own entry is post-merge lag by design); judgment doc linked from the Fable-5 brief; no
chat-only conclusions left unhomed — the deliverable, the two idea files, and this log carry
everything. Note for the next docs session: audit B's three `t/e/f` placeholder rows (§8, one HIGH)
are drift to fix on sight (L-25).
