# Session: P1-1 eval-coverage expansion — non-BTD6 uncovered tools (20 → 27/34)

> **Status:** `complete` — night-executor run; born-red card flipped as the deliberate final step (Q-0133).

**Branch:** `claude/determined-gauss-6zzlo8` · **Date:** 2026-06-15 · **Type:** P1-1 (S1 AI eval matrix) · **Trigger:** scheduled executor issue #894

## What this did

Took the exact handoff the previous run (#886) left in its `.sessions/` card: the eval pick-list's
**non-BTD6 uncovered surface**, same turn-key tool-selection-probe pattern as #881/#886. Added **7
golden probes** to `tests/evals/cases.py` for the remaining read-only non-BTD6 tools, each offering the
*real* production spec (pulled via `all_tool_specs()` — some are guild/flag/scope-gated so they aren't
in the SERVER_OWNER registry `cases.py` builds):

- **server-introspection** (`_ACK_SERVER_TOOLS`, 5): `get_server_overview` · `list_server_channels` ·
  `list_server_roles` · `lookup_member` · `list_all_members` — the "look at this server" surface.
- **AI self-awareness** (1): `get_ai_policy_explanation` — "will you reply here / why not", pairs with
  the existing `get_ai_tool_catalog` probe.
- **operator diagnostics** (1): `diagnostics_health_snapshot` (platform-owner scope) — "how are you
  doing right now".

Collapsed the now-empty acknowledged sets in `tests/evals/test_eval_coverage.py` so
`_ACK_UNCOVERED_TOOLS` is now exactly `_ACK_BTD6_TOOLS` (the 7 specialized BTD6 lookups — the entire
remaining gap), raised `_TOOL_COVERAGE_FLOOR` **20 → 27**, bumped `GOLDEN_SET_VERSION` (`2026-06-15.2`).
Tests-only, additive; the live probes run with creds, the CI drift guard proves coverage structurally.

Verified: `tests/evals/` 41/41 · coverage `27/34` (uncovered = the 7 ack'd BTD6 lookups) · offline
smoke scorecard 16/16 · `check_quality --full` green (9698) · `check_architecture` 0 errors.

## Context delta

- One small infra add was needed vs. #886's pure-append: `cases.py`'s `_tool()` only knew the
  SERVER_OWNER registry (28 tools), but `get_server_overview`/`list_*`/`lookup_member` only enter
  `build_registry` when a live `guild` is passed (and member tools behind a flag), and
  `diagnostics_health_snapshot` is platform-owner-gated. Added a `_CATALOGUE = all_tool_specs()`
  fallback so a probe can offer the *real* spec for a gated tool without faking a guild. The spec
  object is identical either way (`min_scope` is the SoT) — no behavior change, just reach.
- The grader is `tool_called(name)` (selection, not arithmetic) — data correctness stays unit-tested in
  `guild_introspection_service` / `health_snapshot_service`. `tool_results` stubs were shaped to match
  the real service returns (checked) so the probes read true even though the grader only checks dispatch.

## 💡 Session idea (Q-0089)

**A `--coverage` mode on `scripts/run_evals.py` that prints the eval tool/task coverage ratio + the
uncovered pick-list as a one-line scorecard** (e.g. `tools 27/34 · uncovered: btd6_bloon_filter, …`).
Right now the only way to see the ratchet state is to read `_TOOL_COVERAGE_FLOOR` + diff the ack sets by
hand (which is how the floor mismatches in past passes slipped). The drift-guard *test* enforces it, but
a creds-free human/Hermes-readable scorecard line makes the remaining gap legible at a glance and gives
the next executor its pick-list without opening the test. Small, stdlib, pairs with the existing
`--smoke` scorecard. Captured (not built this run — out of this run's tests-only scope).

## ⟲ Previous-session review (Q-0102)

The #886 run (and its #884 sibling) did this loop **well**: it left a precise, actionable handoff in its
card naming *exactly* this tranche and even the tool names, so this run started cold and shipped without
re-deriving anything — that handoff is why this was a 20-minute continuation, not a re-investigation.
The one improvement it surfaces (now acted on as the Q-0089 idea): the coverage state lives only in a
test constant + prose, so each run re-counts by hand and the **floor is easy to set wrong** — a
`run_evals --coverage` scorecard would make the ratchet self-reporting and close that small recurring
papercut. Nothing to hallucinate beyond that; the pattern is healthy.

## Handoff

The acknowledged-uncovered set is now **only the 7 specialized BTD6 lookups** (`btd6_bloon_filter`,
`btd6_ct_team_status`, `btd6_geraldo_lookup`, `btd6_paragon_calculate`, `btd6_power_effect`,
`btd6_power_lookup`, `btd6_relic_lookup`) — the final eval-coverage tranche, same turn-key pattern, one
more PR to reach 34/34. Each needs its real spec verified (build a registry / `all_tool_specs()`) before
writing the probe so the user message triggers THAT tool. After that the deterministic/offline half of
P1-1 is fully covered and the remaining P1-1 work is the **creds-gated live battery** + absence-guard
**Layer B** (design-for-review), then **P1-3 invariants**.
