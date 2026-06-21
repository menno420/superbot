# 2026-06-21 — site.json field-level redaction contract

> **Status:** `complete` — tooling/test/docs only (no `disbot/` runtime changed) → self-merge on
> green (Q-0113).

> **Run type:** routine · dispatch

## What I did

Scheduled dispatch, no work order → advanced the plan. Current-state ▶ Next ungated startable named
the last ungated stdlib-guard candidate `public-data-contract-field-snapshot` (idea
`docs/ideas/public-data-contract-field-snapshot-2026-06-19.md`, Q-0089). Built it: extended the
public `site.json` redaction guard from the **family** boundary (`SITE_TOPLEVEL_KEYS`) down to the
**leaf-field** boundary, so a producer change that adds a new field to an already-allowed family
fails closed instead of riding the family whitelist onto the public marketing site. Keys *and*
leaves now both fail closed — the redaction contract is total.

### The gap (from the idea)
The website split's S1 foundation guards `botsite/data/site.json` only at the top-level **key**
boundary (the producer raises on a stray family; `check_site_subset` + the freshness reporter assert
the family whitelist). The commands family also had a per-command field whitelist (S1.1). But every
*other* allowed family (`meta` / `counts` / `catalogue` / `bot_changelog`) had **no** field-level
guard — a producer change adding a new field to `catalogue` (an internal id, a per-guild value, a
future `owner_only_note`) would pass silently because the family is allowed.

### What shipped
- **`scripts/export_dashboard_data.py`** — promoted the public field contracts to named constants
  (`SITE_META_FIELDS`, `SITE_META_BUILD_FIELDS`, `SITE_COUNTS_FIELDS`, `SITE_CATALOGUE_FIELDS` +
  `SITE_CATALOGUE_ENTRY_FIELDS`, `SITE_CHANGELOG_FIELDS`) and added the **`SITE_FIELD_CONTRACT`**
  registry: family-path → allowed leaf fields, where a dotted path (`meta.build`) pins a nested
  dict. The catalogue projection now derives from the single `SITE_CATALOGUE_ENTRY_FIELDS` source
  (retired the duplicate module-private `_SITE_CATALOGUE_FIELDS`, so one source of truth).
- **`scripts/check_dashboard_data.py`** — `check_site_subset` now drives a **generic within-family
  field whitelist** off `SITE_FIELD_CONTRACT` (replacing the bespoke per-command block), with a new
  `_resolve_field_path` helper for dotted nested paths. Fails closed with `site_field_not_whitelisted`
  (error) naming the offending family + fields.
- **Tests** — `test_check_dashboard_data.py`: new fail-closed cases for catalogue, nested
  `meta.build`, and changelog leaks; the existing command case retargeted to the new code.
  `test_export_dashboard_data.py`: a contract-coverage test (every `SITE_TOPLEVEL_KEYS` family +
  `meta.build` is in the registry) and a live-build parity test (the contract is a superset of what
  the producer actually emits — this is the guard that forces a conscious contract bump before a new
  field can ship).

Q-0105 reliability header: stdlib, no new dep, disposable. Runs in CI through the existing
`test_committed_site_json_passes_guard` / `test_live_site_subset_is_clean` pytest guards (the
`check_dashboard_data` CLI is not hard-wired into `code-quality.yml`, but its behaviour is). Delete
`SITE_FIELD_CONTRACT` + its check loop if it nags across sessions without catching a real leak.

## Verification
- `python3.10 scripts/check_quality.py --full` → **green** (11081 passed, 44 skipped; black/isort/
  ruff/mypy/consistency all clean — the only warnings are the pre-existing warn-only `edit_in_place`
  `views/ai/` family).
- `python3.10 scripts/check_architecture.py --mode strict` → exit 0.
- `python3.10 scripts/check_dashboard_data.py --site` → OK ✓.

## Handoff / next
The **ungated stdlib-guard cluster is now fully consumed** (current-state ▶ option (c) struck).
Next ungated startables: (b) the **botsite React-SPA migration**
([plan](../docs/planning/botsite-react-spa-migration-plan-2026-06-20.md)); or (d) a substantial
**`needs-hermes-review`** lane — consistency-linter **AI-nav PR 1** (runtime/Q-0086 live-walk) or
**procedures→skills Batch 2** (edits CLAUDE.md). The headline product lane — the **creature-game v1
PvP battle** — is `needs-hermes-review` + runtime-verified, not an autonomous self-merge. The
*cleanly-ungated self-merge* subset is now genuinely thin: the next dispatch should prefer a
substantial `needs-hermes-review`/runtime lane or promote a fresh idea → plan → build (Q-0172).

## 💡 Session idea (Q-0089)
**Wire the `check_dashboard_data` redaction guard into `code-quality.yml` (or the botsite-tests
workflow) as a hard gate.** Today the field/family whitelist only fails CI *transitively* through
two pytest guards (`test_committed_site_json_passes_guard`, `test_live_site_subset_is_clean`). That's
real coverage, but the dedicated CLI (`check_dashboard_data.py --site`, which prints the precise
`site_*` finding codes) isn't itself a CI step — so a future refactor that drops or renames those two
tests would silently remove the redaction gate with nothing red. A one-line `--site` step in the
workflow makes the redaction contract a *first-class* gate independent of any single test's survival.
(Dedup-checked `docs/ideas/` + roadmap: the existing field-snapshot idea is now SHIPPED; no idea
covers CI-wiring the redaction CLI. Small/decided-lane — a future empty fire could just do it, but
`check_dashboard_data` needs a live DB-free `_build_fresh` path in CI to run standalone, so capture
first.)

## ⟲ Previous-session review (Q-0102)
Prev session (`2026-06-21-bug0020-trim-floor-pointer-prose.md`) was a tight bugs-first CI-reliability
batch — three root-caused fixes (BUG-0020/0021/0022) each with a stays-fixed guard, exactly the
"bugs jump the queue, root over symptom" discipline CLAUDE.md asks for, and it correctly caught the
adjacent ruff-pin drift (Q-0166 fix-on-sight) rather than ignoring it. One genuine miss: it touched
`export_dashboard_data.py` (BUG-0022, the `data.js` clobber) and was *right next to* this very
redaction-contract surface, but didn't note the still-open field-level gap that was sitting one
function away in `check_site_subset` — a small "while I'm in this file, what else is thin here?"
sweep would have surfaced it. **System improvement it surfaces:** the born-red session-card +
`.sessions/` log convention is working well as a hand-off record, but there's no lightweight "files I
touched this run + an adjacent-gap note" field — adding an optional `## 🔍 Adjacent gaps noticed`
section to the session-card template would turn incidental file-proximity (the cheapest possible
discovery signal) into captured backlog instead of letting it evaporate. (Not pushing this as a rule
edit — it's CLAUDE.md/template territory → noted here for owner/Hermes review, not self-applied.)

## 📤 Run report
- **Run type:** routine · dispatch
- **What shipped:** field-level `site.json` redaction contract (`SITE_FIELD_CONTRACT` +
  generic within-family whitelist), closing the within-family field-leak class. Tooling/test/docs
  only, no runtime.
- **⚑ Self-initiated:** none in the unprompted-feature sense — built the explicitly-queued
  current-state ▶ option (c) candidate (the `public-data-contract-field-snapshot` idea, already
  captured/routed). Idea→build, but it was the named next slice, not an invented feature.
- **⚑ Owner-decisions:** none.
- **⚑ Owner-manual-steps:** none.
- **Bug-book:** no new bugs; none fixed (no OPEN tooling bug this run).
- **Doc audit (Q-0104):** idea doc marked `historical`/SHIPPED with an ▶ Outcome; current-state ▶
  option (c) struck through as shipped; ledger guard expected green (PR self-merges into the living
  ledger via the normal merge-commit path).
