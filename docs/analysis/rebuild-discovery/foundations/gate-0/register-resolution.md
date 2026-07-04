# Gate-0 register resolution — the 19 RATIFY-DEFAULT rows, frozen

> **Status:** `reference` — Gate-0 grammar-freeze artifact; the 19 ratified rows are frozen (2026-07-04). **NOT SOURCE OF TRUTH.**
> Freezes the **19 RATIFY-DEFAULT** rows of the 31-row consolidated question register to their
> **built defaults**. The 14 foundational-design specs win over this table for any shape they own
> (Q-0120); this doc records the *disposition*, not the mechanism. Companion:
> [`owner-decision-packet.md`](owner-decision-packet.md) (the 12 OWNER-ONLY rows + L-21).
>
> **Sources verified against:** `design/question-register.md` (the 31 rows), Part 2 of
> `planning/rebuild-gate0-worklist-2026-07-04.md` (the disposition), and
> `design/seam-consistency-matrix.md` (the F-fork PIN numbering — authoritative for F-labels).

---

## What "RATIFY-DEFAULT" means

Each of these 19 rows has a **safe / conservative built default** that the grammar freeze pins
*mechanically* — no owner ruling needed — because freezing it forecloses no later owner option
(the mechanism is fully built either way; only a default, a wording leg, or a seam reconciliation
is being pinned). Five are **owner-visible**: ratifiable *and* surfaced at the sitting for owner
awareness (a scope confirm, a copy string, an ops caveat, a retention posture, a test audience).
That awareness input does **not** block the freeze.

**F-label correction (Q-0120).** The register's `Owning spec` column mislabels the cross-spec
forks for Q-D2/Q-D3/Q-D4 (it reads F-3/F-5/F-2). The **seam-consistency-matrix PIN numbering is
canonical** and is used below: **F-1** = poll topology (Q-D1) · **F-2** = K7 draft entry (Q-D2) ·
**F-4** = `ActorRef.actor_type` (Q-D3) · **F-5** = background `Surface` (Q-D4) · **F-3** = intent
posture (the one OPEN fork → Q-D5, owner-only). The worklist Part 1/Part 3 already use the correct
labels; only the register + worklist Part 2 disposition tables carry the scramble.

---

## The ratification table (19)

| Q-D | Decision (one line) | Frozen default — **RATIFIED** | Owning spec · maps-to | Owner-visible note |
|---|---|---|---|---|
| **Q-D1** | Who hosts the outbox relay? | **09 hosts** `OutboxRelayLane`+`OutboxReaperLane` on its single `PollSupervisor` @5 s; the standalone `RELAY_TASK`/1 s/"not-my-lane" language is withdrawn, roster non-exhaustive | 08↔09 · **F-1/RC-20** (applied) · ⊕ net-new | — |
| **Q-D2** | Atomic-apply semantics + which K7 entry the draft calls + keep the word "atomic"? | Reconcile to **06's per-op `run(spec,ctx)` + EFFECT legs**; `run_ref`/`apply(op,conn)` restricted to pure-DB external-conn draft ops (`atomic_db_only`-fenced, no draft `op_kind` in scope); **DROP "atomic"** for the non-rollback-able resource lane | 06↔07 · **F-2** (applied) · T2-1/A#1 | — |
| **Q-D3** | Add `ActorRef.actor_type`? | Add **`actor_type: str = "user"`** (`{user, system, backfill, setup_delegate}`) to 02's `ActorRef` + vocab §⑩; K7 maps it into `AuthorityRequest.actor_type`; repair reuses `backfill` | 02·09·11·vocab §⑩ · **F-4/RC-18** (applied) | — |
| **Q-D4** | Which `Surface` member classifies a background fire's `from_exception`? | ONE **`Surface.MAINTENANCE = "maintenance"`** member (scheduler fires AND sweep-repairs both classify under it); `from_exception.target → TargetRef \| None` for headless fires | 02·09·11 · **F-5/RC-19** (applied) | — |
| **Q-D6** | Panel-action grammar (SF-a): per-spec fields vs minimal spec + derived path | **(A) per-spec fields** — panel actions/selectors carry their own `authority_ref`/`enabled_when`/`reply_visibility`/`cooldown`/`defer_mode` (route-through-C-1); retires **L-5** structurally; 01 arms `never_strand`/`action_cooldown_parity` | 02 §8-a · 01 P6 · L-5 | **owner-visible** — grammar-shape confirm only; the resolver contract is unchanged either way. Surface for awareness, non-blocking. |
| **Q-D7** | Owner-override scope + transparency-sink wording (SF-b) | scope **(A) member-guild** (built *structurally* — `owner_override_holds` requires `is_member`, X-7); sink **(ii)** dual bot-log + server-log + owner-DM digest fallback, **no durable row** | 02 §8-b · 04 §8-a · T2-10/L-12 | **owner-visible** — owner confirms scope + names the notice copy string; a cosmetic fill-in. Surface for awareness, non-blocking. |
| **Q-D9** | Which events are `delivery=AT_LEAST_ONCE`? | **v1 set** = `audit.action_recorded`, `xp.awarded`, `xp.level_up`, `economy.balance_changed`; every other event stays `BEST_EFFORT` (zero behavior change for the 30+ observability events; the set is extensible any time) | 08 §13 · 07 §9-#7 · T2-3/L-9 | — |
| **Q-D10** | `StoreSpec.version_policy` default for a `bears_value` store on schema drift with no `upcast_ref` | **`REJECT_AND_PRESERVE`** (refund-before-delete, never forfeit); the compile fence forbids `DROP` on a value store, so the floor is safe regardless | 09 §8.1 · T2-7/A#8 | — |
| **Q-D11** | Invariant enforcement: permanent runtime sweep vs one-time migration script | **(C) permanent `PollLane`, report-only by default**; cutover verify-import hard-checks the same invariants; individual invariants flip to auto-repair as each proves out | 11 §4 Q1 · FJ §4 #7 | — |
| **Q-D12** | verify-import (CUT-2) + verified-restore (CUT-3) as HARD gates or advisory? | **(C) HARD on `bears_value` `RECONCILIATION`+`TERMINAL_ONCE`, advisory on the rest, owner-signed quarantine override**; backup-restorability leg = **HARD** | 11 §4 Q2 · 13 §4 Q2 · L-18/FJ §4 #7 | — |
| **Q-D22** | Un-preserved-override disposition (PG-4) | **(a) admin-notice + exact re-apply overlay** — never silently reset a guild's security config; lands in the CUT-3 comms plan | 14 §4 PG-4 · L-23 | — |
| **Q-D23** | Deployment identity (PG-5): reuse the Discord application id, or a new application? | **(a) reuse the same app id** — un-renamed commands keep their ids ⇒ their overrides survive; only the enumerable rename/drop set needs a notice | 14 §4 PG-5 · ⊕ net-new | **owner-visible** — ops caveat: deviate to (b) new application only if an ops constraint forces it. Surface the caveat, non-blocking. |
| **Q-D25** | Dispatch-trace / audit-retention promotion (SF-c) | **(A) observability-only / DB-spine-only for v1** — adds **no** new retained rows; the per-mutation audit already covers auditable writes | 02 §8-c · 04 §8-c · 06 §9 · 07 §9-#6 | **owner-visible** — a retention/volume posture, not a correctness need; promotable any later time. Surface for awareness, non-blocking. |
| **Q-D26** | `ChannelEmitter` send-egress port (T-7) | **(a) new `ChannelEmitter` port** + `OutboundContent`/`TrustLevel`, default-deny (`UNTRUSTED ⇒ AllowedMentions.none()`), AST-fenced (raw `channel.send` outside `adapters/discord/responders.py` = `SEMANTIC_VIOLATION`) | 10 §8.1 T-7 → 02/K8 · L-24 · **RC-21** | — |
| **Q-D27** | CUT-2 permission census as a *binding* cutover gate (PG-3)? | **Binding** — no swap until the census is captured, the PRESERVED set carry-verified, and RENAMED/DROPPED enumerated into the admin-notice; a bounded per-guild bot-token read | 14 §4 PG-3 · L-23 | — |
| **Q-D28** | Test-mode effect routing (06) | **(a) fail-safe suppress** default — never touch a real guild; concrete test-guild routing is owned by the release-testing band behind the `AcceptHook` seam | 06 §9 · L-10/L-11 | **owner-visible** — owner names the eventual test audience later; doesn't block v1. Surface for awareness, non-blocking. |
| **Q-D29** | Durable cooldown store (SF-e) | **(a) in-memory for v1** — matches shipped behavior (resets on restart); if promoted it is a strand-2 durability `StoreSpec` the resolver reads off `CooldownSpec` | 02 §9 · T2-6/L-8 | — |
| **Q-D30** | Rung-4 NL-orchestration failure policy (SF-f) | **(a) stop-on-first-non-SUCCESS** default — the sequential seam + shared `orchestration_id` are designed now; a per-plan continue/compensate policy is Phase-4 band 6 | 02 §9 · 07 §9-#1 · ⊕ net-new | — |
| **Q-D31** | Batch-ratify the design-decided seam refinements | **Adopt all as recommended** — rubric mechanization tags, `CredentialSpec` leaf, repair `actor_type=backfill`, de-repo-bind mechanics, integrity-floor fix, `>=`-ceilings/`RevocationRef` freeze (each contained + reversible) | 10·11·12·13 (mixed) | — |

---

## Disposition reconciliation notes (Q-0120 — where the worklist disagreed with the register)

The register uses a **binary 🔒** flag (23 rows 🔒). The worklist Part 2 disposition makes a
**finer cut** than 🔒: several 🔒 rows carry a *safe ratifiable default*, so they are RATIFY-DEFAULT
(freeze the default, surface for awareness) rather than hold-for-ruling. **The worklist's finer
disposition wins** for the freeze; the register 🔒 survives as the "surface at the sitting" signal.

- **Q-D2** — register flags a partial 🔒 on the *"atomic" wording leg*; worklist ratifies it. **Ratify
  wins** — dropping "atomic" for the non-rollback-able resource lane is a naming-accuracy fix, not an
  owner ruling; the seam itself is a design co-decision (F-2, applied).
- **Q-D6, Q-D7** — register 🔒; worklist RATIFY-DEFAULT (owner-visible). **Ratify wins** — the resolver
  contract / narrow scope is enforced in code regardless; the owner only confirms scope + names copy.
- **Q-D23** — register 🔒 (ops-caveat); **ratify wins** — the recommendation is the clearly-safer default.
- **Q-D25, Q-D28** — register 🔒 (Tier-3); worklist reclassifies both 🔒-but-safe-default Tier-3 rows to
  RATIFY-DEFAULT. **Ratify wins** — each has a safe v1 default (no new retained rows / suppress).
- **F-labels (Q-D2/3/4/5)** — the register's `Owning spec` F-labels are scrambled; the
  **seam-consistency-matrix PIN numbering wins** (corrected inline above).
