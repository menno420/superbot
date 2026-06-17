# Idea — soft-lint the unbounded "running tally" drift class

> **Status:** `ideas` — capture only, not approved. Routing: **S3 (workflow mechanism) / tooling lane.**
> Captured 2026-06-17 by the band-#1020 Q-0107 reconciliation pass (the Q-0089 session-ender idea).

## The observation that prompted it

The `docs/current-state.md` "Older merges → archive" pointer line had silently accreted a ~2,000-word
parenthetical: every reconciliation/trim session *appended* a sentence saying what it added and what
it archived ("the #X session added its entry and archived the oldest live one — #Y — to hold the
ratchet at 20…"). The band-#1020 pass pruned it, because it was **pure redundancy** — the archive file
(`current-state-archive.md`) is itself the authoritative record of what's archived, so a hand-maintained
running tally of the same fact is a chore *and* a drift surface, never a source of truth.

This is a recurring **class**, not a one-off: a doc grows an unbounded list of per-session "what I did"
notes that duplicates an authoritative record elsewhere. The same shape nearly recurred in the
`Last updated:` stamp wall (already moved to the archive, 2026-06-12) and could recur on any
"newest-first, append a line each time" ledger pointer.

## The idea

A tiny, **disposable** (Q-0105) soft check in `scripts/check_docs.py` (advisory, never CI-hard) that
flags when a *pointer/bookkeeping* line in `current-state.md` exceeds a word budget — specifically the
"Older merges … → archive" line and the `▶ Next action` callout. When a single bullet/blockquote line
crosses, say, ~150 words, emit: *"this line is accreting a running tally — the authoritative record is
probably elsewhere (the archive / the linked pass doc); prune it to a pointer."*

- **Why soft:** the right length is a judgment call; a hard gate would force churn. A nudge in the
  `/session-close` automated half is enough — it makes the next reconciliation pass *notice* the
  accretion instead of adding to it.
- **Why disposable:** if it proves noisy or never fires usefully across a few passes, delete it
  (the standing kill-switch convention). It is a convenience guard, not load-bearing.

## The reusable principle (the real value)

**Don't hand-maintain a running tally of a fact that already has an authoritative record.** Point at
the record instead. This belongs in the reconciliation routine's instincts: when you find yourself
*appending* to a per-session list, ask whether the list duplicates something the system already tracks
— and if so, replace it with a pointer rather than extending it. The lint is just the automated
reminder of the principle.

## Disposition

S3/tooling lane. Small/safe — implement the soft check next time a docs-tooling slice is in flight, or
fold the word-budget check into the existing `check_docs` census output. The principle is usable
immediately regardless of the tool.
