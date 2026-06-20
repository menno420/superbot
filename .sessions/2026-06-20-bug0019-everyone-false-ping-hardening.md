# Session — funny-franklin · BUG-0019 #2 false-personal-ping hardening

> **Status:** `complete`

**Run type:** routine · dispatch
**Branch:** `claude/funny-franklin-tfnzra` · **PR:** #1186

## What this PR does (CLASS: fix — bugs-first)
Shipped the **unambiguous half of the open AI-reply bug, BUG-0019**. The bug splits into two
mechanisms; the bug book flags **#2** as *"unambiguous → hardening"* and **#1** as a design fork
for the owner.

- **Root cause (#2):** the natural-language stage computed `is_mention` via
  `ctx.bot.user.mentioned_in(message)`. discord.py's `ClientUser.mentioned_in` short-circuits
  `True` on `message.mention_everyone`, so an `@everyone`/`@here` blast read as a **personal**
  mention and flipped the `mention_only` policy gate open — the bot replied to a message that
  never pinged it.
- **Fix:** `is_mention` is now `natural_language_stage._is_direct_bot_mention(message, bot_user)`
  — membership of the bot's own id in `message.mentions`. Only a literal `<@bot_id>` counts; an
  everyone/here blast does not. Defensive (missing id / non-iterable `mentions` → `False`).
- **Stays-fixed guard:** `tests/unit/runtime/ai/test_natural_language_stage.py` ::
  `test_everyone_blast_is_not_a_personal_ping` (+ direct-mention / other-user /
  direct-alongside-everyone / defensive cases). Two existing stage test fixtures that drove
  `is_mention` through the old `mentioned_in` double were updated to supply a real
  `message.mentions` list (also in `test_natural_language_stage_memory.py` +
  `test_btd6_central_policy_integration.py`).
- Recorded BUG-0019 **#2 → FIXED** in the bug book (entry stays OPEN for the #1 owner decision)
  and added a Recently-shipped ledger entry for #1186.

**Mechanism #1 (untouched):** `always_reply` ambient mode barges into others' conversations — a
design fork that changes ambient semantics the owner configured intentionally. Stays OPEN, routed
to the owner (agent recommendation: option (a) — stay silent when a message pings another
user/bot and not SuperBot; wants a Q-0086 runtime-verified session).

## Verification
- `python3.10 scripts/check_quality.py --full` → **All checks passed** (black/isort/ruff/check_docs/
  check_consistency 0-err/mypy/**11011 passed, 44 skipped**).
- `python3.10 scripts/check_architecture.py --mode strict` → clean (pre-existing WARN only).

## ⟲ Previous-session review (Q-0102)
The previous run (`funny-franklin-session-enders-claim-gap`) was a clean docs-only session-ender
pass — it correctly did the standing enders a minimal earlier card skipped, and surfaced a genuine
systemic gap (the claim ledger doesn't cover bug-book pickups → captured as an idea). What it
*could* have done better: with a clean tree, main healthy, and an **OPEN bug already in the bug
book carrying an explicitly-unambiguous, offline-testable sub-fix (BUG-0019 #2)**, the bugs-first
rule pointed at real code work it left on the table in favor of a docs-only pass. **System
improvement surfaced:** an empty-fire dispatch should grep the bug book for `PARTIALLY`/`OPEN`
entries whose *proposed fix* is self-labelled "unambiguous"/"hardening" before concluding "no
ungated code lane" — that signal (a bug author pre-clearing a sub-fix) is a high-value, low-risk
startable the current ▶ Next-action prose doesn't index. Candidate: have
`check_bug_book_rootfix_backlog.py` also surface OPEN entries with an unambiguous sub-fix, not just
deferred-root ones.

## 💡 Session idea (Q-0089)
**`bug-book-unambiguous-subfix-signal`** — when a bug entry is OPEN/PARTIALLY-FIXED because *part*
of it needs an owner decision but another mechanism is self-described as "unambiguous → hardening"
(exactly BUG-0019 #2), that ship-ready sub-fix is invisible to the empty-fire dispatch heuristics,
which read "OPEN bug → needs owner" and move on. Idea: extend
`scripts/check_bug_book_rootfix_backlog.py` (or a sibling) to flag entries whose proposed-fix text
contains an "unambiguous"/"hardening"/"offline-unit-testable" sub-fix marker, so the next empty
dispatch finds it as a startable. Genuine — this run *was* that missed startable. (Not built this
run; would itself be a small stdlib guard a later run can promote.)

## 💡 Doc audit (Q-0104)
Bug book updated (BUG-0019 #2 FIXED, header → PARTIALLY FIXED, status fork preserved). Recently-shipped
ledger entry added for #1186. No new owner decisions (mechanism #1 was already routed to the owner in
the prior run's entry). `check_docs --strict` green in the full mirror.

## 📤 Run report
- **Run type:** routine · dispatch
- **PRs:** #1186 (BUG-0019 #2 hardening) — self-mergeable, auto-merge armed by the enabler workflow.
- ⚑ **Owner-decisions:** none (mechanism #1 remains routed to the owner from the prior entry — no new
  decision raised this run).
- ⚑ **Owner-manual-steps:** none (a merge auto-deploys; no data file changed, no `!btd6ops seed-data`).
- ⚑ **Self-initiated:** none (BUG-0019 is an owner-reported bug in the bug book — bugs-first, not an
  invented feature).

## Handoff — ▶ next
This run took the bugs-first lane (BUG-0019 #2). The ungated self-merge backlog beyond it stays thin
(per the band-#1170 pass): next startables are the remaining `public-data-contract-field-snapshot`
small guard, or a substantial `needs-hermes-review` lane (consistency-linter AI-nav PR 1 /
procedures→skills Batch 2). **BUG-0019 #1** is the one live owner-gated follow-up: the `always_reply`
barge-in design fork — needs the owner's option (a)/(b)/(c) call + a Q-0086 runtime-verified session.
