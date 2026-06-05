# ADR-004: Interaction / panel fail-open posture is per-surface

**Status:** Accepted (2026-06-05)
**Supersedes:** none
**Superseded by:** none
**Ratified by:** the maintainer, in the 2026-06-05 planning session — they
explicitly selected "ratify the recommended posture now" when asked (RC-3 was
previously repo-gated as "maintainer-gated"; this ADR records that ratification).
If that provenance is ever in doubt, downgrade this ADR to *Proposed* and hold
the RC-3 implementation until re-confirmed.

## Context

Today every interaction path in `core/runtime/` is *uniformly fail-open*. When
governance/visibility resolution raises, the dispatcher logs, increments
`governance_fail_open_total{subsystem=…}`, and proceeds with `governance=None`
(`interaction_router.py` ~L144-154); when session resolution raises it proceeds
with `session=None` (~L156-167); and `persistent_views.interaction_check` returns
`True` (allow) when the panel anchor row is missing (~L62-67).

Fail-open is the right default for *read-only, public* surfaces — availability
over strictness, with the metric making any spike visible. It is the wrong
default for *owner-scoped / mutating* surfaces: a governance outage silently lets
a user drive a settings / setup / provisioning / admin panel that should have
been denied. RC-3 (audit consolidation) flagged this and deliberately carried it
as a **policy decision**, not a bug — the posture is a trade-off, not an accident.

The audit also rejected the over-correction: a **global** fail-closed rule
(Ideas Lab §6) would turn every transient governance hiccup into a total outage
for read-only surfaces too.

## Decision

**The fail-open vs fail-closed posture is chosen per surface, never globally.**

- **Fail-CLOSED** (deny on governance/anchor resolution failure) for owner-scoped
  or mutating surfaces: settings, setup, provisioning, admin, and any panel that
  performs a mutation or is owner-bound.
- **Fail-OPEN** (allow, emit the existing `governance_fail_open_total` metric)
  only for read-only, public surfaces.

**Refinement — what "owner/mutating" means here.** The fail-closed target is a
panel where a *missing anchor* could let a non-owner take a **privileged or
owner-affecting** action: settings / setup / provisioning / admin config, or a
guild-scoped mutation (e.g. role management). It is **not** every panel that
writes to the DB. The persistent game/economy panels (economy, mining, btd6,
help) are **stateless per-clicker** — every button acts on `interaction.user.id`,
so a non-owner clicking a stale-anchor panel only affects *their own* data, and
the "only you can interact" ownership check there is cosmetic. Those stay
fail-open (availability); their real gate is the per-button permission/data
scoping. Implementations therefore opt **in** the privileged set (e.g.
`RoleHubPanelView`) and leave stateless per-clicker panels fail-open.

The mechanism is a small, declarative marker — a per-`PersistentView` /
per-prefix `public` vs `owner`/`mutating` classification plus a prefix→posture
lookup — and **not** a new panel/router framework (Ideas Lab §6 forbids a second
one). The implementation (a later PR) MUST default the marker to *today's
behavior* (fail-open) and have surfaces opt **in** to fail-closed, so the change
is a revert-safe tightening rather than a blanket flip.

## Consequences

- Owner/mutating panels deny safely when governance is unavailable; a user can no
  longer drive a privileged panel through a governance outage.
- Read-only public panels keep degrading open; `governance_fail_open_total`
  remains the canary.
- Every new persistent view must declare its posture; the default (fail-open) is
  the safe-for-availability choice, so reviewers must consciously mark
  owner/mutating views fail-closed.
- Before the implementation merges, operators should confirm
  `governance_fail_open_total` is not chronically firing in production — if it
  is, fail-closed would convert silent degradation into visible denials, and the
  underlying governance fault must be fixed first.

## Re-evaluation criteria

Revisit if:
1. `governance_fail_open_total` shows governance resolution failing often enough
   that fail-closed causes real user-facing outages (fix the fault, or widen the
   fail-open set deliberately).
2. A surface emerges that is genuinely neither owner/mutating nor read-only
   public — that ambiguity is a signal to refine this taxonomy, not to guess
   (the implementing PR must STOP and surface it).
3. The per-surface marker starts accreting behavior (caching, routing) — that
   would mean it is becoming the forbidden "second framework"; stop and redesign.

## Implements

This ADR is the contract the RC-3 interaction/panel safety implementation PR
fulfils. See `docs/planning/superbot-audit-consolidation-2026-06-05.md` (RC-3)
and `docs/runtime_contracts.md` §3 (PersistentView) / §6 (interaction lifecycle).
