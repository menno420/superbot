# Social, Community, and Progression — roadmap draft

> **Status:** `plan` — planning/routing draft; not implementation approval.
> **Horizon:** Later. **Primary source:** `docs/ideas/owner-vision-ideas-2026-06-08.md` §4, §14, §22.
> **Owner decision Q-0038 — answered (2026-06-09, router):** **server-scoped clans** —
> `(guild_id, clan_id)` keys, one clan per player per server, no cross-server identity
> in v1; code/schema say "clan". Decides tenancy/identity only; implementation still
> needs the new-owner/ownership decision + normal promotion.

## Planning contract

- **Status:** roadmap draft; routing only, not approval and not an active implementation lane.
- Source code, merged PRs, binding contracts, subsystem folios, and `docs/current-state.md` outrank this draft.
- Preserve domain-service mutation ownership, direct-vs-draft lane rules, deterministic event flow, auditability, rollback safety, observability, cache invalidation, and testability.
- Before implementation, re-verify source, live PRs, the relevant folio, and every named gate.

## Context and objective

The owner selected social interaction as the highest-value way to make SuperBot feel alive. This draft groups guilds/clans, guild banks, guild battles, guild upgrades, achievements, profile cards, social leaderboards, and notifications around one progression seam rather than creating isolated social tables and commands.

## Scope

- A guild-scoped social identity and membership model; cross-server semantics settled by Q-0038 (2026-06-09): server-scoped, no cross-server identity in v1.
- Guild treasury controls, upgrades/levels, and competitive events.
- Persistent achievements/badges for game milestones, social actions, and hidden triggers.
- Read-only player profile cards focused on economy and guild membership/rank.
- All-time, weekly, and guild leaderboards plus a notification/inbox read surface with DM/channel delivery preferences and action links.

## Out of scope

Guild missions, seasonal achievement expiry, profile XP/W-L presentation, unconsented cross-server profiles, and implementation before Q-0038/privacy/retention decisions.

## Current state and seams to reuse

No canonical guild/clan or achievement owner exists today. Reuse `economy_service` for all coin effects, existing leaderboard/inventory/economy cogs for reads, guild lifecycle scoping, canonical audit/event paths, and existing Discord views/panels. Notifications must extend configured delivery/audit seams rather than become an unaudited message sender.

Likely roots to verify: `disbot/services/economy_service.py`, `disbot/cogs/leaderboard_cog.py`, `disbot/cogs/economy_cog.py`, `disbot/cogs/inventory_cog.py`, `disbot/guild_lifecycle.py`, `disbot/utils/db/`, and existing view/router foundations.

## Proposed phases

1. **Decision and read-model phase:** answer Q-0038; specify tenancy, identity, consent, retention/deletion/export, membership and officer authority; prototype read-only profile/leaderboard composition.
2. **Achievements foundation:** deterministic event vocabulary, idempotent award service, hidden-achievement disclosure rules, audit and backfill policy.
3. **Guild core:** membership/roles, treasury ledger through economy ownership, then levels/upgrades; no battles yet.
4. **Social competition:** guild leaderboards and manually scheduled guild battles using existing game/event owners.
5. **Notification composition:** inbox/read model first, then opt-in channel/DM delivery and CTA routing.

## Dependencies and gates

Q-0038; privacy/consent/retention decisions; canonical event vocabulary; economy ledger integrity; moderation/abuse controls; and a dedicated ownership decision before adding a new social domain. This work must not compete with the active server-management lane.

## Risks and mechanics

High risk: tenancy ambiguity, officer abuse, treasury races, notification spam, hidden-achievement leaks, and leaderboard privacy. Any schema must be additive with reversible rollout/backfill. Cache keys must include guild/social scope and invalidate on membership/award/ledger changes. Every treasury or award mutation needs idempotency, audit evidence, tests, and a safe-disable path.

## Migration, cache, audit, rollback, and test implications

Use additive schemas and explicit backfill/consent rules; scope and invalidate caches on membership, award, treasury, and preference changes. Audit officer/treasury/award/delivery actions without leaking hidden achievements. Rollback uses feature disable plus compensating domain-service transactions. Tests must cover tenancy, permission races, idempotent awards, treasury concurrency, privacy, and notification opt-out.

## Open questions and next session

- Q-0038 answered (2026-06-09): server-scoped clans — see the router entry for the full
  marked-up answer (membership/transfer/retention/moderation details).
- Decide whether inbox is bot-wide or feature-owned composition before schema design.
- **Recommended next model/session:** Opus product/architecture revision (Q-0038 is now
  answered); no Sonnet implementation slice until ownership is approved.
