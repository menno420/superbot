# Ultracode fleet brief — parallel build run (2026-06-19)

> **Status:** `plan` — coordination brief for a multi-agent ("ultracode") **parallel** build run.
> Not new product scope: it operationalizes already-scoped, **ungated** work into **file-disjoint**
> units a fleet of agents can build at once. Source code + merged PRs win over this doc. Companion to
> [`repo-structure-improvement-plan-2026-06-19.md`](repo-structure-improvement-plan-2026-06-19.md);
> the architecture units are verified live via `scripts/check_architecture.py --mode strict`
> (76 warnings, 0 errors at write time).

## Why this exists

Ultracode's edge is **breadth** — many agents on independent units at once. That only pays off if the
units don't collide. This brief pre-partitions ~16 ungated units into **disjoint file sets** so a fleet
runs with near-zero coordination, and every unit is correctness-gated by CI before it can land. Pick a
subset or run the whole thing.

**The collision rule that matters most:** two agents must never edit the same file. The roster below is
built so they don't. **Agents must NOT each edit the shared ledgers** (`docs/current-state.md`,
`docs/owner/active-work.md`) — 16 simultaneous appends would conflict. This brief *is* the claim ledger;
the reconciliation pass folds the merged PRs into `current-state.md` afterward.

## Lane A — architecture boundary-debt burndown (8 disjoint units)

Burns down the layer-boundary debt the structure review flagged. All `disbot/` runtime refactors —
each PR must pass `scripts/check_architecture.py --mode strict` **and** the full test suite. Clears ~48
of 76 warnings.

| Unit | Files (the agent's exclusive set) | What | Risk |
|---|---|---|---|
| A1 | `cogs/economy/_helpers.py`, `cogs/xp/_helpers.py`, `cogs/economy_cog.py`, `cogs/xp_cog.py`, `views/economy/`, `views/xp/` + new `services/economy_helpers.py`, `services/xp_helpers.py` | Move the two `_helpers` out of cogs into `services/`; fix view imports | Low |
| A2 | `cogs/moderation/_helpers.py`, `cogs/moderation_cog.py`, `views/moderation/modals.py` + new `services/moderation_helpers.py` | Move moderation `_helpers` → `services/` | Low |
| A3 | `cogs/blackjack/_state.py`, `_persistence.py`, `actions.py`, `views/blackjack/`, `views/games/blackjack_panel.py` + new `services/blackjack_state.py`, `services/blackjack_persistence.py` | Move blackjack state/persistence → `services/` (resolve the intra-cog `actions`↔`_state` cycle) | Med |
| A4 ⚠ | `cogs/diagnostic/_platform_embeds.py` (2,280 lines), `cogs/diagnostic/_helpers.py`, `views/diagnostic/` + new `services/diagnostic_embeds.py`, `services/diagnostic_helpers.py` | Move the big embed module → `services/`. **Grep ALL callers incl. lazy/function-body imports first** | Med (large) |
| A5 ⚠ | `cogs/deathmatch/actions.py`, `cogs/deathmatch_cog.py`, `views/games/deathmatch_panel.py` | Untangle the `actions`↔`deathmatch_cog` **circular import**, then lift the shared UI types out of the cog | Med (cycle) |
| A6 | `governance/__init__.py`, `cache.py`, `cleanup.py`, `execution.py`, `resolver.py`, `writes.py` + new `utils/governance_exceptions.py` | Move governance exception types → `utils/` so the layer stops importing `services` | Med |
| A7 | `services/game_state_service.py`, `services/platform_consistency.py` + `utils/db/` (extend) | Wrap the raw `pool.execute()`/`conn.execute()` calls (13 of 18 raw-SQL warns) in `utils/db/` functions | Low |
| A8 | `views/btd6/admin_panel.py`, `views/btd6/strategy_review.py`, `views/channels/list_panel.py`, `views/settings/edit_channel.py`, `edit_number_presets.py`, `edit_role.py`, `views/setup/launcher.py`, `views/xp/rank_view.py` | Each: extend `BaseView`/`HubView` if lifecycle fits, else add a one-line justification comment | Low |

> **A4 and A5 are the only ones needing care** (huge file / circular import). Run them last, or give
> those agents an explicit "map every caller — including lazy imports — before moving anything" step.

## Lane B — ungated tooling / ops / docs quick-wins (8 disjoint units)

File-disjoint from Lane A (these live in `scripts/`, `.github/`, `dashboard/`, `.claude/skills/`), so
Lane B can run **concurrently with Lane A**. Each is a small, low-risk, no-owner-decision unit.

| Unit | Files | What |
|---|---|---|
| B1 | `scripts/check_governance_files.py` + test | Presence + path-freshness guard for the new root files ([idea](../ideas/governance-files-presence-guard-2026-06-19.md)) |
| B2 | `scripts/check_ledger_hygiene.py` + test | Duplicate claim / idea-link detector ([idea](../ideas/ledger-dedup-linter-2026-06-16.md)) |
| B3 | `scripts/check_routine_permission_surface.py` + test | Fail if a routine command resolves to `ask` ([idea](../ideas/routine-permission-surface-lint-2026-06-16.md)) |
| B4 | `scripts/check_plan_backlog.py` + test | Automate the PLAN-BACKLOG-THIN flag (Q-0164) |
| B5 | `scripts/check_autospec_fidelity.py` + test | New AST guard flagging un-`spec`'d mock setattr ([idea](../ideas/autospec-mock-fidelity-guard-2026-06-16.md)) — **new script only, do not refactor existing tests** |
| B6 | `.github/workflows/*.yml` | SHA-pin the third-party Actions (pairs with the now-active Dependabot, which bumps the SHAs) |
| B7 | `dashboard/app.py`, `dashboard/templates/reviews.html` (new), `scripts/export_dashboard_data.py`, `docs/owner/review-inbox.md` (new) | Owner-review-inbox **Phase 1** — read-only `/reviews` page ([plan](owner-review-inbox-plan-2026-06-17.md)) |
| B8 | `.claude/skills/` (new files only) | Procedures→skills **batches 3–4** — additive skill files only ([plan](procedures-to-skills-conversion-plan-2026-06-17.md)). **Do NOT edit `.claude/CLAUDE.md`** (Q-0106) |

## Rules of engagement (every agent)

1. **Own only your unit's file set.** Never touch a file listed under another unit. Never edit
   `docs/current-state.md` or `docs/owner/active-work.md` (shared — they collide).
2. **Born-red session card.** First commit creates `.sessions/<date>-<slug>.md` with
   `> **Status:** \`in-progress\``; flip to `complete` as the last commit (per-file, so no collision).
3. **Green before merge.** `python3.10 scripts/check_quality.py --full` **and**
   `python3.10 scripts/check_architecture.py --mode strict` must pass. CI's `code-quality` is the
   required check; the PR auto-merges on green.
4. **Small, single-unit PR.** One unit = one PR. Don't widen scope.
5. **Flag self-initiated.** On the run-report `⚑ Self-initiated:` line, name the unit (Q-0172).
6. **A4/A5:** map every caller (including lazy/function-body imports) before moving code.

## Held — do NOT fleet these

- **`core/runtime → services` (arch-fix-11, ~13 runtime files)** — serial; one careful PR, done *after*
  Lane A lands. Breaking these breaks the whole bot. Same for `utils/db/pool.py` (arch-fix-6).
- **Consistency-linter graduation** (flipping rules to `error`) — PR #1063 is on the rails; let it settle.
- **`.claude/CLAUDE.md` / `.claude/settings.json` edits** — owner-live only (Q-0106).
- **Gated product lanes** — BTD6 floors (exhausted), fishing follow-ons, dashboard *writes* / control-API,
  anything `needs-hermes-review` or creds-gated.

## Kickoff prompt (paste into ultracode)

> Read `docs/planning/ultracode-fleet-plan-2026-06-19.md`. Launch one agent per unit in the Lane A and
> Lane B rosters, in parallel. Each agent owns ONLY its unit's listed files and follows the "Rules of
> engagement" exactly: born-red session card → implement the unit → `python3.10
> scripts/check_quality.py --full` and `python3.10 scripts/check_architecture.py --mode strict` both
> green → open one small PR that auto-merges on green → flag it self-initiated. Do NOT touch any file
> outside your unit, the shared ledgers (`current-state.md`, `active-work.md`), or anything in the
> "Held" list. Start Lane B and Lane A units A1–A3, A6–A8 immediately; run A4 (diagnostic, huge file)
> and A5 (deathmatch, circular import) last and tell those agents to map every caller — including lazy
> imports — before moving code. Report each PR number as it opens.

## Per-agent task template (if assigning manually)

> You are one agent in a parallel fleet. Your unit is **<Unit ID>** from
> `docs/planning/ultracode-fleet-plan-2026-06-19.md`. Touch ONLY these files: `<file set>`. Do `<what>`.
> Follow the brief's Rules of engagement (born-red card, both checks green, one small PR, auto-merge on
> green, flag self-initiated). Do not touch any other file or the shared ledgers.
