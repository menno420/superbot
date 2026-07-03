# Rebuild verification review — parity, benchmarks, live sign-off, and CI gates (2026-07-03)

> **Status:** `review` — Codex verification review of whether the rebuild planning now has a
> strong enough proving story before Phase B. This is a findings document, not approval to build.
> **Scope:** parity goldens, competitor benchmarks, live co-tests, generated checkers, owner
> sign-off, command/cutover integration, and CI gates across the 43-subsystem rebuild plan.
> **Prepared:** 2026-07-03.
>
> **Required inputs read:** frozen capstone `FINAL-REVIEW.md` + `NEW-BOT-BUILD-PLAN.md`; Phase-A
> planning docs; Stage-1 global review; the ten-class critical-review rubric; hub/navigation/preset
> decisions; runtime-logic mechanics; Prompt-B presentation/proving report; `parity/`,
> `tools/grammar_spike/`, and relevant scripts/tests. Source wins over this review (Q-0120).

---

## 1. Verification maturity verdict

**Verdict: promising, but not yet Phase-B-ready.** The current planning set has the right *shape*
for a strong verification strategy, but it is still unevenly specified. Ported behavior has a
credible parity-golden oracle; new behavior has a named oracle concept, but the
"competitor benchmark + live co-test" half is not yet concrete enough to scale across 43
subsystems without drift, hand-waving, or inconsistent human judgment.

### What is strong

- **Ported-feature oracle is real and unusually strong.** The `parity/` harness is black-box:
  command input flows through the real bot/cogs/dispatch/DB and captures embeds/components/DB
  deltas/events as goldens. The harness states that the current bot is the oracle and that the
  rebuild is red until parity.
- **Golden integrity is designed correctly.** Goldens live in the current repo as a pinned external
  dependency for the new repo; changes require reviewed PRs with explanations, preventing the
  rebuilt bot from rewriting its own oracle.
- **Coverage is measured, not aspirational.** The golden corpus reports 465 cases, with strong
  command/component breadth: 96% prefix commands, 88% slash commands, and 94% persistent-panel
  components, plus an explicit uncovered tail.
- **The critical-review rubric now recognizes verification as a first-class gap class.** It splits
  oracles into ported-feature parity goldens and new-feature competitor benchmark + live co-test,
  and calls for a checker that rejects subsystem plans with no oracle.
- **UX/lifecycle verification is identified as mechanizable.** The rubric calls for a
  navigation-completeness golden that walks every generated panel state and asserts Back/Home plus
  persistence/restart-safety.

### What is not yet strong enough

- **New-feature verification is still too human/vague.** "Works · logical · self-explanatory to
  use" is a useful live acceptance lens, but it is not sufficient as the primary oracle for
  giveaways, starboard, media generation, generated help, or new navigation behavior unless each
  subsystem also declares machine-checkable behaviors, fixtures, and pass/fail thresholds.
- **Prompt B directly contradicts any conclusion that the proving layer is solved.** It calls the
  foundation "engine-rich, grammar-thin, oracle-empty" and names missing oracles for Back/Home,
  preset preview fidelity, result matrices, media cost/abuse posture, one-edit-propagates help
  descriptions, and manifest completeness.
- **Restart-safe navigation is a blocker, not a detail.** Prompt B says the decided
  "Back = pop the real path" contract lacks a serializable storage medium, so redeploys collapse
  the actual path back to semantic-parent behavior.
- **Phase B should not start until Phase A's surface decisions are captured.** The phase doc already
  gates Phase B on Phase A completion because per-step plans cannot be complete against an
  undecided command/method/hub/outperform surface.

---

## 2. Existing proof assets worth preserving

### 2.1 `parity/` golden behavioral harness

This is the central proof asset to preserve and port as the rebuild's parity gate.

- It captures **command in → embeds/components/DB delta/events out** by driving the real current bot
  in-process, with real cogs, converters, cooldowns, governance gates, error handling, and Postgres.
- It documents capture/check commands and expects a future `golden-parity` gate in the new repo once
  a Postgres-serviced workflow exists.
- It has a detailed determinism model: logical clock, seeded RNG, singleton reset, DB truncation,
  symbolic ID normalization, and volatility scrubbing.
- It honestly documents deliberate deviations — no gateway/network, no task-loop ticks, view
  timeouts neutralized, env integrations degraded — which is essential for deciding what needs a
  separate oracle.

**Preserve as:** Phase-C mandatory CI gate for ported commands/panels/DB effects, plus a
**golden-recapture protocol** whenever current-bot behavior changes before rebuild capture freezes.

### 2.2 `parity/COVERAGE.md` breadth accounting

This is valuable because it prevents "we have goldens" from becoming a vague claim.

- It reports concrete coverage by surface type and names the uncovered command/component/event/table
  tails.
- It distinguishes breadth from depth: one invocation per command is not enough for rich
  flag/subpath behavior, so per-subsystem coverage notes are still required.

**Preserve as:** a required coverage report in the new repo, expanded to depth metrics per
subsystem.

### 2.3 Grammar-spike measurement pattern

The grammar spike is useful not because it proves behavior correct, but because it is a precedent for
**measured declarative fit**.

- `tools/grammar_spike/RESULTS.md` reports measured tier-1/2 fit across blackjack, karma, and
  logging, including unit-level rationale.
- The unit ledger records what remains tier-3 and why, preventing unexplained escape hatches.

**Preserve as:** a "manifest fit before code" pattern for new features, especially giveaways, media
creation, and starboard where no old-bot parity exists.

### 2.4 Static surface and architecture checkers

Useful current-repo proof patterns worth porting:

- `scripts/command_surface_dump.py` reads cog source via AST and emits every prefix/slash/group
  command by subsystem without Discord or DB.
- `scripts/check_architecture.py` provides a static seam-checking pattern, especially for raw SQL /
  pool primitive detection outside the approved DB seam.
- The AI eval harness has a useful split between CI-runnable fake-provider smoke tests and opt-in
  paid/live provider runs.

**Preserve as:** rebuild-native generated checkers: command-manifest/help completeness, StoreSpec
sole-writer fences, static authority/DB/import fences, and fake-provider/live-provider oracle split.

---

## 3. Missing oracle/checker classes

These should be added to the Phase-B plan template and, where possible, required before Phase-C
implementation.

### 3.1 Per-subsystem oracle manifest checker

A machine-readable rule should require every subsystem to have one or more oracle rows:

| Feature type | Required oracle |
|---|---|
| `ported` | parity golden case IDs + coverage/depth target |
| `new` | competitor benchmark spec + generated/fake-provider/offline oracle where possible + live co-test |
| `hybrid` | old parity coverage + explicit new-delta checker |

The critical-review rubric proposes this checker at a high level, but it needs to become a concrete
required artifact before Phase-B plans proceed.

### 3.2 Competitor-benchmark specificity checker

Competitor rows are often still prose. The Phase-A agenda correctly says outperform targets must
become a **specific feature list**, not just competitor names. A checker should require each
benchmark row to include:

- named competitor / product;
- evidence date;
- exact user-visible behavior to match, exceed, or intentionally differ from;
- evidence kind: docs, live observation, screenshot/video, or owner judgment;
- pass/fail acceptance conditions;
- whether the requirement is `match`, `exceed`, or `deliberate-difference`.

### 3.3 Live co-test / `verified_live` protocol checker

`verified_live` is a good concept, but it needs schema, storage, and cutover semantics. A live
sign-off should not be just a checkbox. Require fields such as:

- command/panel/custom_id under test;
- test guild/channel/persona;
- scenario steps;
- expected visible result;
- expected DB/audit/event effects;
- owner/operator signer;
- timestamp + build SHA/container image;
- evidence link or transcript;
- rollback/cutover status.

### 3.4 Navigation/restart oracle

The docs identify the need, but Prompt B says the current Back-path persistence model is unsolved.
Required checker classes:

- generated panel graph has Back and Home on every state;
- direct-entry panels have semantic parent fallback;
- multi-hop path survives in-place rerender;
- restart/redeploy preserves the actual path if the contract says "actual path," or the contract is
  rewritten to semantic-parent-only after restart;
- hidden/disabled/permission-lost targets fail closed and rehome predictably.

### 3.5 Authority re-check matrix

The hub/navigation doc correctly requires authority re-check at click time, not only panel open.
Missing checker:

- open authorized → revoke permission → click admin/mod action → denied;
- open unauthorized locked node → grant permission → click/open succeeds if policy allows;
- hidden vs locked vs disabled nodes each have distinct expected output;
- denial renders through the same result grammar as normal errors.

### 3.6 Generated-help projection checker

The rubric names "every command projects into help" and a help-drift test as the answer to invisible
commands. Missing checker:

- every `CommandSpec` has generated help text;
- every alias/rename/drop disposition appears in help/migration docs as intended;
- every hub node is reachable from root unless explicitly hidden by preset/config;
- editing one description source updates slash help, prefix help, hub card, and docs projection.

### 3.7 Preset preview-fidelity checker

The hub doc says preview is the real generated hub. Missing checker:

- preset preview render equals actual post-apply hub render for the same manifest/config;
- safe default always exists;
- pick preset → edit → manual path is always available;
- hidden-vs-disabled semantics match the owner decision.

### 3.8 Restart-safe persistent-panel CI oracle

Runtime mechanics recommends making restart contracts a CI oracle that walks registered view classes
and asserts arg-free instantiation plus static unique custom IDs. This should block Phase C for the
panel framework.

### 3.9 Event/outbox/delivery oracle

Runtime mechanics identifies post-commit events as best-effort in-memory and recommends a
transactional outbox + idempotency key for crash-drop/double-fire gaps. Missing checker:

- DB transaction commits exactly one outbox record;
- worker dispatches at least once;
- idempotency prevents double side effects;
- audit/event correlation ID survives retries.

### 3.10 Clock/RNG fence

Runtime mechanics says direct `datetime.now`, `time.time`, and `random.*` calls are widespread and
recommends kernel clock/RNG plus an AST fence. This should be required before deterministic goldens
can reliably cover games, cooldowns, timers, generated media cost gates, and live co-test replay.

---

## 4. Weak or vague acceptance criteria that need rewriting

### 4.1 "Competitor benchmark + live co-test"

Current form: good direction, insufficiently operational.

Rewrite to:

> For each new feature, declare a benchmark table with competitor, evidence date, exact behavior,
> expected SuperBot behavior, measurable pass/fail check, and live co-test scenario. A feature is not
> complete until its benchmark rows pass either an automated/fake-provider checker or a recorded
> `verified_live` run tied to a build SHA.

### 4.2 "Works · logical · self-explanatory to use"

Current form: useful but too subjective.

Rewrite to:

> Live co-test must include one first-time-user task, one happy path, one denial/error path, and one
> restart/retry path. "Self-explanatory" passes only if the tester completes the task without
> out-of-band instructions and records no more than N confusion notes, with all notes dispositioned
> before cutover.

### 4.3 "Back + Home on every state"

Rewrite to:

> For every generated panel state, the navigation golden opens the state by command and by click path,
> asserts Back and Home controls are present, exercises Back through N-depth stacks, restarts the
> process, repeats the click, and asserts either actual-stack restoration or explicitly documented
> semantic-parent fallback.

### 4.4 "Panels are persistent and restart-safe"

Rewrite to:

> A panel is restart-safe only if a test renders it, captures message/custom_id/state identity,
> restarts the bot process with no in-memory view instance, re-registers from durable state, clicks
> every component, and verifies render is derived from manifest + DB, not TTL session state.

### 4.5 "Every command projects into help"

Rewrite to:

> CI fails if any `CommandSpec`, alias, hub node, or generated panel action lacks help projection; if
> any help projection points to a non-existent command/node; or if any hidden/disabled command lacks
> explicit visibility reason.

### 4.6 "Owner sign-off"

Rewrite to:

> Owner sign-off must be tied to a signed checklist row with build SHA, test guild, scenario ID,
> evidence link/transcript, known deviations, and cutover eligibility. The checker fails if a command
> marked cutover-ready lacks current sign-off.

---

## 5. Suggested per-subsystem done-definition format

Use this structure for each subsystem plan.

```md
## Done definition — <subsystem>

### 1. Surface manifest
- Commands:
  - keep/rename/drop disposition for every legacy command.
  - slash/prefix kind.
  - aliases.
  - namespace collision status.
- Panels/components:
  - panel IDs.
  - custom_id families.
  - Back/Home parent.
  - persistent/restart-safe class.
- Events/stores/settings/help:
  - EventSpec rows.
  - StoreSpec ownership.
  - SettingSpec rows.
  - generated help projection rows.

### 2. Feature classification
| Feature | Type | Oracle |
|---|---|---|
| legacy command/panel/store behavior | ported | parity golden IDs |
| changed behavior | hybrid | old parity + new delta checker |
| new feature | new | competitor benchmark + offline/live oracle |

### 3. Correctness oracles
- Parity goldens:
  - case IDs;
  - required pass threshold;
  - known deviations.
- Generated/static checkers:
  - manifest completeness;
  - namespace/help drift;
  - authority re-check;
  - restart-safety;
  - DB/event/audit invariants.
- Property/race tests:
  - idempotency;
  - settle-once;
  - cooldown scope;
  - no overdraw/no double grant.
- Live co-tests:
  - scenario IDs;
  - required persona;
  - expected visible output;
  - expected DB/audit/event output;
  - `verified_live` sign-off row.

### 4. Competitor benchmark
| Competitor | Evidence date | Behavior | SuperBot target | Checker/sign-off |
|---|---:|---|---|---|

### 5. UX/lifecycle matrix
| Scenario | Required? | Oracle |
|---|---:|---|
| direct command open | yes/no | generated panel test |
| click navigation | yes/no | nav golden |
| Back/Home | yes/no | nav golden |
| timeout/restart | yes/no | restart sim |
| permission revoked after open | yes/no | authority matrix |
| hidden/disabled by preset | yes/no | preset matrix |
| error/denial/refusal | yes/no | result grammar golden |

### 6. Cutover gate
- All CI checkers green.
- Required parity coverage met.
- Required benchmark rows passed.
- Required live co-tests signed.
- No unresolved owner-gated decisions.
- Rollback/disable path declared.
```

---

## 6. Critical blockers before Phase B

1. **Phase A is not done.** Stage 2 still needs to walk all subsystems for exact command surface,
   invocation kind, naming, method conventions, hub placement, triage, and concrete outperform
   targets.
2. **New-feature oracle schema is not concrete enough.** Q-0234 resolves the conceptual split, but
   not the required schema. Without a schema, 43 subsystem plans will interpret "competitor benchmark
   + live co-test" differently.
3. **Restart-safe Back-path storage decision is unresolved.** Prompt B identifies this as the most
   foundational presentation/proving defect. Resolve it before freezing `NavigationSpec` or
   `PanelSpec`.
4. **Hide-vs-disable contract collision is unresolved.** The hub doc leaves it open, and Prompt B
   says the recommended "hidden = off" default conflicts with the shipped display-hide invariant.
5. **`verified_live` is not yet integrated with command manifests and cutover records.** It needs a
   record shape, evidence requirements, and CI/cutover enforcement.
6. **CI-gate inventory is not yet explicit.** The rubric has a mechanization roadmap, but several
   checkers are still only "build" and not yet represented as mandatory Phase-B deliverables.
7. **Prompt B's "oracle-empty" findings need triage into the plan.** The 48 verification-hole and
   48 UX-contract-gap findings should be folded into Phase-A/Phase-B requirements, not left as a
   side report.

---

## 7. Lower-priority verification improvements

- **Expand parity depth metrics.** `parity/COVERAGE.md` correctly warns that coverage is breadth,
  not depth. Add depth rows per subsystem once Phase-B plans define scenario matrices.
- **Add generated coverage dashboards for oracle state.** Track parity cases required/passing,
  benchmark rows required/passing, live co-tests signed, generated checkers passing, and owner-gated
  decisions open/closed.
- **Preserve opt-in live provider patterns.** For media generation and AI features, copy the current
  eval split: fake-provider CI smoke first, opt-in live provider run second.
- **Add semantic dedup before future verification-fleet synthesis.** Prompt-B follow-up notes that
  the multi-agent audit found near-duplicate mechanics; a consolidation pass would reduce duplicate
  verification gaps before Gate-V synthesis.
- **Port current-repo static tools as generated rebuild checkers.** Do not copy every old checker
  literally; port the patterns: command-surface enumeration, architecture seam checks, eval smoke/live
  split, and parity coverage accounting.

---

## 8. Direct answers to the review questions

### Are ported features and new features both covered by clear correctness oracles?

**Ported features: yes, mostly.** The `parity/` harness is a clear oracle with measured coverage and
strong integrity rules.

**New features: not yet.** The plan has the right conceptual split — competitor benchmark + live
co-test — but lacks a strict schema, artifact format, and CI/cutover enforcement.

### Is "competitor benchmark + live co-test" specific enough to be actionable per subsystem?

**No.** The Phase-A agenda correctly says competitor names must become concrete feature lists, but
that is still future work.

### Is the `verified_live` idea well integrated with cutover and command manifests?

**Not yet.** It is mentioned as the live co-test hook, but the reviewed docs do not yet define the
manifest fields, sign-off records, CI enforcement, or cutover status transitions.

### Are Back/Home, restart-safety, authority re-checks, persistent panels, and generated help projection all testable?

**They are testable in principle, but not all testable as currently specified.** Back/Home and
restart-safety need the unresolved serializable Back-path decision. Authority re-check is specified
as a contract and should be tested with a matrix. Persistent panels have a clear target and need a
restart simulation. Generated help projection is identified as a drift/collision solution but still
needs the actual checker.

### Are there missing checkers that should block Phase B or Phase C?

**Yes.**

Block Phase B until required checker/oracle *specs* exist:

- per-subsystem oracle manifest checker;
- benchmark/live co-test schema;
- navigation/restart oracle spec;
- help projection completeness spec;
- authority re-check matrix spec.

Block Phase C implementation/cutover until checker *implementations* exist:

- golden parity gate;
- manifest completeness/help drift;
- namespace collision;
- persistent panel restart sim;
- StoreSpec sole-writer/import fence;
- event/outbox idempotency;
- clock/RNG AST fence.

### Are any verification requirements too human/vague to scale across 43 subsystems?

**Yes.** Most risky: "self-explanatory" without a first-time-user task protocol, "competitor
benchmark" without named behavior rows, "owner sign-off" without build SHA/evidence/scenario IDs,
"restart-safe" without a process-restart simulation, and "Back works" without specifying
actual-stack-vs-semantic-parent after restart.

### Where does the current repo already have useful tests/checkers that should be ported?

Most valuable:

- `parity/` goldens and coverage accounting;
- `tools/grammar_spike/` measured manifest-fit methodology;
- `scripts/command_surface_dump.py` AST command inventory;
- `scripts/check_architecture.py` static architecture/seam checking pattern;
- `scripts/run_evals.py` fake-provider CI plus opt-in live-provider split.
