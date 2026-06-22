# 2026-06-22 — Remove the disproven "synchronize doesn't re-fire CI" claim

> **Status:** `complete` — owner-directed. The owner flagged that the journal's "a born-red PR
> doesn't re-trigger CI on a later push" claim is false (the real cause was a CI-stopping bug,
> since fixed) and directed: **completely remove** wrong/fixed claims from the repo — not annotate
> them "was wrong, now fixed" — so a future session never reads about a problem that no longer
> exists and wastes time on it. Owner-directed (Q-0191) → merge on green.

> **Run type:** `manual · owner-directed`

## What I did

1. **Empirically disproved the claim.** Opened a genuinely born-red PR (#1277, throwaway), then
   pushed a **second commit** to the existing branch and watched the Actions runs:
   - 1st push (PR open, `b7deadd`) → Code Quality run **#3092** (`pull_request`)
   - 2nd push (synchronize, `eadfcaf`) → Code Quality run **#3093** (`pull_request`) — **fired**

   `total_count: 2` — a push to the existing PR branch **does** re-fire Code Quality on the new
   head SHA. (Both runs "failure" = the deliberate born-red session gate; the point is the run
   *triggered*.) Closed #1277 with the result recorded.

2. **Confirmed the real root cause is already fixed.** `code-quality.yml` had
   `concurrency.cancel-in-progress: true` (added #1195, 2026-06-20), which **raced and dropped the
   head-commit run** under the born-red event burst — the actual "CI didn't run on my latest
   commit" strand. Fixed to `false` in **#1267/#1275** (2026-06-22). The "synchronize doesn't fire"
   belief was a misdiagnosis of that race.

3. **Deleted the false claim everywhere it lived** (it was confined to the journal + `.sessions/`;
   `docs/` and `.claude/CLAUDE.md` never carried it, so no propose-first edit was needed — and the
   CLAUDE.md born-red bullet is *correct*: flip-the-card-on-a-later-push works):
   - `.session-journal.md` ⚡ Quick reference — **removed** the *"PR stuck `blocked`, no
     Code-Quality check on the head?"* row (the synchronize-doesn't-fire gotcha + close/reopen
     recovery + "push all commits before opening" workaround) **and** the *"GitHub says a PR is
     `dirty`"* row (a downstream symptom of the same strand, built on the false push-gotcha).
   - **Deleted** `.sessions/2026-06-20-ci-trigger-gotcha-journal.md` — its entire purpose was to
     document the false gotcha.
   - **Trimmed** the two incidental cross-references that restated it
     (`.sessions/2026-06-21-journal-workflow-lessons.md` status line,
     `.sessions/2026-06-21-reaction-roles-pr3-5.md` Context-delta bullet).

## What I deliberately kept

- `.sessions/2026-06-22-ci-strand-cancel-in-progress.md` and the `code-quality.yml` concurrency
  comment — these are the **true, current** record of *why* `cancel-in-progress` is `false`. That's
  forward-looking rationale that stops someone re-introducing the bug to "save minutes," not false
  error-history. Keeping it is the opposite of the confusion the owner is removing.

## Findings / decisions

- **Verify before documenting a root cause.** The false claim came from inferring "synchronize
  doesn't fire" from a *symptom* (no run on the head) without isolating the cause; the cancellation
  race produced the identical symptom. A 4-commit live experiment settles it in minutes — the same
  Q-0120 instinct ("a verdict that fights the evidence is the bug, not the evidence") applied to a
  process claim.
- **Decision made alone — kept the true fix-record, deleted only the false claim.** The owner's
  "remove fixed claims" directive targets confusing error-history in *active reading paths*; a
  config's live rationale is a current fact, not error-history.

## 💡 Session idea

**A "claim epitaph" convention for the journal Quick reference: when a gotcha's root cause is
fixed, DELETE the row in the fixing PR — don't leave a "was X, now fixed" note.** This session
existed because a fixed problem's description outlived the problem. A one-line rule in the journal's
own header ("a Quick-reference row documents a *live* gotcha; when its cause is fixed, remove the
row in the same PR as the fix") would make this self-correcting — the fixer owns the cleanup, so the
guidebook only ever describes problems that still exist. (Complements the existing "correct stale
entries in place" rule, which currently invites annotation rather than deletion.)

## ⟲ Previous-session review (Q-0102)

The immediately-previous work this session (my own #1276 repo-navigation cleanup) correctly
*declined* to churn historical records — but it under-reached on one thing: it accepted the journal's
synchronize-gotcha as still-true env behavior ("likely still true," in its reasoning) instead of
**testing** it. The owner had to push back and ask for the experiment. **Lesson + system
improvement (initiated):** a claim that shapes the whole born-red/merge flow is worth a 4-commit
live probe before being treated as load-bearing — and the `💡` epitaph convention above turns
"someday a session notices the stale gotcha" into "the fixing PR deletes it," closing the gap at the
source rather than relying on a later cleanup pass.

## 📤 Run report

- **Did:** disproved + deleted the "synchronize doesn't re-fire CI" claim and its strand workaround
  across the journal + `.sessions/` · **Outcome:** shipped (this PR, auto-merge on green)
- **Run type:** `manual · owner-directed`
- **⚑ Owner decisions needed:** none.
- **⚑ Owner manual steps:** none — docs-only; merged = deployed (no runtime change). The actual CI
  fix already shipped (#1267/#1275).
- **⚑ Self-initiated:** no — owner-directed (verify the claim, then completely remove it).
- **↪ Next:** ungated build lanes (current-state ▶) untouched.

## ⟳ Doc audit (Q-0104)

`check_docs --strict` + `check_current_state_ledger --strict` green. No merged-PR ledger entries to
add (docs-only). No new owner decisions for the router (the directive was an in-session cleanup, not
a new product decision). Verified `grep` over `.session-journal.md` and `docs/` finds no remaining
"synchronize doesn't fire" / "born-red can strand" residue.
