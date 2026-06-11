# Gap analysis — what's missing and on no list (2026-06-11)

> **Status:** `ideas` — agent answer to the owner's direct question "can you
> come up with anything that's still missing from either the bot or the AI
> system?" (end of the vision-capture conversation). Each item was dedup-checked
> against V-01–V-16, AG-01–15, the teardown dossier, the roadmap queues, and the
> router before capture. **Not a plan, not approval.**

## Bot-side gaps

1. **Cross-server character identity — the unasked architectural question of
   the public era (→ router Q-0091, open).** Every game table is keyed
   `(user, guild)`: a player's character exists *per server*. The moment the
   bot is public (Q-0080), this becomes the biggest invisible product
   decision: per-guild characters (every server a fresh start — clean
   economies, matches equal-start PvP, but progression doesn't travel) vs.
   global identity (portability, but server economies bleed into each other)
   vs. a hybrid (global cosmetics/titles, local progression). Re-keying later
   is a migration nightmare — the decision should exist *before* ecosystem #2
   multiplies the tables.
2. **Per-user data export & erasure — V-15's mirror twin.** We're designing
   *import* of player stats; nothing anywhere offers a player *export* of
   their own data or self-service erasure. For a public bot this is
   trust-infrastructure (and GDPR-adjacent: the owner is EU-based). Cheap
   version: one command producing a JSON of everything keyed to your user id
   + an erasure flow through the audited mutation seams.
3. **Owner alerting — a dead-man's switch.** *(Owner-corrected + downgraded
   2026-06-11: known, prepared, consciously deferred — a decision, not a
   blind spot.)* Facts corrected: the 2026-06-10 build failures caused **no
   user-facing downtime** (Railway keeps the active instance serving until a
   new build is live; the agent misread FAILED/REMOVED dashboard states as an
   outage) — the failure class was a *silent ship-blocker*, not downtime.
   The owner has alerting preparations made and has deliberately
   deprioritized it. Residual point kept for the record: nothing yet alerts
   on real downtime *or* on build-pipeline failure, and the Stage 1 caretaker
   will eventually want both as sensory inputs — pick it up when the owner
   says so, not before.

## AI-system / workflow gaps

4. **Session telemetry — quantify the self-improvement loop.** The reflection
   interview is qualitative; nothing *measures* sessions: PRs merged,
   CI-red rounds per PR (tonight: 2 on #685), repo-rule trips, time-to-green,
   prediction accuracy when offered. A structured footer in each session log
   + a caretaker weekly rollup would show whether the system is actually
   learning (rule-trip rate should trend down) — evidence for Q-0083's
   trust-tier promotions instead of vibes.
5. **AI spend metering — the instrument Q-0082 presupposes.** The owner owes a
   €/month ceiling "after first prod measurements," but the *meter* (per-call
   token/cost counters per exposure + per-guild daily rollup, surfaced via the
   existing diagnostics providers) isn't specified anywhere. The ceiling can't
   enforce, and the figure can't be chosen, without the instrument. Build the
   meter before the prod check, and the first measurement session produces the
   number for free.
6. **Toolchain rot watch — with a live, dated example.** Tonight's CI logs
   carry: "Node.js 20 actions are deprecated… actions/checkout@v4 …
   **forced to Node 24 starting June 16th, 2026**; removed September 16th."
   Same class as the Python-3.13.14 outage: an upstream clock ticking against
   unpinned/aging infrastructure, visible only in logs nobody reads. Concrete
   task: bump the actions versions (CI-config change — owner nod per the
   executable-config rule). Standing fix: a caretaker duty reviewing
   deprecation warnings + dependency freshness monthly.

## Routing

- §1 → **Q-0091** (router §38, open question — needs an owner pick before
  ecosystem #2 build).
- §2, §3, §4, §5 → captured here; groom into the roadmap queue as sessions
  free up (§5 naturally fuses with the Q-0086 joint prod-check session).
- §6 → small CI maintenance task awaiting owner nod; deadline-flavored
  (2026-06-16 for the forced Node switch).
