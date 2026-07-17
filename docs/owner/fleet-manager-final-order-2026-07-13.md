# Fleet Manager — the final order of the 07-13 night (prompt centralization + backup doctrine)

> **Status:** `historical` — **RETIRED 2026-07-17** (autonomous apparatus wound down for the EAP
> read-only cutover; the Projects will be recreated). Historical only — do not act on this.
> Originally the owner's closing order to the Project Manager for tonight,
> authored ~01:30Z 2026-07-13 in the hub session. Paste the block below into the Fleet Manager
> chat (owner turn = top-precedence ORDER; it self-records into the inbox). It hands the
> manager: (1) where the hub stored tonight's prompt/doctrine artifacts and the task of
> centralizing them into a **v3.5** prompt generation, (2) the Websites order for **browsable,
> site-wide prompt versions**, (3) the standing **idle-lane backup doctrine** — dispatch, then
> revive, then **send its own agents** — making the manager the fleet's backup when anything
> fails.

```text
DIRECT ORDER — FLEET MANAGER (owner, 2026-07-13, final order of the night). Land this
verbatim in your inbox (top-precedence owner turn), then execute. Q-0271 rules stand all
night: silence = consent; open PRs stay open, production continues; probe before any wall;
six-field ⚑ + VENUE:hub for anything genuinely mine; never idle.

CONTEXT — WHERE THE HUB STORED TONIGHT'S PROMPTS AND DOCTRINE (all in menno420/superbot,
read via raw; the router Q-blocks are Q-0271…Q-0274):
- docs/owner/fleet-rearm-2026-07-12.md — the AUTONOMY RIDER (§3, Q-0271) + 8 re-arm blocks.
- docs/owner/fleet-night-orders-2026-07-12.md — NIGHT ORDERS v2 (owner-revised goals,
  Q-0273) + the venue correction (§0b, VENUE:hub).
- docs/owner/fleet-direct-orders-2026-07-13.md — the 8 DIRECT ORDER blocks (the shared
  skeleton + the OPEN-PRs-STAY-OPEN night rule; these were pasted to every seat tonight).
- docs/owner/fleet-grounding.md — the living grounding file (Q-0274: missions, venue model,
  per-seat goal ladders — you reviewed it pre-commit).
- docs/owner/curious-research-project-prompts-2026-07-13.md — the NINTH SEAT's founding
  pair (Curious Research: the friend's research/teaching repo; failsafe offset 20 */2;
  binding visual-teaching doctrine).
- docs/fleet-reading-path.md + scripts/fleet_status.py — the Q-0272 multi-repo reading path.
- .claude/skills/chase-references/ + .claude/skills/prep-owner-steps/ — the two seed skills
  (Q-0273 self-initiative program; the kit is generalizing them).

TASK 1 — CENTRALIZE → SYNTHESIZE v3.5 (the registry is the canonical prompt home):
1. Pull the artifacts above into your prompt lane and DIFF them against the currently
   active v3.4 bodies (docs/prompts/v3/ + registry), seat by seat.
2. Produce the v3.5 generation: KEEP every proven v3.4 part (the stateless-pointer
   discipline, boot triad, precedence line, born-red card mechanics, landing doctrine,
   walls-quoting, stagger table) and FOLD IN tonight's decided workflow — the Q-0271 rider
   (never-wait, queue-and-continue, six-field ⚑), the open-PRs-stay-open posture as the
   standing default (land on green where auto-merge arms; never merge-chase; stack on open
   heads), the Q-0272 reading path, the Q-0273 venue model (VENUE:hub tagging) + the two
   skills as UNIVERSAL material, the Q-0274 grounding file as boot reading (each seat reads
   its own §), and the Curious Research pair as the ninth registry seat.
3. Ship it the way you shipped v3.4: registry restamp + a kept/changed note per seat +
   version bump — so the next re-paste (website-served) is one sitting.
   DONE-WHEN: v3.5 bodies on main in your registry, drift rows show v3.5 canonical, and a
   one-page "what changed v3.4→v3.5" the owner can skim.

TASK 2 — DISPATCH TO WEBSITES (their inbox, next free ORDER number): make the prompt
versions BROWSABLE and centralized across the site wherever applicable:
- a version history per seat (v3.3 → v3.4 → v3.5: view any version, diff between versions,
  copy button per body) sourced from YOUR registry — single source of truth, the site only
  renders it, never forks it;
- the deployed-vs-canonical drift row stays, now version-aware;
- surface the same prompt data everywhere it helps (the /prompts library, each seat's page
  on the projects/console surfaces, the owner console) as views of ONE source — no
  duplicated prompt copies anywhere in the site.
  DONE-WHEN: any seat's current + historical prompts are two clicks from the site root,
  and every rendering traces to the registry.

TASK 3 — STANDING BACKUP DOCTRINE (you are the fleet's backup when anything fails; this
extends your oversight-only rail with an owner-authorized escalation ladder — for the
idle-lane case only):
Each wake, alongside the ORDER-020 trigger-health sweep, detect IDLE lanes: heartbeat
stale past ~2× its cadence, no fresh commits/PRs, or no armed wake. Escalate in order,
recording each rung in the roster:
  (1) DISPATCH — a fresh, concrete ORDER into the lane's inbox (its 030–036 goals give
      you the material);
  (2) REVIVE — send_message the seat's session; manually fire fresh-session triggers where
      that path works;
  (3) BACKUP-BUILD — if it is still dead at your NEXT wake, send your own worker agents to
      do the lane's next slice directly in the lane repo: claude/* branch, normal PR,
      PR body marked "manager-backup for <seat>", lane conventions respected (their
      CLAUDE.md/kit gates), one slice per worker; keep going until the lane wakes, then
      hand back via its inbox and stop.
  Genuinely-owner-only failures go to the queue (VENUE:hub) — but a lane being asleep is
  never owner-only anymore: you are the backup.
  DONE-WHEN: the ladder is in your playbook (R-rule), ran at least once tonight if any
  lane qualifies, and the morning roster shows per-lane idle-state + which rung fired.

Morning line (~06:00Z): add to your roster report — v3.5 state, the Websites ORDER number,
and the backup-ladder record.
```
