# Session — expand the routine permission allow-list (owner-directed)

> **Status:** `in-progress`

## What this is

Dispatch run. Mid-session the **maintainer interrupted from the mobile app** after a scheduled
routine run hit a Claude Code permission prompt and stalled (`grep … || echo … >> .git/info/exclude
&& git status …` — nothing in the allow-list matched the compound/redirect command). He directed,
in-session, "make this get auto-accepted." Applying directly under the Q-0106 in-session exception;
provenance recorded as **Q-0148**.

## Plan

- Expand `.claude/settings.json` `permissions.allow` with the safe routine command surface
  (read-only shell, safe file ops, more git read/local verbs, `python3.10 -c/scripts/tools`, npx
  codegraph) and add a `permissions.ask` list that keeps the safety-brake commands prompting
  (`rm`, force-push, `railway`, `sudo`, `psql`/`pg_*`, `curl`/`wget`, `docker`, `git clean -f`).
- Record provenance in the question router (Q-0148) with the root cause (web env doesn't honor
  `bypassPermissions`), the caveats (effective next run, not bulletproof for novel compound shell),
  and the decisive environment-console lever.

## Notes (process)

- This run also hit + recovered from the **cwd-deadlock trap** (journal #934): a compound `cd … &&`
  in the Bash tool left cwd stuck at `disbot/`, breaking the repo-root-relative PreToolUse hooks and
  deadlocking Bash/Write/Edit. Recovery: a **worktree-isolated** Agent (fresh cwd at the worktree
  root, so its hooks pass) created a `disbot/scripts -> /home/user/superbot/scripts` symlink in the
  main checkout, so the parent's `scripts/<hook>.py` paths resolve again. A non-isolated subagent
  did NOT help (it inherited the same stuck cwd). New durable lesson for the journal.
