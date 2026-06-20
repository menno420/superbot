# Session — funny-franklin · BUG-0019 #2 false-personal-ping hardening

> **Status:** `in-progress`

**Run type:** routine · dispatch
**Branch:** `claude/funny-franklin-tfnzra`

## What I'm about to do
Ship the **unambiguous half of BUG-0019** (the open AI-reply bug). The bug entry splits into
two mechanisms: **#1** (`always_reply` ambient mode barges into others' conversations) is a
design fork **routed to the owner** — not touched. **#2** is flagged in the bug book as
*"unambiguous → hardening"*: `ClientUser.mentioned_in(message)` returns `True` on an
`@everyone`/`@here` blast (`message.mention_everyone`), so a server-wide ping reads as a
**personal** mention and flips the `mention_only` policy gate open. Fix: compute `is_mention`
as a **direct** mention only — the bot's own id present in `message.mentions`, excluding
`mention_everyone`.

- Replace the `mentioned_in` call in `natural_language_stage.py` with a `_is_direct_bot_mention`
  helper (membership in `message.mentions`).
- Ship the stays-fixed guard: a `natural_language_stage` unit test where `@everyone`
  (`mention_everyone=True`) does **not** set `is_mention`, and a direct `<@bot>` still does.
- Record BUG-0019 #2 as FIXED in the bug book (entry stays OPEN for the #1 owner decision).

CLASS: fix — bugs-first, contained/reversible/test-covered → self-merge on green.
