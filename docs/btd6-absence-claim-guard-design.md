# BTD6 absence-claim guard — design proposal

> **Status:** DESIGN PROPOSAL — *not* binding, *not* implemented. Written for
> independent review (ChatGPT / Analysis side) before any guard code is merged,
> per the v55 hand-off ("Task 1: DESIGN FIRST, do NOT implement blind").
> The companion status ledger is `btd6-gamedata-decode-status.md`.
>
> **One-line ask of the reviewer:** does the layered design below (a cheap
> retrieval fix + an absence-claim *gate* that never lets an *unresolved* empty
> lookup license a "no") correctly close the false-negative hole without turning
> every legitimate "I don't know" into a tool-loop? The crux is in §4.3.
>
> **Sibling finding (do NOT conflate):**
> `btd6-derived-value-groundedness-finding.md` covers a *different* false-"no" —
> the guard rejecting a value the model *derived* from grounded inputs
> (total-cost). That one is diagnosed from the audit log and already has a
> shipped first fix; this doc is the *absence-claim* family only. They share one
> root question — *what does the guard count as grounded?* — and §5 below names
> the edge where they meet.

---

## Evidence update (2026-06-04) — this guard is DEPRIORITIZED

Two more live tests (maintainer) reshaped the diagnosis after this doc's first
draft. **Build the fix the evidence points at; this general guard is not the
next PR.**

1. **MOAB-bonus, when the upgrade is *named*, now ANSWERS.** Asked "list the
   damage multipliers of the MOAB Mauler," the bot resolves Bomb Shooter 0-3-0,
   states +15 vs MOAB-class, gives base stats (1 dmg / 22 pierce / 0.825s),
   explains the +15 → 16 stack, lists the MOAB-class set, and correctly calls it
   a flat bonus, not a multiplier — a fully-grounded answer (every number is in
   `grounding_for_query("moab mauler")`, verified). So the "middle path" refusal
   does **not** reproduce once a tier is named; it was a resolver/query-shaping
   gap that explicit naming bypasses. **MOAB is no longer the canonical failing
   case — downgraded.**

2. **A *pure* absence-claim ("X has no Y" with no answer attached) has NOT been
   reproduced live.** Every failure caught is one of two narrower things —
   derived-value rejection (total-cost, confirmed) or *deny-then-answer* (below).
   Building the general absence-claim gate for a mode that isn't occurring is
   premature. This design stays a **provisional backstop**, not the next PR.

### The behaviour that IS occurring — deny-then-answer (the mild cousin)

Three live instances now (MOAB "multipliers"; Bomb Shooter "multipliers per
tier"; this MOAB answer): the model **answers correctly but prepends a false
"I don't have `<X>`"** because the user's *word* ("multiplier") is not a literal
field name — even though the flat +15 bonus *is* the answer, relabelled. The
answer survives; the framing is misleadingly negative.

- **Severity:** mild (the answer is correct; only the preamble is wrong) — vs
  the severe derived-value case where the guard kills the answer outright.
- **Mechanism (prompt, not guard):** `ai_instruction_service` already says
  *"ALWAYS run the lookup before telling the user you lack a figure … only
  report missing after found=false"* (good — covers hard refusals) **and** *"if a
  specific figure still cannot be verified, give your general answer but flag
  that one number"* (a hedge-then-answer pattern). The model **over-applies the
  hedge-then-answer pattern** to a figure that is answerable under a *different
  label* — it flags "multiplier" as missing, then answers with the bonus.
- **Proposed fix (next session; prompt change → must live-verify; NOT now):** a
  framing clarification that a differently-*labelled* equivalent (a flat bonus
  answers "multiplier"; a per-tier table answers "scaling") is **not** a missing
  figure to disclaim — answer the substance directly, and only flag a figure
  that is genuinely absent after a `found=false` lookup.

### Revised priority

| Problem | Status | Next |
|---|---|---|
| Derived-value rejection (total-cost) | **confirmed** (audit `grounding_failed` + provider); fix **shipped** (`btd6_cumulative_cost`, #482) | live-verify the re-ask |
| Deny-then-answer preamble | confirmed live ×3; **mild** | framing fix + live-verify (next) |
| Pure absence-claim ("X has no Y") | **not reproduced** live | keep this design as a backstop; do **not** build yet |

The original problem statement and design (§1–§7) remain valid as the *backstop*
for if/when a pure absence-claim does surface — read them in that light.

---

## 1. The problem

The faithfulness verifier catches **ungrounded positives** — a number or proper
name in the answer that is not present in the grounding ledger (tool outputs +
auto-grounded facts). It does **not** catch **absence claims**: the bot can
fluently, version-stampedly assert *"X has no Y"* when X does have Y, and
nothing stops it. A fluent false "no" is **worse than a refusal** — it looks
authoritative, and the user believes it.

This is structural, not a tuning miss. An absence sentence —

> "The Bomb Shooter's middle path has **no** bonus damage vs MOAB-class bloons."

— contains a real, groundable **subject** ("Bomb Shooter middle path") and a
**negative-existential predicate** ("has no bonus damage vs MOABs"). There is no
ungrounded positive token to flag. The claim asserts the *non-existence* of a
fact, and you cannot verify non-existence by checking presence. The verifier
would have to confirm that a lookup was actually attempted **and came back empty
for a data reason** — which it does not do today.

## 2. Diagnostic evidence (run this session, not assumed)

The canonical reproduction is Bomb Shooter middle path MOAB bonus damage. Last
session the bot refused/denied it. We pulled the real service paths
(`btd6_upgrade_detail_service.grounding_for_query`,
`btd6_upgrade_service.resolve_upgrade`) instead of theorising:

| Query | `resolve_upgrade` | Grounding rendered |
|---|---|---|
| `moab mauler` | `exact_name` → `bomb_shooter:030` | "+15 damage vs MOAB-Class" ✅ |
| `moab assassin` | `exact_name` → `bomb_shooter:040` | "+30 damage vs MOAB-Class" ✅ |
| `moab eliminator` | `exact_name` → `bomb_shooter:050` | "+99 damage vs MOAB-Class" ✅ |
| **`bomb shooter middle path`** | **`none`** | **`[]` — 0 lines** |

**The data is extracted and reachable by name.** The MOAB bonus is core
committed stat data, exactly where it should be. The failure is that the
**path/line-level phrasing never resolves to the named tiers that hold it**, so
nothing grounds, and the model fills the vacuum with a confident negative. This
is the second branch of the hand-off's decision tree — *the false-negative /
absence-claim hole, data sitting unqueried* — **not** an extraction gap.

> **Settle it from the audit log, not this doc — still owed.** The table above
> probed the *generic* phrasing `"bomb shooter middle path"`; the **live** query
> string last session is unknown, and it matters: if the user actually named a
> tier ("MOAB Mauler"), it resolves and grounds (shown above), so the live
> failure could be *grounded-then-rejected* — the same shape as the total-cost
> case in the sibling finding — rather than never-resolved. The `recent_audit`
> row discriminates: **`provider=—`** ⇒ never-resolved (this absence-claim /
> retrieval family); **`provider` populated + `grounding_failed`** ⇒
> generated-then-rejected (sibling family). The maintainer must re-ask live and
> read that one row. The total-cost row has been pulled (provider populated); the
> MOAB row has **not** — it decides whether these are one bug or two.

### 2.1 The milder sibling (same root, smaller blast radius)

Asked for "damage **multipliers** per tier," the bot denied having them, then
immediately printed a full per-tier damage table. It gated its "no" on the
user's *word* ("multiplier") rather than on whether the **question was
answerable** from data it already held under another label ("per-tier damage").
Root cause is identical — *reasoning about whether data is labelled a certain
way, vs. whether the question is answerable* — but here the subject **did**
resolve and the data **was** in context, so the fix is narrower (see §4.4). Keep
it noted but **do not conflate** it with the unresolved-subject case.

## 3. Why #478 does not already cover this

#478 auto-grounds a **resolved upgrade**'s modifiers into context (Pass 3c), so
the data is present without an explicit tool call. That mitigates the hole on
**one path only** — the upgrade-modifier path — and **only when the upgrade
resolves**. It does nothing when:

- the phrasing is path/line-level and resolves to `none` (the MOAB case itself);
- the subject is a **round / map / mode / bloon / relic / paragon / CT** entity
  (every non-upgrade domain is unguarded);
- the asserted-absent attribute lives in a **different tool** than the one that
  resolved the subject (cross-domain "does X have Y").

**The general absence-claim hole is open in every domain.** #478 is a point
mitigation, not the guard.

## 4. Design

The fix is **two layers**. Layer A is a cheap retrieval improvement that
removes the most common trigger and should ship as its own small PR. Layer B is
the actual guard and is what needs review.

### 4.1 Layer A — path/line-aware resolution (retrieval, not a guard)

Teach the upgrade resolver to expand **path/line references** to the set of
tiers on that path and auto-ground them:

- "bomb shooter **middle path**" → `bomb_shooter:0X0` tiers 3–5 (or all five) →
  ground each tier's modifiers.
- "**top path** dart monkey", "wizard **bottom path** tier 4", etc.

This is the same shape as the rounds/maps/modes reachability fixes that worked
(*extracted ≠ reachable*: surface a field, don't just hold the file). It is
**not** an absence guard — it shrinks sub-mode A (never-resolved) so the guard
fires rarely. Recommended first, separately, low risk.

### 4.2 Layer B — the absence-claim gate

Add a **negative-existential** claim type to the faithfulness verifier and gate
it. For a draft sentence asserting *"E has no A" / "E lacks A" / "E doesn't have
A" / "there is no A for E"* about a BTD6 subject E and attribute A:

1. **Resolve E to ≥1 concrete catalog entity this turn.** "Middle path" expands
   to its tiers (via Layer A); a tower name to the tower; etc.
2. **If E does not resolve → the absence claim is rejected.** The model may not
   say "E has no A" about a subject it could not identify. It must downgrade to a
   *clarify/refuse* ("I couldn't pin down <E> — did you mean …?"), never a
   confident negative.
3. **If E resolves → check A against the resolved entity's full committed
   record** (all tiers / all fields / all tools that own A for E), not against a
   single tool's empty return. Only if A is genuinely absent from that record
   may an absence be asserted — and then **phrased as bounded**: "the committed
   data for <E> doesn't list <A>", not the absolute "E has no A".

### 4.3 The crux — an empty *unresolved* lookup must never license a "no"

The naive implementation of "force a lookup before allowing an absence claim,
and if it returns empty, allow it" **ships the exact bug we are fixing.** In the
MOAB case `resolve_upgrade("bomb shooter middle path")` returns empty for a
**resolver** reason (the phrasing didn't match a named upgrade), **not** a
**data** reason (the fact is genuinely absent). A guard that treats "lookup
returned empty" as proof of absence would *confirm* the false negative and stamp
it as verified.

So the gate must distinguish:

- **empty because the subject didn't resolve** → re-resolve (Layer A) or
  refuse-to-assert; **never** license the "no";
- **empty because A is absent from a fully-resolved E's record** → may license a
  **bounded** "no".

This distinction — *resolution status*, not *result emptiness* — is the whole
design. A reviewer should attack it here first.

### 4.4 The milder sibling (§2.1)

For the resolved-but-mislabelled case, no resolution work is needed; the gate's
step 3 already covers it: the subject resolved, and "damage" data **is** in the
record, so an absence claim about "multipliers" fails the record check (the
attribute *is* present, under a synonymous label). The remaining work is a small
**attribute-synonym map** (multiplier ↔ per-tier damage, "bonus" ↔ modifier,
etc.) so the record check matches the user's term to the held data. Low risk;
can ride with Layer A.

## 5. Costs and false-positives (confronted, not waved away)

| Concern | Reality | Mitigation |
|---|---|---|
| **Latency** | An extra resolution/retrieval pass before an absence claim ships. | Gate **only** fires when the draft actually contains a negative-existential about a BTD6 subject; normal positive answers are untouched. Cap forced re-resolution to one pass. |
| **False positives (blocking a true "no")** | "Dart Monkey has no camo detection at base" is a *true* negative we'd intercept. | If E resolves and A is verifiably absent from its record, the "no" is **permitted** (bounded form). The true-"no" path is allowed; only the *unverifiable* "no" is downgraded. |
| **Unverifiable negatives (dataset gaps)** | If we genuinely don't model A for E, we cannot *prove* absence. | Enforce epistemic humility: emit "I don't have that for <E>", **not** "E has no A". This is the honest output and is exactly the false-confidence we're killing. |
| **Detection precision** | Distinguishing a real absence assertion from incidental negation ("not recommended", "no need to") is fuzzy. | Tight negative-existential classifier scoped to BTD6 subject+attribute shape; over-broad detection inflates latency and blocks good answers, so err toward precision and lean on Layer A to reduce volume. |
| **Tool-loop risk** | Forcing checks on genuinely out-of-domain subjects could loop. | The gate's terminal state for an unresolved subject is **clarify/refuse**, not "retry retrieval forever". One re-resolution attempt, then a scoped non-answer. |

## 6. Recommendation

1. **Ship Layer A first** (path/line-aware resolution + attribute-synonym map) as
   a small reachability PR — it removes the canonical trigger and the §2.1
   sibling with no guard machinery, and is verifiable live the same way the
   round/map/mode tools were.
2. **Review Layer B (the gate) before implementing.** The design stands or falls
   on §4.3 (resolution-status, not result-emptiness). Land it only after the
   reviewer is satisfied that an unresolved empty lookup can never license a "no",
   and that the false-positive table above is acceptable.
3. **Definition of done for this stage:** this proposal, reviewed — *not* a
   merged guard.

## 7. Open questions for the reviewer

- Is **resolution-status** the right discriminator, or is there a cleaner signal
  (e.g. provider-populated-but-empty vs. provider-absent in the audit ledger)
  that the gate should key on instead?
- Should Layer A expand a "path" to **all five tiers** or only the tiers that
  carry the queried attribute (narrower grounding, but needs the attribute parsed
  before resolution)?
- Where should the negative-existential classifier live — in the existing claim
  extractor, or as a pre-emission pass in the natural-language stage?
- For cross-domain "does X have Y", how do we know **which** tool owns Y for E so
  the record check is complete rather than checking one tool and declaring
  absence?
