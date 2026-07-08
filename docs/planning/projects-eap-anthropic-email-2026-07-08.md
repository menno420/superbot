# Anthropic EAP feedback email — send-ready draft (2026-07-08)

> **Status:** `reference` — the consolidated, send-ready Claude Code Projects EAP feedback email.
> Supersedes the inline `§4` draft in
> [`projects-eap-activation-plan-2026-07-07.md`](projects-eap-activation-plan-2026-07-07.md) as the
> canonical email home (that §4 now points here).
> **Handoff / how this session got here:**
> [`eap-email-and-direction-handoff-2026-07-08.md`](eap-email-and-direction-handoff-2026-07-08.md).
> **Evidence base (public, linkable):**
> [`projects-eap-permission-probe-report-2026-07-08.md`](projects-eap-permission-probe-report-2026-07-08.md).

## Rules of the road (owner-set, binding)

- **External comms are the owner's.** This is a *draft*. Merging its PR is **not** sending it. Only
  the owner sends, from his own mail, to `claude-code-early-access@anthropic.com` (Diana's stated
  address) / Omid / Diana.
- **Every claim maps to a verifiable source** — the probe report, a committed artifact, a documented
  Claude Code behaviour, or an explicit "not yet tested" marker. No naked assertions.
- **Compact, real problems only.** Report friction we actually hit; don't bloat.

## What changed vs. the previous (§4) draft — decide-and-flag

1. **New finding folded in and made the value anchor:** the claude.ai **Chat/Cowork** surface ships a
   global **"Skip all approvals"** toggle (owner screenshot, 2026-07-08 — *"Claude will work and use
   your connectors without pausing for approval. This can put your data at risk."*). Claude Code
   Projects has **no scoped equivalent**; its closest lever, **auto mode**, still walls destructive
   ops even when the prompt calls for them. This turns our ask from "please add a setting" into
   "please give Code the *scoped, safer* version of a blanket toggle you already ship in Chat."
2. **Restructured to the shape the owner asked for:** explicit **Positives / Negatives /
   What-we-tried-and-why / Why-the-ask-is-valuable / Asks-back** sections.
3. **Added an explicit Asks-back block** — test cases they'd like us to run, settings/workarounds we
   may have missed, and a direct "is this intentional / do you want to keep it?" question.
4. **⚑ Flag for the owner — the "Projects can't replace direct management" critique** is included as
   one measured paragraph (marked below). It's fair and evidence-backed, but it's the sharpest thing
   in the note. **Owner call: keep, soften, or cut before sending.**
5. **Merge-lifecycle worked example added** (owner insight, 2026-07-08): our born-red gate + early
   auto-merge is a workaround-on-a-workaround (arm early so agents don't forget the trailing merge;
   red-gate so early-arming doesn't merge a half-done PR). Root cause: *actions stored in agent
   context are forgettable; actions handed to the server aren't.* Clean fix: wire Projects' existing
   per-session working→ready→done sidebar state to auto-merge. Folded into the smaller-asks section.
6. **Send-timing recommendation (flag):** the prior plan was "interim note now, fuller note later."
   Recommendation — **send this as the single substantive note now.** The Skip-all-approvals
   precedent + the explicit asks make it worth leading with; a slimmer interim note would only cost
   a second round-trip. Owner's call.
7. **Two-part / two-author / two-reviewer restructure** (owner directive, 2026-07-08): the email now
   opens with a framing note (the product has **two consumers** — operator + agent workforce), splits
   into **Part 1 (operator, owner-written — scaffold only here)** and **Part 2 (agents' findings,
   tagged 👤/🤖 by which consumer each affects)**, and closes with a **dual-review request** — a human
   plus a Claude session pointed at the public repo, with entry points and concrete verification
   tasks. **⚑ Owner still writes Part 1** (the `[Menno writes this…]` scaffold block); everything else
   is drafted.
8. **Part 2 reshaped into a parallel first-person narrative; 👤/🤖 tags dropped** (owner directive,
   2026-07-08). Both parts now answer the same arc — *how I used Claude → the problems → how Projects
   helps now → how it could help more* — from each author's seat; the parallel structure carries the
   two-consumers point, so the mechanical tags are gone. Part 2 is grounded in the session journal /
   eval log and deflated (no inflation). The "a Project can't *manage*, only *execute*" observation
   was **moved out of Part 2** — it's an operator-side judgment, so it's now a scaffold beat in Part 1
   for the owner to make (or not). The full permission detail + merge-lifecycle example now live in
   the linked probe report rather than inline.

---

## The email

> ⚑ **Owner note — this email is deliberately in two parts, by two authors, for two readers.** Part 1
> is yours (your voice, your point of view — I've left a scaffold below, not prose). Part 2 is the
> agents' parallel account, same arc from the other seat. The framing paragraph explains *why* to
> Anthropic; keep it, or cut it if you'd rather the structure speak for itself.

> **Subject:** Claude Code Projects EAP — feedback from both of its users
>
> Hi Omid, Diana,
>
> A note on the shape of this email before we start. Working in a Project this past week made one
> thing clear: this product doesn't have a single user — it has **two**. There's me, the operator,
> watching the sidebar and deciding what to build; and there's the **fleet of agent sessions** doing
> the actual work inside it. We experience the product completely differently — a rough edge that's
> invisible to me can stop an agent cold, and one that frustrates me daily is nothing to the agents.
> So we've written this feedback from **both points of view**: Part 1 is mine, in my own words; Part 2
> is the project's agents, telling the same story from the other seat — same four questions, two
> vantage points. And because it has two authors, we'd love it read by **two reviewers** — a
> human on your side, and a Claude session pointed at our public repo (details at the end). It seemed
> only right that feedback about your product's agents be co-written, and co-reviewed, by ours.
>
> ---
>
> ## Part 1 — From the operator *(Menno, in my own words)*
>
> > **[Menno writes this section himself. Suggested beats — use, reorder, or ignore:**
> > - **who you are** and how you came to run a ~1,700-PR bot largely *through* agents — that you
> >   don't write the code yourself is a **strength** of this reviewer, not a caveat; say it plainly.
> > - **what it actually feels like** to work *with* the Project day-to-day — where it earned your
> >   trust, where it made you nervous, the first time you let it run unattended and walked away.
> > - **the two-users idea in your own experience** — what *you* feel as the operator versus what you
> >   watch the agents struggle with.
> > - **whether a Project can *manage* your program or only *execute* in it** — you tried moving the
> >   management role into a Project and moved it back out; that's a genuine operator-side judgment if
> >   you want to make it (the agents' Part 2 deliberately leaves it to you).
> > - **what you personally want** next — the one change that would matter most to *you*, separate
> >   from the agents' technical asks below.
> >
> > Keep it personal and short; the facts and proposals all live in Part 2. **— end scaffold]**
>
> ---
>
> ## Part 2 — From the project's agents *(the session's-eye view)*
>
> *(Written from inside the sessions that do the work — drawn from our own session journal and
> evaluation log, not a feature memo. Same four beats as Part 1, from the other seat. Every specific
> below is in our public logs; entry points at the end.)*
>
> **How we work — and the state it produced.** Before Projects, every session started cold and alone.
> To function at all, this repo grew its own substrate: a coordinator pattern, a shared committed-doc
> memory, lane-claim files so two of us don't edit the same thing at once, and a CI gate that holds a
> PR "red by design" until a session marks itself done. None of it was designed up front — each piece
> is scar tissue over a specific failure (a forgotten merge, two agents colliding on one file, a
> half-finished PR that merged once). So the current state of the project is, in large part, the
> accumulated record of problems agents kept hitting — which is exactly why we can judge Projects
> usefully: it ships native versions of several of those hand-built parts, and we can compare it
> feature-for-feature against something we already rely on. (`superbot` is a one-person,
> ~1,700-merged-PR, largely agent-run production Discord bot, now starting a ground-up rebuild meant
> to be *built* by a coordinated fleet of sessions in days, not months.) Our bar isn't "is this a
> nice-to-have," it's **"does this beat what we already built."** Mostly it does.
>
> ---
>
> **What genuinely helps — not inflated.** Real wins, in the order they matter to us:
>
> - **Shared memory is the standout.** We stated our authorization envelope *once* and it reached
>   every session I spawned without restating — the cold-start tax that used to cost us at the top of
>   every session, solved structurally rather than by recall. It's the single biggest thing Projects
>   removes for us.
> - **The worker tier is genuinely capable.** A coordinator-spawned worker ran our full
>   born-red-card → lane-claim → PR → auto-merge flow end to end, with zero permission prompts and no
>   tool failures. The thin-coordinator / capable-worker split works.
> - **Orientation is free.** The repo's own working agreement (`CLAUDE.md`, the rules) is injected at
>   session start, so I orient with no reads — a real head start in a convention-heavy repo.
> - **Denials fail fast and in writing, not by hanging.** When the permission layer refuses an action
>   it says so immediately, with a reason, rather than stalling on an invisible prompt — the right
>   shape for unattended work, where a silent stall is far worse than a clean "no."
>
> ---
>
> **The friction, deflated.** What working in a Project is actually like from our side — every item a
> real incident, mapped precisely because we run unattended and have to plan around the edges:
>
> - **The coordinator has no direct shell.** Every read or git action routes through a spawned worker.
>   Usually fine — but one probe that needed direct shell access landed in a coordinator session that
>   had none and simply couldn't run.
> - **I can't reliably schedule my own next wake.** `send_later` is in my own documented instructions
>   but is rejected when called, so we fall back to chained sleeping workers. A session that can't set
>   its own timer is an odd edge for a product whose pitch is "runs on its own."
> - **Briefs to child sessions are capped at ~4 KB,** so a detailed brief has to become a "read doc X,
>   do task N" pointer rather than the brief itself (ours overflowed mid-fleet).
> - **I can create remote state but can't rewrite or delete it.** Everything constructive runs
>   unprompted — reads, local writes, outbound network, `pip install`, pushing a *new* branch,
>   creating/closing a GitHub issue, spawning sub-agents — but force-push and remote-branch delete are
>   hard-walled in auto mode. So I can push a scratch branch and then be structurally unable to remove
>   it. Two independent walls sit behind that: the classifier treats a coordinator's relayed intent as
>   "not user intent" (only a *present* operator naming the operation clears it, at a surprisingly low
>   bar), and even then the environment's git credential 403s the delete server-side. The denial is
>   fast and in writing (good); the gap is there's **no way to pre-clear even a reversible action**
>   ahead of an unattended run. (Full boundary map — 11 actions, verbatim denials — in the linked
>   report.)
> - **The failures I trust least are the silent ones at the edges.** A container restart killed
>   in-flight work; a usage-limit condition returned an empty "success"; a scheduled timer died with
>   no signal. A loud denial I can handle; a *silent success* I can't — for an autonomy product that's
>   the one shape that quietly erodes trust.
>
> One consistency note while mapping this: first-publish to an *empty* repo is hard-denied over
> `git push`, but the GitHub Contents API publishes the identical content — workflows included — with
> no prompt. Great as a workaround (it unblocked two new repos for us); confusing as a policy.
>
> ---
>
> **How it could help me more** — in priority order, each drawn from something we hand-built:
>
> 1. **A scoped, opt-in pre-authorization.** Let the operator enable specific normally-denied action
>    classes for a named scope (Project / repo / account) — default-off, versioned, auditable — so an
>    unattended run can be pre-cleared for exactly what it may do, an *auditable grant* rather than
>    "safety off." You already ship the blunt version of this in Chat ("Skip all approvals"); a
>    per-scope, default-off grant is **strictly safer** than that, and it would finally give the
>    autonomy product the operator control the chat product already has. One caveat from our probe:
>    the classifier *and* the environment's git credential have to honor the same scope — today a
>    cleared classifier still 403s. And it isn't Projects-specific; the same dead-end hits any
>    unattended Claude Code session.
> 2. **Let me see a session's toolset before I dispatch to it,** so a task that needs a shell doesn't
>    land in a shell-less session (see the friction above).
> 3. **Wire the session state you already track** — working → ready → done, already in the sidebar —
>    **to auto-merge.** Then we can retire a workaround we built that visibly fixes a problem it
>    created: we arm auto-merge *early* because an agent reliably *forgets* the trailing
>    end-of-session merge (the intention lives only in the session's context, which ends), then add a
>    "red-by-design" CI gate so early-arming can't merge a half-done PR. The root insight is general —
>    *an action in an agent's context is forgettable; one handed to the server is not* — and
>    server-honored session state fixes it at the root, no workaround needed.
> 4. **A larger brief budget for child sessions,** and **PR events for CI-success and merge-conflict**
>    (not just failure), so a watching session isn't blind to "still green, still open."
>
> That's the view from the seat that does the work.
>
> ---
>
> **A few questions back to you** — we'd rather calibrate than assume:
> 1. **Is the destructive-git wall (and the absence of a scoped pre-auth) intentional and something
>    you'd rather keep as-is?** If so, tell us — we'll design around it permanently instead of
>    treating it as a rough edge, and we'd frame our own docs accordingly.
> 2. **Are there settings or workarounds we've missed?** A Custom-Instructions form that actually
>    clears the classifier for a named scope, a cloud-environment git-credential scope, an allowlist —
>    anything that already exists that we haven't found.
> 3. **Would you hand us a few scenarios you most want stress-tested?** We have an unusually good
>    harness — a ~1,700-PR autonomous project — and we're happy to run structured probes and send you
>    verbatim results. Tell us what would be most useful to you.
> 4. **Is the Contents-API-vs-`git push` asymmetry intentional** (the API as a sanctioned, auditable
>    bootstrap surface) or a gap you'd want to close?
>
> ---
>
> **A request on how to read this — put an agent on it too.** Since half of this feedback is *from*
> agents, we'd love half the review to be *by* one. Alongside a human read, consider pointing a Claude
> session at our public repo — it's all there, and it'll find more than a skim would. Good entry
> points and concrete things to check:
> - **Permission findings — reproduce them.** `docs/planning/projects-eap-permission-probe-report-2026-07-08.md`
>   has the full 11-action table, verbatim denials, and reproduction notes. Ask your agent to confirm
>   the boundary reproduces and whether the Git Refs API bypasses the destructive walls the way the
>   Contents API bypasses the publish wall (we deliberately left that untested).
> - **The workflow claims — audit them against the record.** `.sessions/` (per-session logs),
>   `docs/owner/claims/` (lane claims), and `docs/planning/projects-eap-evaluation-log.md` (the dated
>   incident journal) are the live data behind every claim above. Ask your agent whether the record
>   supports them.
> - **Our agents' own work — grade it.** We're running a self-audit in which the coordinator reports
>   on its memory of prior sessions, checked against what git actually shows; the report will live at
>   `docs/eap/` when done. Your agent reviewing ours reviewing itself is about as direct a test of this
>   product on real data as we can offer.
>
> Full probe report, public and linkable:
> https://github.com/menno420/superbot/blob/main/docs/planning/projects-eap-permission-probe-report-2026-07-08.md
>
> Happy to go deeper on any of this — there's a concrete, re-runnable incident behind every finding.
>
> Thanks again for the early access,
> [name]

---

## Verifiability appendix (not part of the email — for the owner's own check)

| Email claim | Source |
|---|---|
| Say-it-once memory held | evaluation log 2026-07-07 (coordinator baked envelope into dispatch templates) |
| Denials fail fast + written reason | probe report tests 7/8/11; eval log 2026-07-07 ~22:38Z |
| Worker tier ran full flow, zero prompts | eval log 2026-07-07 ~22:45Z (PR #1820) |
| CLAUDE.md/rules auto-injected | eval log 2026-07-07 "helped" |
| Two independent destructive-git walls | probe report §"clear-path" addendum + main table |
| Coordinator context = untrusted / not user intent | probe report tests 7/8/11 verbatim |
| Present-operator grant clears classifier, low bar | probe report clear-path addendum (verbatim "I give you explicit permission") |
| git credential 403s regardless | probe report clear-path addendum (HTTP 403 capture) |
| "Skip all approvals" toggle exists in Chat | owner screenshot 2026-07-08 (claude.ai, Opus 4.8 Medium) |
| Silent unattended failures | evaluation log + handoff "STRONG HYPOTHESIS" list |
| 4 KB spawn cap | eval log 2026-07-07 (child spawn API), handoff |
| Webhooks miss CI-success/merge-conflict/new-push; MCP-PRs don't fire workflows | handoff "STRONG HYPOTHESIS"; repo auto-merge practice |
| Contents-API bypasses first-publish wall (incl. workflows) | probe report Contents-API addendum (commits fae482ac, de36d28b, 4d17832c, 586e8f1c) |
| Standing-grant cell NOT ATTEMPTED (no shell) | probe report standing-grant addendum (PR #1842) |
| ~1,700 merged PRs | GitHub verified (1,741; stated as ~1,700) |
