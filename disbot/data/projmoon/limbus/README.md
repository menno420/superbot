# Project Moon — Limbus Company committed data

> **Provenance / attribution.** These files carry **summarized, derived structural
> facts** about *Limbus Company* (Project Moon), not verbatim game dumps. Prose is
> summarized from [`limbuscompany.wiki.gg`](https://limbuscompany.wiki.gg) (CC-BY-SA)
> and general structural knowledge of the game. Following the BTD6 data norm
> (`disbot/data/btd6/README.md`) and the Project Moon recon's licensing note, we
> store **facts + provenance**, never raw `dumpedData` game files.

## Scope — the patch-stable structural + mechanics layer

The Limbus knowledge domain
([plan](../../../../docs/planning/project-moon-knowledge-domain-plan-2026-06-21.md)).
It deliberately covers only the **rock-solid, patch-stable facts** so the domain can ship
without the fragile exact-number ingest:

| File | Entity kind | Contents |
|---|---|---|
| `sinners.json` | `sinner` | the 12 fixed LCB Sinners (+ each one's `literary_origin`) |
| `sins.json` | `sin` | the 7 Sin affinities (+ colour) |
| `damage_types.json` | `damage_type` | Slash / Pierce / Blunt |
| `mechanics.json` | `mechanic` | core combat **rules** — Clash, Coin, Speed, Sanity, Stagger, damage resistance, Resonance, Skills, Defensive skills, Identity, Passives, E.G.O (+ `category`) |
| `ego_grades.json` | `ego_grade` | ZAYIN → ALEPH (ranked) |
| `statuses.json` | `status` | common status keywords (conservative summaries) |

`mechanics.json` is the combat layer a Project Moon player asked for (clashing · IDs +
passives · speed · enemy-stat concepts). It models the *rules* — which are patch-stable
and safe to hand-author with provenance — **not** per-unit numbers.

**Not yet here (the StaticData ingest lane):** exact per-Identity / per-E.G.O / per-enemy
**stat numbers** (HP, speed *values*, defences per type, skill power / coin counts). Those
move every ~2–3 weeks and come from the game's **StaticData** dump — the BTD6-dump analogue
— via a dedicated ingest lane, not by hand. Hand-committing them would risk *ungrounded
numbers*, which the groundedness discipline (ADR-006) exists to prevent. Treat the
`statuses.json` / `mechanics.json` descriptions as **verify-at-ingest** summaries.

## Schema

Each file is `{ data_version, game_version, source, entity_kind, entries: [...] }`.
Every entry has `id` (stable slug), `canonical` (display name), `aliases` (lowercased
match tokens), and `description`. Some kinds add fields (`sins.color`, `ego_grades.rank`,
`mechanics.category` — the combat-system group a mechanic belongs to,
`sinners.literary_origin` — the `{work, author}` each Sinner is drawn from).
Loaded + validated by `disbot/services/projmoon_data_service.py`.
