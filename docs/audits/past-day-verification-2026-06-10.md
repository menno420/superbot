# Past-day verification — 2026-06-10 end-of-day

> **Status:** `audit` — a dated end-of-day verification snapshot of the
> 2026-06-10 parallel-agent burst (**21 merged PRs, #648–#668**). Findings
> reflect `main` @ `09a4b16` (the #668 merge). Source and merged PRs win over
> this file. Produced by the past-day verification + docs-cleanup session
> (**PR #669**); session log:
> `.sessions/2026-06-10-past-day-verification-docs-cleanup.md`.

## 1. Executive verdict

**GREEN, with one yellow caveat class.** The past day's work is **correctly and
completely merged**: all 21 PRs are on `main`, zero PRs are open, the migration
chain (052→066) is contiguous with no duplicates, the full CI mirror is green
(**8,817 passed / 22 skipped**), architecture strict mode reports **0 errors**
(84 known warnings), and `check_docs` passes. The one real merge mistake of the
day — the stacked mining PRs #663/#664/#665 merging into their **parent
branches** instead of `main` — was caught and corrected the same day by the
completion PR **#667**, and this session **content-verified** that everything
the three PRs claimed is actually on `main`.

The yellow caveat class: a handful of **doc-truth and small-behavior findings**
(§4) — none are stability bugs, none block the next session. Two were real
code findings, both contained: `quick_craft` silently skipped its documented
game-XP award (**fixed in this session's PR #669**, regression-pinned), and
the #656 **Help Preview staff panel re-derives Help truth outside the #657
projection seam** (mislabels governance hides as "locked", ignores overlay
state — documented with the exact fix; left for a focused Help-lane PR). The
biggest remaining risks are operational, not code: the two AI model loops
(#634/#639) and the BTD6 answers remain **unverified live in production** (no
sandbox provider key — maintainer-only checks), and the day's new live
surfaces (mining panels, Help overlay) have had **no human click-through**
yet.

## 2. Verified merged-work table

All merge times 2026-06-10 (UTC). "Source/tests/docs ✓" = re-verified this
session against `main` @ `09a4b16`, not taken from PR descriptions.

| PR | Area | Claimed change | Source | Tests | Docs | Remaining issue |
|---|---|---|---|---|---|---|
| #648 | docs | Queue-truth reconciliation + consolidated plan | ✓ (docs-only) | n/a | ✓ | none |
| #649 | BTD6 | v55.1 `--all` towers cutover, game-native stats | ✓ | ✓ | ✓ | item 4 maintainer spot-check owed |
| #650 | runtime | Batch 1 truth/clarity (shell deleted, renames) | ✓ `ResourceMutationPipeline` gone; `ensure_and_get_economy` live | ✓ | ✓ | none |
| #651 | runtime | Batch 2 surface-classification invariant | ✓ `unclassified_entry_points` populated + AST mirror | ✓ | ✓ | none |
| #652 | services | Batch 3 routing/threshold-clear seams | ✓ audited clears; fence widened | ✓ | ✓ | RS07 chain slice deliberately open |
| #653 | BTD6 | Decode wave 1 (thorn rings, sentries, banana economy) | ✓ | ✓ | ✓ | none |
| #654 | settings | Phase 2 `DomainPanelSpec` + Q-0064 rows | ✓ | ✓ coverage invariant | ✓ | pointer-classification tail open (tracked) |
| #655 | BTD6 | Post-cutover verification, carry-forwards decoded | ✓ audit 91 CLEAN / 0 DELTA | ✓ | ✓ | none |
| #656 | adaptive | P1C Access Map + Help Preview subpanels | ✓ display-only fence | ✓ | ✓ | none |
| #657 | help | HLP-2 projection seam, five render paths | ✓ all five paths consume `HelpProjection` | ✓ | ✓ | none |
| #658 | BTD6 | Deterministic Ask parity + Effects/Minions renders | ✓ | ✓ | ✓ | none |
| #659 | help | HLP-3 overlay (migration 064, audited seam) | ✓ display-only; no editor UI shipped (correct) | ✓ | ✓ | editor UI = the known tail, not drift |
| #660 | docs | BTD6 backlog handoff truth-up | ✓ (docs-only) | n/a | ✓ | none |
| #661 | economy | RS01 atomic shop purchase (Q-0071=A) | ✓ one `db.transaction()` | ✓ incl. concurrency | ✓ | none |
| #662 | BTD6 | Navarch routing fix + items 6a–c | ✓ income/effect legs, shorthand, diacritics | ✓ | ✓ | none |
| #663 | mining | RS02 stage 1 (relocate + workshop workflow) | ✓ **via #667** — `utils/mining/` + `services/mining_workflow.py` on main | ✓ | ✓ | merged into parent branch, not main (corrected by #667) |
| #664 | mining | RS02 stage 2 (full write boundary + recipes) | ✓ **via #667** — AST ratchet live | ✓ | ✓ | same as #663 |
| #665 | mining | game-XP (065/066), ladders, UX, wear, PIL | ✓ **via #667** — migrations + `game_xp_service` on main | ✓ | ✓ | same as #663 |
| #666 | BTD6 | `btd6_probe.py` + carryover plan doc | ✓ tool runs offline | ✓ | ✓ | none |
| #667 | mining | Land the stranded #663/#664/#665 content on main | ✓ **content-verified** (see §4 method) | ✓ via suite | ✓ | none |
| #668 | BTD6 | Carryover grounding slice 1 + zero-fact sweep | ✓ bounded, labeled, read-only | ✓ 9 pins incl. screenshot sequence | ✓ | eval-harness pin still open (plan §4) |

**Merge-order note (the day's one real mechanics mistake, already corrected):**
#663 → base `confident-bohr` (15:26:22), #664 → base `mining-workflow-2a`
(15:26:34), #665 → base `mining-workflow-2b` (15:26:47) — i.e. each into its
stacked parent, *after* #661 itself merged to main (15:26:05). GitHub does not
auto-retarget a stacked base when the parent merges without branch deletion.
#667 (15:45:12) merged the assembled branch into main. Lesson recorded in
`.sessions/2026-06-10-mining-finalization.md`; nothing further owed.

## 3. Docs cleanup performed (this session, PR #669)

- **`docs/current-state.md`** — ▶ lane bullets: "Batches 1–6 … Next: Batch 7"
  corrected to **Batches 1–8 all executed** + the true remaining queue (RS07 ·
  Batch 4 pointer tail · Batch 9 · Batch 10 · Help editor UI); #666/#668 PR
  numbers added to the BTD6 lane; every 2026-06-10 "verify merged" hedge
  resolved; **Recently-shipped rebuilt newest-first for the full day**
  (#648–#668 — it previously stopped at #657 and had #658/#662 out of order);
  the stale "#634 verify merge state live" hedge dropped; Last-updated chain
  prepended.
- **`docs/roadmap.md`** — at-a-glance Now/Next/Later rows corrected (mining
  next-slice was still "workshop boundary first" — that shipped; Batch 7
  removed from Later; Batches 1–8 stamped done); Settings Phase 2 / Adaptive
  P1C / Help overlay / Building rows: hedges → merged PR numbers; BTD6 row now
  records item 7 slice 1 (#668) + probe (#666).
- **`docs/planning/consolidated-implementation-plan-2026-06-10.md`** — Batch
  1/5/6 headers: hedges resolved; **Batch 7 header stamped COMPLETE** with real
  PR numbers (#663/#664 were "the follow-up PR" / "the next PR"); **Batch 8
  header stamped EXECUTED (#649)**; §5 gained a queue-state banner (what
  remains); §6 rows (HLP-3 / BTD-3 / GME-1 / GME-2) updated to shipped; **§8
  next-agent recommendation rewritten** (it still recommended starting
  Batch 1).
- **This document created** as the day's verification record; linked from
  current-state (▶ lane + Last-updated), roadmap (Next row), and the
  consolidated plan (§5/§8).

Remaining docs debt is listed in §4 (cleanup tier).

## 4. Bugs / inconsistencies found

Severity tiers per `docs/owner/agent-workflow-spec.md` §3.3.

### Tier 1 — critical blocker

- **None found.** No merge corruption, no migration conflicts, no
  architecture-boundary regressions, no test failures.

### Tier 2 — important improvement

- **The #656 Help Preview re-derives Help truth outside the #657 projection
  seam** (`disbot/views/server_management/access_map.py`,
  `build_help_preview_embed` :149-179). Its "hidden" bucket keys only off the
  ledger-classification help axis, so a **governance-denied** subsystem shows
  as "Shown as locked" while live Help *hides* it; HLP-3 overlay hides/renames
  don't render at all. Meanwhile `project_help_with_execution`
  (`services/help_projection.py`) — built for exactly this consumer — has
  **zero production callers**. Sequencing artifact: Batch 5 (#656) shipped
  hours before Batch 6's seam (#657/#659) and was never migrated. Display-only
  + admin-gated, so not critical — but it is an operator *truth* surface
  disagreeing with live Help, and the last duplicate Help-filtering logic in
  the tree. **Fix (next Help-lane slice):** rebuild the preview's buckets on
  `project_help_with_execution` + add governance-deny and overlay-state test
  cases (the existing pin at `tests/unit/views/test_access_map_view.py:144`
  never exercises governance-deny). *This session corrected the false
  docstring claim at `help_projection.py` ("operator surfaces consume this")
  and noted the drift in the server-management folio; the migration itself is
  deliberately left for a focused PR.*
- **`mining_workflow.quick_craft` silently skipped its documented 8-XP award**
  (`game_xp_service._AWARDS["quick_craft"] = 8`; regular `!craft` awarded,
  quick-craft didn't). **FIXED in this session's PR #669** — award now rides
  the op's own transaction like every other action writer, regression-pinned
  by `test_apply_quick_craft_awards_crafting_xp_in_txn`.
- **Production-only verification debt is accumulating.** Three claim classes
  are deliberately unverifiable in the sandbox and are now stacked: the
  #634/#639 AI model loops, the BTD6 live answer quality (decode-status item
  4), and the day's new click-surfaces (mining Gear/Recipe panels, `!fastmine`,
  PIL cards, Help overlay round-trip on a real guild). None is a code bug; all
  need ~15 minutes of the maintainer in production. The longer this waits, the
  more ships on top of unverified surfaces.

### Tier 3 — cleanup (all fixed in PR #669 unless noted)

- The mining write-boundary AST fence omitted `record_depth` / `add_game_xp`
  (theoretical gap — verified zero such calls exist) — **fence widened**.
- `utils/db/games/game_xp.py` docstring said "migration 064"; actual is 065 —
  **fixed**.
- `utils/mining/recipes.py` fallback `DEFAULT_RECIPES` drifted from
  recipes.json (iron pickaxe wood 1 vs 2) — **aligned** (fallback-only;
  JSON wins at runtime).
- #666/#668 PR numbers were unstamped in decode-status ⭐ / item 7 and the
  carryover plan badge — **stamped**; plan §3 step 4 now annotates the
  as-built deviation (grounds the prior turn's text directly).
- `docs/subsystems/btd6.md` still said "extraction remains paused" while its
  own Current-state section (and reality — #649–#668) said implemented/
  resumed — **corrected**.
- `docs/subsystems/settings-bindings-provisioning.md` still described the
  retired `DOMAIN_CONFIG_SUBSYSTEMS` frozenset as the live seam and implied
  Q-0055–Q-0059 were unanswered — **both corrected**.
- `docs/subsystems/server-management.md` had no record of the #656 subpanels
  — **added** (with the Tier-2 drift note).
- *Not fixed (deliberate):* `mining_exploration_brainstorm.md` historical
  "Shipped" notes cite pre-RS02 `cogs/mining/*` paths (history, accurate at
  write time); `ct_relics.json` carries `game_version: 54.0` (harmless —
  CT relic facts are bloonswiki-labeled, never game-data-labeled).

### Tier 4 — future opportunity (captured only)

- The stacked-PR retarget trap now has a recorded lesson; a tiny
  `scripts/` check ("does any open PR base on a non-main branch?") could make
  it structural. Not queued — capture only.
- `btd6_probe.py` prints the *resolver's* confidence only, so paragon-pass /
  carryover hits print `confidence: 0.0` beside 12+ facts — mildly confusing
  triage output; the facts count is the real signal.
- `core/runtime/command_descriptions.py` (the AI command catalog) calls
  `is_command_hidden_from_help` directly — not a Help render path, but worth
  folding into the catalogue/projection vocabulary whenever that file is next
  touched.

### §4a Per-area verification detail

Three parallel read-only verification passes over `main` @ `09a4b16`, each
grep/test-grounded (file:line evidence retained in the session transcript):

- **BTD6 / AI answerability** (#653/#655/#658/#660/#662/#666/#668): carryover
  grounding is **bounded and safe** — reads at most the 3-turn per-channel
  floor the model prompt already sees, channel-scoped, no raw turn text enters
  the fact payload, cannot recurse, Ask/`btd6_lookup` byte-identical, carried
  facts ride the number-guard ledger. Sweep fixes, Navarch income/effect legs,
  shorthand + diacritic matching, minion→owner grounding, and the honest
  source labels all verified at source; `btd6_probe.py` runs offline (12 facts
  incl. the income line for the Navarch question). Version stamps consistent
  at 55.1. **No overstated live-verification claims found** — every doc defers
  the model loop to the maintainer. Focused tests: **1,766 passed** across
  five suites.
- **Mining / economy** (#661/#663/#664/#665/#667): all stack artifacts on
  `main`; `cogs/mining/` gone (single `mining_cog.py` routes everything
  through the workflow); independent grep found **zero** write-primitive calls
  in cogs/views and zero outside `mining_workflow.py`; every multi-write op
  (incl. the 4-write gear-break path and all market ops) runs in one
  `db.transaction()` with events post-commit and XP on the same conn;
  migrations 065/066 idempotent, no 064 conflict; deeper ladders / diamond
  lantern→MAGMA / `!fastmine` / duels wear / PIL cards / depth records all
  present. The #667 merge carried exactly the 13 expected commits. Focused
  tests: **219 passed**. The one behavior-vs-spec gap (quick-craft XP) is
  fixed above.
- **Help / Settings / consolidated batches** (#650/#651/#652/#654/#656/#657/
  #659): #650 deletions/renames clean (zero stragglers); all **five** Help
  render paths consume the one `HelpProjection` with click-time re-checks; the
  overlay stack is a textbook seam (sole-writer DB module → admin-gated/
  validated/audited/cache-invalidating mutation service → fault-tolerant
  cached reads → projection-applied hide/rename), display-only **verified**
  (no execution path consults the overlay; the Q-0055 AST fence exists);
  **no editor UI exists** (matching every doc claim); `DomainPanelSpec`
  coverage invariant pins the frozenset gone; role-threshold clears audited
  with the fence widened; RS07 (chain cog in-cog writes) confirmed genuinely
  open at `cogs/chain_cog.py:107-537`. Focused tests: **596 passed**. The one
  drift is the Tier-2 Help Preview finding above.

## 5. Current repo state — honest opinion

**Structurally strong:**

- **Mutation discipline.** After RS01/RS02 + Batch 3, every economy/mining
  write goes through a workflow service owning one transaction, AST-fenced;
  role-threshold clears are audited; routing mutations own their audit. This
  was the mapping campaign's biggest finding class and it is now closed.
- **Help.** Five render paths on one reason-coded projection + a display-only
  overlay store behind an audited seam — the drift class (per-path filter
  logic) is structurally dead.
- **BTD6 data.** Game-native v55.1 everywhere, 0-DELTA audit, deterministic
  grounding with honest source labels, and a triage tool (`btd6_probe.py`)
  for the next live miss.
- **The workflow itself.** 21 PRs from parallel agents merged in one day with
  exactly one mechanics mistake (stacked bases), which was diagnosed,
  corrected, and recorded the same day. The per-lane ledger convention held
  under real concurrent merges.

**Still fragile / do not expand yet:**

- **AI exposure surface** — both model loops await production checks; Phases
  4/5 answerability and any write/external/UI capability stay gated
  (Q-0048). Do not widen until the maintainer's live pass.
- **Mining balance** — the new economy knobs (deeper ladders, wear, game-XP
  soft cap) are tuned by construction, not by play; expect a balance pass
  after real usage before building structures pricing on top.
- **Chain game (RS07)** — still owns its config/state mutation in-cog; the
  one remaining named service-boundary hole.

**Most ready for further work:** mining structures (§7.5) on the new write
boundary; the Help overlay editor UI (all decisions answered); RS08 diagnostic
read-model extraction (bounded, read-only).

## 6. Recommended next session

**Best next session — maintainer live-walk + targeted fixes (manual review +
Sonnet support).** The single highest-value action is not agent work: the
maintainer spends ~15–20 minutes in production walking the day's new surfaces
— `!minemenu` → Gear/Recipe panels → craft diamond lantern → descend to MAGMA
→ a duel (wear) → `!character` (PIL card) → Help overlay hide/rename
round-trip → one BTD6 "does the navarch make coins" + follow-up "does it make
coins at end of round" (carryover) → the #634/#639 AI loops. A Sonnet session
rides along to fix whatever the walk surfaces (the act-envelope covers
contained fixes). This clears the §4 Tier-2 debt that everything else is
stacking on.

**Alternates (any order, all unblocked):**

1. **Mining structures §7.5 (Forge/Vault/Home)** — Fable/Opus *plan* +
   same-session execute (the games folio + brainstorm §7.5 route; the write
   boundary makes this safe now). The natural games-lane continuation.
2. **RS07 chain-service extraction + Batch 9 RS08 read-model extraction** —
   Sonnet, one session, both bounded and decision-free. Closes the last named
   service-boundary hole + starts Batch 9.
3. **Help-lane completion slice** — first migrate the #656 Help Preview onto
   `project_help_with_execution` (the §4 Tier-2 drift; seam exists, zero new
   contract design), then the overlay **editor UI** (audit Phase 5, Q-0059
   embed builder) — Fable/Opus planning first for the editor (UI-heavy,
   preview mandatory).
4. **Batch 10 planning round** (wizard-finalization slice selection + next AI
   §7 family selection) — Opus/Fable planning-only; produces the next two
   implementation prompts.

**Repo route for the next agent:** `.claude/CLAUDE.md` →
`docs/collaboration-model.md` → `docs/current-state.md` (▶ lane bullets are
now hedge-free) → this audit §5/§6 → the area folio for the chosen lane
(games / help audit / consolidated plan Batch 9–10) → `.sessions/` newest
logs. The consolidated plan's §5 queue-state banner is the implementation
queue truth.

## 7. Verification commands run (this session)

| Command | Result |
|---|---|
| `git status --short` / `git log --oneline -25` | clean tree; HEAD = `09a4b16` (#668 merge) |
| live GitHub `list_pull_requests state=open` | **0 open PRs** |
| live GitHub merged-PR sweep #644–#668 | merge times + base branches verified (the §2 table; stranded-stack mechanics confirmed) |
| `ls disbot/migrations/` | 052→066 contiguous, no duplicates; 064 help_overlay · 065 game_xp · 066 mining_depth_records |
| `python3.10 scripts/check_docs.py` | all checks passed (157 docs) |
| `python3.10 scripts/check_architecture.py --mode strict` | **0 errors**, 84 known warnings |
| `python3.10 scripts/check_quality.py --full` | black/isort/ruff/mypy clean; **pytest 8,817 passed / 22 skipped** in 106s |
| focused per-area test runs | see §4a |
