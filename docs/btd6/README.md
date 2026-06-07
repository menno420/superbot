# BTD6 documentation island

> **Status:** `reference` — index for the BTD6 docs. The folio
> [`../subsystems/btd6.md`](../subsystems/btd6.md) is the entry point; ADR-006 and
> `docs/current-state.md` win over anything here.
>
> **Paused work.** BTD6 data extraction is **paused pending the ADR-006 provenance
> schema** (`../decisions/006-btd6-data-provenance-ownership.md`). These docs capture the
> decode/extraction/pipeline direction; they are subordinate to ADR-006 and the global
> AI/BTD6 gate in `docs/current-state.md`. Do not resume extraction from a docs session.

These were consolidated out of the top level of `docs/` into `docs/btd6/` so the island
is one folder behind the folio instead of ~14 files scattered at the root.

## Decode / gamedata

- [`btd6-gamedata-decode-status.md`](./btd6-gamedata-decode-status.md) — living status of
  the gamedata decode effort (the worklist + decode classes).
- [`btd6-gamedata-decode-explainer.md`](./btd6-gamedata-decode-explainer.md) — how the
  gamedata decode works, explained.
- [`btd6-decode-inventory-v55.md`](./btd6-decode-inventory-v55.md) — decode inventory for
  game data version 55.
- [`btd6-gamedata-dictionary.md`](./btd6-gamedata-dictionary.md) — field/term dictionary
  for the decoded gamedata.
- [`btd6-gamedata-native-schema.md`](./btd6-gamedata-native-schema.md) — the native
  gamedata schema.

## Pipeline / backends / data

- [`btd6-data-pipeline.md`](./btd6-data-pipeline.md) — the ingestion/data pipeline shape.
- [`btd6-data-backends.md`](./btd6-data-backends.md) — data backend options and the choice.
- [`btd6-cloud-data.md`](./btd6-cloud-data.md) — cloud-data backend notes.
- [`btd6-data-tuning-handoff.md`](./btd6-data-tuning-handoff.md) — data-tuning handoff notes.
- [`btd6-game-file-extraction-plan.md`](./btd6-game-file-extraction-plan.md) — plan to
  extract data from the game files (gated on ADR-006).

## AI / grounding

- [`btd6-ai-tool-calling-plan.md`](./btd6-ai-tool-calling-plan.md) — BTD6 AI tool-calling
  direction.
- [`btd6-absence-claim-guard-design.md`](./btd6-absence-claim-guard-design.md) — design for
  absence-claim guards (don't assert a fact is absent without evidence) in grounded context.
- [`btd6-derived-value-groundedness-finding.md`](./btd6-derived-value-groundedness-finding.md)
  — finding on keeping derived values distinguishable from sourced facts.

## Checklists

- [`btd6-smoke-test-checklist.md`](./btd6-smoke-test-checklist.md) — BTD6 smoke-test
  expectations.

## Related (outside this folder)

- `../decisions/006-btd6-data-provenance-ownership.md` — binding provenance/ownership ADR.
- `../audits/agent-d-btd6-ai-subsystem-audit-2026-06-05.md` — BTD6/AI subsystem audit.
- [`../subsystems/btd6.md`](../subsystems/btd6.md) — the folio (start here).
