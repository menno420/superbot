# 2026-06-09 — AI Cog Completion + BTD6 Answerability roadmap

## Arc

Produced a planning-only, source-verified roadmap for completing the AI answerability and
self-awareness bridge, using BTD6 round cash as the first proof path. No runtime code,
tests, migrations, tools, UI, or service behavior changed.

## Findings

- `RoundEntry`, `rounds.json`, and deterministic tests already carry and verify per-round
  and cumulative standard/Medium cash for rounds 1–140.
- Named round cash already reaches BTD6 grounding context, and instructions describe
  endpoint subtraction for ranges; no dedicated deterministic range-cash API/tool exists.
- Bot self-awareness already covers caller standing, bounded command catalog, and recent
  non-reply audit blocks. AI tool/settings/answerability introspection remains fragmented.
- `ai_config_projection_service` and policy dry-run are strong existing owners to compose,
  not replace.
- Runtime work remains behind the global AI/BTD6 expansion gate and orchestration-first
  sequencing decision.

## Docs changed

- Added `docs/planning/ai-btd6-answerability-roadmap-2026-06-09.md`.
- Linked it from `docs/roadmap.md` and the AI/BTD6 subsystem folios.
- No new owner-router question was needed; unresolved activation choices retain safe
  defaults in the roadmap.

## Verification performed

- Read binding workflow/current-state/architecture/ownership/runtime docs and area folios.
- Inspected the central NL stage, AI tool registry, instruction/knowledge/config/policy/
  audit services, BTD6 data/context/resolver/grounding paths, settings/navigation helpers,
  and relevant tests/docs.
- Ran `scripts/context_map.py` successfully with the active Python for all ten requested
  AI/BTD6/settings source paths; the requested `python3.10` invocation failed because
  PyYAML is absent from that interpreter.
- Attempted CodeGraph package verification; it was unavailable/hung in this environment,
  so every claim was manually grep/read-verified.
- Could not inspect live open PRs because `gh` is absent and no git remote is configured;
  local merged history and state docs were inspected instead.
- `check_architecture.py --mode strict` passed with tracked warnings. Gamedata anchor/audit
  checks require an external `--dump` path, which is not present in this checkout.

## Context delta

- **Needed but not pointed to:** `docs/btd6/btd6-smoke-test-checklist.md` contains the
  already-expected round-range cash behavior and was essential to avoid misclassifying the
  lane as new data work.
- **Pointed to but didn't need:** server-management source/folios were not material beyond
  confirming the AI expansion gate; no server-management plan was opened deeply.
- **Discovered by hand:** round-range cash currently works through two grounded endpoint
  records plus instruction-layer subtraction, while the direct BTD6 tool registry has
  composition ranges but no round-cash query.
- **Unresolved assumptions:** live open-PR conflicts and exact orchestration-catalogue shape
  must be re-verified before activating implementation.
