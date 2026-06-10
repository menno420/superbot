# Agent Context Pack — BTD6 Data / Tools

> **Status:** `reference` — generated orientation aid (NOT source of truth).
> Generated: 2026-06-10 · Subsystem key: `btd6`

> **NOT SOURCE OF TRUTH.** This file is generated from `docs/agent/index.yml`.
> Canonical docs listed under *Binding docs* always win over this pack.
> Edit the index, then re-run `python3.10 tools/agent_context/build_pack.py`.

## Folio (start here)

[`docs/subsystems/btd6.md`](../../../docs/subsystems/btd6.md) — canonical area index, debug router, current state, next candidates.

## Binding docs (read before editing)

- docs/architecture.md
- docs/ownership.md
- docs/runtime_contracts.md
- docs/decisions/006-btd6-data-provenance-ownership.md

## Reference docs (consult on demand)

- docs/btd6/btd6-provenance-schema.md
- docs/btd6/btd6-gamedata-decode-status.md
- docs/btd6/btd6-derived-value-groundedness-finding.md
- docs/btd6/btd6-absence-claim-guard-design.md

## Likely source areas

- disbot/cogs/btd6_cog.py
- disbot/cogs/btd6/
- disbot/cogs/btd6_events_cog.py
- disbot/cogs/btd6_ops_cog.py
- disbot/cogs/btd6_reference_cog.py
- disbot/cogs/btd6_strategy_cog.py
- disbot/services/btd6_ai_context_service.py
- disbot/services/btd6_ai_service.py
- disbot/services/btd6_cache_service.py
- disbot/services/btd6_data_provider.py
- disbot/services/btd6_data_service.py
- disbot/services/btd6_fact_store.py
- disbot/services/btd6_grounding_service.py
- disbot/views/btd6/
- disbot/utils/db/btd6_data.py
- disbot/utils/settings_keys/btd6.py

## Related subsystems

- `docs/agent/generated/ai.context.md`
- `docs/agent/generated/media-youtube.context.md`

## Do NOT create

These systems already exist — duplicating them is the main source of
architectural drift in this repo.

- A BTD6-owned YouTube/media pipeline — ADR-007 declares media a shared platform subsystem
- Derived values without provenance/source evidence — groundedness guards are required
- A new extraction path without consulting docs/btd6/btd6-gamedata-decode-status.md

## Active gates

- BTD6 feature expansion gated on: bot-wide stability + provider/provenance checks + caching/source-health clarity + AI behavior/config correctness. See docs/current-state.md.
- ADR-006 provenance schema required for all new BTD6 fact types.

## Verification commands

Run these before pushing any change to this subsystem:

```
python3.10 scripts/check_quality.py --full
python3.10 scripts/check_architecture.py --mode strict
python3.10 -m pytest tests/unit/btd6/ -x -q
```

---

*This pack is orientation only.  When this file and a canonical doc
disagree, the canonical doc wins.  When this file and source code
disagree, source code wins.*
