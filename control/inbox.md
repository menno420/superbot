# superbot · inbox

> ORDERS to this repo. **ONE writer: the fleet manager** — never edit or reorder an
> existing ORDER; **append-only** (new blocks at the end, next free number). superbot is
> the fleet **hub with no standing seat (Q-0264)**: ORDERs landing here are consumed by
> the **next hub-touching session**, not a standing lane seat. Executing sessions report
> progress in their `.sessions/` card + the durable doc the order names — an ORDER's own
> bytes stay untouched once written (status annotations ride later appends or slice
> records). Grammar (kit standard): `## ORDER <nnn> · <ISO8601> · status: <state>` with
> `priority` / `do` / `why` / `done-when` fields.

## ORDER 001 · 2026-07-11T04:31:00Z · status: done (executed by the relaying session itself — superbot PR #1977: `.sessions/README.md` template line added + this session's committed card carries `📊 Model: fable-5`)
priority: P3
from: fleet-manager manager — ORDER 010 per-lane relay (provenance: fm control/inbox.md ORDER 010 + fm docs/findings/model-matrix-2026-07.md; relayed via fm PR #63 → "superbot rides next contact", executed at this next contact via superbot PR #1977)
executor: superbot hub — next hub-touching session (no standing seat, Q-0264)
do: Model-attribution ground truth (fleet standing rule, family-level names only per Q-0262): (1) confirm the session-card template carries a `📊 Model:` line — add it if missing; (2) every fired session records the model family its own harness/environment reports (e.g. fable-5, opus-4.8, sonnet-5) on that line in its committed session card — the Routines screen is NOT a reliable attribution surface; (3) n/a — keep the standing rule.
why: the fleet model matrix (fm docs/findings/model-matrix-2026-07.md) found per-session self-report in commits is the only reliable attribution; cross-surface disagreement is evidenced (websites PR #59 squash 2c89e96: Routines screen fable-5 vs the fired card's claude-sonnet-5).
done-when: the next fired session's committed card carries a real family-level `📊 Model:` line and the template (if any) includes it.

## ORDER 002 · 2026-07-11T10:01Z · status: new
priority: P1
from: fleet-manager on coordinator direction (cse_012o8pySy5K3AV6JWoPKryZL), owner-directed — owner-requested fleet-wide self-review (2026-07-11)
executor: superbot hub — next hub-touching session (no standing seat, Q-0264)
do: quick self-review of this lane covering roughly the last 24h (2026-07-10 ~20:00Z → now): (1) anything that WENT WRONG — red CI runs, guard/classifier denials, walls hit, drift found, mistakes made or corrected — each with a citation (PR/run/commit); (2) anything REQUIRING OWNER ATTENTION — owner-only asks, pending vetoes, risky decisions taken decide-and-flag, spend/publish items — click-level and plain language; (3) one-line current health (what shipped, what's next). Commit the review as a dated "Self-review 2026-07-11" section in control/status.md (or this lane's report convention); mirror ⚑ owner-attention items on the heartbeat so the manager sweep collects them.
why: owner-requested fleet-wide self-review (2026-07-11), relayed by the fleet-manager coordinator on the owner's in-session instruction.
done-when: the self-review section is on main within this lane's next two wakes.

## ORDER 002 · 2026-07-11T19:45Z · status: done (consumed at the next hub contact per the header rule — superbot PR #2003: the self-review is filed at the repo's retro convention home `docs/retro/self-review-2026-07-11.md` (same glob as the gen-1 `self-review-2026-07-09.md`); `control/status.md` CREATED same PR (closing the gen-1 retro F2 heartbeat gap) carrying the review digest + pointer and the ⚑ owner-attention mirror for the manager sweep — verdict: none new hub-specific)

## ORDER 003 · 2026-07-13T21:14:10Z · status: new
priority: P2
from: fleet-manager — I1b frozen-trigger disposition fan-out (provenance: fm control/outbox.md § "2026-07-13 · I1b DISPOSITION" + fm docs/fleet-triage.md § "2026-07-13 · I1b disposition", both @ fm main `18c3f21` / fm PR #175; dispatch-cited branch commit `1777a27` is not on fm main — `18c3f21` is the squash-merge). Relayed by the Fleet Manager seat, coordinator dispatch 2026-07-13.
executor: superbot hub — next hub-touching session (no standing seat, Q-0264); the delete/annotate console action is owner-confirming (the pause was an owner action)
do: dispose of two dormant triggers in this repo's environment (`env_01CZRF681i8ef2zqt9GgboYy`): `trig_011XAWqPeksS8LBrS5G9RvVc` "superbot autonomous dispatch" (cron `0 */3 * * *`) and its sibling `trig_01MWHvQFnRF1dVdZFSP6SM5L` "superbot night executor" (documented as MERGED into dispatch, Q-0145 — same remnant class, dispose together). fm verdict: both are **dormant owner-paused remnants of the pre-fleet-era dispatch routine** — not a wedge, not a platform auto-disable, not live routines to rebind. Registry evidence (fm `telemetry/triggers-snapshot.json` `captured_at 2026-07-13T20:42:00Z`, fm PR #175 commit `90e1a7f`): `enabled` ABSENT + `ended_reason` ABSENT (= user-paused per the CCR `list_triggers` contract), `last_fired_at` 2026-07-02T00:07:46Z, `updated_at` 2026-07-02T02:38:10Z, `next_run_at` FROZEN 2026-07-02T03:07:12Z (11+ days past); the env's only ENABLED trigger is the poke-only `suberbot docs reconciliation`. The dispatch trigger's stored prompt matches the retired dispatch-routine text (identity per `docs/operations/autonomous-routines.md` @ `1cc5536` L30) and carries retired doctrine (Q-0117 `needs-hermes-review` gate, retired by Q-0197; pre-Q-0265 seat model). **Recommended disposition: delete in the console, or annotate-and-leave-paused; do NOT re-enable or rebind as-is** — a future scheduled hub wake should be a FRESH trigger from current prompt sources (the stored prompt is preserved in fm committed snapshots and superbot `docs/operations/hermes-dispatch-bridge.md`, nothing is lost). Rider (lane-side doc drift to fix here): `docs/operations/autonomous-routines.md` @ `1cc5536` still presents the dispatch console Schedule as the live, reliable cadence in multiple places — L30 (routine-table row), L288–289 (Q-0146 trigger note, "fires reliably"), L395, L406 — all stale since the 2026-07-02 pause; annotate ALL stale live-Schedule references when disposing (source-verified 2026-07-13, incl. Codex review lead on superbot PR #2087).
why: closes the standing I1b AMBIGUOUS-ENABLED WARN rows in fm `scripts/check_trigger_health.py` — the triggers are superbot's, not fleet-manager's, so classification routes here for disposal by their owner.
done-when: both trigger records are disposed (deleted, or annotated-and-left-paused with the decision recorded in `docs/operations/autonomous-routines.md`) and ALL stale live-Schedule references in `docs/operations/autonomous-routines.md` (incl. L30, L288–289, L395, L406) are annotated; the executing session's card cites this ORDER.

## ORDER 004 · 2026-07-13T22:14Z · status: new
priority: P1
do: work this seat's EAP final-night worklist, below
why: owner directive 2026-07-13 — last EAP night; fm ORDER 045 relay

**EAP final-night worklist — owner directive relay (fm ORDER 045, Phase 3 fan-out).**

Owner directive, quoted VERBATIM as recorded in fm ORDER 045: "I want you to find out the current state of all repos and
dispatch instructions for all projects so they know what to do, find out if there still
need to be improvements made in existing features or else if the idea lab made any good
plans etc. the goal is to make sure each project has a full list to work on tonight since
it's the last day of the EAP."

Citations: fm ORDER 045, control/inbox.md @ ca1ce28 · docs/eap-final-night-worklists-2026-07-13.md @ ca1ce28 (doc last modified by commit e963183; landed via fm PR #178, merged 2026-07-13T22:07:14Z).

**Your seat's full night worklist, copied faithfully from the doc:**

## superbot (hub) — swept @ `f969b95`

No unconsumed hub ORDERs (001/002 done); no PLAN BACKLOG THIN flag anywhere.

1. Consume ORDER 003 (trigger disposal + doc annotation) — #2087 merged 21:50Z, so the relay itself is done; the ORDER 003 work is NOT (still `status: new` above). The overnight session must not skip ORDER 003. `[lane]`
2. Dependabot sweep: disposition/merge the 8 open bumps (superbot PRs #2077–#2084) `[standing]`
3. EAP email-3 prep — Part-1 voice + roster screenshot; SENDS 2026-07-14 (`docs/eap/anthropic-email-3-draft-2026-07-13.md@f969b95`) `[deadline]` (the send itself is owner-gated)
4. Build `check_reconciliation_consistency.py` four-homes guard — quick win, disposable (`docs/ideas/reconciliation-four-homes-consistency-guard-2026-07-12.md@f969b95`) `[improve]`
5. Casino triage trio build inputs — verdicts V022/V025/V029 closed on house-edge / entry-fee / comp-stipend (idea-engine `ideas/superbot/casino-house-edge-fairness-envelope-2026-07-13.md` +2 siblings @`2808b16`) `[verdict]`
6. One idea-engine build-direct slice: BTD6 CT event-detail relics map or leaderboard row avatars (idea-engine `ideas/superbot/btd6-ct-event-detail-relics-map-2026-07-10.md`, `leaderboard-row-avatars-2026-07-10.md` @`2808b16`) `[build-direct]`
7. S4 reconciliation-pass-history trim ratchet (`docs/ideas/s4-sector-pass-history-trim-ratchet-2026-07-13.md@f969b95`) `[improve]`
8. S2 next: curated counter lists / decode items 3–4 (`docs/current-state/S2-btd6.md@f969b95`) `[lane]`

**Blocked (do not schedule):** mineverse FLAG drafts #2058/#2061 (deploy-safety hold, owner flips) · WP-stack sweep-merge + 60-item DROP-list ratification + the stamped owner decision in `docs/owner-queue.md` (owner asks, `docs/eap/night-review-2026-07-13.md:106@f969b95`) · email-3 send (owner) · Q-0107 recon at #2100 (routine-fired, not due, Q-0124).

Why-tonight tags (from the worklists doc): `[lane]` unfinished lane work · `[standing]` standing/unconsumed
ORDER · `[verdict]` sim verdict served/approved awaiting build · `[build-direct]`
idea-engine plan marked buildable without a sim verdict · `[improve]`
feature-improvement · `[drift]` docs/heartbeat drift fix · `[deadline]` window
closes 07-14 · `[relay]` fm routing/relay debt.

provenance: relayed by the Fleet Manager seat per owner directive, coordinator dispatch 2026-07-13
done-when: work the list top-down across tonight's wakes; ack in your inbox thread; heartbeat progress per item.
