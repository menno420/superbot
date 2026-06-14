# Session: branch-hygiene note in the cheatsheet (626→2 prune capture)

> **Status:** `complete` — docs-only; born-red gate satisfied by this card.

**Branch:** `claude/sharp-ptolemy-5mzbvb` · **Date:** 2026-06-14 · **Type:** docs (ops knowledge capture)

## What this session did

While helping the owner set up Acode↔GitHub, the repo's **626 leftover `claude/*` branches** broke
Acode's branch picker (it paginates and never reaches `main`). The owner pruned them on the VPS
(626→2: `main` + the live session branch). Captured the durable lesson in
`hermes-terminal-cheatsheet.md` → new **Branch hygiene** section: enable "Automatically delete head
branches", the one-time bulk-prune command (run from a clone with push rights — a Claude sandbox's
git proxy 403s on deleting other branches), and the reassurance that deleting a branch never deletes
its PR. `check_docs --strict` ✓.

## 💡 Session idea (Q-0089)

The autonomous loop creates a `claude/*` branch per PR but nothing in-repo enforces cleanup — the
pileup is invisible until something (like Acode) chokes on it. Idea: have a routine (or the
reconciliation pass) include a quick `git branch -r | wc -l` sanity check and flag when remote
branch count crosses a threshold (say >50), so buildup is caught early instead of at 626. The real
fix is the GitHub "auto-delete head branches" setting, but a checker catches the case where that's
off. Captured pending a dedup-grep.

## ⟲ Previous-session review (Q-0102)

This whole Acode arc (a chain of small owner-driven fixes) went well as collaboration but exposed a
gap: agent-facing setup docs assumed the repo was tidy. The branch pileup had been accumulating
silently across hundreds of autonomous PRs because none enabled GitHub's auto-delete-on-merge — a
one-time setting no session ever owned. Lesson: infrastructure defaults that prevent slow accretion
(branch auto-delete, log rotation, cache caps) are worth setting *once, early*; this session both
fixed the symptom and recorded the prevention so it's not rediscovered at the next 600-branch wall.
