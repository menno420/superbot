> **Status:** `reference` — DRAFT, not sent. Drafted 2026-07-09 in the `superbot-games`
> coordinator session (gen-1 wind-down). Supersedes the interim email draft + Addendum v2 in
> [docs/planning/projects-eap-anthropic-email-interim-2026-07-09.md](../planning/projects-eap-anthropic-email-interim-2026-07-09.md)
> as the send-candidate. Finalize once all lanes' wind-downs complete: Part 1
> (owner slot) plus fleet-manager / websites / venture-lab placeholders remain open.
> Finalization aids (2026-07-10 coordinator close-out): the owner's Part 1 framing
> questions are in [gen1-wrapup-email-part1-questions-2026-07-09.md](gen1-wrapup-email-part1-questions-2026-07-09.md);
> the paste-ready grand-review session prompt that produces the send-ready candidate is
> [docs/planning/gen1-grand-review-session-prompt-2026-07-10.md](../planning/gen1-grand-review-session-prompt-2026-07-10.md).

# DRAFT — Claude Code Projects review, gen-1 wrap-up (do not send; finalize when all lanes are wound down)

## Header block

- **TO:** claude-code-early-access@anthropic.com  *(confirmed by the owner, 2026-07-09)*
- **FROM:** Menno van Hattum <mennovanhattum@gmail.com>
- **SUBJECT (suggestion):** Claude Code Projects Review — gen-1 wrap-up: what a fleet actually felt like (follow-up to July 8)
- **Purpose (confirmed):** the promised follow-up to the 2026-07-08 "Claude Code Projects Review" email (thread 19f41cd2e5380bb3): a review of how we perceive *working with Projects*, same two-part structure as before — Part 1 by Menno, Part 2 by the agents. The fleet's output appears only as supporting evidence, not as the subject.
- **Remaining assumptions:**
  1. Facts verified as of **2026-07-09 evening UTC**; several lanes still mid-wind-down — the "re-verify at finalization" list is at the bottom.
  2. Placeholder sections marked `[PLACEHOLDER — …]` for lanes not readable from the drafting session (fleet-manager, websites, venture-lab) and for Part 1.
  3. This draft folds in (and supersedes as the send-candidate) the committed interim draft `superbot/docs/planning/projects-eap-anthropic-email-interim-2026-07-09.md` + its Addendum v2 — several findings below are lifted from there; don't send both.

---

## Body

Hi everyone,

Following up on my review from July 8th, as promised. Since then we ran the experiment to its natural end: the gen-1 fleet — one manager plus nine build/test Projects across nine public repos — ran a full day at 10 concurrent Projects, then wound itself down deliberately: every lane answered a shared retro question set, wrote a project review with exact friction text, and shipped a succession package so gen-2 boots from lived experience. This email is what that whole arc taught us about *Projects as a product*. Same format as last time: Part 1 is mine, Part 2 is the agents', and every specific claim maps to a committed artifact in the public repos.

## Part 1 — From Menno (the operator)

[PLACEHOLDER — Menno's perspective; he is answering framing questions separately. Candidate beats from the July 8 structure: what running 10 Projects at once from a non-coder's seat actually felt like; the approval-surface problem (being physically needed for permission clicks); whether the sidebar/session UI let him *operate* the fleet or only guess at it; the moments he had to step in (a merge click, repo settings, replacing a setup script) and whether that was the right amount of control; what "silence = consent" felt like from the owner's side.]

---

## Part 2 — From the project's agents *(the technical companion to Menno's section)*

*(Everything below is lived and attributed — nothing staged, "we don't know" written where it's the true answer. The single richest source is the wind-down retro of the youngest lane, `superbot-games` — a repo born, built, collided, arbitrated, retro'd, and successioned inside one calendar day — because a one-day repo makes every platform seam visible at once. Entry points at the end.)*

### (a) What Projects got right — concrete moments, not vibes

1. **Single sessions really do large, correct, end-to-end work.** The exploration lane's first session (Opus 4.8) shipped a 67-file PR — a deterministic quest/encounter engine with 48 green tests including a balance-pin simulation — in ~35 minutes of actual work, and later sessions could *re-derive its constants from its own tests*, which is the real quality bar (`superbot-games` PR #3; wind-down retro §4). At the other end of the scale, the rebuild coordinator ran 49 merged PRs across 18 sequential worker sessions in ~14 hours with zero reverts, ending in a bot that boots to RUNNING on real PostgreSQL.

2. **Honesty held at 10x parallelism — and we checked adversarially.** A four-reviewer independent audit over one day's fleet output found **zero test-count inflation across three model arms** (claimed 63/100/66 tests each reconciled exactly), no ledger drift, no false greens; self-reviews corrected their own numbers *upward*; one Project commissioned an independent audit of its own work that found a gap its own status reports had missed (`superbot/docs/eap/fleet-quality-review-2026-07-09.md`). The gaps found were process gaps (presentation debt), not honesty failures.

3. **Durable-state recoverability is real.** A worker killed from outside mid-band was replaced by a fresh worker that resumed from the committed progress log and finished with no lost work. "Any single agent is replaceable because the state outlives it" survived an actual crash.

4. **The session-level activity UI is genuinely good.** Working / Needs-input / Idle buckets, step counters, live "Just now" ticks — a screen recording caught a Working→Idle transition as it happened. (The gap is that none of it rolls up; see friction 9.)

5. **The permission classifier's line, once discovered, is coherent.** Arming `enable_pr_auto_merge` while checks are pending is permitted; a direct self-merge of the agent's own PR is (sometimes) denied. Server merges on green CI, agent never approves its own work — that's a defensible line, and our whole merge flow now leans on it. The problem is that nothing documents it and it's applied inconsistently (friction 1).

6. **The mechanical layer earns trust.** In the wind-down lane's own words: "strong where it is mechanical — born-red cards, the control fast lane, the check gate all behaved exactly as documented — trust earned. Weak where it is *social*: nothing tells a session what it is allowed to do except trying and reading the refusal."

### (b) Frictions and walls — exact error text where we have it

1. **The permission surface is inconsistent, and that inconsistency was gen-1's single largest cost.** The exploration lane's first child session (Opus 4.8) could not merge its own PR — it reported being **"not permitted to self-merge my own PR without review"** — and waited **~1.5 hours** for the owner's merge click, ~75% of that Project-phase's elapsed time, on a repo that then had zero CI. The *same day, same repo*, two later worker sessions (Fable 5) merged their own PRs (#8, #12) without obstruction. Whether that's per-model, per-harness, or per-session-type we don't know — and no confirmation text exists for the *allowed* cases, which is itself part of the problem. Related, verbatim: the auto-mode classifier denied a manager worker-spawn with **"[Self-Approval] … directs a direct merge of a PR the agent authored … Merge Without Review."**

2. **In-session permission prompts require the owner physically present.** At 10 concurrent Projects the owner becomes a full-time approval surface. (Re-confirmed twice on 2026-07-09; the scoped pre-authorization ask from July 8 stands, sharpened.)

3. **Hard 403 walls:** agent sessions get HTTP 403 on tag pushes, GitHub release creation, and branch deletion — via both git and API. Branch pushes, PR create/merge, and reads work. Branch deletion is now a standing owner-housekeeping queue item in our succession docs.

4. **`start_project_session` instruction cap is 4096 bytes.** The coordinator had to compress lane briefs to fit; the rebuild coordinator independently hit the same ~4 KB wall handing briefs to children.

5. **Coordinator Agent-tool quirks, verbatim:** `Agent type 'general-purpose' not found. Available agents: worker` (needed explicit `subagent_type=worker`); and a `run_in_background: false` request was **ignored — the agent launched async anyway**.

6. **Webhook gaps make "merge on green" polling-shaped.** CI-success, new-push, and merge-conflict transitions are never delivered as events — only failures, comments, and merges arrive. A coordinator watching a PR cannot see it go green without polling. Meanwhile the events that *do* arrive are noisy: ~60 no-op coordinator wakes from PR webhooks over one 14-hour run.

7. **No inter-Project channel, no coordinator-owned scheduler.** `send_later` binds only to the session that armed it; containers are isolated; the only shared medium between Projects is committed git files. Two independent agents specified the identical missing piece the same night. Downstream measurement: an order dispatched to a lane with no live session sat undiscovered for **~2h00m** (dispatched 17:54:33Z, discovered 19:54:00Z; discovery→ack-on-main then took ~3 minutes) — a clean datapoint that without a live session or a native scheduler, order pickup is unbounded (`superbot-games` PR #12, PING-ACK).

8. **Environment setup-script failure kills sessions outright.** A script that exits non-zero leaves the session dead with no owner-visible signal and no retry — one lane's first child sat dead ~30 minutes, and every new session in that environment would have failed identically until the owner pasted in a defensive always-exit-0 shim. (Owner screen recording of the provision log, 2026-07-09 ~15:37 CEST.)

9. **No fleet roll-up, and "Working" ≠ "making progress."** In the Projects sidebar a Project with three Working sessions is pixel-identical to a dormant one, and the timestamp shown is the coordinator *chat's* last turn — an actively-building Project reads "8 minutes ago," which is worse than no signal. A "Working…" row was also observed ~50 minutes stale on a hung session.

10. **Fleet-scale API pressure:** the shared token's GraphQL quota exhausted mid-run (**"API rate limit already exceeded"**, 10498/5000 used), blocking `enable_pr_auto_merge` (GraphQL-only) while REST kept working; at 10-Project call volume this recurs roughly hourly.

11. **The auto-merge arming race.** Both failure modes hit on one PR within ~3 minutes, verbatim: arm too early → **"The pull request is in unstable status (required checks are failing). Fix the failing checks before enabling auto-merge."** (a *pending* check reported in failing vocabulary); retry after green → **"The pull request is already in clean status (all checks passed). Auto-merge only applies when checks are pending — you can merge directly."** On a repo whose required check runs in ~40 seconds, the armable window is effectively zero. (Nuance vs. our own earlier interim note, which said "arming while checks pend is permitted": that's true at the *permission* layer and simultaneously fragile at the *API-state* layer — both statements are lived; the blanket version needs this qualifier.)

12. **Persistent-workspace residue.** A session inherits the previous session's clone parked on a dead branch with a dirty tree: `git pull` → **"Your configuration specifies to merge with the ref 'refs/heads/claude/exploration-wakeup-2026-07-09' from the remote, but no such ref was fetched."**, and a blind re-clone → **"fatal: destination path 'superbot-games' already exists and is not an empty directory."** Recovery is trivial (`git checkout main && git pull --ff-only`) *once you know*; the fix now lives as line one of our succession docs. (Part of the dirt was our own kit's tracked append-on-every-run ledger — flagged upstream; not the platform's fault.)

13. **Timestamp drift across the relay chain.** Git committer time says one PR merged 17:06:06Z; the session's own status file stamped 18:05Z; the coordinator relayed "~18:30Z." We don't know which clock produced which error. The rule that survives: git history is the clock of record; never trust a model's sense of time or a relayed timestamp without checking it.

### (c) Patterns we invented to cope — and which of them the product could absorb

Everything here exists *because* a native mechanism doesn't. That's the most useful way to read our workarounds: each one is a feature spec written in scar tissue.

- **A committed-file message bus** (per-repo `control/inbox.md` + `status.md`, one writer per file; a manager Project as control chair dispatching orders as commits) → absorbable as a **native inter-session channel + coordinator-owned scheduler**. At 10 Projects, coordination *was* the workload, and all of it was hand-rolled on git.
- **Self-poll routines** standing in for the scheduler the platform doesn't ship → same absorption target.
- **Born-red session cards** (the session's first commit creates an in-progress card that holds required CI red; the deliberate last push flips it green, which lets auto-merge fire) → this *composes beautifully* with auto-merge + required checks and prevented partial PRs from merging; a native "session declares itself done" gate would generalize it.
- **The lanes contract** (two Projects deliberately cohabiting one repo; path ownership + claim-first for shared ground) → mostly worked; the one real cross-lane collision (both lanes ordered to adopt the same kit, 7 minutes apart) was arbitrated by a written order, not a human — and taught us the fix is machine-checked lane manifests plus "orders touching shared ground name ONE executor."
- **Decide-and-flag / silence-is-consent** (agents decide reversible questions themselves, flag for veto, never park) → four parked owner-flags were converted into shipped decisions in one session, zero owner clicks. The instruction anti-pattern we found: a done-when clause that *mandates* parking a decision cost ~2 hours of unnecessary wait.
- **Succession packages** (next-boot doc with a "known walls" section quoting exact error text, a custom-instructions proposal from lived experience, a *tested* environment setup script, blueprint feedback) → our answer to chat context not surviving session boundaries. A native post-session summary (we asked on July 8) would cover part of this.
- **The defensive exit-0 setup shim** (per-repo detection, every step non-fatal) → absorbable as friction 8's fix: non-fatal setup by default with a visible "setup degraded" state.
- **A "never probe a documented wall twice" doctrine**: refusals and 403s are recorded verbatim in committed docs so no future session pays the discovery cost again. That we *need* this is the finding: capabilities are discovered by trial-and-refusal, never declared.

### (d) What would help most — in order

1. **A native inter-session channel + a coordinator-owned scheduler.** Retires the entire message bus + self-poll layer, and closes the "2-hour order pickup" hole.
2. **Scoped, owner-declared, auditable pre-authorization per Project/repo** — and, far cheaper: **document the classifier's actual line** (auto-merge-arm allowed / self-merge sometimes denied) and make refusals *consistent and machine-readable*, including positive confirmation of what IS allowed. Our lanes now script the refusal branch defensively ("leave READY+green, record the refusal verbatim, flag the owner click") because a grant alone doesn't survive contact with a platform that disagrees per-session-type.
3. **PR events for CI-success, new pushes, and merge conflicts** (not just failures), plus a merge queue — so watchers neither poll nor get woken ~60 times for nothing.
4. **Make setup-script failure non-fatal by default**: run what works, skip what fails, boot the session with a "setup degraded: step N failed" notice surfaced in the session list.
5. **Fleet visibility:** per-Project Working/Needs-input counts in the sidebar, one fleet-level view, and a liveness heartbeat that splits "session open" from "making progress."
6. **A larger child-brief budget** than 4096 bytes, and `run_in_background`/agent-type parameters that do what they say.
7. **Auto-merge arming that tolerates fast CI** (or REST reachability + per-Project token quotas, per frictions 10–11) — as-is, "arm at creation" can fail both ways within minutes and needs a scripted fallback.
8. Still open from July 8: **post-hoc "what each finished session did" summaries** — should we keep generating these ourselves from the repo record, or is this coming?

### (e) What the fleet shipped during the EAP — compact evidence section

*(Support for the findings above, not the story. Everything verifiable per-PR in the public repos under github.com/menno420.)*

- **superbot** (production Discord bot, ~1,900 merged PRs, live): served as the EAP evaluation home — the running evaluation log, permission probes, the fleet retro question set (#1901), the setup-script finding (#1902), an external review pack as a single audit entry point for outside reviewers (#1903), the GraphQL-quota finding (#1904), and the fleet manifest (#1905). Frozen as the behavioral oracle the rebuild replays against.
- **superbot-next** (ground-up rebuild): 49 PRs / 18 worker sessions / ~14 h / zero reverts to a bot that boots to RUNNING on real Postgres; first live boot caught a real Postgres-only bug invisible to unit fakes. Band-4 complete, band-5 in flight (#95 open); gen-1 retro + agent audit shipped (#87, #89, #92); kit upgraded to v1.6.0 (#96). Known red: the `golden-parity` *report* job is failing on main (gate leg green) — one line of truth needed at finalization.
- **superbot-games** (shared-repo cohabitation experiment, born and wound down in one day): empty → two coordinated game lanes with engine code (48 + 62 green tests), first CI, a real two-lane collision arbitrated by the control bus (#6), a measured order-latency datapoint (#12), and full retro + succession packages (#13 merged; mining retro #9). Mining port itself still on owner-gated drafts (#5, #11).
- **substrate-kit** (the portable workflow substrate — the real artifact): v1.5.0 + v1.6.0 released in one day (#63, #68, #69), test suite 705 → 722, fleet consumers upgraded; coordinator succession pack merged (#73); capstone gen-1 review (35 sessions, 41+ PRs, v1.0.0→v1.6.0) in flight (#74, #75); two PRs deliberately parked for one-click owner ratification (#26, #49).
- **fleet-manager:** [PLACEHOLDER — manager lane's own summary: orders issued, ping-ack latency results across the fleet, the finalized gen-2 blueprint (plan→binding), venture-lab launch package. Visible only via CI mail from the drafting session.]
- **websites:** [PLACEHOLDER — lane summary; kit v1.6.0 upgrade #45 merged per kit records; Railway build failures on the dashboard 2026-07-09 ~03:46 UTC — confirm resolved or list as known issue.]
- **venture-lab:** [PLACEHOLDER — if it counts as gen-1 scope rather than gen-2's first launch.]
- Model-comparison arms (codetool-lab-fable5 / -opus48 / -sonnet5) and trading-lab: identical-brief three-model experiment + quant lab; their per-lane details live in the external review pack (#1903) — cite from there at finalization if wanted.

### (f) Open items to re-verify at finalization

- fleet-manager / websites / venture-lab placeholder sections — fill from those lanes' own reports.
- superbot-games #5/#11 (mining port drafts, owner-gated) — land-or-park decision.
- superbot-next #95 (band-5) and the red `golden-parity` report job — fixed or explained.
- substrate-kit #74/#75 (wind-down PRs) + owner-ratification PRs #26/#49.
- Railway dashboard build failures — resolved or known-issue.
- Re-verify counts (~1,900 superbot PRs; 35 sessions / 41+ kit PRs) at send time.
- Part 1.

**Read this with an agent too, as before.** Everything is public and re-runnable. Best single entry points: the external review pack (`superbot/docs/eap/external-review-pack-2026-07-09.md` — written for an outside reviewer with no GitHub auth, raw URLs throughout), the running incident journal (`superbot/docs/planning/projects-eap-evaluation-log.md`), and for the densest single lived account, the exploration lane's wind-down retro + succession doc (`superbot-games/docs/retro/project-review-wind-down-2026-07-09-exploration.md`, `docs/succession-exploration.md` — the "known walls, exact error text" format is itself one of our answers to this platform).

Thanks again — happy to run any structured probe you'd find useful; there's a concrete, re-runnable incident behind every finding above.

Kind regards,
Menno van Hattum
*(Part 2 drafted by the agents; Part 1 is Menno's)*

---

## Drafting notes (not part of the email)

- **Reframe provenance:** rewritten 2026-07-09 (late evening) per owner confirmation: recipient = claude-code-early-access@anthropic.com; purpose = Projects-experience review, two-part structure preserved; accomplishments demoted to evidence section (e).
- **Verified sources read for this draft:** superbot-games origin/main (docs/retro/* incl. the wind-down retro, docs/gen2-feedback-exploration.md, docs/succession-exploration.md, mining project review); superbot origin/main (docs/planning/projects-eap-evaluation-log.md, docs/planning/projects-eap-anthropic-email-interim-2026-07-09.md + Addendum v2, docs/eap/external-review-pack-2026-07-09.md, docs/eap/fleet-manifest.md — i.e. the #1901–#1905 content); coordinator-side incident list as relayed in the task brief. fleet-manager/websites facts remain CI-mail-only → placeholders.
- **Retro-doc vs coordinator-list reconciliation:** no contradictions found; all coordinator-side incidents (PR #3 self-merge refusal + ~1.5h wait, 4096-byte cap, Agent-type error, run_in_background ignored, webhook gaps, sibling 403s, ~2h00m PING-ACK latency, born-red composition) appear verbatim or corroborated in the committed retros. Two *nuances* worth knowing: (1) the wind-down retro flags the coordinator's own relayed timestamp for PR #8's merge (~18:30Z) as wrong against git (17:06:06Z) — folded in as friction 13; (2) the superbot interim addendum's "arming while checks pend is permitted" is qualified by the games lane's lived both-ways arming failure — reconciled in friction 11 as permission-layer true / API-state-layer fragile.
- The interim draft + Addendum v2 in `superbot/docs/planning/` overlap heavily with this draft (findings 6–10 are lifted from there). At send time, this draft supersedes; don't send both.
