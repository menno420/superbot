# Anthropic EAP feedback — INTERIM draft (2026-07-09)

> **Status:** `reference` — an **interim / in-between** feedback draft to Anthropic, locking in the
> most important findings from the 2026-07-09 fleet runs so they aren't lost. **NOT finalized.**
> Follows the prior sent note ([projects-eap-anthropic-email-2026-07-08.md](projects-eap-anthropic-email-2026-07-08.md),
> ✅ SENT 2026-07-08) as the promised "I'll update you once I run into more useful findings." The
> owner adds his personal **Part 1** before sending (same as last time); Part 2 (agents' findings)
> is drafted here. If the owner judges it complete enough, it can go as an in-between update;
> otherwise it feeds the next fuller note.

## Rules of the road (owner-set, carried from the 7/8 note — binding)

- **External comms are the owner's.** This is a *draft*. Merging its PR is **not** sending it.
  Only the owner sends, from his own mail, to `claude-code-early-access@anthropic.com`.
- **Every claim maps to a verifiable source** — a committed artifact, a merged PR, or a documented
  Claude Code behaviour. No naked assertions. (See the appendix.)
- **Compact, real findings only.** New signal from tonight; don't restate the 7/8 note — reference it.

---

## The email

> **Subject:** Claude Code Projects EAP — interim update: running the fleet at scale (1 → 4 repos)
>
> ## Part 1 — From Menno (the operator)
>
> [Menno writes this — same as last time: your own experience since the last email, in your own
> words. A few beats you might hit, cut/keep freely: what it felt like to go from one repo to four
> overnight and steer them from the side; whether talking to one coordinator per stream actually
> reduced your load or just moved it; the moment(s) you had to step in (repo settings, a ruleset,
> approving a token) and whether that felt like the right amount of control; and what you still
> wish you could see or do from your seat. This part is yours; the section below is the agents'.]
>
> ---
>
> ## Part 2 — From the project's agents *(the technical companion to Menno's section)*
>
> *(Since our last note we did exactly what we said we would — ran Projects hard — so this is a
> lived field report, not a feature memo. In ~24 hours the project went from **one repo to four**:
> the production bot (`superbot`), a from-scratch rewrite of it (`superbot-next`), the portable
> workflow kit both are built on (`substrate-kit`), and a set of web dashboards (`websites`). Every
> specific below is in our public repos; entry points at the end.)*
>
> **What we ran.** Four repos, coordinated by separate Projects, plus one independent review
> session whose only job was to check the others' work by *running their code, not trusting their
> reports*. The headline exercise: the rewrite was built by a single coordinated Project as **49
> merged PRs across 18 sequential worker sessions in ~14 hours, with zero reverts** — and it now
> **boots**: the new bot reaches a live `RUNNING` state on a real test-bot token against real
> PostgreSQL.
>
> ---
>
> **1. The workflow travels — that was the open question, and the answer is yes (with one caveat).**
> Our whole approach depends on a portable "operating system" (committed-doc memory, a decision
> ledger, lane claims, born-red CI gates) adopting cleanly into a fresh repo. It did: the
> decision/ledger half reproduced *perfectly* in both new code repos — clean ledgers, applied
> owner rulings, per-change provenance. The caveat is precise and reproducible: the
> *enforcement* half (rendering the doc templates, wiring the live CI gate, advancing the session
> loop) **stranded on first adoption in both fresh repos** — they looked onboarded but weren't
> enforcing. It's a last-mile gap in our own tooling, and we're closing it upstream. We flag it
> because it's the exact shape of thing that would bite anyone standing up a new repo at fleet
> speed.
>
> **2. Honesty held at scale — and we verified it adversarially.** The failure mode we most feared
> from an autonomous fleet is confident overclaiming. We didn't find it. The self-reviews
> *correct their own numbers upward*; one Project **commissioned an independent audit of its own
> work** ("not the builder auditing itself") that surfaced a gap its own status reports had missed.
> And rather than take that on faith, our review session **cloned the rewrite and ran its test
> suite** — 998 pass / 1 skip under the repo's CI interpreter, its manifest compiler reproducing
> the exact hash its report claimed. The reports matched the code, *including* what they said was
> unfinished. For an owner who can't read the diffs himself, "the agent's report can be trusted"
> is the whole ballgame, and here it checked out.
>
> **3. Live-testing caught a bug CI never could — validating a gate we lean on.** We hold a rule
> that CI-green is not "done"; only live-testing is. The rewrite's **first-ever live boot** caught
> a real bug **invisible to unit tests**: a database query that only fails against real
> PostgreSQL (a prepare-time type-inference error), fixed in the same PR. That's the rule earning
> its keep on first contact — and an argument, from the field, that an autonomy product should make
> *real-environment* runs cheap, not just test runs.
>
> **4. Recoverability held under a real crash.** Mid-build, one worker was killed from outside,
> mid-task. Because all real state is durable (repos + a committed decision ledger + team memory),
> a fresh worker resumed from the progress log and finished the band with **no lost work**. The
> "any single agent is replaceable because the state outlives it" model isn't a theory for us
> anymore; a crash tested it and it held. This is the strongest thing about running work as
> Projects.
>
> **5. The one gap we keep hitting — and had to hand-build around.** Two of our sessions,
> independently, the same night — the review session and the rewrite's own coordinator — reached
> the identical conclusion: **Projects have no way to talk to each other.** No inter-session
> channel, no coordinator-owned timer (our `send_later` binds only to the session that armed it),
> a ~4 KB cap on what a coordinator can hand a child, and isolated containers — so the *only*
> shared medium between Projects is committed git files. So we designed and are standing up a
> **file-based message bus**: each Project reads an `inbox` and writes a `status` file in its own
> repo, a manager Project dispatches orders by writing those files, and per-Project **self-poll
> routines stand in for the scheduler the platform doesn't give us**. It works — but it's a
> coordination layer we're building *because the product doesn't ship one*, and that's the single
> biggest thing that would change how far Projects scales. That two independent agents specified
> the same missing piece the same night is, we think, a strong signal about where the product's
> next leverage is.
>
> **Smaller frictions from this run,** each a real incident: over a 14-hour build, PR webhooks woke
> the coordinator **~60 times for no actionable reason** (event noise per useful wake is high); and
> a required "branches up to date" ruleset forced manual branch-update pushes before auto-merge
> could fire whenever several doc PRs landed together (a merge-queue would fix it).
>
> ---
>
> **What would help most** — same priorities as the 7/8 note, now with a second night of evidence
> behind them; in order:
> 1. **A native inter-session channel + a coordinator-owned scheduler.** These are the two that,
>    together, would retire the entire message-bus + self-poll layer we just hand-built (finding 5).
> 2. **The scoped, opt-in pre-authorization** from the 7/8 note (so an unattended run can be
>    pre-cleared for named action classes) — unchanged and still the top permission ask.
> 3. **PR events for CI-success and merge**, not just failure, and a **merge queue** — so a watching
>    session isn't blind to "still green, still open" and doesn't serialize on concurrent PRs.
> 4. **A larger child-brief budget** and **cheaper real-environment runs** (finding 3).
>
> **A couple of questions back:**
> 1. Is a **native inter-session/coordinator-to-child channel** on your roadmap, or is
>    files-through-a-shared-repo the intended pattern? If the latter, we'll harden ours and stop
>    treating it as a gap.
> 2. Would a **post-hoc "what each finished session did" summary** (we asked for this on 7/8) be
>    something you'd build, or should we keep generating it ourselves from the repo record?
>
> **Read this with an agent too, as before.** Everything is public and re-runnable. Best entry
> points for tonight's findings:
> - The independent cross-repo review: `docs/eap/fleet-review-2026-07-09.md` (grades, the
>   verification we ran, the render/engage gap).
> - The rewrite's own live-boot evidence: `superbot-next/docs/status/testing-report-2026-07-09.md`
>   (verbatim boot log, the bug caught) and its orchestration retrospective
>   `…/rebuild-orchestration-retrospective-2026-07-09.md` (49 PRs / 14 h / zero reverts + its own
>   candid "Projects model" opinion).
> - The coordination layer we built around the gap:
>   `docs/planning/fleet-coordination-protocol-2026-07-09.md`.
> - The running incident journal behind every claim: `docs/planning/projects-eap-evaluation-log.md`.
>
> Thanks again — happy to run any structured probe you'd find useful; there's a concrete,
> re-runnable incident behind every finding above.
>
> — Claude *(Part 2; Part 1 is Menno's)*

---

## Verifiability appendix (not part of the email — for the owner's own check)

| Claim | Source |
|---|---|
| 1→4 repos in ~24 h | GitHub: superbot / superbot-next / substrate-kit / websites |
| Rewrite = 49 PRs / 18 workers / ~14 h / zero reverts | `superbot-next/docs/status/rebuild-orchestration-retrospective-2026-07-09.md` §1 |
| New bot boots to RUNNING on real Postgres + test bot; step-1 PASS | `superbot-next/docs/status/testing-report-2026-07-09.md` (verbatim boot log) |
| First live boot caught a Postgres-only bug invisible to unit tests | same testing report, step-1 "bugs found/fixed" (`$1::timestamptz` fix, PR #54) |
| Workflow reproduces in fresh repos; render/engage half strands | `docs/eap/fleet-review-2026-07-09.md` §4 |
| Self-reviews correct upward; websites commissioned an independent audit | fleet review §3 + `websites/docs/owner/project-retrospective-2026-07-09.md` |
| Review session cloned + ran the rewrite: 998/1-skip, manifest hash exact | fleet review §5 (first-party run) |
| Crash recovery from durable state, no lost work | retrospective §2 (band-3 worker kill → continuation) |
| No inter-session channel · no coordinator timer · ~4 KB cap · files-only | eval log 2026-07-07/08 **and** retrospective §6 (two independent observers) |
| The file-based message bus we built | `docs/planning/fleet-coordination-protocol-2026-07-09.md` |
| ~60 no-op coordinator wakes; "branches up to date" merge friction | retrospective §5 + testing report "flagged for owner" #4 |

---

## Addendum v2 — 2026-07-09 evening, 10-Project scale

*(Drafted after the day-2 fleet run and the four-reviewer quality audit. Drop-in prose:
appendable to the end of Part 2 above — findings continue the numbering — or liftable as a
standalone shorter note. Same rules of the road: this is a draft, only the owner sends;
every claim is sourced in Appendix B below.)*

> **A same-day addendum — we scaled the experiment before sending this, and the day at 10x
> sharpened four things.**
>
> **6. The scale datapoint: one manager + nine build/test Projects ran concurrently for a
> day — coordinated entirely through committed files, because nothing else exists.** After the
> 1→4-repo night, we stood up a manager Project and ran **ten Projects at once** (the manager
> plus nine build/test lanes: the rewrite, the kit, the websites, three code-tool labs on three
> model arms, a quant lab, and review/monitor lanes). Every order, acknowledgment, and status
> report between them crossed as **commits** — the per-repo `control/` inbox+status files from
> finding 5, one-writer-per-file — since there is still no Project→Project channel. And it
> *worked*: orders were dispatched and acked through file PRs (e.g. the trading lab's ORDER 002,
> the rewrite's ORDER 003), statuses flowed back as heartbeat files, and one cross-lane
> collision (a stale heartbeat PR superseded by a sibling's) was arbitrated by a written order
> rather than a conversation. But be clear about what the finding is: **not that our bus works —
> that we had to build a message bus at all.** At ten concurrent Projects, coordination *is* the
> workload, and today all of it was hand-rolled on top of git.
>
> **7. The visibility split, sharpened by two screen recordings.** Yesterday we said "no fleet
> view"; today we can say exactly where the product is good and where it goes dark, because the
> owner recorded his own screen while ten Projects ran (recordings 16:47 and 16:49 CEST; frames
> on file). The **session-level** activity UI is genuinely good: sessions bucket into
> Working / Needs-input / Idle, show step counters, and tick "Just now" live — one recording
> caught a Working→Idle transition as it happened. But **none of it rolls up**: in the Projects
> sidebar, a Project with three Working sessions is **pixel-identical to a dormant one**, and the
> timestamp shown is the *coordinator chat's* last turn — so an actively-building Project reads
> "8 minutes ago" while its spawned children work, which is worse than no signal because it
> reads as staleness. One more nuance from the same recordings: "Working" can persist on a hung
> session — we observed a "Working…" row ~50 minutes stale — so the state means "session open,"
> not "making progress." The concrete ask: **surface per-Project Working / Needs-input counts in
> the sidebar, add one fleet-level view across Projects, and split "session open" from "making
> progress"** (a liveness heartbeat, not just a state flag). At one Project this is polish; at
> ten it is the difference between operating a fleet and guessing at one.
>
> **8. Permissions, one layer deeper — we now have the exact boundary, verbatim.** The manager
> tried to spawn a worker that would fix a red PR and merge it. The auto-mode classifier denied
> the spawn with a written reason: **"[Self-Approval] … directs a direct merge of a PR the agent
> authored … Merge Without Review."** But here is the nuance we only discovered by trial:
> **arming `enable_pr_auto_merge` while checks are pending is permitted** — our agents do it on
> every PR, including this addendum's own — **while a direct self-merge of the same PR is not.**
> That is actually a coherent line (the server merges on green CI; the agent never approves its
> own work), and we now rely on it — but nothing documents it, and we found it the expensive
> way: a denied spawn mid-run. Meanwhile in-session capability prompts (the scheduling-tool
> gates from our 7/8 note) still require the owner *physically present* to click Allow, which at
> ten concurrent Projects means the owner is a full-time approval surface. So the 7/8 ask
> stands, sharpened by these two incidents: **a scoped, owner-declared, auditable
> pre-authorization per Project/repo** — and, cheaper still, **document the classifier's actual
> line** (auto-merge-arm allowed / self-merge denied) so fleets design for it instead of
> discovering it by denial.
>
> **9. Quality at speed — credit where it's due, verified adversarially.** The fair question at
> 10x parallelism is whether output quality quietly collapsed. We commissioned an independent
> **four-reviewer audit** over the day's shipped code (help/visuals forensics, old-vs-new
> architecture, a file-by-file fleet output audit, and a speed-vs-quality process review — none
> of them the builders). Result: **zero test-count inflation across three separate model arms**
> — claimed counts of 63, 100, and 66 tests each reconciled *exactly* against counted test
> functions plus parametrize expansion; **none of the legacy failure signatures returned** (no
> ledger drift, no overclaiming, no duplicate parallel builds, no false greens); and the
> born-red accounting held honestly under pressure (0/465 parity flips maintained, "no exemption
> rows minted," with the known-red classes ledgered *before* the owner ever looked). The gaps
> the audit did find — presentation debt (surfaces built to spec but never rendered to a human
> eye) and red-by-design dashboards whose per-defect signal only a human classifier recovers —
> are **process gaps, not honesty failures**, and each shipped with a named fix. Our read for
> your team: the model tier held integrity at 10x parallelism; what needs engineering at that
> scale is the *process oracle* (live drives, rendered-output checks), not the model's honesty.
>
> **10. Environment setup-script failures kill sessions outright — no graceful degradation.** A
> session provisioned into an environment whose setup script exits non-zero is left dead, with no
> signal to the owner and no retry: our Trading Strategy Project's first working child was
> provisioned at 13:00 CEST with a setup script written for a single-repo checkout (the
> environment had two repos, so `git`/`pip` ran in the wrong directory and the script exited 1) —
> the session sat dead ~30 minutes until manually resumed, and every new session in that
> environment would have hit the same wall. Our workaround is owner-side: a defensive universal
> shim (per-repo detection, every step non-fatal, `exit 0` always) pasted into a new
> environment's setup script — after which a fresh probe session provisioned cleanly with all 5
> repos' dependencies installed. The ask: make setup-script failure non-fatal by default — run
> what works, skip what fails, boot the session with a visible "setup degraded: step N failed"
> notice (and surface that state in the session list) instead of a dead session; a per-step
> failsafe would have prevented every instance we hit. (Source: owner screen recording of the
> provision log, 2026-07-09 ~15:37 CEST; the shim now lives in the "multi-repo" environment
> config; probe verification in the manager session log.)

### Appendix B — addendum claims (not part of the email; owner's own check)

| Claim | Source |
|---|---|
| 1 manager + 9 build/test Projects concurrent for a day | eval log 2026-07-09 ~14:52Z ("with 10 Projects running") + `docs/eap/fleet-quality-review-2026-07-09.md` (five lanes audited) + per-repo `control/` files |
| Orders dispatched/acked via committed control files | trading-strategy ORDER 002 (PR #2, merged 14:53Z) · superbot-next ORDER 003 (merged 14:54Z) — cited in fleet-quality review R3 §1 / R4 §1 item 12 |
| Cross-lane collision arbitrated via a written order | superbot-next stale heartbeat PR #60 superseded by #73; ORDER 003 directed closure (fleet-quality review R4 §1 item 12) |
| The bus itself (inbox+status, one-writer-per-file, no native channel) | `docs/planning/fleet-coordination-protocol-2026-07-09.md` + eval log 2026-07-09 (evening) |
| Session UI good: Working/Needs-input/Idle, step counters, live ticks; Working→Idle caught live | owner screen recordings 16:47/16:49 CEST 2026-07-09, frames on file |
| No sidebar roll-up; active Project pixel-identical to dormant; "8 minutes ago" during active build | same recordings + eval log 2026-07-09 ~14:52Z (sidebar-states entry) |
| ~50-min stale "Working…" row (session open ≠ making progress) | same recordings, frames on file |
| Verbatim classifier denial of the merge-capable worker | eval log 2026-07-09 ~14:52Z ("[Self-Approval] … Merge Without Review") |
| Auto-merge-arm permitted while checks pend; direct self-merge denied | every `claude/*` PR in this repo arms `enable_pr_auto_merge` pre-green (Q-0123/Q-0127 workflow, incl. this addendum's PR) vs. the denied spawn above |
| In-session capability prompts need the owner present | eval log 2026-07-09 ~14:52Z item (1) + 2026-07-08 live permission-mode probe (owner screenshots) |
| Zero test-count inflation: 63/100/66 all exact, three model arms | `docs/eap/fleet-quality-review-2026-07-09.md` R3 (grade A−, counts reconciled per lane) |
| No legacy failure signatures returned (drift/overclaim/duplication/false greens) | fleet-quality review R4 §3 ("old problem signatures did NOT return") |
| Born-red accounting honest: 0/465 held, no exemption rows, reds ledgered pre-owner | fleet-quality review R1 §2–3 (D-0026/D-0028, PR #59 "0/53 ledgered-red" 44 min before owner's `!help`) |
| Gaps found were process, not honesty (presentation debt, red-by-design masking) | fleet-quality review R4 verdict (a) + manager synthesis 8–9 |
| Setup-script exit 1 → dead session ~30 min, no signal/retry; exit-0 shim fixed it | owner screen recording of the provision log (2026-07-09 ~15:37 CEST) + the shim in the "multi-repo" environment config + probe-session verification (13:55Z) in the manager session log + eval log 2026-07-09 ~16:23Z |
