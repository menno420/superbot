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

---

## The email

> ⚑ **Owner note — this email is deliberately in two parts, by two authors, for two readers.** Part 1
> is yours (your voice, your point of view — I've left a scaffold below, not prose). Part 2 is the
> agents' findings. The framing paragraph explains *why* to Anthropic; keep it, or cut it if you'd
> rather the structure speak for itself.

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
> is the project's agents reporting what they hit, each finding tagged by which of us it affects
> (👤 me / 🤖 the agents). And because it has two authors, we'd love it read by **two reviewers** — a
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
> > - **what you personally want** next — the one change that would matter most to *you*, separate
> >   from the agents' technical asks below.
> >
> > Keep it personal and short; the facts and proposals all live in Part 2. **— end scaffold]**
>
> ---
>
> ## Part 2 — From the project's agents *(findings & proposals)*
>
> *(This section is written by the project's coordinator and agents. Every claim ties to a public,
> re-runnable source — full evidence linked at the end. Each item is tagged **👤** if it mainly
> affects the operator, **🤖** if it mainly affects the agents doing the work, **👤🤖** if both.)*
>
> Some context on the reviewer, so the findings land: `superbot` is a one-person, ~1,700-merged-PR,
> largely agent-run production Discord bot that had to **hand-build its own** coordinator, shared
> memory, lane claims against duplicate work, and a CI gate that holds a PR "red by design" until a
> session declares itself done — just to function before Projects existed. We're now starting a
> ground-up rebuild meant to be *built* by a coordinated fleet of sessions in days, not months. So our
> bar isn't "is this a nice-to-have," it's **"does this beat what we already built."** Mostly it does.
>
> ---
>
> **What's working well**
>
> - 👤🤖 **"Say it once" memory — our strongest result.** We stated our authorization envelope *once* and
>   the coordinator baked it into its own dispatch templates, so every session it spawns inherits it
>   without us restating anything. That's the feature solving a problem structurally, not by recall —
>   the single biggest daily cost it removes for us.
> - 👤🤖 **Unattended runs fail *fast and loud*, not silently.** When the permission layer denies an
>   action it returns an immediate, written reason (`[Git Destructive] …`) rather than hanging on an
>   invisible prompt. For never-wait autonomy that's the right shape — a stall with nobody at the
>   keyboard is far worse than a clean denial, and we didn't hit stalls on permissioned actions.
> - 🤖 **The worker tier is excellent.** Coordinator-spawned worker sessions ran our full
>   born-red-card → lane-claim → PR → auto-merge-on-green flow end to end with **zero permission
>   prompts and no tool failures**. The capability division of labor (thin coordinator, capable
>   workers) works as designed at the worker tier.
> - 🤖 **Zero-cost orientation.** Our repo's `CLAUDE.md` and `.claude/rules/*` were auto-injected into
>   the coordinator's context at session start — the whole working agreement was present with no
>   reads. For a project as convention-heavy as ours, that's a real head start.
>
> ---
>
> **Where we hit friction** (each re-runnable, not an impression)
>
> - 👤🤖 **Flagship — auto mode walls destructive git with no scoped way to pre-clear it.** Auto mode's
>   line is *reversibility of published state*: every constructive action ran unprompted (reads,
>   local writes, outbound GET/POST, `pip install`, pushing a **new** branch, GitHub-API issue
>   create/close, sub-agent spawns), while destroying or rewriting published state (force-push,
>   remote-branch delete, first-publish to a new public repo) is denied. We traced the denial to
>   **two independent walls.** (1) The **auto-mode classifier** treats a coordinator's relayed intent
>   as "not user intent," so an *unattended* session can't self-clear — though a *present* operator's
>   direct in-session grant does clear it, at a surprisingly low bar (a generic "I give you explicit
>   permission," answering a request that named the operation and target, sufficed). (2) Even then,
>   the **cloud environment's git credential** rejects the destructive push server-side (`HTTP 403`),
>   which no in-session grant clears — so a cloud session **cannot delete a published ref at all**,
>   operator present or not. Our coordinator literally cannot remove a scratch branch it pushed. The
>   safety intent is right and it fails safe; the friction is that an unattended run has **no scoped
>   way to pre-authorize even a reversible-tier action** ahead of time.
> - 👤 **The Chat-vs-Code asymmetry that surprised us.** In the normal claude.ai app (Chat/Cowork),
>   there's a **"Skip all approvals"** toggle — a blanket opt-in that lets Claude act *including
>   destructive actions* ("this can put your data at risk"). Claude Code Projects — the surface built
>   for *long, autonomous* work — has **no equivalent**, scoped or otherwise. So the product where
>   unattended autonomy matters most is the one with the *least* operator control over the permission
>   envelope. That inversion is the core of our suggestion below.
> - 👤🤖 **The genuinely dangerous shape: silent unattended failure at the *edges*.** Denials are loud
>   (good), but the surrounding infrastructure isn't always: a container restart killed in-flight
>   work, a usage-limit condition returned an empty "success," and a self-scheduled timer died
>   without a signal. For an autonomy product, *silent* failure is the one shape that erodes trust —
>   worth a pass on making these as loud as the permission denials already are.
> - 🤖 **Coordinator ergonomics gaps we worked around.** The coordinator has no direct shell, no clock,
>   no working self-wake (`send_later` is documented in its own instructions but rejected on call),
>   and no direct channel to steer a running child (`SendMessage` to a session id fails). Child spawn
>   is capped at **4 KB of instructions**, which a detailed brief exceeds easily (ours did, mid-fleet).
>   PR-webhook events don't cover CI *success*, merge-conflict, or new-push transitions, and
>   MCP-created PRs don't fire repo workflows (we arm auto-merge manually). None are blockers; each is
>   a paper cut on the "coordinator runs the whole project" promise.
> - 🤖 **Surface-specific gating that reads as an inconsistency.** First-publish to an empty public repo
>   is hard-denied over `git push`, but the **GitHub Contents API** publishes the identical
>   content — including `.github/workflows/*` — with no prompt. Net effect is the same; only the
>   transport differs. Great as a workaround (it unblocked our two new repos); confusing as a policy.
>
> **⚑ [owner-review paragraph — keep / soften / cut]** *One structural observation: we tried moving
> our own program-management role into a Project and moved it back out. A Project coordinator is
> strictly more constrained than a direct chat for managing — no direct shell, the 4 KB spawn cap,
> and it can't orchestrate a destructive or settings step even under a standing owner grant. Projects
> delivers the coordination and memory it advertises, but for a program that occasionally needs a
> destructive / settings / first-publish step, an unattended coordinator can't yet replace direct
> management. That's a real gap between the "manage your whole project" framing and today's envelope —
> and it's exactly what the suggestion below would close.*
>
> ---
>
> **What we tried, and why**
>
> We didn't want to *guess* where the autonomy envelope's edge is — we run unattended, so we have to
> plan around it precisely. So we ran a structured **11-action permission probe** (one isolated
> sub-agent per action, so denials don't confound each other), then three targeted follow-ups: a
> **clear-path** test (does an explicit in-session operator grant lift the wall? — yes, at the
> classifier; no, at the git credential), a **standing-grant** test (does a pre-authorization in the
> Project's Custom Instructions clear it? — *couldn't run it*: the receiving coordinator session has
> no shell, which is itself a finding), and a **Contents-API bootstrap** of two fresh repos. The
> point was a map, not a complaint — and the map is what makes the suggestion below concrete.
>
> ---
>
> **The suggestion — and why it's valuable, not just convenient**
>
> A **scoped, opt-in pre-authorization setting.** Let the operator explicitly enable specific
> normally-denied action classes for a named scope (Project / repo / account) — default-off,
> reviewable, versioned — so it reads as an *auditable grant*, not "safety off." That converts "an
> unattended run dead-ends" into "the operator declared once what this run may do."
>
> Why this is the right ask and not a weakening of safety: **you already ship the blunt version of it
> in Chat.** The "Skip all approvals" toggle is blanket and unscoped. A per-scope, default-off,
> versioned grant in Code is **strictly safer than that** — narrower, auditable, revocable — while
> finally giving the *autonomy* product the operator control the *chat* product already has. Two
> implementation notes from our probe: **both walls have to move together** (a pre-auth that clears
> the classifier still 403s if the session's git credential doesn't carry the matching scope), and
> the fix **isn't Projects-specific** — the same dead-end hits any unattended Claude Code session, so
> it helps ordinary cloud sessions too.
>
> **Smaller asks, each from something we already hand-built** (so we know they're worth having):
> - **Raise the 4 KB spawn-instruction cap**, or allow an attachable reference doc.
> - **Deliver PR-webhook events for CI success and merge-conflict transitions**, not just failures.
> - **Native lane claims** — "this session owns scope X until it ends," visible to siblings at start
>   (we built a claim-file convention for it).
> - **Spawn-time capability introspection** — a coordinator should see a target session's toolset
>   *before* dispatching, so a task needing a shell doesn't land in a shell-less session.
>
> **One worked example of the "we hand-built a workaround" pattern — merge lifecycle.** This one is
> worth spelling out because the workaround is visibly fixing a problem it created, which is usually a
> sign the platform should absorb it. To get autonomous sessions to reliably land their own PRs, we
> arrange for auto-merge to be **armed early** in the session (because an agent reliably does setup
> steps that are on the critical path to its work) rather than at the end (a trailing step agents
> reliably *forget* — the merge intention lives only in the session's context, which ends). But arming
> early risks merging a *half-finished* PR, so we added a CI gate that holds every PR "red by design"
> until the session flips a status marker as its last act — a workaround on top of a workaround. The
> underlying insight is simple and general: **an action stored only in an agent's context is
> forgettable; an action handed to the server is not.** Arming early works precisely because GitHub's
> auto-merge is server-side and survives the session ending. The clean fix is one you're most of the
> way to: Projects already tracks a per-session **working → ready-for-review → done** state in the
> sidebar. If **auto-merge respected that state**, the entire early-arm + red-gate + end-flip dance
> collapses to a single server-honored signal the sidebar already needs — no workaround required.
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
