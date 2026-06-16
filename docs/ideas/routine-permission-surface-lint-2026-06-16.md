# Idea — a lint that flags routine-common commands that would hit the `ask` permission brake

> **Status:** `ideas` (Q-0089 session idea, 2026-06-16, from the band-#990 reconciliation pass —
> after the routine **stalled twice** on a `permissions.ask` `rm` prompt, fixed reactively as Q-0161).
> Not approved for implementation. Source + `.claude/settings.json` win over anything here.

## The problem this catches

An **unattended** routine (dispatch / reconciliation) that hits a Claude Code permission prompt
**silently stalls** — there is no human to click "Allow", so the whole scheduled run is wasted. The
web/remote harness does not honor `bypassPermissions` and enforces `permissions.ask` (which outranks
`allow`), so *any* command matching the `ask` list blocks the run — including a part of a **compound**
command (`A && rm scratch && B` stalls on the `rm`). This has now happened more than once and has been
fixed **reactively** each time by widening `allow` / narrowing `ask` (Q-0149, then Q-0161). Reactive
is one stalled run too late.

## The idea

A small stdlib `scripts/check_routine_permission_surface.py` that turns the reactive fix into a
**pre-flight guard**: given a list of the commands the routines actually run (harvested from the
routine prompts + the `scripts/hermes/*` + the documented runbooks, or a maintained allow-listed
corpus), evaluate each against the **current `.claude/settings.json` `ask`/`allow` rules** (same
prefix-match semantics Claude Code uses) and **fail / warn on any routine-common command that would
resolve to `ask`** — i.e. would stall an unattended run. Output: the offending command + which `ask`
rule catches it + the suggested `allow` narrowing.

Run it in `check_docs` / a cheap CI step (it only reads two files) so a settings change that would
re-introduce a routine stall is caught **before** it burns a scheduled run, not after.

## Why it's worth having

- It is the **machine version of the Q-0161 lesson** — "every command an unattended routine issues
  should resolve to `allow`, never `ask`; the `ask` list is only for prod/DB/force-history/external
  brakes." A lint makes that invariant checkable instead of a thing each pass re-learns.
- Cheap, read-only, stdlib, disposable (Q-0105) — exactly the convenience-guard shape the repo
  favours; delete it if it proves noisy over a few sessions.

## Routing / mechanics

- **Ownership:** `.claude/settings.json` (`permissions`) + the routine prompts (`docs/operations/*`).
- **Reuse:** the prefix-match logic is tiny; no new dep. Pairs with the existing `check_*` family.
- **Open question:** where the "routine-common command corpus" lives — a hand-maintained list is the
  simplest start; harvesting from prompts is the richer (but fuzzier) version.

→ relates `.claude/settings.json` · `docs/owner/maintainer-question-router.md` (Q-0149/Q-0161) ·
`.session-journal.md` (the cwd-deadlock + rm-stall recurring-problem notes).
