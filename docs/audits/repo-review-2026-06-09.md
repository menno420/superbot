# Repo review — 2026-06-09 (full-repo consistency, docs structure, plan executability)

> **Status:** `audit` — a dated review snapshot; findings reflect 2026-06-09 only.
> Requested by the maintainer ("thorough review … errors or inconsistencies … review of
> my documentation structure and how easy it is to navigate … how well you can execute
> the plans that already exist"). Everything **fixable in-session was fixed in the same
> PR** (per the bugs-first rule); the rest is routed below. Source and merged PRs win
> over this file.

---

## 1. Verification snapshot (all green)

| Check | Result |
|---|---|
| `check_quality.py --full` (true CI mirror) | ✅ **8352 passed, 16 skipped** (~95s) |
| `check_architecture.py --mode strict` | ✅ **0 errors**, 87 *known* (allowlisted) warnings |
| `check_docs.py` | ✅ pass — 141 docs, top-level ratchet 16/16, all badges valid, reachability gate green |
| CodeGraph build | ✅ 33,214 nodes / 59,190 edges, **0 file-level cycles** (3 function-level) |
| Open PRs at review time | **#620** only (test-only Postgres hardening for migration 062) |

The codebase is in genuinely good shape: CI-mirror green, zero architecture errors,
docs tooling self-validating. The findings below are about **drift and integration
gaps**, not broken code.

## 2. Errors & inconsistencies found

### 2.1 Fixed in this session's PR

1. **Community Spotlight read the DB raw from a cog** — `community_spotlight_cog.py`
   inlined `SELECT … FROM xp` via `db.fetchone`, the **only raw SQL in any cog** in the
   repo (everything else goes through a `utils/db/` owner function). Moved to the
   canonical xp owner: `utils/db/xp.py get_guild_xp_totals()` (+ package re-export +
   mock-pool tests).
2. **Community Spotlight latent crash** — `f"{guild.member_count:,}"` raises
   `TypeError` when `member_count` is `None` (unchunked/uncached guild). Hardened +
   regression-tested. The cog also had **zero tests**; it now has its first six
   (db owner, embed builder, EventBus feed cap).
3. **`docs/current-state.md` had drifted badly** — five unreconciled
   "*(this session)* … Reconcile PR # next session" markers (some three sessions old),
   and the merged side-lane **Community Spotlight** (#613/#614 + hotfixes #615/#617)
   was entirely unrecorded. All reconciled against live GitHub: orchestration Phase 3 =
   **#619**, Character overview = **#610**, market = **#609**, Context Compiler =
   **#594**, P0C conversion = **#592**. The ▶ Next action / Last updated mega-lines
   (~3,000 chars each, single-line) were rewritten into readable structured bullets —
   the doc-test pins sections, not formatting, so this was safe.
4. **`docs/roadmap.md` contradicted reality on three horizons** — AI was
   "**Later** (fully gated)" while orchestration Phases 1–3 and answerability 1A/1B/2
   had shipped with two explicit gate lifts; games was "**Later / maintenance**" while
   five mining Wave-1 PRs (#606–#610) shipped; the "wire `!explore`" bullet said
   "awaiting maintainer go" though #606 shipped exactly that. At-a-glance table +
   AI + games sections refreshed.
5. **`docs/ownership.md` §"Subsystem ownership" table** still said `role_thresholds`
   writes were "direct via `utils/db/roles.py`" — contradicting its own
   "NORMALIZED (P0C)" note 300 lines later. Cell now points at the audited
   `role_automation` seam (#592).
6. **Stale "reconcile" placeholders in three plans** — the orchestration plan, the
   answerability roadmap (×3), and the wire-exploration plan ("pending PR merge")
   now carry their real PR numbers.
7. **`docs/repo-navigation-map.md`** had no row for the new `community_spotlight` cog.
   Added (with its not-yet-registered status).
8. **`.session-journal.md` runbook facts were stale** — "latest migration is `057`"
   (actual: **062**; five migrations behind) and "~7470 tests" (actual: ~8350). Both
   corrected with self-defending phrasing ("check disk, don't trust this number").
9. **Adaptive plan §15 step 3** still listed all three P1B drift providers as "next"
   though `routing_access_conflict` shipped (#592) and `configured_resource_missing`
   was skipped-as-covered. Re-synced with §9 and current-state.

### 2.2 Found, routed — needs the maintainer (not fixed unilaterally)

1. **Community Spotlight is outside the platform** (→ **Q-0044**). Merged via two
   side-lane PRs 19 minutes apart (#613, #614), then hotfixed twice (#615 naming,
   #617 a nonexistent `utils.logger` import). It is **not** in
   `utils/subsystem_registry.py` / `hub_registry.py`, so typed Help, the Help dropdown,
   governance visibility, settings, and the §2 surface-map inventory cannot see it —
   the repo's own command-integration standard requires that wiring. Registration is
   the known **~8-touch-point** task (Q-0025 scaffold backlog). Also product-level:
   the aliases **`!hub`** and **`!server`** grab core platform vocabulary. Bannered in
   `help-command-surface-map.md` §3 until decided.
   *Lesson worth keeping:* side-lane PRs that bypass the session workflow also bypass
   the integration standard, the doc-test net (which pins only *registered* surfaces),
   and current-state recording — all three gaps showed up on this one feature.
2. **Audience-simulation decision** (→ **Q-0045**, formalized from adaptive plan §16.8
   item 3 where it was buried as an "implicit" open point). It blocks **two** queued
   deliverables (P1B `help_advertises_locked`, P1C Help Preview). Two candidate
   designs (synthesize a member-like object vs. a governance tier-input path) are
   written up in the router entry.

### 2.3 Minor (noted, deliberately not acted on)

- `ctx.send(..., ephemeral=True)` in the spotlight guild-check is a silent no-op for
  prefix commands (harmless; remove on next touch).
- Test-run warnings: an aiohttp `NotAppKeyWarning` (`healthserver.py:181`) and a
  `coroutine 'AutomationScheduler.run_forever' was never awaited` RuntimeWarning in
  one fixture — cosmetic, but cheap to silence on next touch of those files.
- `setup_cog.py` is at **744/800 LOC** (warn tier) — same ceiling that forced the
  `ai_cog` Tools surface to be a panel-button. Watch before adding to it.
- CodeGraph reports 3 function-level cycles (no file-level) — within normal bounds.

## 3. Documentation structure & navigability assessment

**Verdict: this is one of the most navigable agent-oriented repos I've worked in, and
the orientation investment demonstrably pays off.** Concretely, this session went from
cold start to confident cross-repo edits on the strength of the prescribed read path
(CLAUDE.md → collaboration-model → current-state → journal → AGENT_ORIENTATION) plus
the per-file `context_map.py` hook. What makes it work:

- **Self-enforcing docs.** Doc-tests pin load-bearing docs to source
  (`tests/unit/docs/`), `check_docs.py` gates reachability/badges/freshness-markers,
  and hooks surface file-level context maps automatically. Docs here *fail CI* when
  they rot — rare and valuable.
- **Clear truth layering** (source > binding > current-state > journal) resolved every
  conflict I hit — e.g. the journal's "latest migration 057" vs. disk's 062 had an
  unambiguous winner and a prescribed repair (correct in place, dated).
- **The badge taxonomy works.** 141 docs would be unnavigable flat; binding=14 /
  living-ledger=18 / reference=42 / plan=29 / audit=9 / ideas=7 + archive/historical
  means an agent can ignore ~60% of the tree for any given task.

**Weaknesses observed (with the structural cause, not just the symptom):**

1. **`current-state.md` accumulates faster than it reconciles.** Five sessions of
   "(this session)" markers piled up because a session ends (and writes docs) *before*
   its PR number exists. Fixed today, but the pattern will recur — see recommendation
   R3.
2. **`roadmap.md` horizons lag current-state by design but had drifted into outright
   contradiction** ("Later, fully gated" vs. three shipped, gate-lifted phases). The
   one-fact-one-home rule needs a sharper edge here: roadmap horizon *labels* are
   facts that live in two places (roadmap + current-state ▶ Next action).
3. **The doc-test net only covers registered surfaces** — an unregistered cog
   (spotlight) is invisible to every pin. The net catches drift in what exists *in*
   the system, not what bypassed it.

## 4. Plan executability assessment (the four active lanes)

Verified against the plans and source (paths spot-checked; ratings mine):

| Lane | Next step | Readiness | Blocking input |
|---|---|---|---|
| **Mining character platform** | Workshop + durability (§7.5); mother-panel live overview (§6.3) | **Turn-key** — decisions table locked (§6.1, 8/8), files real, recipe + test expectations present | none |
| **AI+BTD6 answerability** | Phase 3 (self-awareness tools) | **Turn-key minus one confirm** — Phase 2 read model shipped; needs the committed tool list + an explicit gate lift | tool list + gate lift |
| **AI tool orchestration** | Phase 4 (complex-BTD6 workflow) | **Mostly ready** — §7 describes ideals without naming the MVP slice (which answer contracts are Phase 4 vs. 4B) | Phase-4 MVP scope confirm |
| **Adaptive Setup/Access** | P1B remainder + P1C panels | **Needs one decision** — both remaining deliverables hang on audience simulation, now **Q-0045** | Q-0045 |

**Can I execute these while refining them? Yes — and this session is the evidence
offered:** plan statuses were reconciled while reviewing (three plans), a buried
blocking decision was promoted into the router where it can actually be answered
(Q-0045), a stale execution step (§15.3) was re-synced with shipped reality, and a
convention-violating merged feature was brought up to standard (code + tests + docs)
without waiting for permission — all under green CI. The honest caveats: AI-exposure
steps stay confirm-first (the repo's own gate), and two lanes need one-line owner
confirms before an executor should start them.

## 5. Recommendations (prioritized)

- **R1 — Answer Q-0045** (audience simulation). Highest leverage: one decision
  unblocks two queued deliverables. Safe default already documented.
- **R2 — Answer Q-0044 and, if registering, build Q-0025 first.** The
  `new_subsystem.py` scaffold is already decided backlog; Community Spotlight is its
  perfect first consumer (and the test that the scaffold covers all ~8 touch-points).
- **R3 — Kill the "(this session)" drift class structurally.** Options, cheapest
  first: (a) open the end-of-session PR as **draft before** the final docs commit so
  the number exists when current-state is written; (b) extend `check_docs.py`'s
  freshness gate to fail on `(this session)` / `Reconcile PR #` in
  `current-state.md`, forcing (a). Today's cleanup removed ten of these markers;
  without a forcing function they return. *(Gate change = executable config → ask
  first; hence a recommendation, not done.)*
- **R4 — Burn down the 87 known architecture warnings one slice at a time.** Two
  families dominate: `views → cogs._helpers` imports (economy/xp/moderation/mining/
  blackjack/deathmatch — the helper-policy fix is moving them to `services/` or
  `utils/`) and ~14 undocumented direct `discord.ui.View` subclasses (either adopt
  `BaseView` or add the required justifying comment). Each is a clean, bounded
  end-of-session secondary task.
- **R5 — Roadmap freshness hook.** When current-state's ▶ Next action changes a
  lane's horizon, touch `roadmap.md` in the same commit (add to the session END
  checklist — docs-only, no gate needed).
- **R6 — Spotlight follow-ups on next touch:** drop the no-op `ephemeral=True`,
  consider `before_loop`/`wait_until_ready` on the trim loop, and view-interaction
  tests for the panel buttons.

## 6. What this session changed (one PR)

Code: `utils/db/xp.py` (+`get_guild_xp_totals`), `utils/db/__init__.py` (re-export),
`cogs/community_spotlight_cog.py` (owner read + `member_count` fix), 2 new test files
(6 tests). Docs: `current-state.md` (reconciliation + restructure), `roadmap.md`
(3 sections), `ownership.md`, `repo-navigation-map.md`, `help-command-surface-map.md`
(§3 banner), `maintainer-question-router.md` (Q-0044, Q-0045), adaptive plan
(§15, §16.8), orchestration plan, answerability roadmap (×3), wire-exploration plan,
`.session-journal.md` (2 runbook facts), this audit, and the `.sessions/` log.
