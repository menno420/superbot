# 2026-06-29 — Session-slug-uniqueness guard (close BUG-0027's residual clobber risk) + Mining how-to button

> **Status:** `complete`
<!-- born-red flow (Q-0133): in-progress while open; flip to complete as the final close step. -->

**Run type:** routine · dispatch
**PR:** [#1548](https://github.com/menno420/superbot/pull/1548)
**Branch:** `claude/funny-franklin-dt7i3j`

## What this run did
Empty-fire dispatch advancing the S3/S4 self-improving-workflow lane + the S1 completion-first arc.
Two contained, offline, self-mergeable slices.

### 1. `check_session_slug_unique.py` — close BUG-0027's residual silent-clobber harm
The previous run's own routed Q-0089 idea (#1524 session log). BUG-0027 (#1524) fixed the born-red
merge-gate so a slug-collision card can't *auto-merge* a partial PR — but the **silent clobber** (a
new session reusing an existing `.sessions/` slug *overwrites* the prior session's log) still happened
*before* the gate engaged, and CI is too late to stop it (the prior log is already overwritten in the
commit). This adds the author-time guard: a `[session-close-gate]` checker that fails when a touched
session card path **already exists in `origin/main`** and the card is an active (non-re-badge) session
card, with a rename hint.
- Reuses `check_session_gate`'s `gate_session_cards` / `parse_status` / `_TERMINAL_OK_STATUSES` as the
  single source of truth for session-card status semantics (the two guards can't drift). A
  reconciliation re-badge of an *old* log to a terminal status (`historical`/`archived`/…) is exempt.
- Wired into `/session-close` Step 4; the `check_session_close_gate.py` meta-check now confirms 8
  sentinel-bearing checkers are all wired (was 7).
- **Ground-truth verified (Q-0120):** `_exists_in_main` returns True for a real in-`main` card and
  False for this run's unique slug — not just the mocked unit tests. +14 tests.

### 2. Mining how-to button — completion-cert punch-list #1 (Q-0209)
The Mining cert's last *build* gap (the most feature-complete game; only the owner live walk + sign-off
remained). Added a dedicated **📖 How-to** button at the hub (`mining:how_to`) opening a one-screen
"how mining works" onboarding panel (`views/mining/how_to_panel.py::MiningHowToView`), returning via
the established "↩ Mining Hub" back button — so it is not a dead-end terminal (the #1529 `no_dead_end`
guard is satisfied; verified clean). The cert's six-actions pin was updated to seven (a sanctioned
help/onboarding control, not game-action re-bloat). +3 tests; cert punch-list #1 marked DONE.

Also: deleted the stale claim `funny-franklin-ca1e1q.md` left behind by the already-merged #1524
session (docs drift, fix-on-sight Q-0166).

## Verification
- `check_quality.py --full` GREEN (13031 passed, 48 skipped, 2 xfailed). `check_architecture --mode
  strict` 0 errors (pre-existing `[known]` warnings only; no_dead_end clean). `check_docs --strict` ✓,
  `check_session_close_gate` ✓, ledger exit 0 (16-PR benign newest-merge lag = recon routine's lane,
  Q-0124). Formatters/ruff reconciled green.

## 💡 Session idea (Q-0089)
**Idea:** a `--list-orphan-claims` mode on `check_lane_overlap.py` (or a tiny `check_stale_claims.py`)
that flags `docs/owner/claims/*.md` whose branch has **no open PR** (its session already merged/closed)
— the exact stale-claim class I cleaned up by hand this run (`funny-franklin-ca1e1q.md`).
**Why:** claims are supposed to be deleted at session close, but a routine that ends abnormally (or
forgets) leaves an orphan that misleads the next run's overlap scan into thinking a lane is active.
Cheap (stdlib + one `list_pull_requests` or a `git branch -r` check), "enforce don't exhort", and
directly tied to drift I saw. Routed as an idea (a claims-GC automation already exists per Q-0206 — this
would extend/verify it rather than duplicate), not a unilateral add.

## ⟲ Previous-session review (Q-0102)
The previous dispatch run (2026-06-28 RPS/Deathmatch/Chicken-farm assessments + the BUG-0027 gate fix)
did genuinely strong work — it caught its *own* born-red gate failing open mid-run and root-fixed it,
which is exactly the self-auditing the loop is meant to do. **What it left for this run (correctly, as
a routed idea):** the residual *clobber* half of BUG-0027 — its own session log explicitly flagged that
the gate fix neutralized the premature-merge but the silent-overwrite still happens before the gate
engages, and routed the unique-slug guard as a Q-0089 idea rather than building it. That hand-off worked
perfectly: this run picked up the routed idea and shipped it. **System improvement surfaced:** the
chain *did* work, but only because the idea was written down — there's no machine link from "a routed
Q-0089 idea tied to an OPEN/partial bug" to "a later dispatch run sees it as startable." The bug-book
already has `check_bug_book_rootfix_backlog.py` for deferred *root-fixes*; a parallel surfacing for
**routed-idea-closes-a-known-gap** would make these hand-offs not depend on the next agent re-reading
the prior log. (Captured loosely; not built — would want owner framing on where it lives.)

## Doc audit (Q-0104)
Durable homes updated: mining cert punch-list #1 → DONE + the rubric "how-to affordance" row flipped to
✅ (`feature-completion/units/mining.md`); `/session-close` Step 4 gained the new checker; stale claim
deleted. No new owner *decision* (both slices are a fix + a sanctioned cert punch-list item; the
six→seven hub-button change is justified inline by the Q-0209 cert). `current-state` Recently-shipped
left to the next session/recon (PR #1548 not yet merged — benign lag convention). Claim file deleted at
close.

## 📤 Run report
- **Did:** built `check_session_slug_unique.py` (close BUG-0027 residual clobber, the prior run's Q-0089
  idea) + wired it into `/session-close`; added the Mining 📖 How-to button (cert punch-list #1);
  cleaned a stale claim. · **Outcome:** shipped (PR #1548), auto-merge armed.
- **Shipped:** PR #1548 — `scripts/check_session_slug_unique.py` (+14 tests) + SKILL.md Step-4 wiring;
  `disbot/views/mining/how_to_panel.py` + hub button (+3 tests, cert updated); deleted stale claim
  `funny-franklin-ca1e1q.md`.
- **Run type:** routine · dispatch
- **⚑ Owner decisions needed:** none new.
- **⚑ Owner manual steps:** none. (Mining how-to is live on the next auto-deploy; no data step.)
- **⚑ Self-initiated:** yes — both slices were self-initiated on an empty fire. Slice 1 is the prior
  run's routed Q-0089 idea (closing BUG-0027's residual harm — bugs-first); slice 2 is the dispatched
  completion-first ▶ Next (cert punch-list). No brand-new feature invented; no plan promotion needed.
- **↪ Next:** continue the completion-first arc — the remaining offline cert punch-list pick is
  **Blackjack split/insurance/surrender** (bigger engine work, owner-paced) or another assessed unit's
  offline deepening (Inventory item-grant audit · Proof-channel lock/unlock audit). The `◐ → ✔`
  certifications themselves are `[owner]`/`[needs-live-bot]` (live walkthroughs). Bug-book:
  BUG-0009/0011/0019#1 stay OPEN. Consider the orphan-claim guard above if claim drift recurs.
