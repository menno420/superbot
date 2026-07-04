# Strand 1 · Kernel spine · ⑧ The K1 namespace registry

> **Phase-B foundational design.** Docs-only. Designs the K1 registry's genuinely-undesigned gap to
> buildable depth against the frozen upstream contracts (design-spec §1.1/§2.2/§3.1–§3.5/§9.1; router
> Q-0219…Q-0237, esp. Q-0224 + Q-0237(e/f); FJ Fable-5 L-14/T1-5/T1-6). A fresh agent builds this
> from this file + those contracts making **zero** further design decisions.
>
> **Design against, never reverse:** Q-0237(a–g) — esp. **(e)** slash-common + prefix-long-tail and
> **(f)** decided deep-link names canonical / shipped `-menu` names as hidden aliases.
>
> **Spot-verified seams (2026-07-04, against shipped source):**
> - The **only** name reservation today is `_RESERVED_CAPABILITY_PREFIXES = {_internal, system,
>   governance}` + `is_reserved_capability(cap)` (`utils/subsystem_registry.py:1244-1250`; `cap` head
>   ∈ the set → reserved, **with no notion of an owning subsystem** — the owner map is net-new here,
>   §3.2/§7); the capability format `{subsystem}.{resource}.{action}` is enforced at `Capability.parse`
>   (`:1270-1279`, header rule `:7-8`). There is **no pre-boot command-name registry**.
> - The load-time collision site is `_load_cogs` (`bot1.py:697-736`): a second name claimant raises
>   `CommandRegistrationError` inside `bot.load_extension`; the post-load ledger (`SUBSYSTEMS`
>   entry-point presence check, `:722-736`) is **blind** to load-time name collisions — it only
>   downgrades subsystems whose entry points never loaded.
> - **Ground-truth corpus is flat-only (the L-14 root), and carries no ranking/scope fields:**
>   `command-surface.json` is **271 flat rows** with **exactly six fields** `{name, aliases, kind,
>   perm, cog_file, lineno}` (verified) — **no `usage_weight`, no `namespace_id`, no subcommand
>   markers, no context-menu kind**. Kind counts: `prefix 224 / slash 30 / group 17`. The 17
>   `kind:group` rows (`btd6ops`, …) are **single rows with their subcommands collapsed** (`btd6ops` →
>   `btd6menu`, one row). Computing shared verbs over it yields **1** cross-cog name collision
>   (`platform`); the live expanded tree yields **11**. **The JSON must not be the corpus.** (Because
>   the harvested corpus has none of the manifest [O]/scope fields, every Stage-2 sort key is **defined
>   from the six harvested fields alone** — §3.5.)
> - Slash top-level count on the harvested corpus is **30 flat-slash + 17 groups = 47 ≤ 100**, so the
>   §3.5 prefix-long-tail demotion is **dormant on the real corpus** (grouping only shrinks it further);
>   it is a deterministic safety valve for future growth, fully specified below so it is buildable
>   whether or not it ever fires.
> - **Seam correction carried (Q-0120, FJ L-4/L-25):** there is **no `WorkflowResult` class and no
>   `disbot/core/contracts.py`** (verified absent). The real result vocab is
>   `disbot/services/lifecycle/contracts.py` (`LifecycleResult:77`, `LifecyclePreview:66`,
>   `StepResult:56`, outcomes `SUCCESS/PARTIAL/BLOCKED/DECLINED/DISCORD_FAILED:48-52`, reversibility
>   `:40-42`) + the dispatch analogue `StageResult` (`message_pipeline.py:181`). A trigger-set
>   rejection surfaces as `outcome=BLOCKED` on *that* real constant, never the fabricated type (§3.4).

---

## 1. Summary + the exact undesigned gap

**Already frozen upstream — not re-designed here (anti-pad).** Design-spec **§3.1** froze *one
registry, typed kinds, derived index + the frozen compat core* `legacy_reservations.json`; **§3.2**
froze *declaring-is-reserving, two-phase* (import → CI → boot, collision → `FAILED_STARTUP` naming
both claimants); **§3.3** froze the tombstone *primitive* `reserve_tombstone(kind, value, reason,
provenance)`; **§2.2/G-6** froze *per-`kind` scoping* (prefix `!karma` and slash `/karma` coexist —
one system, kind-keyed partition); **§3.5** froze the *two-mechanism* split (runtime-string registry
vs the `check_symbol_shadowing.py` AST companion). This spec does **not** restate any of it — it
builds the machine the L-14/T1-5/T1-6 amendments demand *inside* that frozen shell.

**The gap this closes** (seven things the spec names but never makes buildable):

| # | Undesigned gap (today) | This spec delivers |
|---|---|---|
| G-a | `is_reserved` has **no runtime read surface** — the registry is compile/CI/boot only; custom triggers (Q-0225) need a set-time query | §3.3 `ReservationIndex.is_reserved(value, kind, *, surface, parent)` + `check_trigger(...)`, over the frozen boot-built index |
| G-b | scoping is per-`kind` only — can't tell `/ticket close` from `/thread close` (subcommand verbs would false-collide) | §3.2 the **`(kind, surface, parent_group)` scope key** + the exact collision rule |
| G-c | `check_namespace` (CI) and boot re-validation are named as **two** things → they can drift (the #763 false-green class) | §3.2 **one** pure oracle `validate(snapshot) -> NamespaceReport`; CI, `git merge-tree`, and boot call the *same* function on the *same* data — CI-green ⟺ boot-green by construction |
| G-d | the 100/25/1-nest cap is **unbudgeted prose** (L-14, T1-5) | §3.5 the **exact cap-budget algorithm** — counting rules + the deterministic prefix-long-tail demotion (with its Stage-2 sort keys fully defined) + the hard compile guard |
| G-e | Q-0231 nav-node deep-links are **minted outside the corpus** K1 computes over (L-14 deep-link leg) | §3.6 the **corpus-computation order** — nav-nodes enumerated *first*, then the shared-verb walk |
| G-f | the shared-verb set is computed over the **broken flat JSON** (1 vs 11, L-14) | §3.6 compute over the **live expanded corpus** (`bot.commands` walk at Stage-2 / `projections.namespace` at compile), never `command-surface.json` |
| G-g | tombstones and "banned" names (common-word trigger blocklist, retired names) have **no unified query** | §3.7 **tombstone/ban-as-reservation** — one `Origin` enum; `is_reserved` returns it, so "taken / renamed → X / banned" is one answer |

One sentence: **K1 becomes the single pre-boot oracle that reserves every runtime string identity
across a `(kind, surface, parent_group)` scope, budgets the Discord command caps, and answers
`is_reserved` at runtime — so the Q-0211 collision class dies at CI + merge + boot, never at
`add_cog`.**

**Normative seam note (read before building against 01).** The namespace reservation contract is
**K1-owned**. Where the sibling compiler spec (01 §4.2) states a *different* name / return type / arg
order / collision-key arity for the same seam, **this file wins** — §4.2 below states the reconciliation
explicitly and marks 01's stated shape superseded. A builder building the compiler from 01 must wire
its P3 `namespace` pass to **this** contract.

---

## 2. Files / modules it becomes

| New path | Layer | Role |
|---|---|---|
| `sb/namespace/kinds.py` | `sb/namespace/` (**stdlib-only leaf**, §1.1) | `NamespaceKind` (16), `Surface`, `Origin` enums; `CommandScope`; `normalize(value, kind)`; `namespace_id(value, scope)` (the deterministic Stage-2 sort/identity key, §3.5). |
| `sb/namespace/records.py` | leaf | `ReservationRecord`, `ReservationHit`, `Collision`, `CapViolation`, `FormatError`, `NamespaceReport`. |
| `sb/namespace/validate.py` | leaf | **The one oracle** `validate(snapshot) -> NamespaceReport`; builds + returns the `ReservationIndex`. |
| `sb/namespace/index.py` | leaf | `ReservationIndex` (frozen after build) + the runtime read API (`is_reserved`, `resolve_command`, `command_corpus`). |
| `sb/namespace/triggers.py` | leaf | `check_trigger(word, *, index, min_len) -> TriggerAvailability` — the Q-0225 set-time consumer. |
| `sb/namespace/legacy_reservations.json` | committed (frozen compat core, §3.1) | Generated-once, hand-ratified: 43 subsystem keys, verbatim legacy custom_ids, settings-key vocab, capability strings + the **reserved-prefix owner map** (§3.2), actor types, event names. |
| `sb/namespace/tombstones.json` | committed (append-only) | Tombstones + bans (retired/renamed names, the common-word trigger blocklist, the bare `ActionSpec` string). §3.7. |
| `sb/namespace/slash_pins.json` | committed (Stage-2 seed; **empty by default**) | Hand-ratified qualified command names force-kept on the slash surface — removed from the demotion candidate pool before the §3.5 sort. Empty on the harvested corpus (it fits under 100); the reviewable override if a future corpus overflows. §3.5. |
| `tools/check_namespace.py` | `tools/` (never imported at runtime) | The required CI check: loads the committed snapshot, calls `validate`, prints violations, exits nonzero if `not ok`. |
| `tools/compute_corpus.py` | `tools/` | The Stage-2 corpus-computation procedure (§3.6): nav-nodes-first → live-ledger walk → shared-verb set → cap-budget → per-subsystem naming list + the initial `legacy_reservations.json` + the (initially empty) `slash_pins.json`. Run **once** at Stage-2. |

**Shipped paths this SUPERSEDES:**

| Shipped path | Fate |
|---|---|
| `utils/subsystem_registry.py` `_RESERVED_CAPABILITY_PREFIXES` + `is_reserved_capability` (`:1244-1250`) | **Superseded.** Generalized into the `capability` kind of the full registry; the reserved prefixes `_internal/system/governance` port as `legacy_reservations.json` entries **with an owner** (§3.2 — the owner map is net-new; the shipped predicate has no owner notion); the 3-part format (`:1270-1279`) becomes P3's `FormatError` check. |
| `bot1.py:697-736` `_load_cogs` collision path (`CommandRegistrationError` at `add_cog`; post-load ledger blind) | **Retired.** A name collision now dies at CI (P3) + `git merge-tree` + boot leg-A **before any network connection** — never as a runtime `add_cog` crash-loop, never invisible to the ledger. |

---

## 3. The complete public contract

### 3.1 Kinds, surfaces, origins, and the scope key

```python
# sb/namespace/kinds.py  — stdlib-only leaf
class NamespaceKind(str, Enum):
    COMMAND="command"; CUSTOM_ID="custom_id"; EVENT="event"; SETTING_KEY="setting_key"
    SUBSYSTEM_KEY="subsystem_key"; CAPABILITY="capability"; PANEL="panel"; HANDLER_REF="handler_ref"
    TASK_PREFIX="task_prefix"; STAT_KEY="stat_key"; ITEM_KEY="item_key"; AI_TASK="ai_task"
    CONTEXT_ID="context_id"; ACTOR_TYPE="actor_type"; INVARIANT_TAG="invariant_tag"; TABLE="table"
    # ^ the 16 kinds frozen at design-spec §3.1, verbatim.

class Surface(str, Enum):
    PREFIX="prefix"; SLASH="slash"          # CommandSpec.kind="both" expands to ONE reservation per surface

class Origin(str, Enum):
    MANIFEST="manifest"   # derived from a live SubsystemManifest spec (the derived index, §3.1)
    LEGACY="legacy"       # frozen compat core (legacy_reservations.json), compat=True
    TOMBSTONE="tombstone" # retired/renamed; never claimable; may carry renamed_to
    BAN="ban"             # permanent deny, no successor (ActionSpec string, common-word blocklist)

# Scope: only the COMMAND kind has a 2-D scope; every other kind is global.
@dataclass(frozen=True)
class CommandScope:
    surface: Surface
    parent_group: str | None = None    # dotted group PATH, ≤2 segments (1-nest): None | "ticket" | "ticket.admin"

def normalize(value: str, kind: NamespaceKind) -> str:
    return value.casefold() if kind is NamespaceKind.COMMAND else value   # commands case-insensitive (Discord); else byte-exact (§3.2)

def namespace_id(value: str, scope: "CommandScope | None") -> str:
    # The deterministic identity/sort key for a command reservation — a TOTAL order under str sort.
    # Derivable from the six harvested corpus fields alone (no manifest/telemetry field needed): §3.5.
    if scope is None:
        return f"//{value}"                                   # non-command kinds (global)
    return f"{scope.surface.value}/{scope.parent_group or ''}/{value}"
```

**The scope key (I own).** Every reservation is keyed by `(kind, normalize(value), scope)` where
`scope = CommandScope(surface, parent_group)` for `kind=command`, and `scope = None` (global) for
every other kind. This is the minimal extension of the frozen G-6 per-`kind` partition that also
scopes **subcommands to their parent group**. `namespace_id(value, scope)` is the string form of that
key — a deterministic total order used as the tie-break in §3.5.

**The collision rule (I own — one rule, all kinds):** two reservations **collide** iff same `kind`
**and** same `normalize(value)` **and** same `scope`. Worked cases:

| A | B | Collide? | Why |
|---|---|---|---|
| `/ticket close` | `/thread close` | **No** | `CommandScope(slash,"ticket")` ≠ `CommandScope(slash,"thread")` |
| `!karma` | `/karma` | **No** | surfaces differ → different scope (the frozen G-6 fix) |
| `/give` (economy) | `/give` (inventory), both top-level | **Yes** | identical `CommandScope(slash, None)` — the Q-0211 class, killed |
| `/close` (top-level) | `/ticket close` (sub) | **No** collision, but see §3.6 | different scope; if `close` is *shared*, §3.6 forces the grouped form so the top-level `/close` never ships |
| `settings_audit.back` | `settings_audit.back` | **Yes** | `custom_id` kind, global scope, byte-exact |

### 3.2 The one shared CI ⇄ pre-boot oracle (I own)

The frozen §3.2 names three kill sites (import, CI `check_namespace`, boot re-validate). The
undesigned risk is that **CI and boot run different code** and disagree (the #763 false-green class,
Q-0120). The fix: **one pure function**, called by all of them.

```python
# sb/namespace/records.py
@dataclass(frozen=True)
class ReservationRecord:
    kind: NamespaceKind
    value: str                     # normalized
    scope: CommandScope | None
    origin: Origin
    owner: str | None              # owning subsystem key (manifest/legacy); None for tombstone/ban
    spec_id: str | None            # declaring spec id — provenance + TargetRef assembly (§4)
    source: str                    # "subsystem@file:line" | "legacy_reservations.json" | "Q-0NNN"
    renamed_to: str | None = None  # tombstone successor → the helpful "renamed to X" error
    reason: str | None = None      # tombstone/ban reason

ReservationHit = ReservationRecord

@dataclass(frozen=True)
class Collision:
    kind: NamespaceKind; value: str; scope: CommandScope | None   # scope is LOAD-BEARING (see §4.2 seam note)
    claimant_a: str; claimant_b: str      # "subsystem@file:line" of each claimant

@dataclass(frozen=True)
class CapViolation:
    cap: str                        # "top_level_100" | "sub_25" | "nest_1"
                                    #   (reserved, dormant: "user_context_5" | "message_context_5" — §3.5)
    locus: str                      # "" (global) | the group path that overflows
    count: int; limit: int
    members: tuple[str, ...]        # overflowing names, sorted (deterministic)

@dataclass(frozen=True)
class FormatError:
    kind: NamespaceKind; value: str; detail: str   # e.g. "capability_not_3_part"; "reserved_prefix_misuse"

@dataclass(frozen=True)
class NamespaceReport:
    ok: bool
    collisions: tuple[Collision, ...]
    cap_violations: tuple[CapViolation, ...]
    format_errors: tuple[FormatError, ...]
    index: "ReservationIndex"        # built once here, REUSED at boot (the shared-oracle guarantee)

# sb/namespace/validate.py — imports neither spec nor manifests (§1.1 line 273): pure data in, report out
def validate(
    snapshot: dict,
    *,
    legacy_path: str = "sb/namespace/legacy_reservations.json",
    tombstone_path: str = "sb/namespace/tombstones.json",
) -> NamespaceReport: ...
```

**What `validate` does (deterministic, collect-all):**
1. Build the index from three pure-data origins: `snapshot["projections"]["namespace"]`
   (origin=`manifest`), `legacy_reservations.json` (`legacy`), `tombstones.json` (`tombstone`/`ban`).
   The `namespace["command"]` nodes carry the exact per-node shape declared in §4.2 (both surfaces,
   `parent_group`) — that shape is a K1-owned requirement on the compiler, not an assumption.
2. **Collisions** — for each `(kind, value, scope)` claimed ≥2×, emit a `Collision` naming both
   claimants + both source loci (**the `scope` field is carried** so `/ticket close` vs `/thread
   close` and `!karma` vs `/karma` never false-collide — §4.2). Cross-origin rules: `manifest` vs
   `legacy(compat)` is **OK iff same owner** (compat is claimable only by its recorded owner, §3.1),
   else `Collision`; `manifest` vs `tombstone`/`ban` is always a `Collision` (`reserved_tombstone` /
   `banned_name`), carrying `renamed_to` in the detail.
3. **Format (P3 owns; see the P3/P4 split below)** — every `capability` value matches
   `{sub}.{res}.{action}` (else `FormatError("capability_not_3_part")`) **and** its head obeys the
   **reserved-prefix owner rule**: if `sub ∈ {_internal, system, governance}` and the declaring
   manifest's subsystem key ≠ that prefix's registered owner, emit
   `FormatError("reserved_prefix_misuse")`. The owner map (net-new — the shipped
   `is_reserved_capability` has no owner notion) is committed in `legacy_reservations.json`:

   ```
   RESERVED_PREFIX_OWNERS = {
       "_internal":  "core",        # kernel/composition framework — NO domain subsystem may mint _internal.*
       "system":     "system",      # the ops/system subsystem (K5 ops rails)
       "governance": "governance",  # the governance layer
   }
   ```
   i.e. the owning framework subsystem MAY mint its own prefix; everyone else is a `FormatError`.
   `subsystem_key` is frozen-verbatim (rename → `FormatError`, compat item 1).
4. **Cap budget** — §3.5 over the slash partition.
5. Return `NamespaceReport(ok = no collisions ∧ no cap_violations ∧ no format_errors, …, index)`.

**Capability-validation ownership split (P3 ⇄ P4 — closes the double-owned overlap).** The two passes
partition the work with **no overlap and no gap**:
- **P3 (K1, here)** owns capability **string identity**: the 3-part `{sub}.{res}.{action}` *format* and
  the *reserved-prefix owner* rule (both `FormatError`). This is a pure namespace check — no lane
  knowledge.
- **P4 (compiler authority, 01 §3.2)** owns capability **lane resolution**: `authority_ref → lane`,
  lane-exclusivity, "capability resolves to a real lane." P4 does **not** re-check format/reserved-prefix
  (P3 already proved it, and P4 runs after P3). "capability not namespace-reserved" in 01's P4 prose is
  the *lane* side (an authority ref must point at a capability P3 has admitted), **not** a second
  format check.

**Three callers, one function** (this is the whole point):

| Caller | Site | Input | On `not ok` |
|---|---|---|---|
| CI required check | `tools/check_namespace.py` | the committed `manifest.snapshot.json` | exit nonzero; print every `Collision`/`CapViolation`/`FormatError` |
| Merge safety | `git merge-tree` re-run (§3.2 phase 2, carried from the current repo) | the **merge-result** snapshot | red before either PR merges (two individually-green PRs that collide together) |
| Boot | the compiler's **P3 `namespace` pass** (sibling 01 §3.2) → `sb/app` leg-A | the recompiled snapshot | `fail_startup(report)` → `FAILED_STARTUP`, pre-network, named culprit pair |

Because all three call `validate(snapshot)` on pure data with no hidden state, **a green CI run and a
green boot are the same verdict by construction** — closing the false-green class (Q-0120).

### 3.3 The runtime read surface (I own — the net-new API)

The index `validate` builds is frozen and handed to the composition root at boot; the runtime reads
it. **No DB, no mutation after boot** — every runtime name is either a manifest identity (immutable)
or a custom trigger (stored elsewhere, §5), so the reservation set never changes at runtime.

```python
# sb/namespace/index.py — stdlib-only leaf; frozen after build
@dataclass(frozen=True)
class ReservationIndex:
    _by_key: Mapping[tuple[NamespaceKind, str, CommandScope | None], ReservationRecord]

    def is_reserved(self, value: str, kind: NamespaceKind, *,
                    surface: Surface | None = None, parent: str | None = None) -> ReservationHit | None:
        """The canonical predicate — a POINT query, not the exhaustive oracle (that is `validate`).

        surface: for kind=command, if given, checks only that surface's scope; if omitted (None),
                 checks BOTH surfaces (conservative — a name reserved in either is unavailable). For
                 non-command kinds, surface/parent are ignored (global scope).
        parent:  the parent-group scope to query. parent=None (default) restricts the query to the
                 TOP-LEVEL scope (parent_group is None). To query a subcommand scope explicitly, pass
                 parent="ticket". There is NO any-parent wildcard here — exhaustive cross-scope
                 collision detection is `validate`'s job. Consequence (relied on by check_trigger): a
                 word equal to a SUBCOMMAND name (e.g. 'close', a subcommand of /ticket) with the
                 default parent=None is reported AVAILABLE, because a bare word is only matched against
                 top-level invokable names and a subcommand is not bare-word invokable — so it cannot
                 shadow anything.
        Returns the blocking ReservationHit (carrying origin + renamed_to + reason), or None.
        """

    def resolve_command(self, name: str, *, surface: Surface) -> ReservationHit | None:
        """Exact command lookup returning a LEAF-SAFE record (owner + spec_id + qualified path) —
        NOT a TargetRef. The resolver/composition (K8) assembles the TargetRef from spec_id (§4 seam
        correction). None ⇒ not a declared command on that surface."""

    def command_corpus(self, surface: Surface) -> frozenset[str]:
        """The fuzzy candidate set (C-5 consumes). K1 owns the CORPUS; C-5 owns the AUTO/SUGGEST/NONE
        thresholds (§9)."""

    def all_for_kind(self, kind: NamespaceKind) -> frozenset[str]: ...
```

**The first consumer — custom-trigger set-time validation (Q-0225 §2.1, T2-12):**

```python
# sb/namespace/triggers.py
@dataclass(frozen=True)
class TriggerAvailability:
    available: bool
    reason: str | None                 # "reserved_command"|"tombstoned"|"banned_common_word"|"too_short"|None
    conflict: ReservationHit | None    # the blocking record when available=False

def check_trigger(word: str, *, index: ReservationIndex, min_len: int) -> TriggerAvailability:
    # ONE lookup against the real is_reserved API, then branch on hit.origin.
    # (Common-word bans are stored kind="command", origin="ban" — §3.7 — so a single COMMAND lookup
    #  covers reserved commands, tombstones AND bans; the origin disambiguates the reason.)
    w = word.casefold()
    if len(w) < min_len:
        return TriggerAvailability(False, "too_short", None)

    hit = index.is_reserved(w, NamespaceKind.COMMAND, surface=None)   # both surfaces, top-level scope
    if hit is None:
        return TriggerAvailability(True, None, None)

    reason = {
        Origin.BAN:       "banned_common_word",
        Origin.TOMBSTONE: "tombstoned",
        Origin.MANIFEST:  "reserved_command",
        Origin.LEGACY:    "reserved_command",
    }[hit.origin]
    return TriggerAvailability(False, reason, hit)
```

Custom triggers stay **additive** at runtime (the union rule, Q-0225 — never K1's concern);
`check_trigger` only gates *set-time*, so a guild can never register a word that shadows a reserved
command, a tombstone, or a common word. This is the sole runtime use of `is_reserved`. (A word equal to
a *subcommand* name is available — see the `is_reserved` docstring; subcommand names are not bare-word
invokable.)

### 3.4 §2.7 result seam — a rejection is `BLOCKED`, built on the REAL constant

K1 does **not** construct a result-grammar object (it is a leaf; the workflow engine owns results).
When the invocation subsystem's trigger-set workflow calls `check_trigger` and gets
`available=False`, it maps that into the §2.7 grammar as `outcome = BLOCKED` — the **real**
`disbot/services/lifecycle/contracts.py:50` constant (there is no `WorkflowResult`; L-4/L-25), built
on the shipped `LifecycleResult`/`StageResult` (`message_pipeline.py:181`) — plus a `user_message`
from `reason`. K1 supplies the `reason`; the engine supplies the shape.

### 3.5 The cap-budget algorithm (I own — L-14/T1-5 made buildable)

Discord caps the **slash** surface only (prefix is uncapped — the "long-tail" escape, Q-0237e). The
budget runs over the `kind=command, surface ∈ {slash}` partition (`kind="both"` counts toward slash).

| Cap | Rule | `CapViolation.cap` |
|---|---|---|
| **≤ 100 top-level** | count of distinct top-level slash names (a grouped family `/ticket …` counts as **1**) ≤ 100 | `top_level_100` |
| **≤ 25 children** | for each group *G* and each subcommand-group *SG*: direct children ≤ 25 | `sub_25` |
| **1 nest** | tree depth ≤ 2 below root (root → {subcommand \| subcommand-group → subcommand}); a subcommand-group MUST NOT contain a subcommand-group | `nest_1` |

**Context-menu caps — out of scope, verified empty (closes the context-menu nit).** Discord also caps
user-context and message-context menu commands at **5 each**. The harvested corpus contains **zero**
context-menu commands (`kind ∈ {prefix, slash, group}` only — verified; there is no `user`/`message`
context kind), so no context-menu surface exists to over-budget. The two cap constants
`user_context_5` / `message_context_5` are **reserved but dormant** in the `CapViolation.cap` enum
(§3.2) so that if a rebuild subsystem ever declares a context menu, the guard extends by adding a
count over a `Surface`-analogous context partition — no structural change. Until then they never fire.

**Two enforcement points, distinct jobs (fork §8-4):**
- **Stage-2 assignment (`tools/compute_corpus.py`, §3.6)** — *produces* a fitting surface: shared
  verbs are grouped (shrinking top-level count); if still > 100, **demote the long tail to
  prefix-only** by the **deterministic rule** below. This writes each command's final `surface` into
  its manifest.
- **Compile guard (`validate`, P3)** — a pure **count-and-compare**; it never auto-demotes and never
  reads any ranking field. If the committed manifests declare a slash surface that violates any cap →
  `CapViolation` → CI-red / `FAILED_STARTUP`. This guard is mandatory: Discord itself rejects the 101st
  top-level command, so a green compile over an over-budget surface would crash-loop at registration
  (exactly the class K1 exists to kill).

**The deterministic demotion rule — sort keys fully defined at Stage-2 (closes the usage_weight /
namespace_id gap).** The overflow candidates are sorted and demoted from the top until the slash
top-level count is ≤ 100. Sort key: **`(usage_weight asc, namespace_id asc)`** — but at Stage-2 both
keys are pinned to values derivable from the six harvested corpus fields alone:

1. **`usage_weight`** is a manifest **[O]** field (01 §5 `field_roles`) that **does not exist at
   Stage-2** — the rebuild manifests are not authored until *after* naming, and the harvest
   (`command-surface.json`) exports no usage telemetry. Therefore `compute_corpus.py` assigns
   **`usage_weight = 0` to every harvested command**, so the primary key is constant and the demotion
   sorts by **`namespace_id` alone** — fully deterministic from harvested data. Stated as a fallback:
   *when usage_weight is unavailable, the ordering is `(0, namespace_id asc)` ≡ `namespace_id asc`.*
2. **`namespace_id`** for a harvested command is `namespace_id(normalize(name), CommandScope(slash,
   parent_group))` = `f"slash/{parent_group or ''}/{normalize(name)}"` (§3.1) — a total string order,
   so ties are impossible and the demotion is reproducible byte-for-byte across machines.
3. **`slash_pins.json`** (committed, **empty by default**) is subtracted from the candidate pool
   **before** sorting: any qualified name listed there is force-kept on slash. Because equal-weight
   demotion is otherwise ranking-blind, the pin list is the *reviewable, deterministic* escape hatch —
   an agent hand-ratifies pins at Stage-2 **only if** a future corpus overflows and would drop an
   important command. On the harvested corpus it is empty (top-level slash = 47 ≤ 100, so the demotion
   is dormant — see the header seam note).
4. **When real `usage_weight` later exists** (manifests authored, or a telemetry export added to a
   re-harvest), a re-run of the Stage-2 assignment supersedes the pins with weight-driven ordering —
   the sort key `(usage_weight asc, namespace_id asc)` then keeps the most-used commands on slash
   automatically. The compile guard is unaffected (it never reads either key).

This mirrors the sim's namespace-id tie-break (design-spec §2.10.5, "ties broken by namespace-id
sort") — same determinism discipline, applied to surface assignment.

### 3.6 The corpus-computation order (I own — L-14, Q-0224 amendments)

The shared-verb set (Q-0224: a verb used by ≥2 subsystems → grouped `/area verb`; a unique verb →
flat) MUST be computed in this order. Steps 1–4 are the Stage-2 `tools/compute_corpus.py` procedure;
step 5 is the every-compile guard.

| # | Step | Why the order is load-bearing |
|---|---|---|
| 1 | **Enumerate the nav-node deep-link commands INTO the corpus first** — the Q-0231/Q-0237(f) hub openers (`!admin`, `!games` canonical + shipped `!adminmenu`/`!modmenu`/`!economymenu` as hidden aliases), one per hub node | These are real commands (~dozens) **not** in the 271. Running the verb computation without them is blind to a verb that collides with a hub name, and leaves the hub names unreserved (**L-14 deep-link leg**). |
| 2 | **Walk the LIVE EXPANDED corpus** — at Stage-2, recursively walk shipped `bot.commands` (every subcommand a distinct node); at rebuild-compile, read `snapshot.projections.namespace["command"]` (subcommands already expanded by the compiler, **both surfaces carried** — §4.2). **NEVER `command-surface.json`.** | The flat JSON collapses the 17 group rows → **1 shared verb vs 11** live (verified). The expanded corpus is the only correct input (**L-14 root**). |
| 3 | **Compute the shared-verb set** over corpus (steps 1+2): verb → set of owning subsystems; shared iff ≥2 | The anti-liability rule (Q-0224): computed once at design time, so no rename is ever forced at runtime. |
| 4 | **Apply the cap budget** (§3.5): group shared verbs, then, only if still > 100 top-level, prefix-demote the long tail by the deterministic `(usage_weight=0, namespace_id asc)` rule minus `slash_pins` until the slash surface fits 100/25/1-nest | T1-5 (Q-0237e): the 271 corpus does not force every command to slash. Dormant on the harvested corpus (47 ≤ 100); the rule is defined for future growth. |
| 5 | **Reserve + guard** — write the resulting `(name, kind, surface, parent_group)` into each manifest; `validate` reserves them and re-runs the cap guard every compile | The reservation is permanent (Q-0224): nothing can later claim a flat name. |

**Terminology reconciliation with sibling 01 (important — not a contradiction).** Sibling 01's L-14
retirement says K1 computes over `projections.namespace`, "no live-ledger walk." My "live ledger
walk" and 01's "compute over `projections.namespace`" are the **same expanded corpus at two lifecycle
points**: the Stage-2 *harvest* walks shipped `bot.commands` (because the rebuild manifests don't
exist yet, and the flat JSON is broken); the rebuild *compile* reads `projections.namespace` (which
the compiler expanded). Both differ from the flat JSON — that is the whole L-14 point. 01 provides
the corpus source; K1 owns the algorithm over it. **The node shape K1 requires that source to carry
is stated in §4.2** (it is a K1-owned requirement, not left to 01's discretion): both `prefix` and
`slash` surface nodes, each with `parent_group`.

### 3.7 Tombstone / ban as reservation (I own — extends §3.3)

The frozen §3.3 primitive `reserve_tombstone(kind, value, reason, provenance)` becomes a build-time
authoring helper that **appends to `tombstones.json`**; there is no runtime mutation (the derived
registry is immutable after boot). `validate` reads `tombstones.json` as a pure-data origin, so a
tombstone/ban is a first-class reservation that `is_reserved` returns:

- **Tombstone** — a retired/renamed name; `renamed_to` set → the helpful "`X` was renamed to `Y`"
  error for one deprecation window. Claiming it in a manifest → `Collision(reserved_tombstone)`.
- **Ban** — a permanent deny with **no** successor: the common-word trigger blocklist (Q-0225 §2.1,
  stored `kind="command"`, `origin="ban"` — so `check_trigger`'s single COMMAND lookup returns it),
  retired command names that must never be re-minted, and the bare `ActionSpec` **string** (decision
  1). No `renamed_to`. Claiming/setting it → blocked.

**The two-mechanism boundary (§3.5 of the design-spec, honored):** the `ActionSpec` *string* ban
lives here (runtime string identity); the `class ActionSpec` *symbol* ban lives in
`check_symbol_shadowing.py` (the AST companion). Neither subsumes the other — stated so a later agent
deletes neither.

```json
// sb/namespace/tombstones.json  (append-only)
{ "tombstones": [
    {"kind":"command","value":"adminmenu","scope":{"surface":"prefix"},"origin":"tombstone",
     "renamed_to":"admin","reason":"Q-0237f deep-link canonical rename","provenance":"Q-0237f"} ],
  "bans": [
    {"kind":"command","value":"the","origin":"ban","reason":"common-word trigger blocklist","provenance":"Q-0225"},
    {"kind":"custom_id","value":"ActionSpec","origin":"ban","reason":"decision 1 — bare symbol reserved","provenance":"design-spec §3.3"} ] }
```

*(Note: `adminmenu` is shown as a tombstone example of the mechanism; Q-0237f makes the shipped
`-menu` names **hidden aliases**, i.e. `legacy` reservations that still resolve, not tombstones. The
compute_corpus step reserves BOTH `admin` (canonical) and `adminmenu` (alias) — the choice of
alias-vs-tombstone per name is Stage-2 data, the mechanism for both is here.)*

---

## 4. Provides / Consumes

### 4.1 Provides — canonical shapes I own (siblings consume these verbatim)

| Contract | Canonical shape | Primary consumers |
|---|---|---|
| The reservation lifecycle / oracle | §3.2 `validate(snapshot) -> NamespaceReport` (collisions + cap_violations + format_errors + the built index); one function for CI, merge-tree, boot | compiler P3 (01); `tools/check_namespace.py`; `sb/app` leg-A boot |
| The `(kind, surface, parent_group)` scope + collision rule | §3.1 — the scope key + the single "same kind ∧ value ∧ scope" rule; `Collision` **carries `scope`** | compiler P3 (01); anything that reasons about name uniqueness |
| `projections.namespace["command"]` node shape | §4.2 — the exact per-node shape the compiler MUST emit (both surfaces, `parent_group`); a **K1-owned requirement** on 01's snapshot, not 01's discretion | compiler (01) emits it; K1 `validate` + `compute_corpus` index on it |
| Reserved-prefix owner map | §3.2 — `RESERVED_PREFIX_OWNERS = {_internal→core, system→system, governance→governance}`, committed in `legacy_reservations.json` | compiler P3 format check; authority (K6) capability minting |
| Runtime read API | §3.3 `is_reserved(value, kind, *, surface, parent)` (parent=None ⇒ top-level scope), `resolve_command(name, *, surface) -> ReservationHit` (leaf-safe record), `command_corpus(surface)` | the resolver/C-1 (02); the fuzzy engine C-5; the trigger service |
| Custom-trigger set-time gate | §3.3 `check_trigger(word, *, index, min_len) -> TriggerAvailability` (no `blocklist_kind` param — removed; the single COMMAND lookup + `origin` branch covers ban/tombstone/reserved) | the invocation subsystem's trigger-set workflow (T2-12) |
| Cap-budget enforcement | §3.5 — the count rules + the deterministic prefix-demotion (Stage-2 keys defined: `usage_weight=0` default, `namespace_id` total order, `slash_pins`) + the compile guard | `tools/compute_corpus.py`; compiler P3 |
| Corpus-computation order | §3.6 — nav-nodes-first → live-expanded walk → shared-verb → cap → reserve | `tools/compute_corpus.py`; Stage-2 naming |
| Tombstone/ban-as-reservation | §3.7 — `Origin` enum; `tombstones.json` schema; `is_reserved` returns origin + `renamed_to` | trigger gate; the "renamed to X" error path; the AST companion (boundary) |

### 4.2 Consumes — sibling shapes I assume (stated exactly for the seam pass)

**Seam reconciliation with 01 (NORMATIVE — supersedes 01 §4.2 / §3.2 P3 for this seam).** 01 states it
consumes `namespace.validate_snapshot(snapshot) -> list[Collision]` with `Collision(kind, value,
claimant_a, claimant_b)`, `is_reserved(kind, value)`, and a `(kind, value)` collision key. **K1 owns
this contract; those names/shapes are superseded** as follows, and a builder wiring 01's P3 must use
the K1 forms:

| 01 §4.2 stated (superseded) | K1 canonical (wins) | What the P3 builder does |
|---|---|---|
| `validate_snapshot(snapshot) -> list[Collision]` | `validate(snapshot) -> NamespaceReport` (§3.2) | call `report = validate(snapshot)`; map `report.collisions`/`.cap_violations`/`.format_errors` into `Violation`s (`claimant_a/b` copy straight across) |
| `is_reserved(kind, value)` (kind first) | `is_reserved(value, kind, *, surface, parent)` (**value first, kind second**) (§3.3) | positional call is `is_reserved(value, kind)` — swap 01's argument order; it is the runtime read surface, not used by P3's collision emit |
| `Collision(kind, value, claimant_a, claimant_b)`, key `(kind, value)` | `Collision(kind, value, **scope**, claimant_a, claimant_b)`, key `(kind, value, scope)` (§3.1/§3.2) | 01's `Collision` dataclass **must add `scope`**; the `(kind, value)` key is superseded — it would false-collide `/ticket close` vs `/thread close` and `!karma` vs `/karma`, the exact cases K1's scope key exists to separate |

| Assumed contract | Precise assumption my code depends on | Owning sibling | If wrong |
|---|---|---|---|
| Manifest snapshot / compiler pass pipeline | `snapshot["projections"]["namespace"]` is the derived corpus **with subcommands expanded**; per-command nodes carry the **K1-required shape** `{value:str, kind:"command", surface∈{"prefix","slash"}, parent_group:str\|None, subsystem:str, source:"file:line"}`; **BOTH surfaces are carried** (prefix commands are runtime string identities K1 reserves even though they never reach Discord's tree — the parity legs' slash-only `_local_paths` is a *different*, narrower set, 01 §3.4); **`validate` is registered as the compiler's P3 `namespace` pass** and is a pure function of the snapshot (no manifest/spec import). 01 §5 renders this inner node as `{…}`; **§4.1 above declares the shape authoritatively** and 01 must emit it. | strand-1 · ① compiler (01) | K1 can't build the index / P3 can't run pure-data / prefix identities go unreserved |
| Nav-node deep-links present in the corpus | the compiler enumerates the Q-0231/Q-0237(f) nav-node commands into `projections.namespace` (I own the *ordering requirement* §3.6-step-1; 01 owns *carrying them in the snapshot*) | strand-1 · ① compiler (01) | step-1 of §3.6 is blind again (L-14 deep-link leg reopens) |
| `authority_ref` → capability | one public `authority_ref: str` (Q-0237d) resolves internally to a capability string in the `{sub}.{res}.{action}` namespace; the reserved prefixes `_internal/system/governance` are `legacy` entries K1 loads **with owners** (§3.2). P3 owns capability *format + reserved-prefix owner*; P4 owns *lane resolution* (the split above) | strand-1 · authority (K6) / 02 | P3 `FormatError` for capability strings can't be scoped / P3-P4 overlap or gap |
| Boot `fail_startup` | the 7-phase lifecycle exposes `fail_startup(report) -> NoReturn` (nonzero exit, **before** network I/O); `FAILED_STARTUP` is a state; the report carries my `Collision.claimant_a/b` | strand-1 · lifecycle (K5) | a collision can't become a red deploy with a named culprit |
| §2.7 result grammar | a trigger-set rejection is surfaced as `outcome=BLOCKED` on the **real** `contracts.py:50` constant, built on `LifecycleResult`/`StageResult` — **no `WorkflowResult`/`core/contracts.py`** (fabricated, Q-0120) | strand-1 · result grammar (②) | the rejection maps to a nonexistent type |

---

## 5. Data model + migration/index shape

**K1 owns no DB table.** The registry is a **derived in-memory index** (§3.1) rebuilt from committed
data on every boot — nothing to migrate, no state to reconcile.

| Artifact | Kind | Owner | Shape |
|---|---|---|---|
| `ReservationIndex` | in-memory, frozen post-boot | K1 | `dict[(kind, value, scope)] -> ReservationRecord`; O(1) lookup |
| `sb/namespace/legacy_reservations.json` | committed pure data | K1 | `[{kind, value, scope?, owner, compat:true, source}]` + the `RESERVED_PREFIX_OWNERS` map — the §3.1 frozen compat core |
| `sb/namespace/tombstones.json` | committed pure data (append-only) | K1 | §3.7 — `{tombstones:[…], bans:[…]}` |
| `sb/namespace/slash_pins.json` | committed pure data (Stage-2 seed, empty default) | K1 | `[qualified_name, …]` — names force-kept on slash before the §3.5 demotion sort |
| `snapshot.projections.namespace` | committed pure data | **compiler (01)** | consumed, not owned — the manifest-origin corpus; **node shape §4.2 is K1-required** (both surfaces, `parent_group`) |
| custom-trigger rows (per guild/channel/user) | DB table | **invocation subsystem (T2-12)** | consumed, not owned — K1 only gates set-time via `check_trigger`; the table + its audited mutation are the invocation domain's |

The invocation subsystem's custom-trigger table (name/owner/scope columns) is written through its own
`*_mutation.py` + `emit_audit_action` (mutation rule); K1 never writes it. K1's only "index" is the
in-memory dict keyed by `(kind, value, scope)`.

---

## 6. Restart & merge=deploy behavior

- **Boot reconcile.** K1's `validate` runs as the compiler's **P3** inside `sb/app` **leg-A**
  (pre-network, sibling 01 §3.4). A collision / cap violation / format error → `fail_startup(report)`
  → `FAILED_STARTUP` with the named culprit pair — never the shipped `add_cog` crash-loop. The
  returned `index` is frozen and injected into the resolver (C-1) and the trigger service.
- **merge = deploy (Q-0193).** A manifest name change that would collide is caught **three times
  before it can run**: CI P3, the `git merge-tree` re-validation of the merge result (two
  individually-green PRs that collide together), and boot leg-A. No collision can reach runtime.
- **Dual-instance overlap (LP-4 handoff).** Both instances build an **identical** `ReservationIndex`
  from the same committed `snapshot + legacy_reservations.json + tombstones.json` — `validate` is a
  pure function of committed data. So `is_reserved` / `check_trigger` answer **identically** on both
  instances: no split-brain on trigger validation, no per-instance state to reconcile. (A commit that
  *changes* the corpus is a new deploy; each instance validated its own snapshot at its own boot.)
- **Restart.** The index is rebuilt deterministically from the same committed data → bit-identical.
  Nothing persisted, nothing to recover. (The Stage-2 demotion is deterministic too — equal weights
  + `namespace_id` total order + committed `slash_pins` → the same surface assignment every run.)

---

## 7. Architecture rules honored (INV / layer-boundary cites)

- **Layer boundary — `sb/namespace/` is a stdlib-only leaf (§1.1 line 273).** `validate`,
  `ReservationIndex`, `check_trigger` import neither `sb/spec` nor manifests — they consume the
  snapshot **dict** + JSON files (pure data). `resolve_command` returns a leaf-safe
  `ReservationRecord`, **never** a `TargetRef` (a kernel/interaction type) — the §4 seam correction
  keeps the leaf pure. No `kernel → domain` edge.
- **INV-B (identity contract across surfaces).** The `(kind, surface, parent_group)` scope is the
  mechanism that lets `!karma`/`/karma` coexist *without* a false collision (G-6) while still
  catching the real dup (`/give`×2) — INV-B held by construction, one declared origin per identity.
  The `Collision.scope` field is what makes this true through the whole pipeline (the seam
  reconciliation, §4.2, exists to keep it from being dropped at 01).
- **`invariant_tag` kind reserved → the INV-K overload cannot recur** (design-spec :868-869,
  :1530-1532). K1 owns reserving that kind; the INV-F/G/K/INV-T tags each resolve to one owner.
- **`capability` kind → generalizes `is_reserved_capability`** (`subsystem_registry.py:1249`): the
  3-part `{sub}.{res}.{action}` format (`:1270-1279`) is **P3's** `FormatError` check, and the
  reserved prefixes `_internal/system/governance` (`:8`) port as `legacy` entries **with an owner**
  (`RESERVED_PREFIX_OWNERS`, §3.2 — net-new; the shipped predicate flags a prefix but has no owner
  notion, so a legitimate framework mint was previously indistinguishable from misuse). P3 owns
  capability *format + reserved-prefix owner*; the compiler's P4 owns *lane resolution* — no overlap.
  `actor_type`, `table`, `event`, `setting_key` kinds carry the design-spec §5 compat items.
- **Mutation seam honored by boundary.** K1 performs **no** mutation; the custom-trigger write it
  gates is the invocation subsystem's audited `*_mutation.py` (`emit_audit_action`), not K1's.
- **Q-0120 (a green check contradicting evidence is the check's bug).** The single `validate`
  oracle makes CI-green ⟺ boot-green **by construction** — the exact mechanism that forecloses the
  #763 two-checkers-disagree false-green.

---

## 8. Options → Decision → Why (every fork I closed)

| # | Fork | Options | Decision | Why |
|---|---|---|---|---|
| 1 | Command scope granularity | (a) one flat pool · (b) per-`kind` only (frozen today) · (c) per-`(kind, surface, parent_group)` | **(c)** | (a) false-collides `!karma`/`/karma`; (b) false-collides `/ticket close` vs `/thread close` (subcommand verbs). (c) is the minimal scope that catches the real Q-0211 dup with zero false positives. |
| 2 | Shared-verb computation input | (a) `command-surface.json` · (b) live expanded corpus (`bot.commands` / `projections.namespace`) | **(b)** | (a) is flat-only — verified **1 shared verb vs 11**; the 17 group rows collapse their subcommands (L-14 root). |
| 3 | Corpus assembly order | (a) shared-verb first, nav-nodes later · (b) nav-nodes enumerated first | **(b)** | Q-0231 mints per-node commands outside the 271; verb computation without them is blind and leaves hub names unreserved (L-14 deep-link leg). |
| 4 | Cap-budget enforcement point | (a) Stage-2 assignment only · (b) compile guard only · (c) both | **(c)** | Stage-2 *assigns* (grouping + prefix-demotion → fitting manifests); the compile guard is a hard **count-and-compare** — Discord rejects the 101st top-level command, so a green compile over an over-budget surface would crash at registration. |
| 5 | Prefix-long-tail demotion rule + its Stage-2 sort keys | (a) ad-hoc/owner-per-command · (b) deterministic sort by `(usage_weight asc, namespace_id asc)` | **(b)**, with the keys **defined at Stage-2**: `usage_weight` is a manifest [O] field absent pre-manifest, so Stage-2 pins it to **0** (fallback ordering `namespace_id` alone); `namespace_id = "slash/{parent}/{name}"` is a total string order (§3.1); a committed **`slash_pins.json`** (empty default) is the reviewable override for the ranking-blind equal-weight case | Fully deterministic from the six harvested fields — no manifest/telemetry needed at Stage-2 (the exact lifecycle point it runs). Dormant on the harvested corpus (47 ≤ 100). Mirrors the sim's namespace-id tie-break (§2.10.5). When real `usage_weight` exists later, a re-assignment supersedes the pins with weight-driven ordering. |
| 6 | Tombstone + ban unification | (a) separate mechanisms · (b) one `Origin` enum in one index | **(b)** | One `is_reserved` answers "taken / renamed → X / banned" uniformly; the helpful "renamed to X" error falls out of `renamed_to`; `check_trigger`'s single COMMAND lookup + `origin` branch distinguishes all three reasons (bans stored `kind="command"`, §3.7). |
| 7 | `resolve_command` return type | (a) `TargetRef` (02's stated assumption) · (b) leaf-safe `ReservationRecord` | **(b)** | `sb/namespace/` is a stdlib-only leaf — returning `TargetRef` (kernel/interaction) violates §1.1. K1 returns the record + `spec_id`; the resolver/composition assembles the `TargetRef` (**seam correction**). |
| 8 | `is_reserved` surface arg for triggers | (a) require `surface` · (b) optional; omitted ⇒ check both surfaces | **(b)** | A custom trigger is surface-agnostic at set-time; the conservative "reserved in either surface ⇒ unavailable" answer prevents ambiguity. |
| 9 | `is_reserved` parent-scope semantics (subcommand names vs custom triggers) | (a) `parent=None` checks every parent scope (any-parent wildcard) · (b) `parent=None` checks TOP-LEVEL only; explicit `parent="ticket"` for a subcommand scope | **(b)** | A bare trigger word is only matched against top-level invokable names — a subcommand (`/ticket close`) is not bare-word invokable, so a trigger `close` cannot shadow it and is **available**. Exhaustive cross-scope collision detection is `validate`'s job, not a point query's; (a) would spuriously block common subcommand verbs from ever being triggers. |
| 10 | Capability-validation ownership (P3 vs P4 overlap) | (a) both passes re-check format+reserved-prefix · (b) P3 owns format+reserved-prefix, P4 owns lane resolution | **(b)** | No duplicate reporting, no gap: P3 is a pure namespace check (string identity), P4 needs lane knowledge P3 doesn't have and runs after P3 (so it trusts P3's format verdict). |
| 11 | Reserved-prefix owner rule | (a) keep the shipped owner-less flag (any use of `_internal/system/governance.*` is reserved, no owner) · (b) an owner map allowing the owning framework subsystem to mint its own prefix | **(b)** | The shipped `is_reserved_capability` can't tell a *legitimate* `governance.*` mint by the governance layer from misuse by a domain subsystem. The 3-entry `RESERVED_PREFIX_OWNERS` map (framework-owned prefixes: `_internal→core`, `system→system`, `governance→governance`) makes "head ∉ a NON-OWNING reserved prefix" precise and lets the owner mint. |
| 12 | Context-menu caps (user_5 / message_5) | (a) design + enforce now · (b) reserve dormant, out of scope | **(b)** | The harvested corpus has **zero** context-menu commands (verified: kinds are only prefix/slash/group). The two cap constants are reserved in the `CapViolation.cap` enum so a future context menu extends the guard by adding a partition-count — no structural change — but nothing to enforce today. |

---

## 9. Labeled deferrals (bounded by the 43-subsystem + named-amendment corpus)

| Deferral | Reason | Bound |
|---|---|---|
| The fuzzy **AUTO/SUGGEST/NONE** confidence logic | That is C-5 (conventions §2.2/§6), a separate function; K1 provides only the candidate corpus | K1 owns `command_corpus(surface)`; C-5 owns thresholds. Closed boundary. |
| The custom-trigger **storage schema + additive-union runtime** | Owned by the invocation subsystem (T2-12); K1 gates set-time only | The two trigger kinds (whole-surface prefix; word→command) are named; the union eval is the resolver's. |
| The **per-subsystem naming result** (which verbs are shared; the actual grouped names per subsystem) | That is the Stage-2 subsystem walk's output — this foundational design owns the **algorithm**, not the per-subsystem naming (explicitly out of scope) | 43 subsystems + the nav-node deep-links; algorithm here, result Stage-2. |
| **`usage_weight`-driven** slash retention (vs Stage-2's equal-weight + `slash_pins`) | No usage telemetry exists pre-manifest; the [O] field is authored only after naming | Bounded: the sort key `(usage_weight asc, namespace_id asc)` is fixed; only the *weight values* land later (a re-harvest/re-assignment), and the demotion is dormant on the current corpus regardless. |
| **Context-menu** command caps (user_5 / message_5) | Zero context-menu commands in the harvested corpus (verified) | The cap constants are reserved in the enum; the guard extends by one partition-count if a rebuild subsystem ever declares a context menu. |
| The `g1:<game_key>:` **custom_id scheme-prefix parsing** (§3.4 design-spec) | K1 *reserves* each game's `g1:<game_key>:` prefix in the `custom_id` kind; the scheme-version router is K8 | K1 reserves the prefix; K8 parses/dispatches. |
| Discord-side **per-guild slash-permission override carryover** (L-23) | A cutover census (CUT-2), not a namespace-registry concern | Named, out of scope — the rename→permission map is a cutover artifact. |

---

## 10. Retirement map (V-3 binding — nothing evaporates)

| FJ L-row / owner-queue item | How this spec retires / consumes it |
|---|---|
| **FJ L-14** (shared-verb inputs broken + caps unbudgeted + hub deep-links outside corpus) — **algorithm half** | **RETIRED.** §3.6 computes over the **live expanded corpus** (verified 1 vs 11, never the flat JSON), §3.5 bakes the **cap budget** *with its Stage-2 demotion sort keys fully defined from the six harvested fields* (no undefined key at the point it runs), and §3.6-step-1 enumerates **nav-nodes first**. (01 retired the mechanism half — `projections.namespace` as the corpus source; §4.2 pins the node shape K1 requires it to carry.) |
| **T1-5** (slash-cap policy) | **CONSUMED, not re-decided** (Q-0237e): slash-common + prefix-long-tail; the 100/25/1-nest budget is baked into §3.5 + §3.6; the demotion is deterministic and dormant on the current corpus. Enforcement designed here. |
| **T1-6** (deep-link canonical names) | **CONSUMED** (Q-0237f): `!admin`/`!games` canonical; shipped `-menu` names → hidden **aliases** (`legacy` reservations that still resolve). §3.6 reserves **both**; the alias-vs-tombstone choice per name is Stage-2 data, the mechanism is §3.7. |
| **Q-0224 amendments** (FJ §8: compute from live ledger · bake cap budget · enumerate nav-nodes first) | **RETIRED** by the §3.6 corpus-computation order + §3.5 cap algorithm — all three amendments made buildable, with the demotion keys defined. |
| **Compiler seam (01 §4.2 stated `validate_snapshot`/`is_reserved(kind,value)`/`(kind,value)` key)** | **RECONCILED (§4.2 normative table).** K1's `validate(snapshot)->NamespaceReport`, `is_reserved(value,kind,…)`, `(kind,value,scope)` key win; 01's shape is superseded (its `Collision` must add `scope`). Prevents the `/ticket close` vs `/thread close` / `!karma` vs `/karma` false-collide. |
| Shipped `_RESERVED_CAPABILITY_PREFIXES` / `is_reserved_capability` (`subsystem_registry.py:1244-1250`) — *the only reservation today* | **SUPERSEDED** — generalized into the `capability` kind of the 16-kind registry (§3.1/§7), gaining an **owner map** (`RESERVED_PREFIX_OWNERS`) the shipped owner-less flag lacked. |
| Shipped load-time collision crash (`bot1.py:697-736`; post-load ledger blind) | **RETIRED** — collisions die at CI P3 + merge-tree + boot leg-A, pre-network, with a named culprit pair (§3.2/§6). |
| **FJ L-4 / L-25** (fabricated `WorkflowResult` / `core/contracts.py`) | **CARRIED** as a seam correction (§4.2, §3.4): a trigger rejection is `outcome=BLOCKED` on the real `contracts.py:50` constant, built on `LifecycleResult`/`StageResult`. Re-verified `core/contracts.py` absent. |

Owner-queue tiers touched: **T1-5, T1-6** (both owner-answered Q-0237e/f — **enforcement designed,
decision honored, not re-opened**). No T1 row is re-decided. No owner-gated fork remains open — every
critic finding closed to buildable depth in-file.

---

## 11. Build order (design-spec §9)

- **Lands at K1** (second kernel step, after K0's observability leaf — design-spec §9.1: "namespace
  registry + tombstones + `legacy_reservations.json` + `check_namespace` + the symbol-shadowing AST
  pass"). K1 is a **leaf** — its only kernel dependency is K0.
- **Pre-K2 one-time step:** `tools/compute_corpus.py` (§3.6) runs at **Stage-2**, harvesting the
  expanded corpus from shipped `bot.commands`, computing the shared-verb set + cap-fitting surface
  (deterministic demotion with `usage_weight=0` + `namespace_id` + empty `slash_pins`), and generating
  the initial `legacy_reservations.json` (incl. `RESERVED_PREFIX_OWNERS`) + `slash_pins.json` + the
  per-subsystem naming list Stage-2 consumes. **Blocks:** Stage-2 command naming.
- **Armed as the compiler's P3 at K2:** `validate` defines + tests against a snapshot fixture at K1
  (the fixture uses the §4.2 node shape — both surfaces, `parent_group`); it *runs end-to-end* once the
  K2 compiler emits `projections.namespace` (the "armed later" pattern, sibling 01 §11). The cap guard
  arms with it.
- **What it blocks — the spine everything declares into:** **K2** (every spec reserves its identity
  via P3), **K6** (`capability` kind + `authority_ref` format + the reserved-prefix owner map), **K8**
  (`custom_id` kind + `g1:` prefixes + `resolve_command` + the fuzzy `command_corpus`), and the
  **invocation subsystem** (`check_trigger`). A green K1 is the precondition for a collision-free
  kernel and port order.
