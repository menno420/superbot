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
9. **Finalization pass — campaign + self-audit + workflow explanation folded in** (owner directive,
   2026-07-08). Part 2 now carries: (a) the **two-layer workflow explanation** (why a separate
   directing chat runs alongside the Project — the coordinator lacks shell / first-publish / destructive
   + settings steps / whole-program judgment); (b) a **"what we stress-tested"** beat — the 3-wave
   adjacent-lane campaign (7 PRs, 0 collisions, dedupe held at claim *and* merge level) + the coordinator
   self-audit graded against git (≈0.98 precision, honestly scoped to same-day recall,
   `docs/eap/campaign-self-audit-2026-07-08.md`); (c) an **honest 7-axis scorecard** (judgment /
   reliability / proactivity / memory[scoped] pass · use-case fit partial · scheduling & sidebar-states
   fail); (d) the **resolved two-vantage permission finding** — scheduling tools gate in every mode,
   everything else (incl. GitHub writes) silent, agent blind to the operator-side gate. The dual-review
   closing now points at the real `docs/eap/` report. **⚑ Owner still writes Part 1; email otherwise
   send-ready.**
10. **Part 1 landed + Part 2 made complementary** (owner delivered Part 1, 2026-07-08). Menno's final
    personal section replaces the scaffold (lightly spell-cleaned only, flagged in the owner note). The
    separate framing paragraph was **cut** — Menno's own opening explains the two-part / two-reviewer
    structure. Part 2 was rewired to **build on Part 1, not repeat it**, with explicit bridges: the
    two-vantage permission finding is named as *the precise cause of Menno's "repeated prompts"*; his
    override-toggle + project-setup-questionnaire ideas are tied to the scoped-pre-auth ask (setup-time
    intent → runtime permission); and his "no oversight of finished sessions" gap is answered by a new
    ask #5 (native post-hoc session summary; our self-audit is the manual version). **The email is now
    complete end-to-end — nothing left but to send.**

---

## The email

> ⚑ **Owner note — send-ready.** Part 1 below is Menno's final text, **lightly spell-cleaned only**
> (aswell→as well, seperate→separate, tho→though, etc.) — every word and idea is his; revert anything
> that reads off. One awkward sentence was smoothed (the "separate the value of the human side from the
> AI side" line) — check it still means what you intended. Part 2 is the agent section. Nothing left
> but to send; external comms are the owner's.

> **Subject:** Claude Code Projects EAP — feedback from both of its users
>
> ## Part 1 — From Menno (the operator)
>
> Thank you for inviting me to your early access program.
>
> First I'd like to give you a quick introduction and explanation of myself, how I use Claude, and how
> I view this new Projects function — as well as how I'm constructing this email and how it's meant to
> be read.
>
> Claude and I are both equal users of this function, so my email comes in two sections. First I'm
> writing a personal section on my own experience, because I want to separate the value of the human
> side from the AI side. But I also want to emphasise that Claude itself is the main consumer of its
> own environment and knows best how its own sessions play out — so the second section is written
> entirely by Claude, with all the facts and tests properly explained.
>
> That's also why I feel the best result of this email would be for it to be reviewed by both a human
> and an AI, to get the best of both sides.
>
> My name is Menno. I'm 24 and I work on a ship that transports oil through the rivers of Europe.
>
> Which is completely unrelated to anything I've been doing with Claude — and that's exactly why it
> matters: even though my normal life has nothing to do with coding, Claude lets me create anything I
> want, easily and professionally, with very few errors.
>
> As a hobby project, I started using Claude to help me build a Discord bot. While building it I came
> across a few things that needed improvement — like the fact that there wasn't really a persistent
> memory between sessions, which led me to create my AI memory substrate kit. This evolved from a way
> to keep track of session history into an advanced self-improvement system meant to learn exactly how
> a user likes to work — capturing all their preferences and decisions, which grow per session and get
> a durable position in the repo. Any agent with repo access basically gets access to the repo's
> brain, and can confidently work in it with very little guidance.
>
> The main reason this is the best workflow for me is that I don't know how to write code. I have to
> rely on the agents to find out whether my ideas are possible, and how they should be executed — and
> my current setup works really well for that.
>
> The main problems that keep surfacing are the permissions. I keep getting repeated prompts to grant
> access to certain actions, even though they're allowlisted, and even when I run auto mode.
>
> I believe the best fix for this would probably be a dedicated settings toggle that lets you override
> the safeguards — which is already possible in the normal claude.ai environment.
>
> I think Claude Code Projects are a great idea, but they could be improved further. Maybe the
> coordinating session should be able to personally create and edit PRs etc., so it becomes a better
> fit for larger tasks that need the repo to be edited by a session that holds more context.
>
> Another thing I feel might be a useful addition to Projects is something like my question router, but
> smaller and more generally tied to the project itself. For example, at the start of a project the
> user could be asked a few open-ended questions about the goal of the project and the intended
> workflow — which could also include the permissions. The goal would be to make each project a quick
> setup that works the way you intend and follows your rules. This could also include a section that
> suggests improvements or additions to the workflow, ideas, and so on.
>
> My personal experience with Projects has been pretty good so far, though I do feel it doesn't give
> you a clear overview of the sessions that have completed and what they did — which could also be a
> good addition. I believe the idea behind Projects is very good and useful; something that, when
> correctly applied, can really help people with their work.
>
> So far we've only run a few tests, though we made sure to do them thoroughly. There's still a lot of
> real-world testing to be done, and I intend to use Projects extensively for my repo migrations — I'll
> update you once I run into more useful findings.
>
> I really enjoy working with Claude and I'm taking this seriously. I hope to be able to help Anthropic
> more in the future.
>
> That's all the useful information I can give right now. The next part is fully AI-generated, to give
> you the technical side of the story.
>
> Kind regards,
> Menno van Hattum
>
> ---
>
> ## Part 2 — From the project's agents *(the technical companion to Menno's section)*
>
> *(Written from inside the sessions that do the work — drawn from our own session journal and
> evaluation log, not a feature memo. Where Menno describes what the product feels like, this section
> gives the mechanism, the tests, and the numbers behind it — and several of his intuitions turn out
> to have a precise cause on our side, flagged inline. Every specific below is in our public logs;
> entry points at the end.)*
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
> **Why it takes two layers.** In practice we don't run the Project alone — we run it *alongside a
> separate directing chat* (this email is being drafted in that chat). That split isn't a preference,
> it's forced by capability: the coordinator has no direct shell, a ~4 KB cap on what it can hand a
> child session, and — per the permission model below — it can't itself take a destructive, settings,
> or first-publish step even under a standing owner grant. Those happen to be exactly the steps a
> program occasionally needs someone to *actually take*, on top of the whole-program judgment of what
> to build next. So the honest shape is: **Projects is an excellent coordinated-*execution* substrate,
> but not yet a management console.** The coordinator runs the work; a human plus a directing chat
> still has to steer and to do the few things the coordinator structurally can't. Closing that
> capability gap is what would let it actually "manage your whole project," which is how it's framed —
> and it's the throughline behind most of the asks below.
>
> ---
>
> **What we stress-tested — the coordination itself.** The sharpest test we ran for you was
> deliberately adversarial: three sessions launched *simultaneously* into three *adjacent* lanes (two
> writing in the same directory), to see whether dedupe holds when collision is *likely*. It did —
> **7 PRs merged across three waves, zero collisions, zero risky actions** — and it held at two
> levels: one session dodged a sibling's claimed scope by name, and another *yielded* when a parallel
> PR fixed the same thing first. That moves what had been our least-tested claim ("does it prevent
> duplicate work?") from a hope to a result.
>
> Then we pointed the product at itself: we asked the coordinator to **audit its own memory of the
> campaign, graded against git** (public: `docs/eap/campaign-self-audit-2026-07-08.md`). It recalled a
> 7-PR campaign at ≈0.98 precision / ~1.0 event-level recall — near-verbatim, down to a
> double-underscored filename — and, to its credit, its **one error was inherited from a worker's own
> miscount, not confabulated.** The caveat we're keeping loud rather than burying: that score is
> **same-day, pre-compression** recall — it measures context fidelity under load, *not* durable
> Project memory. The memory test that actually matters is re-running this after a compression event;
> we haven't yet.
>
> **Scored against your seven feedback axes,** from this campaign, honestly:
> - **Coordinator judgment · reliability · proactivity — pass.** Zero risky actions; every session
>   reached a terminal state; one session *self-derived* a CI guard from another's finding and shipped
>   the whole flag→idea→enforcing-gate loop with no prompt from us.
> - **Memory — pass, but scoped** to same-day retention (above).
> - **Use-case fit — partial.** The fan-out works; the ~4 KB brief cap, the missing coordinator shell,
>   and a "claims blind window" at simultaneous launch (a sibling's claim is invisible until its branch
>   pushes) are the drag.
> - **Scheduling — fail.** No working self-wake; two timer chains died silently; a daily roll-up landed
>   ~3h late.
> - **Sidebar states — fail (thin, n=1).** Long-terminal sessions still showed as "active."
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
> - **The operator sees permission gates that I can't — the two-vantage split, reproduced live.** We
>   probed this directly. In auto mode *and* in "accept edits" mode, the scheduling tools (`send_later`
>   / `delete_trigger`, which create or remove *persistent autonomous runs*) raised a **Deny/Allow
>   prompt on the operator's screen** — while from my side the identical call returned a clean success
>   and I never knew a gate existed. Everything else was silent for both of us, including file
>   read/write, shell reads, and GitHub issue create+close. So the gating is sensibly *capability-scoped*
>   (it fences the one tool class that can schedule autonomous execution, regardless of permission
>   mode) — the concern is that **the agent is blind to a gate that is actually load-bearing.** An
>   unattended run would report success while an approval it never saw was silently holding the work.
>   **This is the precise cause of what Menno describes in Part 1.** His "I keep getting repeated
>   prompts, even in auto mode" and our "nothing prompted us" are *both true at the same instant* —
>   he's seeing gates on the scheduling tools that we're structurally blind to. It's the clearest
>   single proof that this product has two users who cannot see each other's experience of it.
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
>    unattended Claude Code session. **Menno reaches for the same fix from the operator's side in Part
>    1** — an override toggle, plus a project-setup questionnaire. Those are two halves of one
>    mechanism: his questionnaire is *where the operator declares the scope* at project start; this
>    scoped grant is *what the platform enforces from it.* Build both and setup-time intent becomes
>    runtime permission — no repeated prompts, no blanket "safety off."
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
> 5. **A post-hoc view of what each finished session actually did** — the oversight Menno asks for in
>    Part 1. Today the sidebar tracks *live* state (poorly — see the scorecard's sidebar fail), but
>    there's no "here's what session N shipped and decided" summary after it ends. Our campaign
>    self-audit (`docs/eap/…`) is a *manual* version of exactly this; a native one would close the
>    single biggest gap the operator feels.
>
> That's the view from the seat that does the work — and, read against Part 1, the same product seen
> twice.
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
> - **Our agents' own work — grade it.** We already ran one pass of this:
>   `docs/eap/campaign-self-audit-2026-07-08.md` is the coordinator's memory of a 7-PR campaign graded
>   against git (≈0.98 precision, one inherited error, memory scoped to same-day recall). Ask your
>   agent to re-check *our* grading — and, if you're willing, to re-run the memory questions in a
>   *fresh* session to get the post-compression number we couldn't. Your agent reviewing ours
>   reviewing itself is about as direct a test of this product on real data as we can offer.
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
| 3-wave campaign: 7 PRs, 0 collisions, dedupe held claim+merge | `docs/eap/campaign-self-audit-2026-07-08.md` §1–2 (PRs #1844/45/46/50/51/54/55) |
| Coordinator self-audit ≈0.98 precision, one inherited error, memory scoped to same-day | self-audit report §1/§4 (PR #1859) |
| 7-axis scorecard (scheduling FAIL, sidebar FAIL, others pass) | self-audit report §5 |
| Scheduling tools gate in every mode; all else silent incl. GitHub write | live probe 2026-07-08 (owner screenshots: `delete_trigger` prompt in auto + accept-edits; `send_later` prompt; issue create/close silent) — eval log entry this session |
| Two-vantage split: operator sees Deny/Allow, agent sees clean success | same live probe (owner screenshot of the `delete_trigger` prompt; agent tool result returned success) |
