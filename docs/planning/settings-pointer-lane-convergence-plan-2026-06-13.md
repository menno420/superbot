# Settings pointer-lane convergence + Setup-delegate authority — plan (P0-3)

> **Status:** `plan` — the hardening **P0-3** bounded session
> ([hardening roadmap](production-readiness/hardening-roadmap-2026-06-12.md) §P0-3;
> evidence: [settings readiness map](production-readiness/settings-bindings-provisioning-production-readiness-map-2026-06-12.md)).
> The map's "Recommended next session" is a **docs + tests planning session…
> without immediately changing production behavior** — pointer *retirement* is
> risky and stays gated on binding-first reads + migration + rollback proven.
> This doc is that plan; the foundation slice (matrix + reframe + invariants)
> shipped alongside it. **Not a blanket implementation approval** — source +
> merged PRs win.

> **▶ One-line state:** the broken `governance.trusted_role` backfill is
> reframed (no longer permanently `BLOCKED_NO_SCHEMA`); two parity invariants
> now ratchet the lane; the risky scalar retirements + the delegated-apply
> authority route are sequenced below as arc PRs 2–3.

---

## 1. Verified state (ground truth, not the dated map)

Run `python3.10 scripts/settings_lane_matrix.py` for the live inventory. As of
**2026-06-13** (the map's 2026-06-12 counts were already stale — welcome/counters
v1 #775 and logging v1 #774 landed after it):

| Inventory | Live count |
|---|---:|
| Subsystem schemas | 16 |
| Declared `SettingSpec` | **65** (map said 36) |
| Declared `BindingSpec` | **17** (map said 13) |
| Provisionable resource requirements | 15 |
| Backfill `MIGRATED_KEYS` (homed, migratable today) | 2 |
| Backfill `DEFERRED_KEYS` (no binding home yet) | 2 |

**Pointer lane** (every channel/role pointer stored as a scalar `SettingSpec` —
the lane-rule debt this plan converges):

| Disposition | Count | Members |
|---|---:|---|
| `binding_backed_convergeable` (binding declared; scalar pending retirement) | 2 | `economy.economy_log_channel`, `xp.xp_announce_channel` |
| `binding_backed_deferred` (mapping exists, no schema home) | 2 | `moderation.trusted_role`, `moderation.moderator_role` |
| `orphan_no_binding` (scalar pointer, no binding at all) | 6 | `welcome.channel`, `welcome.entry_role`, `counters.{total,humans,bots}_channel`, `moderation.public_log_channel` |

**Finding the map missed (because it predates #775):** welcome/counters v1 added
**five new orphan pointers** — channel/role IDs stored as scalar settings with
`input_hint`, no `BindingSpec`. That is the exact lane-rule violation P0-3
exists to fix, freshly re-introduced. The `test_pointer_lane_ledger` ratchet
(shipped this PR) now blocks the next recurrence.

### The governance reserved-namespace finding (root cause of the broken backfill)

`config_arbitration.get_trusted_tier_role` / `get_moderator_tier_role` already
read the role pointers through `governance.{trusted,moderator}_role` bindings
(`binding_kind="role"`), and the backfill targeted `(governance, trusted_role)`.
But **`governance` is a *reserved* capability namespace**
(`utils.subsystem_registry._RESERVED_CAPABILITY_PREFIXES`), deliberately **not**
a feature subsystem — so those bindings have **no clean `SubsystemSchema`
home**. A `SubsystemSchema(subsystem="governance")` would raise a permanent
`schema_subsystem_unknown` identity-contract finding; forcing a `governance`
entry into `SUBSYSTEMS` to satisfy the backfill is the tail wagging the dog.

This is why the map offered "declare the binding **or reframe the mapping**":
the right foundation fix was **reframe**, and the binding-home decision is a real
design question → **router Q-0119** (§5).

---

## 2. What the foundation PR shipped (this slice — behavior-preserving)

1. **`scripts/settings_lane_matrix.py`** — the machine-readable lane matrix the
   map asked for (rec #1): every `SettingSpec`/`BindingSpec`/resource/backfill
   mapping/arbitration read seam + the pointer-lane disposition, `--json`.
2. **Backfill reframe** (`services/binding_backfill.py`) — split honest
   `MIGRATED_KEYS` (xp, economy — homed) from `DEFERRED_KEYS` (governance
   trusted/moderator role — un-homed). Fixes the "permanently
   `BLOCKED_NO_SCHEMA`" machinery the map flagged (Required #2). Also adds the
   `moderator_tier_role_id` mapping for symmetry (arbitration already reads it).
   **No runtime read/write changes** — arbitration falls back to legacy for an
   UNRESOLVED binding, so deferral is invisible to guilds.
3. **Two parity invariants** (Required #2 + the lane rule, the "stays-fixed"
   P1-3 layer):
   - `test_backfill_target_declaration_parity` — every `MIGRATED_KEYS` target is
     a declared `BindingSpec` (kind-matched); every `DEFERRED_KEYS` target is
     *not* yet declared (forces graduation when homed); no key in both.
   - `test_pointer_lane_ledger` — every channel/role pointer is in exactly one
     ledger bucket (convergeable / deferred / orphan); a **new** unledgered
     pointer fails (the #775 recurrence guard); a stale entry fails (rot).

---

## 3. Pointer-family migration order (map rec #4) — arc PRs 2–3

Each family retires its scalar pointer **only after** all four are proven:
binding-first read live, backfill dry-run clean, operator reconciliation path,
rollback (flip `bindings.primary` OFF). Ordered by risk (lowest first):

| # | Family | Members | Readiness | Notes |
|---|---|---|---|---|
| 1 | **XP announce** | `xp.xp_announce_channel` → `xp.announce_channel` | **Ready** — binding declared, arbitration read live, in `MIGRATED_KEYS` | Lowest blast radius; the reference retirement. |
| 2 | **Economy log** | `economy.economy_log_channel` → `economy.log_channel` | **Ready** — same shape as XP | Pairs with family 1 in arc PR 2. |
| 3 | **Governance role pointers** | `moderation.{trusted,moderator}_role` → `governance.{trusted,moderator}_role` | **Blocked on Q-0119** (no schema home) | The hardest case; touches authority tiers. Do *not* retire until the home is decided. |
| 4 | **Welcome/counters orphans** | `welcome.channel`, `welcome.entry_role`, `counters.{total,humans,bots}_channel` | **Not started** — no binding declared | Each needs a `BindingSpec` + backfill mapping minted first. Lower priority (new, low-traffic). |
| 5 | **Moderation public-log + logging fallbacks** | `moderation.public_log_channel`; `LOGGING_MOD_CHANNEL`/`LOGGING_CLEANUP_CHANNEL` fallbacks | **Not started** | `moderation.public_log_channel` has no binding; the logging fallbacks shadow 7 canonical bindings. |

**Arc PR 2 (next session):** retire families 1+2 (XP announce, economy log) —
the two *ready* convergeable pointers. Delete the editable scalar `SettingSpec`,
keep the legacy KV column readable for one release for rollback, prove the
binding-first read + backfill dry-run on real Postgres, and add the
`test_no_dual_declared_pointer` invariant (it can only be added *after* the dual
is gone — adding it now would fail on the live duals). Update the ledger:
`economy.economy_log_channel` + `xp.xp_announce_channel` move out of
`CONVERGEABLE_POINTERS` (they're no longer pointer settings).

---

## 4. Delegated-Setup apply authority contract (Q-0098 — decided, design here)

**The gap (map Required #4, High):** Final Review's `_gate_apply` →
`setup_access.can_apply_setup` authorizes the **server owner OR a delegated
admin** (a possibly-*non-administrator* member the owner added via
`/setup-delegate`, stored in `SetupSession.delegated_admins`). But every staged
operation then routes through `settings_mutation` / `binding_mutation` /
`resource_provisioning` → `governance.capability.actor_holds_capability`, which
requires the **administrator floor**. A non-admin delegate therefore passes
Final Review, then **fails every per-op write** — the worst UX: "you may apply"
followed by N silent authorization failures.

**Q-0098 decision:** *delegates may apply.* The contract that implements it
without privilege escalation (arc PR 3):

1. **A bounded `actor_type="setup_delegate"` bypass**, mirroring the existing
   `system`/`backfill` bypass in `actor_holds_capability`. When the capability
   check sees `actor_type="setup_delegate"`, it authorizes the write **but
   records `actor_type="setup_delegate"` in the audit row** so a delegated apply
   is never indistinguishable from an administrator write.
2. **The seam is the authority, and re-verifies live.** Only
   `services.setup_operations.apply_operations` may set
   `actor_type="setup_delegate"`, and only after re-checking
   `can_apply_setup(member, fresh_session)` at apply time (the same live-session
   re-check `_gate_apply` already does — never a boolean trusted from the view).
   This matches how `system`/`backfill` are trusted: the capability module trusts
   the actor_type because the seam that mints it is the verifier.
3. **Non-escalation guards (all four required):**
   - **AST fence** — a new `tests/unit/invariants/test_setup_delegate_actor_boundary.py`
     bans the literal `"setup_delegate"` as an `actor_type=` anywhere except
     `services/setup_operations.py` (the `test_game_wager_write_boundary`
     pattern). No other call site can mint the bypass.
   - **Setup-lane only** — the bypass authorizes the three setup-dispatched
     pipelines; it never grants the delegate standing for non-setup mutations
     (they hold no capability outside the apply).
   - **Revoke-only overlay still applies** — an explicit capability disable
     row flips a delegate OFF, same as any actor.
   - **Live re-verification** — delegation lost between opening Final Review and
     pressing apply ⇒ `can_apply_setup` returns False ⇒ no `setup_delegate`
     actor_type is minted ⇒ the write hits the administrator floor and is denied.

**Alternative considered + rejected:** teaching `actor_holds_capability` to read
`SetupSession.delegated_admins` itself. Rejected — `governance/` may not import
`services/` (layer rule), and threading the session through every pipeline call
is a wider, leakier change than a bounded, fenced actor_type. The actor_type
bypass keeps the authority decision compositional (the map's simplification #5).

---

## 5. The open design decision → router Q-0119

**Where do the governance role-pointer bindings live?** Three candidate homes,
each with a cost — this is the genuine architectural fork the convergence of
family 3 is blocked on (routed to the owner as **Q-0119**, DISCUSS lane):

- **(a) A tolerated reserved-schema path** — let `SubsystemSchema` register a
  reserved-namespace schema (`governance`) that the identity-contract validator
  *expects* (an allowlist of reserved schema subsystems), so no
  `schema_subsystem_unknown` finding. Cleanest conceptually (governance owns its
  own bindings); needs a small validator change.
- **(b) Re-home under `moderation`** — declare `moderation.trusted_role` /
  `moderation.moderator_role` *bindings* (the scalars already live in the
  moderation schema) and repoint `config_arbitration` + the backfill from
  `governance.*` to `moderation.*`. No validator change; but it conflates
  cross-cutting authority tiers with the moderation feature, and touches the
  live governance read path.
- **(c) Leave as legacy scalars permanently** — accept the role pointers as a
  documented exception (they're governance-tier authority, not feature config).
  Cheapest; abandons lane-rule uniformity for two keys.

Recommendation in the Q-block: **(a)** — it keeps governance authority in the
governance namespace and generalizes (future reserved bindings get a home), at
the cost of one validator allowlist. No code until the owner picks.

---

## 6. Real-guild smoke checklist (map rec #5) — for the P1-4 owner walk

Run on a real guild + Postgres after arc PR 2 (extends the
[production-eval checklist](../audits/production-eval-checklist-2026-06-10.md)):

1. **Three-lane edits** — a scalar setting edit/reset; a binding set/clear; a
   provisioning create-and-bind + a use-existing. Confirm each audits.
2. **Pointer retirement** — for a retired family (XP/economy): set the binding,
   confirm the runtime reads the binding (not the gone scalar); flip
   `bindings.primary` OFF and confirm legacy-KV rollback still reads.
3. **Backfill** — `dry_run` then `apply_backfill` on a guild with a legacy
   value; confirm the candidate classifies `CANDIDATE_VALID` → `written`, and a
   re-run is `skipped_idempotent`.
4. **Delegated apply** (after arc PR 3) — owner grants `/setup-delegate` to a
   **non-admin**; the delegate stages + applies a draft; confirm every op writes
   and the audit rows show `actor_type="setup_delegate"`; revoke mid-session and
   confirm the next apply is denied at the floor.
5. **Deleted target / revoked capability / kill switch** — each denies cleanly
   with accurate UX, no partial write.

---

## 7. Arc sequencing

| Arc PR | Scope | Gate |
|---|---|---|
| **1 (this PR)** | Matrix tool · backfill reframe (Required #2) · 2 parity invariants · this plan · Q-0119 | shipped, behavior-preserving |
| **2 (next)** | Retire XP-announce + economy-log scalars (families 1+2) · `test_no_dual_declared_pointer` invariant · real-Postgres binding-first proof | unblocked |
| **3** | Delegated-apply contract (§4) — the `setup_delegate` actor_type + AST fence + audit | Q-0098 (answered); design pinned in §4 |
| *(later)* | Families 3–5 (governance roles per Q-0119 · welcome/counters/mod-public-log bindings) | family 3 gated on Q-0119 |

P0-3's **P1-3 follow-up** (declared-setting → runtime-consumer disposition
invariant for the *non-pointer* settings) is deliberately not in this arc — the
map sequences P1-3 "one per track as it lands," and a reliable consumer check is
its own slice. The pointer subset (the privacy/authority-relevant one) is already
ratcheted by `test_pointer_lane_ledger`.
