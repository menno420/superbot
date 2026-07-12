# Scheduler-independent trigger watchdog (GH Actions substrate) — 2026-07-12

> **Status:** `ideas` — session ender (Q-0089), overnight fleet review session.
> **Subsystem:** none (agent network / fleet workflow; lands in fleet-manager).
> **Gate:** ready — extends an existing, proven workflow (fm roster-regen); no owner blocker.

## The idea

Put the fleet's trigger-health watchdog on a substrate the watched scheduler can't take down:
extend fleet-manager's **roster-regen GitHub Actions cron** (fm #81 — already fetches the live
trigger registry into `telemetry/triggers-snapshot.json` every 2h) to *evaluate* that snapshot,
not just store it. Flag in the generated roster, and open/refresh a single `trigger-health`
issue when it finds: **WEDGED** crons (`enabled ∧ next_run_at < generated_at − 15min`),
**dropped one-shots** (`enabled ∧ run_once_at` in the past), and **dead chains** (a seat
session with no future tick — scoped to lanes the roster expects to be running, i.e.
FRESH/ACTIVE verdicts with a declared wake layer; parked/archived/no-wake seats are excluded so
expected-idle lanes don't re-flag the issue every run). ~30 lines of Python in `gen_roster.py`;
zero new infrastructure.

## Why it's worth having

The 2026-07-12 incident is the exact proof: the CCR trigger scheduler degraded for ~5.5h
(2 wedged crons, 9 dropped ticks — `docs/eap/night-review-2026-07-12.md`), and the *only*
oversight that kept running through it was the roster-regen — because it rides GitHub's cron,
not CCR's. An in-band watchdog (a manager wake step, the liveness-sweep idea) dies with the
scheduler it watches whenever the manager's own wake is what got dropped; this one cannot.
The two are complements: in-band sweep for fast reaction + remediation (`send_message`),
out-of-band Actions check for guaranteed detection.

## Sketch

`gen_roster.py`: after loading the snapshot, compute the three predicates against
`generated_at`; render a `⚠ WEDGED`/`⚠ CHAIN DEAD` marker in the roster's wake-state column;
if any fire, `gh issue create/comment` on a pinned `trigger-health` issue (the manager reads
issues at wake; the owner sees it in notifications). Threshold 15 min absorbs normal jitter
(observed fire jitter is seconds-to-single-minutes).

## Dedup

Grepped `docs/ideas/` (`trigger`, `watchdog`, `scheduler`, `liveness`, `cron`):
`trigger-registry-liveness-sweep-2026-07-10.md` is the in-band manager wake step (this file
cross-references it as complement); `external-cron-trigger-for-routines-2026-06-14.md`
proposed external *firing* for superbot's own routines, not fleet-wide *health detection*;
nothing covers out-of-band evaluation of the trigger snapshot.
