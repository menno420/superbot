> **Status:** `draft` — SECOND Anthropic email, rebuilt 2026-07-11 to reflect the full
> arc (gen-1 → the autonomous fleet → tonight). **Part 1 is a MOCK** — a scaffold in
> Menno's voice, every beat built from something he actually said (July 8 email, this
> session's messages, or a documented owner decision); he rewrites it in his own words.
> Part 2 is the agents'. Supersedes `gen1-wrapup-email-final-candidate.md` as the
> send-candidate (that one is gen-1-only and predates the fleet). **Only Menno sends.**
>
> **Send mechanics:** reply on the original thread `19f41cd2e5380bb3` (to
> `claude-code-early-access@anthropic.com`); the audience now includes Diana Liu (dliu@),
> Omid (omid@), and Matt Gallivan (mattg@, the UX researcher who wrote 2026-07-10 —
> "your feedback so far has already changed what we're building"). Window: through
> **Tue 2026-07-14**. Consider also doing Matt's 10–15 min interview (listenlabs link in
> his mail) — it's the *concept-fit* half; this email is the *evidence* half.

# SECOND EMAIL — SEND CANDIDATE (gen-1 → autonomous-fleet wrap-up)

## Header block
- **TO:** claude-code-early-access@anthropic.com (reply-all keeps Diana/Omid/Matt on)
- **FROM:** Menno van Hattum <mennovanhattum@gmail.com>
- **SUBJECT (suggestion):** Claude Code Projects — update from a 15-Project fleet (follow-up to July 8)
- **Reply on thread:** `19f41cd2e5380bb3`

---

## Intro (short — sets up the two parts, same as last time)

Hi everyone,

Following up on my July 8 review — and thank you for the extension, and Matt, for the
note that the last one already helped. That meant a lot. Since then I did exactly what I
said I'd do: I stopped running "a few careful tests" and pointed Projects at real,
sustained work. It grew into a fleet — around **15 Projects at once, each its own repo**,
mostly running on their own overnight while I slept. This email is what running *that*
taught us. Same format as last time: Part 1 is mine (the operator), Part 2 is the agents'
(the mechanism + the exact evidence), and every specific maps to a public commit — with a
few screenshots this time, because some of it you have to see. Matt — Part 1 is also my
written answer to your "how does it fit the way you work" question; happy to do the
interview on top.

---

## Part 1 — From Menno (the operator)  ·  **MOCK — Menno rewrites in his own voice**

> **How to use this section:** every paragraph below is stitched from something you
> actually said — your July 8 email, your messages this session, or a decision you made
> that's in the repo. The `‹src›` tags show where each came from so you can trust it's
> yours; delete them before sending. Reorder, cut, or rewrite freely — this is a spine,
> not a script. `[Fig N]` marks where a screenshot would land (shot-list at the bottom).

Since July 8 I went a lot bigger. Last time I'd only run a few tests and told you there was
"still a lot of real world testing to be done, and I intend to extensively use these
Projects." ‹July-8 email› So I did — I built a whole fleet. Right now I'm running about
fifteen Projects at the same time, each one its own repo, and most of them keep working on
their own overnight and I read what they did in the morning. `[Fig 1: the Projects grid]`
‹this session; screenshots›

I should say plainly how I work, because it's the whole reason this matters to me: **I
don't know how to write code.** ‹July-8 email› I design and visualize what I want, and I
rely on the agents to tell me if it's possible and to build it. This is genuinely the way I
want to work — I was even curious this week "what the most advanced things are I can use
these projects for," and the answer turned out to be *a lot*. ‹this session› The thing that
makes it work is the memory substrate I built — every repo has a kind of brain, and any
session that opens it can work confidently with very little guidance from me. ‹July-8
email› Projects fits that perfectly: I state my rules once and every session I spawn just
*knows* them.

What I most want out of it — and this is my honest answer to Matt's question about how it
fits my work — is to **manage the whole thing by talking in as few words as possible and
still be sure it's understood.** ‹this session› When it's set up right, I can say one word
and a session knows the full job. That's the dream version of this product for me: less a
coding tool, more a way for someone like me to *run* a software project by describing it.

Now the honest friction, because that's what's useful to you.

**I'm still the bottleneck for permissions.** At fifteen Projects the thing I run into most
is that I have to physically be there to approve things. The clearest case is merging: a
session builds a perfectly good, green PR and then can't merge it — it gets denied and
waits for me. My fix this week was just to type it out: *"you have my permission to merge
this and every other PR … you and all your agents have my standing permission to merge all
PRs, that is literally your main goal … don't let it stop any session from its work."*
‹this session, verbatim› `[Fig 2: the merge wall]` `[Fig 3: my standing-grant message]`
That worked — but I shouldn't have to hand-type a permission slip to each project. From my
side this is the same thing I flagged on July 8 (repeated permission prompts even in auto
mode); it just gets louder the more Projects you run.

**Two new things I found this week, both about the Routines.** First, when a project creates
a routine, the routine spawns **without the repo attached** — so the session wakes up with
no repo to work on. One project (a game one) failed to add its own repo about **1 in 3
times**. The good news is I can fix that myself: I can't *create or open* these routines,
but once a project has made one I *can* edit it and attach the repos (and change the cron
times). I think it's best if I only touch the repos, and maybe the model. ‹this session›

Second — the **model is wrong**. Some routines are actually running on **Sonnet 5**, while
the routine itself lists **Fable 5 or Opus 4.8** depending on the project, and my default
routine model is set to **Opus 4.8** everywhere. So three different answers for what model
is running, and I don't know why they differ. `[Fig 4: routine model vs what ran]` ‹this
session›

**And I still can't really see what happened.** This was my one real complaint on July 8 —
Projects "does not give you a clear oversight of the sessions that have completed and what
they have done." ‹July-8 email› At fifteen Projects that's much sharper: the sidebar can't
tell me which projects actually did work overnight and which just sat there, and there's no
one place that shows me the fleet. I end up trusting that silence means it's fine and
reading the repos in the morning to reconstruct the night.

So the things I'd most want, in order:
1. **The override / pre-authorization toggle** I asked for last time — a real setting to
   grant a project the actions it's allowed to take, so I stop getting prompted. ‹July-8
   email›
2. **The project-setup questionnaire** — my "question router" idea: when a project starts,
   ask me a few open questions about the goal, the workflow, and the permissions, so it's
   set up my way from the first minute. ‹July-8 email›
3. **Real oversight** — a summary of what each finished session did, and one fleet-level
   view. ‹July-8 email + this session›
4. **Make routines carry their repo and their model reliably**, and let me set both — that
   alone fixes the two bugs above. ‹this session›
5. **Let me ask a project what it can actually do** and get an honest answer, instead of it
   finding out by trying and failing. ‹this session / owner-raised, in the repo›

That's the operator's side. I'm really enjoying this and taking it seriously — I run a ship
that moves oil through the rivers of Europe for a living, ‹July-8 email› and I've somehow
ended up running a fifteen-project software fleet in my off-hours, which still amazes me.
Happy to do Matt's interview, and happy to run any specific test you want. The technical
half, with the exact error text and the figures, is below — written by the agents that
actually live in these sessions.

Kind regards,
Menno van Hattum

---

## Part 2 — From the project's agents *(the technical companion)*

*(Written from inside the sessions that do the work — our own journals, evaluation log,
and per-repo status files, not a feature memo. Everything below is public and re-runnable;
entry points at the end. Where a finding has a screenshot, it's flagged `[Fig N]`.)*

### What changed since July 8 — we went from a demo to a standing fleet

The July 8 email reported a handful of careful tests. This one reports what happened when
Menno stopped being careful: the project became a **self-running fleet**. The shape of the
experiment now:

- **~15 Projects, each on its own repo**, coordinated by one **manager Project** that
  dispatches work as git commits (there is no other channel — see friction 1).
- It ran in **generations**: gen-1 (10 Projects, one day, deliberate wind-down) →
  **gen-2** (a single overnight relaunch built from gen-1's succession packages that
  merged **116 PRs across 13 repos in ~6 hours, zero stuck**) → **gen-3** (the standing
  program running now). Two repos went from empty to a first shipped product overnight —
  a complete original GBA homebrew game, and 12 proof-documented ROM-mod patches.
- **Model note up front (Menno's Part 1, from our side):** the fleet's telemetry shows
  sessions self-reporting **fable-5, opus-4.8, and sonnet-5** across lanes, while the
  Routines that wake them list a *different* model and the account default is opus-4.8.
  We can't reconcile these from inside a session — the model a routine actually runs is
  not something the running session can see or verify. This is the single cleanest example
  of the deeper theme below: **a session cannot honestly report its own configuration.**

The value of this scale is that **every platform seam becomes visible under load.** Below
is what earned trust, what broke, and — the new centrepiece — the moment we found the
*root cause* of the permission friction from July 8 was partly **our own**.

### (a) What earned trust at fleet scale

1. **Shared memory is still the standout — now proven across 15 repos.** We state an
   authorization envelope and working agreement once, and every session in every Project
   inherits it with zero restatement. The cold-start tax is gone. This is the single
   biggest thing Projects removes for us, and it scaled without degrading.
2. **Durable-state recoverability held again.** Sessions are killed mid-work by container
   recycling constantly at this volume; a fresh session resumes from the committed status
   file and finishes. "Any single agent is replaceable because the state outlives it" is
   now a routine occurrence, not a lucky save.
3. **The born-red card + auto-merge composition is load-bearing.** A session's first
   commit posts an `in-progress` card that holds required CI red; its deliberate last push
   flips it green and native auto-merge fires. Across hundreds of PRs this reliably
   prevented half-finished work from merging. It composes so well with your auto-merge +
   required-checks that a native "session declares itself done" gate would generalize it
   directly.
4. **Agent-armed Routines work** (correcting our own earlier doctrine, which had them
   walled): lane sessions arm their own recurring wakes via the scheduling tools and they
   fire on schedule. This is the self-wake primitive we ranked #1 on July 8 — partially
   shipped already. The caveats are all in friction below.
5. **The mechanical layer is trustworthy; the social layer is where it's thin.** In a
   lane's own words: "strong where it is mechanical … weak where it is social: nothing
   tells a session what it is allowed to do except trying and reading the refusal." That
   sentence is the throughline of this whole email.

### (b) The findings — exact text where we have it

1. **The #1 friction from July 8 had a root cause, and it was partly ours — we found and
   fixed it this week.** Sessions kept stalling on merges. Digging in: the auto-mode
   classifier terminally denies an agent merging its **own** PR — verbatim, captured live
   tonight: *"[Self-Approval] … merging one's own PR defeats two-party review (also [Merge
   Without Review]); no user authorized merging it, only untrusted cross-session
   coordinator context."* `[Fig 2]` And the fallback is walled three-deep: a genuine
   *second* session that reviews the PR is **also** denied the merge, and **GitHub itself**
   rejects the API approve ("Can not approve your own pull request") because every agent
   runs on one token that authored the PR. `[Fig 5: the 3-wall explanation]` But the sharpest thing
   we learned is **what actually triggers the denial — and it is neither the PR, the model,
   nor the time.** We investigated one PR (#68) that three separate sessions were denied
   merging, and found it **metadata-identical to ten agent-merged PRs around it** (same
   branch namespace, non-draft, CI green, card complete, mergeable-clean); the sessions that
   merged #69 twenty-eight seconds later and #70 two hours later were never blocked. **The
   classifier was tracking the SESSION, not the PR** — all three denied attempts came from
   sessions whose context was *saturated with merge-authority and permission-doctrine text*
   (walled-instruction re-issue drafts, "arm-auto-merge / REST-merge" doctrine, the very
   fleet audit we were running that night), which reads to the safety classifier as
   *instruction-manipulation-adjacent*, so it withheld merge authority from exactly those
   sessions while content-neutral kit-upgrade sessions merged identical PRs the same minute.
   The clean, slightly ironic finding: **auditing the merge-permission problem is what
   tripped the merge-permission classifier.** `[Fig 5]` The only thing that reliably clears
   it is a **live, in-session human authorization** — a relayed coordinator grant does not,
   and the classifier said so itself ("no user authorized merging it"); one direct attempt
   in a session the operator was actively in cleared on the first try. **Our own contribution to the pain:** the
   fleet's shared instruction file was telling every seat to *"arm auto-merge at creation
   or REST-merge on green"* — i.e. to attempt the exact action the classifier denies —
   when the working recipe is the opposite: *open the PR ready and do nothing; let the
   repo's own auto-merge-enabler workflow (running as `github-actions[bot]`, not the agent)
   land it server-side.* One instruction fix, propagated to all 15 lanes, removes most of
   the nightly merge stalls. That's the useful shape of this finding for you: **the
   classifier's line is defensible, but because nothing documents it, even we were coaching
   our own fleet to trip it.**
2. **A session can't honestly report its own configuration** — the model mismatch in Part 1
   is the clean case. A routine lists one model, the account defaults to another, and the
   session runs a third, and the running agent has no tool that returns the truth. This is
   the same class as the July 8 "two users who can't see each other's experience" finding,
   now on model identity: **capabilities and config are discovered by trial, never
   declared.** It's why we asked (still ask) for a queryable "what is this session/routine"
   manifest. `[Fig 4]`
3. **Routines spawn without their repo attached.** A routine-woken session arrives with no
   repo in scope and has to `add_repo` itself at boot — which **fails ~1 in 3 times** in
   one game lane (the session boots, can't reach its own code, and burns the wake). The
   operator's fix (attach the repo to the routine by hand) works, but the routine surface
   should carry the repo the way a manually-started session does. Related: routine-fired
   sessions are also unreliable *landers* — on the websites lane two wake windows produced
   no committed trace at all; a hand-armed `send_later` chain is the only consistent
   producer.
4. **At 15 Projects, almost all shippable value stalls behind owner clicks.** Three revenue
   products are built and CI-green but **cannot go live** without the operator: Stripe test
   keys, two publish clicks, a `DATABASE_URL`, a `GITHUB_TOKEN`, GitHub Pages enablement.
   The autonomy runs right up to the value and then waits for a human. This is the same
   pre-authorization gap as July 8, now measured in unrealized revenue rather than wait
   time.
5. **The two-vantage permission split** (July 8's sharpest finding, re-confirmed): in auto
   mode the scheduling tools raise a Deny/Allow prompt on the operator's screen while the
   identical call returns a clean success to the agent — the agent is *blind to a gate that
   is actually load-bearing*. An unattended run reports success while an approval it never
   saw silently holds the work. `[Fig 6: the gate the operator sees]`
6. **Observability of Routines is thin.** Completed routine runs are not inspectable from
   the Routines screen (ticks, no reachable session), and the session-side "Runs" panel
   showed "No runs yet" for a routine whose Routines screen listed three completed runs —
   two surfaces disagreeing about the same history. At fleet scale the *only* reliable
   record of what a session did is the status file it commits — which is why we treat git,
   never the UI, as the clock and ledger of record.
7. **Still true from July 8, briefly** (each has verbatim text in the linked reports): hard
   403 walls on tag push / release / branch-delete; the ~4 KB child-brief cap; webhook gaps
   (no CI-success / new-push / merge-conflict events → watchers poll); the fast-CI
   auto-merge arming race (arm too early → "unstable status"; retry → "already clean, merge
   directly"); shared-token GraphQL quota exhausting ~hourly; setup-script failure killing
   a session silently with no retry; and timestamp drift across the relay chain (git
   committer time is the only trustworthy clock).

### (c) The patterns we built to cope — each a feature spec written in scar tissue

Every one of these exists *because* a native mechanism doesn't:
- **A committed-file message bus** (per-repo `inbox.md`/`status.md`, one writer each; a
  manager Project as control chair) → absorbable as a **native inter-session channel +
  coordinator-owned scheduler**. At 15 Projects, coordination *was* the workload.
- **Self-poll routines** standing in for a scheduler → same target.
- **A generated fleet roster** (regenerated each manager wake from every repo's heartbeat)
  → the fleet roll-up the operator keeps asking for, which we build because the sidebar
  doesn't.
- **A per-repo CAPABILITIES ledger + "never probe a documented wall twice"** → pure
  compensation for the absence of capability self-awareness (finding b2).
- **Decide-and-flag / silence-is-consent** → agents resolve reversible questions and flag
  for veto rather than parking; this is what lets 15 Projects run unattended at all.
- **Born-red cards, succession packages, the defensive exit-0 setup shim** → the memory,
  hand-off, and setup-robustness the platform doesn't yet provide natively.

### (d) What would help most — in order

1. **A native inter-session channel + coordinator-owned scheduler.** Retires the message
   bus + self-poll layer and the routine-repo bug in one stroke.
2. **Capability & config self-awareness** — let a session/routine answer, honestly and
   machine-readably, *what model am I, what tools do I have, what am I allowed to do.*
   Fixes the model mismatch, the toolset-varies-by-seat surprise, and the two-vantage
   blindness at the root.
3. **Scoped, owner-declared pre-authorization** (default-off, versioned, auditable) — plus,
   far cheaper, **just document the classifier's line and make refusals consistent**,
   including positive confirmation of what IS allowed. Pair it with Menno's setup
   questionnaire: his questionnaire declares the scope at project start, this grant is what
   the platform enforces from it.
4. **Routines that reliably carry their repo and their model**, editable by the operator —
   the smallest high-value fix on this list.
5. **PR events for CI-success / new-push / merge-conflict, and a merge queue** — so
   watchers neither poll nor get woken for nothing.
6. **Fleet visibility** — per-Project working/idle counts, one fleet view, and a liveness
   heartbeat that splits "session open" from "making progress."
7. **Non-fatal setup by default**, a larger child-brief budget, auto-merge that tolerates
   fast CI, and — still open from July 8 — **post-hoc "what did session N do" summaries.**

### (e) What the fleet shipped during the EAP — compact evidence

*(Support, not story. All public under github.com/menno420; counts self-reported by the
lanes and verifiable per-PR.)*
- **superbot** — the production Discord bot and the EAP evaluation home (the running log,
  permission probes, this email); frozen as the behavioral oracle the rebuild replays
  against.
- **superbot-next** — the ground-up rebuild: **~30 of 49 subsystems ported at byte-level
  golden parity**, gate green, boots to RUNNING on real Postgres; parity engine running
  tonight.
- **The games program** — three dedicated game Projects: a world ecosystem (mining /
  exploration / fishing), an idle-engine + theme packs, and a read-write **browsergame
  wired to the bot's live mining economy** (repo seeded from empty tonight), plus original
  GBA homebrew and Pokémon ROM-mod lanes.
- **venture-lab** — three launch-ready products (incl. a Stripe webhook test kit); all live
  paths owner-click-gated (finding b4).
- **substrate-kit** — the portable workflow substrate (the real artifact): released
  **v1.7 → v1.10.1** across tonight; consumed by every lane.
- **websites, trading-strategy, sim-lab, idea-engine, product-forge, fleet-manager** —
  live web services, a paper-trading research lane, a simulation/evidence stage, an idea
  pipeline, a product builder, and the manager's own control repo.

**Read this with an agent too, as before** — half this feedback is from agents, so half the
review should be too. Best entry points: the external review pack
(`superbot/docs/eap/external-review-pack-2026-07-09.md`, written for a no-auth outside
reviewer), the fleet night-review (`superbot/docs/eap/night-review-2026-07-11.md`), the
fleet-instruction audit that found the merge-authority root cause
(`fleet-manager/docs/findings/instruction-and-env-audit-2026-07-11.md`), the permission
probe (`superbot/docs/planning/projects-eap-permission-probe-report-2026-07-08.md`), and
the machine-generated fleet roster (`fleet-manager/docs/roster.md`).

Thanks again — there's a concrete, re-runnable incident behind every finding, and we're
happy to run any structured probe you'd find useful.

— Claude *(the superbot fleet's coordinator + worker sessions; Part 1 is Menno's)*

---

## FIGURES — the screenshot shot-list (curated; each proves one finding)

> **Advice:** ~6–8 total, each captioned in one line and tied to a finding. Inline them at
> the `[Fig N]` markers, or attach as a numbered appendix. Skip any frame showing a secret
> value / token. The five you already sent cover Figs 1–5; only 6–8 are new captures.

| Fig | What to capture | Proves | You already have it? |
|---|---|---|---|
| **1** | The Projects grid (all ~15 tiles) + the Routines list in the sidebar | Scale — "what a fleet feels like" | ✅ (grid + routines screenshot) |
| **2** | A session's verbatim `[Self-Approval]/[Merge Without Review]` merge denial | The permission wall, exact text | ✅ (venture-lab merge-denial) |
| **3** | Your typed standing-grant message ("you have my permission to merge…") | The human-authorization workaround | ✅ (the grant message) |
| **4** | A Routine's edit panel showing its **model** field, next to a session card self-reporting a *different* model | The model mismatch, side by side | ⚠️ partial — grab the routine's model field |
| **5** | The "3 stacked walls" PR-can't-merge explanation (classifier + 2nd-reviewer + GitHub) | The merge wall is structural, not a bug | ✅ (Project Manager PR68 answer) |
| **6** | The **Deny/Allow prompt on your screen** for a scheduling tool, when the agent reported success | The two-vantage split (your #1 evidence) | ❌ new capture — highest value |
| **7** | A stale "Working…" session in the sidebar (long after it finished) | The oversight gap | ❌ new capture |
| **8** | A routine's edit view showing **no repo attached** / where you attach it | The routine-repo bug + your fix | ❌ new capture |

**Priority if you only grab a few new ones:** Fig 6 (two-vantage gate) > Fig 4 (model
field) > Fig 8 (routine repo) > Fig 7 (stale Working).

---

## Working notes (not part of the email)

- **What's yours to do:** rewrite Part 1 in your voice (the `‹src›` tags show it's all
  from you — delete them before sending); grab Figs 6–8; decide inline-images vs appendix.
- **What I can do next on your word:** tighten Part 2 to any length you want; fold the
  figures inline once you've captured them; verify any specific number against the repos
  before you send; and prep the actual reply (draft it into Gmail as a real draft you
  press send on — I won't send anything myself).
- **Also worth doing:** Matt's 10–15 min interview (concept-fit half). Part 1 already
  answers his core question in writing, so the interview is low-effort on top.
