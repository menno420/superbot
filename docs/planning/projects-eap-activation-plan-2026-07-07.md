# Claude Code Projects EAP — activation plan (access live, 2026-07-07)

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
shorter and less repo-internal than the full product-review doc, but traceable to it. Fill in
the bracketed examples from what actually happened — the coordinator's evaluation journal
([guidebook](projects-eap-evaluation-guidebook-2026-07-07.md) §2/§5) feeds them. **Owner
intent (2026-07-07 evening): send ~tomorrow, after first real coordinator use** — interim,
incident-backed feedback beats waiting for the Friday deadline; a second, fuller note can
follow at the window close.

> Subject: Re: Claude Code Projects EAP — feedback after first activation
>
> Hi Omid / Diana,
>
> Thanks for the access — and honestly, I think we found each other at quite a good moment.
> Our project is built in a way that makes it close to a purpose-built reviewer for exactly
> this feature: a one-person, ~1,800-merged-PR, largely autonomous-agent program (`superbot`,
> a production Discord bot) that had to hand-build a coordinator, shared memory, lane claims,
> and session-state signalling before Projects existed, just to function at all. And Projects
> lands at the perfect time for us too — we're starting a ground-up rebuild across two repos,
> planned in about three days and meant to be *built* by a coordinated fleet of sessions in
> days rather than months — precisely the stream a coordinator exists to run, at a tempo where
> coordination is genuinely load-bearing. So this feedback comes from running your product on
> the use case it seems designed for, checked against machinery we already operate.
>
> **What we're testing it against:** since we'd already hand-built most of what Projects
> ships — a cron-fired dispatch routine, committed-doc memory, claim files to prevent
> duplicate parallel work, and a CI gate that holds a PR "red by design" until a session
> declares itself done — our bar is "does this beat what we already built," not "is this a
> nice-to-have."
>
> **Four things we're specifically checking, and what we found:**
> 1. *Duplicate-work prevention* — [what happened when two sessions/tasks overlapped]
> 2. *Write-back / "say it once" memory* — [whether a requirement stated once actually carried
>    into a fresh session without restating]
> 3. *Distinguishing "intentionally incomplete" from "broken"* — [what the sidebar/coordinator
>    showed for a deliberately in-progress PR vs. a CI failure]
> 4. *Surviving genuinely unattended stretches* — [whether a session ran 20+ minutes with no one
>    at the keyboard without stalling on a permission prompt]
>
> **Cross-cutting asks, not specific to Projects** (things that would help any autonomous Claude
> Code session, ours included):
> - Deliver PR-webhook events for CI *success* and merge-conflict transitions, not just failures —
>   today a subscribed session only wakes on failure/comment, so "still green, still open" is
>   invisible without polling.
> - A native "work-in-progress, don't auto-merge yet" PR state that auto-merge respects — we
>   built this ourselves (a session-card + CI gate) after a half-done PR merged once.
> - **Auto mode's boundary is *reversibility of published state*, and destroying/rewriting it has
>   no self-clear path — our flagship finding, now mapped action-by-action** (full table +
>   reproducibility in the attached permission-probe report). Every *constructive* action ran
>   unprompted — reads, local writes, web GET/POST, pip install, pushing a **new** branch,
>   GitHub-API issue create/close, sub-agent spawns. **Hard-denied with no way for the session to
>   proceed:** force-push, remote branch deletion, and first-publish to a brand-new public repo —
>   and the classifier also treats reworded retries as bypass attempts, discounts a coordinator's
>   relayed intent as "not user intent," and denies a spawn whose prompt merely *names* a
>   destructive verb. Net: an **unattended** autonomous session can *create* remote state but can
>   never *delete or rewrite* it — ours could not even clean up its own scratch branch. The safety
>   intent is sound; the gap is the absence of a **discoverable, scoped way for the operator to
>   pre-authorize a specific reversible-tier action** (a per-Project allow-list) so an unattended
>   run isn't dead-ended. (Cloud offers no prompting-mode switch and no permission-rule UI, and the
>   `.claude/settings.json` allow-rule is session-start-only and may be classifier-overridden — so
>   today there is no self-serve grant path.)
> - **The coordinator can pass at most 4096 bytes (4 KiB) of instructions to a session it spawns**
>   (`start_project_session` hard-caps it). For an orchestration product whose core job is handing
>   work to child sessions, that's a small budget — a detailed task brief exceeds it easily (our
>   permission-probe spec hit the cap mid-fleet). It's survivable via the repo-as-context model —
>   put the detail in a committed file and dispatch a terse "read doc X, do task N" pointer — but
>   that forces a fetch-from-repo indirection for anything non-trivial and quietly caps how richly
>   a coordinator can direct a child in-band. A larger cap, or a way to attach a reference doc to a
>   spawn, would remove a real orchestration bottleneck.
> - Native lane claims ("this session owns scope X until it ends," visible to siblings at
>   session start) — we built a claim-file convention for exactly this.
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
