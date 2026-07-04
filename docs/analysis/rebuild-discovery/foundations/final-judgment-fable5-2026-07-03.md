# Final judgment — the 2026-07-03 Phase-A day, reconciled (Fable 5)

> **Status:** `audit` — **complete**. Produced by the Fable-5 max-reasoning capstone session the
> owner directed via
> [`../../../planning/rebuild-phase-a-final-review-fable5-brief-2026-07-03.md`](../../../planning/rebuild-phase-a-final-review-fable5-brief-2026-07-03.md).
> This is the **judgment layer over everything 2026-07-03 produced** — not a fourth audit. Source
> wins over this doc (Q-0120). Frozen dispositions are never reversed here; at most **flagged with
> evidence** for the owner.

---

## 0. What was judged (the inputs, all reconciled)

| Input | What it is | Where |
|---|---|---|
| Decision logs | Stage-1 global review (S-1/S-2, D-1…D-6, Q-0219…Q-0223) · conventions freeze (Q-0224…Q-0228) · hub/nav/presets (Q-0230…Q-0232) · rubric (Q-0233) · oracle/Gate-V (Q-0234) · layout sim (Q-0235) · two-prompt brief (Q-0236) | `docs/planning/rebuild-*-2026-07-03.md` + router |
| Audit A (engine room) | 35 mechanics · 246 issues (192 CONFIRMED · 36 plausible · 11 unverified · 7 refuted-dropped) · 32-item owner queue | `runtime-logic-mechanics-2026-07-03.md` (PR #1690) |
| Audit B (surface + proving) | 46 mechanics · 220 verified findings (195 CONFIRMED · 25 REVISED) · 87 owner-flagged · 14-item owner queue | `presentation-verification-mechanics-2026-07-03.md` (PR #1691) |
| Codex review 1 — sanity | Gate/phase-map verification; "mostly clear", no blocking inconsistency | branch `codex/perform-a-repo-grounded-sanity-review` |
| Codex review 2 — decision-log consistency | Conflict table (authority two-lanes, preset wording), durable-home routing, vocabulary normalization, 10 owner questions | branch `codex/review-rebuild-decision-logs-for-consistency` |
| Codex review 3 — Prompt-A trust review | Trust HIGH for audit A (10 sampled claims all supported); B unavailable at review time | branch `codex/review-ultracode-outputs-for-rebuild-planning` |
| Codex review 4 — Stage-2 readiness | "Ready after Prompt B merge"; full Stage-2 row template + verdict vocabulary + lane split | branch `codex/review-repo-readiness-for-phase-a-stage-2` |
| Codex review 5 — verification maturity | "Promising, not Phase-B-ready"; missing oracle/checker classes; acceptance-criteria rewrites | branch `codex/review-validation-strategy-for-rebuild-planning` |
| Prod fixes #1693 | Blackjack tournament fee-forfeit refund + message-pipeline drain gate | `git show 5207699` |

**Note for future readers:** the 5 Codex reviews live on **unmerged `codex/*` branches** (single-doc
commits dated 2026-07-03 ~20:25). This judgment consumed them from the branch tips. Two of them
(reviews 3 and 4) ran while PR #1691 was still open, so their "Prompt B unavailable/pending" caveats
are **timing artifacts, now moot** — B merged before this judgment.

**Independent verification layer:** this session re-verified the highest-stakes claims against
shipped source itself (both #1693 fixes line-by-line inline, plus a fan-out of adversarial verifier
agents over the top ~16 claim clusters), stress-tested the 7 frozen decision areas under a hostile
read, and ran a completeness-critic loop over the whole day. **37 agents, ~2.9M tokens: 16
verifiers → 14 CONFIRMED / 2 PARTIAL / 0 REFUTED · 7 stress agents → 7× HOLDS-WITH-FLAGS, 0
CHALLENGED · 2 ledger deep-ingesters · a 4-round × 3-lens critic loop → 31 raw misses (round cap
hit while still producing — see §4's process note).** §1–§4 carry the results.

---

## 1. VERDICT

# **GO — with amendments.** Proceed past Phase A to the Stage-2 subsystem walk.

**The decisive reasons:**

1. **The fact base held under independent attack.** This session re-verified the 16 highest-stakes
   claim clusters against shipped source with adversarial verifiers: **14 CONFIRMED, 2 PARTIAL
   (substance confirmed, citations wrong), 0 REFUTED.** Codex 3's 10-claim sample had already come
   back 10/10. Across ~470 findings from seven reviewers there is not one fact-vs-fact conflict.
2. **Every frozen decision holds at core.** All 7 decision areas (S-1, C-1+ladder, C-2, D-3, D-4,
   hub/nav/presets, oracle/Gate-V) came back **HOLDS-WITH-FLAGS** under a hostile stress read —
   zero CHALLENGED. The flags are refinements and missing sub-contracts (§2, §8), not reversals.
3. **The gate map is consistent** (Codex 1, re-confirmed): no doc authorizes skipping Stage 2/3,
   Gate-V, Gate-0, or owner ratification. The one hard precondition every reviewer named — Prompt B
   — merged the same day.

**Blockers to clear before/at Stage-2 start (none requires re-opening Phase A):**

| # | Blocker | Why | Size |
|---|---|---|---|
| V-1 | **Fix the RPS tournament fee-forfeit** — the exact bug #1693 fixed for blackjack is still live in `disbot/cogs/rps_tournament/_persistence.py:104-115` (verified this session; latent until an `RPS_TOURNAMENT_VERSION` bump, and the 24h GC refund backstop never sees the row because recovery clears it first) | #1693's fix-1 is otherwise incomplete as a *class* fix; this is real player money on the next version bump | one small PR, same pattern as #1693 |
| V-2 | **The 7 Tier-1 owner answers** (§6): hide-vs-disable, Back-path medium, admin gating, authority vocabulary, slash-cap policy, deep-link names, Stage-2 contract adoption | Each blocks a Stage-2 column or a spec freeze; answering them later means re-walking rows | one owner sitting |
| V-3 | **A findings-closure mechanism** — bind the ~470 reconciled findings (this doc's §2 + both audits + Codex) to Stage-2 rows / Gate-0 items so they cannot evaporate. Codex 4's row template already carries `prompt-a-issue`/`prompt-b-issue` tags; adopt it and make §2 below the seed registry | The day's dominant output is review findings with **no mechanic binding any of them to a plan** (critic finding; "enforce, don't exhort" applied to the meta-level) | process rule + this ledger |

Two further **stage-scoped** blockers that do *not* gate Stage 2 but MUST land before their stage:
the **CUT-1 data-plane rail** (before any container live-testing — see L-10) and the **parity
intended-divergence lane** (before Phase-0.5 golden capture — see L-11).

---

## 2. Master reconciled issues ledger

De-duplicated across audit A (246) + audit B (220) + 5 Codex reviews + this session's verifiers,
stress agents, and critics. Ranked by (severity × how much downstream work each blocks ×
cross-reviewer agreement). Rubric classes per Q-0233. **Verdicts are this session's, from source.**
The tail beyond these ~25 rows lives in the two audits' own ledgers — this table is the judgment
layer, not a replacement.

| L# | Issue | Source(s) | Agreement | Class | Verdict | Key evidence | Durable fix | Owner? |
|---|---|---|---|---|---|---|---|---|
| L-1 | **RPS tournament entry-fee forfeit on version bump — still live post-#1693** | A r4 · FJ verify | high (A + independent re-verify) | 9 | CONFIRMED (latent) | `cogs/rps_tournament/_persistence.py:104-115` drops version-mismatch rows w/o refund at cog_load; guild-remove path (:251-270) refunds correctly, proving the pattern is known | Immediate small PR (V-1); then the declared `refund_policy`/version-mismatch seam (A queue #8) | no |
| L-2 | **No restart-safe Back-path medium** for Q-0231 "pop the real path" | B r1-3 · Codex 5 · FJ verify | high (3 sources) | 3/9/8 | CONFIRMED | In-memory `BackTarget`/`chain_back` closures; the one persisted medium (`navigation_stack.py`, "persisted via state_store") is **wired to zero views** and 2h-GC'd; preset/help views run 180/300s timeouts | Pin the medium (T1-2) before NavigationSpec freezes; add the Back/Home/restart oracle | ⚑ T1-2 |
| L-3 | **Hide-vs-disable contract collision** — "hidden = off" rec would reverse shipped drift-tested HLP-4/Q-0055 invariant | B r4/5 · A r145 · Codex 2 · Codex 4 · FJ verify | **highest of the day (5 sources)** | 9 | CONFIRMED (open sub-decision, not yet a reversal) | `help_projection`/overlay hide is presentation-only today; hub doc :88-92 recommends the inverse as default | Visibility/activation vocabulary split + owner T1-1 before any hub/preset/nav freeze | ⚑ T1-1 |
| L-4 | **C-1 contract cluster:** no error envelope anywhere (0 `on_app_command_error` over 31 slash cmds); slash bypasses subsystem governance today; C-1 named but has no single seam | A r3/13/14/15/53 · Codex 2 · Codex 3 · FJ verify | high | 7/2/9 | CONFIRMED (one cite corrected: `WorkflowResult` exists only in the design spec — the shipped analogue is `StageResult`, `message_pipeline.py:181`; audit A's `contracts.py:48-52` cite is fabricated) | One `resolve()` seam owned by K8; mandatory `from_exception` envelope; slash/prefix/fuzzy/NL all funnel; AST no-skip fence | ⚑ T2-4 |
| L-5 | **The panel/component surface is a SECOND resolver** — buttons never pass C-1 and `PanelActionSpec` has **no cooldown field**: open a panel once (cooldown charged once), then spam its action button freely | FJ stress (novel) | new — single source, source-verified | 7 | CONFIRMED | Design spec routes panels through the kernel panel pipeline (authority→defer→handler), no cooldown step; `CooldownSpec` is command-only | Unify: panel actions resolve through the same C-1 chokepoint (or PanelActionSpec gains cooldown/audit parity) — Gate-0 edit | no |
| L-6 | **Deploy-overlap double-fire only partially closed by #1693** — prefix commands (default `Bot.on_message → process_commands`, ungated), interactions, and non-message listeners still double-fire during LP-4 overlap | A r5/6 · Codex 3 · FJ verify (novel residual) | high | 9 | CONFIRMED | `message_pipeline.setup` registers a *listener*; no `is_shutting_down` gate on `process_commands` or any `bot_check`; fuzzy AUTO re-dispatch (`bot1.py:572`) re-enters it too | Owner T2-2: fast-release + durable per-action idempotency keys (fixes every lane at once) | ⚑ T2-2 |
| L-7 | **One-pipe-two-producers (C-2) premise false in shipped source:** the draft store is a per-guild SINGLETON (no draft_id/producer column) — two producers destructively merge; and slot-key uniqueness makes the flagship "10 D&D channels" draft **structurally unrepresentable** (10 `create_channel` ops collapse to 1 row); Accept gate hard-wired to setup authority | FJ stress (novel, extends A r22/113) | new + extends A | 3/6 | CONFIRMED | `setup_draft` unique index (guild_id, op_kind, subsystem, setting, binding); `final_review.py:86-93` owner/setup-admin-only apply | C-2 lands as *new* producer-agnostic batch primitive keyed (producer, owner_scope, draft_id) — re-baseline "not new architecture" claim | no |
| L-8 | **Restart-safety of tasks/timers systematically unbuilt:** ManagedTaskSpec has no persistence/misfire field; one-shot timers in-memory (`rps_tournament_cog.py:274`, `blackjack_cog.py:572`, `+ :410`); the only durable scheduler defaults OFF in prod | A r2/30/72/73 · Codex 5 · FJ verify | high | 3/9 | CONFIRMED | recovery paths re-arm zero timers; `AUTOMATION_SCHEDULER_ENABLED` defaults false | ManagedTaskSpec durability fields + one kernel due-queue (T2-6) | ⚑ T2-6 |
| L-9 | **No outbox / at-least-once anywhere:** commit-then-emit outside txn; "event lost" is a log line | A r7/74 · Codex 3/5 · FJ verify | high | 9 | CONFIRMED | `settings_mutation.py` commits at :338-349, emits at :385; EventSpec has no delivery field | EventSpec.delivery + in-txn outbox for audit/reward (T2-3) | ⚑ T2-3 |
| L-10 | **CUT-1's data plane is undefined — and the ambient DSN in the container is production `DATABASE_URL`:** the "zero setup prerequisite" claim rests on an ephemeral container-local Postgres that dies with every session (all live-test state lost), while the only configured DSN reaches prod; no rail says which DB the unproven bot may open | FJ stress + critics (novel; the D-3 rails are all Discord-side) | new — convergent from 2 independent agents | 3/9 | CONFIRMED | D-3 rails = guild allowlist, instance lock, verified_live — zero DB rails; Q-0213 credential set puts prod DSN in agent containers | Add the 4th kernel rail: new bot refuses to boot against a DSN not explicitly declared `test`; provision a persistent test Postgres for CUT-1 | ⚑ new |
| L-11 | **The proving model has no lane for its own redesigns:** byte-parity "red-until-parity" goldens are structurally incompatible with the day's OWN decisions (one hub, C-4 grammar, renames, D-5 re-place) — no intended-divergence mechanism distinguishes redesign from regression; plus the live co-test serializes 271 commands through one human with no throughput policy, and golden capture (Gate 1) vs live comparator (CUT-1..3, months later, multiple PRs/day) drift apart | FJ stress + critic + Codex 5 | high (3 sources) | 8 | CONFIRMED | `parity/README.md` allows exactly two golden-change reasons, neither is "intended redesign" | Third oracle lane: *redesigned* = old golden as baseline + reviewed delta-spec; co-test batching policy; pin capture date + old-bot freeze policy | ⚑ new |
| L-12 | **Owner-override gaps:** channel-access axis never consults owner tier; Q-0227 transparency audit unimplemented; override copy-pasted ~11 seams; "any server" vs shipped member-guild invariant | A r8-12 · Codex 3 · FJ verify | high | 2/5 | CONFIRMED | `command_access.py:351-352` bootstrap-only bypass; grep finds no transparency emit | One authority map behind C-1, override once at top, transparency audit in C-1 (T2-10) | ⚑ T2-10 |
| L-13 | **Authority vocabulary two-lanes vs one-label** — design spec's `capability_required`/`audience_tier` vs Q-0227's single label | Codex 2 (only reviewer to catch it) · FJ verify | verified single-source | 7 | CONFIRMED (spec is stale vs newer Q-0227, not wrong at write time) | design spec dated 07-02; Q-0227 dated 07-03 | Single `authority_ref` (T1-4) | ⚑ T1-4 |
| L-14 | **Shared-verb computation inputs broken + caps unbudgeted + hub deep-links minted outside the corpus:** ground-truth JSON yields 1 shared verb vs 11 in live source; 100/25-cap unbudgeted; Q-0231 mints per-node commands (~dozens) not in the 271-corpus K1 computes over | A r78/79/80 · Codex 4 · FJ stress (deep-link leg novel) | high | 8/10 | CONFIRMED | `btd6ops` = 1 row for 6 subcommands in the JSON | Compute from live ledger walk; bake cap budget; enumerate nav-node commands into the corpus BEFORE the K1 computation | ⚑ T1-5 |
| L-15 | **Fragmentation collapses under-sized, now with real counts:** presets/templates **9 live impls** (10-12 by split-counting; plan said ≥7) in two semantically distinct families; pagination reinvented ≥8× (none restart-safe); cooldowns 7×/3 storage models; caches 6×; descriptions 3 lanes; ~1,079 `ephemeral=True` call sites with 1 explicit False | A r31/37/66 · B r8/9/12 · FJ verify (recount) | high | 5 | CONFIRMED | verify recount settles the count dispute (§7 X-5) | Each collapse gets its own acceptance oracle (one-edit-propagates, preview-fidelity, result-matrix) before porting | no |
| L-16 | **Media generation ships with its highest-risk control undesigned:** global budget cap is one line over a spend counter that does not exist; no oracle for the whole cost/abuse posture; PII scrub doesn't cover display names. Mitigating fact found by verify: the spec's existing `external_side_effects=True → off_until_opt_in` compile rule mechanically gives media default-OFF — the *activation* class exists; the *spend* controls do not | B r18/19/33 · Codex 2 · FJ verify | high | 3/8 | CONFIRMED (activation leg softened) | spec :689, :1238 | Spend counter + fake-provider oracle (at-cap ⇒ zero calls) as L4 entry gate (T2-15) | ⚑ T2-15 |
| L-17 | **Discord platform-governance growth gate never treated as a design constraint:** unverified bots hard-cap at ~100 guilds; past verification, `message_content` approval is discretionary and routinely denied — the prefix-heavy rung-1/2 ladder and free-for-everyone growth mission collide with this externally-owned gate | FJ critic (novel — absent from all 7 reviewers' outputs) | new | 2 | CONFIRMED (platform fact + `bot1.py:76-78` hardcoded privileged intents) | — | Name it in the BUILD-PLAN: slash-first survivability posture, verification-application milestone, intent-denial fallback plan | ⚑ new |
| L-18 | **Backup/DR does not survive the cutover** — the sole backup layer is an old-repo CI workflow (self-labeled UNVERIFIED, 90-day artifact, repo-bound secret); no gate requires verified restores for the new ledger-of-record; and **rollback destroys all post-cutover writes** (no reverse importer, no data disposition for the N-day window) | FJ critics + stress D-3 (rollback leg) | new — convergent from 3 agents | 9 | CONFIRMED | `.github/workflows/backup-db.yml` header; spec :1349-1351 rollback = old worker on untouched DB | CUT-3 gains: verified-restore gate + explicit rollback-data disposition (reverse-import, replay, or declared-loss owner sign-off) | ⑂ owner |
| L-19 | **No security/abuse review class anywhere — and the rubric locks the blindness in:** the 10 classes are all structure/completeness probes; no reliability/perf/security/privacy cluster; every future review (Stage 2, Phase B, Gate-V) inherits the gap by design | FJ critic + B §8 (rubric row) | med-high (2 independent) | 8 | CONFIRMED | rubric L38-118 enumerated | Add rubric classes 11-13 (§8); one adversarial-abuse pass over the frozen surface before Gate-0 | no |
| L-20 | **Multi-user interaction is never a verification dimension:** parity harness has 3 personas but every shipped case is single-actor; the bot's defining surfaces (tournaments, trades, counting/chain, giveaways) are multi-actor state machines | FJ critic | new | 8 | CONFIRMED | `parity/harness/world.py:86-92` vs case corpus | Multi-actor golden class (challenge→accept→interleave→settle) as a Gate-V requirement | no |
| L-21 | **Frozen-reference integrity is exhortation-only while the referent keeps moving:** no checker/CI guard write-protects the frozen capstone/decision logs against always-on autonomous agents; and no policy governs old-bot feature development drifting away from the 271-command corpus, goldens, and import mappings during the months of build | FJ critics (2 convergent) | new | 4/7 | CONFIRMED | grep: no script/CI references the frozen paths; freeze exists only as prose | CI guard on frozen paths (allowlist: reconciliation/Gate-0 PRs); an interim old-bot change-policy (surface-affecting changes must update corpus + goldens) | ⑂ owner |
| L-22 | **Navigation machinery is guild-blind while presets make the hub per-guild** — Home/Back/deep-links resolve from the GLOBAL manifest; a preset-excluded node is still reachable/renderable (or strands the user); **a preset can exclude the preset-switching surface itself** (self-lockout, unrecoverable except by bot-owner override) | FJ stress (novel) | new | 9 | CONFIRMED (design-level, against spec text) | NavigationSpec/FOLLOW_PARENT take no guild config input | Nav target resolution takes (manifest × guild visibility config); mark setup/admin nodes un-excludable by construction | no |
| L-23 | **Discord-side per-guild slash-permission overrides are a second config DB the import cannot see:** ~10 surfaces ship `default_permissions`; guild admins customize per-command/role/channel in Server Settings; Q-0224 renames/regroupings silently destroy that security config at cutover | FJ critic (novel) | new | 2/9 | CONFIRMED | `settings_cog.py:198`, `moderation_cog.py:96`, `ai_cog.py:578,775`, `server_management_cog.py:77`, `btd6/_unified.py:484,924` | CUT-2 gains a Discord-side config census (API-readable) + a rename→permission-carryover map + admin-notice in the comms plan | no |
| L-24 | **Presentation-substrate riders the plan strips or forgets** (grouped): zero alt-text across all ~50 `discord.File` sites; no i18n seam despite native Discord support; `allowed_mentions` default on template sends = mass-ping vector; 48 Modal subclasses outside every BaseView guarantee (zero `on_error`); fonts unbundled (host paths + silent fallback = render-nondeterminism); autocomplete absent AND unscheduled | B §8 (deep-ingest; HIGHs not in its own top-42) | med (B-only, spot-checked) | 2/7/9 | CONFIRMED per B's adversarial pass | see B §8 rows | Each becomes a declared Gate-0 grammar field (alt_text, locale seam, allowed_mentions policy, ModalSpec under the same guarantees, bundled fonts) — not per-subsystem discipline | no |
| L-25 | **Audit-artifact defects (process):** audit B's §8 contains 3 literal placeholder rows ("t/e/f", one HIGH); audit A's r3 cites a nonexistent `contracts.py:48-52`, and its r221 verify came back with placeholder reason "test" (self-flagged) | FJ verify + ingest | verified | 4 | CONFIRMED | B §8 lines ~770/1074; A r221 note | Fix the 3 B rows on sight next docs session; fleet-level lesson: structured-output validators should reject placeholder strings | no |

**Reading the ledger:** L-1 is the only *runtime-now* item. L-2..L-9 + L-12..L-15 are the
foundation-contract cluster the audits already owned — this judgment adds independent confirmation,
corrected citations, and the novel seams (L-5, L-7's singleton/unrepresentability, L-14's deep-link
leg). L-10/L-11/L-17..L-23 are **new ground** the day's ~470 findings did not contain.

---

## 3. Re-prioritization — what moves UP (the owner's primary ask)

**The single highest-leverage next action: one owner sitting that answers the 7 Tier-1 rows (§6).**
Every path forward — Stage 2's columns, the hub/preset/nav spec, the K1 computation — runs through
those answers, they are all option-pick decisions with recommendations attached, and nothing else
on the board unblocks as much per minute of owner time.

**Do this FIRST, in order:**

1. **RPS refund fix** (V-1 / L-1) — one small owner-directed PR; don't let the next `VERSION` bump
   forfeit real fees. *(Moves up because this judgment proved #1693 was incomplete as a class fix.)*
2. **The Tier-1 owner sitting** (V-2) — 7 decisions, one session.
3. **Adopt the findings-closure rule** (V-3): this §2 ledger + both audit ledgers become *binding
   inputs* — every Stage-2 row template carries its `prompt-a-issue`/`prompt-b-issue`/`FJ-L#` tags,
   and Gate-0's checklist enumerates the L-rows it retires. Nothing floats.
4. **Launch Stage 2 with Codex 4's contract** (template + verdict vocabulary + Lane-0 normalization
   + the two mechanical inputs: shared-verb set computed from the **live ledger walk** with the
   cap budget and the **nav-node deep-link commands enumerated into the corpus first** (L-14)).
5. **Gate-0 additions locked in now** (executed at Gate-0, decided by the sitting + this doc):
   C-1 single-seam contract including the panel pipeline + cooldown field (L-4/L-5), the error
   envelope (T2-4), authority_ref (T1-4), rubric classes 11-13 (§8), the frozen-path CI guard
   (L-21), and the §7/§8 wording amendments.
6. **Before Phase-0.5 golden capture:** the intended-divergence lane + capture-date/freeze policy
   (L-11), and the multi-actor golden class (L-20).
7. **Before any CUT-1 container live-test:** the data-plane rail + persistent test Postgres (L-10)
   and the rig scheduling/reset contract.

**What can safely WAIT (explicitly de-prioritized):**

- **All of Tier-3** (§6) — batch-bless the defaults at Gate-0.
- **Media-generation detail** (L-16) beyond recording the spend-counter requirement — it's L4 work;
  the activation class already falls out of the existing grammar.
- **The substrate-kit tail (D-4)** — correctly parallel; nothing in Stages 2-3 waits on it. Add the
  one-line disposition of the strategy doc's Phase-2.5 A/B gate so two pre-bootstrap gates don't
  contradict (stress D-4 finding) — a Stage-3 checklist line, not work now.
- **i18n / alt-text / a11y riders** (L-24) — become declared Gate-0 grammar fields; no current-repo
  work.
- **Backup/DR + rollback-data disposition** (L-18) — decide at Stage 3 with rollback-window N; it
  gates CUT-3, not Stage 2.
- **Old-bot interim change-policy** (L-21) — one paragraph in the Stage-3 consolidation.

**What this re-prioritization changes vs. the audits' own rankings:** audit A ranked the
fuzzy-resolver stale-claim #1 — real, but it's a docs patch (fold into Gate-0). Audit B ranked
Back-path #1 — this judgment keeps it top-3 but sequences it as a Tier-1 *decision* rather than
build work. The genuinely new top-priority item neither audit contained is **L-1 (RPS)** — the only
row where real user money is exposed by a routine event (a version bump) in the *current* bot.

---

## 4. What's still missing (survived the whole day)

From the completeness-critic loop (4 rounds, 3 lenses each). **Honest process note:** the loop hit
its round cap still producing genuine finds (7 new in round 4) — completeness is *not* exhausted;
Gate-V should run with deliberately rotated lenses (see L-19 and the Gate-V monoculture flag).
The 31 raw misses de-duplicate to these, ranked by foundational weight; the starred ones already
graduated into §2 as ledger rows.

1. ★ **Discord platform-governance growth gate** (L-17) — verification at ~75-100 guilds +
   discretionary `message_content` approval, vs a free-for-everyone mission on a prefix-heavy ladder.
2. ★ **Rollback destroys post-cutover data / backup-DR doesn't survive cutover** (L-18).
3. ★ **No security/abuse review class — self-propagating via the rubric** (L-19).
4. ★ **Multi-user interaction never verified** (L-20).
5. ★ **Frozen-reference write-enforcement + old-bot interim policy** (L-21).
6. ★ **Discord-side permission-override config invisible to the import** (L-23).
7. **Production data is never audited or repaired** — every oracle verifies code pre-ship; nothing
   sweeps live rows for invariant violations, and the CUT-2 importer inherits silently corrupted
   rows (double-XP residue from the very bug #1693 fixed) as ground truth. CUT-2 needs a
   copy-fidelity/verify-import step too — the disposition report proves *coverage*, never
   *correctness of the copy*, and CUT-3 currently runs freeze→import→swap with no verify between.
8. **The owner is the plan's serial bottleneck and nobody did the arithmetic** — Stage 2 (43×12
   sections), ~50 queue items, per-command co-test sign-off (271), sim-winner ratifications, every
   gate. No batching/delegation/absence policy exists. (Partially mitigated by §6's tiering; a
   real throughput policy belongs in the Stage-3 consolidation.)
9. **No user-facing change-communication mechanic** — D-5 drops, Q-0224 renames, and CUT-3 itself
   have zero announcement/guild-admin-notice/support half; cutover jumps from one test guild to
   every production guild in a single token swap with no progressive ring.
10. **Credential lifecycle** — no rotation/revocation/compromise-recovery contract for the token /
    DSN / Railway credentials that Q-0213 deliberately concentrates in agent containers.
11. **Ungoverned prod-data copies in the proving pipeline** — restored snapshots in agent cloud
    containers + LLM-judged acceptance replays over imported member data; the retention/erasure
    contract only reaches the live DB.
12. **Dependency supply chain** — 12 floating `>=` runtime deps, no lockfile, re-resolved on every
    merge=deploy, agents licensed to adopt packages, no human review; posture carried into the new
    repo with zero disposition.
13. **Owner-consumable review artifacts** — every binding checkpoint hands prose walls/JSON to a
    non-coding, visually-oriented owner; nothing renders decisions visually (the collaboration
    model's own premise, unapplied to the rebuild's gates).
14. **Field-signal intake post-cutover** — no user bug-report/feedback mechanic; the verification
    lifecycle ends at cutover.
15. **Gate failure branches** — every gate after the Phase-2 go/no-go is proceed-or-fix; the named
    canaries (farm-collect, mining-last) have no defined failure arm, and no abort/fallback
    criterion exists for the program itself.
16. **Continuity of the workflow across the migration** — the 186-file idea pipeline, the routines,
    the dual-repo agent-governance interim (Phase C precedes the MIGRATION plan), the off-Discord
    surfaces (botsite/dashboard fed by an old-repo AST parser), and the kit's publication lifecycle
    (license/versioning/fix-propagation) all have no disposition in the repo-as-artifact framing.
17. **Model-availability contingency** — the plan's own provenance records Fable 5 vanishing for 19
    days mid-project; wall-clock is declared the binding constraint; no contingency exists.

Items 7-17 are **not** Stage-2 blockers. The right home for most is the **Stage-3 consolidation
checklist** (7, 8, 9, 15, 16) and **Gate-0** (10, 11, 12, 13), with 14 and 17 as standing owner
awareness. What must not happen is what critic finding 28 predicts: these evaporating because no
artifact owns them — hence V-3.

---

## 5. Judgment on the two prod fixes (#1693)

Both fixes were re-verified **line-by-line against shipped source** in this session (not delegated).
Bottom line: **both are correct, well-targeted stopgaps that do not regress anything — and both are
deliberately partial.** The residual exposure is real, was *mostly* self-declared by the fix's own
commit message, and its durable closure is already owner-queued (audit A owner-queue #2/#8). One
residual gap is wider than the fix's framing acknowledges (fix 2, prefix commands).

### Fix 1 — blackjack tournament fee refund on version mismatch (`blackjack_cog.py:229-300`)

**Correct.** The version-mismatch branch no longer `clear_by_id`s before the refund block; every row
now flows through refund-then-clear regardless of version (`blackjack_cog.py:261-287`). The refund
targets `state['bet']` (guarded `isinstance(bet, int) and bet > 0`), reason string
`blackjack_tournament:restart_refund` is forensics-filterable. The counter-test was rewritten to
assert the refund. This kills the confirmed forfeit path (audit A rank 4) for its subject.

**Residual gaps (narrow, acceptable for a stopgap — but they should be named):**

1. **Refund-failure still clears the row.** `economy_service.refund` is wrapped in try/except that
   logs a warning and falls through to `clear_by_id` (`blackjack_cog.py:270-287`). A transient DB
   error during refund permanently forfeits that fee with only a log line — no retry, no dead-letter.
2. **Clear-failure after a successful refund double-refunds on next boot.** If `clear_by_id` raises
   after the refund committed, the row survives and the next recovery refunds again. There is no
   idempotency key on the refund (static reason string, no row-id correlation). Mirror image of (1).
3. **Schema-coupled refund amount.** The refund reads `state['bet']` — "a stable top-level int" is
   true for the current schema, but a future VERSION bump that moves/renames `bet` silently reverts
   to forfeiting (the guard makes it a *silent* skip). The durable fix — a declared
   `refund_policy` on the persisted-session spec applied by one owning seam (audit A ledger #4 /
   #173, owner-queue #8) — is correctly left to the rebuild.
4. **Single-subsystem scope — and the class is NOT closed: RPS still forfeits.** Verified this
   session: `disbot/cogs/rps_tournament/_persistence.py:104-115` drops version-mismatch rows
   without refund on cog_load, exactly the pre-fix blackjack shape; the 24h `game_state_cleanup`
   refund backstop never sees the row because recovery clears it first. (The RPS *guild-remove*
   path, `:251-270`, refunds correctly — the pattern was known, the recovery path just never got
   it.) Latent today (version constants match) and it fires on the next `RPS_TOURNAMENT_VERSION`
   bump. **This makes fix 1 correct for blackjack but incomplete as a class fix — V-1 in the
   verdict.**

### Fix 2 — message-pipeline drain gate (`message_pipeline.py:264-278`)

**Correct, and the timing is sound.** `dispatch()` now early-returns when
`lifecycle.is_shutting_down()`. Verified ordering: `request_shutdown`/`request_restart` set
`Phase.DRAINING` **at request time** (`lifecycle.py:218-219, 252-253`), and the close driver
releases the runtime lock only after that (`bot1.py:851-865`) — so the gate is already active for
the entire dual-live overlap window. This closes the double-fire for **every additive
message-pipeline stage** (xp, counting, chain, cleanup, rps, four_twenty, btd6) — the widest and
most user-visible class (XP double-award on every deploy).

**Residual exposure during the overlap window (the fix's commit message scopes itself to pipeline
stages — accurately — but the ledger should carry what remains open):**

1. **Prefix commands still double-fire.** `message_pipeline.setup()` registers a *listener*
   (`@bot.listen("on_message")`, `message_pipeline.py:368-369`); discord.py's default
   `commands.Bot.on_message → process_commands` is not overridden in `bot1.py` and carries no
   drain gate — a `!daily`-class economy mutation typed during the overlap executes on **both**
   instances. (Independently re-verified by an adversarial agent: no `on_message` override, no
   drain gate in any `bot_check`; the fuzzy AUTO re-dispatch at `bot1.py:572` re-enters
   `process_commands` on the draining instance too.)
2. **Slash/component interactions are ungated** — both gateway sessions receive
   `INTERACTION_CREATE`; the interaction-token ack race stops the *reply*, not the side effects.
3. **Non-message listeners** (reactions/karma, member-join, voice) are ungated by construction.

None of these is a regression, and the durable fix is exactly the already-queued owner decision
(fast-release + per-action idempotency keys — audit A owner-queue #2, recommended there and
seconded by Codex review 3). **Judgment: ship-worthy stopgaps; do not treat the double-fire class
as closed** — the gate closed the *pipeline* lane only, and the idempotency-key decision is the
actual fix.

---

## 6. Consolidated owner-decision queue

Merged and de-duplicated from **audit A's 32-item queue + audit B's 14 + Codex 2's 10 questions +
Codex 4's pre-Stage-2 list + this session's own findings** — then **tiered by what each decision
blocks**, because the raw union (~50 items) is not a usable owner work-queue. Codex 3's critique is
adopted: a third of A's "owner-gated" items are architecture calls with an obvious default — those
sit in Tier 3 as **"bless the default in one batch"** rather than individual decisions.

Sources per row: A#n = audit A owner-queue item n · B#n = audit B §4 item n · C2-Qn = Codex 2
question n · C4 = Codex 4 §2.3 · FJ = this judgment.

### Tier 1 — answer BEFORE / AT Stage-2 start (each blocks a Stage-2 column or a spec freeze)

> **✅ ALL 7 RESOLVED — owner sitting 2026-07-03, recorded as Q-0237(a–g).** Outcomes: **T1-1** →
> visibility-only (a); **T1-2** → in-session real stack + semantic-parent fallback after restart;
> **T1-3** → admin is a **hidden** node **inside** the unified hub (amends Q-0230's "gated visible
> node"); **T1-4** → one `authority_ref`; **T1-5** → slash-common + prefix long-tail; **T1-6** →
> decided `!admin`/`!games` canonical, shipped `-menu` names become hidden aliases; **T1-7** → adopt
> Codex-4's Stage-2 kit as-is. Six matched the recommendation; T1-3 deviated (owner kept
> hidden-not-locked). **Stage-2 is unblocked** (with V-1 RPS fix + V-3 findings-closure).

| # | Decision | Options | Recommendation | Sources |
|---|---|---|---|---|
| T1-1 | **Hide-vs-disable / preset-exclusion semantics** — does display-hide EVER mean execution-off? | (a) hidden = visibility-only (shipped HLP-4 invariant) · (b) hidden = off · (c) per-feature choice | **(a)** as default + explicit per-preset "also disable" opt-in; adopt Codex 2's visibility/activation vocabulary split. Reverses the hub-doc's in-line agent recommendation — see §7 X-2 | B#1 · A#27 · C2-Q1 · C4 |
| T1-2 | **Restart-safe Back-path medium** — what carries "pop the real path" across merge=deploy? | (a) encode path in versioned custom_id (DynamicItem) · (b) DB panel-state row · (c) amend contract: real stack in-session, semantic-parent after restart | **(c) now + (a) where the path fits the 100-char budget**; pin before NavigationSpec/PanelSpec freeze | B ranks 1–3 · Codex 5 blocker 3 |
| T1-3 | **Admin gating model** — shown-locked gated node (decided) vs shipped hidden-from-non-admins; single admin gate vs multi-tier (moderator door) | (a) gated visible node, multi-tier · (b) keep hidden · (c) per-hub declared hide-vs-lock policy | **(c) with (a) as the default posture** — moderators need their own door | B#2 · B ranks 14–15 |
| T1-4 | **Authority declaration vocabulary** — one `authority_ref` vs the design-spec's two lanes (`capability_required`/`audience_tier`) | (a) single `authority_ref` resolving internally to either lane · (b) authors pick a lane per command | **(a)** — Stage-2 authors fill ONE column; Gate-0 owns the mapping | C2-Q2 · §7 X-8 |
| T1-5 | **Slash-cap policy** — 271-command corpus vs Discord's 100 top-level cap | (a) slash-common + prefix-long-tail · (b) force-group everything under ~25 areas · (c) cut the corpus first (D-5), then decide | **(a)**, with the 100/25/1-nest budget baked into the K1 shared-verb computation; D-5 triage will shrink the corpus anyway | A#16 · C4 |
| T1-6 | **Deep-link canonical names** — decided `!admin`/`!games` vs shipped `!adminmenu`/`!modmenu`/`!economymenu` | (a) decided names canonical, shipped ones become hidden aliases · (b) keep shipped | **(a)** — K1 reserves both | B#3 |
| T1-7 | **Stage-2 contract adoption** — Codex 4's row template + normalized verdict vocabulary (`keep/improve/merge/redesign/drop/defer/re-place/add`) + lane split | adopt / amend / ignore | **Adopt as the Stage-2 starting contract** (it operationalizes D-5 and the rubric per row; nothing else on the table does) | C4 · FJ |

### Tier 2 — answer before GATE-0 grammar freeze (contract-level, don't block starting Stage 2)

| # | Decision | Recommendation | Sources |
|---|---|---|---|
| T2-1 | Atomic-apply meaning for non-rollback-able Discord ops | Drop the word "atomic" for the setup lane; reserve all-or-nothing for pure-DB compound ops; write into ownership contract | A#1 |
| T2-2 | Deploy-handoff posture: drain-then-release vs fast-release + idempotency keys | **Fast-release + durable per-action idempotency keys** — fixes correctness for every listener class the #1693 stopgap can't reach (§5) | A#2 · Codex 3 |
| T2-3 | Internal event durability: outbox / at-least-once tiers | At-least-once via in-txn outbox for audit + reward paths; everything else best-effort, declared per EventSpec | A#3 |
| T2-4 | Error-envelope home | Inside C-1 (one seam, all four rungs); `from_exception` → `{user_error, denied, transient, bug}` + retryable | A#25 |
| T2-5 | C-2 boundary: which actions MUST use preview/confirm | All destructive + all AI-produced + bulk/compound; single-op reversible direct-lane actions exempt | C2-Q4 |
| T2-6 | ManagedTaskSpec durability fields (persistence/misfire/catch-up) | Yes — required for merge=deploy survival | A#6 |
| T2-7 | Payload-version-mismatch policy on persisted state | Reject-and-preserve default for any money/audit-bearing payload; refund runs before any delete (generalizes #1693 fix 1) | A#8 |
| T2-8 | Per-tenant guild lifecycle as kernel primitive (C-8) | Yes — first-class L0, manifest-derived join-bootstrap + leave-reclaim | A#14 |
| T2-9 | Per-guild enablement gate on CommandSpec at C-1 | Yes — first-class `enabled_when`, kills the shipped slash-governance bypass class | A#12 |
| T2-10 | Owner-override: member-guild wording + transparency-audit sink + fallback when the guild has no log channel configured | Member-guilds only; bot-log + server-log, firing on would-not-otherwise-authorize; fallback = bot-log + owner DM digest | A#9 · A#10 · C2-Q6 |
| T2-11 | NL-router model: universal manifest-inherit vs curated opt-in | Per-command NL-eligibility slot defaulting from description | A#18 |
| T2-12 | Custom-trigger kinds: whole-surface prefix and/or word→command | Support both as two declared kinds; state which Q-0225 authorizes | A#17 |
| T2-13 | Single-process vs shard: carry ADR-001 as named non-goal | Yes, with re-eval triggers | A#4 |
| T2-14 | DB-down posture | Refuse-with-notice uniformly, centralized at the DB adapter | A#5 |
| T2-15 | Media posture bundle: budget cap + spend counter · PII scrub · fail-closed · cache semantics | Cap with a real spend counter (highest-risk money control); scrub display names; fail-CLOSED; cache scoped per-guild unless owner opts wider | B#5 B#6 B#7 B#8 |
| T2-16 | C-7 description scope + the 100-char slash limit vs rich help | Two-field description (short + detail), one source; per-guild rename lane excluded from v1 | B#10 · B rank 27 |
| T2-17 | Ephemerality / silent-vs-reply home | Lane-driven resolver in the result grammar (C-4), not per-call-site | B#11 |
| T2-18 | custom_id standard: ratify static-stable + dynamic-versioned two-population model; amend Q-0231 wording | Ratify | B#14 · §7 X-6 |
| T2-19 | Native Discord onboarding/server-template interop for C-3 presets | Interop-aware but independent; document the boundary | B#9 |
| T2-20 | G-22 staging lanes: standardize vs bless three | Still open — carried from Stage-1 §6; must not slip past Stage 3 | A/conventions carry |
| T2-21 | Idempotency posture mandate per mutating action | Mandate a declared posture; single-flight is an allowed posture under single-process | A#13 |
| T2-22 | ⚠ ConfigSpec/SecretSpec + gateway-intent contract (both built on audit A's UNVERIFIED tier) | Verify the underlying claims once, then: yes to both | A#31 A#32 |

### Tier 3 — Phase-B/C detail: bless the defaults in ONE batch (architecture calls, obvious defaults)

Missed-window coalesce policy (A#7) · energy stays separate from C-6 (A#19) · C-6 tiers optional
(A#20) · MetricSpec yes (A#21) · CacheSpec yes (A#22) · /ready docstring rewrite, lock is the
restart seam (A#23) · ParamSpec first-class (A#24) · left-behind-side-effects record without a saga
engine (A#26) · drop dead staged-rollout machinery (A#28) · keep generic env override tier (A#29) ·
kit import renamed `substrate_kit` (A#30) · member-erasure declared in phase-1 grammar, executed
post-cutover (A#15) · card themes/uploads as declared theme packs (B#12) · did-you-mean privacy =
invoker-locked public carrier + ephemeral follow-up (B#13) · fuzzy safety classification derived
from the manifest `effect` field, never a hand-list (C2-Q5) · moderation envelope spot-check =
timeout + one of kick/ban (C2-Q7) · CUT-3 rollback window N set at Stage 3 (carry).

### Additions from this session's stress/critic pass (slot into the tiers above)

| Tier | Decision | Recommendation | Source |
|---|---|---|---|
| T2 | **Rollback-data disposition:** what happens to writes made through the new bot during the N-day rollback window — reverse-import, replay log, or declared-loss sign-off? | Decide with N at Stage 3; a rollback lever whose data cost is unstated is not a safety lever (L-18) | stress D-3 + critics |
| T2 | **CUT-1 data-plane rail:** which database may the unproven new bot open, and how is prod DSN structurally excluded? | 4th kernel rail: refuse boot on any DSN not declared `test`; persistent test Postgres for CUT-1 continuity (L-10) | stress D-3 + critics |
| T2 | **Golden capture timing + old-bot freeze/change policy for the interim** | Pin capture date; surface-affecting old-bot changes must update corpus + goldens (L-11/L-21) | stress oracle + critics |
| T2 | **Guild-sovereignty over member triggers:** may a guild admin disable a member's personal Q-0225 trigger word in their guild? | Yes — add a guild-scope disable that wins over narrower scopes for *that guild only* (amends the pure-additive union rule) | stress C-1 |
| T2 | **Co-test throughput policy:** batching/sampling/delegation for the 271-command live sign-off | Batch by hub; owner signs flows, not every command; delegate parity-green ported commands to spot-checks | stress oracle + critic 8 |
| T3 | Phase-2.5 cold-start A/B disposition vs the D-4 gate (two competing pre-bootstrap gates) | One line at Stage 3: fold, supersede, or schedule it | stress D-4 |
| T3 | Progressive-exposure ring + user comms plan for CUT-3 | Volunteer-guild ring before full swap; announcement + guild-admin notice | critics |
| T3 | Un-excludable hub nodes (preset self-lockout guard) | Setup/admin nodes un-excludable by construction (L-22) | stress hub-nav |

**The queue math:** ~50 raw items + 8 session additions → 7 Tier-1 + 27 Tier-2 + 20 Tier-3-batched.
The owner's real near-term load is **the 7 Tier-1 rows** (one sitting), then Tier-2 lands naturally
inside the Gate-0 pass where each row already has a recommended default.

---

## 7. Cross-reviewer contradiction map (reconciled)

Every place two of the day's seven reviewers (A, B, Codex 1–5) disagree — or a reviewer disagrees
with a decision doc — with this judgment's resolution.

| # | Contradiction | Parties | Resolution (source wins, Q-0120) |
|---|---|---|---|
| X-1 | Conventions doc §2.2 states "no central command-typo resolver exists"; audit A rank-1 refutes it: `disbot/utils/command_resolution.py` ships the decided AUTO/SUGGEST/NONE design, wired at `bot1.py:541-586` | conventions log vs audit A (+ Codex 3 independently confirmed A) | **Audit A is right; the decision log carries a class-4 stale claim about its own subject.** The Q-0225 *decision* stands; its "state today" paragraph is wrong. C-5 re-baselines as **port + generalize**, not greenfield. Gate-0 must patch the §2.2/C-5 prose. |
| X-2 | Q-0232 §3 agent recommendation "hidden = off (not runnable)" vs the shipped, drift-tested Q-0055/HLP-4 invariant "display-hide is presentation-only" | hub/nav log vs audit B (twice: its #4/#5) + Codex 2 + Codex 4 | **Not a frozen contradiction — the sub-decision is explicitly open — but the *recommendation* should be reversed or split.** Four independent reviewers converge: adopt the visibility-vs-activation vocabulary split (Codex 2) and answer it as Tier-1 before any hub/preset/nav spec freezes. This judgment recommends **hidden = visibility-only by default** (preserves the shipped invariant), with explicit per-preset opt-in disable. Owner call. |
| X-3 | Codex 1 "no true blocking inconsistency" vs Codex 2 "not Stage-2/Gate-0 safe without a consolidation pass" vs Codex 4 "ready after Prompt B merge" | Codex 1 vs 2 vs 4 | **All three are right at their own altitude.** No *gate-bypass* inconsistency exists (1); a handful of contract-level questions and vocabulary splits must be settled for Stage 2 to produce *consistent* output (2); and the one hard precondition (Prompt B) has since merged (4). Net: Stage 2 may start once the Tier-1 owner answers land — see §3. |
| X-4 | Codex 3 rates Prompt B "low / unavailable" | Codex 3 vs audit B | **Timing artifact, moot.** Codex 3 reviewed while PR #1691 was open; B merged the same day. No content disagreement exists. Codex 5 — which *did* read B — independently corroborates B's central "oracle-empty" thesis. |
| X-5 | Preset/template fragmentation count: "≥7" (Q-0232) vs "~14" (audit A #37) vs "~13-15 across two families" (audit B #9) | decision log vs A vs B | **Directionally unanimous — the plan under-sizes the collapse.** Exact count pending this session's recount, but the judgment is unchanged at any value ≥7: C-3 is a larger job than one plan line, and it needs B's two-family distinction (draft-bundle vs policy-value) plus its own acceptance oracle. |
| X-6 | Q-0231 "versioned custom_id" wording vs design-spec §3.4 (versions only *dynamic* ids; static hub ids stay stable) vs shipped reality (all static, zero versioned) | hub/nav log vs audit A #134 vs audit B #25 | **A and B agree with each other against the decision log's wording.** The contract *intent* (restart-safe panels) is sound and largely already shipped via `timeout=None` + static ids + re-registration; Gate-0 amends the Q-0231 wording to the two-population model instead of implying every id is versioned. |
| X-7 | Q-0227 "run any command in any server" vs shipped member-guild-only invariant (`capability.py:97-136` + regression test) | conventions log vs audit A #120 | **Source wins: the shipped invariant is member-guilds-only, and it is the safer contract.** Flag to owner as a wording amendment (audit A owner-queue #9 recommends member-guild scoping; this judgment concurs — "any server" without membership would be a new product decision with real abuse surface). |
| X-8 | "One authority label mapped in one place" (Q-0227) vs design-spec's two mutually-exclusive lanes (`capability_required` / `audience_tier`) | conventions log vs design spec (found by Codex 2) | **Real Gate-0 blocker, correctly flagged only by Codex 2** (neither audit caught it as a vocabulary collision). Resolution: one public `authority_ref` that internally resolves to either lane — decide before Stage-2 authors fill the authority column. |
| X-9 | Design-spec §4.4 "safe-default-ON posture today" vs shipped `DEFAULT_ENABLED=False` across automod/counter/welcome/AI (karma the lone ON) | design spec vs audit A #40 | **Source wins; the spec's claim about *today* is false** (activation posture is from-scratch grammar work, not a port of an existing ON posture). Class-4 stale claim; Gate-0 sweep item. |
| X-10 | Audit A's own quality self-reports: ledger row 221's adversarial verdict came back with placeholder reason "test"; 11 config/secrets + intent issues UNVERIFIED | audit A internal | **Treated as A reported them: unvetted leads, not confirmed findings.** They are kept out of this judgment's confirmed ranks; the two ⚠ owner-queue items built on them (#31 ConfigSpec, #32 intents) stay in the queue but flagged as needing one verification pass first. A's honesty here is a process credit, not a debit. |

**Meta-note on reviewer agreement:** across ~470 combined findings, the seven reviewers produced
only the ten genuine tensions above, and **zero cases where two reviewers assert incompatible
facts about the same source line** — every contradiction is doc-vs-source or
recommendation-vs-recommendation. The day's fact base is unusually solid; the disagreements are
concentrated exactly where the owner has not yet ruled (hide-vs-disable, authority vocabulary,
custom_id wording).

---

## 8. Meta-judgment — the rubric and the decisions themselves

### The 10-class rubric (Q-0233): holds, with two candidate additions

Every finding across A (246), B (220), and the 5 Codex reviews mapped into the ten classes without
forcing — the rubric passed its first real-scale test (B's distribution: verification-hole 48 +
ux-contract-gap 48 = the two dominant classes, exactly the "proving half" headline). Two gap
*families* recurred that fit only awkwardly (both currently squeezed into class 2/3):

- **Candidate class 11 — cost / quota / abuse posture gap:** "who pays, what caps it, where is the
  spend counter" (media budget cap, free-for-everyone cooldown posture, cache-by-prompt-hash
  economics). The owner is the payer; this class is existential for the mission and currently has
  no probing question of its own.
- **Candidate class 12 — privacy / retention / erasure gap:** PII-in-prompts, cross-guild cache
  reuse, member-data erasure, guild-leave retention. Adjacent to but distinct from class 9
  (lifecycle-contract), with legal weight the other classes don't carry.

Recommendation: add both at Gate-0 (cheap, and Stage-2 walks then probe them 43×). Not owner-gated
per se — the rubric is a tool — but flagged since Q-0233 froze the ten.

### The decisions Q-0219…Q-0236: none unsound; eight carry amendments (wording/spec, not reversals)

All seven stressed decision areas returned **HOLDS-WITH-FLAGS**; audit A's 35 per-mechanic
recommendations contain **zero** that contradict a frozen decision (all are keep/centralize/tighten).
The amendments each decision owes Gate-0 — every one an evidence-backed flag, never a reversal:

- **Q-0219 (S-1):** Tier-2 "composition" names an orchestration grammar that does not exist yet —
  specify the chaining/conditional grammar (or route those flows to Tier-3 explicitly) before
  Phase-B authors hit it; define the engine-vs-counted-handler boundary (game-rules modules are
  currently claimable as either); note the S-2 dormant-seam rule is a sanctioned exception to
  guardrail 7.
- **Q-0224 (naming):** compute from the live ledger walk, not the ground-truth JSON (1 vs 11 shared
  verbs); bake the 100/25/1-nest cap budget in; enumerate the Q-0231 nav-node deep-link commands
  into the corpus **before** running the computation (L-14).
- **Q-0225 (ladder):** patch the false "no central resolver" state claim (X-1); reconcile the
  decided tier semantics with shipped behavior (decided *silent* NONE vs shipped visible reply;
  decided *private one-tap* SUGGEST vs shipped public text — and "private" is API-impossible for a
  message-origin typo without a carrier-message design); add a guild-scope disable to the additive
  trigger union (sovereignty); place rung-3's cooldown check **before** the paid AI call.
- **Q-0227 (authority):** "any server" → member-guilds (X-7); specify the transparency-audit sink +
  no-log-channel fallback; adopt the single `authority_ref` vocabulary (X-8).
- **Q-0231 (navigation):** amend "versioned custom_id" to the two-population model (X-6); state the
  Back-after-restart carve-out once T1-2 is decided; make nav-target resolution guild-config-aware
  (L-22); resolve the parent_hub authority triple-claim (sim [A] vs Stage-2 owner vs declared
  semantic parent).
- **Q-0232 (presets):** split visibility/activation vocabulary; the in-doc "hidden = off"
  recommendation is contradicted by the shipped invariant and 4 reviewers — re-decide as T1-1;
  define tweaked-preset update semantics (auto-mutate vs snapshot); un-excludable nodes.
- **Q-0222 (cutover):** add the data-plane rail (L-10), the rollback-data disposition (L-18), a
  verify-import step between freeze and swap, the shadow-run/compat-scoreboard stage D-3 dropped,
  and the user-comms/progressive-ring half.
- **Q-0234/Q-0235 (oracle/sim):** add the third oracle lane for *redesigned* ported features; a
  co-test throughput policy; benchmark falsifiability rule (paywalled competitor behaviors need an
  evidence-kind field, per Codex 5); Gate-V runs with rotated lenses (monoculture flag) and
  re-fires at Phase-B granularity for the plans actually built from; **Q-0235's prior-art list
  needs one correction — `claim_layout_sim` is a git-merge-conflict simulation of the claims
  ledger, not a UX-layout sim; the unification is over the other four.**

**Q-0233 (rubric):** add candidate classes 11 (cost/quota/abuse) and 12 (privacy/retention/erasure)
from §8 above, plus **13 (security/abuse + non-functional)** — independently demanded by a critic
and by audit B's own §8 ("rubric has no runtime/non-functional class cluster"). Three sources,
same hole: without it, every downstream review inherits the blindness by construction.

---

## 9. Pointers

- Judged inputs: §0 table. Session log: `.sessions/2026-07-03-phase-a-final-judgment.md` (PR #1701).
- The verdict + re-prioritization feed: the Stage-2 subsystem walk (with Codex review 4's template
  as its starting contract) and the Gate-V verification fleet (with Codex review 5's checker/oracle
  schema demands folded).
