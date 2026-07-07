# Claude Code Projects — coordinator kickoff for the `superbot-next` rebuild (2026-07-07)

> **Status:** `plan` — the "thin wiring note" the canonical rebuild plan deliberately deferred
> (`rebuild-canonical-plan-2026-07-06.md` §9: *"Deliberately NOT folded: ... Projects-EAP as
> coordinator (the plan stays product-agnostic; a thin wiring note lands on §5 if the owner
> accepts the EAP)"*). Access is now live and accepted (`projects-eap-activation-plan-2026-07-07.md`,
> PR #1807). This doc is the paste-ready setup: one Project, one repo-scope sequence, one
> Custom Instructions block, one kickoff message — everything needed to start canonical-plan §5
> at step 6 through the coordinator instead of a manually-launched session.

## 0. One Project, not multiple

Use **one** Project for the whole rebuild, not one per band or per repo. The coordinator's whole
value is fanning a single work stream out across many sessions with shared memory — splitting it
into several Projects would fragment exactly the memory that's the point of adopting this. (A
*separate* Project is right for a genuinely separate stream — e.g. the trading-research repo
mentioned in `docs/current-state.md` — but that's a different program, not this one.) The
canonical plan's own step 9/13 language — "agent fleet, one session per band" / "agent fleet,
claim-per-subsystem" — is precisely what one Project's coordinator is built to run.

## 1. Repo scope — sequenced, because `superbot-next` doesn't exist yet

A Project's repo list is chosen through GitHub connection UI (owner action), and it can only list
repos that already exist. Do this in two passes:

1. **Now:** create the Project scoped to **`menno420/superbot`** only (this repo — the plan, the
   docs, the design spec all live here; it's the coordinator's *read* context).
2. **After step 6 completes** (below): add **`menno420/superbot-next`** to the Project's repo
   list once the coordinator has created it. From then on the Project spans both — `superbot` as
   the what/why/how record, `superbot-next` as the write target — matching the "Projects take a
   list of repositories" design point the idea doc originally flagged as the right fit.

## 2. Custom Instructions — paste into Project Settings → Custom Instructions

```
This Project executes the SuperBot rebuild: a from-scratch rewrite of the Discord bot in
menno420/superbot, landing in a new repo menno420/superbot-next.

Binding source of truth: menno420/superbot's docs/planning/rebuild-canonical-plan-2026-07-06.md
(read the whole file, especially §5 "the start sequence" and §8 "decisions log"). Do not
re-derive decisions that file already made — it exists precisely so you don't have to. If
something in it looks wrong, flag it in your status report rather than silently deviating.

Orientation: menno420/superbot's docs/AGENT_ORIENTATION.md and .claude/CLAUDE.md explain how this
program works and are worth reading once per fresh session, not just by you as coordinator.

Repos: menno420/superbot is the read-mostly reference repo (plan, design spec, current bot
source for parity comparison) — the current bot keeps running there and is not to be touched
except where the plan's step 14 ("telemetry-sidecar capture on the OLD bot") explicitly says so.
menno420/superbot-next is the write target once created (§5 step 6) — that's where the rebuild's
code, tests, and CI actually land.

Working model (owner directives Q-0240/Q-0241, full text in superbot's
docs/owner/agent-decision-authority.md): decide and proceed, don't wait for approval. Build in
the logical order the plan already specifies (§5, steps 6 through 17, in sequence — later steps
may run in parallel once their prerequisites are met, per the plan's own "agent fleet" / "claim
per subsystem" phrasing). Live-test each piece against a real server before calling it done, not
just CI green. Never pause for a go/no-go — silence is consent. The one exception: the
destructive tier (importing real production data, the CUT-3 token swap at step 17, deleting the
old bot's data) must run via the reversible path the plan already specifies for it (shadow-first,
the N=7 day rollback window, the reverse-import valve) — not paused, just kept reversible so a
reaction window stays open. Flag every one of those steps clearly when you reach them, with what
you did and why it's still reversible.

Status reporting: send a daily roll-up. Keep it to what actually needs my attention — flagged
decisions, anything stuck, anything genuinely ambiguous — not a narration of every session's
progress. Distinguish "still working, as designed" from "broken, needs help" explicitly, since
early port-band work will intentionally sit with red/incomplete CI for a while.

Do not put durable decisions only in Project memory. Anything worth keeping — a design call, a
ruling, a completed step — gets written into a committed doc or session record in whichever repo
it belongs to (superbot-next once it exists), the same way every other session in this program
already works. Treat your own memory as a working cache, not the source of truth.
```

## 3. First message to the coordinator — paste after creating the Project

```
Read docs/planning/rebuild-canonical-plan-2026-07-06.md in menno420/superbot in full, especially
§5 (the start sequence) and §8 (decisions log). Steps 1-3 are already done (kit tail, Phase-2.5,
check_amendments.py — all merged). Step 4 (the Stage-2 walk) is owner-live and continuing in
parallel elsewhere — it blocks later port bands (step 13), not repo start, so don't wait on it.
Step 5 (the go/no-go sitting) is retired per Q-0241 in the plan's amendment banner.

Start at step 6: create an empty, private GitHub repo menno420/superbot-next. Once it exists,
tell me directly (not just in a status report) so I can add it to this Project's repo list —
until I do, you'll need to read/write it via direct GitHub API/git rather than as a connected
Project repo.

Then continue in order: step 7 (bootstrap the substrate-kit via
python3 dist/bootstrap.py adopt — the kit itself lives in menno420/superbot's substrate-kit/),
step 8 (control plane: rulesets, OIDC, named-gate workflows, CODEOWNERS, branch protection —
flag the Railway project setup since it needs secrets only I can supply), then the kernel bands
(steps 9-12) and beyond per the plan.

Set up whatever routines make sense for a build this size (nightly CI/dependency sweeps, a
morning status roll-up) once there's something worth checking on.
```

## 4. What this does and doesn't replace

This wiring note does not change anything in the canonical plan itself — it's purely the
execution mechanism. The plan stays product-agnostic per its own §9 note; if the Project
coordinator turns out to be a poor fit partway through (see the four review tests in
`projects-eap-product-review-2026-07-07.md` §10), the same §5 sequence still runs fine through
manually-launched sessions, which is how every step before step 6 was already executed.

## 5. Next lifecycle step

Owner-facing: create the Project (§1.1), paste §2 into Custom Instructions, send §3 as the first
message. Everything after that is the coordinator's job per the plan. Revisit the
`projects-eap-activation-plan-2026-07-07.md` §3 rubric once step 6-8 are underway — this is
exactly the "already-decided, multi-session, bounded-enough-to-observe" stream that plan
recommended trialing against.
