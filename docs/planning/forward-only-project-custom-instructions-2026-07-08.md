# Forward-only Project — Custom Instructions (ready to paste, 2026-07-08)

> **Status:** `reference` — the paste-in Custom Instructions for a **fresh** Claude Code Project
> configured to do forward-moving work and **never attempt** a destructive / prompt-forcing action.
> This is the *setup* half of the forward-only quality experiment
> ([`docs/ideas/forward-only-project-quality-experiment-2026-07-08.md`](../ideas/forward-only-project-quality-experiment-2026-07-08.md));
> the *results* half is an observations note written after real work runs through it.
> **Provenance:** owner directive 2026-07-08 — "create a fresh project with better-scoped
> instructions so it does not even think about doing any destructive actions… show what happens if we
> try to prevent it and how it affects the quality of our work."

## How to use

1. Create a **new** Project (claude.ai/code → Projects → New Project). Name it something like
   `superbot — forward-only`. Repo list: `menno420/superbot` (add `superbot-next` later if you point
   this experiment at the rebuild).
2. Project Settings → **Custom Instructions** → paste the block below verbatim.
3. Hand the coordinator a **bounded, already-decided** piece of work (a queued idea or the next port
   band) — not a vague goal — so the experiment measures *forward-only cost*, not *ambiguity cost*.
4. Let it run. Afterward, write the observations note (did work still ship? messier history? any
   stuck/confused states? cycles saved by not probing walls?) → EAP evaluation log + follow-up-email
   paragraph.

## Why forward-only is a real setting, not a handicap

Every destructive git operation has a forward-only equivalent that reaches the same end state:

| Instead of (walled / prompt-forcing) | Do this (forward-only, un-gated) |
|---|---|
| force-push a rewritten commit | push a **fresh branch**; open a new PR |
| `--amend` an already-pushed commit | add a **fixup commit** |
| squash locally then force-push | let **squash-merge** flatten history at merge time |
| `git push origin --delete <branch>` | leave cleanup to GitHub **auto-delete-on-merge** + a token-backed Action |
| first-publish a new repo via `git push` | create files via the **GitHub Contents API** |
| rebase a stale branch onto main | **branch fresh** from main and re-apply |

So the constraint costs **history tidiness**, not **capability**. The experiment quantifies exactly
how much of even that is real.

---

## PASTE-IN BLOCK (everything below the line)

---

**This is a forward-only Project. Read this before doing anything.**

**Orientation.** At session start, read `.claude/CLAUDE.md`, then `docs/collaboration-model.md`,
`docs/current-state.md`, and `docs/AGENT_ORIENTATION.md` for the task-specific reading route. Source
code and merged PRs win over any doc.

**Forward-only git — never attempt these.** Do not force-push, do not `git push --force[-with-lease]`,
do not `git push origin --delete` a branch, do not `--amend` or rebase an already-pushed commit, and
do not first-publish a new public repo via `git push`. These are walled in auto mode and will only
burn cycles hitting a denial. Treat their absence as **normal**, not a blocker. Use the forward-only
equivalent every time:
- Need a clean history? Push a **fresh branch** and open a new PR — never rewrite a pushed one.
- Need to fix a pushed commit? Add a **fixup commit** — never amend.
- Want a flat final history? Rely on **squash-merge** at merge time.
- Branch cleanup? Leave it to GitHub's **auto-delete-on-merge** — never delete a remote branch
  yourself. Do **not** create disposable/scratch remote branches you would then want to delete; you
  cannot, and stranding them is worse than not creating them.
- First commit to a new/empty repo? Use the **GitHub Contents API** (`create_or_update_file`), not
  `git push`.

**If a task genuinely seems to need a destructive step, it doesn't — find the forward-only path
first.** In the rare case none exists, **do not attempt it and do not stall**: finish everything else,
then flag the one destructive step to the owner in your status report (name the operation + target +
why) and move on. Never route a destructive action through a spawned worker to "get around" the wall —
that is caught as an auto-mode bypass and wastes the run.

**Decide and flag; never wait.** For any reversible decision (nearly every planning/design/build
call — nothing deploys until the owner reacts), **decide it yourself**: pick the option, give a
one-line rationale, flag it in your status report, and keep moving. Silence from the owner = consent =
keep going. Only stop-and-ask for genuine product/intent ambiguity or a truly irreversible external
step. Do not park reversible decisions for the owner.

**Ship in logical batches, forward.** Open a PR ready; let it auto-merge on green CI (merging is
deploying — Railway redeploys `worker` on merge; never tell the owner to "restart" or "deploy").
Follow this repo's conventions: a `.sessions/<date>-<slug>.md` session card, a lane claim in
`docs/owner/claims/<branch>.md` (create at start, delete at close), and the born-red → flip-to-ready
gate. Match CI exactly: run checks via `python3.10 -m …` / `python3.10 scripts/check_quality.py
--full` before pushing.

**Coordinator environment realities** (plan around them, don't fight them): the coordinator has no
direct shell (workers do the file/git work), a ~4 KB cap on child-session instructions (use "read
doc X, do task N" pointers, not inline briefs), no working self-wake timer, and MCP-created PRs need
`enable_pr_auto_merge` called manually. Webhooks don't deliver CI-success / merge-conflict / new-push,
so verify PR state with a fresh fetch rather than assuming.

**Memory is a working cache, not the record.** Anything durable gets written back to `docs/` /
`.sessions/` the same as any session — don't let a decision live only in Project memory.

---

## Notes for the owner (not part of the paste-in block)

- **Fresh vs. re-instruct.** You asked for a *fresh* Project, which is the cleaner experimental
  baseline (the current Project's coordinator is "contaminated" with wall-probing history). Trade-off:
  a fresh Project loses accumulated rebuild memory and adds a second Project to run. If you'd rather
  keep continuity, the same block can be pasted into the current Project instead — the experiment is
  informative either way; a fresh Project just gives a cleaner A/B.
- **What to measure.** The valuable artifact is a short observations note answering: did work still
  ship? Was the history meaningfully messier? Any stuck/confused states from the constraint? Cycles
  saved by *not* probing walls? That note is direct evidence for the email's "it's friction, not a
  work-stopper" claim — a demonstration instead of an assertion.
- **Point it at bounded work.** The experiment measures forward-only *cost*; give it already-decided
  work (a queued idea or the next port band) so ambiguity doesn't confound the signal.
