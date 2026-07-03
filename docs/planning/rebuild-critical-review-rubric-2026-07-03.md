# The critical-review rubric — how to find forgotten steps, missing features & gaps (2026-07-03)

> **Status:** `plan` — a **reusable review lens**, owner-directed (PR #1685). It extracts the
> *classes* of gaps caught while reviewing the rebuild plan on 2026-07-03 into a repeatable rubric,
> so the rest of the bot can be reviewed the same critical way — by the Stage-2 subsystem walk, the
> Phase-B adversarial-completeness pass, and any future review. Owner ruling → **Q-0233**.
> Companion to the session's decision logs (stage-1 · conventions · hub-navigation). Source wins
> over this doc (Q-0120).

---

## Why this exists — the pattern behind the findings

A plan or a piece of code **tells you what it does. It never tells you whether it is complete,
correctly ordered, non-duplicated, verifiable, and consistent with the whole picture.** Reading
top-to-bottom and nodding along never surfaces those gaps — you only find them by *interrogating*
the artifact against four things it can't self-report:

1. its **dependencies** (what must exist first),
2. the **full expected surface** (what a user/competitor would expect but the artifact omits),
3. **what already exists** (is this reinventing something?),
4. **how you'd prove it correct** (is there an oracle?).

The owner named this as "forgotten steps, missing features, proper goals." This rubric turns that
instinct into a checklist so it isn't instinct anymore.

**How to use it.** Run every finding-class below against **each subsystem** in the Stage-2 walk and
against **each plan** in Phase B. Each class has a **probing question**, the **real example** it
was distilled from (2026-07-03), and a **mechanization** tag:
- 🧠 **human-probe** — needs judgment; the reviewer asks the question.
- ⚙️ **checker (exists)** — already mechanized; cite the script.
- 🔧 **checker (build)** — mechanizable; routed in §"Mechanization roadmap".

---

## The finding-classes

### 1. Dependency-order inversion — 🔧 checker (build)
**Probe:** *Is anything here scheduled or built before something it depends on?*
**Today:** welcome (L1b) needed the visual card engine (L1c), built a band later; welcome also
depended on `role`, three slots later in the same band.
**Mechanize:** once dependencies are declared (manifest `depends_on`), a topological check flags any
consumer positioned before its provider. Distinguish *engine-class* (must precede consumer) from
*peer-class* (may ship as a declared-seam deferral) per S-2 (Q-0220).

### 2. Forgotten capability — 🧠 human-probe
**Probe:** *What would a user (or a competitor's user) reasonably expect here that is nowhere in the
plan?* Fastest form: "name the thing you'd be upset to launch without."
**Today:** AI image/media generation — absent from all 43 subsystems until the owner named it.
**Mechanize (partial):** cross-check the capability corpus + competitor feature lists for coverage;
pure absence resists automation, so this stays primarily human — but the corpus cross-check catches
"declared-but-unhomed."

### 3. Thin / underspecified step — 🔧 checker (build)
**Probe:** *Which steps are one vague line where their risk demands a real design?*
**Today:** cutover — the highest-risk moment, described in scattered fragments with no step.
**Mechanize:** flag plan sections whose length/structure is low *relative to their declared
risk/importance* (a high-risk item with a one-paragraph section is suspect).

### 4. Stale / un-anchored state claim — ⚙️ checker (exists, extend)
**Probe:** *Is this %, status, or "done" claim anchored to a verifiable commit — and still true?*
**Today:** the substrate kit read as "45–55%" (and separately believed "complete") when source
showed ~90–95% with a named tail — a figure that misled twice in one week.
**Mechanize:** `scripts/check_plan_staleness.py` already flags `plan`-badged files carrying shipped
markers. **Extend it** to flag an un-anchored `NN%` / "complete" claim about a fast-moving component
(no `as of #PR` anchor) — routed below.

### 5. Fragmentation / reinvention — 🔧 checker (build)
**Probe:** *Does this capability already exist elsewhere — implemented more than once?*
**Today:** presets reimplemented ≥7× (`ai_preset_service`, `ai_orchestration_presets`,
`automation_templates`, `setup_role_templates`, `logging_presets`, `edit_number_presets`,
`preset_picker` + setup `preset_select`); fuzzy matchers scattered; the help editor a separate path
from the setup preset selector.
**Mechanize:** heuristic scan for repeated concept-name suffixes (`*_presets`, `*_templates`,
`*_helpers`) and near-duplicate module shapes; surface clusters for human confirmation. (This is the
"grep for it first" reflex, mechanized.)

### 6. Under-generalization / wrong generalization — 🧠 human-probe
**Probe:** *Is this built for one use when it clearly serves several — or generalized for a single
consumer that doesn't justify it?* (The second-consumer rule, S-1/Q-0219.)
**Today:** the card engine (built as one welcome-card renderer; actually serves 5+ consumers + media
gen). Counter-example held correctly: the world-store (one consumer → stays a convention).

### 7. Missing cross-cutting standard — 🧠 human-probe
**Probe:** *Is this decision being made ad-hoc per subsystem when it should be one rule everyone
inherits?*
**Today:** command naming, invocation, authority — undecided, would have been re-litigated 43× until
we froze them as standards (Q-0224…Q-0227).

### 8. Verification hole — 🔧 checker (build)
**Probe:** *How do we prove this is correct? Is there an oracle?*
**Today:** the new-feature oracle — giveaways/media-gen have no old-bot golden to match; the whole
parity story has a hole for unbuilt capabilities.
**Mechanize:** assert every subsystem plan declares a **done-definition + oracle** (parity golden,
sim, or an explicit "new-feature oracle" method); flag any with none.

### 9. UX / lifecycle-contract gap — 🔧 checker (build)
**Probe:** *Does every state honor the standing contracts — navigation, timeout/restart, authority
re-check-at-callback?*
**Today:** Back/Home not guaranteed across re-renders; panels timing out; no restart-safety.
**Mechanize:** the navigation-completeness golden (walk every generated panel state, assert
Back+Home present; assert persistent/restart-safe) — see
[`../ideas/rebuild-navigation-completeness-check-2026-07-03.md`](../ideas/rebuild-navigation-completeness-check-2026-07-03.md).

### 10. Naming / visibility / collision risk — ⚙️ checker (exists, by construction)
**Probe:** *Could this name collide? Is this command invisible / undiscoverable?*
**Today:** the `give` and `dock`/`sail` collisions that crash-looped production; the invisible-command
worry.
**Mechanize:** the K1 namespace registry rejects collisions pre-boot **by construction**; "every
command projects into help" + a help-drift test kills the invisible-command class (Q-0224/Q-0231).

---

## Applying the rubric

- **Stage-2 subsystem walk:** for each of the 43 subsystems, run all ten probes and record the
  findings alongside its command surface / placement / triage verdict. A subsystem isn't "walked"
  until every probe has an answer (or an explicit "N/A + why").
- **Phase-B adversarial-completeness pass:** this rubric *is* the checklist the adversarial reviewer
  (the one whose only job is to find a gap) works from — it makes "find one open decision" concrete.
- **The bar:** a subsystem/plan passes when every class is either clean or has a labeled,
  owner-visible disposition. Silence on a class is not a pass.

## Mechanization roadmap (enforce, don't exhort — Q-0132/Q-0194)

| Class | State | Action |
|---|---|---|
| 4 stale claim | exists | **extend** `check_plan_staleness.py` with the un-anchored-`NN%` rule (cheapest, highest-proven — the class that misled twice) |
| 10 naming/collision | exists (rebuild) | K1 registry + help-drift test (already in the design) |
| 1 dep-order · 3 thin-step · 5 fragmentation · 8 verification-hole · 9 UX-contract | build | mechanizable against the **new repo's declared manifests** (deps/done-defs/nav are machine-readable there); build as the rebuild's own review checkers, not bolted onto the current bot |
| 2 forgotten-capability · 6 generalization · 7 missing-standard | human | stay judgment probes; the rubric *is* their enforcement |

*Scope note:* the "build" checkers land best in the **rebuild**, where dependencies, done-definitions
and navigation are declared data a checker can read — bolting them onto the current hand-written bot
would be low-signal. The one exception worth doing on the current repo now is the class-4 extension
(routed as an idea). Until each checker is proven, the **human probe is the guard** — that's why the
rubric ships first.

## Pointers

- The session's decision logs this rubric generalizes: [stage-1 global review](rebuild-stage1-global-review-2026-07-03.md) · [conventions](rebuild-conventions-invocation-authority-2026-07-03.md) · [hub/navigation](rebuild-hub-navigation-presets-2026-07-03.md)
- Standards the probes cite: S-1 generalization (Q-0219) · S-2 ordering (Q-0220) · naming (Q-0224) · authority (Q-0227) · nav contract (Q-0231)
- Owner ruling: **Q-0233** in [`../owner/maintainer-question-router.md`](../owner/maintainer-question-router.md)
- Session log: `.sessions/2026-07-03-critical-review-rubric.md` (PR #1685)
