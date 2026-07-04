# Strand 1 · Kernel spine · ① Manifest compiler + committed snapshot + amendment registry

> **Phase-B foundational design.** Docs-only. Designs the linchpin kernel function to buildable
> depth against the frozen upstream contracts (design-spec §2.0/§2.1/§2.7/§2.10/§3.2/§9.1;
> router Q-0219…Q-0237; FJ Fable-5) **and the reconciled cross-spec seams frozen in
> `../shared-vocabulary.md`** (RC-1, RC-7, §②, §⑦.2). A fresh agent builds this from this file + those
> contracts making **zero** further design decisions, except the surfaced owner call in §8/§9
> (store-drop disposition default) and the two owner-gated dependencies it *consumes* (shared-vocab
> SF-a panel-action grammar; SF-d prod-attest custody — neither is this spec's to decide).
>
> **Reconciliation pass carried (design-closer, 2026-07-04).** This revision folds in the missed
> hardening pass its siblings (02/03/05) already had. It **reconciles the K1 namespace seam to the
> canonical `validate(snapshot) -> NamespaceReport` shape** (RC-7, spec 03 §4.2 — 01 was the loser
> spec that had to change), **splits the projection build ahead of serialize so P3 is a pure function
> of snapshot data at all three call sites** (CI / merge-tree / boot leg-A), **carves the namespaced
> `PredicateRef` form out of ref-table resolution** (spec 02 §3.0 — it is a parsed string, not a
> registered callable), **names the exact grammar field every P6 predicate reads**, **adopts the frozen
> `validate_authority_ref` name + the empty-ref ADMIN-floor carve-out + the six authority-bearing spec
> types** (shared-vocab §②), **reconciles the boot order to spec 05 §6 as the single source**, and
> **fixes the result-grammar mis-cite** (below). Every change is marked in §4.2 / §8 / §10.
>
> **Spot-verified seams (2026-07-04, against shipped source):** the spine runs BACKWARD today —
> `command_manifest.build_command_manifest` (`command_manifest.py:176-207`) projects the *live*
> ledger, `panel_manifest.build_panel_manifest` (`panel_manifest.py:180-213`) *instantiates and
> introspects* registered views; `manifest_reconciliation.reconcile` (`manifest_reconciliation.py:66`)
> defers button→command binding (`:21-27`); `command_tree_sync.auto_sync_if_changed`
> (`command_tree_sync.py:96-138`) is a **path set-diff** (`local == remote`; `added = local-remote`),
> not a hash; `SubsystemSchema` (`subsystem_schema.py:234`) declares
> `subsystem`, `bindings`, `settings`, `resource_requirements`, `domain_panels`, `version`,
> `completeness_rule` (`:270-276`, verified) — notably **no `commands`/`panels`/`stores`/`events`
> facets** (the load-bearing point: the shipped schema has no forward command/panel/store/event
> declaration, which is exactly what the rebuild manifest root adds); boot is sequential non-fatal
> glue (`bot1.py:1180-1249`). `tools/manifest_compile.py`, any `*.snapshot.json`, `sb/`, and
> `rebuild-amendments.yml` are all **absent**.
> **Seam correction carried (Q-0120, FJ L-4/L-25 — canonicalized in shared-vocab §0/RC-1):** there is
> **no `WorkflowResult` class and no `disbot/core/contracts.py`** (both re-verified ABSENT this
> session). The **real** result vocab is `disbot/services/lifecycle/contracts.py`
> (`LifecycleResult:77`, `LifecyclePreview:66`, `StepResult:56`, outcomes
> `SUCCESS/PARTIAL/BLOCKED/DECLINED/DISCORD_FAILED:48-52`, reversibility
> `REVERSIBLE/COMPENSATABLE/IRREVERSIBLE:40-42` — all verified). The **dispatch-return** grammar a
> `WorkflowRef` target yields is `WorkflowResult | None` — the §2.7 **kernel** type, a strict superset
> of the shipped `LifecycleResult`, landed in K7 (a *design* type, not a shipped class). The shipped
> `StageResult` (`message_pipeline.py:181`) is the **message-pipeline substrate one layer below
> dispatch — NOT a dispatch return** (RC-1); this spec never places it in the `WorkflowRef` return
> seam. `services/lifecycle/contracts.py:48-52` is **REAL**; the fabricated cite is the absent
> `disbot/core/contracts.py` — the two are never conflated below.

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
| G-c | scattered "compile error / drift = red / FAILED_STARTUP" | §3.5 the **failure taxonomy** — 9 classes → CI-red / `FAILED_STARTUP` / gated-sync |
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
| `sb/spec/refs.py` | `sb/spec/` (stdlib-only leaf) | The **ref value types** (`HandlerRef`/`PanelRef`/`ViewRef`/`PredicateRef`/`EngineRef`/`WorkflowRef`/`ProviderRef`, each a frozen `name:str`) + the `@handler(name)`… registration decorators + the module-global **ref table** (`(kind,name) → callable`), which **raises on a duplicate binding** (§3.1). §3.1. |
| `sb/spec/roles.py` | `sb/spec/` leaf | `Role` enum (`S`/`A`/`O`) + `field_role()` metadata helper + `snapshot_field_roles()` (the `field_roles` map the arrangement-invariance test and sim read). |
| `sb/app/boot_gate.py` | `sb/app/` (composition root; may import all) | The boot gate: leg-A recompile-parity, leg-B build-parity, leg-C remote-parity; calls the K5-lifecycle `fail_startup` seam. §3.4. |
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

Every callable a spec points at (a command handler, a panel renderer override, an engine, a workflow,
a provider) is carried in the manifest as a **ref value object** holding only a string name, never the
callable — this is what makes the snapshot 100% data (§2.0).

```python
# sb/spec/refs.py  — stdlib-only leaf
@dataclass(frozen=True)
class HandlerRef:      name: str          # kind="handler"
@dataclass(frozen=True)
class PanelRef:        name: str          # kind="panel"    (a panel_id)
@dataclass(frozen=True)
class ViewRef:         name: str          # kind="view"     (a re-homed legacy view class, §2.9 tier-3)
@dataclass(frozen=True)
class PredicateRef:    name: str          # kind="predicate"— SPECIAL: two forms, see below
@dataclass(frozen=True)
class EngineRef:       name: str          # kind="engine"
@dataclass(frozen=True)
class WorkflowRef:     name: str          # kind="workflow" (returns the §2.7 WorkflowResult|None grammar)
@dataclass(frozen=True)
class ProviderRef:     name: str          # kind="provider" (a read-model / data provider)

AnyRef = HandlerRef | PanelRef | ViewRef | PredicateRef | EngineRef | WorkflowRef | ProviderRef

class RefRedefined(Exception):            # raised by @handler-family on a duplicate (kind, name)
    """A second module bound an already-bound (kind, name). Names BOTH modules."""

_REF_TABLE: dict[tuple[str, str], Callable] = {}   # (kind, name) -> callable

def handler(name: str) -> Callable[[F], F]:        # + panel/view/engine/workflow/provider twins
    """Decorator used in sb/manifest/<x>.py to bind a ref name to a callable.
    A duplicate (kind, name) binding raises RefRedefined(kind, name, first_module, second_module)
    at import time — never a silent overwrite (§3.1 duplicate-registration rule)."""
def resolve(ref: AnyRef) -> Callable:              # (kind, name) lookup; raises RefUnresolved if absent
def is_registered(ref: AnyRef) -> bool:
def ref_inventory() -> dict[str, dict]:            # {"handler:economy.give": {"module": "sb.manifest.economy"}}
```

**Contract (the seam every sibling relies on):**
- **Declaration** binds a name: `@handler("economy.give")` in `sb/manifest/economy.py` registers
  `("handler","economy.give") → the_callable`. Handler registration is the manifest layer's job (§1.1:
  manifests are "pure declarations + handler registrations").
- **Duplicate registration is an error, never a silent overwrite (closes the §3.1 gap).** If two
  modules both `@handler("x")`, the second decorator call raises `RefRedefined("handler","x",
  first_module, second_module)` **at import time** — surfaced as a **P1 `COMPILE_ERROR`** naming both
  modules. Belt-and-suspenders: because `handler`/`panel`/`engine`/`workflow`/`provider`/`view`/`predicate`
  ref names are also K1 namespace kinds (`handler_ref`, `panel`, … in the 16-kind registry), the same
  cross-manifest dup **also** surfaces as a P3 `COLLISION` on that kind. P1 is the primary, immediate
  catch; P3 is the snapshot-level confirmation — they never disagree.
- **Serialization** (compile): a spec field whose value is any `*Ref` **except the namespaced
  `PredicateRef` form (below)** serializes as `{"$ref": "handler:economy.give"}`. An **unregistered
  `$ref` is a `COMPILE_ERROR`** (`unresolved_ref`) — caught by pass P2 because the compiler imports
  *every* manifest before projecting, so the table is complete and order-independent (it is a
  resolution table, not a collision oracle — §8 fork 3).
- **Resolution** (boot): `sb/app` imports every manifest (repopulating the table), loads the snapshot,
  and `resolve()`s each `$ref` → callable at composition time. A `$ref` with no table entry at boot →
  `FAILED_STARTUP` (`ref_unresolved_at_boot`). No `kernel → domain` import edge and no dynamic import:
  the kernel receives already-resolved callables from the composition root (§1.1).

**`PredicateRef` is the one `*Ref` that is NOT purely table-resolved (RC — reconciled to spec 02 §3.0).**
Spec 02 §3.0 defines a `PredicateRef` as a string in **one of two forms**, and the compiler treats them
differently so P2 never false-rejects a valid namespaced predicate:

| Form | Example | Serializes as | Validated by | Resolved at runtime by |
|---|---|---|---|---|
| **Namespaced string** `"<kind>:<key>[=<value>]"`, `kind ∈ {setting, binding, capability, flag}`; `""` = constant-true | `"setting:logging.enabled"`, `"binding:log_channel"`, `"flag:beta"` | the **plain string** (NOT `{"$ref":…}`) | **P2 format gate** (head ∈ the 4 kinds, well-formed) **+ P3 key check** for `setting:`/`capability:` heads (the `<key>` must be a reserved `setting_key`/`capability`) | `predicates.evaluate(ref, ctx)` (spec 02) — **never** `resolve()`; it is a parsed string, not a registered callable |
| **Registered ref** — a namespace-reserved name resolving to a pure `(PanelContext) -> bool` | `"is_configured_for_logging"` | `{"$ref": "predicate:<name>"}` | **P2 ref-table resolution** (like every other `$ref`; unregistered → `unresolved_ref`) | `resolve()` → the registered callable |

Both `enabled_when` and `visible_when` (spec 02 §3.0, both `PredicateRef`) serialize **per whichever
form each instance holds** — a plain string for the namespaced form, a `{"$ref":"predicate:…"}` for the
registered form. **Under 01's model P2 resolves only the `$ref` form**; the namespaced string is *never*
an unresolved ref (that was the H4 false-reject bug — now closed). The `binding:`/`flag:` heads are
guild-state vocab owned by the settings sibling, so P2 checks only their *form*; `setting:`/`capability:`
heads additionally have their `<key>` reservation checked in P3 (the P3/P4-style split, §3.2).

### 3.2 The ordered validation-pass pipeline (I own)

`compile_manifests()` runs 9 passes. **Order is load-bearing:** each pass consumes the guarantees of
the prior, so a later pass never runs on unresolved/colliding input. **Within a pass, collect ALL
violations** (deterministic, names every culprit); **at a pass boundary, fail fast** (don't run a
pass whose inputs the prior pass just proved invalid).

**The pre-serialize projection step (closes H1 — P3 must be a pure function of snapshot data).** After
P1 (import) and P2 (ref resolution) the compiler runs an internal, violation-free **`_project()`** step
that assembles the **snapshot body as a pure dict** — `subsystems{}` + `projections{namespace, stores,
events, refs}` + `field_roles{}` (§5) — from the loaded manifests and the now-complete ref table.
`_project()` emits no `Violation`s; it exists so that **P3, P4, P6, and P7 read pure snapshot data, not
live spec objects.** P8 (`serialize`) then *canonicalizes* that same body and computes `stable_hash`.
This is what makes the namespace pass **`validate(snapshot)`**: P3 hands K1's oracle the projected
`snapshot` dict — it never "walks specs." The identical `snapshot` dict shape is what the CI check, the
`git merge-tree` re-validation, and the boot leg-A call site all pass to `validate` (§3.4, §6) — so a
green CI namespace verdict and a green boot namespace verdict are **the same verdict by construction**
(the CI-green ⟺ boot-green guarantee, Q-0120; shared-vocab §⑦.2).

```python
# tools/manifest_compile.py
@dataclass(frozen=True)
class Violation:
    pass_name: str
    failure_class: str                 # a §3.5 constant
    subsystem: str | None
    locus: str                         # id / "Type.field" / "file:line"
    detail: str
    scope: str | None = None           # COLLISION on a command: "surface/parent_group" from K1 Collision.scope
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
    baseline_snapshot: dict | None = None,     # previous committed snapshot, for P7 (None ⇒ first compile)
) -> CompileResult: ...
```

| # | Pass | Reads | On failure emits | Failure class | Gate |
|---|---|---|---|---|---|
| P1 | `load` | `import sb.manifest.*`; collect `SubsystemManifest`s; populate ref table | manifest import raised (incl. §3.2-phase-1 `__post_init__` intra-manifest dup; **`RefRedefined` duplicate binding**) | `COMPILE_ERROR` | CI+boot |
| P2 | `ref_resolution` | every `{"$ref":…}` field + every **namespaced** `PredicateRef` string | `unresolved_ref` (`$ref` not in table); `bad_predicate` (namespaced predicate head ∉ {setting,binding,capability,flag} or malformed) | `COMPILE_ERROR` | CI+boot |
| — | *(internal)* `_project` | loaded manifests + complete ref table → the **snapshot body** dict (§5) | — (no violations; the pure data P3/P4/P6/P7 read) | — | — |
| P3 | `namespace` | K1 **`validate(snapshot) -> NamespaceReport`** over `snapshot.projections.namespace` (pure data) + K1's own `legacy_reservations.json` / `tombstones.json` | maps `report.collisions → COLLISION` (both claimants + `scope`); `report.cap_violations → CAP_VIOLATION`; `report.format_errors → FORMAT_ERROR` (capability 3-part / reserved-prefix owner; namespaced-predicate `<key>` reservation for setting:/capability: heads) | `COLLISION` / `CAP_VIOLATION` / `FORMAT_ERROR` | CI+boot |
| P4 | `authority` | every `authority_ref` on all **six** frozen spec types (§4.2) | `bad_authority` — `validate_authority_ref(ref)` raised (ref classifies to no lane); the empty ref `""` is **always valid** (ADMIN-floor carve-out) | `COMPILE_ERROR` | CI+boot |
| P5 | `role_tag` | every field of every spec type | `untagged_field` (not exactly one of [S]/[A]/[O]) | `COMPILE_ERROR` | CI+boot |
| P6 | `semantic` (6 predicates, unordered among themselves) | resolved refs + unique ids + the **named grammar fields §4.2 pins** | one `SEMANTIC_VIOLATION` per failing predicate instance (below) | `SEMANTIC_VIOLATION` | CI+boot |
| P7 | `store_completeness` | declared `StoreSpec` set vs `baseline_snapshot.projections.stores` + `store_retirements.yml` (baseline `None` ⇒ every store `added`) | a store present-in-baseline, absent-now, with **no** signed retirement | `STORE_DROP` (owner-gated) | CI+boot (armed K3) |
| P8 | `serialize` | the projected body + `layout/*.lock.json` | a lock overlay whose resolved `type.field` role ≠ [A] (§5) | `COMPILE_ERROR` (`illegal_overlay_key`) | CI+boot |
| P9 | `recompile_parity` | the serialized snapshot's `stable_hash` vs the committed file's | hash mismatch | `DRIFT` | CI+boot (leg A) |

**P3 is exactly K1's `validate` (RC-7 — 01 reconciled).** P3 does not re-implement collision/cap/format
logic; it **calls K1's one oracle** on the projected snapshot and maps the three `NamespaceReport`
violation categories into the compiler's `Violation` stream (see §4.2 for the precise shapes and the
argument-order/`scope`-key reconciliation). This is the fix for the H2/H3 gaps: a 101st top-level slash
command surfaces as `CAP_VIOLATION`, a malformed capability as `FORMAT_ERROR` — both a red compile, so
the crash-at-registration class the compiler exists to kill cannot pass green.

**P4 authority (reconciled to shared-vocab §②).** P4 reads `authority_ref` on **all six** frozen
authority-bearing spec types — `CommandSpec`, `PanelActionSpec`, `SelectorSpec`, `SettingSpec`,
`BindingSpec`, `ResourceRequirement` (shared-vocab §2.1) — and calls the frozen leaf checker
**`validate_authority_ref(ref)`** (`sb/spec/authority.py`, K6). Per `classify_authority_ref` (total,
non-overlapping — shared-vocab §2.2): `""` → CAPABILITY/**ADMIN-floor, always valid** (the empty-ref
carve-out — P4 must **not** flag it as "capability not namespace-reserved"); a dotted 3-part string →
CAPABILITY (its *format + reserved-prefix* were already proven by P3, so P4 only confirms it resolves to
the capability **lane**); a tier token ∈ TIERS → TIER; anything else → `BadAuthorityError` → `bad_authority`
`COMPILE_ERROR`. **There is no "lane-exclusivity" check** — `classify_authority_ref` is total and
non-overlapping *by construction*, so there is nothing to "break" (the stale phrasing is dropped). P4 is
the **lane side** of the P3/P4 split (spec 03 decision 10): P3 owns capability string identity
(format + reserved-prefix owner), P4 owns lane resolution — no overlap, no gap.

**The 6 `semantic` predicates (P6)** — the §9.1 four, plus two the FJ ledger forces. Each names the
**exact declared grammar field(s) it reads** (the H-medium fix; §4.2 lists the owning spec per field):

| Predicate | Rule | Declared fields it reads | Retires |
|---|---|---|---|
| `never_strand` | every `CommandSpec.route` resolves to a `PanelRef`/justified `HandlerRef`; every `PanelSpec` has a `NavigationSpec`; **every `PanelActionSpec.action_id` is bound by exactly one declared `PanelSpec.components[*].action_id` (a real button) and every component's `action_id`/`selector_id` resolves to a declared action** | `CommandSpec.route`; `PanelSpec.navigation`; `PanelSpec.components[*].{action_id,selector_id}`; `PanelActionSpec.action_id` (**panel grammar, §8-a option A**) | the heuristic `DANGLING_PANEL_ACTION` (now real, because the binding is declared) |
| `destructive_confirmation` | every `destructive` action carries a `ConfirmationSpec`; `irreversible ⇒ typed challenge` (§2.7) | `PanelActionSpec.destructive: bool`; `*.confirm: ConfirmationSpec | None`; `*.reversibility ∈ {REVERSIBLE,COMPENSATABLE,IRREVERSIBLE}` (shipped vocab, `contracts.py:40-42`) | — |
| `external_cost` | every spec with `external_side_effects=True` is `off_until_opt_in`; media declares a spend counter (T2-15) | `*.external_side_effects: bool`; `*.off_until_opt_in: bool`; `*.spend_counter` (a `StoreSpec`/`StatWriteSpec` ref) | — |
| `leaderboard_writer` | every `LeaderboardSpec.stat_key` has a declared writer (`StoreSpec`/`StatWriteSpec`) — decision 10 honesty | `LeaderboardSpec.stat_key`; the declared writer set (`StoreSpec.stat_key` / `StatWriteSpec`) | — |
| `audit_completeness` | every **mutating** ref routes through the audited seam: a spec whose `effect="mutating"` MUST carry a `WorkflowRef` (the K7 audited workflow engine — the compile-checkable proxy for "routes through `emit_audit_action`", using only *resolved refs + a declared field*, never an AST) | `*.effect ∈ {read,mutating,external}` (the manifest `effect` field spec 02 §9 also reads); the routable ref *kind* (`WorkflowRef` vs `HandlerRef`) | — |
| `action_cooldown_parity` | every mutating `PanelActionSpec` declares cooldown/audit parity with the `CommandSpec` it mirrors (G-4) | `PanelActionSpec.cooldown: CooldownSpec`; `PanelActionSpec.mirrors` (the action↔command correspondence); `CommandSpec.cooldown` (**§8-a option A**) | FJ **L-5** (panel = a second, cooldown-free resolver) |

**Dependency flag (P6 ⇄ shared-vocab SF-a — made explicit, the H-medium fix).** `never_strand`'s
button-binding leg and `action_cooldown_parity` read fields (`PanelActionSpec.action_id`/`cooldown`/
`mirrors`) that exist **only under shared-vocab SF-a / spec 02 §8-a *option A*** (panel actions carry
their own authority/cooldown/binding fields — the *recommended* default). Under **option B** those
fields live on the owning panel and the two predicates read the **derived path** (the panel-owned
cooldown + the panel's declared component list) instead. This spec **arms both predicates under option A**
and states the option-B derived-field path; it does **not** re-decide SF-a (owner-gated, tracked in
shared-vocab §8 and spec 02 §8-a). The other four predicates are option-independent.

### 3.3 The forward generation contract (I own the contract; K8 owns the builder)

The rebuild inverts the arrow: `sb/kernel/interaction` builds the discord.py `app_commands.CommandTree`
+ the generic `SubsystemHost` cogs + the persistent-view registrations **from the snapshot**. This
spec does **not** design that builder (K8) — it fixes the **contract** that makes the build checkable:

```python
# the builder K8 must satisfy (pure function of the snapshot):
def build_runtime(snapshot: dict, ref_table) -> BuiltRuntime: ...   # structural; no DB dependency
# BuiltRuntime must expose its *realized* identity sets for leg B:
class BuiltRuntime(Protocol):
    def command_paths(self) -> set[str]: ...     # "group sub" qualified, per §_local_paths shape (slash surface)
    def custom_ids(self) -> set[str]: ...
    def event_names(self) -> set[str]: ...
    def task_prefixes(self) -> set[str]: ...
```

The projections that turn the snapshot into the *expected* sets (I own — mirror the shipped
`_local_paths` qualified-path shape):

```python
# sb/app/boot_gate.py
def snapshot_command_paths(snapshot: dict) -> set[str]: ...   # union over CommandSpec.name+group, slash surface
def snapshot_custom_ids(snapshot: dict)   -> set[str]: ...
def snapshot_event_names(snapshot: dict)  -> set[str]: ...
def snapshot_task_prefixes(snapshot: dict)-> set[str]: ...
```

Leg B (§3.4) asserts `snapshot_*` == `runtime.*` for each set. That equality **is** the "runtime
matches manifest" gate; it is the structural proof that the generation was faithful. (`build_runtime`
is a **structural** function of the snapshot — no DB — so leg B runs before `db.init`; §6.)

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

def gate_recompile(committed: dict) -> list[Violation]:            # leg A (wraps compile_manifests → P1..P9)
async def run_boot_gate(committed: dict, runtime, bot, *, sync_enabled: bool) -> ParityReport: ...
```

| Leg | Compares | When | Reuses | Verdict on mismatch |
|---|---|---|---|---|
| **A — recompile-parity** | committed `manifest.snapshot.json` **==** `compile_manifests()` re-run in-process (all of P1..P9, by `stable_hash`) | CI (P9) **and** boot (before any network I/O) | P9 | CI: `DRIFT` red ("recompile & commit"). Boot: `FAILED_STARTUP` — the deployed code & snapshot diverged. **P3 runs once, inside this leg's `compile_manifests()` — it is NOT a separate boot step (§6).** |
| **B — build-parity** | `snapshot_*()` projections **==** `runtime.*()` realized sets | boot, after `build_runtime` (structural), **before gateway connect** | §3.3 projections | `FAILED_STARTUP` (`build_mismatch`) — the loader built something the manifest didn't declare (a real generation bug), caught before serving. |
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
| `COMPILE_ERROR` | manifest import raises · duplicate ref binding (P1) · unresolved ref / bad namespaced predicate (P2) · bad authority (P4) · untagged field (P5) · illegal overlay key (P8) | CI + boot leg A | CI-red / `FAILED_STARTUP` |
| `COLLISION` | two claimants of one `(kind, value, scope)` (P3, from K1) | CI + boot | CI-red / `FAILED_STARTUP`, **naming both** `claimant_a`/`claimant_b` + both files + the `scope` |
| `CAP_VIOLATION` | slash surface over the 100/25/1-nest budget (P3, from K1 `cap_violations`) | CI + boot | CI-red / `FAILED_STARTUP` — Discord rejects the 101st top-level command, so a green compile over an over-budget surface would crash-loop at registration |
| `FORMAT_ERROR` | capability not 3-part / reserved-prefix misuse / namespaced-predicate `<key>` unreserved (P3, from K1 `format_errors`) | CI + boot | CI-red / `FAILED_STARTUP` |
| `SEMANTIC_VIOLATION` | any P6 predicate fails | CI + boot | CI-red / `FAILED_STARTUP` |
| `STORE_DROP` | store lost without a signed retirement (P7) | CI + boot | CI-red **"needs owner sign-off"** (owner-gated; §3.6) |
| `DRIFT` | recompile hash ≠ committed snapshot (P9 / leg A) | CI + boot | CI-red "recompile & commit" / `FAILED_STARTUP` |
| `BUILD_MISMATCH` | built-runtime set ≠ snapshot projection (leg B) | boot only | `FAILED_STARTUP` (before connect) |
| `REMOTE_LAG` | Discord-remote paths ≠ snapshot (leg C) | boot only | **non-fatal** → gated snapshot→Discord sync |

**Verdict rule:** every class **except `REMOTE_LAG`** is a hard gate — CI-red pre-merge (the
`git merge-tree` machinery re-runs K1's **`validate()` on the merge-result snapshot** for the
namespace/collision/cap/format class, §3.2 phase 2, so two green PRs that collide together are caught
before either merges; the ref/role/semantic/parity classes are the per-PR full-`compile_manifests()`
gate) and `FAILED_STARTUP` pre-connect at boot (a red deploy with a named culprit, never a crash-loop
serving traffic — the §3.2-phase-3 conversion, via the K5 `fail_startup` seam). `REMOTE_LAG` is the sole
reconcile-not-fail leg: Discord's global command registration is eventually-consistent and rate-limited,
so failing boot on it would crash-loop on a transient (§8 fork 4).

**CAP_VIOLATION / FORMAT_ERROR are folded here explicitly (H3 fix).** They were implicit in "the
namespace pass"; the taxonomy now names them so P3's three K1 categories each have a home and a verdict.
`COLLISION`, `CAP_VIOLATION`, and `FORMAT_ERROR` are the three faces of a `not report.ok` from K1's
`validate` — all CI-red pre-merge and `FAILED_STARTUP` pre-connect.

### 3.6 Store-completeness reconciliation (I own)

A `StoreSpec` (§2.8: `table` [S], `sole_writer` [S], `checkpoint_class` [S], `invariant_tag` [S]) is
the *only* declaration of a table the new schema derives at K3. **Dropping one silently = silent data
loss.** P7 makes it loud:

- **Baseline** = `baseline_snapshot.projections.stores` (the previous committed snapshot's store set).
  No hand-maintained ledger (that would reintroduce the drift class §3.1 kills — §8 fork 1).
- **First compile / arming (`baseline_snapshot is None`) — closes the P7-baseline gap.** When no
  baseline exists (the very first compile, or the K3-arming compile when `projections.stores` first
  appears), **every declared store is `added`** and **no drop is possible** — P7 is a no-op that can
  only pass. There is no way to "lose" a store you have no prior record of.
- **Diff (baseline present):** `added` (new tables) → OK, additive. `dropped` (in baseline, gone now) →
  check `store_retirements.yml` for a matching **owner-signed** entry. Unsigned drop → `STORE_DROP`
  (owner-gated CI-red). This mirrors the frozen §3.1 rule that a `legacy_reservations` entry is
  "deletable only with a migration note" — a store drop is the same class, one level up (§8 fork 2).

**Baseline threading at the three call sites (closes the P7 threading gap).**

| Call site | `baseline_snapshot` passed | P7's effective role there |
|---|---|---|
| **CI required check** | the **previous committed** `manifest.snapshot.json` (the merge base's version) | **The real gate** — catches a PR that drops a store without a signed retirement, pre-merge. |
| **`git merge-tree` re-validation** | the **merge-base** committed snapshot (the common ancestor both PRs branched from) | catches two PRs that each look additive but together drop a store the merge-base declared. |
| **Boot leg-A** | the **committed file itself** (deployed code recompiles against the snapshot it ships with) | Trivially self-compares (baseline == current), so P7 is a **no-op at boot** — by design: a store drop must be caught **at CI**, never first discovered on a live boot. Boot leg-A's job is `stable_hash` parity (P9), not store-diff. |

```yaml
# sb/namespace/store_retirements.yml  — append-only, owner-signed
retirements:
  - table: rps_tournament_settings
    retired_by: "Q-0NNN"                 # the owner decision authorizing it
    disposition: reverse-migrate         # REQUIRED — export | reverse-migrate | declared-loss (§8 fork 8)
    date: 2026-07-DD
    note: "folded into tournament_lobby; rows migrated by 00NN_*.py"
```

`disposition` is a **required** field on every signed retirement — there is **no default disposition**,
so a store drop can never silently take a data-loss path (the surfaced owner call — §8 fork 8, §9).

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
| `manifest.snapshot.json` schema | §5 — sorted keys, `stable_hash` header, `subsystems{}` + `projections{namespace,stores,events,refs}` + `field_roles{}`; callables as `{"$ref":"kind:name"}` (namespaced predicates as plain strings) | K1 `validate`, K3 db-schema derivation, K4 event catalogue, K10 sim + generators, the compat differ, the golden scaffolder |
| Ordered validation-pass pipeline | §3.2 — `compile_manifests() -> CompileResult`; 9 named passes + the `_project` pre-serialize step; `Violation` shape (carries `scope`) | CI required-check; boot leg A; every K-step's checker arms into it |
| Ref-table resolution contract | §3.1 — `*Ref` types, `@handler` decorators (raise on dup), `resolve()`; the two-form `PredicateRef` carve-out; unregistered `$ref`=compile-error, unresolved-at-boot=`FAILED_STARTUP` | `sb/manifest/*` (declare), `sb/app` (resolve), every kernel engine (receives resolved callables) |
| Three-way parity oracle | §3.4 — `ParityReport`, `gate_recompile`, `run_boot_gate`; the `snapshot_*` projections | `sb/app` boot; K8 builder (must satisfy `BuiltRuntime`); reuses `command_tree_sync` |
| Failure taxonomy | §3.5 — 9 classes → CI-red / `FAILED_STARTUP` / gated-sync | every checker + the K5-lifecycle `fail_startup` seam |
| Amendment minting authority | §3.7 — `rebuild-amendments.yml` schema + `check_amendments()` | Gate-0 fold; every future lane/session proposing a family |

### 4.2 Consumes — sibling shapes I assume (stated exactly so the seam pass can verify agreement)

| Assumed contract | Precise assumption my code depends on | Owning sibling | If the assumption is wrong |
|---|---|---|---|
| **K1 namespace oracle (RECONCILED — RC-7; spec 03 §4.2 wins, 01 changed)** | **`namespace.validate(snapshot) -> NamespaceReport`** where `NamespaceReport{ok, collisions, cap_violations, format_errors, index}`; `Collision(kind, value, **scope**, claimant_a, claimant_b)` keyed **`(kind, value, scope)`**; the runtime read is **`is_reserved(value, kind, *, surface, parent)`** (value first). K1 loads `legacy_reservations.json`/`tombstones.json` internally; **`validate` is a pure function of the snapshot** (no manifest/spec import — §3.2). My P3 calls `validate(snapshot)` and maps `collisions→COLLISION` (copy `scope`+`claimant_a/b` straight across), `cap_violations→CAP_VIOLATION`, `format_errors→FORMAT_ERROR`. **My `Violation` carries `scope`** so command-collision culprits keep surface/parent_group and `/ticket close` vs `/thread close` never false-collide. | strand-1 · ③ K1 namespace registry (03) | P3 can't emit the three violation categories with named claimants + scope |
| **`projections.namespace["command"]` node shape (K1-required)** | each command node carries `{value, kind:"command", surface∈{"prefix","slash"}, parent_group:str|None, subsystem, source}`; **both surfaces are carried** (prefix identities are reserved even though they never reach Discord's tree); subcommands expanded. My `_project()` **emits this shape** (K1 requires it — spec 03 §4.2/§5) | strand-1 · ③ K1 (03) | K1 can't build the index / prefix identities go unreserved |
| **`authority_ref` + `validate_authority_ref` (RECONCILED — shared-vocab §②)** | one public `authority_ref: str` field on **all six** frozen spec types (`CommandSpec`, `PanelActionSpec`, `SelectorSpec`, `SettingSpec`, `BindingSpec`, `ResourceRequirement`); the checker is **`validate_authority_ref(ref) -> None | raises BadAuthorityError`** (`sb/spec/authority.py`, K6), backed by total non-overlapping `classify_authority_ref`; `""` → CAPABILITY/**ADMIN-floor, always valid**; tier tokens ∈ `TIERS`; dotted 3-part → CAPABILITY lane. P4 owns *lane resolution*; P3 owns *capability format + reserved-prefix* (the P3/P4 split, spec 03 decision 10). **No "lane-exclusivity" check exists** (classify is total by construction). | strand-1 · ④/K6 authority (shared-vocab §②) | P4 calls the wrong name / false-flags `""` / scopes to too few spec types |
| **error-envelope / `FAILED_STARTUP` posture** | the frozen error envelope (`from_exception`, shared-vocab §①) is spec 02's; the `fail_startup(report) -> NoReturn` seam (nonzero exit, **before** network I/O; `FAILED_STARTUP` a lifecycle state) is **K5 lifecycle**'s composition-root seam. `report` carries my `Violation.claimant_a/b`/`scope`. **Spec 01 §3.5 defines the failure *taxonomy* (the classes `fail_startup` converts); it does NOT own the `fail_startup` seam** — K5 does. | strand-1 · **K5 lifecycle** (external to the reviewed 01-05 set as a written spec; the seam spec 05 §3.9 drives) | legs A/B can't convert a violation into a red deploy |
| ConfigSpec boot-preflight + boot order | `preflight() -> Config` (shared-vocab §⑥; spec 05 §3.2) runs **first** in the composition root, before the compiler boot-gate legs and before connect; **the canonical boot order is spec 05 §6** (single source — §6 below defers to it) | strand-1 · ⑩ ops kernel (05) | leg A could run against unvalidated config / boot order drifts from 05 |
| §2.7 result grammar (MIS-CITE FIXED — RC-1) | a `WorkflowRef` target returns the §2.7 **`WorkflowResult | None`** grammar — the K7 kernel type, a strict superset of the **real** `LifecycleResult` (`services/lifecycle/contracts.py:77`, verified) reusing the shipped outcome constants (`:48-52`) + `StepResult` (`:56`). **`services/lifecycle/contracts.py:48-52` is REAL**; the *fabricated* cite is the absent `disbot/core/contracts.py` — the two are distinct. **`StageResult` (`message_pipeline.py:181`) is the message-pipeline substrate, NOT a dispatch return** (RC-1) and never appears in the `WorkflowRef` return seam. | strand-1 · ② result grammar (02, §3.6) | `audit_completeness`/`never_strand` read the wrong return-type seam |
| **P6 predicate grammar inputs (NAMED — the H-medium fix)** | the declared fields §3.2's P6 table lists exist on their owning specs: `route`/`navigation`/`components[*].action_id`/`PanelActionSpec.action_id`/`cooldown`/`mirrors` (**panel grammar §2.4/§2.6 — armed under §8-a *option A***), `destructive`/`confirm`/`reversibility` (§2.7), `external_side_effects`/`off_until_opt_in`/`spend_counter` (T2-15 external/media grammar), `LeaderboardSpec.stat_key` + writer set (§2.8), and the manifest **`effect`** field (spec 02 §9). | strand-1 · ② panel/action grammar (02) + design-spec §2.6/§2.7/§2.8 | a P6 predicate reads an undeclared field |
| **SF-a panel-action grammar (owner-gated dependency — NOT mine to decide)** | `never_strand` (button binding) + `action_cooldown_parity` read `PanelActionSpec.action_id`/`cooldown`/`mirrors`, which exist under **shared-vocab SF-a / spec 02 §8-a option A** (recommended). Under option B they read the panel-owned derived path. | strand-1 · ② (02 §8-a) / shared-vocab §8 SF-a | those two predicates need the option-B derived-field path armed instead |

---

## 5. Data model + snapshot schema

No new DB tables originate here — the compiler is file-based; the schema is **derived** from `StoreSpec`
at **K3** (that's K3's `0001` migration under INV-I's advisory lock — not this function's write).
This function *gates* store drops (§3.6), it does not author DDL.

**`manifest.snapshot.json`** (the canonical interchange shape I own):

```json
{
  "schema_version": 1,                 // IN the hashed body — a shape change legitimately forces regen
  "compiler_version": "1.0.0",         // NOT hashed — a tool-version bump alone must not force a DRIFT
  "stable_hash": "sha256:…",           // NOT hashed (it IS the hash)
  "manifest_count": 43,                // NOT hashed — derivable metadata (== len(subsystems))
  "field_roles": { "CommandSpec.name": "S", "CommandSpec.help_section_order": "A",
                   "CommandSpec.usage_weight": "O", "PanelSpec.layout": "A", "…": "…" },
  "subsystems": {                      // sorted by key
    "<key>": { "key": "…", "commands": [ … ], "panels": [ … ], "settings": [ … ],
               "stores": [ … ], "events": [ … ], "…": "…" }   // §2.1 fields, callables → {"$ref": "…"}
  },
  "projections": {                     // derived indices — no second source of truth
    "namespace": { "command": [ {"value":"give","kind":"command","surface":"slash",
                                 "parent_group":null,"subsystem":"economy","source":"…:12"}, … ],
                   "custom_id": {…}, "event": {…}, "table": {…}, "…": "…" },
    "stores":    { "<table>": { "sole_writer": "engine:…", "checkpoint_class": "ledger",
                                "invariant_tag": "…" } },
    "events":    { "<name>": { "owner_subsystem": "…", "observability_only": false } },
    "refs":      { "handler:economy.give": { "module": "sb.manifest.economy" } }
  }
}
```

- **Determinism** (§2.0, made concrete): serialize via canonical JSON — `sort_keys=True`, `(",", ":")`
  separators, UTF-8, no trailing whitespace; tuples → JSON arrays in declared order; sets → sorted
  arrays. `stable_hash = "sha256:" + sha256(canonical_json(hashed_body))`. Two compiles of identical
  inputs are byte-identical (the leg-A / P9 precondition).
- **What is inside the hash (closes the `compiler_version` gap).** The **hashed body** is the canonical
  JSON of the snapshot **excluding `stable_hash`, `compiler_version`, and `manifest_count`** — it
  **includes** `schema_version` and everything under `field_roles`/`subsystems`/`projections`. Rationale:
  `stable_hash` is a **content** parity primitive; leg A / P9 compares *manifest content*, not the tool
  that produced it. Excluding `compiler_version` means a compiler bump with byte-identical manifest
  content does **not** redden leg A or force a snapshot regen. `manifest_count` is derivable from content
  (`len(subsystems)`) so it can never differ without the content differing — excluding it is harmless and
  keeps the "one thing that changes the hash is a real manifest change" property crisp. `schema_version`
  **is** hashed because a schema-shape change is a genuine content-shape change that *should* force a
  regen. *(This is a decided design call, not owner-gated — §8 fork 9.)*
- **Layout locks** (`sb/manifest/layout/<x>.lock.json`) are applied during P8 **only to [A]-tagged
  fields** — so a sim bug can corrupt arrangement but structurally cannot touch
  semantics/custom_ids/capabilities (§2.10.3). **The overlay-key schema + resolution (closes the P8
  gap).** Each overlay entry is an object:

  ```json
  { "target": "PanelSpec:econ_hub", "field": "layout", "arrangement": [ … ] }
  ```

  `target` names the **declaring spec type + the instance id** (`"<TypeName>:<instance_id>"`), and
  `field` names the field being overlaid. P8 resolves the role by constructing the `type.field` key
  **`f"{TypeName}.{field}"`** (here `"PanelSpec.layout"`) and looking it up in `field_roles`; if the role
  is not `[A]` → `COMPILE_ERROR (illegal_overlay_key)`. This is deterministic: the instance id resolves
  to its declaring spec type (a `panel_id` → `PanelSpec`, a stored `action_id` → `PanelActionSpec`, …),
  and `field_roles` is keyed per `type.field` — so an instance-level overlay always resolves to exactly
  one role to check.

**Indexes/keys:** none (JSON). The only "key" is `stable_hash` (the parity primitive) and the store
`table` names (P7's diff key).

---

## 6. Restart & merge=deploy behavior

- **Boot reconcile — the canonical sequence is owned by spec 05 §6 (single source; this spec defers to
  it, reconciling the earlier draft's drift).** The composition-root order, wired into `sb/app`
  (replacing `bot1.py:1180-1249`'s non-fatal glue):

  `preflight()` (config + `assert_data_plane` + `assert_intents`, spec 05 §3.2 — leg-0)
  → **leg A** recompile-parity (runs `compile_manifests()` = P1..P9 in-process; **P3/namespace runs
  once, INSIDE this leg — it is NOT a separate step**; `FAILED_STARTUP` on divergence)
  → `build_runtime(snapshot)` (structural, no DB) → **leg B** build-parity (`FAILED_STARTUP` before
  connect)
  → **`db.init`** (pool + migrations + `verify_applied_checksums`, spec 05 §3.4/§3.6)
  → EventBus → **lifecycle STARTING** → gateway connect → persistent-view re-registration → `on_ready`
  → **leg C** remote-parity (gated one-shot snapshot→Discord sync) → **lifecycle RUNNING** → `/ready` 200.

  **Reconciliation notes:** (1) the earlier draft placed `db.init` *between* leg A and leg B and listed
  "namespace validation (P3)" as a separate boot step — both are corrected here: `db.init` runs **after
  the compiler boot-gate legs** (spec 05 §6), and P3 runs **once inside leg A**. (2) The lifecycle
  **STARTING/RUNNING** transitions and the `/ready` 200/503 gate are **K5/spec-05-owned** — referenced,
  not restated here (spec 05 §3.8/§6). Legs A/B are hard gates *before* any traffic; leg C is
  post-connect reconcile. `build_runtime` is structural (no DB), which is why leg B can precede `db.init`.
- **merge = deploy** (Railway auto-redeploys `worker` on merge to `main`, Q-0193): a merged manifest
  change is live within minutes. Leg A at boot is the belt-and-suspenders that the deployed artifact is
  self-consistent (CI already enforced it pre-merge via P9 + the `git merge-tree` re-validation of K1's
  `validate` on the merge-result snapshot, so leg A should always pass — a failure means the deploy
  artifact was hand-tampered).
- **Dual-instance overlap** (LP-4 handoff): the old instance ran its leg C at *its* boot against the
  *old* snapshot; the new instance runs leg C against the *new* snapshot. `tree.sync()` is a
  declarative last-writer on a single global resource, so the newer commit's sync is the correct final
  state — no new idempotency needed for tree-sync itself. (The double-*fire* concern for
  messages/interactions — FJ L-6 / T2-2 — is covered by spec 05's `once()`/`IdempotencyKey` seam, out of
  scope here; I note the boundary.) Leg C stays the shipped reconnect-safe one-shot (`on_ready`,
  `command_tree_sync` semantics).

---

## 7. Architecture rules honored

- **Layer boundaries (§1.1 rebuild table):** `tools/manifest_compile.py` lives in `tools/` — imports
  `sb/spec`, `sb/namespace`, `sb/manifest` to walk them, and is **never imported at runtime**.
  `sb/spec/refs.py` + `roles.py` are **stdlib-only leaves** (the ref table is a resolution dict, not a
  cross-layer import). `sb/app/boot_gate.py` is the composition root (may import all); it resolves refs
  so **no `kernel → domain` edge and no dynamic import** ever exists (§1.1).
- **INV-B (identity contract across surfaces):** the snapshot makes INV-B true *by construction* — one
  declared source, projected; P3 (= K1 `validate`) is its generalization/enforcement (subsystem/command/
  custom_id/event identities agree because there is one origin, and the `(kind, value, scope)` key keeps
  `!karma`/`/karma` and `/ticket close`/`/thread close` from false-colliding).
- **INV-A (every emitted event ∈ `KNOWN_EVENTS`):** `projections.events` **generates** `KNOWN_EVENTS`
  from `EventSpec`s; an undeclared emit becomes a pre-boot failure (§1.2), stronger than the shipped
  warn-and-continue.
- **INV-H (SUBSYSTEMS deep-frozen after validate):** the committed snapshot *is* the frozen source;
  the runtime reads it read-only.
- **INV-I (migrations idempotent under advisory lock):** honored by *boundary* — P7 gates store drops
  but authors no DDL; the derived `0001` migration is K3's, run under the shipped advisory lock.
- **INV-F/G/K (audited mutation seams):** `audit_completeness` (P6) enforces that every **mutating**
  ref (declared `effect="mutating"`) routes through a `WorkflowRef` — the K7 audited workflow engine —
  the compile-time, AST-free generalization of the shipped audit fences (shared-vocab §③).
- **§1.5 (no god-functions) / §1.6 (no lazy-import hiding):** the compiler is 9 small single-purpose
  passes + a violation-free `_project` step, not one mega-function; manifests are imported explicitly
  (the ref table is populated by explicit imports, never a lazy body import).
- **Q-0120 (a green check that contradicts evidence is a bug in the check):** legs A + B + the single
  `validate` oracle (shared with CI/merge-tree/boot) are precisely the mechanism that makes a green
  compile *mean* something — the compile cannot be green while runtime ≠ snapshot, or while CI and boot
  run different namespace code, closing the class where a checker reports clean over a real defect.

---

## 8. Options → Decision → Why (every fork I closed)

| # | Fork | Options | Decision | Why |
|---|---|---|---|---|
| 1 | Store-completeness baseline | (a) previous committed snapshot's `stores` projection · (b) a hand-maintained store ledger · (c) live DB schema | **(a)** | (b) reintroduces the exact hand-maintained drift source §3.1 kills; (c) can't run in CI (no DB). The committed snapshot is already the source of truth and diffable. |
| 2 | Store-drop policy | (a) reject outright (like subsystem-key rename) · (b) allow with an owner-signed retirement note | **(b)** | A key *rename* is rejected because the key *is* the identity (rename ⇒ guaranteed loss); a store *drop* can be legitimate (a subsystem genuinely retired). Mirrors the frozen §3.1 "`legacy_reservations` deletable only with a migration note" rule — owner-gated, not forbidden. |
| 3 | Ref-registry location | (a) `sb/spec/refs.py` leaf, populated by manifest decorators · (b) `sb/namespace/` · (c) `sb/app/` | **(a)** | Refs are grammar vocabulary (belong with the specs). The table is a *resolution* map, not a collision oracle, so import-order-dependence is harmless — the compiler imports all manifests before `_project`. Keeps `sb/namespace/` a pure-data leaf (§1.1). |
| 4 | Leg-C failure posture | (a) fail boot on remote lag · (b) reconcile (gated snapshot→Discord sync), non-fatal | **(b)** | Discord's global command registration is eventually-consistent + rate-limited; failing boot on it would crash-loop on a transient. Legs A/B (in-process, deterministic) are the hard gates; C is reconcile. Preserves the shipped `AUTO_SYNC_COMMANDS` kill-switch. |
| 5 | Meaning of `local` in the reused set-diff | (a) reflected from built runtime (today) · (b) snapshot projection | **(b)** for the authoritative diff | The rebuild inverts the arrow — snapshot is the source. `local = snapshot` makes leg C mean "Discord is behind the intended state"; leg B (snapshot vs built-runtime) separately catches loader bugs. |
| 6 | Pipeline failure mode | (a) fail on first error · (b) collect-all · (c) collect-within-pass, fail-fast-at-boundary | **(c)** | A collision pass must name *every* colliding pair (deterministic, one CI run fixes all); but a later pass reading unresolved refs would emit noise — so don't run it until refs resolve. Ordering encodes the dependency. |
| 7 | G-24 mint vs compose | record as `pending-gate-0` with the compose-first note; do not decide | **record faithfully** | The compose-vs-mint call is the Gate-0 spec pass's (a grammar decision), not the minting authority's — the registry carries the instruction, the fold executes it. |
| 8 | **Store-drop `disposition` default** (surfaced owner call) | (a) a global default (e.g. `reverse-migrate`) · (b) **no default — `disposition` is a REQUIRED field on every signed retirement** · (c) default to the safest (`declared-loss` refused) | **surfaced to owner; recommend (b)** | A silent global disposition default is a silent data-loss path — the exact class §3.6 exists to kill. Making `disposition` required forces an explicit per-store `export`/`reverse-migrate`/`declared-loss` call at sign-off time. **Owner-gated** (a real data-loss policy call); pushed to open_decisions + §9. |
| 9 | `stable_hash` body membership | (a) hash everything except `stable_hash` · (b) also exclude `compiler_version` + `manifest_count` | **(b)** | (a) forces a DRIFT + snapshot regen on every compiler bump even when manifest content is byte-identical — `stable_hash` is a *content* parity primitive, and a tool-version bump is not a content change. `manifest_count` is derivable (`len(subsystems)`). `schema_version` stays hashed (a shape change is a real content change). Decided, not owner-gated (§5). |
| 10 | Duplicate ref registration (two modules `@handler("x")`) | (a) silent table overwrite · (b) P1 import-time error · (c) only a P3 collision | **(b) primary, (c) confirmation** | A silent overwrite hides a real double-binding; (b) `@handler` raises `RefRedefined` at import → immediate P1 `COMPILE_ERROR` naming both modules; (c) the same dup is also a P3 `handler_ref` collision, so the snapshot-level oracle confirms it. Never silent (§3.1). |

**Consumed owner-gated forks I do NOT decide (dependencies, tracked elsewhere):** shared-vocab **SF-a**
(panel-action grammar — my P6 `never_strand`/`action_cooldown_parity` arm under its *option A*; §3.2
dependency flag) and **SF-d** (prod-attest custody — spec 05 §9). Both are surfaced in
`open_decisions` as dependencies, never re-decided here.

---

## 9. Labeled deferrals (each bounded by the 43-subsystem + named-amendment corpus)

| Deferral | Reason | Bound |
|---|---|---|
| Leg-B introspection **adapter** for non-command sets (panel `custom_ids`, `event_names`, `task_prefixes`) | The built `SubsystemHost`/`PanelRuntimeView` doesn't exist until K8; over-specifying its internals now would fabricate an interface | The compared sets are exactly the snapshot's `command`/`custom_id`/`event`/`task_prefix` namespace kinds — **closed**. I fix the `BuiltRuntime` Protocol (§3.3); K8 fills the adapter. |
| The golden / **intended-divergence** parity lane (FJ **L-11**) | Orthogonal to this oracle: three-way parity proves *structural* identity (runtime = manifest); the golden harness proves *behavioral* equivalence to the old bot (or a reviewed delta). That lane is K10 + owner-gated | Boundary stated, not designed: parity oracle = "runtime is what the manifest says"; golden harness (K10) = "behavior matches old bot / reviewed delta." |
| Shared-verb computation + 100/25/1 cap budget + nav-node deep-link enumeration (FJ **L-14**) | Namespace-corpus algorithms owned by the K1 sibling (T1-5, owner-answered; spec 03 §3.5/§3.6) | The compiler **provides** the snapshot K1 computes over (`projections.namespace`, `command` kind, both surfaces); the *algorithm* (shared-verb walk, cap demotion) is K1's — P3 only *calls* K1's `validate` and re-runs its cap guard every compile. |
| Per-amendment grammar dataclass design for G-9…G-24 | That is the Gate-0 *fold* + each amendment's owning K-step, not the minting authority | Exactly the 16 G-rows + 15 R-riders + 4 P + refuted set enumerated in FINAL-REVIEW §3 — the registry indexes them; the fold designs them. |
| `store_retirements.yml` **`disposition`** field's data step (export vs reverse-migrate vs declared-loss) | A genuine data-loss policy call (see §8 fork 8 / open_decisions) — mirrors L-18's rollback-disposition class | Bounded to store drops; the *mechanism* (a **required** `disposition:` field, no default) is designed; the *chosen value per store* is the owner's per-retirement call. |
| **SF-a option-B derived-field path** for `never_strand` button-binding + `action_cooldown_parity` | The panel-action grammar (spec 02 §8-a) is owner-gated; option A is the recommended default and armed now | Bounded: under option B the two predicates read the panel-owned cooldown + the panel's declared component list; the switch is a field-path change, not a new predicate (§3.2 dependency flag). |

---

## 10. Retirement map (V-3 binding — nothing evaporates)

| Ledger row / queue item | How this spec retires it |
|---|---|
| **FJ "no buildable compiler" linchpin gap** (the whole assignment) | The §3.2 pipeline (9 passes + `_project`) + §3.4 forward oracle **are** the compiler; the backward reflection paths (§2 table) are retired. |
| **FJ L-14** (K1 corpus "computed at compile from the live ledger") — *mechanism half* | The snapshot's `projections.namespace` (both surfaces, subcommands expanded — the K1-required node shape, §4.2) is the single derived corpus K1 computes over (no live-ledger walk). The shared-verb/cap/deep-link *algorithm* stays K1's (deferred §9). |
| **FJ L-11** (three-way parity vs golden lane) — *structural half* | §3.4 delivers snapshot ⇄ built-runtime ⇄ Discord-remote parity (leg A/B/C), reusing the path set-diff. The intended-divergence *golden* lane boundary is named, not designed (deferred §9). |
| **FJ L-5** (panel = a second, cooldown-free resolver) | P6 `action_cooldown_parity` makes a mutating `PanelActionSpec` without cooldown/audit parity a `SEMANTIC_VIOLATION` (armed under §8-a option A; §3.2 dependency flag). |
| **FJ L-4 / L-25** (fabricated `contracts.py:48-52` / `WorkflowResult`) | Consumed-seam correction (§4.2, canonicalized in shared-vocab §0/RC-1): the `WorkflowRef` return is `WorkflowResult|None` (the K7 superset of the **real** `LifecycleResult`); `services/lifecycle/contracts.py:48-52` is **REAL** and the fabricated cite is the absent `disbot/core/contracts.py`; **`StageResult` is NOT a dispatch return**. Re-verified against source; the earlier line-359 conflation is fixed. |
| **runtime-logic-mechanics #92 & #217** (amendment registry unminted; G-numbers collided 3×; G-9 contested) | §3.7 `rebuild-amendments.yml` + `check_amendments.py` — the sole minting authority, built before Gate-0. |
| **T2-18** (ratify static-stable + dynamic-versioned custom_id two-population model) | P3 (via K1 `validate`) **enforces** the two-population disjointness once the owner ratifies (a legacy `custom_id_override` may not begin with a scheme token; every canonical mint collides against the frozen legacy set). Enforcement designed; ratification stays the owner's. |
| **Q-0162 backward manifest spine** (`command_manifest`/`panel_manifest`/`manifest_reconciliation`) | Superseded by the forward projection; the deferred `DANGLING_PANEL_ACTION` heuristic becomes the real `never_strand` pass (declared bindings). |
| **RC-7** (01's `validate_snapshot`/`Collision(kind,value,claimant_a,claimant_b)`/`is_reserved(kind,value)` seam) | **RECONCILED** — §4.2 adopts K1's `validate(snapshot)->NamespaceReport`, `Collision(+scope)` key `(kind,value,scope)`, `is_reserved(value,kind,…)`; `Violation` gains `scope`; P3 maps all three violation categories. |
| **RC-1** (result-grammar mis-cite) | **FIXED** — the `WorkflowRef` return seam is `WorkflowResult|None`; `StageResult` removed from it; the real vs fabricated `contracts.py` distinction stated at every mention. |

Owner-queue tiers touched: **T2-18** (enforcement designed, ratify = owner) · **T2-22** (ConfigSpec
preflight consumed as a boot-order seam, §4.2) · the **store-drop disposition default** (new surfaced
owner call, §8 fork 8). No T1 row is decided here (T1 all resolved, Q-0237a–g — honored, not re-opened).

---

## 11. Build order (design-spec §9)

- **Pre-K2 / Gate-0 prerequisite:** `rebuild-amendments.yml` + `check_amendments.py` (§3.7) — built
  **before** the Gate-0 fold, so the fold that stamps G-9…G-24 `in-spec` works off a collision-free
  list. **Blocks:** Gate-0.
- **K2 (the grammar band):** `tools/manifest_compile.py` (passes P1–P9 + `_project`), `sb/spec/refs.py`
  (+ the `RefRedefined` guard) + `roles.py`, the snapshot serializer (the `compiler_version`-excluded
  hashed body, §5), the failure taxonomy, leg-A recompile-parity, and the arrangement-invariance test
  (§2.10.2). This is where §9.1 places "manifest compiler + snapshot + validators." P3 is defined here
  as a thin call into K1's `validate` (which lands at K1, one step earlier).
- **Armed later (contract defined at K2, activates when its input lands):** P7 store-completeness
  **arms at K3** (when `projections.stores` + the derived schema exist; dormant/no-op until then, and a
  `baseline=None` first compile only ever adds — §3.6); leg-B build-parity arms at **K8** (when
  `build_runtime` exists); leg-C remote-parity arms at **K8** (needs gateway connect), reusing
  `command_tree_sync`.
- **What it blocks:** the snapshot is the spine *everything* declares into — **K3** (db from
  `StoreSpec`), **K4** (events from `EventSpec`), **K5–K10**, and **all of Phase 4** (every port lands
  a manifest that must compile green) consume it. This function is the gate the entire kernel and port
  order sit behind.
