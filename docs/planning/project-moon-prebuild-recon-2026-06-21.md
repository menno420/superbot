# Project Moon knowledge domain — pre-build reconnaissance (2026-06-21)

> **Status:** `reference` — companion to
> [`project-moon-knowledge-domain-plan-2026-06-21.md`](project-moon-knowledge-domain-plan-2026-06-21.md).
> Pre-execution intelligence gathered to make the first build slice turn-key. Items marked **✓
> verified** were confirmed against live sources on 2026-06-21; the **domain-model** section is a
> first cut from general knowledge — **verify counts at ingest** (Limbus updates every ~2–3 weeks).
> Source code + the plan win over this file. **Subsystem:** btd6, ai.

## 1. Data-source reconnaissance (the plan's #1 dependency)

### 1a. The Limbus wiki does **not** expose Cargo — a correction to the plan

**✓ Verified** (MediaWiki `siteinfo` API, 2026-06-21): `limbuscompany.wiki.gg` runs Scribunto (Lua),
**DynamicPageList3**, ParserFunctions, Arrays, Maps — but **no Cargo and no Semantic MediaWiki**.

**Consequence:** the plan's §5 sketch ("`fetch_pm_limbus.py` modelled on `fetch_bloonswiki.py`,
MediaWiki/Cargo") is **partly wrong** — `fetch_bloonswiki.py`'s `action=cargoquery` calls have no
equivalent here. What **does** transfer from that script: `action=raw` on `Module:` Lua pages (it
already uses this for rounds/stats), the standard MediaWiki API (`list=allpages` /
`list=categorymembers` / `action=parse`), and DPL3 for enumeration.

### 1b. The real structured-stat source: the game's own **StaticData** dump (the BTD6-dump analogue)

**✓** Limbus ships its data as **StaticData**, which the community dumps to JSON — *cleaner than the
wiki for exact numbers* (identity stats, skills, passives, abnormalities, encounters). This is the
true equivalent of BTD6's `Btd6ModHelper/btd6-game-data` dump. Routes found:

- **Lethe modding framework** — `BepInEx/plugins/Lethe/` dumps all static data + locale to a
  `dumpedData/` folder as JSON (the canonical, self-from-the-game source).
- **Server reimplementations** carry synced static data, updated each patch — `LEAGUE-OF-NINE/FurinaLC`,
  `steviegt6/limbus-server` (submodules re-synced on game update).
- **`meatpnppet/limbus_data_analysis`** — scripts that build a dataset of sinner IDs / skills / passives.
- **`bw1nd/limbus_helper`** (MIT) — party-builder carrying Identity/E.G.O data (Kotlin app).

**Caveat (licensing / IP):** `dumpedData` is raw game data; the modding norm is *do not republish raw
game files*. Derive **facts with provenance + attribution** (the BTD6 norm already in
`data/btd6/README.md`), don't commit verbatim game dumps. Project Moon's IP stance is stricter than
Ninja Kiwi's — keep to summarized/derived facts.

### 1c. Lore / prose source: the wiki (no-Cargo API) + story-log datamines

- `limbuscompany.wiki.gg` via the standard API — enumerate with DPL3 / `categorymembers`, pull wikitext
  via `action=raw` or rendered via `action=parse`. **CC-BY-SA** → store summarized facts + attribution.
- `retcons.github.io` **story/identity logs** (datamined story text); `projectmoon.fandom.com` and the
  Miraheze **Cogitopedia** for cross-game lore (LobCorp / LoR connective tissue).

### 1d. Recommended ingestion per data type

| Data | Best source | Method | BTD6 analogue |
|---|---|---|---|
| Identity / E.G.O / enemy **stats** (exact numbers) | game **StaticData** dump | parse JSON → committed `disbot/data/projmoon/…` | the game-dump path (`parse_gamedata.py`) |
| **Lore / story / character / abnormality** prose | wiki.gg + story-logs | standard API (no Cargo) → summarized facts | the wiki-scraper path (`fetch_bloonswiki.py`) |
| Live / event | minimal for Limbus | — (revisit per game) | `btd6_facts` live lane |

**Net:** Project Moon has the **same two-source shape** as BTD6 (clean game dump for numbers + wiki
for prose) — so the architecture fits *better* than first assumed; only the *wiki access mechanism*
differs (no Cargo). **Slice A should start from the StaticData identity JSON** (clean, bounded) plus a
thin lore pull — **not** a Cargo scrape.

## 2. The `KnowledgeDomain` seam contract (from the BTD6 code audit)

What the generalised seam must expose, and — crucially — **what to reuse vs. keep per-domain vs. never
generalise**. Full audit with signatures is in the session record; the load-bearing conclusions:

**Reuse as-is (the plumbing is already domain-agnostic):**
- **Fact store** (`btd6_fact_store.py`) — schema is `(fact_type, entity_kind, entity_key, body_json,
  confidence, version, provenance)` with **no btd6 columns**. Namespace it per domain; no migration of shape.
- **Provider abstraction** (`btd6_data_provider.py`) — `FileRawProvider` / `CloudRawProvider` /
  `PostgresRawProvider` behind a `load(name)` Protocol; a new domain just adds a data dir + backend select.
- **Grounding line shape** — `[entity_kind] headline — details (source: …, fetched …)`, `_cap` (240 chars)
  + `_sanitise`. Reuse the renderer skeleton; per-entity formatters stay per-domain.
- **Resolver matching logic** — word-boundary alias matching + plural tolerance is reusable; the *vocabulary*
  is per-domain.

**Each domain provides (its own copy):**
- Entity dataclasses + committed data files (`disbot/data/<domain>/`).
- Resolver vocabulary (`_VOCABULARY` table) + the `has_<domain>_context()` keyword detector.
- Fixture grounding renderers.
- A new `AITask` enum member (`PROJMOON_ANSWER`) + the 3 wiring points in `natural_language_stage.py`.

**Do NOT generalise (BTD6-only — leave inside a `BTD6Domain`, do not force onto PM):** the 3-path × 5-tier
**upgrade-path** model, **crosspath tier codes** (`0-2-5`), **paragon degree** scaling (1–100 curves),
the **difficulty/mode/modifier** taxonomy, and BTD6's flat **alias-collision** check (PR-relevant: PM has
100+ Identities with nicknames that repeat across Sinners → resolution must be **Sinner-namespaced**, not flat).

**The 6-pillar interface** a `KnowledgeDomain` exposes: ① typed data accessors · ② fact namespace
(`entity_kinds` / `fact_types`) · ③ resolver vocabulary + `has_domain_context()` · ④ grounding renderers
· ⑤ `ai_task` member · ⑥ data location / provider select.

**Key integration points (file:line, verified by audit):** `services/btd6_data_service.py:1222–1559`
(accessors); `services/btd6_fact_store.py:136–241` (store/fetch); `services/btd6_resolver_service.py`
(`resolve` → `ResolvedIntent`); `services/btd6_resolver_vocabulary.py:55–165` (`_VOCABULARY`);
`services/btd6_context_service.py` (`BTD6Context` + `_render_*`/`_cap`/`_sanitise`);
`core/runtime/ai/contracts.py:30` (`AITask.BTD6_ANSWER`);
`core/runtime/ai/natural_language_stage.py:467,623,674` (task routing/floor/faithfulness-guard);
`services/btd6_data_provider.py:40–304` (provider Protocol + 3 impls).

## 3. Limbus domain model — first cut (verify at ingest; the game updates often)

Stable structure (high confidence); specific counts move with patches — confirm during ingestion.

- **Sinners** — the 12 LCB fixed roster (Yi Sang, Faust, Don Quixote, Ryōshū, Meursault, Hong Lu,
  Heathcliff, Ishmael, Rodion, Sinclair, Outis, Gregor).
- **Identities** (`pm_identity`) — alternate versions of a Sinner (100+, growing). Fields: rarity
  (0 / 00 / 000), HP, speed range, **defences per damage type** (Slash / Pierce / Blunt: Fatal / Weak /
  Normal / Endure / Ineffective), **affinity (Sin)**, **skills** (per skill: base power, coin count, coin
  power, offense level, effects), **passives** + **support passive**.
- **E.G.O** (`pm_ego`) — equippable, by **grade** (ZAYIN / TETH / HE / WAW / ALEPH), with resource cost
  (Sin affinities), skill effects, corrosion threshold.
- **Sins (7):** Wrath, Lust, Sloth, Gluttony, Gloom, Pride, Envy. **Damage types (3):** Slash, Pierce, Blunt.
- **Status / keywords** (`pm_status`) — Burn, Bleed, Tremor, Rupture, Sinking, Poise, Charge, Haste, … (+
  newer ones; verify). These are first-class "ask the bot what X does" targets.
- **Enemies / Abnormalities** (`pm_abnormality`) — Mirror Dungeon + story encounters (cross-links to
  LobCorp / LoR Abnormalities).
- **Story** (`pm_story`) — Cantos (I…current), Mirror Dungeons, Intervallos.

**Later-phase models (sketch):** *Library of Ruina* — Combat Pages, Key Pages, Abnormality battles,
Floors/Books, Light/Dice/Emotion. *Lobotomy Corporation* — Abnormalities (risk ZAYIN→ALEPH, work types
Instinct/Insight/Attachment/Repression), Departments, Agents, Ordeals, E.G.O gear.

## 4. Refinements this pushes back into the plan

1. **Slice A ingestion** = StaticData identity JSON first (not a Cargo scrape) — the plan §5 is patched
   to say so and to point here.
2. **Resolver** must be **Sinner-namespaced** (100+ Identities, repeating nicknames) — BTD6's flat
   alias-collision model (audit red flag) won't scale.
3. **Seam discipline:** generalise the plumbing only; leave BTD6's upgrade/crosspath/paragon/mode code in
   a `BTD6Domain`. Proof-first still holds: build the minimal Limbus vertical, then extract.

## Sources

- [Limbus Company Wiki (wiki.gg)](https://limbuscompany.wiki.gg/) · its `siteinfo` API (Cargo absent) ·
  [List of Identities/Data](https://limbuscompany.wiki.gg/wiki/List_of_Identities/Data) ·
  [Category: Pages with Datamined Info](https://limbuscompany.wiki.gg/wiki/Category:Pages_with_Datamined_Info)
- [Lethe modding docs — static-data dump](https://docs.lethelc.site/guide/) ·
  [LEAGUE-OF-NINE/FurinaLC](https://github.com/LEAGUE-OF-NINE/FurinaLC) ·
  [steviegt6/limbus-server](https://github.com/steviegt6/limbus-server)
- [meatpnppet/limbus_data_analysis](https://github.com/meatpnppet/limbus_data_analysis) ·
  [bw1nd/limbus_helper](https://github.com/bw1nd/limbus_helper) ·
  [MusicOnline/LimbusCompute](https://github.com/MusicOnline/LimbusCompute)
- [retcons story logs](https://retcons.github.io/limbus-storylogs/) ·
  [retcons identity logs](https://retcons.github.io/limbus-identitylogs/) ·
  [ProjectMoon Cogitopedia (Miraheze)](https://projectmoon.miraheze.org/)

## Related

[program plan](project-moon-knowledge-domain-plan-2026-06-21.md) ·
[idea capture](../ideas/project-moon-wiki-knowledge-domain-2026-06-21.md) · router **Q-0192** ·
[btd6 folio](../subsystems/btd6.md) · [ai folio](../subsystems/ai.md).
