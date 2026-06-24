# 2026-06-24 — Fix duplicate slash-command sync + /btd6ref round range

> **Status:** `complete` — two owner-reported slash-command issues from one Discord
> thread. PR #1409; auto-merge armed; merges on green.

> **Run type:** `manual · owner-directed`

> **⚑ Self-initiated:** none — both fixes are owner-reported.

The thread: owner couldn't find `/btd6ref income` → realized slash commands weren't
synced → synced them → then **every `/btd6ref` command showed twice**, and
separately noted `/btd6ref round` only takes a single round, not a range.

## Shipped (PR #1409)
1. **Duplicate slash commands (the pressing one).** Root cause: the operator synced
   commands **both globally and to the guild** (`!syncslash global` then
   `!syncslash` which does `copy_global_to` + guild sync) — Discord then renders each
   command twice in that guild, and there was **no way to clear the guild copies**.
   Fix: a new **`!syncslash clear`** scope (`clear_commands(guild)` + `sync(guild)`)
   drops the guild-local copies → each command shows once again from the global set.
   The guild-sync success message now warns about the dupe and points to `clear`, and
   the docstring documents "don't sync both global and guild for one environment."
   (`admin_cog.py`; 4 new tests.)
2. **`/btd6ref round` range.** Added an optional `end_round` (prefix + slash): a single
   round keeps the detail card; a range renders a combined per-round **values table**
   (round | RBE | cash | cumulative) + totals, via new `build_round_range_embed` off
   `round_rbe` + `round_cash`. Totals match the income/rbe commands and the AI floors
   (rounds 30-50 = 28,867 RBE / $30,364). Freeplay-scaled RBE flagged for 81+.
   (`_builders.py`, `btd6_reference_cog.py`; 5 new tests; artifacts regenerated for the
   changed `round` description.)

Note for the owner: `/btd6ref income` and `/btd6ref rbe` already took ranges (#1404) —
they just weren't synced/visible yet; after `!syncslash clear` (or a fresh single-scope
sync) they appear once each.

## 💡 Session idea (Q-0089)
**A startup self-sync of the app-command tree** (global, guarded by a stored tree-hash
so it only calls Discord when the command set actually changed). Right now new slash
commands are invisible until an operator manually runs `!syncslash` — which is exactly
how the owner hit both "income doesn't exist" and then the duplicate (he reached for the
guild-copy path). An idempotent on-`on_ready` global sync (hash-gated to respect the
rate limit) would make shipped commands appear without manual steps and remove the
copy_global_to footgun entirely. Dedup-checked: no existing auto-sync. (Not built —
flagged; it touches startup + Discord rate limits, so it wants its own scoped PR.)

## ⟲ Previous-session review (Q-0102)
Reviewed **2026-06-24-btd6-ai-floor-coverage-fixes** (#1408). Did well: deterministic,
verified against the proven 06/18 anchor. **What the whole #1404→#1408 arc missed:** I
kept shipping BTD6 command/grounding work and verifying it in *tests*, but never checked
the **operator path** — the slash commands I added in #1404 were never even visible to
users (unsynced), and when synced, duplicated. **System improvement:** "done" for a new
*slash* command includes naming the sync step (it won't appear without it) — the Q-0089
auto-sync would make that structural instead of a doc note. Same root theme as #1408's
"grounding ≠ answered": shipped-in-repo ≠ working-in-Discord.

## Backlog grooming (Q-0015)
Logged the auto-sync idea (above) as a new `docs/ideas` candidate-worthy item. Did not
promote an existing idea this session — the two owner bugs + the new idea filled the
capacity; the `round-range-comparison` item noted in #1408 remains the next decided-lane
pick.

## Doc audit (Q-0104)
`check_docs --strict` ✓, ledger ✓, full mirror green. The `!syncslash` behaviour change
is documented in its own docstring (the durable home for operator tooling). No new
runtime-formula fact; no owner-decision/router change. Ledger entry for #1409 lands via
the next reconciliation pass (Q-0052).
