# Trigger-registry liveness sweep (2026-07-10)

> **Status:** `ideas` — session ender (Q-0089), round-3 dispatch session.
> **Subsystem:** none (agent network / fleet workflow).
> **Gate:** ready — one manager wake-step addition; no owner blocker.

## The idea

Make `list_triggers` a first-class fleet liveness source: a manager wake step that diffs
the account trigger registry against the manifest's routine expectations and flags
(a) **missing** routines (lane expected armed, no trigger), (b) **orphaned** triggers
(trigger exists, lane wound down — e.g. the old kit hourly firing after its lane declared
closed), and (c) **session-bound** triggers whose target chat is slated for archive (the
§6b silent-loop-kill class).

## Why it's worth having

Today's dispatch session found all three classes by hand in one day: websites' routine was
discovered only during an unrelated verification; the "kit routine externally stopped"
relay was refuted by the registry (`last_fired_at` is ground truth no status file
carries); and the kit/trading session-bound triggers were an archive hazard nobody's doc
flagged. The launch-readiness report (fleet-manager #30) hit the same gap live (its
DECISION F-1). The registry is the only *platform-truth* view of the fleet's clocks —
querying it once per manager wake turns three manual discoveries into a standing check.

## 2026-07-12 groom — two new failure classes, production-evidenced

The 2026-07-12 scheduler incident (`docs/eap/night-review-2026-07-12.md`) added two classes
the sweep must also flag, both invisible to status files and both live for hours that night:
(d) **WEDGED crons** — `enabled=true` with `next_run_at` frozen >15 min in the past (venture-lab
failsafe stuck at 06:06Z, kit-lab daily at 06:08Z, "last never"); (e) **dead pacemaker chains** —
a seat session with dropped one-shots and **no future tick armed** (9 ticks silently dropped
06:12–08:23Z). Constraint discovered the same morning: **cross-session trigger ops are
org-disabled** — a sibling can't `fire_trigger` a wedged seat awake; only the **manager** can act
(its MCP grant has `send_message`), so the sweep's remediation step is manager-`send_message`,
not a trigger kick. This moves the idea from "nice standing check" to the fleet's only
agent-side detection for a proven outage class — build-ready, priority up.

## Sketch

One wake-step in the manager's routine prompt + a `docs/` table (trigger id · name · cron
· binding [session/fresh] · lane · verdict). ~20 lines of procedure, no new tooling; the
generated-roster work (program review §6.2) can absorb it later.

## Dedup

Grepped `docs/ideas/` (`trigger`, `list_triggers`, `orphan`, `routine sweep`):
`reconcile-trigger-band-consistency-guard-2026-06-26.md` is about reconciliation cadence,
not the routine registry; nothing covers registry-vs-manifest liveness diffing.
