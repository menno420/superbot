# Session — fix BUG-0014: `!coglist` infinite "assumed from" command-resolution loop

> **Status:** `complete`

## Origin

Owner uploaded a Discord screen recording (extracted frames via a pip-installed static ffmpeg, since
none was present): typing `!coglist` / `!cogs` made SuperBot spam **"↩️ Ran `!coglist` — assumed from
`!coglist`." forever — it does not stop until the bot is restarted.** A runaway message loop (spam +
rate-limit risk). Came in mid-session, right after the runtime-lock PR (#948) merged.

## Root cause (audited)

`utils/synonyms.py` declared `"coglist": ["listcogs", "cogslist"]`, but **no `coglist` command is
registered** — an AST audit of the whole table found it's the *only* orphaned canonical of 32. The
loop:

1. `!coglist` → `CommandNotFound`.
2. `on_command_error` → `command_resolution.classify("coglist")` fuzzy-matches the synonym `cogslist`
   → canonical `coglist` (lexically isolated, len≥4, not destructive) → `Outcome.AUTO`.
3. The handler rewrites the message to `!coglist` (**the same token**) and re-dispatches via
   `process_commands`.
4. `!coglist` is still unregistered → `CommandNotFound` → back to step 2. **Infinite loop.**

The structural amplifier: the handler re-dispatched an AUTO correction **without checking the target
exists or differs from the input**, so any phantom/identity correction loops forever.

## Fix (root-cause, three layers)

1. **Loop-breaker — `bot1.on_command_error`:** an AUTO correction is only re-dispatched when it is a
   *registered* command (`bot.get_command(...)`) **and** different from the raw token; otherwise it
   falls through to the normal not-found reply. Makes the loop class impossible regardless of synonym
   data (the durable, general fix at the dangerous seam).
2. **Data — `utils/synonyms.py`:** removed the orphaned `coglist` entry.
3. **CI invariant — `tests/unit/invariants/test_command_synonyms_resolve_to_real_commands.py`:**
   AST-scans every `@commands.command/group` name + alias across `disbot/` (338 tokens) and asserts
   every `COMMAND_SYNONYMS` canonical is a real command — so an orphan can't ship again. Verified it
   flags a re-added `coglist` (not vacuous).

## Verification

- `tests/unit/test_bot1_command_resolution_loop.py` (new, 3 tests): phantom and identity AUTO
  corrections do **not** re-dispatch (single terminal not-found reply, no "assumed from"); a valid
  correction (registered + different) still auto-runs exactly once + rewrites the message.
- The new synonym invariant + existing `test_command_resolution.py` pass.
- `python3.10 scripts/check_quality.py --full` → **green (9958 passed, 37 skipped)**.
- `python3.10 scripts/check_architecture.py --mode strict` → **exit 0**.
- Bug book: **BUG-0014** recorded FIXED.

**Merge ≠ deploy** — needs a Railway prod deploy to clear the loop in production.

## 💡 Session idea (Q-0089)

[`reference-integrity-invariants-2026-06-16.md`](../docs/ideas/reference-integrity-invariants-2026-06-16.md)
— BUG-0014 was a *dangling reference* that failed silently. Extract the AST command-surface discovery
from the new synonym guard into a shared test helper, and close the sibling gap that
`test_entrypoints.py` documents as unchecked: `SUBSYSTEMS.entry_points` → a real command. One "what
commands exist" source for every "this declaration must resolve" invariant. (Filed + indexed.)

## ⟲ Previous-session review (Q-0102)

Previous session: **the runtime-lock early-release fix (PR #948**, `2026-06-16-runtime-lock-early-release.md`).
- **Did well:** correctly treated the singleton-release-timing change as architectural and used
  `AskUserQuestion` to let the owner pick the approach (downtime-vs-overlap) rather than guessing —
  exactly the act-vs-ask line the collaboration model draws; and it shipped a *positive* AST invariant
  pinning the new behavior, not just a fix.
- **Through-line it reinforces:** both #948 and this BUG-0014 fix shipped a **CI guard that fails
  against the old behavior** in the same PR as the fix (#948's "driver releases lock before close"
  assertion; this session's synonym-orphan invariant). That norm is working and is the cheapest
  insurance against regressions.
- **Concrete workflow improvement:** make it an explicit bug-fix-checklist item — *"a live bug fix
  ships a CI guard that fails against the pre-fix behavior."* Both recent sessions did it ad hoc; the
  deathmatch session (two back) *deferred* its guard (still open). Worth codifying so it isn't
  optional. (No code change here — surfaced for the workflow.)

## Documentation audit (Q-0104)

- `check_docs.py --strict` → **green** (new idea file reachable + indexed). `check_architecture
  --mode strict` → exit 0.
- Bug book (BUG-0014), session log, active-work claim, and the idea file/index are all updated — no
  durable info left only in chat. The fix + rationale live in the handler comment + the bug book.
- Living-ledger drift (#944/#945, and now #948) remains the **next reconciliation's** job (not due
  till #960; Q-0124 — manual sessions don't run the reconciliation pass). This PR (#949) is
  intentionally not added to the ledger (unmerged).
- Backlog grooming (Q-0015): deliberately not bundled — focused, higher-risk runtime bug fix; mixing
  unrelated idea-execution would violate the small-focused-runtime-PR norm. The standing grooming
  pickup (the deathmatch timed-view invariant) remains named in #948's log.
