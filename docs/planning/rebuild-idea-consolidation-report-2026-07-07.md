# Rebuild idea-consolidation report (2026-07-07)

> **Status:** `audit` — the fold-and-re-verify pass over the plan of record
> ([`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md)), executed per the
> [idea-consolidation brief](rebuild-idea-consolidation-fable5-ultracode-brief-2026-07-07.md) under
> **Q-0241** (never-wait, silence=consent) and **Q-0240** (decide-and-flag). Scope: fold today's four
> owner-raised captures + re-verify the brief's five §3.C critique points + a free hunt. **Not** a
> fresh A–H review — the [final review](rebuild-final-review-report-2026-07-07.md) stands untouched.
> Evidence: a 9-lane parallel source-verification fan-out (~1.17M tokens, 376 tool calls; every
> load-bearing claim carries `path:line`; the decisive citations re-verified first-hand by the
> coordinator). Source wins over this report (Q-0120). Products: canonical-plan **§11b amendments
> A-12…A-20**, registry mints **R-16 / R-17 / P-5** (`rebuild-amendments.yml`, checker green),
> the owner-briefing correction, and the idea-doc routing updates.

---

## 1. What folded — the nine amendments at a glance

| Row | One line | Lands at |
|---|---|---|
| A-12 | `Lane.ROLE_SET` + channel-access role-sets (allow **and** deny-until-role), rider **R-16** — before K6 is built | K6/S7 |
| A-13 | User-self-service automation on K9's due-queue; category B fenced OFF pending the pricing session; **R-17 + P-5** | K9/S10 |
| A-14 | Moderation decide-at-port anchors (join-verify gate + ban-appeal intake); trigger→response stays backlog | step 13 band 2 |
| A-15 | `run_export` (erasure's read twin) widens S11; guild-config backup/restore = a band-1 draft-lane consumer; one-inventory rule | S11 + band 1 |
| A-16 | Parity-depth floor: 100% declared-surface-or-exempt at the `pending→ported` flip + post-flip count ratchet (`check_parity_depth`) | step 11 / gate 5 |
| A-17 | Knowledge-domain eval gate, band 7: deterministic tier REQUIRED, semantic tier advisory; projmoon must mint a corpus | step 12 + band 7 |
| A-18 | The human `verified_live` lane budgeted: tiered registry, per-band batches, CUT-3 coverage-debt list, capability-claim correction | V-5 + steps 13/15–17 |
| A-19 | Escape-hatch ratchet wired (`check_escape_hatches` in manifest-validate at K2/S3), baseline-pinned, permanent post-cutover | K2/S3 |
| A-20 | N=7d affirmed; day ~8–10 post-window checklist + importer column pin for streak/cooldown state | steps 15/17 |

## 2. The four captures — dispositions

### 2.1 Channel-role-scoped authority gap → **FOLDED (A-12, R-16)** — the time-sensitive one

Every citation in the idea doc spot-checked true, and the lane found the gap is *deeper* than
captured: the live governance stack contains **vestigial role-override plumbing that was never
wired** (`PolicySource.ROLE_OVERRIDE` exists at `disbot/governance/models.py:74`, the resolver's
scope→source map includes "role" at `resolver.py:128`, yet `_build_scope_chain` never emits a role
scope and `cache.py:43`'s `_guild_has_role_overrides` is never set True anywhere) — dead code that
*corroborates demand* and now carries an explicit do-not-port kill note. The frozen K6 design has
the identical shape: `Lane{CAPABILITY, TIER}` with a pinned total classifier
(`04-authority-engine.md:125-129`), an `AuthorityRequest` that carries **no role information at
all** (only the collapsed `member_tier` string), and a role-blind `ChannelAccessDecision`.

**Shape decision (differs from the idea doc's sketch in two load-bearing ways):**

1. **Both legs, one amendment.** The frozen design deliberately separates authority (*who*) from
   channel-access (*where*) — spec 04 §8's "Channel-access placement" fork, decision (b). A lone
   `Lane.ROLE_SET` cannot express "only role X in channel Y"; a lone channel-access extension
   cannot express "only role X may use feature Z." So R-16 carries both: the `role:<binding_name>`
   authority lane **and** an optional per-channel role-set on the channel-access policy (not a 4th
   `AccessMode` — the three shipped value strings stay frozen).
2. **Refs name a declared role *binding*, never literal role IDs.** Specs are guild-agnostic [S]
   grammar; the data path already exists frozen (`BindingKind.ROLE` + `BindingSpec.multiplicity`),
   so the lane needs no new storage grammar — only the ref form, `role_ids` on
   `AuthorityRequest`/`ActorRef` (riding the already-queued RC-12 seam batch, so it costs almost
   nothing now), and the resolution rule. Interaction-time re-check comes free from the K8 no-skip
   resolver + `re_check_actor: Literal[True]` — no new rule needed.

Plus the free hunt's deny-semantics extension (§4 find 4): the lane must express
**quarantine/deny-until-role**, because its first concrete consumer (A-14's join-verification
gate) is the *inverse* of an allow-set. The live-bot convenience half (`!channel restrict
<channel> <role>`) is confirmed separable (pure `disbot/` caller surface over already-audited
plumbing) → routed to the live-bot backlog, consciously weighed against CUT-3 proximity.

### 2.2 User-self-service automation scheduler → **FOLDED (A-13, R-17, P-5)**

The frozen K9 grammar has **zero user-scoped concept** (`TaskScope{GLOBAL, GUILD}`, every fire
runs as `SYSTEM_ACTOR`), and the final-review corpus never mentions the idea — genuinely new, only
to add. The minimal shape rides three existing seams: the spec-09 §5 *producer-armed* task pattern
(the automation_rules import already distinguishes producer-armed from manifest-declared tasks —
frozen doctrine, not a new pattern), the A-9 *reserved-but-unconsumed* pattern for category B, and
the spec-10 **`PER_ACTOR_QUOTA`** socket that pre-named exactly the per-user bound the guardrails
need. Three verification results worth naming:

- **The category-A/B split is structurally clean, twice over:** a compile fence makes `action`
  eligibility a SEMANTIC_VIOLATION until the pricing session rules, *and* sequencing makes pricing
  unbuildable at K9 time regardless — the economy engine ports at band 3, after K9 at step 10. The
  K9 build cannot stall on economics; the pricing session cannot be forced early. Exactly the split
  the brief asked to confirm.
- **The idea doc's Q-0039 citation was wrong in a useful way:** the operative allowance for a
  coins+XP unlock is Q-0039's *earned-track* clause ("milestones, no money … normal game
  progression"), not the cosmetic-only clause. Corollary folded into A-13: automation capability is
  **never** donation/real-money purchasable.
- **`TaskScope.USER` rejected** (one lane proposed it, one argued against; the coordinator sided
  with the minimal shape): user identity lives in the payload + a per-user domain store declared
  `data_class=MEMBER_ID` — which makes erasure and reclaim ride the S11 walk *for free* instead of
  growing the frozen due-queue schema and inventing a user-leave twin of C-8.

The fire-time authority rider (creator's `ActorRef`, never the SYSTEM_ACTOR bypass) and the
quiet-hours + condition-poll R-17 carriers came from the free hunt — see §4 finds 1–3.

### 2.3 Moderation feature gaps → **THIN ELEVATION (A-14)**, deliberately not new scope

The judgment call came out *elevate items 1–2, backlog item 3* — but thinner than the idea doc
implies, because the verification found **the owner already committed half this territory on
2026-07-05**: walk row 6 commits a case/appeal system and row 9 commits the quarantine action as
required Phase-B deliverables. A band-2 builder executing those commitments without today's idea
doc in view would decide the quarantine shape without the verify-gate variant and the case/appeal
shape without the banned-user intake question — exactly the evaporation the §11 named-landing
pattern exists to prevent. So A-14 anchors decisions to committed work rather than committing new
scope. Two constraints folded in: the gate must stay **button-verify, zero-PII, no external calls**
(the Q-0111 declined tiers 3/4 must not be re-litigated by "CAPTCHA" phrasing), and true banned-user
appeal implies a **DM (non-member) intake surface** — genuinely new for this bot (the ticket system
is guild-only, `ticket_cog.py:60-63`), owned by K5 admission.

Item 3 (trigger→response) stays backlog with *zero* evaporation risk: a full prior design exists
(`community-platform-features-2026-06-12.md` §4 — which the idea doc's "never captured before"
claim missed; corrected there), G-11 is minted pending, and the frozen grammar pre-names "triggers"
as an IntentSpec capability class.

### 2.4 Guild-config backup/restore + GDPR export → **FOLDED (A-15)** — the cheapness claim held, with one honest correction

The "rides S11/S14" claim verified **true for the hard half, understated for the rest**: the
erasure executor's ENUMERATE step walks the compiled `data_class != NONE` StoreSpec slice with
machine-complete coverage by CI construction — that inventory (the completeness proof, the hard
part) is directly reusable read-mode, and S11 *also* lands `cost_posture`/`quota_ref` (the throttle
an export command needs) in the same step. But export is a **small feature riding a free
inventory, not a pure rider**: delivery format, cross-guild aggregation, Art. 15(4) third-party
filtering, and tombstone-ordering are real (bounded) design points, and A-15 says so rather than
pretending it's free. GDPR verdict: Art. 15 access almost certainly applies (EU operator,
multi-guild public bot, Discord IDs are personal data — the frozen grammar itself encodes
`MEMBER_ID` as pseudonymous), but the law requires *answering requests*, not shipping a command —
so mechanized export is a **posture-consistency** choice (matching the already-mechanized erasure,
"enforce don't exhort"), flagged as such for the owner.

Two genuine finds beyond the idea doc: the **erasure executor itself is single-guild**
(`run_erasure(guild_id=…)`) while a GDPR request is account-level — A-15 fixes the cross-guild gap
for *both* walks in the same S11 session; and guild-config **restore** is ~already specced — the
reserved `Producer.IMPORT_REPAIR` + spec-06's retired T2-19 boundary ("we can read a template into
ops") make it a draft-lane consumer at band 1, explicitly **not** S14 (which verified whole-DB-only).

## 3. The §3.C re-verify — five verdicts

| # | Critique point | Verdict |
|---|---|---|
| 1 | Layer-V depth "widen per band" is a norm, not a gate | **CONFIRMED → A-16.** The commitment was a build task + prose note — no number, no owner of the number, no red check ("blocking: no" on the P-5 punch-list row). The floor is **count-based, flip-anchored**: 100% declared-surface-or-exempt at the `pending→ported` flip + a post-flip count ratchet, enforced by `check_parity_depth` *inside* the existing `golden-parity` gate. Percentages were rejected on thin-denominator math (most subsystems declare 1–5 surfaces → any X% degenerates to 0-or-100); band-declared targets were rejected because under never-wait the declarer and satisfier are the same unsupervised agent. Key discovery: `parity/parity.yml` doesn't exist yet, so the depth section costs ~nothing now and a migration later. Honest limit flagged: the gate binds at ship-time (the flip), not at band start. |
| 2 | AI/knowledge verification should be required for band 7 | **HYBRID → A-17.** A required *live-judge* gate is infeasible (judge-outage⇒FAIL, provider-degrade⇒FAIL, paid, nondeterministic) **and forbidden by the frozen design-spec §8 Q9 socket-deny decision** — but the brief's framing understated today's reality: three deterministic eval layers (grounding corpus, anchor re-derivation, coverage ratchet) *already run in required per-PR CI*; only the llm_judge layer is opt-in. So the deterministic tier becomes required band-7 exit criteria (mostly *keeping* existing protection — parity goldens capture only the AI path's deterministic denial and prove nothing about generative answers), the semantic tier stays advisory with pinned-baseline flag-on-drop + mandatory-to-run milestone runs. Named deliverable: **projmoon has no corpus** — band 7 must mint one. |
| 3 | The human verified_live bottleneck isn't budgeted | **CONFIRMED, worse than suspected → A-18.** The ~2-week floor is explicitly agent-velocity math; humans appear only as 4 decision-gates' latency; and post-Q-0241 the owner briefing *actively denied* remaining human work ("no human gates remain") while §5 step 12 still schedules the owner walking verified_live items. The exact analysis was already done 2026-07-03 (final-judgment finding #8: "nobody did the arithmetic") and then dropped by the consolidation. A-18 does the arithmetic (~150–250 units, ~15–30 h serial if big-banged → ~15–30 min/band if batched), tiers the registry, and defines CUT-3 debt disposition. Two contradictions surfaced and flagged (see §6). |
| 4 | Is the manifest-fit ratchet permanent post-cutover? | **WORSE THAN THE QUESTION → A-19.** There is no ~15% allowance rule and no "fit may never decrease" rule anywhere; the §2.9 ratchet checker is specified as CI-failing but has **no landing step in the entire program** (not in K-bands, S0–S15, step 11, or Gate-0) — it would silently never be built. And its "acknowledged in the PR" semantics have no mechanical form (unimplementable as specced). A-19 wires it (`check_escape_hatches` in manifest-validate at K2/S3), hardens it to the proven A-2 pinned-baseline ledger pattern (counts, not share), and stamps the CUT-3 baseline as the permanent year-two ceiling. V-2 (the hand-classified 85.26% ledger) honestly retires at cutover — the mechanical count is its successor. |
| 5 | Does any game cycle outlive the 7-day rollback window? | **N=7d SOUND → A-20 (no extension).** Grounded inventory: no live game/economy system has a weekly-or-longer bot-side cycle — the weekly automation templates are dormant (scheduler env-gated OFF, kept off by the B-2 rider), BTD6 CT weekly is external read-only, and the true >7d-latency mechanisms (temp role grants ≤1y, 30/90/365d time tiers, ≤7d karma pair cooldown) all fail forward-fixably. Extending N would destroy more than these bugs cost. What *was* real: a day ~8–10 post-window checklist, an importer column-carriage pin for streak/cooldown state co-located in money stores (spec-13's aggregate upsert leaves column scope unstated — a day-1 streak reset is the likeliest visible import bug), and spec-13 T-7's containment inherited by the CUT-3 runbook. |

## 4. The free hunt — five finds, all folded

1. **User automations would have bypassed the new role lane entirely.** Every scheduled fire runs
   as `SYSTEM_ACTOR` through K6's scripted bypass ("scheduled tasks are not authority-gated") — so
   a user-scoped automation could fire in a channel its creator's roles no longer allow, and
   neither idea doc covered deferred-execution authority. The live executor has the identical hole
   as an acknowledged never-finished TODO (`automation_executor.py:133-135`) — spec-09 froze the
   workaround as design. → A-13's fire-time ActorRef rider (R-17).
2. **Quiet-hours has no frozen carrier.** Live, shipped scheduler behavior (skip + advance,
   wrap-around windows) that spec-09 "retires" without a home — and an owner-named guardrail for
   the user scheduler. → R-17's delivery-window field, skip-vs-defer × MisfirePolicy pinned at the
   fold.
3. **TriggerKind is the next `Lane{CAPABILITY,TIER}`-class outgrown closed enum.** Three of the
   live substrate's seven trigger kinds (the condition-poll class) map to nothing frozen; §2.4
   B-2's "the frozen specs already close all of it" was false for them — corrected in place.
   → R-17.
4. **The join-verification gate is the role lane's first consumer, and it needs deny-semantics.**
   Allow-only `ROLE_SET` would have forced the moderation band to bolt on a second bespoke
   mechanism — the exact smear the rebuild exists to kill. → A-12's allow+quarantine sentence.
5. **Three parallel store-walk inventories were about to be built** (erasure's, the CUT-2
   importer's, and export/restore's). → A-15's one-inventory rule.

## 5. Corpus corrections made in this pass

- Canonical plan §2.4 B-2: condition-poll/quiet-hours correction (in place, pointered to A-13).
- Owner briefing §7: "no human gates remain" corrected to name the bounded lane-B click-through
  budget (A-18).
- `moderation-feature-gaps-2026-07-07.md`: item 3's "never captured before" claim corrected (a
  full prior design exists at `community-platform-features-2026-06-12.md` §4 + a live UX-lab
  mockup); item 2 noted as partially subsumed by walk row 6's committed scope.
- `guild-config-backup-and-data-export-gap-2026-07-07.md`: the garbled "§11 A-… adjacent" citation
  fixed (erasure lands via the S11 build-order row).
- `user-self-service-automation-scheduler-2026-07-07.md`: the Q-0039 citation corrected
  (earned-track clause, not cosmetic-only).
- All four idea docs' "Recommended routing" sections now point at their landings.

## 6. Decisions log (Q-0240 — ⚑ = flagged for veto)

| # | Decision | Rationale (one line) |
|---|---|---|
| ⚑ IC-1 | Role-scoped authority ships as **rider R-16**, not family G-25 | vocab addition to existing types; R-2 ("two-lane authority extension") is the exact precedent — G-25 is equally checker-legal if the owner prefers the status/spec_ref machinery |
| ⚑ IC-2 | `role:` refs name a declared **binding**, never literal role IDs | specs are guild-agnostic [S] grammar; a literal-ID escape hatch would be a guild-config policy surface, not spec grammar |
| IC-3 | Registry IDs minted NOW; owning-spec + Gate-0 freeze edits execute at each row's build step | the R-1…R-15 precedent (minted 2026-07-04, freeze at fold); unlike A-9's G-19 directive, R-16/R-17 have owning build steps (S7/S10) so they cannot evaporate |
| ⚑ IC-4 | Category-B automation: compile-fenced OFF; unlock rides Q-0039's earned track; **never real-money purchasable** | the owner ruled B exists-but-paid; the fence + band-3 sequencing keep pricing fully out of the K9 build, per the owner's dedicated-session instruction |
| IC-5 | `TaskScope.USER` rejected — payload identity + `data_class=MEMBER_ID` domain store | no frozen due-queue schema growth; erasure/reclaim ride the S11 walk for free |
| ⚑ IC-6 | Interval-floor + per-user cap defaults = Tier-3 numbers set at the K9 fold, not routed to the owner | Q-0240 decide-and-flag; both reversible settings on an unshipped kernel |
| ⚑ IC-7 | Moderation items 1–2 elevated as **decide-at-port anchors**, not committed scope; item 3 backlog | anchoring to the owner's 2026-07-05 committed walk rows prevents evaporation without exceeding his decisions |
| ⚑ IC-8 | Export mechanized (S11 twin) despite manual-DSAR legal sufficiency | posture-consistency with the mechanized erasure; the owner may deliberately decline (GDPR reading is general knowledge, not legal advice) |
| ⚑ IC-9 | Cross-guild (account-level) scope added to **both** privacy walks | a GDPR request is account-level; erasure shares the single-guild limitation — same session, same fix |
| ⚑ IC-10 | Depth floor = 100%-or-exempt at the flip + count ratchet; % floors and band-declared targets rejected | thin denominators degenerate percentages; self-declared targets are self-grading under never-wait |
| ⚑ IC-11 | Eval gate hybrid: deterministic tier required, semantic advisory (mandatory-to-run at milestones) | frozen §8 Q9 forbids a live judge in required CI; the deterministic tier is already required in today's repo — dropping it would be a regression |
| ⚑ IC-12 | Unsigned human-tier verified_live rows ride through CUT-3 as a **published debt list** | reconciles never-wait with verification-review §4.6; the owner may prefer a hard block — vetoable |
| ⚑ IC-13 | Q-0241's "agent can drive all commands live" parenthetical: corrected at citing sites, **flagged not edited** in the router | the frozen A-10 constraint wins per Q-0120, but the owner dictated the Q-0241 wording — he may know a mechanism the corpus doesn't record |
| ⚑ IC-14 | Escape-hatch ratchet: baseline-pinned counts, permanent post-cutover ceiling, inside manifest-validate | "acknowledged in the PR" is mechanically undefined; counts resist denominator stuffing; strengthens owner-ratified §10.2(4) — vetoable |
| IC-15 | N=7d kept; targeted checklist + importer pin instead | every >7d mechanism fails forward-fixably; late rollback destroys more than it saves |
| IC-16 | Live-bot `!channel restrict` command → live-bot backlog, not this plan | pure `disbot/` caller surface; value decays at CUT-3; new-bot equivalent rides G-18 at the channel band |

## 7. What the owner may want to veto (the compact list)

IC-1, IC-2, IC-4, IC-6…IC-14 above — plus, from the amendments themselves: A-18's coverage-debt
disposition (vs hard-blocking CUT-3) and delegation question (may a non-owner human sign Q-0234
rows?); A-17's paid milestone-run cadence; A-19's tightening of ratified §10.2(4). Silence =
consent (Q-0241). Nothing in this pass waits.

## Evidence base

Nine parallel Fable-5 research lanes (2026-07-07): K6 authority shape · K9 scheduler shape ·
moderation gaps · backup/export · parity-depth floor · AI eval gate · verified_live budget ·
ratchet permanence · cadence + free hunt. ~1.17M subagent tokens, 376 tool calls, all claims
`path:line`-cited against live source + the frozen corpus; the coordinator re-verified the decisive
citations first-hand (spec-04 Lane/AuthorityRequest, spec-09 TaskScope/SYSTEM_ACTOR, design-spec
§2.9/§8-Q9/six-gates, the parallel plan's 2-week floor, the registry mechanics). Where a lane and
an idea doc disagreed, source won and the correction is recorded in §5 (Q-0120).
