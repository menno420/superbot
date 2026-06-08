# BTD6 data provenance — schema contract

> **Status:** `binding` — this is the follow-on docs/schema PR that
> [ADR-006](../decisions/006-btd6-data-provenance-ownership.md) requires.
> Merging this PR **lifts the RC-10 gate** and allows BTD6 data extraction
> to resume against a defined provenance contract.
>
> **Last updated:** 2026-06-08.

---

## 1. Purpose

Every BTD6 fact surfaced to a user carries an implicit claim: *"this figure
came from source X, fetched at time T, and is valid for game version V."*
Without a formal representation that travels with the fact, different services
make that claim inconsistently — one renders a freshness label, another silently
drops it, a third re-fetches freshness on demand via a separate query.

This doc defines:

1. The **`DataProvenance`** value object — the single composed envelope every
   live BTD6 fact carries.
2. How it is **assembled** from a joined fact row.
3. The **owner-per-fact-type matrix** — which service writes and which reads
   each fact domain.
4. How the **hybrid storage** split works (`btd6_facts` vs `btd6_data_blobs`
   vs committed JSON).

---

## 2. Scope — live facts vs static blobs

BTD6 data splits cleanly into two families with different freshness models:

| Family | Examples | Freshness model | Storage |
|---|---|---|---|
| **Live facts** | Race/boss/CT metadata + leaderboards, active event windows, challenge lists | Regularly re-fetched from NK API or bloonswiki; can become stale | `btd6_facts` table (Postgres) |
| **Static blobs** | Tower/hero/upgrade/bloon stats, map metadata, round composition | Game-version-locked; only change on a patch | Committed JSON under `disbot/data/btd6/`, optionally mirrored to `btd6_data_blobs` |

**`DataProvenance` applies to live facts only.** Static blob provenance is
carried inline as a `source` field stamped into each JSON file by
`parse_gamedata.py` / `fetch_bloonswiki.py` (e.g.
`"source": "BTD Mod Helper game data export"`). Those scripts are the write
path; `btd6_stats_service` is the sole runtime reader.

---

## 3. `DataProvenance` value object

Python definition (canonical — lives in
`disbot/services/btd6_fact_store.py`, exported from `__all__`):

```python
@dataclass(frozen=True)
class DataProvenance:
    source_id: int          # FK → btd6_source_registry.id
    source_key: str         # e.g. "nk_btd6_races"
    source_name: str        # e.g. "data.ninjakiwi.com"
    source_kind: str        # "official_api" | "webpage" | "patch_notes"
    trust_tier: int         # 1 = highest (official_api), 2 = webpage/patch
    fetched_at: datetime    # UTC, when the fact was last written
    game_version: str | None  # e.g. "43.0" or None for non-version-stamped facts
    freshness: FreshnessBucket  # "fresh" | "aging" | "stale" | "never"
```

**Rules:**

- `freshness` is computed from `fetched_at` via
  `btd6_source_registry.bucket_freshness()` — **do not recompute inline**.
- `trust_tier` 1 means the source is an official NK API endpoint; tier 2 is
  a third-party page or patch notes. The fact store's ordering
  (`trust_tier ASC, fetched_at DESC`) puts tier-1 facts first.
- The object is **frozen** — it must never be mutated after construction.
- `source_kind` is the raw DB value; callers should compare against the
  `"official_api"` | `"webpage"` | `"patch_notes"` literals from the
  schema constraint, not a free string.

### Helper property

`DataProvenance.label` — a short human-readable string for embeds/logs:
```
"data.ninjakiwi.com (tier 1, fresh)"
```

---

## 4. Assembling `DataProvenance` from a fact row

`btd6_db.fetch_facts_for_intent` already joins `btd6_source_registry` and
returns rows with `source_id`, `source_key`, `source_name`, `source_kind`,
`trust_tier`, `fetched_at`, `game_version` present. Use `extract_provenance`:

```python
from services.btd6_fact_store import extract_provenance, FactRow

provenance = extract_provenance(row)     # row is a dict from fetch_for_intent
typed_row = FactRow.from_row(row)        # body + provenance in one typed object
```

`FactRow` is the typed wrapper for new code; `fetch_for_intent` continues to
return raw dicts for backward compatibility with the one existing caller
(`btd6_context_service`).

---

## 5. Owner matrix

| Fact-type family | Write owner | Read owner | Storage |
|---|---|---|---|
| `btd6.races_*`, `btd6.race_*` | `btd6_fetch_service` | `btd6_knowledge_service` | `btd6_facts` |
| `btd6.boss_*` | `btd6_fetch_service` | `btd6_knowledge_service` | `btd6_facts` |
| `btd6.ct_*`, `btd6.odyssey_*` | `btd6_fetch_service` | `btd6_knowledge_service` | `btd6_facts` |
| `btd6.events_index` | `btd6_fetch_service` | `btd6_knowledge_service` | `btd6_facts` |
| `btd6.challenge_*`, `btd6.map_*` | `btd6_fetch_service` | `btd6_knowledge_service` | `btd6_facts` |
| Tower/hero/upgrade/bloon/round/map **static stats** | `parse_gamedata.py`, `fetch_bloonswiki.py` (offline scripts) | `btd6_stats_service` | committed JSON + `btd6_data_blobs` |
| **Cross-cutting composition** (anything the AI or an embed sees) | — | `btd6_view_model_service` | (composed from above) |

**The invariant:** `btd6_view_model_service` is the only service that should
compose across fact families. It may call `btd6_knowledge_service` and
`btd6_stats_service` in the same response, but neither of those should call
the other directly.

---

## 6. Hybrid storage

```
Live event/race/boss/etc. data
  → fetched by btd6_fetch_service
  → written to btd6_facts (source_id FK → btd6_source_registry)
  → read by btd6_knowledge_service / btd6_fact_store.fetch_for_intent
  → DataProvenance assembled by extract_provenance()

Static tower/hero stats
  → extracted offline by parse_gamedata.py / fetch_bloonswiki.py
  → committed as JSON under disbot/data/btd6/
  → optionally mirrored to btd6_data_blobs at startup (BTD6_DATA_BACKEND=postgres)
  → read by btd6_stats_service (file or blob, same interface)
  → provenance is the inline "source" + "version"/"_last_updated" field in the JSON
```

No new storage table is introduced. `btd6_data_blobs` already carries a
`sha256` column for integrity checking; its `updated_at` is the blob-write
timestamp, not the game-data extraction timestamp (use the JSON's own
`"version"` field for that).

---

## 7. Relationship to `DataFreshness` in the view-model service

`btd6_view_model_service.DataFreshness` is a **view-model** object — it
summarises freshness for an embed's footer. It is assembled *from*
`DataProvenance` or from a `SourceHealth` object returned by
`btd6_source_registry.list_health()`. The two types are not the same:

| Type | Layer | Scope | Used for |
|---|---|---|---|
| `DataProvenance` | service (fact store) | One fact | Carries source attribution through the read pipeline |
| `DataFreshness` | service (view model) | One embed panel | Renders freshness into a Discord embed footer |
| `SourceHealth` | service (source registry) | One source row | Operator-facing health dashboard |

When building a new embed that needs a provenance footer, the correct flow is:
`FactRow.provenance → DataFreshness(state=provenance.freshness, ...)` — not
re-querying the source registry.

---

## 8. Resuming extraction

This PR implements the provenance contract. The following are now unblocked:

- New BTD6 data extraction (buff decode tail, zone types, subtower mechanisms)
- New fact-type registrations (any new `fact_type` string)
- The tower cutover (game-native stats replacing bloonswiki)

**The existing `extracted ≠ reachable ≠ answerable` discipline survives this
gate.** Provenance is a prerequisite for extraction, not a substitute for
verifying that extracted data is rendered and answerable live. See
`btd6-gamedata-decode-status.md` for the ordered decode backlog.

---

## 9. Explore tooling (new)

`scripts/explore_gamedata.py` — added in the same PR. A read-only search tool
for the BTD Mod Helper game-data dump that makes decode sessions faster: find
all instances of a model type, search by field name, inspect a tower's
structure, list all `$type` values. Run with `--help` for full usage.

```bash
git clone --depth 1 https://github.com/Btd6ModHelper/btd6-game-data /tmp/btd6gd
python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --list-types
python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --search RangeSupportModel
python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --field damageAddative --in "Towers/DartMonkey"
python3.10 scripts/explore_gamedata.py --dump /tmp/btd6gd --struct MoabShoveZoneModel
```

Provenance header (per repo convention, 2026-06-08): added to aid BTD6 decode
work; **unverified — confirm outputs against the raw dump a few times before
trusting them fully.**
