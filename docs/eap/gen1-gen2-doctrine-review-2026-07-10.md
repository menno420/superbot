# Gen-1 → Gen-2 doctrine review — fleet-manager vs superbot

> **Status:** `audit` — independent external doctrine comparison. Every claim is
> quoted from the repos at HEAD (superbot `77b76de`, fleet-manager `8e08cd0`);
> unverifiable claims are marked UNVERIFIED. Not a source of truth for either
> repo — the source files win.
>
> **Method:** four questions (contradictions, regressions, duplication,
> portability) were each analysed independently, every quoted line was
> adversarially re-checked against the file with `grep`, and a final
> completeness pass audited the set for misses and overreach. Two plausible-
> sounding criticisms were checked and **rejected** (recorded below), which is
> the point of an independent review.

---

## Executive summary (plain language)

**The big picture: these are not two rival systems — they are one program at two
layers.** superbot is the battle-tested original (its `.claude/CLAUDE.md`
governance has ~1900 PRs behind it). fleet-manager is a brand-new (~11 PRs)
substrate-kit repo that *implements* the fleet coordination layer superbot
designed. fleet-manager's own file even says so: `control/README.md` calls
superbot's protocol doc the *"Canonical spec."* So most "gen-2 vs superbot"
tension is really *the same team evolving its own system*, and several
"divergences" are **deliberate and scoped** ("gen-1 carve-outs unaffected").
One caveat the review kept front-of-mind: superbot's *coordination-protocol*
doc is itself brand-new (dated 2026-07-09) — it does **not** carry the 1900-PR
maturity that superbot's *bot* doctrine does.

**The reassuring headline — gen-2 did NOT throw away the hard-won machinery.**
The natural fear ("the fresh repo dropped session cards / ledgers /
friction→guard / the idea lifecycle") is **mostly false at HEAD**, and I checked
each one against the actual enforcement:

- **Session cards** are present *and CI-enforced* — `substrate-gate.yml`:
  *"Holds the merge red until the session journal is written"* — and gen-2 even
  requires **one more** card marker (a Model line) than superbot does.
- **Friction→guard** is carried intact (the whole `playbook.md` R1–R21 *is* a
  friction→rule ledger; the collaboration model states the same
  checker→hook→rule ladder, *"Enforce, don't exhort"*).
- **The idea lifecycle** is present (a live `docs/ideas/` backlog, a grooming
  session-ender).
- **The reconciliation cadence** number survived (`reconciliation_prs: 30`).

**So where are the real problems?** Five things genuinely matter, and only one
is a "which side is right" disagreement:

1. **The ledger gate is hollow.** gen-2 copied superbot's reconciliation *number*
   but not the *checker* that makes it mean anything — and the `30` knob has zero
   code reading it. As the fleet accumulates merges, its institutional memory will
   rot silently. **(highest-value fix)**
2. **An owner-facing safety contradiction in the environment doc.** The one file
   the owner hand-pastes production secrets from contradicts itself about *where
   production Railway credentials are allowed*. **(highest-consequence defect)**
3. **The "single owner queue" isn't single and breaks its own format.** The doc
   that exists to be the owner's clean, one-stop action list already violates the
   five-field rule it mandates and hands its live truth to a *second* doc.
4. **A cheap, high-value back-port for superbot:** a capability manifest of
   platform "walls" with exact error text so agent sessions stop re-probing the
   same 403s.
5. **The merge-authority divergence is deliberate and correct** — not a safety
   regression. gen-2 makes "REST merge-on-green" the primary landing path and
   kills the pre-merge owner-gate *for product lanes*; superbot keeps a pre-merge
   gate. Both are right *in their scope*, and both still require green CI and
   forbid deferring the merge. This just needs one sentence of documentation so
   nobody reads it as gen-2 "going rogue."

**Two criticisms I rejected** (to show the review is not just pattern-matching):
(a) "superbot's own auto-merge is secretly failing to arm on its born-red PRs" —
**false**; superbot arms during the *pending* window at PR-open, which GitHub
allows, and the flow is battle-tested. (b) "fleet-manager owns a cite-don't-copy
rule but ignores it" — built on a quote that **does not exist** in superbot and a
category error (an operational format that agents must read locally is not a
"copied ruling body").

---

## Verdict table

| # | Finding | Q | Severity | Verified | Right side / disposition |
|---|---|---|---|---|---|
| C1 | REST merge-on-green primary vs never-hand-merge | 1 | med | CONFIRMED | gen-2 (fleet); convergent principle |
| C2 | do-not-automerge "dead in gen-2 lanes" vs superbot keeps it | 1 | med | CONFIRMED | both, scoped |
| C3 | Constitution bans inline provenance; superbot narrates it | 1 | low | CONFIRMED (no real conflict) | gen-2 doc-split |
| C4 | never-wait / silence=consent | 1 | low | CONFIRMED convergent | agree |
| C5 | Escalation routed to an inert (empty) router | 1 | low | CONFIRMED | weakening, not conflict |
| R1 | Per-PR ledger-completeness checker not carried | 2 | med | CONFIRMED | **weakened** |
| R2 | Q-0104 doc-audit ender has no gen-2 equivalent | 2 | low | CONFIRMED | weakened (structural half is CI-gated) |
| R3 | Program law non-resident (D/Q/R/PL split) | 2 | low | PLAUSIBLE (overreached) | defensible tradeoff, one real cost |
| R0 | TRAP-checks: session cards + friction→guard | 2 | — | CONFIRMED PRESENT | **not dropped** |
| D1 | status/inbox format block in ≥3 homes | 3 | med | PLAUSIBLE | single source = kit template |
| D2 | collaboration kernel in 4+ homes | 3 | med | PLAUSIBLE | single source = kit program doc |
| D3 | decide-and-flag/never-wait: two ID registers (Q vs PL) | 3 | low | PLAUSIBLE | canonical = PL register + crosswalk |
| D4 | one-writer-per-file restated 4× | 3 | low | PLAUSIBLE | R9 legit; collapse the prose copies |
| D0 | "program ignores its own cite-don't-copy rule" | 3 | — | **REFUTED** | rejected (fabricated quote) |
| B1 | Back-port capability manifest / walls-with-error-text | 4 | med | CONFIRMED | **[backport]** |
| B2 | Back-port measured liveness mechanics | 4 | med | PLAUSIBLE | **[backport]** |
| B3 | Back-port R19/R20 protocol refinements | 4 | med | PLAUSIBLE | **[backport]** |
| B0 | "superbot's enabler silently fails to arm (port R21)" | 4 | — | **REFUTED** | rejected (no live bug) |
| F1 | Forward-port strict ledger checker + procedure | 4 | high | CONFIRMED | **[fix in gen-2]** |
| F2 | Forward-port Q-0104 doc-audit ender | 4 | low | PLAUSIBLE | **[fix in gen-2]** (as a prompt, not a marker) |
| F3 | Forward-port CI-parity code-lane addendum | 4 | med | PLAUSIBLE | **[fix in gen-2]** |
| F4 | Forward-port Q-0210 router invariants | 4 | low | PLAUSIBLE | **[accept divergence]** (already ~present) |
| F5 | Forward-port the "why this system exists" framing | 4 | med | PLAUSIBLE | **[fix in gen-2]** (verify program doc) |
| M1 | archetypes.md self-contradiction on prod secrets | + | high | CONFIRMED | **internal defect** |
| M2 | owner-queue violates its own R17 format | + | med | CONFIRMED | internal defect |
| M3 | "one queue" not deduplicated; delegates to a 2nd doc | + | med | CONFIRMED | internal defect |
| M4 | review-queue.md is an uncounted 5th register | + | low | CONFIRMED | internal defect |
| M5 | environment click-path triplicated | + | med | CONFIRMED | internal defect |
| M6 | gen2-blueprint marked `binding` embeds live PR state | + | low | CONFIRMED | internal defect |

(`+` = surfaced by the completeness pass, outside the four framed questions but within the review's remit.)

---

## Question 1 — Contradictions

### C1 · Merge mechanism: "REST merge-on-green primary" vs "never merge by hand" — **MED, gen-2 right for a fleet**
- **fleet** `docs/playbook.md`: *"REST merge-on-green is the PRIMARY landing path on born-red"* (R21).
- **superbot** `.claude/CLAUDE.md`: *"You don't merge your session PR by hand — GitHub-native auto-merge does"* (hand-merge is *"a carve-out, or auto-merge is down"*).
- **Verdict:** Not an accidental contradiction — a repo-shape-keyed generalization. superbot's "never hand-merge" is correct *for superbot*, where a dedicated `auto-merge-enabler` workflow reliably arms native auto-merge on every `claude/*` PR. A fleet spans repo shapes where GitHub **structurally refuses** to arm auto-merge — born-red repos (*"unstable status"*) and PR-required-but-no-CI repos (*"only applies when checks are pending"*); R21 records fleet PR #10 burning 3 failed arm attempts. On those shapes REST-merge is the *only* working path. Crucially both sides converge on the invariant superbot actually cares about: **land the instant CI is green, never defer the merge** (superbot's #778 lesson). Right side: **gen-2** for the fleet; superbot's rule stays right for superbot.

### C2 · Human-review gate: "owner-gated merges dead in gen-2 lanes" vs superbot's live do-not-automerge — **MED, both right in scope**
- **fleet** `docs/gen2-blueprint.md`: *"No gen-2 lane is owner-gated on [merges]"* / *"no PR ever waits for review before landing … review is post-merge; veto = revert."*
- **superbot** `.claude/CLAUDE.md`: *"The one remaining carve-out stays manual — a PR labelled `do-not-automerge` (Q-0114) is never auto-armed."*
- **Verdict:** A **deliberately scoped** divergence, and the fleet proves the gate is not actually dead: the blueprint says *"(gen-1 carve-outs unaffected)"*, and the live infrastructure lanes still use do-not-automerge exactly where a revert would be unsafe — `owner-queue.md` marks kit PRs #26/#49 *"do-not-automerge by design"* (program-law ratification / the lab must never merge its own correctness oracle), and the coordination protocol tells the manager *"Never merge another Project's owner-blessed PR."* So the real fleet policy is: **post-merge review by default; a hard pre-merge gate only where merge == irreversible ratification.** That is arguably *better* factoring than superbot's per-PR label, because gen-2 also moves irreversible-*action* gating off the merge entirely (venture-lab's HARD RAILS: *"NO spend, NO publishing … without an owner action — every such step is queued click-level, never performed"*). The one thing worth stating explicitly: post-merge-review assumes **cheap forward-only revert**, which is true for product code and false for a production bot with a database — which is exactly why the blueprint excludes the bot. Right side: **both**, in their scopes; document the cheap-revert precondition.

### C3 · Provenance narration — **LOW, no real conflict**
- **fleet** `CONSTITUTION.md`: rules state current value only; provenance *"is never narrated inline."*
- **superbot** `.claude/CLAUDE.md`: dense inline provenance, e.g. *"(owner directive Q-0129, 2026-06-14)"*.
- **Verdict:** Dissolves on document role. The constitution's no-inline rule is *self-scoped* (*"This file carries no history — the ledger does"*), and fleet-manager's own `playbook.md` (a *"living-ledger"*) keeps *"the WHY that earned it"* inline — because the playbook *is* the ledger. gen-2's thin-constitution + friction-ledger split is a direct, sensible correction of superbot's real anti-pattern: a `CLAUDE.md` bloated toward unreadability by inline Q-number provenance in nearly every bullet. (Minor factual correction from verification: the playbook narrates WHY + bare dates, not literal "owner directive" strings.)

### C4 · never-wait / silence = consent — **LOW, convergent (not a contradiction)**
- **fleet** `gen1-winddown-universal.md`: *"decide-and-flag, never wait."*
- **superbot** `agent-decision-authority.md`: *"Silence = consent = done. Never wait for the owner."*
- **Verdict:** The two **agree**. The only delta is scope: superbot confines never-wait to *"the rebuild program"* and keeps a live-bot ask-first brake; gen-2 makes it the fleet default — correct for a fleet of unattended self-poll lanes, and gen-2 retains the same class of brake (*"Silence = consent for reversible dispatches"*).

### C5 · Escalation routed to an inert router — **LOW, a weakening not a conflict**
- **fleet** `CONSTITUTION.md`: *"Record the question in `docs/question-router.md` instead of skipping it or guessing."*
- **superbot** `.claude/CLAUDE.md`: *"Consult or add to `docs/owner/maintainer-question-router.md` when product/owner intent is genuinely unclear."*
- **Verdict:** The constitution points agents at `question-router.md`, but that file is template-only (zero real Q-blocks) while the live escalation surface is `owner-queue.md`. The three-way split (router = intent-ambiguity, owner-queue = owner actions, decisions = resolved provenance) is defensible, but right now the router the constitution names is a doc no session actually uses — a young-repo operational gap to close, not an opposite instruction.

---

## Question 2 — Regressions

**First, the trap-checks (all confirmed PRESENT, not dropped):**

- **Session cards — present and enforced, equal-plus.** `.github/workflows/substrate-gate.yml`: *"Holds the merge red until the session journal is written."* `.sessions/README.md` carries the born-red ritual verbatim (*"the session's FIRST commit with a born-red status … flip it to `complete` as the deliberate LAST step"*), and gen-2's marker set is a **superset** of superbot's (adds a Model line). A "dropped session cards" claim is **false**.
- **friction→guard — carried intact.** `collaboration-model.md`: friction is *"converted into the **cheapest enforcing prevention**"* → checker/CI/test → hook → rule, *"Enforce, don't exhort"*; the whole R1–R21 playbook is a live instance; `PL-007` is the program-law citation.

**The genuine weakenings:**

### R1 · Per-PR ledger-completeness checker not carried — **MED, weakened**
- **superbot** `scripts/check_current_state_ledger.py`: *"Ledger drift guard — flag merged PRs absent from `current-state.md`."* (wired into `/session-close --strict`).
- **fleet** `docs/current-state.md` "Recently shipped" is the bare template: *"(Merged work only, newest first.)"*
- **Verdict:** The kit inherits the reconciliation *cadence* and a decision-ledger *grammar* checker, but **no** check that cross-references the living ledger against git merge history. Verified against `bootstrap.py`: `check_ledger` validates D-NNNN grammar only. This is the exact drift class superbot built its guard to catch — discounted for newness (an 11-PR repo has little to lose yet), but real as merge volume grows.

### R2 · Q-0104 documentation-audit session-ender — **LOW, weakened**
- **superbot** `.claude/CLAUDE.md`: the mandatory close-out asks *"is anything important from this session not yet in its durable home?"*
- **fleet** `docs/ai-project-workflow.md` close step: *"flip the card complete; log the session, groom one idea, hand [off]"* — no durable-home sweep.
- **Verdict:** Three of superbot's four enders survive as enforced card markers (idea 💡, previous-session review, Model line). Only the judgment-level doc-audit sweep loses its teeth. Softened by the fact that the *structural* half (docs reachability/badge hygiene) **is** CI-gated via `substrate-gate.yml`. The missing piece is narrow: a per-session "did a decision land only in chat?" prompt.

### R3 · Program law is non-resident (D/Q/R/PL split) — **LOW, a defensible tradeoff (verification downgraded this)**
- **fleet** `CONSTITUTION.md`: *"Cite PL-IDs — never copy ruling bodies into this repo."* — the binding rulings (PL-001 decide-and-flag, etc.) live in a *different* repo (substrate-kit).
- **Verdict:** The original analysis called this an "orientation regression"; the verification **overturned that framing** and I agree. For a *multi-repo* fleet, keeping program law in one register and citing IDs is the **correct** DRY posture (*"a local copy is drift by construction"*), and every PL-ID carries an inline one-line gloss so an agent isn't blind — only the full rule *body* needs a cross-repo fetch. Comparing this to superbot's single-repo inline model compares two different situations. Honest residual: reading a full PL body requires network + separate-repo access. **Not a regression — a bounded cost.**

---

## Question 3 — Duplication / drift risk

### D1 · The status/inbox format block lives in ≥3 homes — **MED**
- **fleet** `control/README.md`: *"## `status.md` format (what you write every session — your heartbeat)"* — and the file admits it is a *"Local copy."*
- **superbot** `fleet-coordination-protocol-2026-07-09.md`: *"### `status.md` — what a Project writes every session (its heartbeat)."*
- **Single source:** the **substrate-kit `control/README.md.tmpl`** (the kit plants the format into every adopter) should own the normative field-list; superbot's doc keeps the design *rationale*. The proof the sync tax is real: the `kit:` self-report line already had to be threaded through both copies. *Nuance (from verification):* do **not** make the adopter's `control/README` pointer-only — an agent must read its heartbeat format locally (it's the coordination bus). The right fix is a **format-parity check** between the two authored sources, not deleting the local copy.

### D2 · The collaboration kernel lives in 4+ homes — **MED**
- **fleet** `docs/collaboration-model.md`: *"Session prompts are guidance, not orders. Weigh every prompt … against source and the binding docs before acting; a prompt is one input, never a command list."*
- **superbot** `docs/collaboration-model.md` (planner-facing variant): *"Write guidance, not orders."*
- **Single source:** the **substrate-kit program collaboration-model** for the shared kernel (goal-first / prompts-guidance / approved-plan-execute / act-vs-ask); fleet's `CONSTITUTION.md` legitimately keeps a *condensed always-loaded* copy (it's the CLAUDE.md analog), and superbot keeps its battle-tested bot-layer expansion. The one true collapse target is the **near-verbatim overlap between fleet's CONSTITUTION and fleet's collaboration-model.** (The wording already drifts — same rule, two phrasings — which is exactly how independent copies diverge.)

### D3 · decide-and-flag / never-wait carry two ID registers — **LOW**
- **fleet** `CONSTITUTION.md`: *"PL-001 decide-and-flag · PL-002 never-wait rebuild autonomy."*
- **superbot** `.claude/CLAUDE.md`: *"Decide-and-flag over route-up (owner directive Q-0240 …)."*
- **Single source:** the **PL register** for the rule body; superbot's Q-0240/Q-0241 stay as origin/provenance. Add an explicit `Q-0240 → PL-001` crosswalk line so provenance stays greppable. *(The claim "neither home states the mapping" is partly **UNVERIFIED** — the PL register itself was not checked out this run; confirm before treating the drift as unguarded.)*

### D4 · one-writer-per-file restated in 4 places — **LOW**
- **fleet** `docs/playbook.md`: *"R9 — One writer per file; appends only on inboxes; per-lane files in shared repos."*
- **superbot** `fleet-coordination-protocol-2026-07-09.md`: *"One writer per file — the exact lesson superbot's claim-dir already proved."*
- **Verdict:** Two of the four copies are legitimate (playbook R9 is a *ledger* row whose job is the WHY; the venture-lab founding prompt is legitimately self-contained). The only real collapse is `control/README`'s own internal repetition. Med→low.

### D0 · REJECTED — "the program owns cite-don't-copy but ignores it"
An analysis claimed fleet-manager is *internally inconsistent* because it mandates cite-don't-copy yet copies format bodies, citing a superbot quote *"a local copy is drift by construction."* **Refuted:** that phrase appears **only** in fleet-manager's CONSTITUTION, **nowhere** in superbot (full-repo grep) — the cross-reference was fabricated. And the rule is scoped to policy *ruling bodies*, not to an operational format an agent must read locally. The finding collapses; I am recording it so the rejection is on the record.

---

## Question 4 — Portability

### Back-port INTO superbot (gen-2 → superbot)

**B1 · Capability manifest of platform walls with exact error text — MED — [backport to superbot]**
- **fleet** `docs/gen2-blueprint.md`: seed a `docs/capabilities.md` of *"walls with exact error text ('probing a documented wall twice is a bug')."*
- superbot's capability docs cover the **bot's** runtime authority, not the **agent session's** platform walls (tag-push 403, branch-delete 403, claude.ai UI = owner-only) — it only has an *idea* file, no shipped manifest. Cheap, zero runtime risk, stops sessions re-probing known 403s. **Land it in superbot's agent-workflow layer.**

**B2 · Measured liveness mechanics — MED — [backport to superbot]**
- **fleet** `docs/gen2-blueprint.md`: *"Walking skeleton through the FULL merge path in the first 20 minutes — branch → PR → CI → merge proven before real work"*, plus a spawn watchdog and a **measured** order-pickup SLA (§2a: 9m47s/14m43s pickup; 7/9 lanes never acked).
- *Narrowed by verification:* superbot already has a first-commit heartbeat (the born-red card) and its coordination doc already carries a status heartbeat/staleness contract. The genuinely-absent, worth-porting pieces are the **20-min walking skeleton**, the **5–10 min spawn-liveness respawn watchdog**, and the **measured SLA** — and the right home is superbot's *fleet-coordination-protocol* doc, not the bot-session CLAUDE.md.

**B3 · R19/R20 protocol refinements — MED — [backport to superbot]**
- **fleet** `docs/playbook.md`: R20 *"unacknowledged by close-out = re-dispatch it as a fresh order"* + R19 serialize-same-inbox-appends.
- superbot's canonical spec has the one-writer invariant and a base acked/done model, but not these two same-day-learned hardening guards (the ORDER-number append race; an out-of-band PR-comment scope addition evaporating unacked). The field out-learned the spec within a day — port the specific guards back to where `control/README` points.

**B0 · REJECTED — "back-port R21 because superbot's enabler is silently failing to arm"**
The claim was that superbot is born-red (session gate) and its `auto-merge-enabler` *"may be silently failing to arm."* **Refuted:** superbot's enabler fires on `opened`, when Code Quality is **pending** (not failed), and GitHub **allows** arming while a required check is pending — R21's "refuses the arm" case is about a *failed* check. The flow is battle-tested across ~1900 PRs. This also inverted the maturity ordering (crediting one 3-attempt fleet PR over the mature system). No live bug. (Residual, low: superbot *could* record the R21 taxonomy as documentation — optional.)

### Forward-port INTO the gen-2 blueprint / substrate-kit (superbot → gen-2)

**F1 · Strict every-merged-PR ledger checker + reconcile procedure — HIGH — [fix in gen-2]**
- **fleet** `substrate.config.json`: *"reconciliation_prs": 30* — but verification found this knob has **zero consumers in `bootstrap.py`** (only a session-count staleness trigger actually runs), and `current-state.md` is the empty template.
- **superbot** `.claude/CLAUDE.md`: *"`scripts/check_current_state_ledger.py --strict` (every merged PR is in the living ledger)."*
- A cadence *number* with no checker and no procedure is a hollow gate. Forward-port into substrate-kit program: (a) a ledger-parity checker wired into `substrate-gate`, (b) the reconcile procedure as a saved routine prompt, and (c) actually wire the dead `reconciliation_prs` knob. **This is the single strongest forward-port.**

**F2 · Q-0104 documentation-audit ender — LOW — [fix in gen-2]**
- **fleet** `substrate.config.json` session markers: Status / 💡 idea / *"previous-session review"* / Model — **no** doc-audit ender.
- Forward-port it as a **session-close trigger prompt** (not a 5th card marker — verification correctly noted a judgment sweep has no stampable token to grep).

**F3 · CI-parity code-lane addendum — MED — [fix in gen-2]**
- **fleet** `docs/gen2-blueprint.md`: seed checklist covers *"the required contexts name the actual CI job(s); no legacy contexts"* (check *naming*).
- **superbot** `.claude/CLAUDE.md`: *"Tool versions are pinned to identical values in three places."*
- *Narrowed:* interpreter pinning already exists at the environment-archetype layer; the missing, complementary piece is **development-time tool-version drift** protection (formatter/linter pinned in workflow + requirements-dev + pre-commit + a single true-CI-mirror command). Without it, gen-2 code lanes (venture-lab, superbot-next) will rediscover superbot's PR #338 trap.

**F4 · Q-0210 router invariants — LOW — [accept divergence, document why]**
- **superbot** `docs/owner/ai-project-workflow.md`: *"The router is the single canonical, append-only Q-block [ledger]."*
- Verification found the two anti-drift guarantees gen-2 "lacks" are **already present** (decisions.md: *"superseded, never deleted"*; question-router.md: *"Append only … never rewrite history"*; distinct D/Q/R/PL prefixes make every ref resolve to one home). The residual is only an **enforcement-strength** nit — no CI id-uniqueness/orphaned-ref checker. Accept the multi-register split; optionally add the checker.

**F5 · The "why this system exists" framing — MED — [fix in gen-2]**
- **superbot** `.claude/CLAUDE.md`: *"the real artifact is this workflow (docs, journal, hooks, tooling, router) that lets any agent work correctly with little steering."*
- **fleet** `docs/collaboration-model.md` is a thin *"Generated by substrate-kit … NOT SOURCE OF TRUTH"* rails summary with none of the self-improving-ecosystem premise, the two-part-memory model, or *"improving the docs … is first-class work."* This is the difference between a rules list and a doctrine — agents self-improve the substrate because superbot's doc tells them the system *is* the product. **Forward-port it into substrate-kit *program* law** so every adopter inherits the motive, not just the rails. *(UNVERIFIED: the substrate-kit program collaboration-model was not checked out — confirm it lacks the framing before porting.)*

---

## Bonus — internal-consistency defects in gen-2 (surfaced by the completeness pass)

These are within fleet-manager rather than cross-doctrine, but they are real and one is the highest-consequence item in the whole review.

- **M1 · The environment doc contradicts itself about where production secrets may live — HIGH, owner-facing.** `environments/archetypes.md` line 30: bot-prod is *"the only archetype allowed production-pointing vars."* Line 75: *"production trio excluded outside bot-prod/coordinator"* (**two** archetypes). Line 48: the coordinator row actually lists `RAILWAY_PROJECT_ID`, `RAILWAY_SERVICE_ID`, `RAILWAY_ENVIRONMENT_ID`. The owner **hand-pastes** secrets from this doc — a self-contradictory rule about live production Railway credentials is a genuine footgun. Fix the wording to "bot-prod **and** coordinator."
- **M2 · owner-queue breaks its own mandatory format — MED.** Header: *"Every item below must carry WHAT/WHERE/HOW/WHY/UNBLOCKS + proof it's owner-only (R17)"* — yet items 6, 7, 12, 13 carry only a subset.
- **M3 · The "one deduplicated queue" isn't single — MED.** Items 3/6/8 are restated, and item 16 delegates live truth to a *second* doc: *"work through merge-queue-2026-07-09.md … the doc is the current source of truth on their live state"* — reintroducing the scatter R16 exists to prevent.
- **M4 · An uncounted 5th register — LOW.** `review-queue.md` is a real post-merge append-only ledger the D/Q/R/PL register-count never counted.
- **M5 · The environment click-path is triplicated — MED.** The same "New environment → paste script" procedure lives in `gen2-blueprint.md` §3, `environments/archetypes.md`, and `owner-queue.md` items 1 & 14 — higher drift risk than the format duplication, because it changes as the UI changes.
- **M6 · A `binding` doc carrying perishable state — LOW.** `gen2-blueprint.md` is *"Status: `binding`"* yet §5 embeds *"PR #9 (mining retro) MERGED by the owner 19:02:46Z"* — dated live PR state that goes false the moment those PRs move.

---

## TOP 5 recommendations

1. **Give the reconciliation cadence real teeth.** — **[fix in gen-2]** (severity HIGH).
   Ship a ledger-parity checker (every merged PR present in `current-state.md`)
   wired into `substrate-gate`, add the reconcile procedure as a saved routine
   prompt, and wire the currently-dead `reconciliation_prs: 30` knob. gen-2 copied
   superbot's number but not the enforcement; without it the fleet's memory rots
   silently. (F1)

2. **Fix the environment doc's production-secrets contradiction.** — **[fix in
   gen-2]** (severity HIGH, highest owner consequence).
   `environments/archetypes.md` says bot-prod is "the only archetype allowed
   production-pointing vars" (line 30) but elsewhere allows bot-prod **and**
   coordinator (line 75) — and the coordinator row actually carries the Railway
   IDs. The owner pastes secrets from this file by hand; make the rule
   self-consistent. (M1)

3. **Make the owner queue actually single and self-consistent.** — **[fix in
   gen-2]** (severity MED-HIGH).
   Bring every item into the mandated WHAT/WHERE/HOW/WHY/UNBLOCKS + owner-only
   format, and fold the `merge-queue-2026-07-09.md` delegation back in so a second
   doc doesn't become the de-facto source of truth. The whole value of the
   owner interface rests on this doc being clean and singular. (M2 + M3)

4. **Back-port a capability manifest into superbot.** — **[backport to superbot]**
   (severity MED).
   Ship `docs/capabilities.md` in superbot's agent-workflow layer: the platform
   walls (tag-push / branch-delete 403s, claude.ai-UI-only actions) with **exact
   error text** and the "probing a documented wall twice is a bug" rule. Cheap,
   reversible, and it stops unattended sessions burning time re-probing 403s. (B1)

5. **Document the merge-authority divergence as deliberate — don't "fix" it.** —
   **[accept divergence, document why]** (reassurance).
   gen-2's "REST merge-on-green primary" + "post-merge review, veto = revert" +
   "do-not-automerge dead in gen-2 lanes" is a **correct, scoped** adaptation for a
   fleet, not a safety regression: born-red/no-CI repos physically can't arm native
   auto-merge, both sides still require green CI, and the irreversible cases
   (ratification, oracle PRs, the production bot, all spend/publish) remain gated
   by a *separate* mechanism. Add one sentence to the blueprint naming the
   **cheap-revert precondition** so no future agent reads it as gen-2 abandoning
   merge safety. (C1 + C2)

---

*Reviewer's note on method: 30 analysis/verification/audit passes; every quoted
line was `grep`-checked against the file at HEAD; two plausible criticisms
(B0, D0) were rejected on verification; three original severities were downgraded
when the adversarial pass showed the criticism overreached. Items marked
UNVERIFIED depend on the substrate-kit repo, which was not in scope this run —
paste it in and I will close those out.*
