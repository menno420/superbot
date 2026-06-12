# 2026-06-12 — UX Lab build (PRs A/B/C, owner-steered same-session execution)

> **Status:** `audit`

**PRs:** #758 (core gallery) · #760 (CV2 + PIL) · #762 (mock studio + compare +
export) — all merged 2026-06-12
**Branch:** `claude/wizardly-planck-c04laf` (continuation of the #755 design session)

## Context

~35 minutes after the design PR (#755) merged, the owner steered: *"you can start
building it, let me know if you need anything from me"* → Q-0116 answered (immediate
build; audience = the recommended admin-gate). The approved plan executed in full,
in one session, as three sequential merged PRs — the plan→execute lifecycle working
exactly as written.

## What shipped

- **#758** — `utils/ux_patterns/` registry + builders · home hub · wings 1–4 (42
  patterns) · probe bench (4 probes) · AST **zero-write fence** · full
  `new_subsystem.py` registration (9/9) · 23 tests.
- **#760** — CV2 wing (8 `LayoutView` exhibits via render-button indirection; the
  `_LabLayout` commented divergence) · PIL wing (reused #665/#702 renderers + 3 new
  candidates incl. the Q-0110 welcome card) · probes 4→10 · 10 tests.
- **#762** — mock studio (8 Q-0108–Q-0112 mocks; declined tiers test-pinned absent) ·
  ⚖️ compare + `uxlab-verdict` lines (the verdict modal dogfoods Label+Select) ·
  **`docs/ux/pattern-library.md`** (registry-generated, freshness doc-pin) · the real
  PersistentView exhibit (deferred from B, done via canonical registration) · 8 tests.

**Verification per PR:** `check_quality --full` green (suite grew 9,139 → 9,180 →
9,188-ish) · `check_architecture --mode strict` 0 errors · live boot on Galaxy Bot
(0 ERROR/CRITICAL) ×3. Owner follow-ups: run a slash sync for `/uxlab`; walk
`!uxlab` on desktop + phone (the CV2 mobile exhibit exists for exactly that).

## Process notes

- **Pinned-surface updates** adding a subsystem requires (found by running the suite,
  fixed in #758): advanced-help top-level set · `EXPECTED_SLASH_SURFACE` ·
  surface-map counts (29→30 subsystems, 36→37 extensions). The `new_subsystem.py`
  scaffold does NOT list these three — see the ⟲ improvement below.
- The **raw-defer invariant** caught two `interaction.response.defer()` uses
  (probes, image wing) → `safe_defer`. The invariant works.
- **Q-0107 reconciliation pass is now overdue** (merged PRs crossed #750 at #751;
  we are at #762). Deliberately not folded into this owner-steered build session —
  it is the next session's job (or the #752 nightly Routine).

## 💡 Session idea (Q-0089)

**`uxlab-verdict` harvester** — a small script (or `/uxlab-verdicts` skill step)
that greps pasted `uxlab-verdict: <id> — adopt|reject|tweak — note` lines from a
session's chat/log, applies them to the registry (`status` flips, `adopted_by`
appends), and regenerates `pattern-library.md`. Why I believe in it: the verdict
loop currently ends at a copy-paste line; the harvester closes it into one motion,
and the freshness doc-pin already guarantees the regeneration step can't be
forgotten. Small, read-only-except-the-registry-file, quick-win lane.
Dedup-checked: nothing in `docs/ideas/` covers verdict routing.

## ⟲ Previous-session review (Q-0102) — the #755 design session (same conversation)

**Did well:** the design survived implementation almost 1:1 — the 9-wing inventory,
the registry schema, the AST-fence idea, and the 3-PR slicing all built as drawn;
verifying library facts by introspection during *design* meant zero API surprises
during *build*.
**Missed / could improve:** the plan under-specified the **host-message shape** per
wing — CV2 exhibits can't live inside a classic-View browser, and the render-button
indirection had to be invented mid-build (it's good, but it was improvisation).
**Concrete workflow improvement:** `scripts/new_subsystem.py` should grow three
checks for the pinned surfaces a new subsystem trips (advanced-help top-level set ·
slash-surface pin · surface-map counts) — this session found them by red suite, the
exact discovery mode the scaffold exists to prevent. Captured here for the grooming
queue rather than built now (the session is at capacity; scaffold edits deserve
their own focused slice).

## Context delta (reflection interview)

- **Route hit:** the "Adding a new subsystem / cog" orientation route +
  `new_subsystem.py` scaffold carried the registration cleanly; context maps fired
  per-file with accurate blast radii.
- **Route miss:** nothing pointed at the three pinned-surface tests (above) — the
  scaffold gap is the actionable form of this miss.
- **Discovered by hand:** `LayoutView` dynamic-construction signatures
  (introspection — right method, cheap); the `Modal`-callback drive idiom for
  decorated buttons was already in the journal (it saved a debugging round).
- **Decisions made alone (all reversible, recorded):** CV2 render-button
  indirection; PersistentView exhibit deferred B→C then built via canonical
  registration; verdicts as copy-paste lines (fence-preserving); audience =
  admin-gated per the standing recommendation.
- **Weak point of what shipped:** exhibit *copy* (the explainer texts) is one
  person's voice and untested against the owner's taste — expect wording tweaks
  after his first walk; also probe P-08's answer (entity selects in modals) is
  genuinely unknown until he presses it live.
- **One change that would have helped:** a "host message shape per wing" row in the
  plan's architecture table (the ⟲ improvement above).
