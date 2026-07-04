# SuperBot rebuild — foundational design (Phase-B) · the owner's entry point

> **Status:** `synthesis` — **complete** (2026-07-04). **NOT SOURCE OF TRUTH for runtime.** This is
> the front-matter for the foundational-design deliverable: a scannable map over the 14 buildable
> specs + the four synthesis artifacts that bind them. Source & merged PRs win (Q-0120); each owning
> spec wins for a shape it owns; the frozen [`shared-vocabulary.md`](shared-vocabulary.md) wins where
> it reconciled a two-spec disagreement. **This is the first thing the owner reads** before Gate-0.

---

## 1 · What this is — the AUDITED → Gate-0 / L0-plannable bridge

Stage-1 review **audited** the rebuild into a verdict: the final judgment
([`../final-judgment-fable5-2026-07-03.md`](../final-judgment-fable5-2026-07-03.md)) is a **GO — with
amendments**, resting on ~470 reconciled findings, a 25-row **L-ledger** (L-1 … L-25), 17 surviving
**§4 gaps**, and a three-tier owner-decision queue. That output was *prose* — a proven list of what is
broken and what must not evaporate, but nothing a builder could pick up and implement, and nothing a
grammar freeze could ratify. **This deliverable is the bridge.** It converts every audited finding
that this foundational layer owns into **14 buildable specs** (a fresh agent builds each from its file
+ the frozen contracts making *zero* further design decisions), freezes the recurring seams **once**
into a shared vocabulary, **proves** the 14 specs write to that same vocabulary, **harvests** every
decision they leave open into one owner-consumable register, and **audits** that no L-row or gap was
dropped on the way. The result is a design that is now both **Gate-0-ratifiable** (the grammar-field
additions the specs pin are enumerable and blessable in one sitting) and **L0-plannable** (the
foundational — layer-0 — kernel + durability + cross-cutting layer now has a concrete build order).

---

## 2 · The three strands + the 14 specs

Fourteen specs, grouped into three build strands. Kernel spine is the foundation everything imports;
runtime-durability builds on it; cross-cutting concerns ride both.

### Strand 1 · Kernel spine (the C-1 chokepoint + the ops rails)
| # | Spec | Designs |
|---|---|---|
| 01 | [Manifest compiler + committed snapshot + amendment registry](strand-1-kernel-spine/01-compiler-snapshot-amendments.md) | The linchpin K1 compiler: snapshot⇄runtime⇄remote parity, the six compile fences (P3/P4/P6…), the derived namespace projection. |
| 02 | [The C-1 resolver + the dispatch error/failure envelope](strand-1-kernel-spine/02-resolver-error-envelope.md) | The single `resolve()` seam all six surfaces funnel through + `from_exception`/`ErrorEnvelope` + reply-visibility + the drain gate. |
| 03 | [The K1 namespace registry](strand-1-kernel-spine/03-k1-namespace-registry.md) | Shared-verb/cap/deep-link namespace over the live corpus; slash-cap budget; custom-trigger set-time gate. |
| 04 | [The authority engine (`authority_ref` + owner override)](strand-1-kernel-spine/04-authority-engine.md) | One `authority_ref` → `Lane{CAPABILITY,TIER}`; the 10-field `AuthorityDecision`; owner-override-once; channel-access; transparency sink. |
| 05 | [The ops kernel — config · DB seam · migrations · metrics · readiness · data-plane rail](strand-1-kernel-spine/05-ops-kernel-rails.md) | `ConfigSpec`/`SecretSpec`/`IntentSpec`; the `IdempotencyKey`/`once()` primitive; `/ready`; the 4th rail `assert_data_plane()`. |

### Strand 2 · Runtime durability (restart-safe state)
| # | Spec | Designs |
|---|---|---|
| 06 | [The C-2 draft / preview / confirm / apply pipeline](strand-2-runtime-durability/06-draft-pipeline.md) | Producer-agnostic `sb_drafts`; N-ops-as-N-rows; Accept = AND-over-refs; per-op idempotent-resume apply. |
| 07 | [The workflow / compound-op engine (K7)](strand-2-runtime-durability/07-workflow-engine.md) | `LegSpec`/`CompoundOpSpec`; `run()`/`run_ref()`/`apply()`/`preview()`; the central `audit_log` row; the idempotency-posture fence. |
| 08 | [The event outbox / durable delivery (K4)](strand-2-runtime-durability/08-event-outbox.md) | `DeliveryClass{AT_LEAST_ONCE,BEST_EFFORT}`; in-txn `event_outbox` + post-commit relay; the durable audit twin. |
| 09 | [The durable scheduler / due-queue + versioned-state policy](strand-2-runtime-durability/09-scheduler-state.md) | `sb_due_queue` + `ManagedTaskSpec` durability/misfire/catch-up; boot-reconcile; the `PollSupervisor`; `VersionPolicy`. |

### Strand 3 · Cross-cutting concerns (posture across every subsystem)
| # | Spec | Designs |
|---|---|---|
| 10 | [Security / abuse posture + rubric classes 11 / 12 / 13](strand-3-cross-cutting-concerns/10-security-abuse-rubric.md) | The three adversarial review classes; `cost_posture` grammar; member-erasure executor; the `ChannelEmitter` send-egress port. |
| 11 | [Production-data integrity / repair](strand-3-cross-cutting-concerns/11-data-integrity-repair.md) | Declared invariants + always-on report-only sweep lane; CUT-2 verify-import; `QUARANTINE_ONLY` money-repair default. |
| 12 | [Credential lifecycle + dependency supply-chain posture](strand-3-cross-cutting-concerns/12-credential-lifecycle.md) | `CredentialSpec` + tiered rotation cadence + revocation carve-out + blast-ordered compromise runbook; lockfile + `pip-audit` gate. |
| 13 | [Backup / DR surviving cutover + rollback-data disposition](strand-3-cross-cutting-concerns/13-backup-dr-rollback.md) | Backup port + de-repo-bind; verified-restore gate; the derived `rollback_class` disposition + reverse-import valve. |
| 14 | [Discord platform-governance](strand-3-cross-cutting-concerns/14-platform-governance.md) | Slash-first survivability + intent-denial fallback ladder; verification milestone; CUT-2 permission census + admin-notice. |

---

## 3 · What got designed — buildable specs + a frozen vocabulary

**14 buildable specs.** Each is drawn to build-from-this depth against the frozen upstream contracts,
carries its own §10/§5 retirement map (which L-rows / gaps it retires), and surfaces its own residual
owner calls. Together they retire the **structural** half of the L-ledger — the C-1 cluster (L-4),
the panel second-resolver (L-5), the deploy-overlap double-fire (L-6), the two-producers pipe (L-7),
restart-safety (L-8), the missing outbox (L-9), the CUT-1 data plane (L-10), owner-override gaps
(L-12), the authority two-lanes (L-13), backup/DR (L-18), the security-review-class hole (L-19),
credential lifecycle (§4 #10), supply-chain (§4 #12), and production-data integrity (§4 #7).

**One frozen shared vocabulary.** [`shared-vocabulary.md`](shared-vocabulary.md) freezes the exact
shape of every recurring seam the kernel hands downstream — the error envelope, `authority_ref → lane`,
audit-row + `mutation_id`, the idempotency-key contract, the restart-safety pattern,
`EventSpec.delivery`, and the config/secret + data-plane rail — so no downstream port re-derives them
(the exact drift class the rebuild exists to kill). The **seam-consistency matrix**
([`seam-consistency-matrix.md`](seam-consistency-matrix.md)) then **proves** the specs agree:
**56 of 61 touched cells AGREE**, all 15 prior reconciliations (RC-1 … RC-15) hold, and every seam is
verified against shipped source. Five genuine open forks remain (F-1 … F-5) — none blocks strand-2/3
from *building* to the frozen shapes; each is a register entry an owner or a vocab re-freeze closes.
The one concentrated edit the matrix surfaces: **spec 02** is written to its pre-hardening shapes and
must absorb 04's frozen authority contracts before K8 wires up.

---

## 4 · What stayed open — the question register

Every open decision the 14 specs + the seam matrix + the adversarial sweep surfaced is rolled into one
owner-consumable landing site: [`question-register.md`](question-register.md).

**31 decisions · 23 owner-gated 🔒.** Each carries a **built default** so the build is unblocked
today; the owner ratifies or overrides. Reading order: **Tier-1 first** (five cross-spec seams that
gate the strand-2 build + the vocab re-freeze), then the **Tier-2 Gate-0 contract batch** (19 rows),
then the **Tier-3 batch-bless** (defaults + bounded deferrals).

The genuinely **owner-only** rows — irreversible, or narrowing a binding owner decision, so no built
default can substitute for a ruling:

| Register row | The call | Why owner-only |
|---|---|---|
| **Q-D15** rollback-data disposition (+ window N) | Which post-cutover writes survive an N-day rollback; reverse-import valve vs declared-loss | **Near-irreversible** data-loss policy with a real reverse-importer build cost. |
| **Q-D13** money-repair direction | For a value-bearing invariant violation, which store is ground truth (mint ledger vs claw aggregate) | **Near-irreversible** money call; ships `QUARANTINE_ONLY` until signed. |
| **Q-D16 / Q-D17 / Q-D19** credential custody & recovery | Whether to arm a recovery cadence; narrow the Q-0213 `*Delete` brake for a token revoke; the `SB_PROD_ATTEST` custody source | Each narrows the **binding Q-0213** credential-concentration decision → router DISCUSS. |
| **Q-D20** security-rubric adoption | Adopt rubric classes 11/12/13 + run one adversarial-abuse pass; who runs it | Rubric edits are owner-directed (Q-0233 froze the ten). |
| **L-21** old-bot change-policy | An interim policy so old-bot feature work doesn't drift from the frozen corpus/goldens during the build | **Carried** on the softest binding (§4 gap #5) — no CI guard owns it yet. |

Also owner-gated and worth a sitting: **Q-D5** intent-denial posture (fail-closed vs DEGRADE),
**Q-D14** RPO target + backup source tier, **Q-D8** store-drop disposition default, **Q-D21** the
growth posture. Full table + recommendations in the register.

---

## 5 · The design → retirement map — nothing evaporates

The final judgment's binding verdict **V-3** demands the ~470 findings bind to a plan so none
evaporate. [`retirement-coverage-map.md`](retirement-coverage-map.md) is the closure audit — it walks
**every** row the owner is owed and records which spec retires it, or where it is explicitly carried,
or why it is out-of-scope.

| Metric | Value |
|---|---|
| **Total rows audited** | **96** (25 L-rows + 17 §4 gaps + 7 Tier-1 + 22 Tier-2 + 17 Tier-3 + 8 stress/critic) |
| **Covered** — a spec retires it | **62** |
| **Carried** — to a named gate / register / Stage-3 line / resolved owner Q | **32** |
| **Out-of-scope** — a V-1 PR or Stage-2 subsystem work | **2** |
| **⚑ EVAPORATIONS (V-3 violations)** | **0** |

**V-3 holds — no finding evaporated.** Every one of the 96 rows has a home. The one thing to keep in
view: **nine rows are only *weakly* carried** — their sole home is a Stage-3 consolidation line or
"standing owner awareness," the two softest bindings in the set (the residual V-3 watch-list). The
softest of all are **§4 #14** (field-signal intake) and **§4 #17** (model-availability contingency),
which have no stage/gate/register at all — only judgment-ledger prose. Not a violation today, but the
recommended fix is a one-line home-upgrade before Stage 2 closes.

---

## 6 · How to consume this next

This foundational design **feeds two gates** and **hands off a third**:

**→ Gate-0 (the grammar freeze).** The specs *pin* the grammar-field additions Gate-0 ratifies in one
sitting: the C-1 single-seam contract incl. the panel pipeline + cooldown field (L-4/L-5), the error
envelope (T2-4), the single `authority_ref` (T1-4), rubric classes 11–13 (L-19), the frozen-path CI
guard (L-21), the additive `ActorRef.actor_type` / background `Surface` members (F-5/F-2), the
`ChannelEmitter` egress port (Q-D26), and the L-24 presentation riders (alt-text, locale seam,
`allowed_mentions` policy, `ModalSpec`, bundled fonts) as declared fields. All of Tier-3 batch-blesses
here. This README + the four artifacts are the sitting's inputs.

**→ The Phase-B L0 build (order across the specs).** L0 is the foundational layer everything imports;
the strands *are* the build order:
1. **Strand 1 first** — 01 (the linchpin compiler) then 02/03/04/05. 05's `IdempotencyKey`/`once()` +
   `db.transaction()` primitive and 04's authority contracts are the substrate strand-2 depends on.
   Land the **spec-02 absorption edit** (RC-2/3/4/5/12/13/14/15 + `actor_type`) here.
2. **Strand 2 next** — 07 (K7 engine) underlies both 06 (draft) and 09 (scheduler); 08 (outbox)
   provides durable delivery. **Close F-1** (who hosts the outbox relay — adopt 08's registered-lane
   model) and **F-3** (which K7 entry the draft calls — reconcile to 06's `run()` semantics) before
   wiring the composition root, plus the two residual blockers below.
3. **Strand 3 rides both** — 10–14 consume the frozen grammar; adopt the owner rulings from §4.

**Stage-2 still owns (and does NOT depend on completing this L0 build).** The 43×12 subsystem walk
proceeds against the *frozen contracts*, not the finished code. It owns: the per-family fragmentation
collapse with per-subsystem acceptance oracles (L-15); the hub / nav / preset build and the
`NavigationSpec` (L-2/L-3/L-22); the invocation subsystem's custom-trigger storage + additive union
(T2-12); per-command NL-eligibility (T2-11); the two-field description freeze (T2-16); and the C-8
per-tenant orchestration wiring. Stage-2 launches with Codex-4's row template (each row tagged with
the L-rows it retires). Downstream of Stage-2: **Gate-V** (the multi-actor golden class, L-20),
**Phase-0.5 golden capture** (the intended-divergence lane, L-11), and the **CUT-1/2/3** cutover
gates (the data-plane rail, verify-import, backup/DR, permission census).

---

## Residual polish — adversarial CLOSE-IN-SPEC items still un-applied

An adversarial sweep after the specs froze found **8 cross-spec defects deeper than the registered
forks** (F-1 … F-5). Each is a contained **CLOSE-IN-SPEC** edit — recorded here so it stays visible,
not lost, and lands with the F-1/F-3 reconciliation during the strand-2 wire-up. **All 8 remain
un-applied** in the specs as of this synthesis (verified 2026-07-04). The two blockers make a green
build *structurally impossible* until closed.

| Sev | Where | The defect (one line) | Close-in-spec |
|---|---|---|---|
| **blocker** | 07 §3.6 `atomic_db_only` ↔ 06 §3.3/§3.5 | The fence scopes "…**or a draft `op_kind` mapping**" and requires every leg be `kind==DB` → it CI-reds every EFFECT-bearing draft op, so the flagship 10-channel D&D canary (06 §11) cannot compile. Deeper than F-3: the entry-name fix alone does not remove it — the **fence scope** is what turns the disagreement CI-red. | **07:** drop "or a draft `op_kind` mapping" from `atomic_db_only`'s scope; draft ops go through `run()` (own txn; EFFECT legs allowed post-commit); fence only true external-conn callers (scheduler `run_ref` / `apply`). Land jointly with F-3. |
| **blocker** | 09 §3.5/§3.7 arm + §5 DDL | GLOBAL recurring tasks are **double-armed on every boot**: they store `guild_id = NULL`, and Postgres treats NULLs as DISTINCT, so `ON CONFLICT (task_key, guild_id) WHERE recurring` never fires — duplicate rows accrue and each fires every interval (daily digests double-post). `once()` can't dedup them (distinct `task_id` in the key). The table stores NULL while the fire key uses `guild_id or 0`. | **09:** normalize the GLOBAL slot key — `COALESCE(guild_id, 0)` in the unique index (or store `0`, or `NULLS NOT DISTINCT`); make the arm slot key and the fire dedup key use the **same** normalization. |
| gap | 07 §3.3/§4 ↔ 02 §3.1; 09 §4 / 11 §8.2 | K7 classifies leg failures "via `from_exception`", but `from_exception(exc, *, surface, target)` needs both — and `WorkflowContext` carries **neither**; a background fire has no `TargetRef` at all. Deeper than F-2 (which only names the missing `Surface` member). The error path of every K7 public entry is unbuildable as literally written. | **07 (+ vocab §①):** either make `target: TargetRef \| None` + add the background `Surface` member + thread optional `surface`/`target` onto `WorkflowContext`; **or** state K7 classifies via a surface/target-free helper and reserves `from_exception` for the resolver. Pick one and pin it. |
| gap | 13 §2.4c ↔ §2.4a/§2.4b | 13 self-contradicts on `audit_log`: §2.4c lists it as a REVERSE_IMPORTABLE/LEDGER reverse-import target ("re-insert into the OLD DB by `mutation_id`"), but `audit_log` is a **new** fresh-chain spine table with no OLD-DB predecessor — and by 13's own derivation it is NEW_ONLY ⇒ DECLARED_LOSS. Would send the importer at a nonexistent OLD table. | **13 §2.4c:** remove `audit_log` from the reverse-import set — the LEDGER reverse-import target is `economy_audit_log` (NAME_STABLE) only; the new-bot `audit_log` slice is forensic + DECLARED_LOSS per §2.4a. |
| gap | 12 §2.B | Credential rotation claims restart-safety "re-armed by boot-reconcile (§⑤.3)", but §⑤.3 is the **scheduler's** boot-reconcile (re-arms `sb_due_queue` only) and the rotation is a GitHub-Actions routine, not a due-queue task — nothing re-arms it. And the ledger has only `last_rotated_at`: an "issued-but-not-yet-verified" crash has undefined recovery. | **12:** arm rotation as a real durable `ManagedTaskSpec` (so §⑤.3 literally applies), **or** add a `rotation_state ∈ {issued, verified}` intermediate so a `once()`=False + outcome-pending re-run completes the read-back; fix the §⑤.3 cite. |
| nit | 10 T-7 vs seam matrix §8 / vocab §⑩ | The new `ChannelEmitter` egress port + AST fence (a whole new port in the frozen `kernel/interaction` module) is registered by **neither** the seam matrix's fork roster nor the vocab's tracked-corrections list — only inside 10's own T-7 — while the analogous `ActorRef.member_tier`/`actor_type` additions **are** registered. An unreconciled cross-spec module addition the completeness layer omits. | **seam matrix / vocab §⑩:** register the `ChannelEmitter` port + egress fence as a pending 02/K8 seam correction (an RC or a fork row), parallel to RC-12/F-5. *(Homed as Q-D26 in the register; just not in the reconciliation layer.)* |
| nit | 08 §12.5 vs 07 §3.3 4e+6 | 08 flags "07:192,236 **must change** to the two-call protocol / best-effort events never emit" — but 07 as written **already** implements it (§3.3 step 4e captures the in-txn `enqueue_all`; step 6 calls `emit_after_commit()`). The correction is stale; the seam matrix marks seam ⑥ AGREE without noting 08's flag is outdated. | **08 §12.5:** downgrade "07 must change" to "07 §3.3 steps 4e+6 already implement the two-call protocol — confirmed consistent," so a builder isn't sent to "fix" correct wiring. |
| nit | 06 §6 ↔ 09 ExpiryJanitorLane | The stuck-`APPLYING` → PARTIAL TTL is never specified; a legitimately slow multi-channel apply (Discord rate limits) can exceed a short TTL and be flipped to PARTIAL while `apply_draft` is still running — a last-writer race (benign for correctness, wrong terminal status). | **06/09:** make the janitor transition a conditional compare-and-set (`WHERE status='applying' AND updated_at < now-TTL`), have apply's final `update_status(APPLIED)` re-read/heartbeat, and pin a TTL above worst-case resource-create batch time. |

---

## Provenance

- **Authored by** Claude Opus 4.8 (ultracode), 2026-07-04 — a docs-only Phase-B foundational-design
  synthesis session; shipped in this session's design-synthesis PR.
- **Method** (the recurring workflow, applied once for the whole set): design each seam to buildable
  depth (the 14 specs) → **freeze** the shared vocabulary once → **prove** the specs agree
  (seam-consistency matrix, method step 5) → **harvest** every open decision into one register
  (method step 7) → **audit** retirement coverage so V-3 holds (no finding evaporates) → render this
  owner-consumable front-matter. Design contracts, not runtime source: shipped source & merged PRs
  win (Q-0120); the owning spec wins for a shape it owns; the frozen vocab wins where it reconciled a
  two-spec disagreement.
- **Upstream:** [`../final-judgment-fable5-2026-07-03.md`](../final-judgment-fable5-2026-07-03.md)
  (the Stage-1 GO verdict + L-ledger + §4 gaps + owner queue) and the four capability-audit maps in
  [`..`](..).

### The five files of this deliverable
- **[`shared-vocabulary.md`](shared-vocabulary.md)** — the frozen seam contracts (the source of truth for the recurring shapes).
- **[`seam-consistency-matrix.md`](seam-consistency-matrix.md)** — proof the 14 specs agree (56/61 AGREE · 5 open forks).
- **[`retirement-coverage-map.md`](retirement-coverage-map.md)** — the V-3 closure audit (96 rows · 0 evaporations).
- **[`question-register.md`](question-register.md)** — the 31 open decisions with built defaults (23 owner-gated).
- **The 14 specs** — [strand 1](strand-1-kernel-spine/) · [strand 2](strand-2-runtime-durability/) · [strand 3](strand-3-cross-cutting-concerns/).
</content>
</invoke>
