# ADR-001: In-process state, not Redis (Phase Sc skip)

**Status:** Accepted (2025-Q2)
**Supersedes:** none
**Superseded by:** none

## Context

`docs/architecture.md` "Single-process assumption" lists six
in-process registries (EventBus._handlers, governance.cache._CACHE,
governance.execution._OVERRIDES, persistent_views._REGISTRY,
interaction_router._handlers, live_update_scheduler._last_edit) and
identifies four of them as candidates for a future Redis backend
under the label "Phase Sc".

SuperBot currently runs as **one shard, one process**, handling
≤100 guilds.  The work to swap each registry to Redis would be
weeks of refactoring, would introduce an operational dependency
(Redis), and would create a new failure mode (Redis partition) for
no measurable performance win at current scale.

The forensic audit (P0–P3 plan) explicitly recommended skipping
Phase Sc.  Without an ADR, the question gets re-asked every time a
new contributor reads the "future work" note in architecture.md.

## Decision

**Keep all in-process registries in-process.**  Do not invest in
Redis-backed alternatives until the criteria below are met.

The Phase Sc planning note in `docs/architecture.md` stays as a
forward reference, but it is intentionally indefinite — Phase Sc
work does not begin until the project crosses one of the explicit
triggers below.

## Consequences

- Cross-shard event routing is **not supported**.  If we ever shard
  the bot, the architecture has to change.
- Restart drops EventBus subscriptions, governance cache, scheduler
  rate-limit dict, navigation_stack locks.  These are documented as
  restored lazily; the contract is unchanged.
- Operational footprint stays minimal: one process, one Postgres,
  no Redis.
- New features that want shared state across processes must either
  use Postgres (the existing pattern) or propose a new ADR.

## Re-evaluation criteria

Re-open this decision if any of the following hold:

1. **Sharded deployment.** The bot is split across more than one
   `discord.Client` instance (whether by guild count or by region).
2. **Sustained guild count > 250.** Operational telemetry shows
   meaningful pressure on a single-process registry (lookup
   latency, cache miss rate, OOM under cache size growth).
3. **Cross-process state requirement.** Any new feature
   intrinsically needs state visible to a sibling process — for
   example, an out-of-band admin worker that mutates governance
   without going through `discord.py`.

Hitting any one trigger means **revisit**, not automatic adoption.
A new ADR documents the actual decision at that point.

## Notes for implementers

Until this ADR is superseded:

- Do not add Redis configuration knobs.
- Do not split a single-process registry "in case we want to move
  it later" — `MappingProxyType` and module-level dicts are fine.
- New events go in `core/events_catalogue.KNOWN_EVENTS`; the bus's
  drift detection (INV-A) is the only contract that matters.
