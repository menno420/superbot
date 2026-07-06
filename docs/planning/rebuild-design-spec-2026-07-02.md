# SuperBot Rebuild — The Design Spec (Phase 2, owner-gate artifact)

> **Status:** `plan` · **⚠ SUPERSEDED-IN-PART (2026-07-06, canonical plan §9):** where this spec
> and the Gate-0 corpus differ, **the Gate-0 frozen grammar + the 14 foundational specs win** —
> specifically: §9.1's K9/K10 definitions (K9 = the strand-2 durability band per
> [`phase-b-l0-build-order.md`](../analysis/rebuild-discovery/foundations/gate-0/phase-b-l0-build-order.md);
> the old K9 `kernel/ai` is re-homed as **K10**, the old K10 loops as **layer V**), §9.2's port
> order (→ Sequence C), and §2's grammar (→
> [`frozen-l0-grammar.md`](../analysis/rebuild-discovery/foundations/gate-0/frozen-l0-grammar.md)).
> The consolidated arc + gates:
> [`rebuild-canonical-plan-2026-07-06.md`](rebuild-canonical-plan-2026-07-06.md). §10.2's
> ratification list remains the G1 sitting payload, as amended by that plan's F-3. The header's
> "amendments — now folded in" refers only to the six 07-02 spike amendments; the G-9…G-24 set
> lives in the Gate-0 registry (`rebuild-amendments.yml`).

> *(original status)* — **the Phase-2 rebuild design spec, awaiting the owner gate (strategy §3's
> "🔒 OWNER GATE — the big one").** Design only: this document changes no `disbot/` code and
> approves no new-repo code — the owner ratifies the design + the §5 backward-compat contract + the
> rebuild go/no-go before any Phase-3 work starts. Written as one picture. **Evidence base:**
> [`fresh-rebuild-strategy-2026-07-02.md`](fresh-rebuild-strategy-2026-07-02.md) (verified baseline
> + phase order), [`simulation-driven-design-2026-07-02.md`](simulation-driven-design-2026-07-02.md)
> (standing owner rule),
> [`codex-preserve-map-synthesis-2026-07-02.md`](../analysis/rebuild-discovery/codex-preserve-map-synthesis-2026-07-02.md)
> (§1 corrections binding) + the four drill-down maps.
>
> **Method (2026-07-02, Fable-5 ultracode judge panel):** four independent full designs —
> clean-slate-ideal / minimal-migration-risk / manifest-grammar-maximal (Fable 5) + one
> unconstrained Opus 4.8 design — scored by independent judges (the manifest-maximal design won,
> min-migration-risk second; the migration-risk judge run died mid-panel and its lens was re-covered
> by the review round) → best-of synthesis → a four-reviewer adversarial round: Opus 4.8 `max` ·
> a mechanical §5 compat verifier · a simulability red-team · **a live non-Claude review over the
> OpenAI API (`gpt-5.4-mini` — the strongest model available to this deployment's key; a full-tier
> Codex/GPT pass at owner review remains worthwhile)**. All 24 surviving findings were
> source-verified and applied, including two blockers (the ADMIN-floor scope over-extension → the
> §2.2 two-lane authority model; the sim/`parent_hub` custom-id hazard → §2.4's hub-keyed frozen
> routing constants).
> **Every load-bearing `file:line` citation in this document was re-verified against live source this
> session, and the four-reviewer round (Opus adversarial · compat verifier · simulability red-team ·
> GPT) is applied.** Three corrections to the briefing materials are carried forward, verified: the
> `BindingMutationPipeline` lives at `disbot/services/binding_mutation.py:154` and
> `ResourceProvisioningPipeline` at `disbot/services/resource_provisioning.py:240` (not in
> `settings_mutation.py`); the `EventBus` lives at `disbot/core/events.py:52` and
> `disbot/utils/events.py` does not exist (the catalogue is `disbot/core/events_catalogue.py`); and —
> correcting the synthesis §1 PARTIAL-3 itself — the three `governance.visibility/cache/cleanup`
> events **are live-subscribed** (`core/runtime/__init__.py:181–183`), the cache event's real name is
> `governance.cache.invalidated`, and the genuinely subscriber-less pair is
> `governance.execution.allowed/denied` (§1.2). Source wins over docs.
>
> **Linchpin validation (2026-07-02, #1639):** the two unproven load-bearing assumptions — golden-
> harness coverage (§6, §10.1 risk 1) and grammar tier-1/2 expressiveness (§2, §10.1 risk 5) — are
> now **built and measured**: see
> [`rebuild-linchpin-validation-2026-07-02.md`](rebuild-linchpin-validation-2026-07-02.md)
> (harness: [`parity/`](../../parity/README.md), replay-deterministic, coverage measured; grammar:
> 73% as-specced → **85% with six named amendments**, operator band 97%). Evidence verdict:
> **GO with amendments — now folded in** (2026-07-02, see addendum below): `GatewayListenerSpec`
> (§2.8, G-1), list-valued settings + declarative validator bounds (§2.5, G-2/G-5),
> `AnnouncementRouteSpec` (§2.8, G-3), `CommandSpec.cooldown` (§2.2, G-4), per-`kind` command-pool
> scoping (§2.2/§3.1, G-6), plus the harness-mechanism naming correction, the evals/harness
> composition note, the K10 Postgres-service-container CI requirement, the determinism-pinning
> budget note, and clock+RNG as injectable kernel services (§1.2, §6, §9).
>
> **Revision (2026-07-02, external review round 2):** the owner ran **two external GPT review
> sessions** over the merged spec (the §E full-tier seam). Folded in, each verified per Q-0120:
> the plain-language summary below (owner-endorsed), the table of contents, the glossary (§11), the
> §8 decision quick-table, the dashboard/control-surface contract (§6), pre-cutover operational
> contracts + deliberate non-goals (§10.3), importer mismatch stop-codes (§5.2), the shadow-window
> compat scoreboard (§5.4), canary + renderer kill-switch (§10.1), the AI session-state layering
> note (§5.1), and the dense-panel sim fallback (§9.3). **Declined with reasons** (detail in the
> session log): footnote-izing `file:line` citations (they are the verification substrate — every
> one is re-checkable), splitting the document (the TOC solves navigation without breaking the
> merged artifact's links), full normative/rationale separation (the new repo's *generated* docs do
> that — §7; this document argues its case to the owner on purpose), a fixed per-subsystem
> "manifest budget" (§2.9's ratchet already enforces the same thing without an arbitrary number),
> and compile-time Discord component caps (already specified, §2.3).
>
> **Addendum (2026-07-02, owner architecture-brainstorm session):** two grammar gaps the owner
> flagged before code starts, both folded in as compile rules rather than left as conventions:
> **(1)** `SettingSpec`'s preset mechanism was ported verbatim in numeric-only form (§2.5) even
> though Q-0070 already decided presets-plus-manual-entry applies to *every* setting class,
> including authored text — closed via a `preset_kind` field (§2.5, Q-0215); **(2)** multi-select
> was Q-0205's owner-directed idiom for the *current* bot but was never promoted into the rebuild
> grammar as a compile-time default — closed via a `SelectorSpec` multiplicity-inference rule
> (§2.4, Q-0216). Both are additive, no other section changes.

---

## Plain-language summary — read this first

*This section says what the whole document says, without the engineering vocabulary. Every claim
here is specified precisely later; when they differ, the technical sections win.*

**What this document is.** The complete blueprint for rebuilding SuperBot from scratch in a new
repository. **You approve or reject this document before a single line of the new bot is written.**
The current bot keeps running in production, untouched, the entire time — the new one replaces it
only after it provably behaves the same.

**Why rebuild at all.** Three verified problems, all structural — none fixable with one more patch:

- **Every feature is smeared across many files** (its commands in one place, its buttons in another,
  its settings in a third, its help text in a fourth). They drift apart, and keeping them aligned
  consumes most of the effort of every change.
- **Names collide at boot.** Twice in three days, two features claiming the same command name
  crash-looped the production bot — and nothing in the system could catch that before it hit
  Discord. The same class of silent name-clash exists for buttons, settings, and events.
- **The good rules exist but are optional.** There is a correct, audited path for changing settings —
  and 40 places in the code quietly bypass it. A safety rail you can step around is not a rail.

**The three big ideas of the new design:**

1. **One description file per feature (a "manifest").** Each feature declares everything it has —
   commands, buttons, settings, events, tables, help — in one typed file. Panels, help pages, the
   settings hub, permission checks, documentation, and test scaffolding are all *generated from it*,
   so they can never drift apart again. Hand-written UI code still exists, but as a counted,
   justified exception — not the normal way.
2. **One name registry.** Every name — commands, button identities, setting keys, event names —
   is reserved when declared. Two features claiming the same name fail the pull request *and* fail
   the deploy **before the bot connects to Discord**. The crash-loop class dies structurally.
3. **Layouts are computed, not debated.** Which button goes where, how settings group, which hub
   hosts a feature: a deterministic simulator searches the options against real usage data and
   produces a "here's the winner and why" report. **You ratify it** — and the machinery can touch
   *only* arrangement, never meaning, wiring, or button identities (that separation is enforced by
   tests, not promises).

**What changes for you and your servers:**

- **Useful things are ON by default.** Logging and AI answering work out of the box instead of
  being silently off. Two hard safety lines survive verbatim: nothing posts or gets created until
  you pick/confirm a destination, and anything that sends member content to an external paid
  service (image moderation) stays strictly opt-in per server — the compiler physically refuses a
  spec that tries otherwise.
- **No more boot crash-loops from name collisions** — a colliding change goes red in CI instead.
- **One settings surface** with one authority model and one audit trail.
- **Nothing observable breaks.** Every button identity, setting key, event name, and all data
  (coins, XP, karma, inventories, tickets, audit history) is on a frozen, machine-checked
  compatibility list. Your data crosses over via an importer whose dry-run report **you review
  before it runs for real**, and the old bot + its untouched database stay available as rollback
  for a bounded window after the switch.

**How the build runs after approval** (nothing below starts before it):

```
kernel first (K0–K10)          the engines + name registry + checkers — no features yet
  → port features in 7 bands   each feature: declare manifest → implement → must match
                               recordings of the CURRENT bot's behavior ("golden parity")
  → cutover                    dry-run data import you review → freeze → flip → rollback window
```

**What you are approving:** the 14 items in [§10.2](#102-what-the-owner-ratifies-by-approving-this-spec)
— most importantly: the manifest architecture, the name registry, safe-default-ON with its two
carve-outs, the fresh-database-plus-importer migration (with a specified conservative fallback),
and the build order. **What you are *not* approving yet:** the final cutover — that is a separate,
owner-verified step at the very end.

**Reader's guide.** Skim [§0](#0-executive-summary--the-one-picture) (the technical summary), then
[§8](#8-the-ten-open-questions--decisions) (the ten decisions, with a quick-table) and
[§10](#10-risks--what-the-owner-is-approving) (risks + exactly what approval means). The
[glossary (§11)](#11-glossary) defines every term of art; the deep sections (§1–§7, §9) are
reference material for the agents that will build this.

### Table of contents

- [Plain-language summary](#plain-language-summary--read-this-first)
- [§0 Executive summary — the one picture](#0-executive-summary--the-one-picture)
- [§1 Architecture](#1-architecture) — packages/layers, runtime contracts, ownership, AIGateway home, complexity budget
- [§2 The manifest grammar](#2-the-manifest-grammar) — every primitive, field-level; format; escape hatch; the simulability contract
- [§3 The central namespace](#3-the-central-namespace) — reservation, fail-before-boot, tombstones, custom-id versioning
- [§4 Settings model](#4-settings-model) — one declaration path; three lanes; AI fold-in; safe-default-ON
- [§5 Data model + backward-compat contract](#5-data-model--backward-compat-contract) — schema, migration decision, all nine hazard classes
- [§6 Control plane](#6-control-plane) — rulesets/OIDC, required gates, golden parity, the dashboard contract
- [§7 Regenerated binding docs](#7-regenerated-binding-docs)
- [§8 The ten open questions — decisions](#8-the-ten-open-questions--decisions)
- [§9 Build order](#9-build-order) — K0–K10, the seven port bands, the first simulator passes
- [§10 Risks + what the owner is approving](#10-risks--what-the-owner-is-approving) — incl. §10.3 operational contracts + non-goals
- [§11 Glossary](#11-glossary)

---

## 0. Executive summary — the one picture

**What the new bot IS.** A small set of **kernel engines** interpreting one typed, versioned
**manifest** per subsystem. Today a subsystem is smeared across a cog, a views directory, a
`schemas.py`, an entry in `SUBSYSTEMS` (`disbot/utils/subsystem_registry.py:58` — 43 persisted keys),
an entry in `HUBS` (`disbot/utils/hub_registry.py`), help-catalogue metadata, settings-key constants,
and event literals. In the rebuild, a subsystem is **one manifest module** — a `SubsystemManifest`
declaring its commands, panels, actions, settings, bindings, resources, events, tasks, diagnostics,
stores, help, and (where relevant) game and knowledge facets — plus a thin file of registered
*handlers* for the behavior the grammar deliberately cannot express. The engines (panel engine,
settings engine, workflow engine, help projection, diagnostics, task supervisor) are written once, in
the kernel, and never per-feature. Panels, help, docs, the custom-id and event inventories, the
ownership map, property tests, golden-harness scaffolding, and the simulator's search space are all
**generated from the manifest**. Hand-written UI code is the counted, justified exception — not a
layer.

**The three spines**, built before any feature:

1. **The manifest grammar + engines** (§2) — the declarative primitives, **extending the shipped
   types** (`SettingSpec`/`BindingSpec` in `subsystem_schema.py`, `ResourceRequirement`,
   `CapabilityDecision`, the lifecycle result contracts, `AIGateway`) rather than recreating them,
   and consolidating the three shipped registry fragments (`SubsystemSchema` + `SUBSYSTEMS` + `HUBS`)
   into one record. Every field is classified **semantic / arrangement / objective**, so a
   deterministic simulator can search layouts without ever being able to touch meaning.
2. **The central namespace** (§3) — every string identity in the system (commands and aliases,
   custom_ids, event names, settings keys, subsystem keys, capability strings, handler refs, task
   prefixes, item keys, AI task names) is reserved at declaration and validated in CI (including on
   the merge result) and again in full **before the gateway connects** (§3.2's two-phase model). This
   kills the class that crash-looped production twice in
   three days (Q-0211 `give`, BUG-0030 `dock`/`sail`) and the Q-0200 silent same-name-`def` shadowing
   — structurally, not reactively.
3. **The simulation loop + the golden harness** — arrangement (which button goes where, how settings
   group, which hub homes a subsystem) is **discovered by a deterministic, auditable simulator** over
   the manifest, gated by a required *sim-reviewed-or-exempt* CI check; and the Phase-0.5 golden
   behavioral harness, captured from the **live** bot, is the acceptance oracle — every ported
   subsystem is **red until parity**, and green is a one-way door.

**What changes for the owner.**

- **Safe-default-ON.** Logging, AI answering, and other discoverability-starved features are on out
  of the box instead of silently off (`server_logging_config.py:85 DEFAULT_ENABLED = False` is the
  verified current state this reverses). Two hard carve-outs survive verbatim: nothing that sends
  member content to an external paid API turns on without explicit guild opt-in (image moderation),
  and nothing silently creates channels or roles — features go live *pending a destination*, with a
  one-click bind offer, never an unasked mutation (§4).
- **No more boot crash-loops from name collisions.** A colliding PR goes red in CI; a bad deploy
  fails before it connects, with a report naming both claimants.
- **Layouts stop being debated.** The simulator proposes, with a "why it won" record; the owner
  ratifies. Panels, help, and settings hubs are generated from one declaration and can never drift
  from it.
- **Configuration has exactly one surface**, one authority model, one audit trail.

**What does NOT change.** Every persisted contract in the synthesis §5 backward-compat set —
subsystem keys, static custom_id strings verbatim (including the eight `ai:*` panel ids, enumerated
and verified this session), catalogued event names and payload shapes, settings keys, actor-type and
sole-writer invariants, AI stable identifiers, env/secrets behavior, versioned content files — is
frozen in a machine-readable reservation set that CI enforces (§3, §5). The owner's data comes across
whole, checksum-reconciled, with the old bot and its untouched database held as rollback for a
bounded window (§5).

---

## 1. Architecture

### 1.1 Package and layer model

New repo layout (top-level package `sb/`; `disbot/` stays behind in the frozen reference repo):

```
sb/
  spec/          # the grammar: frozen dataclasses only, incl. AI typed contracts   (dependency-free leaf)
  namespace/     # the reservation registry + collision policy + legacy_reservations.json
  manifest/      # one module per subsystem: pure declarations + handler registrations
    layout/      # <subsystem>.lock.json arrangement overlays — written ONLY by sim/apply
  kernel/        # the engines:
    observability/ #  metrics + structured logging (cross-cutting leaf — importable by every layer)
    events/        #  EventBus + catalogue generated from EventSpecs
    lifecycle/     #  7-phase machine, admission gate, managed task supervisor
    authority/     #  actor_holds_capability + CapabilityDecision (ported field-for-field)
    workflow/      #  ONE mutation executor: ALL four write lanes (incl. scalar), Result grammar, audit fan-out
    settings/      #  read-side resolution only (per-guild → global → activation default); never writes
    interaction/   #  panel engine, custom-id router, EmbedFrame, selectors, navigation
    help/          #  help-as-projection from manifests
    diagnostics/   #  provider registry + health-findings persistence
    ai/            #  AIGateway (extended) — the blessed facade; providers behind a port (§1.4)
  domain/        # business logic: economy, moderation, games engines, knowledge domains
  adapters/      # IO edges: discord client glue, db/ (asyncpg-only), ai providers, http
  app/           # composition root: load manifests → validate namespace → build → boot
tools/           # checkers, manifest compiler, generators (docs/tests/goldens), importer
sim/             # simulators + sim records (deterministic, auditable; never imported at runtime)
parity/          # golden-harness wiring + the per-subsystem parity expectation file
```

There is **no hand-written views layer and no per-feature cog file**. discord.py's Cog objects still
exist at runtime (they are its loading unit), but they are instances of one generic `SubsystemHost`
the loader builds from the manifest — so there is no per-feature place for permission checks, embed
builders, or DB writes to drift into. The only view *code* is the escape-hatch tier: renderer
overrides and re-homed legacy views living in **`domain/<x>/ui/`** — the one domain sub-tree cleared
to import discord — registered as refs and counted under the tier-3 regime of §2.9. The kernel
resolves them through the ref table at composition time, so no `kernel → domain` import edge and no
dynamic import ever exists.

**Import rules** (enforced by `tools/check_architecture.py` from commit 1 — errors, not warnings; the
grandfathered-warnings pattern of the current repo starts at zero):

| Package | May import | Must NOT import |
|---|---|---|
| `sb/spec/` | stdlib only | everything else — the grammar is a dependency-free leaf |
| `sb/namespace/` | stdlib only | everything else — it validates compiled snapshots (pure data, §3.2), so it is a second leaf importing neither `spec` nor manifests |
| `sb/kernel/observability/` | stdlib (+ `prometheus_client`, lazy with fallback) | everything else — cross-cutting leaf |
| `sb/adapters/db/` | asyncpg, `spec`, `observability` | everything else — nothing else touches SQL |
| `sb/kernel/*` (events, lifecycle, authority, workflow, settings, interaction, help, diagnostics) | `spec`, `namespace`, `observability`, adapter *ports* it defines, discord | `domain`, `manifest`, `adapters` internals |
| `sb/kernel/ai/` | `spec`, `namespace`, `observability`, `kernel/events`, `kernel/settings`, the db port | **`domain`**, `manifest`, `kernel/interaction`, adapters internals — nothing above it, ever |
| `sb/domain/<x>/` | `spec`, `namespace`, kernel facades, **declared** sibling domains only (§1.3) | `adapters`, `manifest`, any undeclared domain, discord |
| `sb/domain/<x>/ui/` | everything its parent domain may, **plus discord** and the `kernel/interaction` renderer contract | `adapters` internals, `manifest`, other domains — the one domain sub-tree cleared for discord; reachable only via registered refs; every module counted by the §2.9 escape-hatch report |
| `sb/manifest/<x>` | `spec`, `namespace`, `domain` (handler registration only) | `kernel`, `adapters`, discord |
| `sb/adapters/` | stdlib, discord/asyncpg/provider SDKs, `spec`, kernel ports | `domain`, `manifest` |
| `sb/app/` | everything | — |

Two zero-tolerance rules generalize the current repo's hardest rule (`services/ → views/` blocked):
**the kernel never imports domains**, and **`kernel/ai` never imports anything above itself**. The
second is the structural generalization of the fix for the one live layer break in the current repo
(§1.4). The docs render the layer table *from* the checker's config file, so doc and checker cannot
drift.

### 1.2 Runtime contracts (carried forward, engine-owned)

- **Lifecycle.** The shipped 7-phase machine (`STARTING → RUNNING → DRAINING → SHUTTING_DOWN →
  RESTARTING → STOPPED / FAILED_STARTUP`) and the `can_accept_commands()` admission gate carry
  forward into `kernel/lifecycle`. Boot order: load manifests → **namespace validation (fail here,
  before any network I/O)** → DB pool + migration check → catalogue freeze → host construction →
  gateway connect → persistent-component re-registration → admit commands. A validation failure is
  `FAILED_STARTUP` with a structured named-collision report and a nonzero exit — a red deploy, never
  a crash-loop serving traffic.
- **Event bus.** `EventBus` semantics preserved from `disbot/core/events.py:52`: publish-accepted
  `emit` (a subscriber failure never raises; `event_emitted`/`audit_emitted` flags mean
  publish-accepted only, **not** delivered), per-handler timeout, delivery stats, fail-safe
  subscribers. One upgrade: today an uncatalogued emit produces a metric and a one-shot WARNING and
  keeps running (verified `events.py:22–49`); in the rebuild the catalogue is **generated from the
  union of all manifests' `EventSpec`s** (replacing the hand-maintained
  `core/events_catalogue.py:45 KNOWN_EVENTS` frozenset), and an emit or `on()` against an undeclared
  name is a pre-boot failure. A CI drift check asserts every declared event has ≥ 1 declared
  subscriber or an explicit `observability_only=True` marker (§2.8). Two source-verified facts
  calibrate that check, correcting the synthesis §1 PARTIAL-3 claim: the three
  `governance.visibility.changed` / `governance.cache.invalidated` / `governance.cleanup.changed`
  events **have live subscribers** — `core/runtime/__init__.py:181–183` wires them to scope-aware
  session invalidation, guild-state cache invalidation, and the reserved DEBT-003 cleanup-cache hook
  (wiring that today exists only inside `setup()` closures, exactly the import-invisible class §1.6
  makes declared) — so the rebuild carries them as `EventSubscription`s in the governance manifest;
  dropping them would silently serve stale visibility/authorization state after governance
  mutations. The genuinely subscriber-less catalogued events are `governance.execution.allowed` /
  `governance.execution.denied` (emitted decision traces, `governance/execution.py:228`; verified no
  `bus.on` anywhere) — **those** are the `observability_only=True` carriers. Note the third literal:
  `governance.cache.invalidated`, not `.changed` (`governance/events.py:23`).
- **Task registry.** The managed task supervisor (`spawn/cancel_all/cancel_by_prefix`, diagnostics
  self-registration) carries forward; every recurring task is a `ManagedTaskSpec` with its name
  prefix namespace-reserved; a free-floating `asyncio.create_task` is an AST-fenced violation — the
  task-spawn invariant, renamed **INV-T** (§8, decision 4).
- **Interaction lifecycle.** Opening a panel is never authorization: **every callback re-resolves
  its declared authority** — config/governance-lane surfaces through `actor_holds_capability`
  (`disbot/governance/capability.py:71`, semantics ported field-for-field: target-guild membership
  binding, platform-owner override, ADMINISTRATOR floor, revoke-only overlay, `setup_delegate`),
  domain-lane surfaces through the shipped visibility-tier check (the §2.2 two-lane model). The
  kernel enforces this structurally — the generated component callback *is* kernel code that
  resolves the action's declared authority before invoking any handler, so a domain cannot forget
  the check; there is no code path from a Discord component interaction to a handler that skips it. `safe_defer/safe_followup/safe_edit`,
  embed clamping, timeout-disable, invoker-lock, and the `PersistentView` restart contract
  (`timeout=None` + static custom_id + startup re-registration) are engine behavior, not
  per-view convention.
- **Clock + RNG are injectable kernel services (linchpin-validation finding, 2026-07-02).** The
  golden-harness spike found current-bot paths that are nondeterministic by construction —
  unseeded private RNG instances, real-TTL caches, `datetime.now()` folded directly into minted
  ids — each one a golden the harness had to exclude rather than capture (the `parity/cases/
  sweep.py` exclusion ledger). The rebuild makes `kernel/clock` (`now()`) and `kernel/rng`
  (seedable per test/session) the only sanctioned time/randomness sources; a direct
  `datetime.now()`/`random`/`time.time()` call outside `kernel/clock`/`kernel/rng` is an
  AST-fenced violation, same enforcement shape as the task-spawn (INV-T) and lazy-import fences.
  This is what makes every surface golden-testable, not just the ones that happened to avoid
  wall-clock/randomness already.

### 1.3 Ownership model — who writes what

- **One writer per table.** Every persistent store is declared by a `StoreSpec` (§2.8) naming its
  sole-writer seam. `adapters/db` is the only package that touches SQL (asyncpg-only, as today). The
  ownership doc is a generated projection of `StoreSpec`s, and **seam authority is itself checked**:
  a generated invariant test per store asserts no other module writes the table — the current repo's
  hardest-won settings lesson being that a good seam which isn't *authoritative* equals no seam.
- **One workflow engine, four lanes.** The four shipped audited pipelines —
  `SettingsMutationPipeline` (`disbot/services/settings_mutation.py:221`),
  `BindingMutationPipeline` (`disbot/services/binding_mutation.py:154`),
  `ResourceProvisioningPipeline` (`disbot/services/resource_provisioning.py:240`),
  `GovernanceMutationPipeline` (`disbot/governance/writes.py:107`) — become **four lane strategies
  inside one workflow engine** sharing one contract: resolve authority → coerce/validate → preview
  (when declared) → transactional write + audit row → post-commit event → cache invalidation →
  `WorkflowResult`. The lanes stay semantically separate (scalar / binding / resource / governance —
  the preserve-map's "never collapse to one generic config table" rule) but speak one Result grammar
  and share one audit fan-out (`emit_audit_action` semantics preserved, including the
  import-invisible `audit.action_recorded → server_logging` bus wiring, which the manifest now makes
  *declared* rather than grep-archaeological).
- **Sole-writer invariants port verbatim as AST fences:** **INV-F** (every coin mutation through the
  economy service → `economy_audit_log`), **INV-G** (XP), **INV-K** (karma — now unambiguous,
  decision 4), and the `setup_delegate` sole-minting boundary (only the setup apply workflow mints
  that actor type; `test_setup_delegate_actor_boundary` ports with it). The platform-owner bypass
  (`config.is_platform_owner`, `config.py:46`) is preserved.
- **Cross-domain calls are declared.** A domain may call another domain's service only if the
  dependency appears in its manifest (`dependencies=("economy",)`); the architecture checker reads
  the manifests. Undeclared cross-domain interaction happens only via events. This keeps the real
  coupling graph visible and machine-checkable — the direct answer to the verified finding that the
  current repo's true coupling is runtime/lazy and invisible to every static tool.

### 1.4 Where AIGateway lives (open question 7 — decided)

**The root cause moves, then the gateway lands where the layer rules make the break unrepeatable.**
The one live layer break — `disbot/core/runtime/ai/gateway.py:51 from services import metrics`
(verified) — exists because `services/metrics.py` is **misfiled observability**: its only external
import is `prometheus_client` (line 18, with a clean no-op fallback; verified). So the fix is
two-part:

1. **Metrics relocates to `kernel/observability/`** — a cross-cutting leaf importable by every
   layer. The break dissolves at its root rather than being patched around.
2. **The gateway extends into `kernel/ai/`** — same class, same never-raise `execute()` contract,
   provider registry, redaction choke point, guild-policy overlay, degraded-response shape, and
   diagnostics collector, carried forward field-for-field from `gateway.py:177`. Its guild-policy
   reads go through `kernel/settings` (sideways), its DB reads through the db port (downward), its
   metrics through observability (downward). **`kernel/ai` may import nothing above itself — a hard
   forbidden edge**, so the break *class*, not just the instance, is dead: the gateway can never
   again acquire an upward dependency.

The **seam split is preserved in its new form**: today exactly one blessed module re-exports the
gateway and its typed contracts (`disbot/services/ai_gateway.py:25`, verified — "cogs and services
consume the AI gateway through this module"); in the new repo `sb/kernel/ai/__init__.py` is that
sole sanctioned import point, enforced by the architecture checker (only `kernel/ai/*` may import
`kernel/ai/providers` or the provider port's adapter implementations). The typed AI contracts
(`AIRequest`, `AIResponse`, `AITask`, …) live dependency-free in `sb/spec/ai.py`, importable from
anywhere. Knowledge domains attach via the manifest's `knowledge` facet (§2.8), never by touching
the gateway; the sole-passive-responder invariant is asserted at the composition root (exactly one
passive conversational stage registered).

### 1.5 God-functions are prevented — the complexity budget

The verified worst debt after collisions: `AINaturalLanguageStage.process` at cognitive 135 / 869
LOC, `validate_registry` at 83, 533 functions over threshold. Defenses, in order of leverage:

1. **The grammar removes the incentive.** The repeated defer/auth/mutate/audit/render choreography
   that bloats callbacks today is engine code written once; per-feature code is a declaration plus a
   small handler, so there is no place for an 869-line `process()` to accrete.
2. **A hard budget in the required CI check:** cognitive complexity ≤ 15 per function, ≤ 80 lines
   per function, ≤ 500 lines per module. The exception file starts **empty** (nothing exists to
   grandfather); a deliberate exception carries a justification and a ledger link, and the check
   fails if a measured value improves past its recorded entry without the entry tightening — a
   ratchet, in both directions.
3. **The two worst offenders are decomposed at design time.** NL routing becomes a thin
   `NaturalLanguageRouter` in `kernel/ai` dispatching to per-domain intent routes declared by
   `KnowledgeDomainSpec` — the monolith cannot re-form because no single module owns all intents,
   the routing table being manifest data. `validate_registry` (`subsystem_registry.py:1309`) is
   replaced by the namespace validator — a linear pass over reservations.
4. **The manifest itself is subject to the budget.** `SubsystemManifest` is a thin identity spine
   plus optional typed facets (§2.1), following the shipped codebase's own instinct — guild config
   and per-user participation are deliberately *sibling* registries, never one record (verified
   docstring, `subsystem_schema.py:31–37`). A mega-record would be the god-object the budget
   forbids, declared instead of coded.

### 1.6 Coupling stays visible — no lazy-import hiding

Function-body imports are **banned** by the architecture checker except for entries in a
cycle-breaking allowlist — each entry names the cycle it exists to break with an inline
justification the checker verifies, the list is shrink-only, and the presence of any entry is a
standing CI warning nagging for a graph fix. "Fixing a cycle by hiding the import" — the pattern
that made the current repo's true fan-out invisible (`essential_setup` measured at 0 dependents by
`impact_analysis` because everything imports it lazily) — is a build failure, not a style nit. The
edges that are invisible to *both* import and call graphs today (EventBus subscriptions, registry
callback fields, prefix dispatch) are all **manifest-declared** in the new repo — `EventSpec` names
its expected subscribers, `PanelActionSpec` names its handler ref — so the wiring map is generated
from data, complete by construction. This is also the precondition for the file-ordering simulator
to be honest: a clustering engine can only optimize a graph it can see.

---

## 2. The manifest grammar

### 2.0 Format decision and the compile pipeline

**Decision: hybrid.** **Python frozen dataclasses are the sole authoring surface; a canonical
committed JSON snapshot is the interchange artifact; arrangement lives in machine-written lock
overlays that can never touch semantics.**

- *Authoring* is Python (`sb/spec/` types, instantiated in `sb/manifest/<subsystem>.py`). This is
  forced by binding constraint 2: the shipped lanes being extended are already frozen dataclasses
  (`SettingSpec` `subsystem_schema.py:109`, `BindingSpec` `:75`, `ResourceRequirement`
  `resource_specs.py:79`) with callable fields (`validator`, `completeness_rule`) that YAML can only
  carry through a string-import indirection — new machinery that reinvents Python worse and is
  itself a fresh collision surface. Dataclasses fail at import time with real tracebacks (the
  fail-before-boot posture), and mypy + IDEs check manifests for free.
- *Interchange* is `manifest.snapshot.json`: deterministic (sorted keys, stable ordering by
  `key`/`panel_id`/`action_id`, stable hashing), produced by `tools/manifest_compile.py`, committed,
  and regenerated in CI (drift = red). Every callable serializes as its **registered ref name** — an
  unregistered callable is a compile error — so the snapshot is 100% data. The simulator, the doc
  and test generators, the golden scaffolder, the namespace CI check, and the compat differ consume
  the snapshot; none imports Python.
- *Arrangement* lives in `sb/manifest/layout/<subsystem>.lock.json` — overlays **written only by
  `sim/apply.py`** and applied at compile time. The loader rejects any overlay key that is not
  tagged arrangement, so a simulator bug can corrupt layout but structurally cannot corrupt
  semantics, custom_ids, or capability strings. The manifest source files are never machine-mutated;
  a sim re-run is a reviewable, revertible data diff.

YAML-only was rejected (loses typing, recreates the shipped types, stringly-typed drift);
Python-only was rejected (callables and import order make it non-diffable and non-simulable). The
hybrid gives one authoring truth and one simulable truth, pinned together by a checker.

**Field roles.** Every field of every spec is tagged in the dataclass field metadata — and therefore
in the snapshot — with exactly one role:

- **[S] semantic** — identity, wiring, behavior, policy, **and all user-facing copy** (labels,
  hints, summaries, user messages). Hand-authored; a simulator never touches it. Copy is meaning:
  the sim arranges surfaces, it does not rewrite language.
- **[A] arrangement** — grouping, ordering, layout, placement. Owned by the simulator: humans seed,
  sims optimize, the gate audits.
- **[O] objective** — data the cost function reads (usage-weight slots, co-occurrence keys,
  destructive flags, flow stages). Never affects runtime behavior except as display-independent
  safety constraints.

A unit test asserts every field of every spec is classified exactly once; an untagged new field is a
red check.

### 2.1 SubsystemManifest — the root record (consolidation, not greenfield)

One manifest per subsystem, in `sb/manifest/<key>.py`. It **extends the shipped `SubsystemSchema`**
(`subsystem_schema.py:234` — fields `subsystem, bindings, settings, resource_requirements,
domain_panels, version, completeness_rule` all carried forward with their names and semantics) and
folds in the `SUBSYSTEMS` dict entry shape and the `HubEntry` metadata — one record, several
projections. Per the anti-god-object rule (§1.5), it is a **thin identity spine plus optional typed
facets**: a facet a subsystem doesn't need is absent, not empty, and per-user *participation* shape
stays a sibling registry exactly as shipped (`participation_schema` — the verified
`subsystem_schema.py:31–37` doctrine: "Guild config and participation are never mixed into the same
schema").

| Field | Type | Role | Notes |
|---|---|---|---|
| `key` | `str` | S | The persisted `subsystem_registry` key, **verbatim** (compat item 1). Ported keys must exist in `legacy_reservations`; new keys are namespace-minted. |
| `display_name`, `description`, `emoji` | `str` | S | Presentation copy — semantic (sim-frozen). |
| `color_token` | `str` | S | Style-token indirection into the EmbedFrame theme (replaces raw ints). |
| `category`, `tags` | `str`, `tuple[str,...]` | S | Search/diagnostics metadata. |
| `visibility_tier`, `visibility_mode` | `str` | S | Governance defaults, today's vocabulary. |
| `supports_dm`, `has_cleanup_rules` | `bool` | S | |
| `capabilities` | `tuple[str,...]` | S | Three-part `{subsystem}.{resource}.{action}` strings (format enforced at compile — the shipped rule, `subsystem_registry.py:7`, incl. reserved prefixes `_internal.* / system.* / governance.*`); each namespace-reserved. |
| `dependencies` | `tuple[str,...]` | S | Sibling domains whose services this one may import (§1.3). |
| `commands` | `tuple[CommandSpec,...]` | S | §2.2. |
| `panels` | `tuple[PanelSpec,...]` | S | §2.3. |
| `settings` | `tuple[SettingSpec,...]` | S | The scalar lane — the extended shipped type (§2.5). |
| `bindings` | `tuple[BindingSpec,...]` | S | The pointer lane (§2.5). |
| `resources` | `tuple[ResourceRequirement,...]` | S | The provisionable lane (§2.5). |
| `domain_panels` | `tuple[DomainPanelSpec,...]` | S | Shipped type (`subsystem_schema.py:203`) kept for external config destinations. |
| `events` | `tuple[EventSpec,...]` | S | Events this subsystem owns/emits (§2.8). |
| `subscriptions` | `tuple[EventSubscription,...]` | S | Handler refs for events it consumes — the wiring map's source. |
| `tasks` | `tuple[ManagedTaskSpec,...]` | S | §2.8. |
| `diagnostics` | `tuple[DiagnosticProviderSpec,...]` | S | §2.8. |
| `stores` | `tuple[StoreSpec,...]` | S | Tables it solely writes (§2.8). |
| `help` | `HelpEntrySpec` | S | Summary, examples, rules text — projection input. |
| `game` | `GameFacet \| None` | S | Optional typed facet bundling ChallengeSession / IdleAccrual / Leaderboard / catalog specs (§2.8). |
| `knowledge` | `KnowledgeDomainSpec \| None` | S | Optional AI/knowledge facet (§2.8). |
| `completeness_rule` | `HandlerRef \| None` | S | Shipped hook, now a registered ref. |
| `version` | `int` | S | Schema-version drift diagnostics, as today. |
| `parent_hub` | `str \| None` | **A** | Hub placement — sim-owned. The sim doc's per-domain table explicitly names hub/category grouping as a sim target, so this is arrangement, not identity. Its two runtime projections — hub-roster membership and *which* hub-keyed home-nav constant a panel shows — are **enumerated derivation targets** (§2.10.2); **no custom_id is ever minted from it** (§2.4). |
| `hub_group` | `str \| None` | **A** | Sub-grouping within a hub — membership across the hub's **[S]-declared `HubGroupSpec` pool** (§2.5: the sim assigns, it never mints groups or copy). |
| `ui_priority` | `int` | **A** | Ordering weight within hub/help. |
| `usage_profile` | `UsageProfile` | O | Declared frequency class (`hot/warm/cold`) + co-use seed keys; overridden by measured telemetry at sim time (§2.10.4). |

**Derivation rules (the anti-drift core).** Hubs have **no `primary_children` data**: a hub's roster
is *computed* as the `parent_hub` filter, so the CI-tested bidirectional roster rule
(`test_every_hub_primary_children_match_parent_hub_filter`, documented at `hub_registry.py:48–57`)
becomes true by construction — one side of the pair no longer exists to drift. Hub-level presentation
(`entry_command`, `purpose`, `minimum_tier`) lives in a small `HubSpec` on the hub subsystem's own
manifest, together with the hub's hand-authored `hub_groups: tuple[HubGroupSpec,...]` pool (§2.5).
Arrangement **provenance** is not a manifest field at all — it lives per [A]-field-group in the lock
overlay, written only by `sim/apply.py` (§2.10.3), so provenance travels with exactly the layer that
owns arrangement. Likewise the help catalogue, the settings-hub group list, the event catalogue, the
capability inventory, the ownership map, and the wiring map are all projections; none is separately
maintained. `RouteRegistry` (map P3) is **not a second type** — routing is a projection of the
manifest; `KnowledgeDomainSpec` (P4) is a facet of it (decision 2).

### 2.2 CommandSpec

| Field | Type | Role | Notes |
|---|---|---|---|
| `name`, `aliases` | `str`, `tuple[str,...]` | S | Each reserved individually in the namespace `command` kind, **scoped per `kind`** — the exact Q-0211/BUG-0030 fix, corrected by the linchpin spike (G-6, 2026-07-02): prefix (`!karma`) and slash (`/karma`) legitimately coexist today because Discord's own command namespaces are disjoint, so one *shared* pool across kinds would flag every dual-surface command as a false collision. The pool is one reservation *system* with a kind-keyed partition, not one flat pool. |
| `kind` | `enum {prefix, slash, both}` | S | |
| `summary`, `usage` | `str` | S | Help projection input. |
| `capability_required` | `str = ""` | S | Config/governance-lane authority (the two-lane model below): empty ⇒ ADMINISTRATOR floor — the shipped mutation-pipeline invariant, verbatim, at its shipped scope. |
| `audience_tier` | `str = "user"` | S | Domain-lane authority: the shipped visibility-tier vocabulary (`user/trusted/staff/moderator/administrator/owner`, `utils/visibility_rules.py:21`), resolved at execution time. |
| `route` | `PanelRef \| HandlerRef` | S | Commands open panels by default; command-only behavior requires an escape-hatch justification (command-only surfaces are a drop class per the preserve map). |
| `cooldown` | `CooldownSpec \| None = None` | S | **New (linchpin spike G-4, 2026-07-02).** `rate: int`, `per_s: float`, `scope: enum {user, guild, channel, global}` — declares the shipped command-layer rate limit (`@commands.cooldown`, live on karma/economy and widely elsewhere) as data. Without this field a port silently drops shipped anti-abuse behavior — caught only because the spike's manifests were checked against real source, not assumed. |
| `help_section_order` | `int` | **A** | Order within the subsystem's help entry. |
| `usage_weight` | `float` | O | Seeded from the Phase-1 harvest; telemetry-updated. |

**One authority model, two lanes — the invariant kept at its shipped scope.** The
empty-`capability_required` ⇒ ADMINISTRATOR-floor rule is *scoped to the mutation pipelines* in
source — `governance/capability.py`'s module docstring and the `subsystem_schema.py:129–134`
invariant both say "treated by the mutation pipelines" — and under v1 policy every capability
resolves to the administrator tier (`capability.py:51 _DEFAULT_REQUIRED_TIER`). The grammar keeps
that scope instead of over-extending it: a surface whose `route`/`handler` targets a
**config/governance workflow lane** (scalar, binding, resource, governance) resolves
`capability_required` through `actor_holds_capability`, empty meaning the ADMIN floor, verbatim.
Every other surface — `!help`, `!blackjack`, karma give, game buttons, role-menu selects — is a
**domain-lane** surface: it declares `audience_tier` instead, resolved via the shipped
visibility-tier check, and its writes flow through the audited *domain* seams (INV-F/G/K), which
carry their own domain validation (escrow, cooldowns, no-self). A compile rule makes the lanes
exclusive and total: a config/governance route must leave `audience_tier` at its default, and a
domain-lane surface must leave `capability_required` empty — declaring the wrong lane's field is a
compile error, so every surface has exactly one authority story. The kernel-generated callback
always resolves the *declared* authority — capability or tier — before any handler, so "no path
skips the check" holds and the check is the right check per lane; without this split the grammar
could not lawfully declare the member-facing majority of the ~100-PR surface (every game button
would demand ADMINISTRATOR — contradicting observable behavior on day one). `SelectorSpec` (§2.4)
and `PanelActionSpec` (§2.6) use this same model.

### 2.3 PanelSpec + PanelContext + EmbedFrame + Table/List

The declarative panel. One kernel `PanelRuntimeView` (invoker-lock, timeout-disable, error doctrine,
standard nav, persistence) interprets the spec; no per-panel view class exists for
grammar-expressible panels.

| Field | Type | Role | Notes |
|---|---|---|---|
| `panel_id` | `str` | S | Namespace kind `panel`; the custom-id root for its components. |
| `subsystem` | `str` | S | Owner key. |
| `title` | `str` | S | |
| `audience` | `enum {invoker, public, persistent}` | S | Invoker-locked ephemeral session, shared panel, or restart-safe anchored panel. |
| `anchor_policy` | `enum {reply, channel_anchor, dm}` | S | |
| `timeout_s` | `int \| None` | S | Compile rule: `None` required when `audience=persistent` (the shipped `PersistentView` contract). |
| `frame` | `EmbedFrameSpec` | S | Below. |
| `body` | `tuple[BlockSpec,...]` | S | Typed content blocks — `TextBlock`, `FieldsBlock(provider_ref)`, `TableBlock(TableSpec)`, `ListBlock(ListSpec)`; data from read-model provider refs, never inline queries. |
| `actions` | `tuple[PanelActionSpec,...]` | S | §2.6. Membership and behavior are semantic; placement is not on the action (see `layout`). |
| `selectors` | `tuple[SelectorSpec,...]` | S | §2.4. |
| `navigation` | `NavigationSpec` | S | §2.4. |
| `layout` | `LayoutSpec` | **A** | The one arrangement structure per panel — defined below; the sim's primary search space. |
| `renderer_override` | `HandlerRef \| None` | S | Escape hatch (§2.9) for grammar-inexpressible surfaces (game boards); requires `justification`. |
| `legacy_view` | `ViewRef \| None = None` | S | **Contingency lane** (§2.9): registered ref of a ported hand-coded view class, re-homed under `domain/<x>/ui/` — never a dotted import path. Tier-3, justification-required, ratcheted — not the default port path. |
| `usage_weight`, `co_open_group` | `float = 1.0`, `str = ""` | O | |

**LayoutSpec** — arrangement lives here, in exactly one structure per panel, not scattered on the
child specs: `pages: tuple[PageSpec,...]` (A), each `PageSpec` a tuple of rows, each row a tuple of
**component refs by namespace id** (the panel's declared action and selector ids — the addressing
scheme every overlay, mutation, and cap check uses). Compile rules make omission impossible and
pagination honest: **coverage is exhaustive and exclusive** — every declared action and selector
appears exactly once across the union of pages, so a layout structurally cannot add, drop, or
duplicate a component and reachability can never quietly become arrangement; each page obeys
Discord's caps (≤ 5 rows, ≤ 5 components per row, ≤ 25 per page); page order is deterministic
(tuple order); nav slots and the engine's page-turn controls are engine-injected outside the
searchable space (§2.4's permanent exemption). The §2.10.2 invariance test is defined over the
**union of all pages**, so layouts that page differently still render the identical component
population.

`PanelContext` — the engine's runtime argument to every provider and handler: `bot, guild, actor,
channel, origin (interaction | anchor), audience`. Constructed only by the kernel; handlers never
touch a raw `discord.Interaction`. This replaces the `help_ctx_shim`.

`EmbedFrameSpec` folds `clamp_embed` + `home_embed_frame` + the ad-hoc builders into one budgeted
renderer: `style_token` (S), `max_fields` (S), `field_budget_chars` (S), `footer_mode: enum {none,
subsystem, provenance}` (S), `thumbnail_ref` (S). The engine enforces Discord's size limits —
clamping is not a per-callsite courtesy.

`TableSpec` / `ListSpec` (bounded rendering): `columns: tuple[ColumnSpec,...]` / `item_render_ref`
(S), `page_size` (S), `max_pages` (S), `empty_state: str` (S), `sort_options / filter_options` (S),
`default_sort` (**A** — the sim may pick the first ordering users see). One shared `BrowserView`
engine renders every inventory, dex, recipe browser, leaderboard, and audit list — the verified
seven bespoke selector modules (`views/selectors/`: `channel, role, subsystem, multi, multi_role,
scope, _resource_helpers` — no `multi_channel.py`; synthesis correction 1) collapse into
option-providers behind it.

### 2.4 NavigationSpec + SelectorSpec

**NavigationSpec** — serializable, killing the closure-backed `BackTarget`/`chain_back` stacks that
cannot survive restarts:

| Field | Type | Role |
|---|---|---|
| `parent` | `PanelRef \| None` | S |
| `home_hub` | `str = FOLLOW_PARENT` | S — the routing *rule*, not a captured value: the sentinel default resolves the subsystem's **current** `parent_hub` from the manifest at render/click time, so home routing follows arrangement without being arrangement; an explicit hub key is the rare semantic pin |
| `show_help` | `bool = True` | S — the `nav:help` slot, custom_id verbatim-preserved |
| `show_home` | `bool = True` | S — the home slot. It places one of the frozen **hub-keyed** `nav:hub:<hub>` constants (verbatim-preserved; today minted at `views/navigation.py:452`); each dispatches "open hub `<hub>`" through the custom-id router by manifest lookup at click time. The string is minted per **hub identity** [S], never from `parent_hub` — reassigning a subsystem's hub changes *which* stable button its panel shows on next render, not any string. Every hub's constant stays registered for the hub's lifetime, so a message anchored under an older assignment keeps a working (stale-but-routable) button until its next refresh — the restart-compat rule |
| `show_rules` | `bool = False` | S |
| `extra_routes` | `tuple[NavRouteSpec,...]` | S |

The never-strand rule (every panel reachable back to Help/hub) becomes a **manifest validator**: a
panel with no parent, no help, and no home fails compile unless it is a session-lifecycle game view.
Nav slot placement is deliberately **not** arrangement — consistency beats optimality for
orientation controls; this is a stated, permanent sim exemption. Every route is re-resolved and
capability-checked at click time; parents are rebuilt fresh, never captured.

**SelectorSpec:** `selector_id` (S, namespaced), `kind: enum {channel, role, member, subsystem,
enum, entity}` (S), `options_source: static tuple | ProviderRef` (S), `placeholder` (S),
`min_values`/`max_values` (S), `page_size: int = 25` (S — the engine paginates past Discord's cap),
`empty_state` (S), `on_select: WorkflowRef | HandlerRef` (S), `capability_required` /
`audience_tier` (S — the §2.2 two-lane authority model), `usage_weight` (O). Placement lives in the
owning `PanelSpec.layout` (A).

**Multi-select-by-default compile rule (Q-0205's "pick which of these to turn on" idiom,
promoted from bot-code convention to rebuild grammar, Q-0216):** when a `SelectorSpec`'s
`on_select` target is a `BindingSpec` with `multiplicity > 1`, or a `str`-typed set/list
"pick which apply" choice, `max_values` must default to that multiplicity (or the full option
count for an unbounded pick-many) rather than the Discord-default `1`. A single-select
(`max_values=1`) requires an explicit, justified override — the grammar treats "one at a time"
as the exception for a naturally multi-valued choice, not the default. Genuinely single-valued
selections (channel/role/member pickers backing a scalar `SettingSpec` or a `multiplicity=1`
binding) are unaffected and stay single-select.

### 2.5 SettingSpec · BindingSpec · ResourceRequirement — the extended shipped types

**Binding constraint 2, executed literally: these are the shipped classes**, carried into `sb/spec/`
with every existing field name, type, and semantic intact, and **only additive changes, every one
carrying a constructor default** — a ported `schemas.py` constructor call parses unchanged. One
deliberate validator rides on top: `activation` defaults to `None`, and the **compiler refuses
`None` on any `bool`-typed spec** (§4.4) — ported calls don't *break*, but the port must consciously
choose each feature's activation posture before the manifest compiles, so safe-default-ON flips are
reviewed diffs, never silent inheritance.

**SettingSpec** (shipped fields verbatim from `subsystem_schema.py:109`: `name, value_type, default,
settings_key, capability_required, hint, validator, allowed_values, input_hint, presets` — including
the docstring invariant at `:129–134`, preserved word-for-word: *an empty `capability_required` is
treated by the mutation pipelines as the administrator floor, NOT "no auth"*). Added:

| New field | Type | Role | Notes |
|---|---|---|---|
| `activation` | `Activation \| None = None` | S | The safe-default-ON axis (`on_by_default / on_when_bound / on_when_keyed / off_until_opt_in`; §4.4, decision 5). Applies **only at the unset terminus** of `resolve()` — explicit stored values always win (§4.1). Compile rules: a `bool`-typed spec **must** declare it (the conscious-choice rule, §4.4); a non-bool spec must leave it `None` (the shipped static `default` governs). |
| `external_side_effects` | `bool = False` | S | **Compile rule: `True` forces `off_until_opt_in`** — the image-moderation gate as grammar. And the flag is **verified, not trusted**: the `external-cost-honesty` check reddens any spec gating a path that reaches an egress-marked provider adapter without it (§4.4) — so it cannot be *forgotten* in a port, only failed loudly. |
| `storage` | `enum {kv, typed_column} = kv` | S | Folds AI's typed `ai_guild_policy` columns into the one declaration path (§4). |
| `scope_default` | `enum {guild, global} = guild` | S | Mirrors the pipeline's two scopes. |
| `legacy_keys` | `tuple[str,...] = ()` | S | Old KV key strings this spec answers for (§4). |
| `group` | `str = ""` | **A** | Settings-hub group **membership** — sim-assigned across the subsystem's [S]-declared `SettingGroupSpec` pool (below); `""` = the implicit default group. |
| `advanced` | `bool = False` | **A** | Primary-vs-advanced placement — sim-owned. |
| `panel_order` | `int = 0` | **A** | Order within its group. |
| `edit_weight`, `co_edit_group` | `float = 1.0`, `str = ""` | O | Seed data for the settings-grouping sim: neutral-prior weight, optional seed pair-group — measured pairwise telemetry overrides both (§2.10.4). |
| `depends_on` | `tuple[str,...] = ()` | O | Dependency-order constraint for grouping. |
| `preset_kind` | `enum {none, numeric, text} = none` | S | **Generalizes the shipped `presets` field to authored-text settings (Q-0070, folded in Q-0215).** `numeric` is the shipped numeric-presets behavior, unchanged. `text` extends the same preset-then-edit-then-manual UX to any `str`-typed spec (DM templates, AI instruction bodies, embed copy): the editor renders `presets` as selectable starting points, each openable into a pre-filled override modal, plus an always-present "write your own" entry — never a preset-only editor. Compile rule: a `str`-typed `SettingSpec` with a non-empty `presets` tuple must declare `preset_kind="text"` (or the compiler flags it as decorative/inert data); manual entry can never be disabled by a preset list. |
| `value_type` (list variant) | `"list[int]" \| "list[str]" \| ...` | S | **New (linchpin spike G-2, 2026-07-02).** The shipped exclusion lists (`logging_ignored_channels`/`logging_ignored_users`, #1594) are JSON-list KV values with add/remove UI, and §2.5's `SettingSpec` had no list shape at all — a gap that recurs across automod word lists, security allowlists, and welcome roles, not just logging. A list-typed spec gets kernel-generated add/remove/clear workflows and a chip-list widget for free, the same tier-1 payoff as scalar settings. |
| `bounds` | `tuple[Number, Number] \| None = None` | S | **New (linchpin spike G-5, 2026-07-02).** Declarative `(lo, hi)` range for numeric specs, or `max_len` for string specs — replaces a whole class of trivial tier-3 `validator` refs (karma's two bounded-int settings, welcome's, automod's) with grammar the compiler checks directly. `validator` stays available for genuinely custom rules; `bounds` is the common case lifted out of escape-hatch code. |

**SettingGroupSpec / HubGroupSpec — groups are declared; the sim only assigns.** A settings-hub
group and a hub sub-group render user-visible headers, and copy is semantic (§2.0) — so group
**identity, label, and description are [S]**, hand-authored in a small per-subsystem pool
(`SubsystemManifest.setting_groups`; `HubSpec.hub_groups`), extendable only by humans. **Membership
and order are [A]**: the optimizer assigns nodes across the declared pool, and when it wants a
partition no human seeded it emits a `wants_new_group` finding in its record for a human to name —
it never mints copy, so the S/A split survives regrouping intact.

`validator` stays a real callable in Python; the compiler serializes it by registered ref and errors
on unregistered callables.

**BindingSpec** (shipped fields verbatim from `subsystem_schema.py:75`: `name, kind, required, hint,
capability_required`). Added: `legacy_settings_key_aliases: tuple[str,...] = ()` (S — the KV→binding
alias map, decision 3), `resource_link: str = ""` (S — names the `ResourceRequirement` it binds,
replacing the loose back-pointer convention), `multiplicity: int = 1` (S — bounded list bindings),
`group: str = ""` (**A** — membership across the declared pool, as above), `bind_weight: float = 1.0`
(O).

**ResourceRequirement** (shipped fields verbatim from `resource_specs.py:79`: `kind, intent,
provisioning, binding_name, description`, with the `ProvisioningHint`/`ProvisioningPriority`
companions at `:64`/`:50` unchanged). Added: `offer_on_enable: bool = False` (S — when the owning
feature activates, the settings hub *offers* a provisioning preview; it never silently creates),
`teardown_policy: enum {keep, archive, delete_on_confirm} = keep` (S), `shareable: bool = True` (S),
`audit_intent: str = ""` (S — labels the provisioning audit rows, mig-030 semantics). A separate
"ResourceSpec" name is **not introduced** — one type, the shipped one, extended.

### 2.6 PanelActionSpec — the renamed action primitive (decision 1)

**The UI primitive is `PanelActionSpec`. The shipped automation metadata record ports as
`AutomationActionSpec`. The bare name `ActionSpec` is tombstoned in the namespace and AST-forbidden
repo-wide — before any domain adopts the primitive.**

The shipped `ActionSpec` (`disbot/services/automation_registry.py:35`, verified: a frozen dataclass
of `kind / display_name / description / required_config_keys / optional_config_keys /
requires_owner`) is a *different concept* — a stored automation-rule payload validator, not an
interaction contract. Its **persisted contract is the `action_kind` strings mirrored by migration
032's CHECK constraint** (verified: `032_*.sql:87–88` constrains the string column, not the Python
symbol), so renaming the *class* in the new repo is free — and renaming **both** classes away from
the generic bare name removes the magnet that invites the next collision, which is the whole lesson
of Q-0211/BUG-0030. Unification is rejected: a button-press lifecycle contract and a scheduled
headless side-effect validator share a suffix, not a shape; one grammar over both is optional-field
soup. `PanelActionSpec` beats `UIActionSpec` because it names its owning grammar and stays honest
when actions appear in modals and selects — all panel-scoped.

| Field | Type | Role | Notes |
|---|---|---|---|
| `action_id` | `str` | S | Unique within its panel; custom-id leaf, minted through the namespace (`<panel_id>.<action_id>` for new panels; legacy panels pin verbatim ids via `custom_id_override` from `legacy_reservations`). |
| `label`, `emoji` | `str` | S | Copy is semantic. |
| `style` | `enum {primary, secondary, success, danger, link}` | S | Compile rule: `destructive=True` ⇒ `danger`. |
| `capability_required` / `audience_tier` | `str` | S | The §2.2 two-lane authority model. **"Mutating" here means config/governance-mutating**: actions routing into the scalar/binding/resource/governance lanes resolve `capability_required` (empty ⇒ ADMINISTRATOR floor — the shipped invariant, verbatim). Domain-lane actions — including domain *mutations* that flow through the audited INV-F/G/K seams, e.g. wager escrow — declare `audience_tier`. **Re-resolved at execution by the engine, always.** |
| `defer_mode` | `enum {auto, modal, none}` | S | |
| `handler` | `WorkflowRef \| HandlerRef` | S | Either a parameterized kernel workflow (setting edit, binding set, provision, toggle, paginate — zero code) or a registered domain handler returning `WorkflowResult`. |
| `confirm` | `ConfirmationSpec \| None` | S | Compile rule: any workflow declaring `reversibility=irreversible` **must** carry one. |
| `result_render` | `enum {toast, refresh_panel, result_card, none}` (+ `ResultCardSpec?`) | S | Default: the kernel `WorkflowResult` card. |
| `audit` | `AuditRef \| None` | S | Compile rule: mutating handlers must name their audit event. |
| `visible_when` | `PredicateRef = ""` | S | E.g. `setting:logging.enabled`. |
| `destructive` | `bool` | **O + safety** | Objective input AND a hard layout constraint: never row 0, never adjacent to a hot action — a constraint, not a preference, with *hot* and *adjacent* defined deterministically in §2.10.4. |
| `usage_weight`, `co_use_group`, `flow_stage` | `float`, `str`, `int` | O | Click frequency slot; co-use adjacency; position in the natural task sequence (browse→pick→apply). |

Row/position/page are deliberately **not** on this spec — arrangement lives in the owning
`PanelSpec.layout`, so the sim mutates exactly one structure per panel. The kernel-generated
callback is fixed for every action: resolve the declared authority (capability or tier, §2.2) →
defer per `defer_mode` → confirmation
round-trip if declared → invoke handler → route through the Result grammar → render — with the audit
row already emitted inside the workflow engine. Domains cannot reorder or omit these steps.

### 2.7 The Result grammar — WorkflowResult / MutationPreview / ConfirmationSpec

**Extends — never recreates — the shipped lifecycle vocabulary**
(`disbot/services/lifecycle/contracts.py`): `StepResult` (`:56`) is adopted **verbatim**;
`MutationPreview` is a strict superset of `LifecyclePreview` (`:66`); `WorkflowResult` is a strict
superset of `LifecycleResult` (`:77`), reusing the shipped constants verbatim (reversibility
`REVERSIBLE/COMPENSATABLE/IRREVERSIBLE`, `:40–42`; outcomes
`SUCCESS/PARTIAL/BLOCKED/DECLINED/DISCORD_FAILED`, `:48–52`).

**WorkflowResult** (kernel-owned, frozen) — every shipped `LifecycleResult` field appears with its
name, type, and default unchanged (verified `contracts.py:77–90`): `mutation_id` · `guild_id` ·
`domain` · `operation` · `outcome` (the shipped vocabulary, generalized across lanes) ·
`reversibility` (shipped constants) · `steps: tuple[StepResult,...]` (**the shipped `StepResult`,
reused as-is** — batched Discord operations genuinely need per-step results, so the lifecycle shape
*composes into* the general one rather than being discarded) · `committed_at` · `audit_emitted` /
`event_emitted` (both keep the shipped **publish-accepted-only** honesty), plus the
`applied`/`failed`/`first_error` helpers — and adds:
`lane: enum {scalar, binding, resource, governance, lifecycle, domain}` · `before` / `after` ·
`cache_invalidated` · `warnings` · `user_message` (S — copy). All S. Lifecycle-domain code and the
golden harness read the new type as the old one.

**Adapters, not rewrites, at the seams.** The kernel's four lane engines return `WorkflowResult`
natively. Where ported domain code still returns a shipped shape during Phase 4 —
`SettingsMutationResult` (`settings_mutation.py:149`), `LifecycleResult`,
`ProvisioningPreview`/`ProvisioningResult` (`resource_provisioning.py:207`/`:217`), the governance
write result, `TreasuryResult` (`treasury_service.py:61`) — a ~10-line, test-pinned classmethod
adapter (`WorkflowResult.from_settings(...)`, `.from_lifecycle(...)`, `.from_provisioning(...)`,
`.from_governance(...)`, `.from_treasury(...)`) bridges it. The mapping contract is fixed, not
per-implementer: every field the shipped shape shares with `WorkflowResult` maps **name-for-name**
(`mutation_id, guild_id, domain, operation, outcome, reversibility, steps, committed_at,
audit_emitted, event_emitted`); `lane` is set by the adapter (`from_settings ⇒ scalar`,
`from_lifecycle ⇒ lifecycle`, `from_provisioning ⇒ resource`, `from_governance ⇒ governance`,
`from_treasury ⇒ domain`); `before`/`after` fill from the legacy result's own before/after or
preview diff where it carries one, else `None`; `warnings` and the user-facing message carry over;
anything lane-specific stays reachable through a typed `source` field holding the **original
object** (never a stringly `extra` dict), so nothing is lost in translation. Each adapter is
**test-pinned against recorded legacy audit rows** — losslessness asserted, not asserted-about.
Renderers, the action executor, the audit spine, and the golden harness
consume exactly one grammar; `CurrencyMutationResult` is `WorkflowResult` with `lane=domain,
domain="economy"` plus `balance_after`/`escrow_ref` — not a sixth shape.

**MutationPreview:** `allowed` · `operation` · `summary` · `reversibility` ·
`planned_steps: tuple[PlannedStep,...]` · `diff: tuple[FieldChange,...]` (structured before→after) ·
`warnings` · `requires_confirmation` — the shipped `LifecyclePreview`/`ProvisioningPreview`
generalized; every lane engine exposes `preview()`/`apply()`, and the panel engine renders previews
uniformly.

**ConfirmationSpec:** `reversibility` (shipped constants; compile rule `irreversible ⇒ level ≥
confirm`) · `challenge: enum {button, typed_phrase, typed_hash}` (typed for irreversible) ·
`timeout_s: int = 60` · `re_check_actor: Literal[True]` (**frozen — confirmation always re-resolves
authority**) · `snapshot_before: bool = True` (before-state into the audit payload).

### 2.8 The remaining taxonomy primitives — how they attach

All attach to `SubsystemManifest` fields (§2.1), completing the synthesis §3 taxonomy:

- **GatewayListenerSpec** (`gateway_listeners`) — **new (linchpin spike G-1, 2026-07-02), the
  load-bearing amendment.** §2's original taxonomy declared bus events only; raw Discord gateway
  listeners (`@bot.event`/`on_message`/`on_reaction_add` etc.) had **no primitive at all** — and
  the spike found the operator band lives on exactly these: server logging alone consumes 8
  (`logging_cog.py:170–311`), plus karma's react-to-thank (`karma_cog.py:95`) and blackjack's
  reaction-join (`:410`). Without this spec, every gateway-driven feature is tier-3 escape-hatch
  code by construction, and the wiring map goes blind precisely where the current repo's own
  wiring is invisible today. Fields: `event: enum {on_message, on_reaction_add, ...}` (S),
  `handler: HandlerRef` (S), `gate: PredicateRef | None` (S — the shipped fast-gate-before-work
  pattern, checked before dispatch so the listener body only runs when the declarative gate
  passes). This single family alone moved the spike's logging-subsystem coverage from 79% to
  90%+.
- **AnnouncementRouteSpec** (`announcement_routes`) — **new (linchpin spike G-3, 2026-07-02).**
  The pattern "event class → templated embed → bound destination channel" recurs across
  server-logging routes, welcome greetings, and counters/spotlight, each currently hand-rendered.
  Fields: `event_class: str` (S), `template: EmbedFrameSpec | HandlerRef` (S),
  `destination: BindingRef` (S — the channel binding it targets). Declaring
  event+template+binding as data guts most of `server_logging.py`'s bespoke per-event rendering
  into one generic engine.
- **EventSpec / AuditEventSpec** (`events`): `name` (S — legacy names verbatim-frozen),
  `payload_schema: tuple[FieldSpec,...]` (S — must be a **superset** of the current kwargs; a compat
  check diffs against the recorded legacy payload inventory), `owner_subsystem` (S),
  `expected_subscribers: tuple[HandlerRef,...]` (S — generates the wiring map),
  `observability_only: bool = False` (S — the validator rule is hard: `expected_subscribers` may be
  empty **only** when this is `True`, red otherwise; marked events still enter the generated
  catalogue and the emit path — they are decision-trace telemetry, not dead names. Verified
  carriers: `governance.execution.allowed/denied`, per §1.2; the visibility/cache/cleanup trio has
  live subscribers and is declared as `EventSubscription`s instead),
  `audited: bool` (S — audited events flow through the workflow engine's `emit_audit_action`
  fan-out, the payload schema doubling as the audit-row shape, freezing the §5.3/§5.6 contracts),
  `redaction_ref` (S). `KNOWN_EVENTS` is a generated artifact. `event_emitted=True` still means
  publish-accepted, not delivered.
- **DiagnosticProviderSpec** (`diagnostics`): `name` (S), `lane: enum {sync, async}` (S),
  `timeout_ms` (S), `audience: enum {owner, admin, public}` (S), `redaction_ref` (S),
  `provider: HandlerRef` (S), `status_map` (S). Health-snapshot composition, audience projection,
  and persistent findings (mig-057 semantics) are kernel engines fed by these specs. The current
  import-time self-registration (`subsystem_schema.py:368–378` calls
  `_register_diagnostics_providers()` at module import — a hidden core→services edge, verified)
  becomes boot-time composition-root wiring.
- **ManagedTaskSpec** (`tasks`): `name` (S — the `<subsystem>:<purpose>` cancellation prefix,
  namespace kind `task_prefix`), `trigger: Interval | Cron | Event` (S), `handler: HandlerRef` (S),
  `error_policy: enum {log, disable_after_n, escalate_finding}` (S), `metrics_labels` (S).
- **StoreSpec** (`stores`): `table` (S), `sole_writer: HandlerRef | EngineRef` (S), `retention` (S),
  `checkpoint_class: enum {ledger, aggregate, session}` (S — drives the §5 collapse decision),
  `invariant_tag: str` (S — INV-F/G/K generate their AST fences from here; tags are
  namespace-reserved so the INV-K overload class cannot recur), `reader_domains` (S).
- **The game facet** (`game: GameFacet`) bundles kernel-defined shapes, domain-instantiated data —
  one vocabulary for all games:
  - **ChallengeSessionSpec:** `game_key` (S), `accept_timeout_s / turn_timeout_s / stale_after_s`
    (S), `escrow: CostVector | None` (S — routes through the economy engine's `bet_and_settle` seam,
    INV-F), `settle_once: Literal[True]` (S — the `SettleOnceMixin` contract,
    `utils/terminal_guard.py:44`, promoted to engine behavior on the *state* seam — the verified
    users are rps/creature_battle/deathmatch/blackjack_state, not the pvp view),
    `persistence: enum {ephemeral, checkpointed, authoritative}` (S — `GameSessionPersistencePolicy`),
    `stat_writes: tuple[StatWriteSpec,...]` (S — decision 10), `custom_id_scheme: Literal["g1"]`
    (S — §3), `refund_policy: HandlerRef` (S). Accept/decline/timeout/escrow/settle-once/rematch is
    written once for blackjack/RPS/deathmatch/creature/casino alike.
  - **LeaderboardSpec:** `board_id` (S), `stat_key` (S — **the compiler rejects any leaderboard
    whose `stat_key` lacks a declared writer** — decision 10's honesty mechanism), `metric` (S),
    `tie_breakers` (S), `scope` (S), `privacy` (S), `empty_state` (S — a game without persisted
    stats shows an explicit empty state, never a fabricated zero), `card_frame` (S),
    `display_order` (**A**).
  - **IdleAccrualSpec:** `resource_key` (S), `rate_model: LinearRate(per_hour, capacity) |
    FormulaRef` (S), `settle_field` (S), `collect_workflow: WorkflowRef` (S — transactional,
    idempotent).
  - **ItemCatalogSpec / RewardSpec / CraftingRecipeSpec / CollectionDexSpec / CostVector:** typed
    content declarations. Item keys are namespace-reserved (`item` kind), preserving the verified
    mining-inventory-as-generic-material-store coupling by declaring the cross-game refs explicitly
    (§5 hazard 9); recipes/rewards/dex entries reference versioned content files via
    `ContentSchemaSpec(version, path, validator_ref)`.
- **KnowledgeDomainSpec** (`knowledge`): `domain_key` (S), `context_ids: ContentSchemaSpec` (S —
  BTD6/ProjMoon entity IDs frozen per compat item 7), `sources: tuple[SourceProvenanceSpec,...]`
  (S — key, trust tier, freshness policy, license note, answer label),
  `ingestion: IngestionPipelineSpec` (S — ordered stage refs `fetch→parse→validate→audit→diff→pr→seed`;
  a refresh opens a reviewable PR, never pushes), `context_builder: HandlerRef` (S — emits typed
  `ContextBlock`s: domain/facts/source_label/freshness/max_chars), `intents: tuple[IntentRoute,...]`
  (S — NL-router registrations; this is what keeps the monolith dead),
  `task_profiles: tuple[TaskProfileSpec,...]` (S — `task` is the frozen `AITask` enum name;
  provider/model/response-mode/tool-budget/grounding/cache/eval-suite, folding today's `routing.py`
  + `feature_flags.py` + `AI_*` env scatter into declaration), `eval_suite: EvalSuiteSpec` (S —
  golden corpus path + `deterministic` provider pin + a content-version hash binding every data bump
  to a golden bump). Aligned with the in-flight KnowledgeDomain seam (Slice B) — the facet points at
  those registered seam objects; it does not compete with them.

### 2.9 Where declarativity stops — the escape hatch

The grammar's hard rule: **the manifest contains no logic.** No expressions, no conditionals, no
template language, no inline lambdas in the snapshot. The moment a declaration wants an `if`, it
becomes a **registered handler** — a plain async function in `domain/`, registered under a
namespace-reserved ref with a typed signature per slot kind (`WorkflowHandler`, `ProviderHandler`,
`RendererHandler`, `FormulaHandler`, `ValidatorHandler`, `IngestStageHandler`).

Three tiers, checked and counted:

1. **Generated (zero code):** kernel workflows parameterized entirely by specs — setting edit/reset,
   binding set/clear, resource provisioning, toggles, open-panel, pagination, standard confirm
   flows. Target steady state for admin/config surfaces: 100% tier 1.
2. **Declared-parameterized:** typed spec families covering a domain's regularity — rewards, linear
   accrual, recipes, leaderboards, dex filters, cost vectors, task profiles. Data, not code.
3. **Escape-hatch code**, each registration carrying `justification="…"` and appearing in a
   generated `escape_hatch_report.md`, with a ratchet checker that fails CI when a subsystem's
   tier-3 count grows without the justification diff being acknowledged in the PR. Discord-coupled
   escape-hatch UI (renderers, legacy views) lives in **`domain/<x>/ui/`** — the one domain sub-tree
   the layer table clears for discord (§1.1) — and is reachable **only through registered refs**
   resolved by the kernel at composition time, so it appears in the wiring map and needs neither a
   `kernel → domain` import nor a dynamic import (§1.6's ban stands unpierced):
   - **Game engines** — blackjack rules, RPS/deathmatch resolution, fishing/mining/farm math,
     creature battles: pure functions, no Discord/DB imports (the shipped `blackjack_engine`
     pattern, preserved).
   - **Game-board renderers** — `renderer_override` for stateful boards the block grammar cannot
     express.
   - **The `legacy_view` lane** — a `PanelSpec` may front a ported, hand-coded view class, re-homed
     under `domain/<x>/ui/` and registered as a `ViewRef`
     (`legacy_view=ViewRef("economy.ui.legacy_panel")`-style — never a dotted import path) so the
     manifest is immediately authoritative for metadata (help, navigation, namespace, compat
     pinning) while the ported class renders byte-identically. This is the **named contingency for a port that stalls against the
     panel engine — not the default path**: generated rendering is the default (the manifest must be
     the sim's real search space, or the standing owner rule is hollow); each `legacy_view` use is
     tier-3 with justification, tracked on the parity dashboard, one-way (a panel never flips back),
     and budgeted for elimination post-parity.
   - **AI prompt construction / system prompts** — reviewed string modules in `domain/ai/prompts/`,
     referenced by `TaskProfileSpec`, never embedded in the manifest.
   - **Redaction patterns, provider adapters, Discord API quirks** — `adapters/` code.
   - **Novel read-model providers** — complex queries behind `ProviderRef`s.

This is the answer to "a worse programming language": the grammar is deliberately not
Turing-capable and never grows conditionals. Pressure to express logic routes to tier 3, where it is
real, typed, testable Python — and its *quantity* is the visible metric of where the grammar needs a
new tier-2 spec family.

### 2.10 The simulability contract (critical)

**The manifest is the search space; the simulator is the search** (the standing owner rule). Six
parts:

1. **The classification is the grammar's.** S/A/O tags live in dataclass field metadata and the
   snapshot groups them, so the simulator's write surface is machine-derived, never guessed.
   The full arrangement vocabulary: `parent_hub`, `hub_group`, `ui_priority`, `PanelSpec.layout`
   (rows/positions/pages), `SettingSpec.group/advanced/panel_order`, `BindingSpec.group`,
   `CommandSpec.help_section_order`, `TableSpec.default_sort`, `LeaderboardSpec.display_order`.
   Everything else — identity, wiring, capability, copy — is S and invariant under simulation.
2. **Arrangement fields provably carry no meaning.** A kernel test renders the full surface under
   two random [A]-assignments and asserts the **identical component population** — the same set of
   registered custom_ids (taken over the union of every panel's pages, §2.3, so pagination
   differences don't matter), each with identical handler wiring and authority declarations. The
   test excludes exactly the **enumerated derivation targets** — hub-roster composition, the
   home-slot choice (§2.4), paged distribution — whose variation under [A] is those fields'
   documented purpose; the exclusion list is closed, lives in the test, and growing it is a spec
   change, not a test edit. The cheapest standing proof that the S/A split is real, run in CI
   forever.
3. **The sim's patch format cannot express a semantic mutation.** `sim/apply.py` writes
   `manifest/layout/<subsystem>.lock.json` overlays addressing [A] fields **by namespace id**; the
   compile loader rejects any overlay key not tagged [A]. Manifest source is never machine-mutated.
   **Provenance lives in the overlay**, per [A]-field-group, machine-written by `sim/apply.py`: each
   entry stamps `SimRef(record_id, input_hash)` or `Exempt(reason)` — the overlay being the sole [A]
   writer, provenance travels with exactly what it describes, and `check_sim_gate` reads it
   deterministically (auto-generated below-threshold `Exempt`s persist here too). And because no
   custom_id is ever derived from an [A] field (§2.4), a simulator bug can corrupt layout but
   structurally cannot corrupt semantics, custom_ids, or capability strings.
4. **The objective is data-grounded, with provenance — never vibes.** The manifest carries the
   seed slots and flags ([O] fields: `usage_weight`, `co_use_group`/`co_edit_group`/`co_open_group`,
   `destructive`, `flow_stage`, `depends_on`, `UsageProfile`); a **telemetry sidecar**
   (`sim/usage.snapshot.json`) carries what the objectives actually read: per-node counts keyed by
   namespace id **and the pairwise co-occurrence matrix** — `(kind, id_a, id_b) → count` for
   settings co-edits, action co-clicks, and panel co-opens, with the capture window and the session
   definition (same actor, same guild, within a 10-minute interaction session) recorded in the
   snapshot header. The declared `co_*_group` strings are **seed priors only**; measured pairs
   override them the moment they exist, so the sim rediscovers grouping from data rather than
   echoing its own seed. The aggregation from pairs to score terms is stated, not implied: *group
   cohesion* = the normalized share of pair mass falling intra-group; *co-edit / co-use distance* =
   the pair-mass-weighted mean placement distance. Telemetry is **captured from the live bot as an
   explicit Phase-0.5 sibling task** (scheduled with golden capture, before any freeze) and
   refreshed from the new bot's own kernel metrics after cutover. Every objective config carries a
   provenance tag — `weights: seeded | telemetry(period)` — and every scorecard a `confidence`
   field; **low-confidence arrangement changes are deferred**, and a feature with no telemetry runs
   on a neutral prior and stays `Exempt` until real signal exists. The sim never runs on invented
   data. Destructive placement is a hard constraint evaluated deterministically, not a weighted
   preference: never row 0, never adjacent to a **hot** action — *hot* = top usage-weight quartile
   within the panel (ties broken by namespace-id sort), *adjacent* = neighbouring column in the same
   row, or the same column in a vertically neighbouring row.
5. **Runs are deterministic and reproducible bit-for-bit.** `sim/run.py --space <sim_id>` loads
   `manifest.snapshot.json` + the sidecar (both hashed into the record), enumerates the space's
   mutation vocabulary (move component to row/page within `LayoutSpec`'s coverage rules, regroup
   settings across the declared pool, reassign `parent_hub` within the **derived** allowed set —
   hubs whose `HubSpec.minimum_tier` ≤ the subsystem's `visibility_tier`; an owner pin is an
   explicit `Exempt` on the field, never a hidden constraint — reorder children) under the hard
   constraints (Discord 5-row/25-component caps, roster bidirectionality, ≤2-hop hub nesting,
   destructive placement), scores with the
   space's stated objective (clicks-to-action weighted by usage; group cohesion via co-occurrence;
   co-edit distance; navigation depth), searches exhaustively when small and by fixed-seed annealing
   otherwise, and emits `sim/records/<sim_id>-<date>.json`: winning arrangement, per-term score
   breakdown, **top-5 alternatives**, input hashes, seed — the auditable "why it won."
6. **The sim-reviewed-or-exempt gate is a required check.** `tools/check_sim_gate.py` diffs
   [A]-fields against the merge base; any change without a matching new sim record or an explicit
   `Exempt(reason)` is red. The trigger threshold is **encoded, not vibes — and defined on semantic
   input size, invariant under arrangement**, so the gate cannot be escaped by re-partitioning its
   own output: a panel is below the floor at ≤ 4 *declared* actions + selectors (pre-layout, so
   paging can't split its way under), and a settings surface at ≤ 6 settings **per subsystem** —
   never per group, group membership being the [A] variable under gate. Below-floor nodes are
   auto-exempted (`Exempt("below threshold")`, written to the overlay), so a 2-button panel never
   drowns in ceremony; a subsystem over the floor needs a sim record for its whole settings surface
   however the seed partitions it. Navigation slots are permanently exempt by design (§2.4).

**Generated from the manifest** (the one-picture payoff, all via `tools/generate.py` over the
snapshot): help catalogue + projection; per-subsystem reference docs; the custom-id and event
inventories; the wiring map; the ownership map; property-test suites (every command routes to a
panel or a justified handler; every panel has navigation; every capability string parses; every
mutating action audits; every leaderboard has a stat writer; every persistent panel has static ids);
golden-harness scaffolding (a parity checklist + golden case stubs per command/panel); simulator
search spaces; the migration/compat checklists (§5); and the agent context packs (the
substrate-kit's `AgentContextPack`, fed by the manifest instead of a hand-maintained index).

---

## 3. The central namespace

### 3.1 One registry, typed kinds, derived — with a frozen compat core

`sb/namespace/` holds one reservation registry with typed kinds:

`command` (names + aliases, partitioned per `CommandSpec.kind` — prefix and slash are disjoint
Discord namespaces, §2.2 G-6), `custom_id`, `event`, `setting_key`, `subsystem_key`,
`capability`, `panel`, `handler_ref`, `task_prefix`, `stat_key`, `item_key`, `ai_task`,
`context_id`, `actor_type`, `invariant_tag`, `table`.

Two populations, two lifecycles:

- **Live reservations are a derived index with a veto** — computed by walking the manifests (plus
  the kernel's own manifest for kernel-owned identities like `nav:help`). There is **no
  hand-maintained reservation list** to update, so the registry cannot itself become a merge
  bottleneck or drift source.
- **`sb/namespace/legacy_reservations.json` is the frozen compat core** — a generated-once,
  hand-ratified inventory of every persisted legacy name: the 43 subsystem keys; the verbatim static
  custom_ids (the `nav:*`/`help*`/`settings_hub.*`/`settings_*` families **plus the eight `ai:*`
  ids — `ai:refresh`, `ai:diagnostics`, `ai:providers`, `ai:routing`, `ai:settings`, `ai:policy`,
  `ai:behavior`, `ai:tools`, verified at `disbot/views/ai/panel.py:120–249`; `support_report.py`
  declares none** — closing the synthesis §5.2 named gap); catalogued event names; the full
  `utils/settings_keys/*` key vocabulary (all 17 modules); capability strings; `AITask` member
  names; actor types. Entries are marked `compat=True`: claimable only by the recorded owner, never
  re-issuable, and deletable only with a migration note. **This file is the §5 backward-compat
  contract in machine-readable, CI-enforced form.** Every enumeration in this spec is
  **illustrative; the generated inventory from the frozen reference repo is the authoritative
  population** — it is what catches the long tail (e.g. `settings_needs_setup.back`,
  `settings_audit.back`, and the six-id `settings_command_access.*` family, all live in
  `views/settings/`) — and hand-ratification may only **add** annotations, never remove generated
  entries.

### 3.2 Declaring is reserving — a two-phase model; fail before merge and before boot

Declaring is reserving: a `CommandSpec` claims its name and every alias; a
`PanelSpec`/`PanelActionSpec` its custom_id; a `SettingSpec` its key; an `EventSpec` its name. But
the reservation index is **derived, never accumulated**: spec construction performs no global
registration — a global registry mutated at import would misfire on test doubles and re-imports and
make collision detection import-order-dependent. The phases, earliest wins:

1. **At import — intra-manifest only.** Each record validates its *own* identities in
   `__post_init__` (stdlib-only, no shared state): two same-named commands or duplicate action ids
   inside one manifest raise immediately, with a real traceback at the declaration site. This is why
   `sb/spec/` stays a dependency-free leaf (§1.1) — local checks need no registry.
2. **In CI — the full cross-manifest set.** `tools/manifest_compile.py` walks every manifest into
   the snapshot; `tools/check_namespace.py` validates the snapshot (pure data — why `sb/namespace/`
   imports neither `spec` nor manifests, §1.1) as part of the required check. A collision fails the
   PR naming both claimants and both source files, deterministically, independent of import order.
   The deterministic `git merge-tree` machinery carried from the current repo **runs the same
   validation on the merge result**, so two individually-green PRs that collide together are caught
   before either merges.
3. **At boot** — `app/` recompiles and re-validates the full set and exits `FAILED_STARTUP` with a
   structured two-claimants report **before any network connection**. The old failure mode
   (crash-loop after connecting, discord.py raising at command registration) becomes a red deploy
   with a named culprit pair.

The Q-0211/BUG-0030 collision class is cross-manifest, so its kill sites are phases 2 and 3 — both
ahead of any production impact; phase 1 exists so the cheapest, most local mistake still dies at
import with zero machinery.

**Collision policy:** hard error, no warning tier, no arbitration, no grandfathering for new names.
Command names and aliases share one pool and match case-insensitively (Discord is); custom_ids,
events, settings keys match byte-exact. Subsystem keys are frozen verbatim — renaming one is
rejected outright (compat item 1: rename = data loss).

### 3.3 Tombstones

The registry supports `reserve_tombstone(kind, value, reason, provenance)` — names that must never
be claimed: the bare symbol **`ActionSpec`** (decision 1), retired event names, and dropped command
names whose muscle memory deserves a helpful "renamed to X" error for one deprecation window rather
than silence. Tombstones are the namespace's institutional memory; each carries its provenance
reference, so the rename resolution is permanent by mechanism, not tribal memory.

### 3.4 The versioned custom_id scheme (decision 6)

- **Static ids** (hubs, settings, nav, help, the AI panel): the legacy strings survive **verbatim**
  via `custom_id_override` + `compat=True` entries. New static ids follow `<panel_id>.<action_id>`
  and are namespace-minted.
- **Dynamic session ids** (game challenges, per-session boards): scheme
  **`g1:<game_key>:<session_id>:<action>`** — `g1` is the scheme-version token, parsed by the kernel
  custom-id router before dispatch; the namespace reserves each game's `g1:<game_key>:` **prefix**,
  so two games can never mint overlapping session ids. `session_id` is the `game_state` checkpoint
  key, so restart recovery re-binds components to persisted sessions (the id routes to a recovered
  session; it is never itself the authority). A future shape change mints `g2:` while the router
  keeps the `g1` parser for a deprecation window; an unrecognized or retired version yields a polite
  "this session has expired — start a new one" response and disables the message's components —
  schema evolution can never crash routing or strand a clickable corpse.
- **Router precedence is fixed, and the id families cannot collide by construction.** Dispatch
  order: (1) exact match in the static registration table — legacy verbatim ids and canonical
  `<panel_id>.<action_id>` ids live in **one** table, and both populations share the namespace's
  single `custom_id` kind, so they are byte-exact-unique at compile time and cannot race at runtime;
  (2) versioned dynamic parse — an id beginning with a scheme token (`g<N>:`) routes to that
  version's parser; (3) no match → the polite-expiry response. Two compile checks keep the
  populations disjoint forever: a legacy `custom_id_override` may not begin with a scheme-version
  token, and every new canonical mint collides against the frozen legacy set in the shared pool.
- During Phase-5 cutover a small shim maps in-flight legacy dynamic ids best-effort; game sessions
  are short-lived and restart-lossy today by design, so the shim window is days, not months.
  In-process session state otherwise keeps today's restart semantics; money-safety continues to rely
  on the ported refund/recovery paths (compat item 9).

### 3.5 Relation to Python symbol collisions — two mechanisms, deliberately

The reservation registry governs **runtime string identities**. It structurally *cannot* catch the
Q-0200 class — a second same-name `def` silently shadowing the first never *registers* anything; the
second definition just wins at import. So the namespace ships with a **static AST companion**,
`tools/check_symbol_shadowing.py` (evolved from the substrate-kit's portable namespace guard):

- no module defines the same top-level `def`/`class` name twice;
- no two modules define the same public name within one package unless one is an `__init__`
  re-export;
- grammar type names (`*Spec`, `*Result`, the lexicon of load-bearing types: `PanelActionSpec`,
  `AutomationActionSpec`, `SettingSpec`, `BindingSpec`, `SubsystemManifest`, `WorkflowResult`,
  `CapabilityDecision`, `AIGateway`, …) are globally unique across the repo, and any new
  `class ActionSpec` anywhere is red;
- symbols matching a namespace reservation may not be re-defined outside their canonical module.

Conversely, the AST pass cannot catch runtime-composed identities (a custom_id assembled from
parts, a key read from data). **Neither mechanism subsumes the other — this is written into the
architecture doc explicitly, so a later agent does not delete one believing the other covers it.**
Both report through one failure surface.

---

## 4. Settings model

### 4.1 SettingSpec is the only declaration path — enforced, not aspirational

The strategy's verified finding: the shipped pipeline is already correct (~100 settings flow
`SettingSpec → settings_registry → resolve_setting / SettingsMutationPipeline`, with coerce →
validate → capability → DB-write + audit in one transaction), but it is **not authoritative** — 40
raw callsites bypass it, including a read inside a view (`views/setup/sections/moderation.py:408`),
and ~14 keys have no spec at all. In the rebuild:

- There is **no public raw-KV API**. The KV store functions are private to `adapters/db/`, callable
  only by the kernel settings engine. `kernel/settings` is the **read side only**: it exposes
  exactly `resolve(guild, subsystem, name)`; every write goes through the workflow engine's scalar
  lane — `kernel/workflow` owns all four mutation lanes, settings never writes (§1.3). `resolve()`
  keeps the preserved chain and makes it **tri-state**: per-guild explicit → global explicit →
  default. Stored values are explicit-`true` / explicit-`false` / unset; an explicit stored value
  always wins, and `activation` (§4.4) is consulted **only at the unset terminus** — `on_by_default`
  and `off_until_opt_in` are constants; `on_when_keyed` resolves once at boot (secret presence);
  `on_when_bound` is dynamic, re-evaluated per read against the binding store's cached state (the
  binding lane's cache invalidation keeps it coherent and cheap; never persisted, so it flips with
  the binding in both directions). Non-bool specs terminate at the shipped static `default`,
  unchanged. The 40 bypass callsites have no equivalent because the functions they called do not
  exist publicly.
- The **~14 spec-less keys** gain mechanical `SettingSpec` declarations at port time; type and
  default are extracted from their inline callsite defaults by a script whose output diff is
  reviewed (the one behavior-affecting step; goldens cover the read paths, and this lands in the
  first Phase-4 slice while the oracle is freshest).
- **Seam authority is checked, not asked:** a generated test asserts every consumed setting is
  declared and every declared setting is consumed, and a store-level fence asserts no SQL against
  the settings table exists outside the store module. A CI completeness check asserts every key
  observed in the production dump has exactly one owning spec or alias — the orphan-key gap closed
  by force.

### 4.2 Three lanes, kept separate

Scalar (`SettingSpec` → settings store), pointer (`BindingSpec` → `subsystem_bindings` semantics),
provisionable (`ResourceRequirement` → provisioning lane with preview + explicit confirm, never
silent auto-create). The preserve rule holds — the lanes differ in storage, mutation contract, and
widgetry, and the workflow engine keeps them distinct strategies. What *is* unified is everything
around them: one authority seam, one audit fan-out, one Result grammar, one generated settings-panel
family. The compiler cross-validates the lanes: a `BindingSpec.resource_link` must name a declared
requirement; a scalar spec with `input_hint="channel"` that should be a binding is flagged.

### 4.3 AI's typed policy folds in

Today AI's on/off lives three ways — env `AI_ENABLED` + a KV scalar + typed `ai_guild_policy`
columns kept in sync by a projection service, with two independent default declarations (the
verified "outgrew itself" case). New model: these are ordinary `SettingSpec`s with
`storage=typed_column` — the typed table remains the physical store (it is read per-request on the
hot path), but declaration, defaults, capability, audit, and UI all come from the one spec in the
`ai` manifest. The projection service and the duplicate defaults die. `AI_ENABLED` demotes to
exactly one role: a **process-level operator kill-switch** read by the gateway — emergency-off
overrides every setting and policy, with one defined scope: it kills **live provider execution and
external side effects**, while the offline `deterministic_provider` and the diagnostics surfaces
stay executable, so the socket-denied eval suites and health panels have identical, defined
semantics with the switch thrown (an emergency-off you can still see and test through). It is no
longer a default source; it is documented on the spec and surfaced in diagnostics — provider
behavior is never again hidden behind env with no runtime projection.

### 4.4 Safe-default-ON, reconciled (decision 5)

The new `activation` axis on the extended SettingSpec:

- **`on_by_default`** — active out of the box. For features whose blast radius is reversible
  in-guild output: diagnostics surfaces, help/discovery, passive quality-of-life features.
- **`on_when_bound`** — **active the instant its required binding exists; inert before.** The
  reconciliation with "no silent auto-create": server logging defaults here per category (reversing
  the verified `DEFAULT_ENABLED = False`) — the feature's logic runs, the completeness rule reports
  a *pending destination* finding, the settings hub and panel surface "logging is ON — choose a
  channel" with a one-click bind (and, where `ResourceRequirement.offer_on_enable=True`, an
  *offered* provisioning preview) — but **nothing posts and nothing is created** until the operator
  binds or confirms. Discoverability without unasked mutations.
- **`on_when_keyed`** — active iff the deployment carries the named secret. AI passive answering
  and review loops default here: the presence of `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` *is* the
  bot-owner's cost consent, so guilds get AI on by default wherever the deployment can serve it.
- **`off_until_opt_in`** — off until explicit per-guild operator action, **forced by compile rule
  whenever `external_side_effects=True`**. Image moderation is the canonical case: it sends
  member-posted images to OpenAI (the external call lives in
  `core/runtime/ai/providers/openai_moderation.py`; the scanner service explicitly does not call
  OpenAI — synthesis correction 6), a privacy boundary no bot-owner key can consent to on a guild's
  behalf. The gate is grammar, validator-enforced at manifest load — and the flag it keys on is
  **verified, not merely declared**: provider adapters that reach a paid external API carry an
  `egress=external_paid` marker at the port (declared once, in `adapters/`, asserted by a trivial
  test over the modules importing external SDK clients), and the `external-cost-honesty` validator
  in `manifest-validate` walks each setting's declared refs — handlers, task profiles,
  `visible_when` gates — and reddens any spec gating a path that reaches an egress-marked adapter
  without `external_side_effects=True`. A ported or new setting cannot *forget* its way past the
  privacy gate; losing the flag is a red check, not a silent default — the namespace's
  derived-not-declared discipline applied at the most safety-critical field.

**Why `activation` has no usable constructor default — the trilemma, resolved.** Any blanket
default would be wrong: defaulting ON would activate image moderation wherever the egress flag had
been forgotten (the privacy breach); defaulting OFF would silently reproduce today's
discoverability failure (the exact thing the owner is reversing); a hard-required field would break
every ported constructor call (§2.5's compat promise). So the field defaults to `None` at the
dataclass — ported `schemas.py` calls parse unchanged — and the **compiler refuses `None` on any
`bool`-typed spec**: the port must consciously choose each feature's posture before the manifest
compiles. The port script pre-fills the *legacy-equivalent* posture from the shipped `default`, and
every safe-default-ON flip is a reviewed diff against that baseline — the same diffs that feed the
owner's one-page "what flips ON" cutover review below.

**The authority invariant is untouched and orthogonal:** `capability_required` (empty = ADMINISTRATOR
floor, verbatim from `capability.py` and the `subsystem_schema.py:129–134` docstring) governs *who
may change* a setting; `activation` governs *what the value is before anyone changes it*.
Default-ON never weakens mutation authority and never provisions a resource. Rollout honesty:
because data comes across whole (§5), the importer maps stored rows **verbatim into the tri-state
model** — a legacy stored `false` imports as explicit `false` and keeps winning `resolve()` forever,
a stored `true` as explicit `true`, and only rows *absent* under the old bot arrive `unset` (the
sole population an activation-derived default touches). Safe-default-ON changes **unset guilds
only**, and the cutover checklist includes a one-page owner-facing diff of exactly which features
flip ON for unset guilds.

### 4.5 Legacy-KV → binding route-truth + alias map (decision 3)

Binding rows become the **only route-truth** for every Discord-pointer config; legacy KV keys become
**declared read-aliases**:

1. Each affected `BindingSpec` lists its `legacy_settings_key_aliases` — the exact old KV keys
   (logging's channel-id settings, etc.) that historically stored the pointer. The alias map is
   *data in the manifest*, so the migration is generated, testable, and auditable — never a
   hand-written script's private knowledge.
2. The one-time importer (§5) converts existing KV pointer rows into binding rows.
3. During the shadow-run window a read-through shim satisfies a legacy-key read by dereferencing the
   binding, with a residue metric per fallback hit; the shim is removed when the metric flatlines.
4. There is **no write path to legacy pointer keys** in the new repo (there is no API for them,
   §4.1); writes go through the binding lane only.
5. Scalar legacy keys map via `SettingSpec.legacy_keys`: the key *strings* remain the canonical
   persisted vocabulary (interface preserved — compat item 5) while the 17 `settings_keys` constant
   modules collapse into the manifests.

---

## 5. Data model + backward-compat contract

### 5.1 The new schema shape

The schema is **derived from the manifest**: `StoreSpec` declarations generate the table inventory,
the sole-writer fences, and retention jobs. Three checkpoint classes decide physical shape:
**ledgers** (append-only: `economy_audit_log`, mod logs, the audit spine, `ai_review_log`) and
**aggregates** (balances, XP, karma, inventory, treasury, tickets, bindings, settings, health
findings, presets, BTD6 provenance including `btd6_data_blobs.sha256`) are first-class tables;
**session** state collapses into `game_state`-style checkpoints. The migration-019 precedent
(`019_drop_rps_matches.sql`, verified — per-match state moved into `game_state_service`, table
dropped) generalizes into a written rule, the **checkpoint test**: *if the row's loss costs a user
money or an operator an audit answer, it is a table; if it costs a player a rematch, it is a
checkpoint.* Per-user game stats become first-class (new, decision 10). In-process live-play state
(counting, word-chain, casino rounds) either checkpoints or is declared
`GameSessionPersistencePolicy.ephemeral` explicitly — never implicitly lossy. The same two-layer
memory split governs the AI domain: **AI conversation/approval state is session-class** (short-lived
thread state in checkpoints, resumable across restarts where declared), while its durable stores
(`ai_review_log`, `ai_answer_presets`, provenance) are ledgers/aggregates — an AI dialog never
smuggles long-term truth into thread state or vice versa.

### 5.2 The migration decision (decision 8) — fresh chain + one-time importer, with a named fallback

The new repo starts its own migration chain at `0001` and does **not** carry the verified
103-migration chain forward. A standalone `tools/importer/` reads the live DB (frozen at cutover) by
its *table shapes* — not its migration numbers — maps rows through the manifest's generated alias
maps and store specs, and writes the new schema. The numbers are load-bearing only inside the old
repo's migration runner; what is externally observable is the *data* (keys, rows, hashes), which the
importer preserves — while carrying the chain forward would freeze the exact schema fragmentation
the rebuild exists to shed, and would leave the manifest describing tables it didn't shape.

**Importer properties (the risk work, front-loaded):** idempotent (upsert by natural key); ordered
by dependency (guilds → settings/bindings → economy/XP/karma ledgers → inventory/game aggregates →
tickets/treasury → AI stores → provenance); **dry-run mode emitting a reconciliation report** (row
counts + per-table checksums + key coverage, old vs new) that the **owner reviews before the real
run**; hard abort on any unmapped settings key, unknown subsystem key, or orphaned binding — and
every abort class is **machine-readable**: the dry-run report enumerates a fixed set of mismatch
classes (`unmapped_key`, `unknown_subsystem`, `orphaned_binding`, `checksum_drift`,
`row_count_drift`, `key_coverage_gap`), each with a distinct hard stop-code, so "reconciliation
failed" is never a judgment call read out of a log — the fallback trip-wire (below) keys on
stop-codes, not vibes.
Ledger/aggregate tables import **name-stable** where cheap (`subsystem_bindings`,
`economy_audit_log`, `ai_review_log`, `ai_answer_presets`), shrinking the diff surface. The importer
is **built and golden-tested in Phase 4 against a sanitized production snapshot fixture** — never
written at cutover — and the golden harness is replayed against the new bot on imported data as the
real acceptance test.

**The named fallback:** if the importer's dry-run reconciliation ever fails owner review, the
documented contingency is the conservative cutover — vendor the numbered chain unchanged, point the
new bot at the same schema, and defer every collapse to golden-guarded post-parity migrations
(two-step: transform, then a later drop, so rolling back the drop never loses data; any pre-cutover
migration applied to the live DB must be proven old-bot-tolerable by running the frozen old suite
against the migrated schema in CI). This lane is specified now so switching to it mid-program is a
decision, not a redesign.

Shadow-run discipline either way: the new bot shadow-runs against a **restored snapshot**, never the
live DB — exactly one bot writes the production database at all times; cutover is a deployment flip;
rollback re-deploys the old worker against its untouched database for a bounded window.

### 5.3 Disposition of every §5 hazard class

| # | Hazard class (synthesis §5) | Disposition | Mechanism |
|---|---|---|---|
| 1 | Persisted `subsystem_registry` keys | **Keep verbatim** | All 43 keys frozen in `legacy_reservations` (`compat=True`); the manifest compiler rejects unknown/renamed keys; `HUBS` rosters generated from `parent_hub`, so the CI-tested bidirectional rule is true by construction. |
| 2 | Persistent `custom_id` strings | **Keep verbatim (static) / migrate (dynamic)** | Static set frozen verbatim in `legacy_reservations` — `nav:help`, the hub-keyed `nav:hub:<hub>` constants (dispatched by router lookup at click time, never minted from `parent_hub` — §2.4), `help:back`, `help_categories:select`, the `settings_hub.*` family, `settings_missing_bindings.back`, `settings_invalid.back`, `settings_subsystem.*`, `settings:back`, `settings_needs_setup.back`, `settings_audit.back`, the six-id `settings_command_access.*` family, hub/panel ids of the ported views, **and the eight verified `ai:*` ids** (§3.1) — with the generated inventory from the frozen repo authoritative over any enumeration here (ratification adds, never removes). Dynamic session ids move to the versioned `g1:` scheme with router dispatch, polite expiry, and a short cutover shim (§3.4). |
| 3 | Event names + payload shapes | **Keep verbatim** | Names frozen in the namespace; payload schemas typed as **supersets** of current kwargs with a compat diff against the recorded legacy inventory; publish-accepted semantics preserved. The `governance.visibility.changed` / `governance.cache.invalidated` / `governance.cleanup.changed` trio ships as **declared `EventSubscription`s** (live subscribers verified at `core/runtime/__init__.py:181–183` — §1.2); the genuinely subscriber-less `governance.execution.allowed/denied` pair carries `observability_only=True`, not dropped. |
| 4 | DB migrations / tables (incl. the 019 precedent) | **Migrate** | Fresh chain `0001+` + one-time importer with owner-reviewed dry-run reconciliation (§5.2); session-shaped state collapses per the checkpoint test; ledgers/aggregates import row-for-row, name-stable where cheap; the conservative carry-the-chain cutover is the specified fallback. |
| 5 | Settings keys | **Keep + alias** | Key strings verbatim as the canonical persisted vocabulary (namespace `setting_key`, compat-frozen — all 17 modules harvested); ~14 orphan keys gain specs with reviewed extracted defaults; pointer keys become declared read-aliases behind bindings (§4.5). **Hard invariant preserved verbatim: empty `capability_required` ⇒ ADMINISTRATOR floor, never anonymous.** |
| 6 | Actor types / audit invariants | **Keep verbatim** | `actor_type` strings namespace-reserved; `setup_delegate` sole-minting declared on the setup-apply workflow spec with its AST fence ported (`test_setup_delegate_actor_boundary`); INV-F/INV-G/INV-K sole-writers declared in `StoreSpec.invariant_tag` with generated fences (INV-K unambiguous, decision 4); audit payload field sets frozen and diffed by `check_compat_frozen` (§6); platform-owner bypass preserved. |
| 7 | AI/knowledge stable identifiers | **Keep verbatim** | `AITask` member names reserved (`ai_task` kind); BTD6/ProjMoon context IDs frozen via `ContentSchemaSpec`; the normalized-question-key function ported **byte-compatible and golden-pinned** (mig 100/102 rows must keep resolving); `ai_review_log`/`ai_answer_presets` imported keys-intact; `btd6_data_blobs.sha256` provenance carried; YouTube cache TTL + video-id normalization declared in its `KnowledgeDomainSpec`. |
| 8 | Env/secrets behavior | **Keep verbatim (behavior); redesign (CI credentials)** | Same env names and meanings; `AI_ENABLED` demotes to kill-switch (stricter, never looser); **image moderation calls no external API until guild opt-in** — `off_until_opt_in` forced by the `external_side_effects` compile rule (§4.4); repo-side tokens move to OIDC/GitHub-App (§6) — the one deliberate change, ops-side only. |
| 9 | Versioned product content | **Keep verbatim + version headers** | `data/fishing/fish.json`, `data/creatures/creatures.json`, `data/projmoon/limbus/*.json`, `data/btd6/{towers,heroes}.csv` (repo root) copied as-is under `ContentSchemaSpec` version validation; **data bump ⇒ eval-golden bump enforced by content-version hashes** in `EvalSuiteSpec` (decision 9). The mining-inventory-as-generic-material-store coupling is preserved *explicitly*: one `ItemCatalogSpec` namespace with item keys unchanged and cross-game refs declared rather than incidental. |

### 5.4 The data-migration plan shape

(1) Manifests land with the compat sets frozen → (2) importer dry-run against a production snapshot;
owner reviews the reconciliation report → (3) golden harness replayed against the new bot on the
imported snapshot — the real acceptance test → (4) cutover: freeze old bot, final import delta, flip
the Railway service → (5) bounded rollback window with the old repo + pre-import snapshot intact.
The importer never writes to the old schema.

**The shadow window is measured, not felt — the compat scoreboard.** During shadow-run and the
rollback window, one generated report tracks per compat artifact: unknown-`custom_id` hits (clicks
the router could not dispatch), legacy-alias read residue (§4.5's shim metric), event payload-shape
diffs against the frozen inventory, importer residue by stop-code class, actor-type/audit-shape
mismatches, and golden-parity status. Cutover-exit criteria are scoreboard lines (residue flatlined,
zero unknown-id hits, goldens green), so "the window is over" is a read-off, not a feeling.

---

## 6. Control plane

**GitHub-native from day one; the PAT accretion dies.** Repository **rulesets** (not classic branch
protection) on `main`: required checks below, linear history, no force-push,
auto-delete-head-branches. **OIDC / GitHub-App auth** for every workflow that acts on the repo — the
verified 7-workflow `ROUTINE_PAT` single-point-of-failure does not carry over. Secret scanning +
push protection + Dependabot security updates on at repo creation. `CODEOWNERS` maps `sb/spec/`,
`sb/namespace/` (including `legacy_reservations.json`), `sb/kernel/workflow/`, `parity/`, and the
compat-contract doc to owner review — the surfaces where a wrong merge is expensive.

**Required checks (one workflow, named gates):**

1. `code-quality` — format/lint/mypy/pytest under the pinned interpreter; tool versions pinned in
   one place (the workflow installs from the pin file, structurally removing the current repo's
   three-way pin-drift class).
2. `manifest-validate` — compile + snapshot drift + namespace collisions (including on the
   merge-tree result, §3.2) + manifest validators (never-strand, destructive-requires-confirmation,
   `external_side_effects ⇒ off_until_opt_in` plus the `external-cost-honesty` egress-reachability
   check (§4.4), activation-explicitly-chosen (§4.4), layout coverage (§2.3),
   leaderboard-has-writer, ownership completeness) + payload-superset checks.
3. `architecture` — layer table, lazy-import ban, complexity budget, symbol-shadowing pass.
4. `sim-gate` — sim-reviewed-or-exempt (§2.10.6).
5. `golden-parity` — the acceptance oracle. `parity/parity.yml` lists every subsystem as
   `pending | ported`; `ported` subsystems run their goldens (the `parity/` harness — see below —
   against a real Postgres service container in CI) and **must** be green — any regression is a
   hard failure; `pending` subsystems are expected-red and *reported*, not failing — so the check
   is required from day one, red-until-parity is CI-enforced, flipping `pending → ported` is the
   port PR's deliberate last commit, and **green is a one-way door**. The file doubles as the
   owner's live port-progress dashboard. **CI requirement (linchpin spike, item 4, 2026-07-02):**
   this repo's own `code-quality` workflow runs no Postgres service container, which is why the
   harness skips there today — the new repo's CI must provision one from K10 onward, or
   `golden-parity` cannot actually run in CI at all.
6. `check_compat_frozen` — diffs the pinned compat artifacts (legacy custom_id list, subsystem keys,
   event literals, `AITask` names, audit payload field sets) against the manifest export; any drift
   from the §5.3 contract is red until the compat doc is explicitly amended **with owner sign-off**.

**The runtime control surface (the dashboard) is a client, never a second write path.** The current
repo ships a separate FastAPI dashboard service; the rebuild keeps that split but makes the contract
explicit — a gap the external review round correctly flagged. Rule: **every dashboard write goes
through the same audited workflow lanes as a Discord interaction** (authority resolved for the
acting operator, preview/confirm where declared, audit row, event, cache invalidation — the seams
of §1.3), exposed over one versioned internal control API; the dashboard never receives DB
credentials for direct writes, and its read models are the same generated projections the bot
renders from. The concrete API contract (endpoints, auth, which workflows are exposed) is a
**required K7/K8-entry deliverable** — the interaction runtime must not land while the dashboard's
write path is undefined, or side-channel orchestration regrows.

**The harness itself** is captured in Phase 0.5 against the live bot (command-in → embed/DB-out).
**Naming correction (linchpin spike, item 2, 2026-07-02):** the mechanism actually built and
running today at [`parity/`](../../parity/README.md) is **fake HTTP over the real discord.py state
machine, against a local Postgres** — not "testcontainers + dpytest or equivalent" as earlier
drafts assumed; it needs no new test dependencies and gets real dispatch fidelity by driving
discord.py's own state machine. **Composition with evals (item 3):** the harness and the `evals/`
corpus are not the same asset merged — **evals stay the AI-answer oracle** (`tests/evals/
harness.py` drives `AIGateway` directly, judging answer quality), while **the golden harness owns
the deterministic command/panel surface** (embed/DB assertions, no AI judgment involved); the two
compose (a subsystem can need both) rather than one subsuming the other. The new repo consumes the
harness **read-only as a pinned external dependency — the goldens live outside the new repo's write
reach**, so neither bot can silently rewrite its own oracle; golden updates are explicit, reviewed
PRs to the harness repo. Telemetry capture (the sim's objective sidecar) is the scheduled Phase-0.5
sibling task (§2.10.4). **Determinism-pinning budget (item 5):** capturing commands deterministically
required pinning eight distinct nondeterminism classes (documented in the harness's determinism
ledger); scheduled-loop capture (background tasks, not just interactions) will pay a comparable
pinning cost again — budget for it rather than treating command-capture's cost as the whole bill.

**Carries over from the current repo:** the deterministic `git merge-tree` conflict check (extended
with namespace validation on the merge result), GitHub-native auto-merge armed on green at PR-open,
the self-healing watcher routines (re-authored on app tokens as versioned `WorkflowRoutineSpec`s),
and the session-log discipline. **Dies:** every PAT-powered workaround; bespoke auto-merge machinery
beyond the native enabler; retired review-gate labels; unverified-check accretion (every adopted
tool enters via the Q-0105 provenance-header convention — dated, "unverified until proven," with an
explicit delete-if-unreliable note).

---

## 7. Regenerated binding docs

Small, provenance-separated, partly generated, budget-capped by a checker — the direct answer to the
verified ~25,300-word boot tax and the rules-that-narrate-their-own-history failure mode. The
substrate-kit bootstraps the skeleton at repo creation (its templates, ledger format,
orientation-budget checker, namespace guard, and seam-authority checks are Phase-0 deliverables).

| Doc | Source | Budget |
|---|---|---|
| `CONSTITUTION.md` | hand (kit template) — working agreement, autonomy rails, rule-change protocol | ≤ 150 lines |
| `docs/architecture.md` | hand prose + **generated** layer table (rendered from the checker's config — doc and checker cannot drift) + the two-mechanism namespace note (§3.5) | ≤ 250 lines |
| `docs/runtime-contracts.md` | hand — lifecycle, bus, interaction, Result grammar (§1.2) | ≤ 200 lines |
| `docs/manifest-reference.md` | **fully generated** from `sb/spec/` docstrings + the snapshot | n/a (generated) |
| `docs/ownership.md` | **generated** from `StoreSpec` + invariant tags | n/a (generated) |
| `docs/domains/<x>.md` | **generated** per-subsystem folio (surface, settings, events, stores, sim provenance) | n/a (generated) |
| `docs/compat-contract.md` | the frozen §5.3 table + pinned artifacts — **amendable only with owner sign-off** (backed by `check_compat_frozen`) | ≤ 200 lines |
| `docs/decisions.md` | the distilled ledger: one machine-parseable status format, ordered IDs, `supersedes:` links, promote/retire as first-class ops; seeded from the Phase-1 router distillation with zero orphaned citations. **Entry depth (owner-decided, Q-0214.4, 2026-07-02): verdict + 2–3 lines of rationale + provenance link; full deliberation lives in git/PR history.** `supersedes:` is a machine-readable field so "what is the current rule?" is a query, never prose archaeology | append-only |
| `docs/current-state.md` | living dated snapshot, today's discipline | ≤ 150 lines |
| `docs/orientation.md` | the reading router | ≤ 120 lines |

Rules state their current value only; provenance lives in `docs/decisions.md` via `[D-NNNN]` links —
never narrated inline. **Stamp discipline (from the 2026-07-02 retention session's measured spread
pattern — Q-0089 accumulated 176 live-doc citations as per-file footers):** a D-number is cited
**once, at the rule's canonical home**; every other doc links *the rule's home*, not the decision —
stamps are immutable pointers, never content, so they never need rewriting when content moves.
`tools/check_orientation_budget.py` (a required-check sub-gate) fails CI when
the hand-written boot-read set exceeds **7,000 words total** (vs ~25,300 today), so the docs cannot
silently regrow — and the kit's **context-economy engine**
([`memory-retention-and-context-economy-plan-2026-07-02.md`](memory-retention-and-context-economy-plan-2026-07-02.md)
§10, posture per Q-0214) supplies the retention half: per-class windows, tombstone/stub semantics,
and the checker+actuator pair, so the corpus stays bounded by construction, not by cleanup heroics.
Generated docs carry the `NOT SOURCE OF TRUTH — edit the manifest` marker (the context-compiler
convention, kept).

---

## 8. The ten open questions — decisions

At a glance (full rationale in the numbered entries below):

| # | Question | Decision (one line) |
|---|---|---|
| 1 | `ActionSpec` rename | UI primitive = `PanelActionSpec`; automation record = `AutomationActionSpec`; bare name tombstoned |
| 2 | One manifest vs split registries | One `SubsystemManifest` (thin spine + typed facets), extending the shipped `SubsystemSchema` |
| 3 | Legacy-KV vs binding route-truth | Bindings authoritative; old KV keys become declared read-aliases; no legacy write path |
| 4 | INV-K overload | Karma keeps INV-K; the task-spawn invariant becomes INV-T; invariant tags namespace-reserved |
| 5 | Safe-default policy | Four-valued `activation` axis; logging `on_when_bound`, AI `on_when_keyed`, image moderation compiler-forced `off_until_opt_in` |
| 6 | Custom-id versioning | Static ids frozen verbatim (incl. the eight `ai:*`); dynamic session ids = versioned `g1:` scheme |
| 7 | Where `AIGateway` lives | `kernel/ai` with a hard no-upward-imports rule; misfiled metrics moves to `kernel/observability` |
| 8 | Data migration | Fresh chain from `0001` + one-time owner-reviewed importer; carry-the-chain is the trip-wired fallback |
| 9 | Ingestion + eval determinism | One ingestion pipeline; `deterministic_provider` only for evals, socket-deny enforced; data bump ⇒ golden bump |
| 10 | Leaderboard honesty | Stat writes ship inside the game-session primitive; a leaderboard without a declared writer fails compile |

1. **The ActionSpec rename.** **`PanelActionSpec`** for the UI primitive; the shipped automation
   metadata record ports as **`AutomationActionSpec`**; the bare name **`ActionSpec` is tombstoned**
   in the namespace and AST-forbidden, resolved repo-wide in the kernel's first PR before any domain
   adopts the primitive. Unification rejected — the field sets are disjoint and the lifecycles
   unrelated. Renaming the automation class is free: its persisted contract is the `action_kind`
   *strings* mirrored by migration 032's CHECK constraint (verified), not the Python symbol — and
   retiring the generic bare name removes the magnet that invites the next collision.
2. **One manifest vs split registries.** **One `SubsystemManifest`** — a thin identity spine with
   typed facets — extending the shipped `SubsystemSchema` and absorbing `SUBSYSTEMS` + `HUBS`.
   `RouteRegistry` dies as a name (routing is a projection); `KnowledgeDomainSpec` survives as the
   `knowledge` facet aligned with the in-flight Slice-B seam; per-user participation stays a sibling
   registry per the shipped doctrine (`subsystem_schema.py:31–37`). One source, several read models,
   no god-record.
3. **Legacy-KV vs binding route-truth.** **Bindings are authoritative** for every Discord pointer;
   legacy KV keys become declared read-aliases (`BindingSpec.legacy_settings_key_aliases`), converted
   once by the importer, read-through-shimmed only during the shadow window with a residue metric,
   with **no write path** to the old keys. Scalar key strings stay canonical via
   `SettingSpec.legacy_keys` (§4.5).
4. **INV-K disambiguation.** Karma keeps **INV-K** (it sits in the user-facing sole-writer family
   with INV-F/INV-G, matching the `ownership.md` + `karma_service` pairing); the
   `architecture.md:136` task-spawn invariant is renamed **INV-T**. Invariant tags are
   namespace-reserved (`invariant_tag` kind), so the overload class cannot recur. Doc-label rename
   only; no persisted footprint.
5. **Settings safe-default policy.** The four-valued `activation` axis: `on_by_default` for
   reversible-output features; **`on_when_bound`** for binding-dependent features (logging — active
   the instant a channel is bound, inert and *offering* before); **`on_when_keyed`** for AI (the
   deploy key is the bot-owner's cost consent); **`off_until_opt_in` forced by the
   `external_side_effects` compile rule** (image moderation — the guild-privacy gate as grammar),
   with the flag itself verified by the `external-cost-honesty` egress-reachability check. The axis
   is a **required conscious choice** on every bool-typed spec (constructor-defaulted `None`,
   compiler-refused — the §4.4 trilemma resolution) and acts **only on unset values** in the
   tri-state `resolve()` (§4.1). The empty-capability ⇒ ADMINISTRATOR-floor invariant — at its
   shipped, mutation-pipeline scope (§2.2) — and no-silent-auto-create are untouched and orthogonal
   (§4.4).
6. **Custom-id versioning.** Static ids frozen verbatim in `legacy_reservations` — **including the
   now-enumerated `views/ai/` set** (`ai:refresh/diagnostics/providers/routing/settings/policy/
   behavior/tools`, verified `panel.py:120–249`; `support_report.py` declares none). Dynamic session
   ids use versioned **`g1:<game_key>:<session_id>:<action>`** with per-game prefix reservation,
   central router dispatch, graceful unknown-version expiry, and a short cutover shim (§3.4).
7. **Where AIGateway lives.** **Metrics moves; the gateway lands in `kernel/ai/` with a hard
   no-upward-imports rule.** The root cause of `gateway.py:51` is that `services/metrics.py` is
   misfiled observability (verified: sole external import `prometheus_client` with a fallback) — it
   relocates to the cross-cutting `kernel/observability` leaf, dissolving the break at the root. The
   gateway extends field-for-field into `kernel/ai`, which may import nothing above itself
   (the break *class* is dead, not just the instance); the blessed single-module import seam
   (successor of `services/ai_gateway.py:25`) is preserved and linter-enforced; the typed contracts
   live dependency-free in `sb/spec/ai.py` (§1.4).
8. **Data migration off fixed numbers.** **Fresh chain from `0001` + a one-time idempotent importer**
   with owner-reviewed dry-run reconciliation; ledgers/aggregates import name-stable; the 019
   precedent generalizes into the checkpoint test via `StoreSpec.checkpoint_class`
   (session → checkpoints; ledgers/audit/aggregates → tables). The conservative carry-the-chain /
   zero-migration cutover is retained as the **specified fallback** with an explicit trip-wire: it
   activates if the dry-run reconciliation fails owner review (§5.2).
9. **Ingestion + eval determinism.** Confirmed: **`deterministic_provider` is the only sanctioned
   eval provider**, and the seal is mechanical — CI runs unit + eval suites under a socket-deny
   fixture, so no unit/eval path can reach a live API by construction. One `IngestionPipelineSpec`
   for BTD6/ProjMoon/YouTube over shared `SourceProvenanceSpec`s (refresh opens a PR, never pushes);
   **data bump ⇒ golden bump** enforced by content-version hashes in `EvalSuiteSpec`; the
   `RedactionContract` (every request field and tool result crosses the redactor) is test-proven per
   `AIRequest` field.
10. **Leaderboard honesty.** Stat writes ship **inside the game-session primitive**
    (`ChallengeSessionSpec.stat_writes`), and **the compiler rejects any `LeaderboardSpec` whose
    `stat_key` lacks a declared writer.** Honest boards therefore land per-game as each game ports —
    never deferred wholesale, never faked; a game without persisted stats shows an explicit empty
    state, never a fabricated zero.

---

## 9. Build order

### 9.1 Phase 3 — the kernel (refining the synthesis §6 ten-step kernel)

The synthesis order is kept with three deliberate changes, and the sequence is **topologically
sorted against the §1.1 layer table** (each step depends only on those above it): the **namespace
moves to the front** (everything else declares into it), the **grammar precedes the DB seam** (the
schema is derived from `StoreSpec`s, so the grammar is the spine and the DB a consumer), and
**observability lands with the substrate in K0** — the layer table makes it a cross-cutting leaf
below the DB seam, so building it after its first consumer would invert the topology. Each step
lands with its checker, so the required-check set arms incrementally.

- **K0 — repo substrate + control plane + observability.** Substrate-kit bootstrap (doc skeletons,
  ledger, orientation-budget checker), rulesets + OIDC, the named-gate workflow, CODEOWNERS, and
  `kernel/observability` (metrics + structured logging — the leaf everything below imports, §1.1).
- **K1 — namespace registry** + tombstones (bare `ActionSpec` reserved in the first PR) +
  `legacy_reservations.json` generated from the frozen reference repo and hand-ratified +
  `check_namespace` + the symbol-shadowing AST pass.
- **K2 — the grammar** (`sb/spec/`, every §2 dataclass extending the shipped types
  verbatim-field-first), S/A/O metadata, manifest compiler + snapshot, validators (never-strand,
  destructive-confirmation, external-cost, leaderboard-writer), and the grammar's kernel tests —
  including the **arrangement-invariance test** (§2.10.2).
- **K3 — db seam + fresh migration runner** (`0001` schema core) + `StoreSpec` ownership projection
  + generated seam-authority fences.
- **K4 — EventBus + generated catalogue** + subscriber-drift check (`observability_only` rule,
  §2.8).
- **K5 — lifecycle + task supervisor** (7 phases, admission gate, INV-T fence).
- **K6 — authority** (`actor_holds_capability` + `CapabilityDecision` ported field-for-field;
  capability strings namespace-validated).
- **K7 — the workflow engine**: audit spine + `WorkflowResult`/`MutationPreview`/`ConfirmationSpec`
  + the four lane strategies + settings resolution (§4.1–4.3). The largest kernel band.
- **K8 — the interaction runtime**: custom-id router (versioned `g1:` scheme + the frozen legacy
  alias table), `PanelRuntimeView`, EmbedFrame, Table/List/Browser, selectors, navigation, generated
  settings panels, help-as-projection, diagnostics + health findings.
- **K9 — `kernel/ai`**: gateway extended in place, contracts in `spec/ai`, redaction, provider port
  + adapters, deterministic provider, eval harness scaffold, the socket-deny egress guard.
- **K10 — the loops**: `sim/` runner + objective configs + `check_sim_gate`; golden harness wired as
  `golden-parity` with the all-`pending` expectation file; `check_compat_frozen`. **The repo is born
  red on parity and green on everything else.**

### 9.2 Phase 4 — port order, red-until-parity

Per subsystem, the loop is invariant: **declare the manifest (sim-optimized or exempt) → implement
`service.py` + `engine.py` behind the audited seam → run the importer mapping for its tables against
the snapshot fixture → flip `pending → ported` as the PR's last commit.** Order, by dependency then
blast radius:

1. **settings + diagnostic + help** — the platform proves itself on itself; exercises all four
   lanes, the generated settings panels, and the ~14 orphan-spec extraction while the oracle is
   freshest.
2. **admin + server_management + moderation + logging + automod/security/welcome/counters** — the
   operator spine; the generated-panel payoff lands here (subsystems that today have settings but no
   views get panels for free); binding route-truth + the alias map; `EVT_MOD_ACTION` payload pins;
   **safe-default-ON logging flips here** (the showcase).
3. **economy + inventory + treasury** — INV-F territory; the coupled item namespace registers; the
   audit spine's hottest tables import name-stable.
4. **XP + karma + community** — INV-G/INV-K; the `xp.level_up → community_spotlight` wiring becomes
   declared.
5. **games** — wager-workflow games first (blackjack, RPS: escrow/settle-once seam, `g1:` ids,
   `ChallengeSessionSpec`, the richest goldens), then checkpoint games (mining, fishing, farm,
   creatures — idle accrual, catalogs, dex), then casino/counting/word-chain/deathmatch — each
   landing its stat writes (decision 10).
6. **AI + knowledge domains** — NL router + per-domain intents; review/preset stores (normalizer
   golden-pinned); BTD6 (the mature exemplar), then ProjMoon, then YouTube through the shared
   ingestion pipeline. Deliberately last among the majors: the AI/ingestion runtimes are the
   **outer ring** — the deterministic platform kernel and the operator/economy/game bands prove the
   grammar and the parity loop first, so AI-runtime complexity (provider behavior, session state,
   ingestion) never holds the platform hostage.
7. **tickets, role menus, spotlight, BTD6 ops, long tail** — by golden coverage; parallelizable.

The old repo serves production throughout as the frozen oracle. Post-parity bands (explicitly after
cutover, each golden-guarded): remaining `legacy_view` eliminations, any 019-style collapses
deferred by the fallback lane, escape-hatch reductions, telemetry-refreshed sim re-runs.

### 9.3 The first three simulator passes

0. *(Pre-pass, Phase 3 — engine exists today.)* **File-ordering** via CodeGraph community detection
   over the frozen repo's call/import graph (the session banner already reports `drift 48% /
   modularity 0.4712`) — feeds `sb/domain` package boundaries. The standing rule's proof pass, zero
   new tooling.
1. **Hub topology** — `parent_hub` + `hub_group` + `ui_priority` across all subsystems, reassignment
   bounded by the derived tier rule (§2.10.5) and touching no custom_id (§2.4) (objective:
   navigation depth + semantic cohesion + tier separation; weights from Phase-0.5 telemetry). The
   biggest [A] space; run before port band 2 so admin surfaces land in sim-chosen homes. Decides the
   new bot's top-level shape; the owner ratifies the "why it won" report.
2. **Settings-hub grouping** — `group/advanced/panel_order` over the full ~114-key surface, assigned
   across the hand-declared group pools (§2.5) (objective: co-edit distance + dependency order +
   edit frequency, aggregated from measured pairs per §2.10.4). Before band 2's generated settings
   panels.
3. **Dense-panel layout** — `PanelSpec.layout` for the server-management and games hubs, the two
   largest component sets under the 5×5 caps, with the destructive-placement constraint doing real
   work (engine precedents: the BTD6 #1617 and reaction-roles #1612 sims). Before those panels flip
   `ported` — **with the §2.10.4 confidence rule doing real work here**: if telemetry is still thin
   at band-2 time, the pass runs on the neutral prior, and a low-confidence winner **defers to the
   legacy layout as the seed arrangement** (an explicit `Exempt`) rather than blocking or reshuffling
   the port — dense-panel optimization is a post-telemetry win, never a parity gate.

---

## 10. Risks + what the owner is approving

### 10.1 Top risks and mitigations

1. **Golden-harness coverage is the ceiling on safety.** Parity-green means "matches captured
   behavior"; uncaptured flows can regress silently. *Mitigation:* per-subsystem coverage notes
   required at every `pending → ported` flip (uncovered flows listed, never assumed); capture
   continues against the live bot until freeze; the `evals/` corpus and payload-superset checks
   backstop the AI and event surfaces; the frozen old repo remains the arbitration oracle
   post-cutover.
2. **Engine bugs have total blast radius** (one panel-engine defect breaks every panel).
   *Mitigation:* engines land in Phase 3 with their own golden + property suites before any feature
   exists; generated property tests exercise every spec instance; the port order proves the platform
   on low-risk surfaces (settings/help) first; the `legacy_view` contingency bounds a stall. Two
   operational additions from the external review round: each engine family gets a **canary
   subsystem** (the first, lowest-risk consumer that ports on it and soaks in shadow-run before the
   band ships wide), and the panel engine carries a **per-renderer-family runtime kill-switch** — an
   operator toggle that drops an engine-rendered family back to its `legacy_view`/minimal rendering
   while a defect is diagnosed, so an engine bug is a degraded surface, not a dead bot.
3. **Importer correctness at cutover** — the least rehearsable step and the one irreversible failure
   class. *Mitigation:* built and golden-tested in Phase 4 against a sanitized snapshot; dry-run
   checksum reconciliation **owner-reviewed before the real run**; name-stable ledger imports; the
   carry-the-chain fallback is specified with an explicit trip-wire; the old repo + pre-import
   snapshot stay a bounded-window rollback; shadow-run never touches the live DB.
4. **Confidently-wrong sim layouts** (a guessed objective — the sim doc's named failure mode).
   *Mitigation:* objective provenance tags (`seeded` vs `telemetry(period)`); scorecard `confidence`
   with low-confidence deferral; neutral-prior + `Exempt` until real telemetry exists; destructive
   placement as a hard constraint; the owner ratifies the first three passes' "why it won" reports;
   exemption is always available below the encoded threshold.
5. **The grammar becomes a worse programming language.** *Mitigation:* structurally bounded — no
   logic in the manifest ever; behavior only via typed handler refs; the tier-3 escape hatch is
   counted, justified, and ratcheted; recurring tier-3 patterns promote to tier-2 spec families, not
   grammar conditionals. The design succeeds if 80%+ of surfaces are tier 1–2, not 100%.
6. **A bespoke flow resists the generated-panel model** (a dense game board, the setup wizard).
   *Mitigation:* `renderer_override` and the `legacy_view` lane are first-class, justification-
   required outcomes; games are sequenced late so the grammar hardens on operator surfaces first.
7. **Session-id routing at scale is unproven here** (dynamic `g1:` dispatch). *Mitigation:*
   prototyped in K8 with a load test before any game ports; fallback is per-session registered views
   behind the same codec — the scheme, not the mechanism, is the contract.
8. **The namespace/manifest becomes ceremony** and slows the ~100-PR port. *Mitigation:* every
   validation is derived from data (no hand-maintained lists to update); exemption paths (sim gate,
   complexity file, escape hatch) are explicit and cheap; manifest modules are per-subsystem files,
   so parallel agents collide at compile, not at merge.
9. **Compat contract misses something unfrozen.** *Mitigation:* `legacy_reservations` is generated
   from the frozen reference repo, not hand-listed; `check_compat_frozen` diffs the pinned artifacts
   on every PR; goldens replay on imported production data; the shadow-run window catches the
   remainder.

### 10.2 What the owner ratifies by approving this spec

1. **The architecture:** kernel engines + manifest-declared domains; **no hand-written views/cogs
   layers** (generated panels; counted escape hatches); the §1.1 layer table with its two
   zero-tolerance rules; metrics in `kernel/observability`.
2. **The rename set:** `PanelActionSpec` + `AutomationActionSpec`, bare `ActionSpec` tombstoned;
   the task-spawn invariant renamed **INV-T** (karma keeps INV-K).
3. **One `SubsystemManifest`** (thin spine + typed facets) extending the shipped
   `SubsystemSchema`/`SettingSpec`/`BindingSpec`/`ResourceRequirement` verbatim-field-first; hub
   rosters, help, catalogues, ownership, and wiring as generated projections.
4. **The manifest format:** Python frozen dataclasses → committed canonical JSON snapshot →
   sim-owned layout lock overlays; the S/A/O field classification (copy is semantic); the
   **sim-reviewed-or-exempt required check** with encoded thresholds and the arrangement-invariance
   proof test.
5. **The namespace:** declaring-is-reserving over a **derived** index (§3.2's two-phase model —
   intra-manifest duplicates fail at import; the full cross-manifest set fails in CI, including on
   the merge result, and again at boot before the gateway connects); the frozen
   `legacy_reservations.json` compat core (generated inventory authoritative; ratification add-only);
   tombstones; the two-mechanism split (registry + AST shadowing pass) as permanent law.
6. **The custom-id scheme:** all static ids verbatim (including the eight `ai:*` ids); versioned
   `g1:` dynamic session ids with graceful expiry.
7. **Safe-default-ON** via the four-valued `activation` axis — an explicit per-spec choice, never
   silently inherited (§4.4) — logging `on_when_bound`, AI `on_when_keyed`, **image moderation
   `off_until_opt_in` (compiler-forced, egress flag checker-verified)** — with the
   ADMINISTRATOR-floor mutation invariant preserved verbatim at its shipped scope (§2.2: the
   `audience_tier` lane covers member-facing surfaces), no silent auto-create, effects on unset
   guilds only, and the owner reviewing the one-page "what flips ON" diff before cutover.
8. **Bindings as route-truth** with declared legacy-KV aliases; `SettingSpec` as the only settings
   declaration path (no public raw-KV API; seam authority checker-enforced).
9. **Fresh schema from `0001` + the one-time importer** with owner-reviewed dry-run reconciliation
   (the §5.3 disposition table in full, including the checkpoint test) — and the carry-the-chain
   zero-migration cutover as the specified fallback if reconciliation fails review.
10. **`kernel/ai` placement** with the facade-only seam, the no-upward-imports rule, and the
    no-live-API eval guard (deterministic provider only, socket-deny enforced).
11. **The control plane:** rulesets + OIDC from day one; the six named required gates including
    `golden-parity` (red-until-parity, one-way green, goldens pinned outside the repo's write reach)
    and `check_compat_frozen` (compat amendments require owner sign-off); PAT machinery retired.
12. **The regenerated doc set** with the ≤ 7,000-word orientation budget (checker-enforced),
    generated architecture/ownership/manifest/domain docs, and the provenance-separated decision
    ledger.
13. **The build order** (§9): the K0–K10 kernel sequence, the seven-band port order with the
    per-subsystem red-until-parity loop, and the first three simulator passes (owner ratifies each
    pass's "why it won" report).
14. **The deferral discipline:** post-parity bands (remaining `legacy_view` flips, escape-hatch
    reductions, any fallback-lane collapses) are accepted as catalogued, ratcheted debt — approving
    this spec approves *not* doing them before cutover.

What the owner is **not** approving here (still gated per the standing rules): the Phase-5 cutover
execution and final data migration (owner-verified), live verification/rollback, and any per-PR
data step a change names. This spec is the design gate; no new-repo code exists until it is
approved.

### 10.3 Pre-cutover operational contracts + deliberate non-goals

**Operational contracts — specified during Phase 4, required before cutover** (the external review
round correctly flagged these as present-but-implicit; they are now named deliverables, not
solved-in-this-document):

1. **An SLO set per runtime surface** — interaction-response latency, event-delivery lag, task-loop
   health, AI-answer latency/degraded-rate — with the kernel observability metrics (K0) as the data
   source and the diagnostics panel as the read surface. "Healthy" becomes a number before the flip.
2. **Rate-limit and quota budgets** — a declared budget per external edge: Discord REST/gateway
   (the adapters already own the choke points), and per AI provider via `TaskProfileSpec`'s
   tool/cache budgets; provider spend surfaces in diagnostics, not in a bill surprise.
3. **A DR runbook beyond the rollback window** — the specified rollback covers the bounded window;
   the runbook covers the day after it closes: which stores restore from what (ledgers/aggregates
   from Postgres backup, sessions accepted-lossy per their declared class), importer re-run
   semantics on a partially-diverged database (idempotent by natural key — verified against the
   snapshot fixture), and the decision tree for re-freezing.
4. **A retention/deletion policy per store** — `StoreSpec.retention` (§2.8) already carries the
   field; the pre-cutover deliverable is the filled-in inventory (what holds member content, how
   long, how a guild-leave or member-erasure request cascades) — the privacy complement to the
   image-moderation opt-in gate.

**Deliberate non-goals of this design** (decided now so they are not re-litigated mid-port):

- **No vector database in phase 1.** Nothing in the parity scope needs vector retrieval; if a
  post-parity AI feature does, the first step is `pgvector` inside the existing Postgres (one
  datastore, one ownership model, one backup story) — a dedicated vector service is a later,
  evidence-gated escalation, never a parity dependency.
- **No durable-execution engine (Temporal-class) in phase 1.** The workflow engine's lanes are
  short-lived, transactional, and previewable; nothing in scope is a multi-day saga. If one appears
  post-parity, it gets its own design pass.
- **No external agent framework for the platform loop.** The interaction loop stays
  application-owned (the whole point of the kernel); AI-domain internals may adopt session/handoff
  patterns behind the gateway, but the platform never delegates its loop to a framework.
- **No model pinning in this spec.** Provider/model choices are `TaskProfileSpec` data, decided at
  the Phase-4 AI band against then-current models and prices — a design document is the wrong place
  to freeze a model name.

---

## 11. Glossary

Plain-word definitions; each term links the section that specifies it precisely.

| Term | Meaning |
|---|---|
| **manifest** | The one typed file per feature declaring everything it has (commands, panels, settings, events, tables, help). The single source the engines and generators read. (§2.1) |
| **spec** (e.g. `PanelSpec`) | One typed record inside a manifest describing one thing — a panel, a button, a setting. (§2) |
| **kernel** | The small set of engines written once — panels, settings, workflow/mutations, help, events, tasks, diagnostics, AI gateway — that interpret manifests. No feature code lives here. (§1.1) |
| **engine** | A kernel component that turns specs into runtime behavior (e.g. the panel engine renders `PanelSpec`s). (§0) |
| **domain** | A feature's actual business logic (game rules, moderation actions) — plain code behind typed handler refs. (§1.1) |
| **panel** | An interactive message the bot posts: an embed plus buttons/menus. (§2.3) |
| **custom_id** | The hidden identity string on every Discord button/menu; Discord sends it back on click, and the router dispatches on it. Persisted in old messages — which is why legacy ids are frozen verbatim. (§3.4) |
| **capability** | A named permission string (e.g. `logging.settings.configure`) resolved through the authority seam on every click. (§2.2) |
| **audience tier** | The member-facing authority lane (`user/trusted/staff/…`) for surfaces that aren't config mutations. (§2.2) |
| **binding** | A stored pointer from a feature to a Discord object ("logging posts to #mod-log"). The pointer lane of config. (§2.5) |
| **provisioning** | The confirm-first lane that creates Discord resources (channels/roles) — never silently. (§4.2) |
| **lane** | One of the four write paths in the workflow engine: scalar setting / binding / resource / governance. (§1.3) |
| **namespace** | The central registry where every name (commands, custom_ids, events, keys) is reserved at declaration; collisions fail CI and fail before boot. (§3) |
| **tombstone** | A name deliberately reserved so nobody can ever claim it (e.g. bare `ActionSpec`). (§3.3) |
| **golden harness** | Recordings of the *current* bot's observable behavior (command in → embed/DB out), replayed against the new bot as the acceptance oracle. (§6) |
| **red-until-parity** | A ported feature's CI check stays failing until it matches its goldens; flipping to green is deliberate and one-way. (§6) |
| **checkpoint** | Short-lived session state (a game in progress) saved via the game-state store rather than its own table. (§5.1) |
| **importer** | The one-time tool that copies all data from the live database into the new schema, with an owner-reviewed dry-run first. (§5.2) |
| **shadow-run** | The new bot running against a restored data snapshot (never the live DB) while the old bot still serves production. (§5.2) |
| **cutover** | The deployment flip from old bot to new, after goldens + scoreboard are green; rollback stays available for a window. (§5.4) |
| **compat scoreboard** | The generated report that makes the shadow window measurable (unknown-id hits, alias residue, payload diffs…). (§5.4) |
| **S / A / O tags** | Every manifest field is semantic (meaning — hand-authored), arrangement (layout — simulator-owned), or objective (data the sim's scoring reads). (§2.0) |
| **sim gate** | The required CI check: any arrangement change ships with a simulator record or an explicit exemption. (§2.10.6) |
| **lock overlay** | The machine-written file holding the simulator's arrangement choices — structurally unable to touch meaning. (§2.0) |
| **escape hatch** | The counted, justified path for hand-written code where the grammar can't express something (game boards, ported legacy views). (§2.9) |
| **telemetry sidecar** | The usage-data snapshot (click counts, co-use pairs) the simulator's objectives read — measured, never invented. (§2.10.4) |
