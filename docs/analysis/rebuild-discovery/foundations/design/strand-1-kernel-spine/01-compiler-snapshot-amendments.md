# Strand 1 · Kernel spine · ① Manifest compiler + committed snapshot + amendment registry

> **Phase-B foundational design.** Docs-only. Designs the linchpin kernel function to buildable
> depth against the frozen upstream contracts (design-spec §2.0/§2.1/§2.7/§2.10/§3.2/§9.1;
> router Q-0219…Q-0237; FJ Fable-5). A fresh agent builds this from this file + those contracts
> making **zero** further design decisions, except the one surfaced owner call in §8/§9.
>
> **Spot-verified seams (2026-07-04, against shipped source):** the spine runs BACKWARD today —
> `command_manifest.build_command_manifest` (`command_manifest.py:176-207`) projects the *live*
> ledger, `panel_manifest.build_panel_manifest` (`panel_manifest.py:180-213`) *instantiates and
> introspects* registered views; `manifest_reconciliation.reconcile` (`manifest_reconciliation.py:66`)
> defers button→command binding (`:21-27`); `command_tree_sync.auto_sync_if_changed`
> (`command_tree_sync.py:96-138`) is a **path set-diff** (`local == remote`; `added = local-remote`),
> not a hash; `SubsystemSchema` (`subsystem_schema.py:234`) declares only
> `settings/bindings/resource_requirements/domain_panels` (`:270-276`); boot is sequential non-fatal
> glue (`bot1.py:1180-1249`). `tools/manifest_compile.py`, any `*.snapshot.json`, `sb/`, and
> `rebuild-amendments.yml` are all **absent**. **Seam correction carried (Q-0120, FJ L-4/L-25):**
> there is **no `WorkflowResult` class and no `disbot/core/contracts.py:48-52`** — the real result
> vocab is `disbot/services/lifecycle/contracts.py` (`LifecycleResult:77`, `LifecyclePreview:66`,
> `StepResult:56`, outcomes `SUCCESS/PARTIAL/BLOCKED/DECLINED/DISCORD_FAILED:48-52`, reversibility
> `REVERSIBLE/COMPENSATABLE/IRREVERSIBLE:40-42`) plus the dispatch analogue `StageResult`
> (`message_pipeline.py:181`). This spec consumes the §2.7 grammar as *that* seam, never the
> fabricated type.

---

## 1. Summary + the exact undesigned gap

**Already frozen upstream — not re-designed here (anti-pad).** §2.0 froze the hybrid format
(dataclasses author · committed `manifest.snapshot.json` interchange · `layout/*.lock.json` [A]
overlays), the snapshot's *properties* (sorted keys, stable ordering by `key`/`panel_id`/`action_id`,
stable hash, callable→registered-ref, CI-regenerated=drift-red), the [S]/[A]/[O] field-role tags, and
that `tools/manifest_compile.py` is the producer. §2.1 froze the `SubsystemManifest` root record
(extends `SubsystemSchema`). §3.2 froze the two-phase *declaring-is-reserving* posture (import /
CI / boot; collision → `FAILED_STARTUP`). §9.1 placed "manifest compiler + snapshot, validators
(never-strand, destructive-confirmation, external-cost, leaderboard-writer)" at **K2**. This spec
does **not** restate any of that — it builds the machine those sentences assume.

**The gap this closes** (five things the spec names but never makes buildable):

| # | Undesigned gap (prose today) | This spec delivers |
|---|---|---|
| G-a | "validators (…)" — a bare list | §3.2 the **ordered validation-pass pipeline** — 9 named passes, dependency-ordered, with per-pass reads / emits / verdict |
| G-b | "there is no compiler"; the arrow runs backward | §3.3 the **forward generation contract** + §3.4 the **three-way parity oracle** (snapshot ⇄ built-runtime ⇄ Discord-remote), reusing `command_tree_sync`'s path set-diff |
| G-c | scattered "compile error / drift = red / FAILED_STARTUP" | §3.5 the **failure taxonomy** — 7 classes → CI-red / `FAILED_STARTUP` / gated-sync |
| G-d | "a dropped `StoreSpec`…" (unwritten) | §3.6 **store-completeness reconciliation** — a lost store is **owner-gated, never silent** |
| G-e | amendment IDs collided 3× in one audit (FINAL-REVIEW §3; runtime-logic #92/#217) | §3.7 the committed **`rebuild-amendments.yml` + `check_amendments.py`** — the SOLE minting authority, built **before** Gate-0 folds G-9…G-24 |

One sentence: **this turns the manifest from a thing the runtime reflects into the thing the runtime
is compiled from, gated so a green compile provably means "the running bot is exactly what the
manifest declares."**

---

## 2. Files / modules it becomes

| New path | Layer | Role |
|---|---|---|
| `tools/manifest_compile.py` | `tools/` (never imported at runtime) | The compiler: runs the §3.2 pass pipeline, emits `manifest.snapshot.json`. CLI + library. |
| `sb/spec/refs.py` | `sb/spec/` (stdlib-only leaf) | The **ref value types** (`HandlerRef`/`PanelRef`/`ViewRef`/`PredicateRef`/`EngineRef`/`WorkflowRef`/`ProviderRef`, each a frozen `name:str`) + the `@handler(name)`… registration decorators + the module-global **ref table** (`name → callable`). §3.1. |
| `sb/spec/roles.py` | `sb/spec/` leaf | `Role` enum (`S`/`A`/`O`) + `field_role()` metadata helper + `snapshot_field_roles()` (the `field_roles` map the arrangement-invariance test and sim read). |
| `sb/app/boot_gate.py` | `sb/app/` (composition root; may import all) | The boot gate: leg-A recompile-parity, leg-B build-parity, leg-C remote-parity; calls the lifecycle `fail_startup` seam. §3.4. |
| `tools/check_amendments.py` | `tools/` | The ~40-line uniqueness/consistency checker over `rebuild-amendments.yml`. Required check. §3.7. |
| `manifest.snapshot.json` | repo root (committed) | The interchange artifact. Schema §4/§5. |
| `docs/planning/rebuild-amendments.yml` | committed | The amendment minting authority. §3.7. |
| `sb/namespace/store_retirements.yml` | committed (append-only, owner-signed) | The store-drop sign-off ledger the §3.6 pass reads. |

**Shipped paths this RETIRES** (the backward spine — replaced by the forward one):

| Shipped path | Fate |
|---|---|
| `disbot/core/runtime/command_manifest.py` (`:176-207` live-ledger projection) | **Retired.** Commands are declared in `sb/manifest/<x>.py`, projected forward into the snapshot; nothing reflects `bot.commands`. |
| `disbot/core/runtime/panel_manifest.py` (`:180-213` instantiate-and-introspect) | **Retired.** Panels are `PanelSpec`s; no view is instantiated to learn its own shape. |
| `disbot/core/runtime/manifest_reconciliation.py` (`reconcile`, `DANGLING_PANEL_ACTION`) | **Superseded.** The deferred, heuristic button→command check (`:21-27`) becomes the real `never_strand` compile pass (§3.2 P6), because `PanelActionSpec` *declares* the binding. |
| `disbot/services/command_tree_sync.py` (`auto_sync_if_changed`) | **Partly reused, partly retired.** `_local_paths`/`_remote_paths` set-diff machinery is **lifted verbatim** into the leg-C oracle; the "sync whenever local≠remote (local = reflected runtime)" heuristic is retired — `local` becomes the **snapshot projection**, and the sync direction is always snapshot→Discord. Kill-switch `AUTO_SYNC_COMMANDS` carries forward. |

---

## 3. The complete public contract

### 3.1 The ref-table resolution contract (I own)

Every callable a spec points at (a command handler, a panel renderer override, a predicate gate, an
engine, a workflow, a provider) is carried in the manifest as a **ref value object** holding only a
string name, never the callable — this is what makes the snapshot 100% data (§2.0).

```python
# sb/spec/refs.py  — stdlib-only leaf
@dataclass(frozen=True)
class HandlerRef:      name: str          # kind="handler"
@dataclass(frozen=True)
class PanelRef:        name: str          # kind="panel"    (a panel_id)
@dataclass(frozen=True)
class ViewRef:         name: str          # kind="view"     (a re-homed legacy view class, §2.9 tier-3)
@dataclass(frozen=True)
class PredicateRef:    name: str          # kind="predicate"(a gate, §2.8 GatewayListenerSpec.gate)
@dataclass(frozen=True)
class EngineRef:       name: str          # kind="engine"
@dataclass(frozen=True)
class WorkflowRef:     name: str          # kind="workflow" (returns the §2.7 WorkflowResult grammar)
@dataclass(frozen=True)
class ProviderRef:     name: str          # kind="provider" (a read-model / data provider)

AnyRef = HandlerRef | PanelRef | ViewRef | PredicateRef | EngineRef | WorkflowRef | ProviderRef

_REF_TABLE: dict[tuple[str, str], Callable] = {}   # (kind, name) -> callable

def handler(name: str) -> Callable[[F], F]:        # + panel/predicate/engine/workflow/provider twins
    """Decorator used in sb/manifest/<x>.py to bind a ref name to a callable."""
def resolve(ref: AnyRef) -> Callable:              # (kind, name) lookup; raises RefUnresolved if absent
def is_registered(ref: AnyRef) -> bool:
def ref_inventory() -> dict[str, dict]:            # {"handler:economy.give": {"module": "sb.manifest.economy"}}
```

**Contract (the seam every sibling relies on):**
- **Declaration** binds a name: `@handler("economy.give")` in `sb/manifest/economy.py` registers `("handler","economy.give") → the_callable`. Handler registration is the manifest layer's job (§1.1: manifests are "pure declarations + handler registrations").
- **Serialization** (compile): a spec field whose value is any `*Ref` serializes as `{"$ref": "handler:economy.give"}`. An **unregistered ref is a `COMPILE_ERROR`** (`unresolved_ref`) — caught by pass P2 because the compiler imports *every* manifest before serialize, so the table is complete and order-independent (it is a resolution table, not a collision oracle — §8 fork 3).
- **Resolution** (boot): `sb/app` imports every manifest (repopulating the table), loads the snapshot, and `resolve()`s each `$ref` → callable at composition time. A `$ref` with no table entry at boot → `FAILED_STARTUP` (`ref_unresolved_at_boot`). No `kernel → domain` import edge and no dynamic import: the kernel receives already-resolved callables from the composition root (§1.1).

### 3.2 The ordered validation-pass pipeline (I own)

`compile_manifests()` runs 9 passes. **Order is load-bearing:** each pass consumes the guarantees of
the prior, so a later pass never runs on unresolved/colliding input. **Within a pass, collect ALL
violations** (deterministic, names every culprit); **at a pass boundary, fail fast** (don't run a
pass whose inputs the prior pass just proved invalid).

```python
# tools/manifest_compile.py
@dataclass(frozen=True)
class Violation:
    pass_name: str
    failure_class: str                 # a §3.5 constant
    subsystem: str | None
    locus: str                         # id / "Type.field" / "file:line"
    detail: str
    claimant_a: str | None = None      # COLLISION: "subsystem@file" of first claimant
    claimant_b: str | None = None      # COLLISION: second claimant

@dataclass(frozen=True)
class CompileResult:
    ok: bool
    snapshot: dict | None              # None if a pre-serialize pass failed
    stable_hash: str | None
    violations: tuple[Violation, ...]

def compile_manifests(
    manifest_pkg: str = "sb.manifest",
    *,
    baseline_snapshot: dict | None = None,     # previous committed snapshot, for P7
) -> CompileResult: ...
```

| # | Pass | Reads | On failure emits | Failure class | Gate |
|---|---|---|---|---|---|
| P1 | `load` | `import sb.manifest.*`; collect `SubsystemManifest`s; populate ref table | manifest import raised (incl. §3.2-phase-1 `__post_init__` intra-manifest dup) | `COMPILE_ERROR` | CI+boot |
| P2 | `ref_resolution` | every `*Ref` in every spec field | `unresolved_ref` (`ref.kind:ref.name` not in table) | `COMPILE_ERROR` | CI+boot |
| P3 | `namespace` | the **derived** reservation index (walk all specs) + K1 `legacy_reservations.json` | two claimants of one `(kind,value)`; a `compat=True` name claimed by a non-owner; a capability string that fails the 3-part `{sub}.{res}.{action}` / reserved-prefix format | `COLLISION` | CI+boot |
| P4 | `authority` | every `authority_ref` string | `bad_authority` (ref doesn't resolve to a lane; capability not namespace-reserved; lane-exclusivity broken) | `COMPILE_ERROR` | CI+boot |
| P5 | `role_tag` | every field of every spec type | `untagged_field` (not exactly one of [S]/[A]/[O]) | `COMPILE_ERROR` | CI+boot |
| P6 | `semantic` (6 predicates, unordered among themselves) | resolved refs + unique ids | one `SEMANTIC_VIOLATION` per failing predicate instance (below) | `SEMANTIC_VIOLATION` | CI+boot |
| P7 | `store_completeness` | declared `StoreSpec` set vs `baseline_snapshot.projections.stores` + `store_retirements.yml` | a store present-in-baseline, absent-now, with **no** signed retirement | `STORE_DROP` (owner-gated) | CI+boot |
| P8 | `serialize` | the validated manifest set + `layout/*.lock.json` | a lock overlay key not tagged [A] | `COMPILE_ERROR` (`illegal_overlay_key`) | CI+boot |
| P9 | `recompile_parity` | the serialized snapshot's `stable_hash` vs the committed file's | hash mismatch | `DRIFT` | CI+boot (leg A) |

**The 6 `semantic` predicates (P6)** — the §9.1 four, plus two the FJ ledger forces:

| Predicate | Rule | Retires |
|---|---|---|
| `never_strand` | every `CommandSpec.route` resolves to a `PanelRef`/justified `HandlerRef`; every `PanelSpec` has a `NavigationSpec`; **every `PanelActionSpec` binds to a real button and every button's action resolves** | the heuristic `DANGLING_PANEL_ACTION` (now real, because the binding is declared) |
| `destructive_confirmation` | every `destructive` action carries a `ConfirmationSpec`; `irreversible ⇒ typed challenge` (§2.7) | — |
| `external_cost` | every spec with `external_side_effects=True` is `off_until_opt_in`; media declares a spend counter (T2-15) | — |
| `leaderboard_writer` | every `LeaderboardSpec.stat_key` has a declared writer (`StoreSpec`/`StatWriteSpec`) — decision 10 honesty | — |
| `audit_completeness` | every mutating `WorkflowRef`/`PanelActionSpec` routes through the audited seam (INV-F/G/K shape) | — |
| `action_cooldown_parity` | every mutating `PanelActionSpec` declares cooldown/audit parity with `CommandSpec.cooldown` (G-4) | FJ **L-5** (panel = a second, cooldown-free resolver) |

### 3.3 The forward generation contract (I own the contract; K8 owns the builder)

The rebuild inverts the arrow: `sb/kernel/interaction` builds the discord.py `app_commands.CommandTree`
+ the generic `SubsystemHost` cogs + the persistent-view registrations **from the snapshot**. This
spec does **not** design that builder (K8) — it fixes the **contract** that makes the build checkable:

```python
# the builder K8 must satisfy (pure function of the snapshot):
def build_runtime(snapshot: dict, ref_table) -> BuiltRuntime: ...
# BuiltRuntime must expose its *realized* identity sets for leg B:
class BuiltRuntime(Protocol):
    def command_paths(self) -> set[str]: ...     # "group sub" qualified, per §_local_paths shape
    def custom_ids(self) -> set[str]: ...
    def event_names(self) -> set[str]: ...
    def task_prefixes(self) -> set[str]: ...
```

The projections that turn the snapshot into the *expected* sets (I own — mirror the shipped
`_local_paths` qualified-path shape):

```python
# sb/app/boot_gate.py
def snapshot_command_paths(snapshot: dict) -> set[str]: ...   # union over CommandSpec.name+group
def snapshot_custom_ids(snapshot: dict)   -> set[str]: ...
def snapshot_event_names(snapshot: dict)  -> set[str]: ...
def snapshot_task_prefixes(snapshot: dict)-> set[str]: ...
```

Leg B (§3.4) asserts `snapshot_*` == `runtime.*` for each set. That equality **is** the "runtime
matches manifest" gate; it is the structural proof that the generation was faithful.

### 3.4 The three-way parity oracle (I own)

Three artifacts, three legs:

```python
# sb/app/boot_gate.py
@dataclass(frozen=True)
class ParityReport:
    recompile_ok: bool                 # leg A
    build_ok:     bool                 # leg B
    remote:       SyncOutcome | None   # leg C — the SHIPPED type (command_tree_sync.py:86)
    violations:   tuple[Violation, ...]

def gate_recompile(committed: dict) -> list[Violation]:            # leg A
async def run_boot_gate(committed: dict, runtime, bot, *, sync_enabled: bool) -> ParityReport: ...
```

| Leg | Compares | When | Reuses | Verdict on mismatch |
|---|---|---|---|---|
| **A — recompile-parity** | committed `manifest.snapshot.json` **==** `compile_manifests()` re-run in-process (by `stable_hash`) | CI (P9) **and** boot (before any network I/O) | P9 | CI: `DRIFT` red ("recompile & commit"). Boot: `FAILED_STARTUP` — the deployed code & snapshot diverged. |
| **B — build-parity** | `snapshot_*()` projections **==** `runtime.*()` realized sets | boot, after `build_runtime`, **before gateway connect** | §3.3 projections | `FAILED_STARTUP` (`build_mismatch`) — the loader built something the manifest didn't declare (a real generation bug), caught before serving. |
| **C — remote-parity** | `snapshot_command_paths()` **vs** `_remote_paths(await tree.fetch_commands())` | boot, **after** connect (`on_ready`, reconnect-safe one-shot) | `command_tree_sync._remote_paths` + `SyncOutcome` verbatim | **non-fatal** → gated `tree.sync()`, direction snapshot→Discord. `SyncOutcome.reason ∈ {disabled,fetch_failed,unchanged,synced,sync_failed}`. |

**Why the reuse is load-bearing, not cosmetic:** the shipped set-diff compares *reflected-local* vs
remote, so its only meaning is "someone forgot to sync." Flipping `local` to the **snapshot
projection** gives the same machinery three distinct meanings — leg A proves the artifact is
self-consistent, leg B proves the runtime equals the artifact, leg C proves Discord is catching up to
the artifact. `added = snapshot − remote` (declared, not yet on Discord); `removed = remote − snapshot`
(on Discord, dropped from the manifest). The path shape (`"group sub"`, per-kind, subcommands walked)
is identical to `_local_paths`/`_remote_paths`, so the comparator is lifted verbatim.

### 3.5 The failure taxonomy (I own)

| Class | Trigger | Caught at | Verdict |
|---|---|---|---|
| `COMPILE_ERROR` | manifest import raises · unresolved ref (P2) · bad authority (P4) · untagged field (P5) · illegal overlay key (P8) | CI + boot leg A | CI-red / `FAILED_STARTUP` |
| `COLLISION` | two claimants of one namespace id (P3) | CI + boot | CI-red / `FAILED_STARTUP`, **naming both** `claimant_a`/`claimant_b` + both files |
| `SEMANTIC_VIOLATION` | any P6 predicate fails | CI + boot | CI-red / `FAILED_STARTUP` |
| `STORE_DROP` | store lost without a signed retirement (P7) | CI + boot | CI-red **"needs owner sign-off"** (owner-gated; §3.6) |
| `DRIFT` | recompile hash ≠ committed snapshot (P9 / leg A) | CI + boot | CI-red "recompile & commit" / `FAILED_STARTUP` |
| `BUILD_MISMATCH` | built-runtime set ≠ snapshot projection (leg B) | boot only | `FAILED_STARTUP` (before connect) |
| `REMOTE_LAG` | Discord-remote paths ≠ snapshot (leg C) | boot only | **non-fatal** → gated snapshot→Discord sync |

**Verdict rule:** every class **except `REMOTE_LAG`** is a hard gate — CI-red pre-merge (the
`git merge-tree` machinery re-runs the whole pipeline on the merge result, §3.2 phase 2, so two
green PRs that collide together are caught before either merges) and `FAILED_STARTUP` pre-connect at
boot (a red deploy with a named culprit, never a crash-loop serving traffic — the §3.2-phase-3
conversion). `REMOTE_LAG` is the sole reconcile-not-fail leg: Discord's global command registration
is eventually-consistent and rate-limited, so failing boot on it would crash-loop on a transient
(§8 fork 4).

### 3.6 Store-completeness reconciliation (I own)

A `StoreSpec` (§2.8: `table` [S], `sole_writer` [S], `checkpoint_class` [S], `invariant_tag` [S]) is
the *only* declaration of a table the new schema derives at K3. **Dropping one silently = silent data
loss.** P7 makes it loud:

- **Baseline** = `baseline_snapshot.projections.stores` (the previous committed snapshot's store set).
  No hand-maintained ledger (that would reintroduce the drift class §3.1 kills — §8 fork 1).
- **Diff:** `added` (new tables) → OK, additive. `dropped` (in baseline, gone now) → check
  `store_retirements.yml` for a matching **owner-signed** entry. Unsigned drop → `STORE_DROP`
  (owner-gated CI-red). This mirrors the frozen §3.1 rule that a `legacy_reservations` entry is
  "deletable only with a migration note" — a store drop is the same class, one level up (§8 fork 2).

```yaml
# sb/namespace/store_retirements.yml  — append-only, owner-signed
retirements:
  - table: rps_tournament_settings
    retired_by: "Q-0NNN"                 # the owner decision authorizing it
    disposition: reverse-migrate         # export | reverse-migrate | declared-loss  (§8 — owner-gated)
    date: 2026-07-DD
    note: "folded into tournament_lobby; rows migrated by 00NN_*.py"
```

### 3.7 The amendment-registry minting authority (I own)

The capability audit minted amendment IDs **locally** in 4 lanes and collided 3× (Lane B/C/D all
claimed "G-7…G-9"; the capstone reconciled by hand — runtime-logic #92/#217; idea doc
`rebuild-amendment-registry-2026-07-03.md`). One committed file becomes the sole minting authority,
built **before** Gate-0 (so the Gate-0 fold that stamps G-9…G-24 `in-spec` works off a collision-free
list).

```yaml
# docs/planning/rebuild-amendments.yml
version: 1
amendments:            # G-n — grammar families
  G-1:  {name: GatewayListenerSpec,   status: in-spec,        spec_ref: "§2.8", consumers: [logging, karma, blackjack],           source: spike}
  # … G-2…G-6 in-spec (spike) …
  G-9:  {name: DeferredActionSpec,    status: pending-gate-0, spec_ref: null,   consumers: [proof, utility, security],            source: "D+A"}
  G-10: {name: ModalFormSpec,         status: pending-gate-0, spec_ref: null,   consumers: [settings, moderation, roles, btd6],   source: "D+A"}
  G-11: {name: MessagePipelineStageSpec, status: pending-gate-0, spec_ref: null, consumers: [automod, cleanup, counting, chain, xp], source: "A+C+B"}
  G-12: {name: EconomyTransactionSpec, status: pending-gate-0, spec_ref: null,  consumers: [economy, treasury, mining, farm, fishing, inventory], source: "B"}
  # … G-13 ProgressionSpec, G-14 ShopSpec, G-15 ItemCatalog-audited-ops, G-16 ChannelMatchSpec,
  #    G-17 TournamentLobbySpec, G-18 ResourceLifecycleSpec, G-19 WizardSectionSpec,
  #    G-20 InstanceLifecycleSpec, G-21 RecordTableSpec, G-22 StagedBuilderSpec,
  #    G-23 CommandSpec-arg-schema, G-24 PreviewConfirmApplySpec …
  G-24: {name: PreviewConfirmApplySpec, status: pending-gate-0, spec_ref: null, consumers: [cleanup],
         note: "Gate-0: compose from §2.7 MutationPreview+ConfirmationSpec first; mint only if composition fails"}
riders:                # R-n — field/vocab additions (batch into the same fold PR)
  R-1: {desc: "GatewayListenerSpec.handler: WorkflowRef|HandlerRef", ...}   # … R-2…R-15 …
provisional:           # P-n — held; ratify-condition recorded
  P-1: {name: EventFeedProjectionSpec, ratify_when: "second instance found (check Lane E feed plans)"}
  # … P-2 catchup_policy, P-3 UserMemorySpec, P-4 IdentityScope/TransferPolicy …
refuted:               # do-not-re-propose; one-line refutation
  LootTableSpec:            {reason: "4 distinct roll engines are not one family", source: "Lane B refute"}
  MultiSeatTableSessionSpec:{reason: "→ R-6 fold; 68% casino lift unsupported (24%)", source: "Lane B"}
  # … ReadModelProjectionSpec→R-9, ParticipationPrefSpec, ManagedProjectionSpec→R-7,
  #    SettingsPresetSpec, AutoResponderSpec, RegistryHubSpec, TournamentBracketSpec, PaginatedBlockSpec …
```

```python
# tools/check_amendments.py  (~40 lines, required check)
def check_amendments(
    registry="docs/planning/rebuild-amendments.yml",
    spec="docs/planning/rebuild-design-spec-2026-07-02.md",
) -> list[str]:
    # 1. G-/R-/P- ids unique and contiguous (next-free-number; no gaps, no dups)
    # 2. every status:in-spec entry's spec_ref names a section that exists in `spec`
    # 3. no `refuted` name appears as an amendment/rider `name`
    # 4. bidirectional: every `G-\d+` cited in `spec` exists in the registry (and vice-versa for in-spec)
    # returns [] when clean; each string is one violation (fail the check)
```

**Rules (from the idea doc, made enforceable):** next-free-number only; append-only; a lane/session
proposing a family mints *here* in the same PR and cites it; Gate-0 consumes it and flips
`pending-gate-0 → in-spec` + sets `spec_ref`. This is the same collision-kill pattern as the runtime
namespace registry (§3.1), applied to **meta-artifacts** — deliberately a *different* mechanism from
K1 (which governs runtime string identities), and the two never overlap.

---

## 4. Provides / Consumes

### 4.1 Provides — canonical shapes I own (every sibling consumes these verbatim)

| Contract | Canonical shape | Primary consumers |
|---|---|---|
| `manifest.snapshot.json` schema | §5 — sorted keys, `stable_hash` header, `subsystems{}` + `projections{namespace,stores,events,refs}` + `field_roles{}`; callables as `{"$ref":"kind:name"}` | K1 `check_namespace`, K3 db-schema derivation, K4 event catalogue, K10 sim + generators, the compat differ, the golden scaffolder |
| Ordered validation-pass pipeline | §3.2 — `compile_manifests() -> CompileResult`; 9 named passes; `Violation` shape | CI required-check; boot leg A; every K-step's checker arms into it |
| Ref-table resolution contract | §3.1 — `*Ref` types, `@handler` decorators, `resolve()`; unregistered=compile-error, unresolved-at-boot=`FAILED_STARTUP` | `sb/manifest/*` (declare), `sb/app` (resolve), every kernel engine (receives resolved callables) |
| Three-way parity oracle | §3.4 — `ParityReport`, `gate_recompile`, `run_boot_gate`; the `snapshot_*` projections | `sb/app` boot; K8 builder (must satisfy `BuiltRuntime`); reuses `command_tree_sync` |
| Failure taxonomy | §3.5 — 7 classes → CI-red / `FAILED_STARTUP` / gated-sync | every checker + the lifecycle `fail_startup` seam |
| Amendment minting authority | §3.7 — `rebuild-amendments.yml` schema + `check_amendments()` | Gate-0 fold; every future lane/session proposing a family |

### 4.2 Consumes — sibling shapes I assume (stated exactly so the seam pass can verify agreement)

| Assumed contract | Precise assumption my code depends on | Owning sibling | If the assumption is wrong |
|---|---|---|---|
| K1 namespace reservation lifecycle | `namespace.validate_snapshot(snapshot) -> list[Collision]` where `Collision(kind, value, claimant_a, claimant_b)`, plus `is_reserved(kind, value)` and `legacy_reservations.json` entries `{kind, value, owner, compat:bool}`; **the namespace pass is a pure function of the snapshot** (no manifest/spec import — §3.2 phase 2) | strand-1 · namespace registry | P3 can't emit `COLLISION` with named claimants |
| `authority_ref` | one public `authority_ref: str` field on `CommandSpec`/`PanelActionSpec`/`SelectorSpec` (T1-4, **not** the stale two-lane `capability_required`/`audience_tier` split — L-13/X-8); `authority.validate(ref) -> None|Error` resolving internally to a lane at compile time | strand-1 · conventions/authority | P4 has nothing to call; lane-exclusivity check is undefined |
| error-envelope / `FAILED_STARTUP` posture | the 7-phase lifecycle exposes `fail_startup(report) -> NoReturn` (nonzero exit, **before** network I/O) and `FAILED_STARTUP` is a state; `report` carries a named-culprit list (my `Violation.claimant_a/b`) | strand-1 · lifecycle | legs A/B can't convert a violation into a red deploy |
| ConfigSpec boot-preflight | ConfigSpec/SecretSpec preflight (T2-22) runs **before** the manifest recompile in the boot sequence, so the compiler assumes env/secrets are valid; boot order = **ConfigSpec → recompile(leg A) → namespace → DB pool → build → build(leg B) → connect → remote(leg C)** | strand-1 · lifecycle/config | leg A could run against unvalidated config |
| §2.7 result grammar | `WorkflowRef` targets return the §2.7 grammar built on the **real** `LifecycleResult`/`StageResult` (**no `WorkflowResult` class / `contracts.py:48-52` — fabricated**, Q-0120) | strand-1 · result grammar (function ②) | `audit_completeness`/`never_strand` read the wrong return-type seam |

---

## 5. Data model + snapshot schema

No new DB tables originate here — the compiler is file-based; the schema is **derived** from `StoreSpec`
at **K3** (that's K3's `0001` migration under INV-I's advisory lock — not this function's write).
This function *gates* store drops (§3.6), it does not author DDL.

**`manifest.snapshot.json`** (the canonical interchange shape I own):

```json
{
  "schema_version": 1,
  "compiler_version": "1.0.0",
  "stable_hash": "sha256:…",          // sha256 of canonical-JSON of everything below, excluding this key
  "manifest_count": 43,
  "field_roles": { "CommandSpec.name": "S", "CommandSpec.help_section_order": "A",
                   "CommandSpec.usage_weight": "O", "…": "…" },
  "subsystems": {                      // sorted by key
    "<key>": { "key": "…", "commands": [ … ], "panels": [ … ], "settings": [ … ],
               "stores": [ … ], "events": [ … ], "…": "…" }   // §2.1 fields, callables → {"$ref": "…"}
  },
  "projections": {                     // derived indices — no second source of truth
    "namespace": { "command": {…}, "custom_id": {…}, "event": {…}, "table": {…}, "…": "…" },
    "stores":    { "<table>": { "sole_writer": "engine:…", "checkpoint_class": "ledger",
                                "invariant_tag": "…" } },
    "events":    { "<name>": { "owner_subsystem": "…", "observability_only": false } },
    "refs":      { "handler:economy.give": { "module": "sb.manifest.economy" } }
  }
}
```

- **Determinism** (§2.0, made concrete): serialize via canonical JSON — `sort_keys=True`, `(",", ":")`
  separators, UTF-8, no trailing whitespace; tuples → JSON arrays in declared order; sets → sorted
  arrays. `stable_hash = "sha256:" + sha256(canonical_json(snapshot_without_hash))`. Two compiles of
  identical inputs are byte-identical (the leg-A / P9 precondition).
- **Layout locks** (`sb/manifest/layout/<x>.lock.json`) are applied during P8 **only to [A]-tagged
  keys** (looked up in `field_roles`); a non-[A] overlay key → `COMPILE_ERROR` — so a sim bug can
  corrupt arrangement but structurally cannot touch semantics/custom_ids/capabilities (§2.10.3).

**Indexes/keys:** none (JSON). The only "key" is `stable_hash` (the parity primitive) and the store
`table` names (P7's diff key).

---

## 6. Restart & merge=deploy behavior

- **Boot reconcile** (the sequence, wired into `sb/app` — replacing `bot1.py:1180-1249`'s non-fatal
  glue): ConfigSpec preflight → **leg A** recompile-parity (deployed code ⇄ committed snapshot;
  `FAILED_STARTUP` on divergence) → namespace validation (P3) → DB pool + migration check →
  `build_runtime(snapshot)` → **leg B** build-parity (`FAILED_STARTUP` before connect) → gateway
  connect → persistent-view re-registration → **leg C** remote-parity (gated one-shot sync) → admit
  commands. Legs A/B are hard gates *before* any traffic; leg C is post-connect reconcile.
- **merge = deploy** (Railway auto-redeploys `worker` on merge to `main`, Q-0193): a merged manifest
  change is live within minutes. Leg A at boot is the belt-and-suspenders that the deployed artifact
  is self-consistent (CI already enforced it pre-merge via P9 + the `git merge-tree` re-validation, so
  leg A should always pass — a failure means the deploy artifact was hand-tampered).
- **Dual-instance overlap** (LP-4 handoff): the old instance ran its leg C at *its* boot against the
  *old* snapshot; the new instance runs leg C against the *new* snapshot. `tree.sync()` is a
  declarative last-writer on a single global resource, so the newer commit's sync is the correct final
  state — no new idempotency needed for tree-sync itself. (The double-*fire* concern for
  messages/interactions — FJ L-6 / T2-2 — is a separate seam, out of scope here; I note the boundary.)
  Leg C stays the shipped reconnect-safe one-shot (`on_ready`, `command_tree_sync` semantics).

---

## 7. Architecture rules honored

- **Layer boundaries (§1.1 rebuild table):** `tools/manifest_compile.py` lives in `tools/` — imports
  `sb/spec`, `sb/namespace`, `sb/manifest` to walk them, and is **never imported at runtime**.
  `sb/spec/refs.py` + `roles.py` are **stdlib-only leaves** (the ref table is a resolution dict, not a
  cross-layer import). `sb/app/boot_gate.py` is the composition root (may import all); it resolves refs
  so **no `kernel → domain` edge and no dynamic import** ever exists (§1.1).
- **INV-B (identity contract across surfaces):** the snapshot makes INV-B true *by construction* — one
  declared source, projected; P3 is its generalization/enforcement (subsystem/command/custom_id/event
  identities agree because there is one origin).
- **INV-A (every emitted event ∈ `KNOWN_EVENTS`):** `projections.events` **generates** `KNOWN_EVENTS`
  from `EventSpec`s; an undeclared emit becomes a pre-boot failure (§1.2), stronger than the shipped
  warn-and-continue.
- **INV-H (SUBSYSTEMS deep-frozen after validate):** the committed snapshot *is* the frozen source;
  the runtime reads it read-only.
- **INV-I (migrations idempotent under advisory lock):** honored by *boundary* — P7 gates store drops
  but authors no DDL; the derived `0001` migration is K3's, run under the shipped advisory lock.
- **INV-F/G/K (audited mutation seams):** `audit_completeness` (P6) enforces that every mutating ref
  routes through the audited service — the compile-time generalization of the shipped AST fences.
- **§1.5 (no god-functions) / §1.6 (no lazy-import hiding):** the compiler is 9 small single-purpose
  passes, not one mega-function; manifests are imported explicitly (the ref table is populated by
  explicit imports, never a lazy body import).
- **Q-0120 (a green check that contradicts evidence is a bug in the check):** legs A + B are precisely
  the mechanism that makes a green compile *mean* something — the compile cannot be green while
  runtime ≠ snapshot, closing the class where a checker reports clean over a real defect.

---

## 8. Options → Decision → Why (every fork I closed)

| # | Fork | Options | Decision | Why |
|---|---|---|---|---|
| 1 | Store-completeness baseline | (a) previous committed snapshot's `stores` projection · (b) a hand-maintained store ledger · (c) live DB schema | **(a)** | (b) reintroduces the exact hand-maintained drift source §3.1 kills; (c) can't run in CI (no DB). The committed snapshot is already the source of truth and diffable. |
| 2 | Store-drop policy | (a) reject outright (like subsystem-key rename) · (b) allow with an owner-signed retirement note | **(b)** | A key *rename* is rejected because the key *is* the identity (rename ⇒ guaranteed loss); a store *drop* can be legitimate (a subsystem genuinely retired). Mirrors the frozen §3.1 "`legacy_reservations` deletable only with a migration note" rule — owner-gated, not forbidden. |
| 3 | Ref-registry location | (a) `sb/spec/refs.py` leaf, populated by manifest decorators · (b) `sb/namespace/` · (c) `sb/app/` | **(a)** | Refs are grammar vocabulary (belong with the specs). The table is a *resolution* map, not a collision oracle, so import-order-dependence is harmless — the compiler imports all manifests before serialize. Keeps `sb/namespace/` a pure-data leaf (§1.1). |
| 4 | Leg-C failure posture | (a) fail boot on remote lag · (b) reconcile (gated snapshot→Discord sync), non-fatal | **(b)** | Discord's global command registration is eventually-consistent + rate-limited; failing boot on it would crash-loop on a transient. Legs A/B (in-process, deterministic) are the hard gates; C is reconcile. Preserves the shipped `AUTO_SYNC_COMMANDS` kill-switch. |
| 5 | Meaning of `local` in the reused set-diff | (a) reflected from built runtime (today) · (b) snapshot projection | **(b)** for the authoritative diff | The rebuild inverts the arrow — snapshot is the source. `local = snapshot` makes leg C mean "Discord is behind the intended state"; leg B (snapshot vs built-runtime) separately catches loader bugs. |
| 6 | Pipeline failure mode | (a) fail on first error · (b) collect-all · (c) collect-within-pass, fail-fast-at-boundary | **(c)** | A collision pass must name *every* colliding pair (deterministic, one CI run fixes all); but a later pass reading unresolved refs would emit noise — so don't run it until refs resolve. Ordering encodes the dependency. |
| 7 | G-24 mint vs compose | record as `pending-gate-0` with the compose-first note; do not decide | **record faithfully** | The compose-vs-mint call is the Gate-0 spec pass's (a grammar decision), not the minting authority's — the registry carries the instruction, the fold executes it. |

---

## 9. Labeled deferrals (each bounded by the 43-subsystem + named-amendment corpus)

| Deferral | Reason | Bound |
|---|---|---|
| Leg-B introspection **adapter** for non-command sets (panel `custom_ids`, `event_names`, `task_prefixes`) | The built `SubsystemHost`/`PanelRuntimeView` doesn't exist until K8; over-specifying its internals now would fabricate an interface | The compared sets are exactly the snapshot's `command`/`custom_id`/`event`/`task_prefix` namespace kinds — **closed**. I fix the `BuiltRuntime` Protocol (§3.3); K8 fills the adapter. |
| The golden / **intended-divergence** parity lane (FJ **L-11**) | Orthogonal to this oracle: three-way parity proves *structural* identity (runtime = manifest); the golden harness proves *behavioral* equivalence to the old bot (or a reviewed delta). That lane is K10 + owner-gated | Boundary stated, not designed: parity oracle = "runtime is what the manifest says"; golden harness (K10) = "behavior matches old bot / reviewed delta." |
| Shared-verb computation + 100/25/1 cap budget + nav-node deep-link enumeration (FJ **L-14**) | Namespace-corpus algorithms owned by the K1 sibling (T1-5, owner-answered) | The compiler **provides** the snapshot K1 computes over (`projections.namespace`, `command` kind); the algorithm is K1's. |
| Per-amendment grammar dataclass design for G-9…G-24 | That is the Gate-0 *fold* + each amendment's owning K-step, not the minting authority | Exactly the 16 G-rows + 15 R-riders + 4 P + refuted set enumerated in FINAL-REVIEW §3 — the registry indexes them; the fold designs them. |
| `store_retirements.yml` **`disposition`** field's data step (export vs reverse-migrate vs declared-loss) | A genuine data-loss policy call (see §10 / open_decisions) — mirrors L-18's rollback-disposition class | Bounded to store drops; the *mechanism* (a required `disposition:` field) is designed; the *default* is the owner's. |

---

## 10. Retirement map (V-3 binding — nothing evaporates)

| Ledger row / queue item | How this spec retires it |
|---|---|
| **FJ "no buildable compiler" linchpin gap** (the whole assignment) | The §3.2 pipeline + §3.4 forward oracle **are** the compiler; the backward reflection paths (§2 table) are retired. |
| **FJ L-14** (K1 corpus "computed at compile from the live ledger") — *mechanism half* | The snapshot's `projections.namespace` is the single derived corpus K1 computes over (no live-ledger walk). The shared-verb/cap/deep-link *algorithm* stays K1's (deferred §9). |
| **FJ L-11** (three-way parity vs golden lane) — *structural half* | §3.4 delivers snapshot ⇄ built-runtime ⇄ Discord-remote parity (leg A/B/C), reusing the path set-diff. The intended-divergence *golden* lane boundary is named, not designed (deferred §9). |
| **FJ L-5** (panel = a second, cooldown-free resolver) | P6 `action_cooldown_parity` makes a mutating `PanelActionSpec` without cooldown/audit parity a `SEMANTIC_VIOLATION`. |
| **FJ L-4 / L-25** (fabricated `contracts.py:48-52` / `WorkflowResult`) | Consumed-seam correction (§4.2): the result grammar is the **real** `LifecycleResult`/`StageResult`; re-verified against source; carried in `seam_corrections`. |
| **runtime-logic-mechanics #92 & #217** (amendment registry unminted; G-numbers collided 3×; G-9 contested) | §3.7 `rebuild-amendments.yml` + `check_amendments.py` — the sole minting authority, built before Gate-0. |
| **T2-18** (ratify static-stable + dynamic-versioned custom_id two-population model) | P3 **enforces** the two-population disjointness once the owner ratifies (a legacy `custom_id_override` may not begin with a scheme token; every canonical mint collides against the frozen legacy set). Enforcement designed; ratification stays the owner's. |
| **Q-0162 backward manifest spine** (`command_manifest`/`panel_manifest`/`manifest_reconciliation`) | Superseded by the forward projection; the deferred `DANGLING_PANEL_ACTION` heuristic becomes the real `never_strand` pass (declared bindings). |

Owner-queue tiers touched: **T2-18** (enforcement designed, ratify = owner) · **T2-22** (ConfigSpec
preflight consumed as a boot-order seam, §4.2). No T1 row is decided here (T1 all resolved,
Q-0237a–g — honored, not re-opened).

---

## 11. Build order (design-spec §9)

- **Pre-K2 / Gate-0 prerequisite:** `rebuild-amendments.yml` + `check_amendments.py` (§3.7) — built
  **before** the Gate-0 fold, so the fold that stamps G-9…G-24 `in-spec` works off a collision-free
  list. **Blocks:** Gate-0.
- **K2 (the grammar band):** `tools/manifest_compile.py` (passes P1–P9), `sb/spec/refs.py` +
  `roles.py`, the snapshot serializer, the failure taxonomy, leg-A recompile-parity, and the
  arrangement-invariance test (§2.10.2). This is where §9.1 places "manifest compiler + snapshot +
  validators."
- **Armed later (contract defined at K2, activates when its input lands):** P7 store-completeness
  arms at **K3** (when `projections.stores` + the derived schema exist); leg-B build-parity arms at
  **K8** (when `build_runtime` exists); leg-C remote-parity arms at **K8** (needs gateway connect),
  reusing `command_tree_sync`.
- **What it blocks:** the snapshot is the spine *everything* declares into — **K3** (db from
  `StoreSpec`), **K4** (events from `EventSpec`), **K5–K10**, and **all of Phase 4** (every port lands
  a manifest that must compile green) consume it. This function is the gate the entire kernel and port
  order sit behind.
```