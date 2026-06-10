# BTD6 data-mapping continuation — ABR ingest + decode tail (2026-06-09, evening)

> Direct maintainer request in-session ("continue with the btd6 data mapping…
> you can use multiple agents to map the rest of the dump"), same session as
> Lane 5 (#633, merged). PR: **#638** (draft at first push per Q-0052).

## Summary

Executed the decode-status backlog with a **4-scout fan-out → serial implementation**
pattern: four read-only subagents built evidence packs (Rounds/IncomeSets · subtower
tail · SCHEMA_FIRST/DEFER buff-zone confirmations · loose files + verdict staleness),
every load-bearing claim was spot-checked against source, then two implementation
slices landed:

**Slice 1 — ABR + income sets** (`abr_rounds.json`, `income_sets.json`,
`--abr-rounds`/`--income-sets`, roundset-aware `get_round`/`round_composition`/
`round_cash` + the two AI tools, introspection domain). DefaultRoundSet was
parity-checked first: committed rounds.json matches the dump 140/140 — provenance
now dump-verified. Defaults byte-identical (the $19,840 Q-0043 anchor pinned).

**Slice 2 — decode tail**: subtower spawn mechanisms **7/7** (premise corrections:
no named-ref morph exists — Alchemist is `secondaryTowerModel`; nested zones were
already emitting), subtower lifespan falls back to embedded `TowerExpireModel`
(Marine 30 s / Lava Phoenix 20 s — was 0), subtower-scoped `AttackAirUnitModel`
(Mini-Comanche missile), zone `inclusive` flag (Obyn's same-tag pair would read
inverted without it), buffs 11→15 (`RangeSupport` pinned by 4 independent committed
confirmations · `ProjectileRadius` Striker identity · `BananaCashIncrease` Benjamin
prose, committed via deterministic hero re-export · `ProjectileSpeed` owner-confirmed
+25%, Q-0069), renderer `_BUFF_FIELDS` +5 rows (Striker's committed ×1.1 rendered as
a bare "buff" before), decode-class registry + SHA-pinned report regenerated at v55.1.

**Owner decisions captured (router §29):** Q-0066 cutover = dedicated session ·
Q-0067 Farm/Village minimal tiers at cutover · Q-0068 per-tier beast names ·
Q-0069 projectile-speed = +25% (implemented same session).

**Also:** paragonDegreeData cross-checked (display table game-exact 100/100; the
API-replica fallback's 48-boundary floor-vs-round edge documented); loose files
triaged (frontier/rogue/resources = skip on scope); 7 stale `_DOMAIN_META` verdict
rows fixed; dictionary/coverage-map labels corrected ("Boss/Legends scaling" was
wrong — frontierData is Frontier-event meta).

## Verification

- Real-dump confirmation harness: every new mechanism's emitted numbers matched the
  committed arbiter exactly (Alchemist 72/0.03/10/2 · beasts · Comanche 0.228 + 3/4 ·
  Marine 30 · PermaPhoenix 5/8 · LordPhoenix 20 · TranceTotem · Obyn inclusive pair).
- ABR recompute discipline: stored cash re-derived from composition × pop table ×
  the committed income bands for all 140 rounds; cumulative null r1-2 then runs
  from $650 at r3.
- `--audit` stays **0 SUSPECT**; `--overlay` stays a 0-change no-op; full CI mirror
  **8475 passed / 22 skipped**; arch strict 0 errors; clean test-bot boot.
- CI tripped once on slice 1: **black** — the journal's known trap (the PostToolUse
  format hook doesn't fire in the remote container) plus my own shortcut (pushed on
  targeted tests only). Fixed in 630179a; full mirror before every push after.

## Files changed (beyond Lane 5's)

Mapper + generators (`parse_gamedata.py`, both inventory scripts), service
(`btd6_data_service.py`, `ai_tools.py`, `ai_introspection_service.py`,
`btd6_upgrade_detail_service.py`), data (`abr_rounds.json`, `income_sets.json`,
`benjamin.json` re-export, regenerated coverage map + decode report), tests
(new `test_btd6_abr_rounds.py` + extensions in 5 files), docs (decode-status,
dictionary, router §29, roadmap BTD6 section + Later fragment, pipeline plan
untouched this time). `current-state.md` deliberately untouched (merged-PRs-only
convention; the scoreboard isn't this work's home — decode-status is).

## Parallel-agent notes

- 4 read-only scouts (~600K subagent tokens) kept the main context lean; ALL
  scout outputs spot-checked before acting (journal rule) — every checked claim
  held, and two scout *premise corrections* (named-ref morph doesn't exist;
  nested zones already emit) materially changed the plan.
- One self-inflicted red: my appended test helper `_tower_model` shadowed an
  existing same-name helper in `test_parse_gamedata.py` (26 failures) — renamed.
  Greppable lesson: check for name collisions before appending helpers to a
  3,000-line test file.

## Context delta

- **Needed but not pointed to:** the test-helper namespace of
  `test_parse_gamedata.py` (collision above); `_REQUIRED_ROUND_FIELDS` demanding
  wiki-prose fields (summary/danger/common_threats) — any new round-set ingest
  must derive mechanical equivalents; `parse_round_bloon_key` already handling the
  dump's PascalCase ids (huge reuse win nothing documented — now noted in
  decode-status via the ABR cash_source).
- **Pointed to but didn't need:** the decode-status session-log middle (lines
  ~243-980) — the ⭐ top section + completion tables + inventory report carried
  everything; CodeGraph (context_map/grep/scouts sufficed for a scripts-heavy
  session).
- **Discovered by hand:** (1) benjamin.json is a mod-helper *export* — committing
  hero buff decodes = re-running `map_hero`, not hand-editing (and the diff being
  exactly 16 buff blocks + version stamp proves export determinism); (2) the dump
  round files' `emissions[]` is redundant (groups suffice — verified 280/280) and
  `start`/`end` are 1/60-s frames; (3) webhook CI-failure events can be delivered
  twice for the same job — check the job ID before re-investigating; (4) the
  committed decode-inventory report had drifted from its own generator twice over
  (badge + stale verdicts) — generated docs need their generator re-run in CI or
  a pinning test (the badge prefix test now covers half of this).
