# Rebuild Phase A · Stage 1 — the global review: decisions log (2026-07-03)

> **Status:** `plan` — **Phase-A companion decisions log #1** (the vehicle
> [`rebuild-planning-phase-2026-07-03.md`](rebuild-planning-phase-2026-07-03.md) names for Phase-A
> output). Records the owner-live **Stage-1 global review** of the frozen
> [`NEW-BOT-BUILD-PLAN.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md):
> the decided standards, the dependency-order audit, the plan deltas Gate-0 must fold, the state
> corrections, and what Stages 2–3 still owe. **The frozen capstone artifacts are not edited** —
> deltas ride this log, per the phase doc's "annotated BUILD-PLAN *or companion decisions log*" rule.
> **Provenance:** owner + agent live session 2026-07-03 (PR #1679); the standards review ran at
> owner-escalated reasoning (Fable 5 max) at the owner's explicit request. Owner rulings recorded as
> **Q-0219…Q-0223** in the question router. Where this log and shipped source disagree, source wins
> (Q-0120).

---

## 1. The stage map — owner's three review stages ↔ Phase A

The owner runs the Phase-A content review as **three stages** (his vocabulary; recorded here so the
two vocabularies never drift):

| Owner stage | = Phase-A slice | Goal | State |
|---|---|---|---|
| **Stage 1 — global review** | this log | understand the whole plan; audit order; catch forgotten/misplaced steps; set the cross-cutting standards | **done** (this session) |
| **Stage 2 — the subsystem walk** | phase-doc seed agenda items 1–4, 6–7 | walk all 43 subsystems with the Stage-1 lens: exact command surface + names, kind (slash/prefix), hub placement, outperform list, **triage verdict** (D-5) | next |
| **Stage 3 — consolidation** | Phase-A close | reconcile the walk into the final surface record; feed Gate-0; owner ratification | after Stage 2 |

Phase B (per-step 100%-complete plans) starts only after Stage 3, exactly as the phase doc gates it.

---

## 2. The decided standards (binding for every Phase-B plan)

### S-1 — The engine / declaration / seam standard (the generalization keystone) — Q-0219

The owner's requirement: *every foundational function is a plug-and-play entry for any future
function — a base structure steered by the thing calling it.* The owner himself flagged the
apparent conflict with centralization ("sounds like the methods would live in multiple places").
The resolution, agreed live and sharpened by the escalated review:

**What varies per caller is *data*, not *code*.**

1. **One engine per domain, in exactly one place.** The engine owns structure, control flow,
   transactions, audit. Engines are **per-domain** (card renderer, workflow engine, ingestion
   pipeline) — never one universal engine. Cross-engine composition happens via the workflow
   engine, not engines calling each other ad hoc.
2. **Callers steer with explicit declarations.** Three tiers, used in order, dropping down only
   when forced:
   - **Tier 1 — declarative parameters** (data in the manifest): ~90% of steering.
   - **Tier 2 — composition**: assembling declared pieces (workflow lanes chaining specs). Still data.
   - **Tier 3 — a named handler seam** (the *only* per-caller code): the declaration names a
     registered function (`handler_ref`), the engine calls it at a defined seam.
3. **Handlers are leaves.** A handler computes and returns a result; it never orchestrates other
   specs, opens its own transactions, or takes over flow. A handler that starts orchestrating is a
   review smell — handlers are counted under the design spec's escape-hatch ratchet (§2.9
   discipline: justified + counted).
4. **Steering is by explicit spec, never by call-site identity.** No behavior branching on *which
   code* called the engine (no stack inspection, no implicit ambient context). Precision: the
   invoking **user/authority context** legitimately affects behavior — but it arrives as explicit
   data in the request envelope, not by inspecting the caller. Rationale: implicit call-site
   behavior is invisible and unsimulable — it would violate the owner's own 100%-visibility rule
   (§4 of the review) and the simulability contract (spec §2.10).
5. **The second-consumer rule** governs *when* to build the general engine: generalize into an
   engine when a **real second consumer exists now or is clearly imminent**; with only one
   consumer, keep the logic specific **but shaped behind a clean seam** (declaration in → result
   out). Precedent inside the frozen plan itself: R-12 world-store stays a convention (one
   consumer: mining); the card engine generalizes (5+ consumers, §3 D-1).
6. **Seam-first is what "plug-and-play ready" means.** The owner's "ready for any possible future
   function" is bought by the **seam discipline**, not by speculative engine-building: because
   single-consumer logic already sits behind (declaration in → result out), generalization at
   second-consumer time is a refactor of the *inside* — callers don't move. This reconciles
   "ready for anything" with "don't over-abstract" without compromise.
7. **The schema-growth guardrail (anti-inner-platform).** The failure mode of declarative engines
   is the declaration schema itself becoming a programming language. Rule: when a declaration
   needs conditional logic beyond what the schema expresses, that is the signal to use a Tier-3
   handler — **not** to grow the schema with if/else constructs. The schema grows a field only
   when the same pattern recurs across ≥2 consumers (the second-consumer rule applied to the
   grammar itself). Companion enforcement idea (schema-growth ledger):
   [`../ideas/rebuild-schema-growth-ledger-2026-07-03.md`](../ideas/rebuild-schema-growth-ledger-2026-07-03.md).

*Why this is safe to bind:* it is the same bet the design spec already makes (manifest grammar,
escape hatches, simulability) — S-1 states it as the standard every Phase-B plan must apply to
**every foundational function**, with the guardrails named.

### S-2 — Foundation-before-consumer ordering (generalizes the card-engine finding) — Q-0220

The owner's ruling on the welcome/card-engine inversion: *"the foundation is correct first —
standard practice for every function."* As a build-order rule, with the distinction the order
audit (§3) forced:

- **Engine-class dependency** (a one-to-many foundation engine that a capability consumes):
  the engine **always ports before its first consumer**. No capability ships before an engine it
  needs. *(This is the welcome ← card-engine case.)*
- **Peer-class dependency** (one feature consuming another feature's *content* — gear from
  mining, spawn tables from fishing): may be satisfied by a **declared-seam deferral** — the
  consumer's manifest declares the integration seam from day one (file-completeness philosophy),
  ships with it dormant, and the wiring activates when the peer lands. The deferral is labeled
  with its activation point. *(This preserves deliberate sequencing like mining-last.)*
- Every Phase-B layer plan must include an explicit **internal-order dependency check** against
  this rule (the §3 audit found the frozen plan itself violated it twice — the check is not
  optional ceremony).

---

## 3. The dependency-order audit (Stage 1's structural pass over §1.1/§2)

Walked **every dependency cell** of the BUILD-PLAN §1.1 table against the §2 within-layer
orderings. Result: the layer skeleton (L0→L5) is sound — economy before games, AI after the
deterministic platform, dashboard last, mining as the L3 acceptance test all verify. **Three
ordering inversions found**, dispositioned under S-2:

| # | Inversion | Class | Disposition |
|---|---|---|---|
| 1 | **welcome (L1b) ← visual card engine (L1c)** — a named card consumer scheduled a band *before* the engine ("ProBot card depth via the L1c card engine") | engine-class | **Reorder (D-1):** welcome moves out of the L1b spine to **L1c, immediately after the card engine**, serving as the engine's first-consumer acceptance test (mirrors the mining-last pattern: engine proven by a real consumer immediately). |
| 2 | **welcome (L1b, position 8) ← role (L1b, position 11)** — welcome's row lists `role` as a dependency (R-1 role-grant workflow), but role ports three slots later in the same band | engine-class (in-band) | **Fixed by the same reorder:** welcome now ports after the entire L1b spine, so role (and logging) are long-built. |
| 3 | **deathmatch (L3, 3rd) ← mining (L3, last)** — deathmatch's row lists `mining (gear)`; **explore hub** likewise lists mining among its deps and ports before it | peer-class | **Declared-seam deferral:** deathmatch and explore declare their mining-integration seams (gear modifiers, mining-world encounter hooks) in their manifests from day one, dormant, activation labeled "when mining lands." **Mining-last stands** — its role as the whole-stack acceptance test outweighs two dormant seams. |

No other inversions: all remaining §1.1 dependency cells point at same-or-earlier positions
(verified row-by-row this session). The `image_moderation → L4 AI adapter` cell is *not* an
inversion — the plan already annotates it "L4 stub ok" (egress adapter), which is precisely an
S-2 peer-class deferral avant la lettre.

**Also flagged (vocabulary, not order):** the BUILD-PLAN speaks L0–L5 while the design spec §9
speaks Phase-3/K0–K10. One canonical spine (the L-layers) with a K↔L crosswalk table is a Gate-0
edit (D-6) — the dual numbering is a standing confusion cost for the owner reviewing in plain
language.

---

## 4. Plan deltas for Gate-0 (D-1…D-6)

These are the Stage-1 amendments the Gate-0 spec pass folds (alongside G-9…G-24). None re-opens
the capstone's dispositions; each refines order, adds a capability, or replaces a thin section
with a decided model.

### D-1 — Card engine: promoted to a general presentation engine; welcome becomes its acceptance test — Q-0220

- The **visual card engine** is a first-class S-1 engine: one renderer, per-card
  **CardTemplateSpec declarations** (layout, fields, theme, image source), Tier-3 handler seam
  for irreducible custom elements. Consumers: welcome cards, rank cards, leaderboard cards,
  profile cards, future story/scene cards — 5+, decisively past the second-consumer bar.
- **Placement:** stays at L1c (before every card consumer — L2 profile/leaderboard, etc.), with
  **welcome re-homed to L1c right after it** (§3 #1–2). The L1b operator spine is *not* delayed
  behind presentation work.
- **The image-source seam is declared from day one** (file-completeness philosophy): a card's
  `image` source may be a static asset, an attachment, **or a generated image (D-2)**. The engine
  ships at L1c consuming static/asset sources; the generated-image source activates when the D-2
  provider lands at L4 — a labeled S-2 peer-class deferral inside the engine's own spec.

### D-2 — NEW capability: media generation (prompt → image) — Q-0221

A genuinely **forgotten capability** surfaced by Stage 1 (nowhere in the 43-subsystem corpus):
AI image generation from prompts, for card imagery and story visuals (the owner's example: scene
art for a D&D-style story game).

- **Shape:** a `MediaGenerationSpec` capability in the **L4 AI band** — provider call is an
  egress escape hatch behind a **provider-agnostic adapter** (swap-able API), consumed through
  the card engine's image-source seam (D-1).
- **Cost/abuse posture is mandatory at declaration time** (the free-for-everyone mission makes
  the owner the payer): per-guild quota + global budget cap + cache-by-prompt-hash + owner kill
  switch, and **default-OFF per guild** (the image_moderation off-by-default precedent).
  Content-safety filtering on prompts before egress; no user PII in prompts.
- **Feasibility grounded:** `OPENAI_API_KEY` is verified present in agent containers (Q-0213
  credential set), so a provider exists without new owner setup.
- **The D&D-style story game itself is NOT scheduled** — it enters the §1.3 known-options menu as
  a named future consumer the card engine + media-gen must not preclude. Scheduling it is a
  future owner decision, not a Stage-1 side effect.

### D-3 — The cutover model: 3-phase, container-first (replaces the plan's thin cutover story) — Q-0222

The BUILD-PLAN's weakest area (cutover was scattered across "post-parity bands" + ops rows).
Owner-decided model, verified feasible this session (test-bot token **Galaxy Bot** + `DATABASE_URL`
live in agent containers, per Q-0213 — note the env var is misleadingly named
`DISCORD_BOT_TOKEN_PRODUCTION`):

- **Phase CUT-1 — container-only live testing.** The new bot runs **only in the agent's cloud
  container** on the test-bot token, in the owner's test server — never auto-deployed, never on
  the real token. Every session live-tests what it built **with the owner present,
  command-by-command**; a command passes only when it beats the old bot's version. Structural
  rails, in the kernel from day one: a **guild allowlist** (refuse to operate outside declared
  test guilds until cutover), the **single-instance lock** (no duplicate gateway connections from
  parallel sessions), and a **per-command `verified_live` sign-off registry generated from the
  manifest** — the live-test checklist is an artifact, not vibes, and it gives "better than the
  old bot" a per-command ledger. In the new repo the token env var gets an honest name.
- **Phase CUT-2 — manifest-driven selective import.** The importer walks the **manifest
  snapshot** and copies **only data the new bot's manifests declare a need for**: every StoreSpec
  carries an `import` mapping (old table/column → new store + transform, or `fresh-start` +
  reason). Outdated/unused writes are left behind **by construction**, not by hand-filtering.
  Plus the 100%-means-100% completeness check: the importer **enumerates every old-DB table and
  emits a full-coverage disposition report** (imported / deliberately-dropped + reason) — "not
  copied" is always a decision, never an oversight. *Template consequence:* every Phase-B
  component plan gains a mandatory **Import-mapping section** (its stores' old→new mappings or
  fresh-start rationale), so the importer is buildable incrementally and the coverage report is
  enumerable. This is the concrete design of the spec §5.2 "fresh chain + one-time importer"
  decision — it amends §5.4's plan shape.
- **Phase CUT-3 — token swap + retirement.** Ordering: telemetry/golden capture (Phase-0.5)
  happens **before** any old-bot freeze → short freeze window → final CUT-2 import → swap to the
  real SuperBot token → old bot retired. **Rollback window:** the old bot stays runnable
  (not deleted) until N days of stable operation; N set at Stage 3.

### D-4 — Substrate-kit completion is a named pre-bootstrap gate — Q-0223

The strategy doc's "kit first" premise, made a scheduled gate with its real remaining tail
(the BUILD-PLAN had waved the kit off as out-of-scope substrate; the owner directs it **fully
completed before the new repo bootstraps**):

1. **Re-entrant `JsonStateBackend.transaction` → atomic `apply_review_verdict`** — the one real
   correctness bug (3 un-batched flushes on the fail path; crash mid-way leaves inconsistent
   state). Own PR + full suite, per
   [`../ideas/substrate-kit-review-followups-2026-07-02.md`](../ideas/substrate-kit-review-followups-2026-07-02.md).
2. **Standalone CI** — prove the kit extraction-clean on its own (today it rides the repo suite
   via a `sys.path` shim).
3. **Extraction + rename** — the `engine`/`substrate-kit` placeholder names; published name is
   owner-chosen at extraction (existing owner decision).

Runs **parallel to Stages 2–3** (it's code in *this* repo); the gate binds only the new-repo
bootstrap. State correction recorded in §5.

### D-5 — Per-subsystem triage: return is not automatic — Q-0223

The BUILD-PLAN schedules all 43 subsystems back. Owner ruling: **some may not return, or not
yet** — outdated, misplaced, or simply not worth planning to completion now. Stage 2 therefore
assigns every §1.1 row a verdict: **`bring back` / `defer until planned to completion` / `drop` /
`re-place` (different hub/shape)** — recorded per row, with one-line reasons, in the Stage-2/3
surface record. A `defer`/`drop` verdict removes its row from the Phase-B plan queue (and its
dependents get re-checked under S-2).

### D-6 — One canonical build vocabulary

Gate-0 adds a **K↔L crosswalk table** to the design spec and declares the **L-layers canonical**
for sequencing talk; K-numbers remain the kernel's internal component names. (Papercut, but a
recurring comprehension tax on the owner — cheap to kill at Gate 0.)

---

## 5. State corrections captured (so no later reader plans on stale figures)

1. **The substrate-kit "~45–55% complete" figure
   ([`fresh-rebuild-strategy-2026-07-02.md`](fresh-rebuild-strategy-2026-07-02.md) §1.2) is
   stale.** It predates #1649 landing. Verified this session (2026-07-03): the `loop/` nervous
   system (episodes, triggers, reflections, maintenance, review-seam, kpis), all five hooks, and
   **real mode behavioral branching** (`lib/modes.py` — policy, quotas, actuator gating) are
   shipped; **422 kit tests, all green** (run this session); `pyproject.toml` packaging present.
   Honest state: **~90–95% with the named D-4 tail.** The owner had been led to believe
   "complete"; neither figure was right — D-4 is the truth.
2. **The container can boot the new bot today.** Test-bot token (Galaxy Bot) + `DATABASE_URL`
   verified present in this session's container. CUT-1 has zero setup prerequisite.
3. *(Carried, already in the capstone's §4.4 list, not re-litigated here):* the design spec's
   "amendments folded" header, phantom handoff §F, stale handoff §C, strategy Phase-0 stamp,
   numeric drift — all still Gate-0's sweep.

---

## 6. Remaining Phase-A agenda (what Stages 2–3 still owe)

Unchanged from the phase doc's seed agenda, minus what Stage 1 closed, plus what it added:

- **The subsystem walk (Stage 2, the big one):** per-subsystem exact command surface — keep /
  merge / drop / rename with final names + aliases (271 commands); slash-vs-prefix kind per
  surface; **naming conventions** (the K1 registry's input scheme); hub topology; concrete
  outperform feature lists; **the D-5 triage verdict per row**.
- **Cross-cutting method/seam vocabulary** (audited-mutation signatures, `WorkflowResult` shape,
  handler-ref + provider-ref naming) — now to be written **as S-1 applications** (which tier each
  recurring pattern uses).
- **The uncertainty-ledger rows assigned to Phase A, still open:** `ModerationActionSpec`
  (envelope vs tier-3 — needs its own discussion + the ~1hr spot-check) and **G-22 staging
  lanes** (standardize vs bless three). Neither was decided in Stage 1; they must not silently
  slip past Stage 3.
- **Stage-3 consolidation:** fold the walk into the final surface record; set CUT-3's rollback
  window N; feed Gate-0 (G-9…G-24 + D-1…D-6 + the §4.4 freshness sweep); owner ratification.

---

## 7. Pointers

- Process + gates: [`rebuild-planning-phase-2026-07-03.md`](rebuild-planning-phase-2026-07-03.md)
  (Phase A → B → C; this log is Phase-A output #1)
- Frozen reference:
  [`NEW-BOT-BUILD-PLAN.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/NEW-BOT-BUILD-PLAN.md)
  · [`FINAL-REVIEW.md`](../analysis/rebuild-discovery/new-bot-capability-audit/findings/FINAL-REVIEW.md)
- The grammar the standards bind to:
  [`rebuild-design-spec-2026-07-02.md`](rebuild-design-spec-2026-07-02.md) §2 (incl. §2.9 escape
  hatches, §2.10 simulability)
- Owner rulings this log records: **Q-0219 (S-1) · Q-0220 (S-2/D-1) · Q-0221 (D-2) ·
  Q-0222 (D-3) · Q-0223 (D-4/D-5)** in
  [`../owner/maintainer-question-router.md`](../owner/maintainer-question-router.md)
- Session log: `.sessions/2026-07-03-rebuild-stage1-global-review.md` (PR #1679)
