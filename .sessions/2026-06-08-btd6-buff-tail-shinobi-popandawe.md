# 2026-06-08 — BTD6 buff decode tail: 9 → 11 (Shinobi Tactics + Pop-and-Awe)

- **Arc:** picked up the BTD6 buff decode tail (provenance gate lifted by #587, which also
  added `scripts/explore_gamedata.py`). Branch `claude/quirky-tesla-psodD`. Cloned the v55
  dump to `/tmp/btd6gd`; `--validate-anchors` PASS (Dart 200, Super 2500).
- **Key finding — the prior "exhausted" read was on incomplete discovery.** Earlier sessions
  ranked only `*SupportModel`/`*BuffModel`-suffixed types. Scanning **all** top-level
  `behaviors[]` against the committed curated `buffs[]` surfaced two confirmable types:
  - **`SupportShinobiTacticsModel` → `rateMultiplier`** (Ninja Shinobi Tactics 0-3-0+):
    dump `multiplier 0.92` == committed `rateMultiplier 0.92`, `maxStackSize 20` == 20. No
    pierce field on the model, so the committed +8% pierce (different mechanism) stays
    unasserted.
  - **`DamageModifierSupportModel` → `damageAdditiveForBad`** (Mortar Pop-and-Awe 0-4-0+):
    the 2026-06-04 note wrongly said the effect "lives in a different model" — it's in the
    **nested `damageModifierModel.damageAddative`** (the misspelled-additive trap), `1.0` vs
    tag `Bad` == committed `damageAdditiveForBad 1`, consistent across all 5 instances.
- **Implementation** (`scripts/parse_gamedata.py`): added Shinobi to `_BUFF_FIELD_MAP`; added
  `_BUFF_DAMAGE_MODIFIER_TYPES` + `_BUFF_TAG_FIELD` + a nested-tag branch in `_buffs()` that
  reads `damageAddative` (never `damageMultiplier`), maps Bad/Ceramic/Moabs, and **drops the
  entry** when the tag is unmapped (never a bare value-less buff). Both effect fields already
  existed in the renderer's `_BUFF_FIELDS`, so **no renderer change** — `_buff_text` emits
  "x0.92 attack cooldown" / "+1 damage vs BAD".
- **Honest frontier:** 11 is the confirmed ceiling for committed **combat** towers
  pre-cutover. Every remaining unmapped type lands on a hero (separate `map_hero` path, no
  matching committed `buffs[]`), an economy/support tower with no committed tiers
  (Village/Farm — blocked, maintainer call), a paragon `base` node, or is degenerate
  (`GroundZeroBombBuffModel` `damageIncrease 0`). Documented the suffix-filter methodology
  trap so the next session doesn't re-derive the false "exhausted" conclusion.
- **Known uniform gap (not fixed, not per-type):** `_buffs()` emits no `maxStackSize`, so the
  renderer's `_stack_cap` "(stacks up to N)" clause is dropped on the parser-native path.
- **Gates:** `--audit` nothing-SUSPECT; real-dump output verified; 4 new tests
  (`test_buffs_shinobi_tactics_*`, `test_buffs_damage_modifier_support_*`).
  `python3.10 scripts/check_quality.py --full` **green (8070 passed)**.
- **Docs:** updated `docs/btd6/btd6-gamedata-decode-status.md` (header, "Do next" step 1,
  the data-stands summary, the 🟡 buff row, + this session's status-doc log entry).

## Follow-on (same session) — Heli Pilot MOAB Shove rendered (Zone #3)

Maintainer engaged mid-session and gave the open sign-semantics call: **negative push cap =
shoved backward**. Verified the committed per-blimp caps match the dump's
`moab/bfb/zomgPushSpeedScaleCap` **exact** on every tier, then:

- **Renderer** (`btd6_upgrade_detail_service._zone_text` + new `_moab_shove_bits`): renders
  MOAB-Shove per blimp — negative = "shoved backward at xN speed", positive = "slowed to xN
  speed", 0 = "slowed to a halt". Keyed on the singular `multiplierForMoab` (unique to shove;
  never collides with Ice's plural `multiplierForMoabs`). Heli Pilot 0-0-3/0-0-4 now answer
  end-to-end via `get_upgrade_detail`.
- **Parser** (`_zones` + new `_ZONE_RENAME`): emits the renamed caps for the cutover.
  Deliberately does **not** fabricate `multiplierForDdt` — the dump has no DDT field (open
  maintainer call; committed mirrors ZOMG).
- **Corrected the maintainer's assumption:** MOAB is always negative, but **BFB also goes
  negative (−0.11)** at the tier-4/5 top/middle crosspaths — not MOAB-only. ZOMG always positive.
- **Crosspaths ARE stored + reachable** (all 15 states via `stats.tier(code)`); the bare
  crosspath code `014` just isn't an *upgrade-card* id for `get_upgrade`, which is not a gap.
- 4 new tests (3 renderer, 1 parser); `--audit` still nothing-SUSPECT; `check_quality --full`
  green.

## Follow-on #2 — named-crosspath effects are now answerable (gap the maintainer found)

Maintainer asked whether a `0-1-4` heli's stats are askable. Empirically: the crosspath path
(`_render_tower_crosspath`) grounded only *headline* combat stats — it dropped buff/zone
effects, so the crosspath-specific MOAB Shove (0-1-4 → MOAB −0.51) was stored but unanswerable
(only the base-tier −0.4 surfaced, via the upgrade-detail path). Fixed at the seam:
- New public `btd6_upgrade_detail_service.tier_effect_lines(tier)` renders a tier's buff+zone
  strings (reuses `_buff_text`/`_zone_text`, identical phrasing).
- `_render_tower_crosspath` now appends a `[btd6_tower_stats effect]` line per crosspath
  buff/zone. "0-1-4 heli" now grounds "MOAB-class shoved backward at x-0.51 speed…", distinct
  from the 0-0-4 base. +1 context test; full suite green (8075 passed).

## Follow-on #3 — DDT settled + whole-dump coverage map + scheduled-refresh design

Maintainer asked to (a) thoroughly search for the DDT shove value (agents keep wrongly saying
"not in the dump"), (b) map what's in each dump file for future reference, (c) design a system
that re-fetches all data on every update / at intervals.

- **DDT — settled by exhaustive search.** `moab/bfb/zomgPushSpeedScaleCap` are the ONLY three
  push caps in all 9,916 files; no `ddtPushSpeedScaleCap` exists. BUT DDT-speed fields DO exist
  for towers that define them (Silas `ddtSpeedModifier`, Gyrfalcon `moabSpeedScale`) — so the
  "under a different name" instinct was right in general, just not for Heli's zone. Game text
  ("shove MOAB-class Bloons, reversing or slowing") + maintainer's in-game check (DDT slowed,
  not stopped) confirm DDT uses the heaviest-handled (ZOMG) cap, which committed mirrors. Parser
  still never fabricates `multiplierForDdt`. Documented in parser + decode-status.
- **Coverage map (the mapping ask).** Added `btd6_gamedata_inventory.py --full-map [--out]` →
  generates `docs/btd6/btd6-dump-coverage-map.md`: every domain's file count + all model
  `$types` + the primary model's fields + loose-file structure + a **fetch-status column**
  (`✅`/`🟡`/`⬜`) that bridges "what exists" → "what we fetch yet". `_PRIMARY_OVERRIDE` fixes
  the heuristic misfire on Towers (→ `TowerModel`). Regenerable per pull; v-stamp + sha header.
  Provenance: dump is now **v55.1** (was 55.0). 4 new tool tests.
- **Scheduled refresh (the system ask).** Wrote `docs/btd6/btd6-data-refresh-pipeline-plan.md`:
  the manual fetch-everything command chain works today (clone → validate-anchors → overlay →
  audit → --full-map → decode-inventory); the GitHub Actions weekly automation is designed +
  YAML-sketched but flagged as needing maintainer sign-off (executable CI config + 320 MB clone
  cost). Gate: `--overlay` is auto-safe; the `--all` cutover stays human-reviewed. Routed into
  the folio + roadmap.
- Gates: `--audit` nothing-SUSPECT, `check_docs --strict` clean (121 docs), `check_quality
  --full` green (8078 passed).

## Follow-on #4 — Powers + Monkey Knowledge ingested (next-step extraction) + DDT depth

Maintainer picked Powers + Knowledge as the next extraction and Steam-API as the refresh trigger.
Did Powers + Knowledge end-to-end (the bigger, player-facing win):

- **Parser:** `parse_gamedata.py --powers` / `--knowledge` → `powers.json` (25) /
  `monkey_knowledge.json` (134). Names/descriptions via `textTable`; MK category from the
  `Knowledge/<Category>/` folder (authoritative). `_clean_desc` strips HTML tags; `{0}` kept.
- **Runtime:** `btd6_data_service` `PowerEntry`/`MonkeyKnowledgeEntry` (optional fixtures,
  validated, unique-checked) + `get_power`/`get_monkey_knowledge`; `ai_tools`
  `btd6_power_lookup` + `btd6_monkey_knowledge_lookup` (registered + grounding allowlist).
- **Coverage map:** Powers/Knowledge fetch-status → ✅.
- **DDT (deeper search):** confirmed `moab/bfb/zomgPushSpeedScaleCap` are the only 3 push caps
  in 9,916 files; DDT-speed fields exist for Silas/Gyrfalcon (different mechanics), not Heli.
  Maintainer confirmed DDT slowed-not-stopped → matches the ZOMG cap mirror. (In a prior commit.)

**⚠ Process note (recurring trap, avoided):** bare `python3.10 -m black .` reformatted 243
files because **CI excludes `tests/`** (`black --check . --exclude '(...|tests|...)'`). Reverted
all test reformatting (`git checkout HEAD -- tests/`), re-applied only the intended test
additions, kept the CI-checked non-test files black-clean. Lesson reinforced: never `black .`
the whole tree; trust `check_quality.py`'s pinned scope. Final `check_quality --full` green
(8083 passed); diff is feature-only (11 files).

**Answerability audit (maintainer asked the sharp question).** Verified that Powers/Knowledge
are **lookup catalogs, not applied modifiers**: "what does Monkey Boost do" / base Crossbow
Master stats answer ✅, but **"attack speed of Crossbow Master *on* a Monkey Boost"** and
**"starting cash / costs / free monkeys / lives *with* knowledge X"** do **not** ✅ — nothing
applies a Power/MK effect to a tower stat or the economy. Two gaps: (1) Power effect factors
ARE in the dump (`MonkeyBoostModel.rateScale 0.5`/`duration 15`) but unextracted (the `{0}` in
the prose is the hole) + no apply-tool; (2) MK magnitudes are **not** in the dump at all (every
`mod` is a bare `ModModel{name}`; magnitudes are hardcoded game logic). Full verdict + ordered
next steps in the decode-status "Answerability audit" section. **Lesson: "ingested" (catalog
committed) ≠ "answerable" for *combined/applied* questions — keep claiming only the lookup.**

**Still owed (next session):** the Steam-API patch-detect trigger for the refresh pipeline
(maintainer chose it) — design exists in `btd6-data-refresh-pipeline-plan.md`; the Steam
`GetAppList`/`up_to_date` build-id check + the GH Actions workflow remain to build (gated on
sign-off for the executable CI config).
