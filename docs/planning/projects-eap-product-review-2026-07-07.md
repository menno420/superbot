# Claude Code Projects (EAP) — product review from the SuperBot rebuild program (2026-07-07)

> **Status:** `reference` — the owner-sendable product review Anthropic asked for with the
> Projects EAP invite, organized on the EAP's own feedback axes. **Provenance:** written inside
> the SuperBot repo's final rebuild review (Fable 5, ultracode) at the owner's direction; the
> workflow facts cited are this repo's shipped machinery (~1,780 merged PRs of it), verifiable
> in-tree. §9 separates the cross-cutting ideas that would improve **normal Claude Code**, not
> just Projects — flagged because that is the highest-signal feedback we have.

## 0. Who this feedback is from, honestly

This review is grounded in a repo that **hand-rolled every feature Projects ships, before
Projects existed** — because we needed them to run a one-person, many-agents project at all:

| Projects feature | Our hand-rolled equivalent (in-tree today) |
|---|---|
| Coordinator opening/monitoring sessions | Cron-fired "dispatch" routine + paste-ready session briefs (`docs/planning/*brief*.md`) |
| Shared memory across sessions | Committed docs as memory: `docs/current-state.md` ledger, `.session-journal.md`, per-session `.sessions/*.md` cards, a 240-entry owner question router |
| Session-state sidebar (blocked/ready/working/idle) | Born-red session cards: the first commit opens the PR with an `in-progress` badge that **holds the merge red** until the close-out flips it (`scripts/check_session_gate.py`) |
| Serializing parallel work | One-file-per-claim lane locks (`docs/owner/claims/`) + an overlap checker — adopted after measuring a ~98% merge-conflict rate on the shared-ledger alternative with a simulator |
| Routines/scheduling | Console cron triggers firing self-contained routine prompts (`docs/operations/autonomous-routines.md`) |
| Progress reporting | Auto-merge on green CI + a reconciliation pass every 30 PRs that reconciles the ledger and plans the next band |

So when we say a Projects feature matters or misses, it is not speculation — we have operating
data on the exact failure the feature exists to prevent. The owner is a non-coder who steers by
reading run reports and reacting to what he sees in a live Discord server; the agents decide and
flag (our Q-0240/Q-0241 model). That makes us close to the target user for "auto mode."

## 1. Use-case fit — Project vs one-off session

**Strong fit, one honest caveat.** The rebuild program (build `superbot-next` kernel S0–S15, then
port ~43 subsystems band-by-band, then a 3-stage cutover) is *exactly* the shape a Project claims
to serve: a work stream of dozens of sessions with shared context (once sketched as months-long;
days-to-weeks at fleet velocity under the never-wait model, owner-corrected 2026-07-07), where today every
session pays a real orientation tax (our measured boot-read is capped at 7,000 words *because* it
grew unbounded). One-off sessions were never the problem; **the seams between them are** — a
finished session's knowledge dies unless it is written into the repo, and the next session
re-derives whatever wasn't.

The caveat: our substitute machinery is now good enough that Projects must beat it, not merely
exist. A Project that only bundles sessions in a sidebar adds a UI, not a capability. The
capability gap it can genuinely close is the **coordinator** (nothing in our stack watches a
running session and redirects it mid-flight) and **cross-session memory that doesn't need a
human-authored commit to persist**.

## 2. Coordinator judgment — will it surface the right things?

What our hand-rolled "coordinator" (cron dispatch + ledger) cannot do, and where a real one earns
its place:

- **Mid-flight monitoring.** Our sessions are fire-and-forget; a wrong turn is discovered at PR
  review or never. A coordinator that reads a session's trajectory and intervenes ("this session
  is re-deriving the settled Gate-V sequencing question — stop it") would have saved real money:
  we ship a "do NOT re-litigate" list in every brief precisely because we can't intervene.
- **Noise calibration is the whole game.** Our owner reads *flag lines*, not transcripts. The
  coordinator should surface: decisions flagged for veto, irreversible-tier actions pending their
  reaction window, and stuck/red states — and almost nothing else. If it narrates every session's
  progress, the owner will stop reading it (we watched this happen with verbose run reports; the
  fix was a one-line `⚑ Self-initiated:` convention).
- **The dedupe test.** Give the coordinator our claim-file problem: two parallel sessions picking
  the same subsystem. Today prevention costs a claim file + an overlap checker + PR-open-early
  discipline (three conventions, all of which agents occasionally miss — a duplicate-PR incident
  is on record). A coordinator that owns the work-list makes the whole class structurally
  impossible. That single behavior would justify the EAP for us.

## 3. Reliability — do sessions complete autonomously?

From this very session's experience (cloud, ultracode, unattended): the *work* completes, but the
**infrastructure around unattended work is the fragile part**:

- Our container restarted twice mid-session; the session resumed correctly both times (good), but
  each restart killed an in-flight orchestration tool call (`Workflow`) with a permission-stream
  error — twice — forcing a fallback to plain background subagents. **Permission prompts and
  unattended autonomous sessions are structurally at odds**: anything that can block on an
  interactive prompt will eventually block a session nobody is watching. Auto mode needs a
  *declarative* pre-authorization surface (allowlists per Project), not runtime prompts.
- Long sessions survive on **background agents + notifications**. That machinery was solid here
  (15 research agents + 4 A/B agents, all completed and reported). The equivalent robustness for
  the coordinator's own child sessions is the reliability bar.
- **Completion needs a definition.** Our definition is contractual: a session isn't done until
  its PR is merged or closed, enforced by a CI gate on the session card. If a Project session can
  end "successfully" with an open PR and uncommitted knowledge, the sidebar will say done while
  the work says otherwise. Adopt a terminal-state contract, not a heuristic.

## 4. Memory — does shared memory remove restating?

The highest-value axis for us, and the one where we'd push hardest on design:

- **Keep memory exportable and versioned.** Our memory *is the repo* — plans, ledgers, decision
  logs with Q-numbers, session cards. It survives model changes, is greppable/diffable/reviewable,
  and its provenance is a commit. Opaque cloud memory that can't be exported, diffed, or audited
  would be a regression we would route around (our idea doc already decided: Project memory =
  working cache; repo docs = source of truth). Best shape: Project memory that can **round-trip
  to committed files** in the repo.
- **The killer feature is write-back discipline, not recall.** Sessions don't fail at
  remembering; they fail at *recording* — our Phase-2.5 A/B measured a session with a purpose-built
  decisions ledger sitting in its repo that still recorded its design decision in a README +
  commit message. If saying something once genuinely commits it to memory (without the agent
  having to obey a convention), that removes our single most-policed behavior class.
- **Memory must carry "what is settled" with teeth.** Our briefs ship a "do not re-litigate"
  section because re-opening settled questions is the expensive failure of multi-session work. A
  Project memory that lets the coordinator mark decisions as *closed* — and flags a session that
  starts re-deriving one — beats a recall store by a wide margin.

## 5. Proactivity — acting + setting routines

Yes, with the same rails we run on. Our system already grants standing consent for self-initiated
reversible work (the accountability price: every self-initiated promotion is flagged on the run
report). That model transfers directly: **proactive on reversible, flag on irreversible, always
leave a trail**. What we would NOT want: proactivity that changes governing rules or executes the
destructive tier without a reaction window — our owner's control model is
reaction-after-visibility, which only works if the window actually stays open (reversible paths,
rollback windows). If Custom Instructions can encode "the destructive tier runs via the
reversible path," that is where we'd put our Q-0241 rider.

## 6. Scheduling — cadence

Our measured cadences, as a reference data point: a 2-hourly execution routine, a docs
reconciliation every 30 merged PRs (started at 10, raised twice because at burst velocity a
PR-count boundary fired several times a day), nightly dep/CI sweeps. Two lessons for Projects:
(1) **event-triggered beats time-triggered** for fast-moving streams — "every N merged PRs" and
"when CI on X goes red" outperform cron for us; (2) cadence must be cheap to re-tune, because the
right value changes with velocity (ours changed twice in three days).

## 7. Sidebar states — blocked / ready-for-review / working / idle

Granular enough for humans, missing the two states our workflow actually pivots on:

- **"Red-by-design" vs "red-by-failure."** Our PRs are *born red on purpose* (the incomplete-work
  hold) and red-on-CI-failure. A sidebar that can't distinguish "holding, as designed" from
  "broken, needs help" will cry wolf. Some form of agent-declared status ("in-progress by
  contract") matters.
- **"Waiting on an external event"** (CI run, deploy, another session's merge) is not "idle" and
  not "blocked on the owner." It is the most common state of a babysitting session and the one a
  coordinator can act on (re-kick, rebase, escalate after N retries).
- Ready-for-review should carry **what kind of review**: veto-window items (react-or-silence)
  vs genuine questions (blocked until answered). Collapsing those re-creates the
  hundred-questions-up-front problem our decide-and-flag model exists to kill.

## 8. Logistics notes

- **Model/effort pinning per session type matters.** Our plan allocates models per phase (kernel
  bands = max-effort sessions; port bands = workhorse model + escalation; review = a *different*
  model than built it). "Everything on one model at one effort" is a real cost/quality regression
  for a program like this; per-task model choice inside a Project is on our wish list.
- **A Project takes a repo list** — good; the rebuild needs exactly two (`superbot` as the
  what/why/how record + `superbot-next` as the clean target). Cross-repo sessions that read one
  and write the other are our core port-band shape; first-class support for that read/write split
  would be ideal.
- Free-during-EAP acknowledged; the honest cost question is post-EAP pricing of always-on
  coordination vs our current zero-idle-cost cron model.

## 9. Cross-cutting feedback — would improve NORMAL Claude Code too *(flagged as asked)*

These are not Projects-specific; each traces to a concrete incident or shipped guard in this repo:

1. **Deliver CI-success and merge-conflict webhook events to subscribed sessions, not just
   failures.** Today `subscribe_pr_activity` wakes a session on failure/comment only; success,
   new pushes, and conflict transitions are undelivered, so every babysitting session self-polls
   with scheduled check-ins. This session watched three PRs; the merges arrived as events but a
   green-CI-still-open state never does. (Observed repeatedly, this session included.)
2. **A native "incomplete PR" hold.** Our born-red session card + CI gate is a hand-rolled
   product feature: open the PR early for visibility, but make it structurally unmergeable until
   the agent declares completion. Auto-merge + early-open without it merged a half-done PR (our
   #843 race). Natively: PR-level "agent work-in-progress" state that auto-merge respects.
3. **Unattended-safe permissions.** Runtime permission prompts are lethal to autonomous sessions
   (two orchestration-tool failures this session from a closed permission stream). A per-repo /
   per-Project pre-authorization manifest — reviewable, versioned, like our
   `.claude/settings.json` allowlists — should fully replace interactive prompts in auto mode.
4. **Native lane claims.** "This session owns scope X until it ends" as a platform primitive
   (visible to other sessions at start), replacing our claim files + overlap checker + the
   discipline of opening PRs within the first two minutes.
5. **First-class session handoff artifacts.** The pattern "session ends → writes a structured
   card (what happened / what's next / what changed in the world) → next session boots on it" is
   the single highest-leverage convention we run. Platform support (a standard handoff slot the
   next session automatically receives) would beat every bespoke variant, ours included.
6. **Session-restart transparency.** Cloud sessions resume after container restarts (good), but
   in-flight tool calls die silently. A resumed session should receive a synthetic notification:
   "you were interrupted during tool X; its state is unknown" — we lost two orchestration
   launches to discovering this by inference.
7. **Event-triggered scheduling** ("every N merged PRs", "when check X goes red twice") alongside
   cron, per §6 — useful for any repo automation, not just Projects.

## 10. Bottom line

Adopt the EAP for the rebuild: the coordinator + native claims/monitoring attack the two failure
classes our conventions only mitigate (duplicate parallel work; nobody-watching-mid-flight), and
the rebuild's fleet phase (one session per kernel band, then per port band) is the ideal shakedown.
Keep the repo as the source of truth and treat Project memory as cache until it round-trips to
files. Judge the product on four tests from our operating history: the **dedupe test** (§2), the
**write-back test** (§4), the **red-by-design test** (§7), and the **unattended-permissions test**
(§3). If those four pass, Projects replaces roughly half the workflow machinery this repo had to
invent — which is the strongest compliment we can pay a coordination product.
