# P1-3 — machine-checkable contract invariants · disposition (2026-06-15)

> **Status:** `reference` — the closing record for hardening-roadmap §P1-3
> ([hardening-roadmap-2026-06-12.md](hardening-roadmap-2026-06-12.md)). Not binding;
> source + the invariant tests win. Companion to the four production-readiness maps.

## What P1-3 asked

> "Add AST/registry parity tests, ideally one per track as it lands. This is the durable
> 'stays fixed' layer." — §P1-3

The 2026-06-15 `current-state.md` finding refined this: each of the four named tracks already
carries *an* invariant, so the pass is **"identify a specific uncovered contract and add an
invariant, or close the track as substantially-covered"** — not "land one per track from scratch."

This pass reviewed all four tracks, found **two** genuine uncovered contracts (settings, games),
added a CI-runnable invariant for each, and closed the other two with evidence.

## Track-by-track disposition

### 1. Settings — declared-setting → runtime-consumer parity · **GAP → CLOSED**

**Contract:** every declared `SettingSpec` is read by at least one runtime consumer — no
*editable-no-op* setting (one the operator can toggle in the settings UI while nothing reads the
value).

**Why it was a genuine gap:** the settings map flagged it explicitly twice —
§Required #3 ("no invariant prevents a future editable declaration from becoming a no-op… add a
generated disposition/consumer check") and §Bugs ("Declaration-to-runtime-consumer parity is
manually verified, not invariant-backed"). The existing settings invariants cover the *other*
contracts — backfill-target parity (`test_backfill_target_declaration_parity`), no-dual-pointer
(`test_pointer_lane_ledger`), typed-accessor / no-raw-write discipline — but **none** proved every
declared setting has a reader.

**Closed by:** `tests/unit/invariants/test_settings_declared_vs_consumed_parity.py`. It enumerates
all 63 declared keyed settings from the schema registry and proves each is consumed via one of four
runtime read patterns the codebase actually uses:
1. literal `resolve_value`/`resolve_setting(g, subsystem, name)` (the modern typed path);
2. `resolve_batch(g, subsystem)` or a **dynamic-name** `resolve_*` call (e.g. the AI config
   projection's `resolve_setting(g, "ai", legacy_key)` loop) — conservatively consumes the whole
   subsystem, fail-safe toward "consumed";
3. the setting's `settings_keys` constant / raw key referenced anywhere outside its own
   `settings_key=` declaration — covers legacy `db.get_setting(KEY)` **and** the binding/governance
   lane (a pointer key consumed as `legacy_key=` in `binding_backfill` / `config_arbitration`, e.g.
   `moderation.trusted_role`).

Result today: **0 dead settings** (matches the manual verification). A future editable-no-op now
fails CI; an intentional ahead-of-consumer declaration takes an explicit reviewed waiver
(`_DECLARED_NO_OP_OK`, empty today). Pure AST + registry, no DB.

### 2. Games — terminal-state / wager write-boundary completeness · **GAP → CLOSED**

**Contract:** no two-party game moves money outside `game_wager_workflow` (the audited,
transactional escrow seam) — the pre-P0-1 credit-then-debit *mint window* cannot reappear.

**Why it was a genuine gap:** `test_game_wager_write_boundary.py` fenced a **hardcoded
`_WAGER_FILES` list**. Its `assert path.exists()` only catches the list going stale by *deletion* —
a **newly-added** two-party game that pairs a bare `economy_service.credit` with `.debit` and never
passes `allow_overdraft` would be in neither `_WAGER_FILES` nor the overdraft glob, so the mint
window ships silently. That is precisely the "next regression ships silently" failure P1-3 exists
to stop.

**Closed by:** a third check in `test_game_wager_write_boundary.py` —
`test_two_sided_economy_calls_are_accounted_for`. It scans every `views/` + `cogs/` file for the
**two-sided money signature** (a file calling *both* `economy_service.credit` and `.debit`) and
fails unless the file is an allowlisted single-party path (`_TWO_SIDED_ALLOWED` — the two solo views,
whose win-credit / loss-debit are mutually exclusive branches against the house). A new two-party
game added outside the workflow now surfaces here even without `allow_overdraft`. Today only the two
solo views match; the check passes. Pure AST.

### 3. AI — declared-vs-consumed tools · **SUBSTANTIALLY-COVERED → CLOSED (no new invariant)**

The three-part ratchet jointly closes declared == registered == specs == eval-covered:
- `tests/unit/services/test_ai_tool_catalogue.py::test_catalogue_covers_exactly_the_registered_tools`
  — catalogue == the registry's offered tools;
- `…::test_all_tool_specs_match_the_catalogue` — the introspection spec surface == catalogue;
- `tests/evals/test_eval_coverage.py` — every tool is evaluated or explicitly acknowledged-uncovered,
  with a coverage floor that cannot regress.

As of #896 the floor is **34/34** and `_ACK_UNCOVERED_TOOLS` is empty, so the drift guard fails
closed on any newly-added tool. Adding a tool fails check (1); failing to add a case fails the eval
guard; a stale acknowledgement self-cleans. Nothing to add — closed.

### 4. BTD6 — derived-value provenance · **SOURCE-PROVENANCE COVERED → CLOSED; one design-for-review residual**

The **source registry + migration provenance** contract is invariant-covered:
`test_btd6_source_registry.py`, `test_btd6_source_registry_m3b.py` (migration 042 enables exactly
the captured endpoints), `test_btd6_source_registry_bucket_freshness.py`,
`test_btd6_source_registry_seed.py`. Live fact rows trace to a registered source with freshness.

**Residual (deliberately NOT closed with an invariant):** the BTD6 map (§Data provenance) notes
`DataProvenance` does not yet prove *uniform per-fact* provenance for every static blob field,
composed view, or derived sentence. A guard for that would have to AST-scan every
`btd6_*service` function for a docstring marker or a `DataProvenance` wrapper — a **brittle,
high-false-positive, high-maintenance** check that fails the repo's "verifiable, not a temporary
patch" bar (CLAUDE.md). It is a genuine **design-for-review** item (uniform provenance schema
first), not a P1-3 AST invariant. Recorded here so it is tracked, not silently dropped; it pairs
with the faithfulness-guard work in the AI lane (the claim-assembly class, BUG-0009).

## Outcome

| Track | Verdict | Invariant |
|---|---|---|
| Settings | GAP → **closed** | `test_settings_declared_vs_consumed_parity.py` (new) |
| Games | GAP → **closed** | `test_game_wager_write_boundary.py::test_two_sided_economy_calls_are_accounted_for` (new) |
| AI tools | substantially-covered → **closed** | existing 3-part catalogue/eval ratchet |
| BTD6 provenance | source-provenance covered → **closed** | existing source-registry suite; per-derived-value attribution = design-for-review residual |

**P1-3 is substantially complete** — the two buildable-now gaps are closed with durable
machine-checked invariants; the one remaining provenance item is design-for-review (not a quick
guard) and is tracked above. The next P1 work is the gated remainder: absence-guard **Layer B**
(design-for-review) and the **live-quality eval battery** (prod creds) — both already queued.
