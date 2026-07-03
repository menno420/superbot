# Final judgment — the 2026-07-03 Phase-A day, reconciled (Fable 5)

> **Status:** `audit` — *(sections marked PENDING are being finalized in-session; complete before
> PR #1701's card flips green)*. Produced by the Fable-5 max-reasoning capstone session the owner
> directed via
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
read, and ran a completeness-critic loop over the whole day. §1–§4 carry the results.

---

## 1. VERDICT

<!-- PENDING-WORKFLOW: final verdict + blockers table filled after verify/stress/critic results -->

---

## 2. Master reconciled issues ledger

<!-- PENDING-WORKFLOW: rubric-scored, ranked, de-duplicated across A + B + 5 Codex + own findings -->

---

## 3. Re-prioritization — what moves UP

<!-- PENDING-WORKFLOW -->

---

## 4. What's still missing (survived the whole day)

<!-- PENDING-WORKFLOW: completeness-critic loop results -->

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
4. **Single-subsystem scope.** <!-- PENDING-VERIFY: rps/other pre-debited version-drop paths -->

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
   instances. <!-- PENDING-VERIFY: independent confirmation -->
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

<!-- PENDING-WORKFLOW: any additional owner-gated items surfaced by stress/critic agents -->

**The queue math:** ~50 raw items → 7 Tier-1 + 22 Tier-2 + 17 Tier-3-batched. The owner's real
near-term load is **the 7 Tier-1 rows** (one sitting), then Tier-2 lands naturally inside the
Gate-0 pass where each row already has a recommended default.

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

### The decisions Q-0219…Q-0236: none unsound; five need amendments

<!-- PENDING-WORKFLOW: finalize after stress results -->

---

## 9. Pointers

- Judged inputs: §0 table. Session log: `.sessions/2026-07-03-phase-a-final-judgment.md` (PR #1701).
- The verdict + re-prioritization feed: the Stage-2 subsystem walk (with Codex review 4's template
  as its starting contract) and the Gate-V verification fleet (with Codex review 5's checker/oracle
  schema demands folded).
