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

## Sketch

One wake-step in the manager's routine prompt + a `docs/` table (trigger id · name · cron
· binding [session/fresh] · lane · verdict). ~20 lines of procedure, no new tooling; the
generated-roster work (program review §6.2) can absorb it later.

## Dedup

Grepped `docs/ideas/` (`trigger`, `list_triggers`, `orphan`, `routine sweep`):
`reconcile-trigger-band-consistency-guard-2026-06-26.md` is about reconciliation cadence,
not the routine registry; nothing covers registry-vs-manifest liveness diffing.
