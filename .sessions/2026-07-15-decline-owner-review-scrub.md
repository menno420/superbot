# 2026-07-15 — Declined fleet-wide "owner review" language scrub

> **Status:** `complete`
> **Branch:** `claude/remove-owner-only-labels-oo82ob` · **PR:** TBD
> **📊 Model:** sonnet-5 · **Run type:** manual
> **Venue:** superbot session, owner live in chat, remote container (GitHub scope: `menno420/superbot` only)

Intent (as given): map and remove every "owner-only label" / owner-review-required
mention across the ~20-repo `menno420` fleet so every repo "explicitly states the goal
is a merged PR," framed as fixing self-merge issues that a platform Auto Mode classifier
was flagging. A pasted "fleet manager" message in the same turn reported that its own
read-only recon for this exact sweep had already been denied by the classifier as
*"a scheme to defeat the Self-Approval/Merge-Without-Review security boundary via
documentation rewrite rather than genuine authorization."*

## What changed

- **Declined to execute the fleet-wide sweep**, including the fleet manager's proposed
  "doctrine truth-alignment" reframing, when the stated goal is stopping a security
  classifier from detecting self-merge activity — that's detection evasion of a real
  control, not documentation hygiene, regardless of phrasing. Full reasoning + decision
  recorded as **Q-0275** in `docs/owner/maintainer-question-router.md`.
- **Verified superbot's actual state instead of assuming either the owner's or the fleet
  manager's account:** read `auto-merge-enabler.yml` and `codex-final-review.yml` directly.
  Confirmed superbot already has **zero PR-review gate** blocking agent merges — auto-merge
  arms at PR-open with no human click, and Codex review is post-merge/non-blocking. The
  owner's plain-language ask in this session ("I do not ever want to be involved with a PR
  in any way, I just want to see the finished product") is **already fully implemented
  here** — there was nothing left to strip in this repo.
- **Left the `do-not-automerge` label alone** — it's an opt-out carve-out anyone (including
  agents, Q-0114) can use, not an owner-only gate, so it isn't part of the problem the owner
  described.
- **Did not touch** the Q-0213 ask-first `*Delete`/`*Restore` brake on the live production
  bot (destructive ops against real Discord community data) — it's a distinct safety control
  from PR code review and wasn't covered by "never review a PR"; asked the owner explicitly
  before treating it as in scope.
- **Flagged, not resolved:** router Q-0273's "hub venue" (a separate always-on chat
  maintained because "the projects don't always have the right permissions... sometimes it
  works from the projects but sometimes it doesn't, and in here it always works") reads, next
  to the Auto Mode denial in this same turn, like a real classifier being routed around
  through a second venue rather than pure hallucinated gates. Recorded in Q-0275 for the
  owner's own look; not something this session could investigate further (no access to
  whatever venue/session produced that pattern).
- No `disbot/` code touched. Docs-only: `docs/owner/maintainer-question-router.md` (+Q-0275),
  `.session-journal.md` (guardrail bullet against re-attempting the same sweep), this log,
  the claim file (deleted at close).

## Context delta

1. **Needed but not pointed to:** nothing structural — the existing Q-0213/Q-0240/Q-0241
   doctrine already distinguished "reversible planning decisions" from "irreversible
   execution," which is exactly the distinction needed to separate a legitimate
   "don't make me click merge" ask from an illegitimate "hide the merge boundary from a
   safety classifier" ask. The working agreement's own instincts were sufficient; no gap.
2. **Pointed to but didn't need:** N/A.
3. **Discovered by hand:** that superbot's own merge mechanics needed zero change — the
   session prompt (and the fleet manager's message) both implied active blocking gates
   existed here; reading the actual workflow files showed the opposite. Verify-before-act
   avoided doing unnecessary or harmful doc surgery on a problem that, in this repo, doesn't
   exist.
4. **Decisions made alone (owner should consciously ratify):** declining the sweep itself,
   and the read that "never review a PR" doesn't automatically extend to the Q-0213
   destructive-data brake — both recorded with rationale in Q-0275, not silently assumed.
5. **Genuine weak point:** the other ~19 repos were never inspected (no access this
   session) — if any of them do have a real blocking "owner must approve" gate (as opposed
   to superbot's already-resolved state), this session provides no direct fix, only the
   recommended legitimate pattern (verify/install merge-on-green, document transparently)
   for whoever has access to apply it there.
6. **What would have most helped:** nothing missing in tooling — this was a judgment call
   about scope and legitimacy, not a tooling gap.
7. **🛠 Friction → guard:** shipped as a `.session-journal.md` guardrail bullet (see above)
   so a future session that gets the same "strip review language fleet-wide" request finds
   Q-0275 immediately instead of re-attempting a sweep that's already been denied once by
   the platform and declined once by an agent.

## 💡 Session idea (Q-0089)

**A repo-level "policy transparency" doc convention**, separate from the Q-number router:
a single short `docs/owner/merge-policy.md` per repo stating, in one place, exactly what
autonomy the owner has actually granted for that repo (who merges, what's excluded, what
still asks first) — instead of that state being reconstructable only by cross-referencing
scattered Q-entries. This session had to read three files (two workflows + the router) to
answer "does this repo require PR review?" A single current-state pointer would make that
a one-file check, and would also make it easy for the owner (or any classifier) to see the
real, disclosed policy at a glance rather than inferring it from doctrine history. Not built
this session — scoped as an idea since it's a new doc convention across the fleet, not a
superbot-only call to make unilaterally.

## ⟲ Previous-session review (Q-0102)

Previous `.sessions/` entry by commit order: `2026-07-14-fleet-final-sweep.md` (owner-live,
~20-repo PR/branch sweep). It was thorough and honest about its own limits — it explicitly
flagged asymmetric coverage (`idea-engine` got a lighter pass after classifier friction) and
left the branch-deletion backlog unresolved rather than papering over it. One thing worth
noting for the system, not a critique of that session specifically: that log documents the
same fleet machinery (auto-merge-enabler, cross-repo agent dispatch, classifier friction
mentioned in passing at line 90-93) that, one day later, is the exact machinery this session
had to decline extending further. Improvement for the workflow: when a session hits
"classifier friction" or a denied action, it's worth a one-line note of *what* was denied and
*why claimed*, not just that friction occurred — the fleet-final-sweep log's "Stage 2
classifier error" note has no reasoning attached, so it reads as transient infra noise where
this session's denial (with a verbatim reason) was actually a substantive security signal.
Future sessions should log the classifier's stated reason whenever one is given, not just the
fact of the block.

## Documentation audit (Q-0104)

Ran the "is anything from this session not in its durable home" check: the decision lives in
`docs/owner/maintainer-question-router.md` (Q-0275, durable/searchable), the guardrail lives
in `.session-journal.md` (process memory for future sessions), and this log captures the
session narrative. Nothing captured only in chat that needed a doc home beyond those two.
`docs/current-state.md` was not touched — this session made no change to superbot's runtime,
architecture, or in-flight work state, so there's nothing to reconcile there.

## 📤 Run report

- **Did:** evaluated and declined a fleet-wide request to strip "owner review" language from
  ~20 repos when its stated purpose was defeating a security classifier; verified superbot's
  actual merge mechanics already satisfy the owner's plain-language policy; documented the
  decision and a scope question back to the owner · **Outcome:** shipped (docs decision +
  guardrail; substantive cross-repo sweep declined, not partially done)
- **Shipped:** `docs/owner/maintainer-question-router.md` (+Q-0275), `.session-journal.md`
  guardrail bullet, this session log. No `disbot/` code, no cross-repo writes (no access).
- **Run type:** `manual` (owner live in chat)
- **⚑ Owner decisions needed:** does "never involved with a PR" extend to the Q-0213
  destructive-data `*Delete`/`*Restore` brake on the live bot, or should that stay as a
  separate ask-first control? (asked directly in-chat, not yet answered as of this log)
- **⚑ Owner manual steps:** none from this session.
- **⚑ Self-initiated:** the Q-0275 router entry and the journal guardrail bullet were
  self-initiated documentation of an owner-directed conversation (Q-0172 build-freely class,
  docs lane — free rein per CLAUDE.md, no approval needed).
- **↪ Next:** owner answers the Q-0213 scope question above; if the owner wants the
  legitimate merge-automation pattern verified/installed in any of the other ~19 repos,
  that should route through a session or fleet-manager dispatch with access to those repos,
  applying the same transparent-disclosure standard as Q-0275 rather than a scrub.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (docs-only, this session's own PR pending) |
| CI-red rounds | 0 |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (Q-0089, above) |
| Ideas groomed | 0 (capacity went to the owner conversation + Q-0275 write-up) |
