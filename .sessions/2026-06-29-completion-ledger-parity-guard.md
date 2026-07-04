# 2026-06-29 — Registry↔completion-ledger parity guard + inventory sort/filter

> **Status:** `complete`

**Run type:** routine · dispatch

## What this run did

Empty-fire scheduled dispatch (no work order). Acted on the live **S1 ▶ Next** offline startable
(completion-arc deepening) and the previous run's (#1545) ↪ Next priority list. Shipped **three complete
slices** in one PR (#1553), CI-green.

### Slice 1 — registry↔completion-ledger parity guard (Q-0089 follow-up)
The previous run proposed this as its Q-0089 session idea, and the ledger README has flagged
"*a registry↔ledger parity guard is a noted follow-up*" since the arc began. Now that the completion
ledger is at **36/36 ◐ assessed**, the next drift class is the ledger itself. Built
`scripts/check_completion_ledger_parity.py` (stdlib, read-only, Q-0105 disposable header): asserts the
registry ↔ ledger ↔ cert triangle — every certifiable registry subsystem (registry **minus** the
documented routing-only/knowledge-domain exclusion set) has exactly one ledger row + a `units/<key>.md`
cert, every cert maps to a live registry key (or the documented non-registry `setup` exception), no
orphans/dupes. Pure `analyze()` core (injectable) + a `check()` disk-gatherer; advisory by default,
`--strict` for CI. **12 tests** (each violation class A/B/C on synthetic data + a live committed-state
regression that gates CI). Replaced the README "noted follow-up" line with the guard pointer.

> The guard **immediately earned its keep**: on first run it flagged `btd6` as a certifiable registry
> key with no cert — because the registry key has a digit and my initial exclusion set (and an earlier
> manual key-scan with `[a-z_]+`) silently dropped it. `btd6` is a knowledge domain the README already
> excludes; added it to `EXCLUDED`. A guard catching a gap in its own author's first draft is the point.

### Slice 2 — inventory sort cycle (cert punch #5, sort half)
The inventory category detail view was fixed rarest-first only. Added a `🔀 Sort:` cycle
(Rarity / Quantity / Name) — pure `_sort_items()` total order (item key breaks ties), footer shows the
active mode, button suppressed for a single-item category, cycling resets to page 0. +9 tests.

### Slice 3 — inventory type filter (cert punch #5, filter half) → punch #5 CLOSED
Added a `Filter by type…` select to the category view (shown only when a category mixes >1 item type;
"All types" restores). Refactored `_CategoryView` so `_all` (sorted full set) and `_shown` (filtered
slice) are distinct; `_apply()` recomputes the shown slice + page count and **clamps the page** when a
filter shrinks the set; sort + filter compose. +6 tests (15 view tests total). Together with slice 2 this
**fully closes inventory completion-cert punch #5**.

**Bug-first fix-on-sight (Q-0166):** removed 2 stale claim files (`fv5s7p`, `fv5s7p-inv` — both merged
branches, flagged by `check_stale_claims --strict`).

## Verification
- `python3.10 scripts/check_quality.py --full` → **All checks passed** (13088 passed, 48 skipped).
- `python3.10 scripts/check_architecture.py --mode strict` → **0 errors** (49 pre-existing warnings).
- `python3.10 scripts/check_completion_ledger_parity.py --strict` → consistent.
- `python3.10 scripts/completion_scoreboard.py --check` → up to date (36 assessed; unchanged).
- `python3.10 scripts/check_consistency.py` → all rules pass (allowlisted the pre-existing `items[:3]`
  hub preview — a top-3 embed preview with "+N more", flagged only because the file now also builds a
  select; scoped by `::qualname` so the file's real select stays checked).
- mypy clean on `disbot/cogs/inventory_cog.py`; economy→inventory nav lifecycle test still green.

## 💡 Session idea (Q-0089)
**A "select-options bounded source" annotation for `check_consistency`.** This run hit the
`select_option_truncation` heuristic's coarseness: adding *any* `discord.ui.Select` to a file makes the
checker flag *every* `[:N]` slice in that file, including unrelated embed-preview slices — so each new
select forces a per-line `::qualname` allowlist entry that says "this slice isn't a select." The
allowlist already has a whole "Embed / text displays, NOT selects" section proving this is a recurring
tax. A cheaper fix: let the checker recognize a slice whose source is provably bounded (a literal list,
a `sorted({...})` over a small fixed catalog, or an inline `# bounded:<reason>` marker) and skip it
without a YAML round-trip — shrinking the allowlist to *genuine* truncations. Genuinely tied to this run
(I paid the tax directly); a small AST refinement, not a new system.

## ⟲ Previous-session review (Q-0102)
The previous run (#1545, the 17-unit server-fn assessment sweep) did its best work in the **research
fan-out** — one read-only agent per unit, with synthesis + Q-0120 spot-verification kept in the main
session — clearing 17 independent units where a serial cadence would have taken many sessions. Its one
genuine miss: it left its certs' punch-lists tagged `[offline]`/`[owner]` but **did not distinguish
"offline = just build it" from "offline-looking but actually owner-decision-first."** Inventory punch #2
("audit item grants") was tagged `offline/owner` and listed as a top offline pick — but it is really an
*owner-granularity* decision (auditing every ore-dig would flood the audit channel), not a build task.
**System improvement this run surfaced + acted on:** a punch-list line should separate *mechanical
offline* from *decision-first* work, so a later empty-fire run doesn't barrel into a hot-path change
with the wrong shape. I refined inventory punch #2 to state the question explicitly and contrast it with
BUG-0029 (XP *role* grants, which legitimately belong on the audited seam) — turning a mis-tagged
"offline pick" into a clear owner decision.

## ⚐ Doc audit (Q-0104)
Ran the automated half: `check_current_state_ledger --strict` (clean; benign newer-merge lag recorded by
the #1560 pass), `check_docs --strict` (passed), `check_consistency` (passed), `completion_scoreboard
--check` (up to date), `check_completion_ledger_parity --strict` (consistent). New owner decisions: none
(the guard formalizes the *existing* README exclusion set in code; no new Q). Everything from this run
lives in its durable home (the guard + tests, the inventory cog + tests, the inventory cert, the S1 ▶
Next, this log). No chat-only residue.

## 📤 Run report
- **Did:** (1) built the registry↔completion-ledger parity guard (Q-0089 follow-up, 12 tests); (2)
  closed inventory completion-cert punch #5 — sort cycle + type filter on the category view (15 tests);
  (3) fix-on-sight stale-claim cleanup · **Outcome:** shipped (CI green, auto-merge armed)
- **Shipped:** #1553 — `scripts/check_completion_ledger_parity.py` +
  `tests/unit/scripts/test_check_completion_ledger_parity.py` · `disbot/cogs/inventory_cog.py`
  (sort cycle + type filter) + `tests/unit/cogs/test_inventory_display_logic.py` (+15 cases) ·
  `docs/planning/feature-completion/{README,units/inventory}.md` · `architecture_rules/consistency_exceptions.yml`
  (one allowlist line) · S1 ▶ Next · 2 stale claims removed.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** **1 surfaced (not blocking this PR):** inventory punch #2 ("audit item
  grants") needs an owner *granularity* call — which trail + what frequency — before building, because
  the naive "audit every grant" would flood the admin audit channel (the coin trail is the
  high-frequency `EVT_BALANCE_CHANGED` economy log, not `audit.action_recorded`). Documented in the
  inventory cert punch #2. No *new* Q recorded (it's a refinement of an existing punch-list item).
- **⚑ Owner manual steps:** none (no migration, no data step; runtime change auto-deploys on merge).
- **⚑ Self-initiated:** yes — empty-fire dispatch; all three slices built without a dispatch/owner ask
  (Q-0172). Grounded in the live S1 ▶ Next + the prior run's ↪ Next priority list + the ledger README's
  own "noted follow-up" + Q-0209 completion-cert punch #5. The stale-claim cleanup is fix-on-sight (Q-0166).
- **↪ Next:** inventory's remaining gaps are now **owner-gated** (#1 item actions · #2 item-grant audit
  *granularity decision* · #3 capability cleanup) + the `◐ → ✔` live walkthrough. Other offline deepening
  picks still open: **Blackjack split/insurance/surrender** engine work (games punch-list) · **logging
  ignored-lists / channel+voice events** · inventory item-detail **density** (punch #4, minor). The new
  parity guard now keeps the 36/36 ledger honest automatically as the registry evolves.
