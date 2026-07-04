# Gate-0 owner-decision packet — the 12 OWNER-ONLY rows (+ L-21)

> **Status:** `reference` — owner-consumable Gate-0 grammar-freeze artifact (2026-07-04). **NOT SOURCE OF
> TRUTH.** Renders the **12 OWNER-ONLY** register rows (+ L-21) for the maintainer to rule on.
> This packet **decides nothing** — each card renders THE CALL, the options, the built default that
> ships *until* you rule, and *why* it can't be auto-ratified. Companion:
> [`register-resolution.md`](register-resolution.md) (the 19 already-frozen rows).
>
> The maintainer rules from this packet in plain language; an agent then routes each answer to
> `docs/owner/maintainer-question-router.md` (DISCUSS lane where a row narrows a binding Q). Source
> specs win (Q-0120): `design/question-register.md`, worklist Part 2, `seam-consistency-matrix.md`.

**How to read a card.** (1) **THE CALL** — the one decision · (2) **OPTIONS** · (3) **SHIPS UNTIL
YOU RULE** — the built default already in the code · (4) **WHY THIS IS YOURS** — irreversible? money?
architecture? narrows a binding Q? rubric edit? · (5) **register-Q + binding-Q touched.**

---

# GROUP 1 — NEAR-IRREVERSIBLE / DATA-LOSS (decide these with the most care)

These four either move real money, set how much data a disaster may destroy, or write a
silent-loss default into the grammar. Freezing the *wrong* default here is expensive or unrecoverable.

---

### 🔴 Q-D8 — Store-drop disposition default (SF-g)

- **THE CALL:** When a `StoreSpec` is dropped via a signed retirement, is there a *global default*
  disposition, or must **every** retirement name one explicitly?
- **OPTIONS:**
  - (a) global default (e.g. `reverse-migrate`) applied when a retirement names none
  - (b) **no default — `disposition` REQUIRED** per signed `store_retirements.yml` entry (`export` / `reverse-migrate` / `declared-loss`)
  - (c) default to the safest disposition
- **SHIPS UNTIL YOU RULE:** (b) — there is deliberately **no default**; a retirement with no
  `disposition` is unconstructible. (The compile fence forbids `DROP` on a value store regardless.)
- **WHY THIS IS YOURS:** **data-loss policy.** A silent global disposition is a silent data-loss path
  — the exact class §3.6 exists to kill. The recommendation is literally *"there is no default,"* so
  there is nothing for Gate-0 to auto-pin; each retirement forces an explicit signer call at sign-off.
- **Register-Q:** Q-D8 (01 §8 fork 8 / SF-g · ⊕ net-new, ∥ L-18). No binding-Q.

---

### 🔴 Q-D13 — Repair DIRECTION for a value-bearing violation (the money call)

- **THE CALL:** When an invariant finds a money mismatch (e.g. aggregate = 500 but ledger = 480),
  which store is ground truth — **mint** 20 ledger rows, or **claw** the aggregate down to 480?
- **OPTIONS:**
  - (A) aggregate = ground truth → mint the difference (launders an unaudited mint)
  - (B) ledger = ground truth → claw the aggregate (destroys real balance)
  - (C) **`QUARANTINE_ONLY`** — never auto-mutate; you sign each disposition case-by-case
- **SHIPS UNTIL YOU RULE:** (C) `QUARANTINE_ONLY`. The fence *requires* an owner-signed
  `ground_truth_store` before any value-bearing auto-repair, so absent your direction it quarantines
  and never touches money.
- **WHY THIS IS YOURS:** **money, near-irreversible.** The per-invariant A-vs-B direction either mints
  balance from nothing or destroys a real one — an unrecoverable call only you can make.
- **Register-Q:** Q-D13 (11 §4 Q3 · ⊕ net-new, money; relates L-1). No binding-Q.

---

### 🔴 Q-D14 — RPO target + backup source tier

- **THE CALL:** How much data may a disaster lose (the RPO), and via which backup source?
- **OPTIONS:**
  - (A) daily `pg_dump` only ⇒ flat **≤24 h** loss for *all* stores including money/audit
  - (B) build an off-box `audit_log` export ⇒ **minutes-RPO money spine** (a real build cost)
  - (C) Railway PITR ⇒ **minutes-RPO whole-DB** (a plan upgrade cost)
- **SHIPS UNTIL YOU RULE:** (A) daily `pg_dump` / flat ≤24 h — the honest built floor.
- **WHY THIS IS YOURS:** **plan-cost vs build-cost vs 24 h-acceptable.** Near-continuous RPO on the
  money spine is **not free** — it costs either a plan upgrade (C) or a real build (B). A genuine
  spend/scope call; do not present minutes-RPO as free.
- **Register-Q:** Q-D14 (13 §4 Q1 · L-18 RPO leg). No binding-Q.

---

### 🔴 Q-D15 — Rollback-data disposition + window N

- **THE CALL:** What happens to writes made *through the new bot* during an N-day rollback window —
  and how long is N?
- **OPTIONS:**
  - (A) pure `DECLARED_LOSS` + short N + sign-off
  - (B) **`DECLARED_LOSS` + a narrow reverse-import valve** for the derived `REVERSE_IMPORTABLE`
    (invertible-∧-value-bearing) tier + short forward-fix-biased N + owner-signed M1/M2 loss manifest
  - (C) full reverse-import (**rejected** — impossible for collapsed / new-only stores)
- **SHIPS UNTIL YOU RULE:** (B) — round-trip the one class where loss is unacceptable (money/audit by
  `mutation_id` / absolute-value copy), declare the rest lost, keep N short and forward-fix-first.
  **The value of N stays your Stage-3 carry.**
- **WHY THIS IS YOURS:** **data-loss policy, near-irreversible either way**, with a real
  reverse-importer build cost. The README's #1 owner-only.
- **Register-Q:** Q-D15 (13 §4 Q3 / §2.4 · L-18 + FJ §6 T2 + Tier-3 N carry). No binding-Q.

---

# GROUP 2 — POLICY / BINDING-Q / ARCHITECTURE (rule, or bless the default)

The default unblocks the build today; each is yours because it **flips a frozen field, narrows a
binding owner brake, edits the rubric, sets mission strategy, or commits an architectural primitive.**

---

### Q-D5 — `IntentPosture`: DEGRADE or fail-closed?

- **THE CALL:** On an *unapproved privileged intent* (`message_content` / `members`), should the bot
  **boot slash-only** (DEGRADE), or **refuse to boot** (`FAILED_STARTUP`)?
- **OPTIONS:**
  - (a) **DEGRADE** — boot slash-only + explicit `DegradedCapability` + admin notice
  - (b) keep 05's `required=True` **fail-closed** (`FAILED_STARTUP`)
- **DESIGN RECOMMENDATION:** (a) DEGRADE — fail-closed darks the whole bot when it could serve
  slash-only; slash-first survivability is the growth posture, and the degrade keeps the fail-closed
  goal (no *silent* reliance) by being explicit.
- **SHIPS UNTIL YOU RULE:** **`required=True` fail-closed** — the conservative floor. (Note the
  divergence: the recommendation is DEGRADE, but flipping a *frozen* field can't be auto-applied, so
  the seam-matrix ships `required=True` until you rule. Worklist Part 2 lists DEGRADE as the shipped
  default; the seam-consistency-matrix + Part 3 win per Q-0120 — see reconciliation note below.)
- **WHY THIS IS YOURS:** **flips a frozen `required` field** on the `INTENT_CONTRACT` (05 §3.1) —
  narrows a frozen-vocab decision; the one OPEN cross-spec seam (**F-3**), carried not closed.
- **Register-Q:** Q-D5 (14→05 · **F-3** / PG-2 · L-17). Touches the frozen INTENT_CONTRACT.

---

### Q-D16 — A credential-lifecycle recovery arm at all?

- **THE CALL:** Build a credential-lifecycle recovery arm (registry + tiered rotation cadence +
  revocation carve-out + compromise runbook), or not?
- **OPTIONS:**
  - (a) **full arm** — registry + tiered cadence + revocation carve-out + runbook
  - (b) runbook only, no cadence
  - (c) none (accept no declared kill-path)
- **SHIPS UNTIL YOU RULE:** (a) full arm.
- **WHY THIS IS YOURS:** **touches binding Q-0213** (credential concentration) → route as **router
  DISCUSS.** A recovery arm is orthogonal to Q-0213 (which declined *custody/scoping*, not *recovery*)
  and *removes* owner-dependency at compromise-time — the opposite of what Q-0213 guards.
- **Register-Q:** Q-D16 (12 §4 CL-1 / FJ §4 #10) · **binding Q-0213.**

---

### Q-D17 — Revocation carve-out from the Q-0213 `*Delete` brake?

- **THE CALL:** Narrow the Q-0213 ask-first `*Delete` brake to exclude an **agent-run credential
  revoke**, so a compromised token can be killed without waiting on you?
- **OPTIONS:**
  - (a) credential revoke (`RevocationRef` closed set) = agent-runnable recovery; **resource** delete
    stays ask-first
  - (b) keep all `*Delete` ask-first (recovery waits on the owner)
- **SHIPS UNTIL YOU RULE:** (a).
- **WHY THIS IS YOURS:** **narrows a binding Q-0213 brake** → route as **router DISCUSS.** Narrowing a
  binding owner brake is by definition an owner ruling (a token revoke loses no data; the brake's
  intent is *data-loss*, and its `*Delete` pattern over-captures `apiTokenDelete`).
- **Register-Q:** Q-D17 (12 §4 CL-2 / FJ §4 #10) · **binding Q-0213.**

---

### Q-D18 — Supply-chain lockfile + `pip-audit` CI gate? *(found this harvest)*

- **THE CALL:** Add a `requirements.lock` + hash-verify + `pip-audit` CI gate alongside the Q-0105
  adopt-freely grant?
- **OPTIONS:**
  - (a) **lockfile + CI gate** — adopt-freely unchanged; the lock diff becomes the deferred-review artifact
  - (b) blocking human-review on every dep add
  - (c) status quo (floating `>=`, no lock)
- **SHIPS UNTIL YOU RULE:** (a) lockfile + CI gate.
- **WHY THIS IS YOURS:** **touches binding Q-0105** (adopt-freely) → route as **router DISCUSS.**
  *Low-confidence owner-only* — it **composes with** rather than contradicts adopt-freely (adopt →
  regenerate lock → CI verifies), so you could reasonably wave it through at the sitting; flagged so
  the call is deliberate.
- **Register-Q:** Q-D18 (12 §4 CL-3 / FJ §4 #12) · **binding Q-0105.**

---

### Q-D19 — `SB_PROD_ATTEST` durable custody source (SF-d)

- **THE CALL:** Keep `SB_PROD_ATTEST` as a plain env token, or upgrade its custody at CUT-1?
- **OPTIONS:**
  - (a) **presence-gated env `SecretSpec`** (the 4th data-plane rail is correct today)
  - (b) sealed / managed secret
  - (c) short-lived OIDC claim
- **SHIPS UNTIL YOU RULE:** (a) presence-gated env `SecretSpec` — buildable now; the custody *source*
  is carried forward unresolved.
- **WHY THIS IS YOURS:** **ops / CUT-1 call.** The register verdict is literally *"defer to owner —
  genuinely owner-gated"* (shared-vocab §⑧ SF-d); only the custody source is deferred, the rotation
  row homes in the credential registry (CL-5).
- **Register-Q:** Q-D19 (05 §9 · 12 CL-5b / SF-d · L-10 / FJ §4 #10). No single binding-Q (relates Q-0213).

---

### Q-D20 — Adopt security rubric classes 11/12/13 + run one adversarial-abuse pass?

- **THE CALL:** Adopt three new review classes — **11 cost/quota · 12 privacy/retention · 13
  security/non-functional** — and run one adversarial-abuse pass; and who runs it?
- **OPTIONS:**
  - classes: (a) **adopt all three as-shaped** · (b) a different cut · (c) fold into audit-B's 5-facet
  - retro scope: (a) forward-only · (b) full re-walk · (c) **forward + one retroactive pass**
  - runner: (a) **dedicated adversarial agent** · (b) Stage-2 walkers · (c) owner
- **SHIPS UNTIL YOU RULE:** classes (a) + retro (c) + runner (a) — three orthogonal victim-axes
  (payer / data-subject / integrity), the one pass *is* the retroactive coverage.
- **WHY THIS IS YOURS:** **rubric edit.** Q-0233 froze the ten rubric classes; edits are *proposed,
  not self-applied*, so adopting new classes is an owner ruling by construction.
- **Register-Q:** Q-D20 (10 §4 T-1/2/3 · L-19 / FJ §8) · **binding Q-0233.**

---

### Q-D21 — Growth posture (PG-1): hard-gate on verification, or slash-first?

- **THE CALL:** Pursue Discord verification as a **hard gate on growth**, or grow **slash-first** with
  an intent-denial fallback and pursue verification in parallel?
- **OPTIONS:**
  - (a) **slash-first survivability** + intent-denial fallback; verification = a parallel milestone,
    **not** a growth gate
  - (b) hard-gate — freeze growth past ~75 guilds until `message_content` is approved
- **SHIPS UNTIL YOU RULE:** (a) slash-first.
- **WHY THIS IS YOURS:** **mission / growth strategy.** Verification approval is externally-owned,
  discretionary, and latency-uncontrollable; a hard gate freezes the mission on Discord's queue and
  `message_content` denial is routine. A genuine owner strategy call.
- **Register-Q:** Q-D21 (14 §4 PG-1 · L-17 / FJ §4 #1). No binding-Q.

---

### Q-D24 — Multi-actor session concurrency-control: kernel primitive now, or Stage-2? *(found this harvest)*

- **THE CALL:** Name a **foundational kernel concurrency primitive** for multi-actor session
  transitions now (two joins as the window fires, a round-advance racing a forfeit, a double-settle),
  or defer to Stage-2 per-subsystem?
- **OPTIONS:**
  - (A) **name K7 `NATURAL_KEY`-on-the-session-row** (`FOR UPDATE` / `WHERE state_version=N`
    compare-and-swap) as the designated seam + a **compile fence** requiring session-transition ops to
    declare it
  - (B) leave it to Stage-2, but add one coverage-map / strand-2 line stating the concurrency seam
    **is** K7 `NATURAL_KEY` and Stage-2 must use it
- **SHIPS UNTIL YOU RULE:** (A) — gives the Gate-V multi-actor golden a mechanism to pass against;
  do **not** leave L-20 a test with no named mechanism.
- **WHY THIS IS YOURS:** **architecture.** Committing a new kernel-level concurrency primitive +
  compile fence is the "large / cross-cutting (architectural)" ask-first class. *Nuance:* both options
  converge on the **same** K7 `NATURAL_KEY` mechanism — the call is *build-the-fence-now (A)* vs
  *defer with a coverage line (B)* — an easy bless if you want the fence now.
- **Register-Q:** Q-D24 (whole-set gap; 07 `NATURAL_KEY` · 11 `TERMINAL_ONCE` · L-20). No binding-Q (architecture).

---

# FLAGGED SEPARATELY — L-21 (owner-only, but NOT one of the 31 register rows)

### L-21 — Old-bot change-policy

- **THE CALL:** Ratify an **interim old-bot change-policy** so ongoing old-bot feature work doesn't
  drift from the frozen corpus / goldens during the rebuild.
- **OPTIONS:** *(the source gives no formal a/b/c set — it is an L-ledger gap, not a register row.)*
  The shape to rule on: freeze-aligned (new old-bot work must not diverge the corpus) vs. unconstrained.
- **SHIPS UNTIL YOU RULE:** no enforced policy — this is the **softest binding, no CI guard owns it.**
- **WHY THIS IS YOURS + WHY SEPARATE:** it is an **L-ledger row carried on README §4 gap #5**, **not**
  a Q-D register row, so it is **excluded from the count of 31.** Flag it at the sitting alongside the
  12, but track it as an **L-row**, not a register disposition.
- **Maps-to:** L-21 (README §4 gap #5).

---

## Reconciliation notes (Q-0120 — where sources disagreed)

- **Q-D5 shipped default.** Worklist Part 2 lists the shipped-until-ruled default as **(a) DEGRADE**;
  the **seam-consistency-matrix (F-3, CARRIED) + worklist Part 3 win** — the built floor ships
  **`required=True` fail-closed** until PG-2 rules, because a *frozen* field can't be auto-flipped.
  DEGRADE is the design *recommendation*, not the shipped floor. Rendered both above.
- **Register F-labels.** The register mislabels the cross-spec forks for Q-D5 (reads "F-4"); the
  canonical PIN numbering is **F-3 = intent posture** (used above). Same scramble corrected in
  `register-resolution.md` for the RATIFY-DEFAULT rows.
- **Count.** 12 OWNER-ONLY = README §4 baseline of 10 (Q-D5/8/13/14/15/16/17/19/20/21) + 2 found this
  harvest (**Q-D18**, **Q-D24**). L-21 is owner-only but outside the 31.
