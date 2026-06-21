# 2026-06-21 — Allow `git push --force-with-lease` + `cd` in permission allowlist

> **Status:** `complete`

## Arc
Owner-directed, in-session config fix. The maintainer (on web/remote) kept hitting
confirmation prompts on the standard verification + force-push bundle and asked to add
them to the always-allow list (screenshots of the "Verify rebased branch and force-push"
prompts).

## Root cause
The web/remote harness does not honor `defaultMode: bypassPermissions` — it evaluates the
`allow`/`ask`/`deny` rules. Two things forced the prompt on the whole bundle:
1. `permissions.ask` contained `Bash(git push --force*)`, which matches the
   `git push --force-with-lease …` step. Any sub-command of a compound command matching
   `ask` makes the **entire** bundle prompt.
2. `cd` (the bundle's first command) had no `allow` rule.

## Shipped
- `.claude/settings.json` `permissions.allow` += `Bash(git push --force-with-lease*)`
  (the safe, non-clobbering force variant) and `Bash(cd*)`.
- Bare `git push -f` / `git push --force` stay in `ask` (genuinely dangerous clobbering
  forms); the more-specific `--force-with-lease` allow wins by rule specificity.
- Committed to the checked-in `settings.json` (not `settings.local.json`) **on purpose**:
  the remote environment clones fresh each container, so only committed config persists
  across the owner's web sessions.

## Provenance
Owner-directed in-session change to executable config — the CLAUDE.md Q-0106 carve-out
("a change the maintainer directs in-session: the owner is the live reviewer, apply it
directly"). No new router Q required; recorded here for the trail.

## Context delta
- **Needed but not pointed to:** that `bypassPermissions` is a no-op in the web/remote
  harness (it falls back to allow/ask/deny evaluation). Worth a journal note for the next
  agent debugging "why am I still being prompted?".
- **Discovered by hand:** the compound-command rule — one `ask`-matched sub-command
  prompts the whole bundle — which is why bundling a force-push with verification made
  every verify step prompt too.

## ⟲ Previous-session review
The prior run (PR #1207) correctly resolved the conflict and let auto-merge land it, and
left a clean status. What it could have done better: it ended on a **stale branch** whose
sole commit was already merged, without resetting — the next session inherited a "4 behind
/ 1 ahead" tree. Improvement: a session whose PR has merged should reset to `origin/main`
(clean tree) before ending, so the branch it leaves isn't pre-conflicted.

## 💡 Session idea
A tiny `scripts/check_permission_overlap.py` (stdlib, disposable) that flags
`permissions.allow`/`ask`/`deny` entries where a broader `ask` prefix shadows a narrower
`allow` (or vice-versa) — would have caught the `git push --force*` (ask) vs
`--force-with-lease` (allow) overlap at config-edit time instead of at the prompt.

## 📤 Run report

- **Did:** Added `git push --force-with-lease` + `cd` to the permission allowlist so the verify+force-push bundle stops prompting · **Outcome:** shipped
- **Shipped:** PR (this branch) — `.claude/settings.json` allowlist additions
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none
- **↪ Next:** resume the `current-state.md` ▶ Next ungated startable (creature-game PvP lane is owner/Hermes-gated; botsite React-SPA migration or a small stdlib guard are the clean ungated options)
