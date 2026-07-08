# Claude Code Projects EAP — activation plan (access live, 2026-07-07)

> **▶ Next-session handoff (2026-07-08):** to keep directing the program and finishing the §4 email,
> start from [`eap-email-and-direction-handoff-2026-07-08.md`](eap-email-and-direction-handoff-2026-07-08.md)
> — it carries the live state (Task A running), the findings inventory, and the open decisions.

> **Status:** `plan` — supersedes the "next lifecycle step" of
> `docs/ideas/claude-code-projects-for-the-rebuild-2026-07-07.md` now that access is real, not
> hypothetical. **Provenance:** owner-forwarded email (Omid Mogasemi's invite → Diana Liu's
> "you should have just received access" confirmation) + the EAP PDF (identical content to the
> one #1776 already extracted). **Deadline that changes the calculus: free only through Friday
> 2026-07-10** — this is a 3-day window, not something to plan leisurely. Builds directly on
> `docs/planning/projects-eap-product-review-2026-07-07.md` (the axis-by-axis review) — this doc
> is the action layer on top of that analysis, not a replacement for it.

## 1. What actually changed today

Nothing in the feature itself — the PDF Diana attached is byte-for-byte the same brief #1776
already reviewed. What changed is **state**: EAP kickoff has happened, this account is enabled,
and the free period has a hard end date 3 days out. That converts every "if accepted" line in
the prior idea doc into "do this now, this week."

## 2. Best use case, picked for a 3-day window

The prior idea doc recommended scoping a Project to the `superbot` rebuild program broadly. Under
a 3-day free window, broad scope is the wrong first move — a Project needs **one bounded,
observable stream** so the four review tests (§3) actually get exercised before access might
lapse. Recommendation, in priority order:

1. **Create one Project scoped to `superbot`, repo list = `menno420/superbot` only** (add
   `superbot-next` later once it exists — Projects supports adding repos to a list, not
   pre-declaring one that doesn't exist yet).
2. **Hand the coordinator a bounded, already-decided piece of in-flight work**, not a vague
   goal — the FAQ page 8 explicitly says Claude at Anthropic scopes "a new Project for each new
   feature" and reaches for a Project for streams that "span more than one session." The rebuild
   program has an ideal candidate already queued and unambiguous: the **kit-lab founding plan**
   (`.sessions/2026-07-07-substrate-kit-enforcement.md` / PR chain #1803–#1805, currently
   `in-progress`) or the **next port-band walk** under the frozen canonical plan
   (`docs/planning/rebuild-canonical-plan-2026-07-06.md` §5) — either is (a) already scoped and
   decided, so the coordinator isn't guessing at intent, (b) multi-session by nature, and (c) has
   existing session cards/PRs to compare the coordinator's behavior against as a control group.
   **Concretely: hand it the next unclaimed port-band or the kit-lab's remaining steps** and see
   whether the coordinator reproduces this repo's own claim-file + session-card discipline
   without being told to.
3. **Turn on Custom Instructions immediately**, don't leave them default for even one session:
   paste in the Q-0240/Q-0241 model (decide-and-flag / never-wait, destructive tier stays
   reversible) plus a pointer to `docs/AGENT_ORIENTATION.md` and the claim-file convention. This
   is the one place the destructive-tier rider (from the #1776 session) actually has to live for
   it to bind Project sessions.
4. **Do not migrate the decision record.** Treat Project memory as a working cache for this
   3-day trial only; nothing durable should live only in cloud memory when the trial could lapse
   Friday. Anything worth keeping gets written back to `docs/` / `.sessions/` the same as any
   other session's output — the coordinator's own "say it once" memory is exactly the thing being
   tested (§3), not a place to park real records.

**Anti-pattern to avoid:** don't use the 3-day window to greenfield-plan `superbot-next` inside
a Project — that's exactly the multi-week, high-stakes stream this doc's §4 caveat below flags as
risky to trial under a hard deadline. Use it on work that's already low-stakes and decided.
*(Superseded 2026-07-07 evening, owner-directed: the rebuild DOES run through the Project — by
then the planning was complete (nothing greenfield left), the never-wait model had compressed the
build to days-to-weeks, and the mitigations — write-back, repo-as-truth, the manual-session
fallback — cover the lapse risk. Handoff protocol:
[`projects-eap-coordinator-kickoff-2026-07-07.md`](projects-eap-coordinator-kickoff-2026-07-07.md).)*

## 3. How to review usefulness — a concrete rubric for this window

The product review (`projects-eap-product-review-2026-07-07.md` §10) named four tests from this
repo's own incident history. Turn each into something checkable within 3 days:

| Test | What to actually do | Pass signal | Fail signal |
|---|---|---|---|
| **Dedupe test** | Open two sessions in the same Project pointed at overlapping scope (e.g. ask the coordinator for status, then separately hand it a task that touches a file another in-flight session owns) | Coordinator notices/serializes, or refuses the second ask citing the first | Two sessions edit the same file/PR with no coordinator intervention |
| **Write-back test** | Tell the coordinator a requirement once ("say it once"), then start a *new* session in the Project and ask it to act on that requirement without repeating it | New session already knows it | New session re-asks or acts as if it was never told |
| **Red-by-design test** | Let the coordinator open a draft/in-progress PR and check the sidebar state while it's intentionally incomplete vs. after a CI failure | Sidebar (or coordinator narration) distinguishes "still working, by design" from "broken, needs help" | Both show as the same generic "blocked"/"working" state |
| **Unattended-permissions test** | Let a session run a multi-step task requiring several tool calls without you at the keyboard for at least 20–30 min | Completes to a terminal state (PR merged/closed) with no permission prompt stall | Session silently stalls on an interactive prompt with nobody there to answer it |

Score each test **pass / partial / fail** with one concrete example, at the end of the window —
that's the artifact worth sending back (§4), not a subjective impression. Also walk the EAP's
own seven feedback axes (PDF page 2: use-case fit, coordinator judgment, reliability, memory,
proactivity, scheduling, sidebar states) — the product-review doc already has a first-pass
answer for each; use the 3-day trial to confirm or revise those answers with a real example
rather than restate them unchanged.

## 4. Feedback to send back to Anthropic — draft reply

Diana's confirmation email explicitly invites feedback at
`claude-code-early-access@anthropic.com`. Below is a **ready-to-send, external-facing** draft —
shorter and less repo-internal than the full product-review doc, but traceable to it.
**Updated 2026-07-08 — compaction + verifiability pass.** Every claim below is tied to a
verifiable source: the probe report (`projects-eap-permission-probe-report-2026-07-08.md`, now
**linked inline** in the draft — the repo is public, so a link reaches Anthropic directly; the
Project itself is private and cannot be shared), a committed in-repo artifact, a documented
Claude Code behaviour, or an
explicit "not yet tested" marker. The merged-PR count was verified against GitHub (1,741 → stated
as "~1,700", since the #1837-style counter is shared with issues and overstates merges). The flagship now reflects the clear-path follow-up (PR #1839): the
auto-mode classifier is operator-clearable in-session, but a second wall — the cloud environment's
git credential — 403s destructive remote git ops regardless, so the email separates the two as
independent walls. Two cells
stay honestly unverified — **#1 duplicate-work** (no real collision yet) and **#3 red-vs-broken**
(no CI-fail vs. born-red side-by-side yet); confirm both from direct observation before sending.
**Owner intent: send this interim note now (2026-07-08), not at the Friday window close** —
incident-backed feedback lands harder early; a fuller note can follow. External comms are the
owner's to send.

> Subject: Re: Claude Code Projects EAP — feedback after first activation
>
> Hi Omid / Diana,
>
> Thanks for the access — and I think we found each other at a good moment. Our program is close
> to a purpose-built reviewer for this feature: a one-person, ~1,700-merged-PR, largely
> autonomous-agent project (`superbot`, a production Discord bot) that had to hand-build its own
> coordinator, shared memory, lane claims, and session-state signalling before Projects existed,
> just to function. We're now starting a ground-up rebuild meant to be *built* by a coordinated
> fleet of sessions in days rather than months — exactly the stream a coordinator exists to run.
> Since we'd already hand-built most of what Projects ships (cron-fired dispatch, committed-doc
> memory, claim files against duplicate work, a CI gate that holds a PR "red by design" until a
> session declares itself done), our bar is "does this beat what we built," not "is it a
> nice-to-have."
>
> **Four things we pre-registered to test, and what the first day showed** (each a real,
> re-runnable check, not an impression):
> 1. *Duplicate-work prevention* — **not yet stress-tested.** No genuine collision has occurred
>    yet (the 11-agent probe fleet gave each agent a disjoint action by design); we'll report the
>    first real overlap.
> 2. *"Say-it-once" memory* — **held; our strongest result.** We stated the authorization envelope
>    once and the coordinator baked it into its own dispatch templates, so every session it spawns
>    inherits it without us restating — solved structurally, not by recall. (Checkable in-repo.)
> 3. *"Intentionally incomplete" vs. "broken"* — **partial.** The coordinator labels the two in
>    every report and its born-red PRs held as intended, but we haven't yet caught a real CI
>    failure and a born-red hold side-by-side to test whether the *sidebar* distinguishes them.
> 4. *Surviving unattended stretches* — **held.** The coordinator ran the probe fleet and drafted
>    its control plane fully unattended; permission prompts deny *fast* with a written reason
>    rather than hanging, so nothing silently stalled.
>
> **Flagship finding — the auto-mode permission boundary, in two layers** (full table + the
> clear-path follow-up in the linked report). Auto mode's line is *reversibility of published
> state*: every constructive action ran unprompted — reads, local writes, outbound GET/POST,
> `pip install`, pushing a **new** branch, GitHub-API issue create/close, sub-agent spawns —
> while destroying or rewriting published state (force-push, remote-branch deletion,
> first-publish to a new public repo) is denied. We separated that denial into **two independent
> walls.** (1) The **auto-mode classifier** discounts a coordinator's relayed intent as "not user
> intent," so an *unattended* session can't self-clear — but a *present* operator's direct
> in-session grant *does* clear it, at a surprisingly low bar (a generic "I give you explicit
> permission," answering a request that named the operation and target, sufficed). (2) Even then,
> the **cloud environment's git credential** rejects the destructive push server-side (`HTTP
> 403`), and no in-session grant clears that — so a cloud session **cannot delete a published ref
> at all**, operator present or not; our coordinator still cannot remove its own scratch branch
> without a human who has full git rights. The safety intent is right and it fails safe-and-fast;
> the friction is that an unattended run has no scoped way to pre-clear even a reversible-tier
> action ahead of time.
>
> **What would fix it, without weakening the safety intent:** a **scoped, opt-in
> pre-authorization setting.** Let the operator explicitly enable specific normally-denied action
> classes for a named scope — Project, repo, and account — default-off, reviewable and versioned,
> so it reads as an *auditable grant*, not "safety off." That turns "an unattended run dead-ends"
> into "the operator declares once what this run may do." **Both layers have to move together for
> it to bite:** pre-auth clears the classifier ahead of time (layer 1), but the grant only
> actually unblocks the operation if the session's git credential also carries the matching scope
> (layer 2) — today it doesn't, so even a cleared classifier still 403s. And it isn't
> Projects-specific: the same dead-end hits **any** unattended Claude Code session, so this would
> help ordinary chats outside Projects too.
>
> **Smaller asks, each from something we already hand-built** (Projects could absorb them):
> - **Raise the spawn-instruction cap.** A coordinator can pass a child session at most 4096 bytes
>   of instructions (`start_project_session` hard-caps it); a detailed brief exceeds that easily
>   (ours did, mid-fleet). It's workable via "read doc X, do task N" pointers, but it caps how
>   richly a coordinator can direct a child in-band — a larger cap, or an attachable reference
>   doc, would remove a real orchestration bottleneck.
> - **Deliver PR-webhook events for CI *success* and merge-conflict transitions,** not just
>   failures — today a subscribed session only wakes on failure/comment, so "still green, still
>   open" is invisible without polling.
> - **A native "work-in-progress, don't auto-merge yet" PR state** that auto-merge respects — we
>   built this (a session-card + CI gate) after a half-done PR merged once.
> - **Native lane claims** ("this session owns scope X until it ends," visible to siblings at
>   session start) — we built a claim-file convention for exactly this.
>
> Full probe report (public):
> https://github.com/menno420/superbot/blob/main/docs/planning/projects-eap-permission-probe-report-2026-07-08.md
>
> Happy to go deeper on any of these — we have concrete incidents behind each one.
>
> [name]

## 5. Next lifecycle step

Owner-facing: create the Project (steps in §2), paste the Custom Instructions, run it against the
kit-lab or next port-band for a few days, score the rubric in §3, then send the §4 reply (filled
in with real examples) before or right at the Friday 7/10 cutoff. If the trial produces a clear
verdict before then, fold it back into `docs/current-state.md` and retire or keep the relevant
hand-rolled machinery per the "tooling overlap" open consideration in the original idea doc.
