# Idea — server-owner-configurable moderation/warning DMs

> **Status:** `ideas` — capture only, not approved. Routing: **safety / community lane**.
> Captured 2026-06-16 from the owner's **Q-0147** decision (the standing DM policy).
> **Subsystem:** moderation — moderation-DM config (shipped #1023).

## The owner's standing DM policy (the decision this came from)

Deciding the `/myprofile` onboarding gate (Q-0147), the owner set a **standing rule** for *all*
bot DMs:

- **Profile / onboarding / informational DMs are opt-in and never fire on join.** Discoverability
  is in-guild (a welcome-surface line), never an unsolicited DM (public-bot abuse posture, Q-0080).
- **The only DMs that may be sent without the recipient opting in are moderation/warning DMs** —
  and only when **the server owner has enabled them** and has a **clear way to configure which
  moderation actions trigger a DM** (warn → DM yes; auto-delete → DM no; the owner's call per guild).

The opt-in / in-guild half is satisfied by myprofile PR C (plan §4.3). **This idea captures the
second half** — the configurable moderation-DM feature — so it isn't lost.

## The idea — a moderation-DM config the server owner controls

Let a server owner opt their guild into **DMing a member when a moderation action is taken against
them** (e.g. "you were warned in *<server>* for *<reason>*"), with **per-action** granularity:

- A master `moderation_dm_enabled` setting (**off by default** — no DMs unless the owner turns it on).
- A per-action map: which `moderation_service` actions (warn · timeout · kick · auto-delete · …)
  send a DM. Configured via `!settings` → Moderation, mirroring the existing enable/disable/threshold
  surface.
- The DM is **best-effort, fail-open** — a closed-DM user simply doesn't get it, never blocking the
  moderation action — and content is a neutral notice (action · server · reason · appeal pointer if
  configured).

## Why it's worth having (and the guardrails)

- It is the *useful* unsolicited DM (a member learns why they were actioned) without the spammy one
  (mass onboarding DMs). It stays inside the owner's policy because it is **off by default,
  server-owner-enabled, and per-action configurable.**
- Seam: it rides the existing `moderation_service` action authority + `audit_events` — the DM is a
  *notification side-effect* of an already-audited action, not a new mutation path. No DM logic in
  cogs/views; a small `moderation_dm` notifier keyed off the moderation action events.
- Privacy/abuse: only members already in the guild, only on an action against *them*, only when the
  owner enabled it. Rate-limit-aware (Discord DM caps). Disclose in the setting hint.

## Disposition

Safety/community lane. Promote to a `docs/planning/` plan when that lane has capacity — the
moderation cog + settings surface already exist, so it is a contained feature, not a new subsystem.
Anchor: the Q-0147 standing DM policy (router).
