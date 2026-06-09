# 2026-06-09 — AI tool orchestration Phase 3 (typed policy + operator UI)

## Arc

"Continue the work of the last PR." The last PR was **#618** (orchestration Phase 2 —
provider-neutral tool-choice + budgets), so the documented next step is the plan's
**Phase 3** (typed orchestration-policy storage + resolver + the operator UI). `current-state`
said to confirm scope because the operator UI is net-new AI exposure under the expansion gate;
I asked, and the maintainer chose **"Full Phase 3 incl. operator UI"** — explicitly lifting the
gate for it this session (as they did for `btd6_round_cash`). Delivered the whole lane (PR D+E).

## Shipped

- **Migration `062`** — nullable `orchestration_profile` column on `ai_guild_policy` /
  `ai_channel_policy` / `ai_category_policy` (additive, idempotent; NULL = inherit → compatible
  default = today). No CHECK — valid keys live in the service layer, so adding a preset never
  needs a migration.
- **`services/ai_orchestration_presets.py`** — built-in presets (the only v1 source of profile
  keys). `compatible_default` reproduces today's behaviour byte-for-byte; `balanced_helper`,
  `btd6_grounded`, `btd6_grounded_strict` (REQUIRED_GROUP), `no_tools` (NONE). A drift test pins
  every referenced toolset to the catalogue.
- **`services/ai_orchestration_policy.py`** — the resolver: most-specific-wins (channel →
  category → guild → default), generation-keyed cache, dry-run trace, **DB-fault-tolerant**
  (a read fault degrades to the default — never breaks a reply; also keeps DB-less unit tests
  green).
- **`services/ai_orchestration_mutation.py`** — the audited write seam (mirrors
  `ai_policy_mutation`): admin gate + built-in-key validation + generation bump + cache
  invalidate + `ai.orchestration.*_changed` events (catalogued in `events_catalogue.py`).
- **`utils/db/ai.py`** — `orchestration_profile` added to the policy SELECTs + three column-only
  setters (channel/category insert `mode='inherit'`; the NL upsert paths leave the column
  untouched — disjoint columns, no clobber).
- **`AIConfigSnapshot.orchestration`** (`ai_config_projection_service`) — read-only sub-namespace
  (guild profile + override counts); the read-only invariant (`test_ai_readonly_invariants`) was
  *strengthened* to forbid the new writers from the projection layer.
- **Live wiring** — `natural_language_stage._invoke_gateway` resolves the profile and threads
  `enabled_toolsets`/`disabled_tools` into `build_registry` + `tool_choice`/`tool_budget` onto the
  `AIRequest`. **Default byte-identical**; `if not specs: handlers=None` keeps the no-tools path
  identical to the legacy single-shot.
- **Operator UI** — `views/ai/tools/` + the `ai:tools` AI-panel button: per-scope profile pickers
  (Guild/Channel/Category) writing through the audited seam, and a **dry-run analyzer** (resolved
  profile + offered/withheld tools with reason codes + budget). The cog stayed at 795 LOC (no new
  `!ai` subcommand → no growth, no doc-pin §4 trigger).
- **Docs** — binding `docs/ai-config-ownership.md` (read model / mutation seam / resolved
  semantics / `ai:tools` custom_id), the orchestration plan (Phase 3 + PR D/E ✅), the AI folio,
  `current-state`.

## Verification

- `python3.10 scripts/check_quality.py --full` → green (see PR). `check_architecture --mode
  strict` → 0 errors. New + adjacent AI tests (orchestration, tool-calling, stage, projection,
  readonly-invariant, events-catalogue, ai-config doc-pin) all pass.
- **Live**: clean boot (AICog + all cogs, 0 errors), migration 062 applied (3 columns present),
  panel shows `ai:tools` (8 buttons), a real-DB round-trip (set guild/category/channel profile →
  resolve precedence → projection counts → clear → invalid-key + non-admin rejected), and the
  dry-run preview embed resolves `btd6_grounded (source channel)` after a write.

## Context delta

- **Needed but not pointed to:** the **800-LOC cog ceiling** (`ai_cog.py` was at 795) forced the
  Tools surface to be a panel-button→view with **no `!ai tools` subcommand**. That also dodged the
  `test_ai_config_ownership_doc` §4 UI-surface pin. Worth flagging in the AI folio for the next
  agent adding an AI surface: prefer a panel button, not a cog subcommand.
- **Needed but not pointed to:** the live `_invoke_gateway` runs `build_registry` **without a DB**
  in the existing tool-calling tests — adding a resolver DB read there would have reddened them.
  The fix (resolver degrades to default on any read fault) is *also* the correct production
  resilience. A subtle coupling no doc warned about.
- **Pointed to but didn't need:** the plan's §7 (complex-BTD6 workflow), §10 (answer contracts),
  §12.1 (audit trace) — all Phase 4 / deferred; only §4–§6, §8–§9, §13–§14 drove this slice.
- **Discovered by hand:** new bus events must be added to `core/events_catalogue.py KNOWN_EVENTS`
  or the bus logs an "uncatalogued event" warning (and `test_events_catalogue` would catch it).
  The catalogue path isn't in the mutation-seam runbook.
- **Deferred (named):** the durable per-decision orchestration *audit trace* (plan §12.1) — the
  dry-run preview already gives operators inspectability, and deferring it keeps the hot
  `ai_decision_audit` write path + its doc §5 pin untouched. Phase 4 picks it up.
- **Unresolved for next session:** reconcile this PR's #. Live tool-choice/budget *behaviour*
  (the model actually narrowing/forcing) still needs a provider-keyed prod check — the sandbox AI
  is degraded (no key), so only the deterministic resolve/mutation/UI paths were live-verified.
