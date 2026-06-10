# 2026-06-10 — Mapping-PR reconciliation + Q-0070 preset-posture capture

Continuation of the 2026-06-09 standards session (PR #641, merged). Two work
items today; the second ships as its own small docs PR.

## 1. Reconciled the two Codex mapping PRs (#643 / #644) — pushed to their branches

Both agents started **before #641 merged**: the standard was absent from their
checkouts, so each imported a copy from PR #641's then-head — a
**pre-reconciliation snapshot** (stale "#639 open/provisional" framing). Both
PRs were add/add-conflicted with main on that one file. Fixed on each branch
(owner asked): merged `main`, resolved the standard to the merged version +
that agent's own §5.5 output link, appended an identical **§7.1 reconciliation
note for the merge session** (post-`560e351` deltas: #640/#642; owner-question
routing owed; verification debt). Verified: both PRs `mergeable_state: clean`,
sequential A→B merge simulated clean, `check_docs --strict` green on every
combination.

**Review verdict (asked by owner):** both reports follow the standard
faithfully — §3 record shapes, exact column names, FIND evidence format,
verdict/severity vocabularies, split respected, owner questions collected
in-doc (Q-A01–A03 · Q-B01–B02). Both independently live-verified GitHub and
corrected the standard's stale #639 expectation. 19 findings, zero severity-1;
dominant pattern = **ledger classification drift** (hidden-via-decorator
panels/legacy commands not classified; slash commands have no classification
wiring at all — FIND-A01/A05/B04/B07).

## 2. Captured owner posture Q-0070 + the AI template-advisor idea (this PR)

Owner reacted to four live free-text editor modals
(`moderation.warn_timeout_minutes` int modal, `ai.ai_default_model`,
`moderation.dm_template`, `ai.ai_guild_instruction_profile`):
**presets wherever feasible + preset-then-edit + always-manual-entry**, with
the AI-suggested-templates system explicitly "an idea for later".

- Router **§30 / Q-0070** (verbatim answer + decoded posture + scope; numbering
  note: Q-0066–0069 reserved by in-flight #638).
- New `docs/ideas/settings-presets-and-ai-template-advisor.md` (posture =
  decided; advisor = captured/gated) + pointers: ideas README, roadmap
  §Someday, settings folio Ideas section, settings audit §11 **Phase 4** row.
- Also recorded in the ideas file: two live-walk polish items for Phase 4 —
  the `current=" · default="` empty-placeholder bug and raw-key modal titles.

## Decisions made alone

- Took **Q-0070** (skipping 0066–0069) to avoid the #638 renumber-on-merge
  cost — noted in the router section header.
- Resolved the codex branches' standard copies to main's content rather than
  asking each Codex session to redo it (mechanical, owner-requested outcome).

## Flagged for maintainer / known limits

- Neither mapping PR has a CI run yet (Codex PRs; zero check runs) — watch
  `code-quality` go green at merge; Agent A's sandbox never executed pytest.
- The §7.1 note rides *both* mapping branches identically — if you close one
  PR instead of merging it, the note still lands via the other.

## Context delta

- **Needed but not pointed to:** nothing major — the §7.1-note placement
  question (where does a "note for the next session" durably live when the
  carrying PRs are someone else's?) had no convention; identical-text-on-both-
  branches worked and is worth remembering for parallel-agent reconciliation.
- **Pointed to but didn't need:** —
- **Discovered by hand:** GitHub add/add conflicts for two branches that each
  imported the same file from an open PR resolve cleanly when the second
  merge's both-sides edits are byte-identical — the basis of the §7.1 note
  trick; also `git merge-tree`/worktree simulation is the cheap way to prove
  PR merge order doesn't matter before promising it.
