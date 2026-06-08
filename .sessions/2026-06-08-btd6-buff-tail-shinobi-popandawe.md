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
