# BTD6 derived-value groundedness — finding + fix

> **Status:** FINDING with a shipped first fix. Distinct from — **do not conflate
> with** — `btd6-absence-claim-guard-design.md`. That doc is about the model
> asserting a false *"X has no Y"*; **this** is about the faithfulness guard
> *rejecting a valid answer the model derived by arithmetic over grounded
> inputs*. Cousins ("the bot says no when it could say yes"), different fixes.

## 1. The finding — guard over-rejects derived-but-grounded numbers

The faithfulness guard checks whether each number/name in a draft answer appears
in the grounding ledger. It has **no notion that arithmetic over grounded inputs
yields a grounded output** — provenance does not flow through computation. So a
number that is *derived* from grounded values (a sum, a difference) looks
identical to a number that is *ungrounded* (invented): neither appears literally
in the source. The first should be allowed; the second refused. Today they are
the same to the guard, and both are rejected.

## 2. Evidence — the audit log settled it (maintainer pulled it live)

Reproduction: the bot rendered Tack Shooter's full per-tier pricing across all
paths and difficulties + paragon costs (a large, correct, version-stamped,
grounded answer). The follow-up — *"now only list the total cost it would take
to reach every upgrade, base cost and all earlier upgrade costs included"* —
**refused**, stamped 55.0, "I don't have verified data."

The `recent_audit` rows for that window:

| Age | Decision | Reason | Provider/model | Read |
|---|---|---|---|---|
| 8m | `denied` | **`grounding_failed`** | **anthropic / claude-haiku-4-5** | the total-cost turn — **the bug** |
| 3m | `denied` | `cooldown_active` | — | rate-limit (tposergaming "ice monkey"), *not* a faithfulness failure |
| 0s | `denied` | `no_mention_required` | — | bot correctly stayed silent, *not* a failure |

Per the hand-off's own rule, **`grounding_failed` with a populated
provider/model = the model generated an answer and the guard rejected it** — not
empty retrieval, not a missing tool, not a resolver gap. The model produced a
total-cost answer; the guard killed it because the summed total is not a literal
field in the grounding. (Two of the three recent "denials" are the system
working as intended — the refusals are narrower than the screenshots felt.)

## 3. Why the model cannot be trusted to just derive it either

The cumulative cost is not a naïve sum. BTD6 prices are stored as **Medium**;
other difficulties scale **per purchase** and round each to $5 *before* they are
summed. So `sum-then-scale ≠ scale-then-sum`:

- Tack Shooter top path → Inferno Ring, **Medium**: `260 + 150 + 300 + 600 +
  3500 + 45500 = $50,310`.
- Same on **Easy**, done right (per-item): `220 + 125 + 255 + 510 + 2975 +
  38675 = $42,760`.
- Same on Easy, done wrong (`round5($50,310 × 0.85)`): **$42,765** — off by $5.

So even if the guard let a derived number through, a model deriving it freehand
would sometimes be *wrong*. The right answer is **deterministic**, which points
straight at the fix this project already favours.

## 4. Fix — deterministic aggregation tool (grounded by construction)

Two options were on the table:

- **(a) A deterministic tool that computes the total**, so the number is a *tool
  output* (grounded by construction) the guard accepts — the #468 "make it
  deterministic so it's groundable" precedent.
- (b) Teach the guard that a value whose components are all grounded is itself
  grounded (provenance-through-arithmetic).

**(a) is safer and in-pattern; shipped this session:** `btd6_cumulative_cost`
(`btd6_data_service.cumulative_upgrade_costs`). Given a tower (+ optional
difficulty / path) it returns each tier's `cumulative_cost` = base + all earlier
tiers on that path, scaling **per purchase**. Registered in
`BTD6_GROUNDING_TOOL_NAMES` so its output grounds the answer. The tool's
description tells the model: *do not add the prices yourself — the returned
`cumulative_cost` is the grounded answer.*

**Verified (in-sandbox) against committed data and the live screenshot:** Tack
Shooter top → Inferno Ring = **$50,310** Medium / **$42,760** Easy (test pins
both, incl. the $42,760-not-$42,765 per-item-rounding case).
**Owed:** the live Discord confirmation — re-ask the exact total-cost question;
it must now answer with the tool's totals, not refuse.

## 5. Scope — this is the first instance, not the whole class

Option (a) fixes *cost* aggregation. The guard's derived-value blind spot is
**broader**: any answer that is arithmetic over grounded inputs (cross-path cost,
DPS from damage×rate×pierce, RBE deltas, "how much more does X cost than Y") can
hit the same `grounding_failed`. Each is closed either by a deterministic tool
(the cheap, in-pattern move, one at a time as they surface) **or** by option (b)
(one guard change that covers them all, but riskier — it must not also start
passing genuinely-invented numbers). Option (b) is the real general fix and
belongs in the same review as the absence-claim guard, because both ask the
same question: *what does the guard count as grounded?*

### 5.1 Next instance surfaced live — difficulty-scaled pricing ("buccaneer")

"Pricing of monkey buccaneer" was refused live (`grounding_failed` + provider).
**Verified it is not a data gap:** `btd6_context_service.build("pricing of monkey
buccaneer")` returns **27 facts** with the base cost and upgrade prices, the same
as sub/tack. So the *Medium* prices are grounded; what isn't is the **Easy /
Hard / Impoppable** column the model emits in a "pricing across all difficulties"
table — those are *derived* from Medium (×0.85 / ×1.08 / ×1.20, round-to-5) and
are only grounded if the model calls `btd6_difficulty_cost` for **each** number.
A full table is base + ~15 upgrades = ~16 calls; the model stitches it
inconsistently (sub table rendered; buccaneer refused), so the guard rejects the
ungrounded scaled prices. **Same root as total-cost: a derived value the model
produced without routing through the deterministic tool.** The in-pattern fix is
a single **all-difficulties tower-pricing tool** (1 call → per-upgrade × 4
difficulties, grounded by construction) — collapsing the fragile 16-call stitch.
**Owed first:** the buccaneer turn's tool-call trace, to confirm whether the
model called *nothing* (pure tool-use-discipline) or called the lookup but
freehand-scaled (the tool fixes the latter cleanly and de-risks the former).

### 5.2 Tower upgrade-cost tables — and routing is NOT the cause (tested)

More live repros: "upgrade prices for heli", "monkey ace upgrades", "pricing of
monkey buccaneer" refused; "what are all the upgrade costs of the heli", "what
about buccaneer" returned full correct cumulative/all-difficulty tables. The
intuitive theory — *the task router sometimes sends cost questions to general
instead of BTD6* — was **tested and disproven** against `ai_task_router.classify`:

| Phrasing | Route | Live |
|---|---|---|
| `monkey ace upgrades` | **btd6.answer** | **FAILED** |
| `pricing of monkey buccaneer` | **btd6.answer** | **FAILED** |
| `what are all the upgrade costs of the heli` | **general.nl_answer** | **WORKED** |
| `upgrade prices for heli` | general.nl_answer | FAILED |

**Route does not determine outcome** — questions route to BTD6 and still fail;
route to general and still work. So the determinant is **whether the model
invokes the deterministic cost tool** (`btd6_cumulative_cost` /
`btd6_difficulty_cost`) for the *derived* numbers (cumulative totals,
difficulty-scaled prices), which it does inconsistently (temperature-driven). The
"Cumulative Cost" column in the working tables is literally `btd6_cumulative_cost`
output; the failing turns free-generated the derived numbers → `grounding_failed`.

**The fix is not in the router** (that was the wrong location). It is to **stop
depending on the model to call the tool**: detect tower upgrade-cost intent and
**auto-attach the deterministic cost grounding** (cumulative + all-difficulty
facts, built from `btd6_data_service.cumulative_upgrade_costs` +
`difficulty_costs`) into the BTD6 context, the same way #478 auto-grounds upgrade
modifiers.

**SHIPPED** (`_render_tower_costs`, maintainer chose the broad scope — **every**
resolved-tower question): each tower now grounds a `[btd6_cost]` block — base +
each upgrade's per-buy (Easy/Med/Hard/Impop) and cumulative (base+priors) cost —
so the all-difficulty and total-cost tables are grounded by construction, no tool
call required. Numbers verified in-sandbox (reuses the tested cumulative engine);
**efficacy (model uses them, guard accepts) is live-owed**.

> The false **"no paragon"** claim (see the absence-claim doc, Update 2) is the
> *same shape* on a different field: the paragon grounding line exists and is
> correct, but on a turn where it wasn't surfaced the model confabulated an
> absence. Auto-attaching tower grounding reliably (this section's fix) also
> removes that false negative — the two fixes overlap.

## 6. Relationship to the absence-claim guard (the named edge)

The absence-claim backstop proposed in `btd6-absence-claim-guard-design.md`
inspects a generated negative and checks whether grounding supports it. The
total-cost case exposes a real edge that design must name: **some false-negatives
are not "no grounding exists" but "grounding exists yet requires derivation"** —
a naïve supports/doesn't-support check passes the refusal as legitimate because
it cannot see that the grounded inputs needed to be *summed*. So:

- **MOAB / "X has no Y"** → absence-claim family (model asserts/refuses a
  negative; fix = resolution-status gate, see the other doc).
- **Total-cost** → derived-value family (guard rejects a valid derivation; fix =
  deterministic tool now, provenance-through-arithmetic later).

They share a root question (*what is grounded?*) but are separate fixes, and the
audit `reason`/`provider` columns discriminate them turn-by-turn.

**Update (post-#482):** the MOAB row chase is now moot — asked with the upgrade
*named*, the bot **answers** (+15 vs MOAB-class), so the MOAB *refusal* no longer
reproduces and a *pure* absence-claim hasn't surfaced live. What MOAB now shows
instead is the **deny-then-answer** preamble (it opens "I don't have a
'multiplier' figure", then answers) — the **mild cousin** of this derived-value
bug: in the severe case the guard kills the answer; in the mild case the model
just narrates a false "I don't have it" before giving the grounded answer. Both
come from conflating *"this exact labelled figure isn't a field"* with *"I can't
answer."* See the evidence-update + revised-priority table in
`btd6-absence-claim-guard-design.md`.
