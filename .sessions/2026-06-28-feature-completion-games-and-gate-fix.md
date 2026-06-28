# 2026-06-28 — Feature-completion assessments (RPS · Deathmatch · Chicken farm) + born-red gate collision fix

> **Status:** `complete`

**Run type:** routine · dispatch

## What this run did
Empty-fire dispatch advancing the completion-first arc (Q-0209). **Mid-run it surfaced and root-fixed
a real workflow-integrity bug** (born-red gate failed open → a partial PR auto-merged + clobbered a
prior session log), then delivered the planned game assessments.

**PR #1524 — two deliverables in one PR (bugs-first + the plan slice).**

### 1. BUG-0027 — born-red merge-gate silently failed open on a session-card slug collision (root fix)
- **What happened:** my *first* attempt this run (PR #1523) opened a born-red card and **auto-merged
  immediately while still `in-progress`**. Root cause: the card filename
  `.sessions/2026-06-28-feature-completion-assessments.md` **already existed in main** (a prior same-day
  dispatch run used the same slug). So `git add -A` recorded a **modification** (`M`), not an addition
  (`A`); `check_session_gate.py` scanned `--diff-filter=A` only, saw "no new card", failed open. The
  collision also **clobbered** the prior session's complete log in main.
- **Fix (root):** the merge gate now scans **added *or* modified** cards (`--diff-filter=AM`,
  `gate_session_cards`); carves out re-badged old logs (`historical`/`archived` via
  `_TERMINAL_OK_STATUSES`) so reconciliation PRs are never wrongly held; prints a **rename hint** when a
  held card was modified-not-added. Codex `--require-ready-card` keeps added-only semantics. Restored
  the clobbered prior log from git history (`a182ac30`); this card uses a unique slug.
- **Guard:** `test_main_modified_card_collision_held_with_hint` reproduces #1523 (held + hint) +
  `test_main_reconciliation_rebadge_not_held` (carve-out). Both fail against the pre-fix gate. Verified
  against the real #1523 SHAs (`MERGE HELD`, rc=1). **This very PR dogfooded the fix** — CI held #1524
  red while the card was `in-progress` (the intended behavior the original gate lacked).

### 2. Feature-completion assessments — RPS, Deathmatch, Chicken farm (`▢ → ◐`, now 7/36)
Three game certs against the game rubric (parallel Explore-agent source maps, verified against source):
- **RPS** ([cert](../planning/feature-completion/units/rps_tournament.md)) — mode-rich + money-safe;
  **fixed offline:** `!rpshelp` listed underscored command names that don't exist + a non-existent
  `!rps_leaderboard` → rewritten to the real names. Punch-list: PvP-play back affordance, rules-copy,
  edge tests, owner PvP-rematch call.
- **Deathmatch** ([cert](../planning/feature-completion/units/deathmatch.md)) — **headline gap: PvP
  `_DuelView`/`_ChallengeView` are trapped dead-ends** (plain `discord.ui.View`, no back nav after
  terminal) while the bot-duel path does it right. Turn-key fix flagged in S1 ▶ Next.
- **Chicken farm** ([cert](../planning/feature-completion/units/farm.md)) — structurally complete +
  money-safe; punch-list is hardening (defer-on-DB, double-settle window, workflow/view tests).

## Verification
- `check_quality.py --full` GREEN (12957 passed, 48 skipped). `check_architecture --mode strict` 0 new
  (pre-existing tracked warnings only). 18 gate tests pass. `check_docs --strict` ✓. Ledger lag is
  benign newest-merge lag (recon routine's lane at #1500, Q-0124).

## 💡 Session idea (Q-0089)
**A `check_session_slug_unique.py` checker** (or a `/session-close` step) that fails when a PR's new
`.sessions/` card path *already exists in `origin/main`* — catching a slug collision at author time, so
it never reaches the clobber+merge stage at all. BUG-0027's gate fix neutralizes the *premature-merge*
harm, but the *clobber* (overwriting the prior log) still happens silently before the gate engages; a
unique-slug guard closes the collision at the root. Genuinely tied to this run's bug, cheap (stdlib,
one `git cat-file -e origin/main:<path>`), and "enforce don't exhort". Routed as an idea, not a
unilateral checker add (a CI-wired guard is judgment-call; the gate fix already ships the enforcement
half).

## ⟲ Previous-session review (Q-0102)
The previous dispatch run (2026-06-28 Blackjack/Counting feature-completion assessments) did genuinely
good work — it established the assessment format and shipped real punch-list fixes (#1521). **What it
missed, and this run paid for:** it chose a *generic* session slug (`feature-completion-assessments`)
for a recurring task type, which is exactly the collision trap that defeated the born-red gate here. It
also (like every prior run) never noticed the gate's added-only blind spot — understandable, since the
hole only manifests on a collision. **System improvement surfaced:** the Q-0089 unique-slug guard above
— and the broader lesson that *recurring task types need disambiguated slugs* (the collision is a
structural consequence of date+topic slugs for a task that fires repeatedly). The gate fix makes the
failure loud instead of silent; the slug guard would make it not happen.

## Doc audit (Q-0104)
Durable homes updated: BUG-0027 → bug-book; three certs → `feature-completion/units/` + the ledger
table + regenerated scoreboard (7 assessed); S1 ▶ Next sharpened (7/36, the Deathmatch turn-key
follow-up, RPS fix noted). No new owner *decision* (BUG-0027 is a fix, not a decision; three owner
*calls* are raised in the cert punch-lists). `current-state` Recently-shipped untouched (PR #1524 not
yet merged — next session/recon records it). Claim file deleted at close.

## 📤 Run report
- **Did:** root-fixed BUG-0027 (born-red gate slug-collision hole) + restored a clobbered session log +
  assessed RPS/Deathmatch/Chicken farm (◐) + fixed RPS help-text drift. · **Outcome:** shipped (PR #1524)
- **Shipped:** PR #1524 — `check_session_gate.py` AM-scan + terminal-OK carve-out + collision hint
  (+18 tests); bug-book BUG-0027; restored `…feature-completion-assessments.md`; certs
  `rps_tournament.md`/`deathmatch.md`/`farm.md` + ledger + scoreboard; RPS `!rpshelp` fix.
- **Run type:** routine · dispatch
- **⚑ Owner decisions needed:** none new. (Three owner *calls* raised in cert punch-lists for later
  certification: Word Chain re-classify, Counting/Deathmatch reward/coin-staking, and each assessed
  unit's `◐ → ✔` live-walkthrough sign-off.)
- **⚑ Owner manual steps:** none.
- **⚑ Self-initiated:** yes — the BUG-0027 gate fix + log restoration were self-initiated (a bug the run
  surfaced from its own behavior, fixed root-cause per bugs-first); the three assessments + RPS fix are
  the dispatched plan slice (completion-first ▶ Next). No new feature invented.
- **↪ Next:** continue the completion-first arc — assess Mining (big read) / Casino / Creatures, **or**
  take the turn-key **Deathmatch PvP trapped-view fix** (mirror the bot-duel `HubView` result view +
  🔁 Rematch). Bug-book: BUG-0027 FIXED; BUG-0009/0011/0019#1 stay OPEN. Consider the Q-0089 unique-slug
  guard so this collision class can't recur.
