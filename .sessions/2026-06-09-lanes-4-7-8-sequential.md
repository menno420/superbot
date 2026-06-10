# 2026-06-09 — Execution-plan Lanes 4 + 7 + 8, one sequential session (3 PRs)

**Arc:** the first *sequential* multi-lane session (vs. the morning's parallel-agent
burst): Lane 4 → Lane 7 → Lane 8 in order, **one PR per lane**, each branched from
latest `main` (no stacking). #639 merged mid-session; the remaining branches were
re-synced against post-merge main where it mattered.

**Shipped:**

- **Lane 4 — #639 (merged):** Answerability Phase 3 — the three self-awareness tools
  (`get_ai_tool_catalog` · `get_ai_policy_explanation` · `btd6_answerability`),
  audience-tiered at construction over the #616 read model (Q-0047/Q-0048).
- **Lane 7 — #640:** Settings hub actionable-groups discovery
  (`customization_catalogue.actionable_settings_groups()`, 11 live groups) +
  paginated >25 reachability + per-guild routing availability markers (audit Phases 0+1).
- **Lane 8 — #642:** Help surface-map counts reconciled **and pinned by test**
  (10 hubs · 29 subsystems · 36 extensions · 28 define the hook) + the 28-test
  characterization net for the five Help render paths. No behavior changes.

Per-lane detail: the scoreboard's executor notes
(`docs/planning/multi-lane-execution-plan-2026-06-09.md`) + each PR body.

**Decisions made alone (ratify if wrong):**

- **`btd6_answerability` name + grounding domain** (Lane 4): the roadmap's candidate
  name was `get_btd6_answerability_snapshot`, but the tool *must* join the faithfulness
  ledger (the BTD6_ANSWER path checks every number in a reply against it — an
  unledgered inventory would block its own replies), and the catalogue invariant pins
  grounding ⟺ the `btd6_*` prefix. Named for the constraint, documented in code/PR.
- **`DOMAIN_CONFIG_SUBSYSTEMS = {"cleanup"}` as a declared Phase 1 seam** (Lane 7):
  domain-panel groups are a declared table, not discovery — Phase 2 replaces it with
  real registrations. Adding a name affects discovery only.
- **Availability = guild-scope routing rows only** (Lane 7): channel/category
  restrictions deliberately don't mark a group (a partial restriction isn't a
  group-level state); routed-off groups stay reachable with a "⛔" marker.

**Flagged for maintainer:**

- **Prod checks owed:** (1) the three Lane-4 tools' live model loop (no sandbox key) —
  probes: "what can you do here?" / "why didn't you reply to him?" / "what BTD6 data do
  you have?"; (2) a visual `!settings` hub walk (sandbox verified structure + the
  11-group taxonomy, not Discord rendering).
- **Shared-ledger merge order:** #640 and #642 both touch `current-state.md` /
  `roadmap.md`. #642 carries the **final superset state** (all three lanes) — if the
  second-to-merge conflicts, take #642's side. (#640 was re-synced to post-#639 main
  in-session.)

**Context delta (reflection interview):**

- **Needed but not pointed to:** the *faithfulness-verifier interaction* with new
  BTD6-adjacent tools — nothing in the Lane-4 read set said "a tool whose output the
  model restates on the BTD6 path must be in the grounding allowlist." Found by reading
  `natural_language_stage`'s guard block. Routed: now stated in the catalogue comment,
  the scoreboard executor note, and the AI folio line. Also: the routing rows store
  *subsystem keys* (not cog class names) — found only by reading the setup section's
  option values; now noted in `group_availability`'s docstring.
- **Pointed to but didn't need:** PR #616's notes (the introspection service's
  docstrings + tests were sufficient); `consolidated-productive-session-plan` §5 for
  Lane 7 (the settings audit §4/§6/§11 carried everything).
- **Discovered by hand:** the help surface map's counts were stale in **two different
  generations** in the same doc ("23 of 24" and "25 of 26") — count claims without a
  pin test rot at whatever rate each paragraph is edited; the Lane-8 pin closes the
  class for that doc. Consider the same pattern for other count-bearing binding docs.
- **One change that would have helped:** a one-line "registry tool-addition recipe" in
  the AI folio (spec → handler → `_ALL_TOOL_SPECS` → `build_registry` catalog →
  `CATALOGUE` entry → toolset → the two enumeration tests) — assembled by hand from
  three files this session. Filed mentally for the next AI-lane agent via the folio
  line; small enough to add when the folio is next touched.

**Process notes:** one-PR-per-lane with fresh-from-main branches worked; the only
friction class was the shared status ledgers (`current-state.md` header / Recently
shipped / `roadmap.md` rows) colliding across the session's own open PRs — handled by
making the last PR the superset and re-syncing after each merge event. Grooming pass
skipped per the multi-lane plan's parallel-lane convention (three lanes + reconciliation
was the session's capacity).
