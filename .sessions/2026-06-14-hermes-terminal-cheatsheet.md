# Session: Hermes terminal cheatsheet doc + Acode/GitHub setup guidance

> **Status:** `complete` — PR #874; born-red card flipped as the deliberate final step (Q-0133).

**Branch:** `claude/sharp-ptolemy-5mzbvb` · **Date:** 2026-06-14 · **Type:** docs (owner-requested ops reference)

## What this session did

The owner wanted a copy-paste command reference for operating Hermes/SuperBot from his phone, stored
durably (he'll open it in Acode) rather than as a drifting Notes paste. Created
**`docs/operations/hermes-terminal-cheatsheet.md`** (`reference`) — service control, repo→Hermes
deploy (`install-soul.sh`/`install-skills.sh`), Hermes config/identity, read-only repo health,
prod diagnostics (`railway_*`), and general Linux — each command with a one-line what/why. Wired it
into `hermes-control-plane.md` § Useful commands (reachability) so `check_docs` passes and Hermes can
reference it too. One versioned source, openable from Acode/GitHub.

Also gave the owner verified Acode↔GitHub setup guidance (the Acode **GitHub plugin** for
browse-without-clone + a fine-grained PAT, vs the Clone Repository + GitPro plugins for full edit/commit)
in chat — researched against the current Acode plugin ecosystem.

Verification: `check_docs --strict` ✓. Docs only.

## 💡 Session idea (Q-0089)

The cheatsheet is hand-maintained, so it can drift from the actual scripts (a renamed flag, a new
installer). Idea: a tiny CI check that greps the fenced commands referencing `scripts/hermes/*.sh|.py`
and asserts each referenced script path exists — cheap protection against the cheatsheet citing a
script that was moved/removed. Captured pending a dedup-grep.

## ⟲ Previous-session review (Q-0102)

The previous run (#873, install-soul.sh) correctly made the operating-prompt install repeatable but
stopped at "here are the commands in chat" for everything else — the owner then (reasonably) wanted
those commands somewhere durable. Lesson reinforced: when a chat answer is a list of commands the
owner will reuse, the durable move is to version it in the repo from the start (one source, Hermes-
readable, Acode-openable), not leave it as a transient message. This session closes that by shipping
the cheatsheet doc.
