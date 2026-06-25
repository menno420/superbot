# Project Moon — Limbus Company committed data

> **Provenance / attribution.** These files carry **summarized, derived structural
> facts** about *Limbus Company* (Project Moon), not verbatim game dumps. Prose is
> summarized from [`limbuscompany.wiki.gg`](https://limbuscompany.wiki.gg) (CC-BY-SA)
> and general structural knowledge of the game. Following the BTD6 data norm
> (`disbot/data/btd6/README.md`) and the Project Moon recon's licensing note, we
> store **facts + provenance**, never raw `dumpedData` game files.

## Scope (PR 1 — the stable structural layer)

This is the *first* slice of the Limbus knowledge domain
([plan](../../../../docs/planning/project-moon-knowledge-domain-plan-2026-06-21.md)).
It deliberately covers only the **rock-solid, patch-stable structural facts** so the
domain shape can ship without the fragile exact-number ingest:

| File | Entity kind | Contents |
|---|---|---|
| `sinners.json` | `sinner` | the 12 fixed LCB Sinners |
| `sins.json` | `sin` | the 7 Sin affinities (+ colour) |
| `damage_types.json` | `damage_type` | Slash / Pierce / Blunt |
| `ego_grades.json` | `ego_grade` | ZAYIN → ALEPH (ranked) |
| `statuses.json` | `status` | common status keywords (conservative summaries) |

**Not yet here (later slices):** exact per-Identity / per-E.G.O **stats** (HP, speed,
defences, skill power/coin counts). Those move every ~2–3 weeks and come from the game's
**StaticData** dump — the BTD6-dump analogue — via a dedicated ingest lane, not by hand.
Treat the `statuses.json` mechanic descriptions as **verify-at-ingest** summaries.

## Schema

Each file is `{ data_version, game_version, source, entity_kind, entries: [...] }`.
Every entry has `id` (stable slug), `canonical` (display name), `aliases` (lowercased
match tokens), and `description`. Some kinds add fields (`sins.color`, `ego_grades.rank`).
Loaded + validated by `disbot/services/projmoon_data_service.py`.
