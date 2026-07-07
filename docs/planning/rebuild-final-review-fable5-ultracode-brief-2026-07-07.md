# Fable-5 ultracode brief — the FINAL rebuild-plan review + Projects-EAP repo prep (2026-07-07)

> **Status:** `plan` — the launch brief + paste-ready prompt + structured re-verify checklist for a
> dedicated **Claude Fable 5, `/effort ultracode`** session. Owner-directed (2026-07-07). Grounded by a
> 5-lane grounding workflow (`wf_c69d860b-a40`) + web-verified Fable-5/ultracode capabilities + the
> canonical plan. Governance: **Q-0241** (never-wait, live-test, silence=consent). This session decides
> its own calls (Q-0240) and does not wait for the owner.
>
> **Prep already done by session #1777 (do NOT redo):** the live-ledger drift Lane E/D flagged is fixed —
> `current-state.md` (readiness note + S3 row), `current-state/S3-ai-memory.md`, `roadmap.md` §S3, and the
> canonical plan's stale gate/shipped prose (§0 kit-tail-①/check_amendments, §3 G1 row, §4 header, §5
> step 6) now reflect Q-0241 + #1775, and the veto-clause parity was added to the plan amendment.

---

## 0. Launch (owner: paste §7; the rest is the session's reading route)

- **Model:** Claude **Fable 5** (`claude-fable-5`) — 1M-token context (load the whole corpus at once),
  128k max output, self-validates its own work at high effort.
- **Effort:** `/effort ultracode` (xhigh + automatic workflow orchestration; the session plans a workflow
  per substantive task; caps: 16 concurrent / 1,000 agents per run). Verify `/config` → Dynamic workflows
  is on. Add the repo's read-only tools to the allowlist so mid-run agents don't stall.
- **Where it runs:** cloud session; if the **Claude Code Projects EAP** is accepted, run it *inside* the
  Project so its memory + coordinator carry forward (see the Projects idea doc).
- **One Fable-5 caveat:** safety classifiers refuse ~<5% of sessions and reroute to Opus 4.8 — nothing in
  this review is refusal-prone, but if a sub-task returns a refusal, retry on Opus.

## 1. Reading route (read in this order, then hold it all in context)

1. `.claude/CLAUDE.md` (Working agreement; note the **Q-0241** rebuild-override bullet) →
   `docs/collaboration-model.md` → `docs/current-state.md` + `docs/current-state/S3-ai-memory.md` (live
   state, **just updated 2026-07-07**) → `.session-journal.md` (Quick reference).
2. **The plan of record:** `docs/planning/rebuild-canonical-plan-2026-07-06.md` (read fully — §1 flags,
   §2 taxonomy, §3 arc, §4 gates, §5 the 17-step start sequence, §8 decisions, §9 supersessions) + its
   two companions `rebuild-test-guild-design-2026-07-06.md` and `rebuild-phase-2.5-procedure-2026-07-06.md`.
3. **The evidence it rests on** (skim — already settled, see §2): `GATE-V-SYNTHESIS.md`,
   `new-bot-capability-audit/findings/{FINAL-REVIEW.md,NEW-BOT-BUILD-PLAN.md}`,
   `docs/planning/phase-2.5-cold-start-report-2026-07-07.md`.
4. **Governance of your own autonomy:** `docs/owner/agent-decision-authority.md` § Q-0241;
   `docs/owner/maintainer-question-router.md` Q-0241 + O-1..O-7.

## 2. What is ALREADY settled — spot-check, do NOT re-litigate

Spend budget on genuinely open questions, not these (each verified this cycle):

- **Gate V is COMPLETE** — Sequence C adopted; the frozen L3→L4/L5 games edge refuted 3× incl. live;
  punch-list P-1…P-9 handed forward. Do **not** reopen sequencing or the "K7 urgency" question.
- **Capability audit = GO-with-amendments, 85.1% fit** (re-verified live 85.26%); 14 ratified spec
  families + 15 riders; the bucket-(d) do-not-re-propose list is adversarially refuted.
- **Phase-2.5 A/B RAN (#1775) → verdict FAIL as-tested** — adopt ships the kit **inert** (unrendered
  `${...}` templates), 0/3 measures beaten. This is a *specific fixable cause*, **not** a green light and
  **not** a reason to redo the whole A/B. Remainder = the adopt-render fix + one re-run pair.
- **Kit tail ① + `tools/check_amendments.py` shipped (#1775)** — verify live, then treat as done.
- **Sim dispositions decided (D-17):** grammar_spike re-run per band; help_menu/settings_order = living
  CI checks; creature/mining drift-pinned; role_menu/casino/etc. archived as decision-records.
- **Economy/karma/xp function live** (Arm D): wager escrow/settle-once is idempotent under real
  concurrency. Do **not** report them as "broken today" — the only confirmed live defect is deathmatch
  `_DuelView` double-write. Audited-write atomicity is a *systemic contract gap*, not a live break.

## 3. The mandate — what this session must produce

Decide-and-proceed (Q-0241). Produce **one report** (`docs/planning/rebuild-final-review-report-<date>.md`)
covering A–H, **plus** a **separate Projects product-review artifact** (F) for the owner to send Anthropic.

### A. Final plan review + explicit readiness score
Give a **candid opinion** on the plan's state and a **readiness score**: *how much work remains before the
new repo can actually start*, broken down by the §5 start-sequence steps (what's done / blocking / can run
in parallel). Score the plan on completeness, internal consistency, and start-readiness. Name the single
biggest risk.

### B. Feature-vs-existing comparison (find what the plan forgets)
All 43 registered subsystems are dispositioned — but the grounding found **UNACCOUNTED background/glue
surface** the command inventory misses. **Confirm each has an explicit landing (ManagedTaskSpec consumer,
disposition, or deliberate drop) and hunt for more of the same class:**
- `HealthMaintenanceCog` retention loop (Q-0097 30-day findings TTL prune) — **no landing anywhere** in
  the plan corpus; a *data-minimization obligation*, not just a feature.
- `MediaMaintenanceCog` purge loop (Q-0099 youtube cache expiry, physical deletion every 6h) — **no
  landing**; a privacy obligation.
- `hermes_cog` `/dispatch` + `/bugreport` — in the 271-command corpus but **zero disposition** in any lane.
- Setup/provisioning wizard — the largest hidden service surface (~17 `setup_*` services + the AI setup
  advisor + `quicksetup`) rests on a single "register setup as a real subsystem" line + an owner-gated
  `WizardSpec` family. Confirm the full wizard lifecycle *and* the quick/essential presets *and* the AI
  advisor all have a carried home.

### C. Un-added ideas — decide which to fold into the plan now
The grounding surfaced 9 rebuild-relevant ideas not (fully) in the plan. Evaluate each and **fold the
worthwhile ones into the canonical plan / the relevant Phase-B slot** (Q-0241: build/decide freely):
websites-cutover-role + owner-facing progress dashboard · in-server release→test→verify loop (announcer +
production-usage coverage oracle + debug-trace mode) · schema-growth ledger + CI checker for the K2
grammar · navigation-completeness golden · **unified layout-success simulator** (see G) · audit-coverage
AST checker + Discord state-mutation fence · invocation-ladder centralization C-7 "one description
surface" · Claude Code Projects EAP as coordinator · `check_doc_cites.py`. (Full notes: the idea files
under `docs/ideas/rebuild-*`.)

### D. Forgotten items / stale prose
Sweep the rebuild corpus for stale G1/G2/👤 blocker language now that Q-0241 landed (prep #1777 fixed
current-state, S3, roadmap, and the canonical plan's §0/§3/§4/§5 — **verify those and find the rest**:
strategy, parallel-execution-plan, phase-2.5-procedure, gate-v-findings, ultracode-handoff still carry
owner-gate language but are superseded by §9 — confirm none is cited as live). Also validate the
Companion-C slash/component interaction-token constraint against an official Discord doc before it freezes.

### E. Today's-work review (Q-0241)
The five homes are mutually consistent and the reversibility rider is sound (grounding-confirmed). Two
things to nail: (1) at **CUT-2/CUT-3** the coordinator executes never-waiting via the reversible path — the
👤 markers are *reaction windows, not pauses*; confirm the cutover prose reads that way. (2) The
**Q-0213↔Q-0241 boundary at CUT-3** (real token swap + old-data wind-down = live prod): the governing
safety is the N=7d rollback + archived backup, not "it's shadow." Consider restating CUT-3's justification
as the reversible rider rather than shadow-ness.

### F. Projects product review — a proper deliverable for Anthropic *(separate artifact)*
Anthropic expects a product review of the **Claude Code Projects EAP**. Produce a structured, honest
review the owner can send, organized on the EAP's own feedback axes: **use-case fit** (Project vs one-off
session), **coordinator judgment** (surfaces the right things? too noisy/quiet?), **reliability**
(sessions complete autonomously?), **memory** (does shared memory remove restating?), **proactivity**
(acts + sets routines?), **scheduling** (cadence right?), **sidebar states** (blocked/ready/working/idle
granular enough?). **Separately capture the owner's cross-cutting ideas that would improve the *normal*
Claude Code environment too** (not Projects-specific) — mark them clearly, they're the highest-signal
feedback. Ground the review in *this repo's actual workflow* (claim files, born-red cards, the
PR-babysitting loop, cron routines) since Projects would replace much of that hand-rolled machinery.

### G. Simulator grouping/naming centralization audit
Verify the sim fleet is **centralized and covers grouping + naming completely**. Known state: the
`sim/` runner + `check_sim_gate` **do not exist yet** (built at §5 step 11); the 5 bespoke UX sims
(claim_layout / help_menu_grouping / role_menu / settings_order / setup_wizard) are scattered with per-sim
dispositions (D-17). **Assess:** is grouping (help-menu / settings / subsystem-namespace) and naming
(command names, the K1 namespace registry, conventions) validated by *one centralized mechanism* or
several disconnected ones? Where is a grouping/naming dimension covered by *no* sim/checker? Evaluate the
**unified layout-success-simulator idea** (one sim scoring any generated layout by task-success-rate,
deterministic + AI-naive-user models) as the centralizing target, and confirm the plan's 3 new manifest
sims (hub topology, settings grouping, dense-panel layout) + `check_sim_gate` are specified to land.

### H. Active repo-prep + opportunistic live-bot improvements
**Do as much as you safely can, now (Q-0241 — reversible, test-covered, flag it):**
- **Repo prep:** land the Phase-2.5 remainder (the **adopt-render fix** so `bootstrap.py adopt` plants
  *rendered* minimal docs, then one re-run pair to confirm the overhead flips — required before bootstrap
  is trusted cold in the new repo; regenerate `dist/bootstrap.py` after any `src/engine/` edit). Run
  `check_amendments.py` and spot-check its output (Q-0105 unverified-tier). Confirm the six new-repo CI
  gates + CODEOWNERS + Railway are *specified* (they're built in superbot-next, not this repo).
- **Live-bot fixes worth doing now** (FINAL-REVIEW §6.3 — reversible, test-covered): deathmatch
  double-settle (`SettleOnceMixin` retrofit + widen the Rule-6 checker), blackjack free-tourney
  double-pay, admin bot_spam greeting, the 2 cleanup unaudited paths, the security unaudited slowmode, the
  role 3-table teardown gap, and the unwired `economy.transfer()` → `!give`/`!pay`. Plus the §7.2
  committed-scope items from the Stage-2 walk if capacity remains.

## 4. What NOT to do
- Don't re-open Gate V sequencing / Sequence C / the K7-urgency question (settled).
- Don't treat the frozen `NEW-BOT-BUILD-PLAN.md` / `FINAL-REVIEW.md` **K9=kernel/ai, K10=loops**
  numbering as live — the **Gate-0 numbering wins** (K10 = AI kernel, K9 = durability; D-1/F-3.1).
- Don't build the wire-level live-bot driver as written (source-contradicted, F-4) — use the two-lane
  model (in-process synthetic gateway + human lane).
- Don't report economy/karma/xp as broken-live; don't redo the whole Phase-2.5 A/B (fix the cause).
- Don't wait for the owner on anything reversible — decide, live-test, flag (Q-0241). Route to the router
  only the genuine product/intent calls (the O-1..O-7 set).

## 5. Owner decisions to FLAG (not block on — Q-0241 decide-and-flag)
O-1..O-7 from Gate V still want the owner's product/intent call (atomicity policy, XP audit granularity,
workflow-engine choice, EventBus durability, inventory migration, deathmatch fix shape, advisory→hard
checker promotions). Under Q-0241: **recommend + proceed on the reversible path + flag on the run report**;
only genuinely irreversible product forks wait.

## 6. Output artifacts
1. `docs/planning/rebuild-final-review-report-<date>.md` — the A–H findings, the readiness score, the
   folded ideas, and the flagged decisions.
2. A **Projects product-review artifact** (F) — standalone, owner-sendable to Anthropic, with the
   cross-cutting Claude-Code ideas clearly separated.
3. Any repo-prep / live-bot fixes shipped as their own PRs (born-red card, auto-merge on CI green).
4. Update `current-state.md` / `S3-ai-memory.md` / the canonical plan with whatever the review changes.

## 7. Paste-ready prompt

> You are a **Claude Fable 5** session at **`/effort ultracode`** on the SuperBot repo. Read
> `docs/planning/rebuild-final-review-fable5-ultracode-brief-2026-07-07.md` first — it is your full brief,
> reading route, and the "already-settled, don't-redo" baseline. Then execute its mandate §3 (A–H):
>
> Do a **final review of the rebuild plan of record** (`rebuild-canonical-plan-2026-07-06.md`): give a
> candid opinion + an explicit **readiness score** (how much work before `superbot-next` can start,
> per §5 step). **Compare the plan against the existing bot's features** and surface anything it forgets
> (start from the known gaps: HealthMaintenance/MediaMaintenance retention loops, `hermes_cog`
> dispatch/bugreport, the setup wizard surface). **Find un-added ideas/improvements** and fold the
> worthwhile ones in. **Catch forgotten items / stale prose.** **Review today's Q-0241 work** (esp. the
> CUT-2/3 never-wait interpretation + the Q-0213 boundary). Write a **dedicated Projects (EAP) product
> review** for Anthropic on its feedback axes, separating out my cross-cutting ideas that would also help
> the normal Claude Code environment. **Audit the simulators** for centralized, complete grouping+naming
> coverage. **Verify the simulators/grouping/naming are centralized**. And **actively get the repo into
> the right state** — land the Phase-2.5 adopt-render remainder, and **fix/improve/add live-bot features**
> where you judge it beneficial (the FINAL-REVIEW §6.3 bugs are a good start).
>
> You operate under **Q-0241**: build in logical order, **live-test each piece in a real server**, and
> **never wait for me — if I say nothing, it's approved.** Decide reversible calls yourself, keep the
> destructive tier on the reversible path, flag every self-made decision on your run report. Ship work as
> born-red PRs that auto-merge on green CI. Route only genuine product/intent forks to the question router.

## 8. The structured re-verify checklist (ranked)

Beyond the owner's named asks — things worth re-verifying, most-valuable first:

1. **Feature-coverage completeness** — every command-less/glue cog + background job (retention/purge/
   maintenance loops) has a named ManagedTaskSpec consumer or explicit disposition; no data-minimization
   obligation silently drops. *(Known misses: health, media, hermes dispatch/bugreport, setup wizard.)*
2. **Plan↔source consistency** — no stale "unshipped/doesn't-exist/owner-gated" prose survives (prep
   #1777 fixed the main ones; sweep the rest). A green checker that contradicts evidence is a bug (Q-0120).
3. **The systemic audited-write atomicity contract (P-1)** is specified as one mechanism across
   economy+karma+xp — not per-subsystem — before the port bands.
4. **Simulator/grouping/naming centralization (mandate G)** — one runner/registry, complete coverage,
   `sim/`+`check_sim_gate` specified to land.
5. **Parity depth (P-5)** — events 21% / tables 25% / settings 2% is too thin to claim "shared primitive
   proven"; the per-band curated-golden plan exists.
6. **The verified_live registry (V-5)** and **telemetry-sidecar capture** (capture-before-freeze) — both
   have zero implementation; confirm they land before CUT-1 / any old-repo freeze.
7. **The 6 known live-bot bugs** (FINAL-REVIEW §6.3) + the unwired `transfer()`→`!give`/`!pay` — fix now.
8. **CUT-2/CUT-3 never-wait + Q-0213 boundary** (mandate E) — the two steps touching real prod data.
9. **Roadmap/pointer freshness** — S3 roadmap + any subsystem folio still pointing at superseded
   design-spec/handoff docs instead of the canonical plan.
10. **Numeric bases** are stated once and not re-litigated (kit tests 427, corpus 271 vs surface 484 by
    design — D-16); ignore benign snapshot lag.
