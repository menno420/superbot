# Maintainer Question Router — archive

> **Status:** `archive` — overflow from
> [`maintainer-question-router.md`](./maintainer-question-router.md) § Q-blocks.
> Old, fully **answered + routed** `Q-0NNN` blocks are moved here (oldest first) by the
> reconciliation pass (Q-0107) to keep the live router lean, **without ever renumbering or
> re-homing a decision's canonical record** (convention Q-0210).
>
> **Source code, merged PRs, and binding docs win over anything here.** Start at the live router.

## How this file works (Q-0210)

- The live router stays the **single canonical, append-only Q-block ledger**. A decision keeps
  its `Q-0NNN` block forever; numbers are **never moved or reused**.
- References across the repo are plain `Q-0XXX` **text** (only one `#q-0017` *anchor* link exists
  repo-wide), so a block archived here stays fully **grep-resolvable** — moving it changes nothing
  for the ~9,000 references that cite it by number.
- **Archiving is a reconciliation-pass job** (the same pass that trims `current-state.md` →
  `current-state-archive.md`), not an ad-hoc edit. Move the **oldest answered + routed** blocks,
  newest stay live, and leave the live router's pointer intact.

## Archived Q-blocks

> _Empty._ No blocks have been archived yet — the live router is still within a comfortable size.
> The first move happens in a future reconciliation pass when the live file grows unwieldy; archived
> blocks land below this line, newest-first within each move.
