# SuperBot — Helper Discipline & Placement Policy

> **Status:** binding. The rules below govern when a helper may exist,
> where it must live, when it may be promoted, and what review must
> precede every new helper. Companion to `docs/architecture.md`
> (layering), `docs/ownership.md` (which service owns which write),
> and `docs/repo-navigation-map.md` (where things live today).
>
> **Why this exists:** the codebase already shows three signs of
> helper sprawl: `utils/helpers.py` is a grab-bag of unrelated
> functions, `utils/embeds.py` ships embed builders that two cogs use
> while every other cog builds embeds inline, and at least one
> back-button factory was duplicated across five view modules before
> `views/navigation.py` consolidated it. The rules here exist to stop
> the next instance, not to relitigate the existing ones.

---

## 1. When you may create a helper

Create a helper **only** when at least one of the following is true.
If none apply, inline the logic.

- **Reuse.** Two or more existing call sites would have identical (or
  near-identical) logic. Two is the trigger; one is not.
- **Single-responsibility clarity.** The helper has one obvious name,
  one obvious return shape, and removes a meaningful chunk of
  branching from the caller.
- **Stable domain operation.** The helper encapsulates a primitive
  the domain already names (e.g. "value the hand", "resolve the
  cleanup channel", "format a duration"). The name comes from the
  domain, not from "the code that happens to be here".
- **Audited mutation seam.** The helper is the place INV-E / INV-F /
  INV-G is enforced (governance, economy, XP). These are services,
  not utilities; see § 3.
- **Cross-cog coordination.** The helper is the seam through which
  two cogs talk without importing each other (the EventBus or a
  service — never a third cog).

The bar for **moving** an existing helper is higher: even if reuse
exists, do not move a helper unless the new location is one of the
allowed ones in § 3 *and* the caller's understanding improves.

---

## 2. When you must **not** create a helper

If any of the following is true, do not create the helper. Inline the
logic or reuse what exists.

- **One-line wrapper.** `def x(a): return f(a)` adds a name without
  adding meaning.
- **Hides control flow.** If the caller now reads `await
  do_the_thing(ctx)` and there is no way to tell what `do_the_thing`
  decides, defers, or sends, the helper is opaque.
- **Mixes responsibilities.** Helpers that "log and also send and
  also delete" have at least three callers' worth of edge cases
  inside them. Split them or leave them inline.
- **Makes a function look shorter.** Length is not a quality metric.
  A 60-line function with one responsibility is fine.
- **Duplicates an existing helper / service.** Search before adding.
  The duplication rate in `utils/helpers.py`, `utils/embeds.py`, and
  the back-button factories is high enough that "I will check later"
  reliably becomes "I will not check".
- **Bypasses a registry, pipeline, or owner.** If a helper writes
  directly to a governed table, the helper is illegal regardless of
  how convenient it is. Re-read `docs/ownership.md` § "Direct DB
  writes — explicit blocklist".
- **Captures cog-specific behaviour in a shared utility.** A
  formatter that only the blackjack cog will ever call does not
  belong in `utils/`. Put it in `cogs/blackjack/_helpers.py` or
  `services/blackjack_engine.py`.
- **Creates a parallel abstraction.** If `views/navigation.py`
  exists, the next back-button helper goes there or stays inline.
  Do not create `views/navigation_v2.py` or
  `views/<subsystem>/back_buttons.py`.
- **Permanentizes a temporary path.** Migration shims (e.g. a wrapper
  that flips between legacy `guild_settings` and new `bindings`)
  belong in `core/runtime/config_arbitration.py` and have a finite
  life. Do not stamp them into `utils/`.

---

## 3. Where helpers belong

Pick the **most local** category that fits. Promotion happens in one
direction (local → shared); demotion does not happen, so an
overpromoted helper sticks around forever.

### 3.1 Inline (no helper)

Default. Logic stays in the function that needs it until § 1's
triggers fire.

- **Where:** the calling function.
- **Allowed dependencies:** anything the caller already imports.
- **Promotion path:** § 3.2 once one of § 1's triggers fires.

### 3.2 Subsystem-private function

A private (`_underscored`) function in the same module as the caller,
or a sibling module under the cog's package
(`cogs/<name>/<topic>.py`).

- **Where:** the cog's own file, or `cogs/<name>/<topic>.py` for
  pure-domain logic (no Discord).
- **Allowed dependencies:** the same surface the cog file already
  uses. Pure-domain modules (`cogs/<name>/parsing.py`,
  `cogs/<name>/state_machine.py`) **must not** import `discord`,
  `views/*`, or other cogs.
- **Forbidden dependencies:** other cogs (use EventBus or a service).
- **Promotion path:** § 3.3 once a second function in the same cog
  starts reusing it.

### 3.3 Cog-local helper module

`cogs/<name>/_helpers.py` (leading underscore signals "private to
this subsystem"). Existing examples: `admin`, `blackjack`,
`counting`, `diagnostic`, `economy`, `moderation`, `rps_tournament`,
`setup`, `xp`.

- **Where:** `disbot/cogs/<subsystem>/_helpers.py`.
- **Allowed dependencies:** `utils/`, `services/`, `core/runtime/`,
  `utils/db/` (read-side), `discord`. May import from other files in
  the same subsystem package.
- **Forbidden dependencies:** other cogs; other subsystems'
  `_helpers.py`; `views/<other>/`.
- **Promotion path:** § 3.4 once a second cog or `views/` package
  needs the same helper.

### 3.4 View-private helper

`views/<subsystem>/_helpers.py` for UI-only shared logic within one
subsystem's view package (currently used by `channels`, `roles`,
`rps`).

- **Where:** `disbot/views/<subsystem>/_helpers.py`.
- **Allowed dependencies:** `discord`, `views/base.py`,
  `views/navigation.py`, `services/`, `utils/`.
- **Forbidden dependencies:** other cogs; `utils/db/` (writes go
  through services).
- **Promotion path:** § 3.5 if a second subsystem's views need the
  same logic.

### 3.5 Shared view primitive

`views/base.py` (`BaseView`, `HubView`, `send_panel`,
`handle_view_error`), `views/navigation.py` (back buttons,
`BackTarget`), or `views/selectors/` (shared modal selectors).

- **Where:** the existing files above. **Do not create a new
  top-level view-helpers module** without an ADR — the codebase has
  one canonical navigation module and adding a second is the kind of
  duplication this policy exists to prevent.
- **Allowed dependencies:** `discord`, `core/runtime/` for safe
  interaction helpers.
- **Forbidden dependencies:** `cogs/`, `services/` (callers pass
  builders in as callables instead — see `views/navigation.py`).
- **Promotion path:** none beyond this. If something graduates past
  here, it has become a service.

### 3.6 Service helper

`services/<name>_service.py` (audited mutation) or
`services/<name>_engine.py` / `services/<name>_catalogue.py` (pure
domain). The service layer is the **only** legitimate writer of
shared state — INV-E / INV-F / INV-G are AST-enforced.

- **Where:** `disbot/services/`.
- **Allowed dependencies:** `utils/db/*`, `core/events`, other
  `services/`, `core/runtime/` (read primitives).
- **Forbidden dependencies:** `cogs/`, `views/`, `discord` (services
  are headless — they do not render UI). Audited mutation services
  may accept Discord IDs but must not call Discord API methods.
- **Promotion path:** none. A service is the terminal node.

### 3.7 Runtime / lifecycle primitive

`core/runtime/*` — sessions, panels, anchors, interaction router,
EventBus consumers, tasks supervisor, navigation_stack,
persistent_views registry, scope_locks, guild_config cache, identity
contract validator, scheduler. These are **platform primitives** —
they outlive every feature.

- **Where:** add a new file under `disbot/core/runtime/` only if no
  existing primitive owns the concern. Promoting a helper here is
  almost always wrong unless the helper has become a primitive that
  every subsystem depends on.
- **Allowed dependencies:** `utils/db/*`, `core/events`,
  `services/metrics` only (everything else in services is too
  feature-aware to belong here).
- **Forbidden dependencies:** `cogs/`, `services/*` other than
  `metrics`, `views/`, `governance/` (governance uses runtime, not
  the reverse).
- **Promotion path:** none. This is the bottom.

### 3.8 DB helper

`utils/db/<feature>.py` — per-table CRUD. Every asyncpg call in the
codebase happens here. The package re-exports symbols so the
historical `from utils import db; db.func(...)` and
`from utils.db import func` patterns both keep working.

- **Where:** `disbot/utils/db/<feature>.py`. New tables get a new
  file plus an entry in `utils/db/__init__.py`.
- **Allowed dependencies:** `utils/db.pool`, `utils/db.codec`,
  standard library.
- **Forbidden dependencies:** anything outside `utils/` (see
  `docs/ownership.md` § "Dependency direction").
- **Promotion path:** none. DB helpers are leaves.

### 3.9 Leaf utility

`utils/<topic>.py` — pure helpers with no I/O (except `utils/db/`,
which is the DB layer).

- **Where:** the existing files: `cooldowns.py`, `channels.py`,
  `visibility_rules.py`, `synonyms.py`, `tournaments.py`,
  `ui_constants.py`, `hub_registry.py`, `subsystem_registry.py`.
- **Allowed dependencies:** standard library, `discord` (no I/O —
  type and constant use only), other `utils/` modules.
- **Forbidden dependencies:** `cogs/`, `services/`,
  `core/runtime/`, `views/`.
- **Promotion path:** none.

#### Special cases inside `utils/`

- **`utils/helpers.py`** is a legacy grab-bag (currently five
  unrelated public surfaces). **Do not add to it.** New leaf
  helpers go in a dedicated topic file (`utils/<topic>.py`); new
  cog-aware helpers go to § 3.3 instead.
- **`utils/embeds.py`** has two consumers (`utility_cog`, `xp_cog`)
  while every other cog builds embeds inline. **Do not invest in
  it** — neither by extending nor by routing other cogs through it.
  If embed-builder consolidation is ever the goal, it needs its own
  PR with a clear migration plan, not opportunistic additions here.

### 3.10 Test helper

`tests/unit/<area>/conftest.py` (pytest fixtures) or
`tests/unit/<area>/_helpers.py` for shared test scaffolding inside
one area.

- **Where:** test-tree only.
- **Allowed dependencies:** anything the tests in that area use.
- **Forbidden dependencies:** none from production source code into
  test helpers.
- **Promotion path:** none — test helpers stay in tests.

---

## 4. Promotion ladder

Helpers move **one rung at a time**, only when evidence demands it.
Skipping rungs ("this looks like it could be useful elsewhere") is
how `utils/helpers.py` ended up the way it is.

| Rung | Trigger to move up |
|---|---|
| 1. Inline | A second function in the **same file** wants the same logic. |
| 2. Private function in the same file | A second file in the **same subsystem package** wants it. |
| 3. `cogs/<name>/<topic>.py` (pure) **or** `cogs/<name>/_helpers.py` | A second subsystem **or** the corresponding `views/<name>/` package wants it. |
| 4. `views/<subsystem>/_helpers.py` | A second `views/*` package wants the same UI primitive. |
| 5. `views/base.py` / `views/navigation.py` / `views/selectors/` | The helper is a UI primitive that every subsystem could use. **Or** it is going the other way and becomes a service. |
| 6. `services/<name>_*` | The helper carries state-mutation, audit, or cross-subsystem coordination. |
| 7. `core/runtime/*` | The helper is a platform primitive that every subsystem depends on. (Promotion to here is rare and needs an ADR.) |

**Evidence rule:** "needs" means an existing PR makes the second
caller. Speculative promotion ("I think someone might use this
later") is forbidden — it is how parallel abstractions appear.

**Demotion:** if you find an overpromoted helper (e.g. a
subsystem-specific function in `utils/`), do not relocate it during
an unrelated PR. File it in the "Follow-up recommendations" section
of a docs PR (or open an issue) so the move happens with intent.

---

## 5. Helper review checklist

Run this before merging any PR that adds or moves a helper. CI does
not check most of it; the safety net is review.

- [ ] **Existing surface?** Did you grep for an existing helper /
  service with the same name or shape? (`grep -rn "def
  <name_or_synonym>" disbot/ --include="*.py"`)
- [ ] **Name is domain-specific.** "format_money", not "format_str".
  "resolve_cleanup_channel", not "get_channel".
- [ ] **One responsibility.** A reviewer can describe the helper's
  purpose in one sentence without using "and".
- [ ] **Correct rung.** It is in the most local rung from § 3 that
  still satisfies its callers. (If it is in `utils/`, can two
  unrelated subsystems honestly use it?)
- [ ] **Dependencies flow downward.** Imports stay within the
  allowed-deps list for its rung (§ 3). No new cycles. No new lazy
  function-body imports added to "make the rule work".
- [ ] **Caller reads better.** Open the longest call site and check
  that the helper makes the caller easier to read, not just shorter.
- [ ] **Testable in isolation.** Pure-domain helpers have a unit
  test in `tests/unit/<area>/`. UI helpers have a smoke or a
  pinning test where one exists.
- [ ] **Does not bypass ownership.** Never writes a governed table
  outside its service. Never emits an uncatalogued event.
- [ ] **Not a temporary path made permanent.** Migration shims live
  in `core/runtime/config_arbitration.py` (or equivalent) and have
  a documented removal trigger.
- [ ] **No second navigation/router/registry created.** The
  canonical ones are: `views/navigation.py` (back buttons),
  `cogs/help/route.py` (Help resolver), `core/runtime/interaction_router.py`
  (interaction dispatch), `utils/subsystem_registry.py`
  (subsystem metadata), `utils/hub_registry.py` (hub presentation),
  `core/runtime/persistent_views.py` (panel registry). If the
  helper resembles any of these, it goes **in** them, not next to
  them.
- [ ] **No new `_v2` / `_new` / `_helpers2.py`.** Suffixed names
  signal a parallel abstraction. Update the canonical surface
  instead.

---

## 6. Quick reference — common mistakes to avoid

| Anti-pattern | Why it is wrong | Do this instead |
|---|---|---|
| Adding a one-line helper to `utils/helpers.py` | Grows the grab-bag. | Inline it, or put it in a topic-named file (`utils/<topic>.py`) or the cog's `_helpers.py`. |
| New back-button factory in a cog | Duplicates `views/navigation.py:attach_back_button`. | Call the canonical helper; pass a `parent_builder` callable. |
| New `*_router.py` or `*_dispatch.py` in a cog | Bypasses `core/runtime/interaction_router.py`. | Register the prefix with the canonical router. |
| New "settings cache" in a cog | Bypasses `core/runtime/guild_config`. | Use the canonical guild_config cache; emit invalidation on write. |
| New `add_coins` / `set_coins` wrapper anywhere | Violates INV-F (AST-checked). | Call `services/economy_service` directly. |
| New embed-builder file under `utils/` | Adds to the underused `utils/embeds.py` problem. | Build `discord.Embed` inline at the call site, or extend a single existing builder if the case already lives there. |
| New "we'll need it for X later" helper | Speculative promotion. Never the right call. | Wait until X exists; then promote with evidence. |
| Helper that imports a cog from a service | Reverses the dependency graph (§ "Dependency direction" in `docs/ownership.md`). | Emit a catalogued event; let the cog subscribe. |
| Helper that does Discord I/O inside a `scope_locks.lock_for` block | Violates the V/M/A pattern. | Compute under the lock; apply outside it. |

---

## 7. When in doubt

1. Re-read **`docs/ownership.md`** — most "where does this go?"
   questions are answered by "which owner already owns this concern?"
2. Re-read **`docs/architecture.md`** § "Subsystem decomposition" —
   most helpers belong inside a subsystem package, not in `utils/`.
3. If two owners both seem to qualify, the rule from
   `docs/ownership.md` § "What to do when the boundary is unclear"
   applies: extract a third (service) that mediates rather than
   coupling the two.
4. If the helper is genuinely new platform territory (does not fit
   any existing rung), it is an architectural change. Write an ADR
   under `docs/decisions/` before the implementation PR.

---

## 8. Updating this file

This policy is binding. Change it by PR with reviewer signoff. When
you change it:

- If you tighten a rule, update existing references in `docs/architecture.md`
  and `docs/repo-navigation-map.md` to match.
- If you relax a rule, explain the relaxation in the commit body.
- Do not extend this file into a "best practices" essay — every rule
  must map to an actual pattern observed in this codebase.
