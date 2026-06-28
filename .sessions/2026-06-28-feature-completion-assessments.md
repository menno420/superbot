# 2026-06-28 — Feature-completion unit assessments + counting leaderboard

> **Status:** `complete`

**Run type:** routine · dispatch

## What I did

Empty-fire dispatch (no work order). The completion-first certification framework had just shipped
(#1513, owner decision Q-0209) with **only Blackjack assessed (1/36)**. I deepened that just-started
arc: assessed three more game units and, in the same PR, closed a contained punch-list gap one of the
assessments surfaced.

**Assessed (▢ → ◐), one certificate each under `docs/planning/feature-completion/units/`:**
- **Fishing** (`fishing.md`) — feature-rich (full cast→bite→reel→trophy-fight loop, two venues, daily
  weather, 4 craft paths, leaderboards, dex, all on an audited seam with strong tests). **Headline
  gap: trapped Rod/Bait shop views** — the menu `self.stop()`s when it opens them and the shops
  (`BaseView`) have no back-nav, so a player who opens Rod/Bait is stranded (rubric B "no trapped
  views"). Recorded as punch-list #1.
- **Counting** (`counting.md`) — deep 11-mode game, DB-persisted/restart-safe, scope-locked,
  BUG-0012-hardened. **Headline gap: the per-channel leaderboard was tracked but never displayed**
  (dead state) → **fixed this run** (below). Remaining: XP/coin reward decision, admin-only discovery.
- **Word Chain** (`chain.md`) — **mis-classified**: the registry advertises it as a "Word-chaining
  game" (`category: games`, caps `chain.game.*`) but the code is a **channel word-restriction
  moderation tool** with no game loop. Cannot be certified against the game rubric — needs an owner
  re-classify decision (the cert's blocking punch-list item).

Ledger flipped to `assessed` (1 → **4 of 36**, 11%); scoreboard regenerated.

**Closed a punch-list item in the same PR (the assess → close loop the framework exists for):**
- **Counting #2 — surfaced the leaderboard.** The tally `handler.py` increments on every accepted
  count was never shown. Added `game_logic.top_counters` (pure ranking), `cogs/counting/leaderboard.py`
  (embeds — kept the cog under the 800-LOC threshold via the `_channel_manager` delegation pattern),
  a `!counttop`/`!ct` command, and a "Top counters" field on `!count_info`, with
  `tests/unit/cogs/test_counting_leaderboard.py`.

CI mirror green end-to-end (`check_quality.py --full`: **12946 passed**, 48 skipped; black/isort/ruff/
mypy clean) · `check_architecture --mode strict` **0 errors** · `check_consistency --mode strict`
clean · `check_docs --strict` clean · dashboard artifacts regenerated (new command, 459 total).
Born-red gate held the merge until this card flipped `complete`.

## 💡 Session idea (Q-0089)

**A registry↔completion-ledger parity guard.** The framework README itself flags this as a noted
follow-up ("A registry↔ledger parity guard is a noted follow-up"), and this run made it concrete: the
**Word Chain mis-classification** (registry says "game", it's a moderation tool) is exactly the drift a
parity guard would have caught mechanically. Idea: a `scripts/check_completion_ledger.py` that asserts
(a) every certified-eligible `subsystem_registry` unit appears in the ledger table (no unit silently
un-tracked), (b) every ledger row maps to a real registry key, and (c) — the new, higher-value part —
each `units/<key>.md` cert's declared **Type** (game vs server-fn) matches the registry's
`category`/`parent_hub`, so a "this is registered as a game but assessed as a moderation tool" finding
becomes a CI signal, not a thing a human has to notice. Pure stdlib, read-only, disposable (Q-0105).
Will file to `docs/ideas/` if not already captured.

## ⟲ Previous-session review (Q-0102)

Reviewing `2026-06-27-feature-completion-framework` (#1513, the framework this run built on): **did
well** — it nailed the orthogonal-axes framing (completion *ceiling* vs readiness *floor*), grounded
"complete" in concrete rubrics rather than vibes, and crucially **chose a near-complete unit
(Blackjack) as the pilot** so the rubric was exercised against real strength *and* still produced a
5-item punch-list — proving the tool finds gaps even in good code. **Could improve / system note:** it
left the ledger at 1/36 with no startable "assess next" handoff beyond the general posture, so this
run had to re-derive which units to assess and in what order. The framework would benefit from a
**suggested assessment order** (or the parity-guard idea above auto-listing `▢ unassessed` units by
family) so each completion-first run has a turn-key next pick rather than choosing from 35 blanks —
the same "give the next session a turn-key recipe" discipline the planning docs use.

## 📤 Run report

- **Did:** assessed 3 game units (Fishing/Counting/Word Chain) against the completion rubric + closed
  Counting's dead-state-leaderboard gap in the same PR · **Outcome:** shipped
- **Shipped:** PR #1519 — 3 completion certificates (ledger 1→4 assessed) + `!counttop`/`count_info`
  leaderboard (`cogs/counting/leaderboard.py` + `game_logic.top_counters` + tests)
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** **Word Chain re-classify** (is it a game, or a mis-typed
  channel-restriction moderation tool? — see `chain.md` punch-list #1) · **Counting reward** (should
  correct counts grant game_xp/coins, or stay reward-free? — `counting.md` #1). Plus every assessed
  unit's eventual `◐ → ✔` sign-off needs an owner live walkthrough.
- **⚑ Owner manual steps:** none (no migration; the new command applies on the next auto-deploy)
- **⚑ Self-initiated:** the whole run — promoted the completion-first arc (Q-0209) by assessing more
  units + closing Counting #2, with no dispatch/owner ask (Q-0172). *Deepening* an already-started
  system, inside the completion-first soft default.
- **↪ Next:** S1 ▶ Next (sharpened): assess the remaining unassessed units (Mining [big] · Casino ·
  Deathmatch · RPS · Creatures · Farm, then server-fns); close the offline punch-list gaps —
  **Fishing #1** (trapped Rod/Bait shop nav) and **Counting #3** (player entry point). Owner-gated:
  the re-classify/reward decisions above + per-unit certification walkthroughs.

## Doc audit (Q-0104)

`check_current_state_ledger --strict` green (15 newer merges = benign post-#1500-marker lag, recorded
by the reconciliation routine — Q-0124/Q-0166) · `check_docs --strict` green · `completion_scoreboard`
regenerated and tested. De-staled: the games folio (`subsystems/games.md` — now lists the 3 newly
assessed units, not just the Blackjack pilot), the S1 sector ▶ Next (added the completion-first
continuation bullet), and the Counting cert (marked #2 fixed). No new owner *decision* was made this
run (two are *raised* for the owner, above) → router untouched; the decisions live in the cert
punch-lists where the owner will act on them.
