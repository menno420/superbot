# Session — night-queue slot 5: hero ability roster floor (slot 4 reframed)

> **Status:** `in-progress`

## Origin

Third slice of the same scheduled dispatch fire (after #1008 slot 2 + #1009 slot 3),
continuing the ▶ NIGHT QUEUE
([`planning/night-queue-2026-06-16.md`](../docs/planning/night-queue-2026-06-16.md)).

**Slot 4 (bloon property roster) is NOT cleanly data-complete — pivoted to slot 5.**
See the finding below; the third slice is **slot 5 — hero ability roster** (§7.6),
which IS data-clean (all 17 heroes carry `abilities[{level,name,summary}]`, 0
missing).

## Slot-4 finding (recorded for the next fire — this is the bug-first move)

The night queue assumed `bloons.json` → `properties[]` answers "which bloons are
camo / fortified / regrow". It does **not**, cleanly: in BTD6 **camo / fortified /
regrow are universal *modifiers*** applied to *any* bloon, not intrinsic per-type
properties. In the data they appear only on the three `category:"modifier"` marker
pseudo-entries (`Camo property` / `Fortified property` / `Regrow property`) plus a
couple of innate cases (DDT is innately camo+black+lead; Lead Bloon is lead). A
roster "which bloons are camo" served from `properties[]` would return just
`[DDT, Camo-property-marker]` — itself a **BUG-0009-class wrong assembly** (it
implies only DDT can be camo, when every bloon can). The existing
`deterministic_bloon_roster_reply` already excludes `category:"modifier"` for this
reason. **Reframe needed before building slot 4** (recorded in the night-queue doc).

## What I'm about to do (slot 5)

Add the **hero ability** roster — the per-hero sibling of the capability / bloon /
relic rosters. "what abilities does Quincy have?", "list Adora's abilities" lists a
hero's abilities (level + name + summary) so the model can never mis-level /
mislabel one (BUG-0009). The "which heroes have an ability at level N" cross-query
was **dropped** — the data only carries levels 3 and 10 uniformly across all 17
heroes, so the cross-query is degenerate (all-or-nothing); the per-hero list is the
useful, clean shape.

- `btd6_data_service.hero_abilities(name)` — resolve one hero via the shared
  surface resolver, return abilities ascending by level, `None` on miss.
- `btd6_context_service.deterministic_hero_ability_roster_reply` — fires on an
  ability cue + exactly one resolved hero; defers on a cost cue (the hero *cost*
  builder's job), strategy, zero or two-or-more heroes. Registered in
  `_BTD6_LIST_BUILDERS` after the relic roster.
- Tests: `tests/unit/services/test_btd6_hero_ability_roster.py` + an exclusivity
  corpus should-fire phrase.

Ships under **Q-0048** (read-only deterministic floor, no prod-check, auto-deploys).
