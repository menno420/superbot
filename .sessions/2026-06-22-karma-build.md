# Session — 2026-06-22 · Karma (thanks/upvote reputation) — build

> **Status:** `complete` — Karma subsystem shipped; full CI-mirror suite green on the rebased head.

**Run type:** owner-directed. **Branch:** `claude/peaceful-franklin-klgw3f`.
**Trigger:** the owner explicitly authorized building the Karma plan ("you can execute this plan",
2026-06-22) and went offline. Executing with the plan's **recommended defaults** (both surfaces with
reaction off by default · positive-only · pure reputation · karma-roles deferred · 1h cooldown /
10-per-day cap), since the 5 design questions were not individually answered.

## What I'm about to do

Implement the Karma subsystem per
[`docs/planning/karma-reputation-plan-2026-06-22.md`](../docs/planning/karma-reputation-plan-2026-06-22.md),
delivering the plan's **PR 1 (foundation + audited seam) + PR 2 (cog + leaderboard)** as one cohesive
PR — Karma is a net-new isolated subsystem (nothing else imports it), so the risk is contained and a
single PR avoids inter-PR merge coordination while the owner is offline. **PR 3 (reaction-grant +
karma-roles) is deferred** per the recommended defaults.

Files: migration `093_karma.sql` (karma + karma_audit_log) · `utils/db/karma.py` (+ `__init__`
re-export) · `services/karma_service.py` + `services/karma_config.py` · `core/events_catalogue.py`
(`karma.granted`) · `utils/settings_keys/karma.py` (+ re-export) · `cogs/karma/schemas.py` +
`cogs/karma_cog.py` · `KarmaProvider` in `rank_providers.py` · `config.py` extension · subsystem
registry entry · INV-K invariant test + service tests · `docs/ownership.md` rows + `docs/subsystems/karma.md`.

## What changed

Implemented the Karma subsystem end-to-end (plan PR 1 + PR 2 in one PR; PR 3 deferred):
- **DB:** migration `093_karma.sql` (`karma` + append-only `karma_audit_log`) ·
  `utils/db/karma.py` (credit/get/top/rank + the two anti-abuse reads + audit insert) ·
  re-exported from `utils/db/__init__.py`.
- **Service:** `services/karma_service.py` (`give` — positive-only, no-self, cooldown,
  daily cap; `get_record`) emitting the catalogued `karma.granted` · config read model
  `services/karma_config.py` (`KarmaPolicy`/`load_policy`).
- **Settings:** `utils/settings_keys/karma.py` (+ re-export) · `cogs/karma/schemas.py`
  (`enabled`/`cooldown_seconds`/`daily_cap` SettingSpecs).
- **Cog + leaderboard:** `cogs/karma_cog.py` (`!thanks`, `!karma [give]`, `/karma`) ·
  `KarmaProvider` in `rank_providers.py` (+ `rep`/`reputation`/`karmalb` aliases) ·
  `config.py` extension · `subsystem_registry.py` entry.
- **Tests:** INV-K invariant (`test_inv_k_karma_service.py`) · `test_karma_service.py`
  (grant/audit/event + self/cooldown/cap/disabled rejections) · `test_karma_schemas.py`
  (default parity). Updated `test_rank_providers.py` canonical-categories set.
- **Docs + generated artifacts:** `docs/ownership.md` rows (table/service/event/audit) ·
  new folio `docs/subsystems/karma.md` · plan rebadged BUILT. Regenerated the crosswalk
  (`extension_roles.yaml` + doc), dashboard/site.json, atlas, and the env-vars doc head
  (the config.py line shift from adding the extension).

**Decisions made autonomously (owner offline):** delivered PR1+PR2 as one PR (net-new
isolated subsystem — contained risk); used the plan's recommended defaults; homed karma as
a **first-class governance subsystem under the Community hub** (`parent_hub: "community"`,
alongside XP/Role). The repo invariant (post-#1290) requires every advertisable subsystem to
be hub-homed, and the Community hub's button view was at Discord's 5-per-row cap — so I
**generalized `CommunityHubView` to wrap buttons past 5/row** (a contained, test-covered
capacity evolution any new community subsystem would have triggered) rather than hide karma
from help. Existing buttons keep their positions; karma + the wrapped row are additive.

Full first-class integration also required: `KarmaCog.build_help_menu_view` (the Community-hub
button target + the `help_hook` discoverability path), pinning `/karma` in the top-level
slash-surface ledger, homing the karma folio to sector S1, karma sections in the
settings-customization command-map + the help-command-surface-map inventory (with count bumps),
and updates to the pinned hub/registry/view/provider tests. Several rounds were driven by the
PR's own CI feedback (the new-subsystem ripple surfaced as failing invariants one tranche at a
time) plus two rebases onto a moving `main` (PR #1331 farm, then #f768c5f) — generated-artifact
conflicts resolved by regeneration each time.

⚑ **Self-initiated:** none — owner explicitly authorized building the plan ("you can
execute this plan"). PR 3 (reaction-grant + karma-roles) deferred, owner-gated.

Verification: `check_quality.py --full` green (black + ruff + isort + mypy[801 files] + 11.8k
pytest) on the final rebased head; `check_architecture --mode strict` clean (no new karma
violations); `check_docs --strict` + `check_current_state_ledger --strict` green.

## 💡 Session idea (Q-0089)

[`audited-score-subsystem-scaffold`](../docs/ideas/audited-score-subsystem-scaffold-2026-06-22.md)
(carried from the planning session, now *validated by building it*): adding karma required
hand-editing **a dozen+** coordinated surfaces beyond the core seam — `config.py`,
`subsystem_registry.py`, `hub_registry.py`, `extension_roles.yaml`, the sector-folio map, the
`CommunityHubView` row-wrap, three regenerated artifacts (dashboard, atlas, env-vars), and
five pinned hub/registry tests. A `new_score_subsystem` scaffold
+ a "new-subsystem ripple" checklist (the artifacts/registries a new subsystem must touch)
would turn this from archaeology into a fill-in-the-blanks job. The build is the ground-truth
the idea's Q-0105 header asked for — promote it.

## ⟲ Previous-session review (Q-0102)

The previous session (the Karma *planning* session, PR #1330) paid off directly here: its
"mirror economy/XP exactly" framing and concrete code-pointers (db→service→cog→provider) were
accurate against source, so the build had almost no rework on the core seam. One genuine miss
it could have flagged: the plan enumerated the *seam* files but **not the registry/artifact
ripple** (subsystem_registry, extension crosswalk, dashboard/atlas/env-vars regen, hub
capacity) — exactly where the 31 first-run test failures landed. **System improvement
(initiated):** that ripple is mechanical and knowable, so it belongs in a checklist/scaffold,
not rediscovered per subsystem — captured as the Q-0089 idea above and worth a `new-subsystem`
skill step.

## 📋 Doc audit (Q-0104)

- `check_docs --strict` green (425 docs; folio reachable, badges valid, ratchets at 20).
- `check_current_state_ledger --strict` — only benign-lag (8 PRs newer than marker #1320;
  the next reconciliation records them). #1332 records on merge — no manual ledger edit now
  (adding an unmerged PR would break the Recently-shipped ratchet).
- New owner decision (build authorization + the recommended-defaults selection) is captured
  here + in the plan's BUILT banner; no router Q needed (no rule change).
- All generated artifacts regenerated and verified fresh by their drift tests.
