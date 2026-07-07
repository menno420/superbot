# Moderation feature gaps versus competitor bots (researched, most turned out already covered)

> **Status:** `ideas` — capture only, not approved for implementation. Owner-raised 2026-07-07
> ("I believe we still don't have all the commands and features some other bots have related to
> [moderation]"), researched against the live bot and `docs/ideas/competitive-teardown-2026-06-10.md`.
> **Subsystem:** moderation, security

## The honest finding: less of a gap than expected

The live bot already has ban/kick/timeout/warn with an escalation ladder, unban/clearwarnings/
modlogs (`disbot/cogs/moderation_cog.py`, `disbot/services/moderation_service.py`), automod
(spam/invite-links/caps/mass-mentions, `disbot/cogs/automod_cog.py`), a prohibited-word filter
(`disbot/services/prohibited_words_service.py`), AI image moderation
(`disbot/cogs/image_moderation_cog.py`), raid detection + lockdown + account-age join filtering
(`disbot/cogs/security_cog.py`, `disbot/services/security_service.py`), full audit/event logging
(`disbot/cogs/logging_cog.py`), reaction roles, bulk-delete/cleanup, and a staff support-ticket
system (`disbot/cogs/ticket_cog.py`). All of this is architecturally owned per `docs/architecture.md`.
An earlier gap-tracking doc (`docs/ideas/server-safety-and-automod-2026-06-12.md`) that once listed
several of these as missing is now stale — they've since shipped.

**Three things are genuinely absent** — not live, and not captured as an idea anywhere before this
document:

## 1. Verification/CAPTCHA-style join gate

Today's only join-time defense is an account-age filter (kick/alert if the account is too new) in
`security_service.py`. There is no "click to verify" / human-acknowledgment gate that holds a new
member out of normal channels until they actively confirm they're not a bot/raid account — a
standard feature on Carl-bot/Dyno-class bots for servers that take raid risk seriously. Distinct
from the existing raid *detection* (which reacts to a burst of joins), this is a *per-member* gate
applied to every join regardless of burst detection.

## 2. Dedicated ban-appeal / mod-report modmail flow

The existing `ticket_cog.py` is a general staff-support flow (open/claim/close/transcript) — it is
not specifically a ban-appeal intake or a moderator-facing DM-relay "report a problem to the mod
team" tool. The only prior mention anywhere in the repo is two one-line rows in the competitive
teardown table (`competitive-teardown-2026-06-10.md:69-70`, "Modmail/ticket panels" and "Ban appeals
flow," both scored 3/5, both marked `ideas`, neither designed). Worth deciding whether this should
be a genuinely separate flow or a specialized ticket *category* on the existing ticket system —
the latter is probably the smaller build, given the audited ticket machinery already exists.

## 3. Custom trigger→response commands

Keyword-triggered custom auto-replies (Nadeko/ReTrigger-style — an admin configures "when someone
says X, reply with Y") appear nowhere as a moderation/admin-config feature. It's listed once, in
passing, in the same competitive-teardown table (row 15) but framed as a general admin-config
feature alongside game/economy items, not discussed in any moderation-focused doc. Lower priority
than the two above — closer to a "fun/utility" feature than a moderation gap — but worth naming
since it's a common request in servers that don't want a full automod rule for a one-off phrase.

## Recommended routing

**ROUTED — thin decide-at-port anchors folded as canonical-plan
[`§11b A-14`](../planning/rebuild-canonical-plan-2026-07-06.md) (2026-07-07, same day,
idea-consolidation session).** The verification confirmed all three absences but corrected this
doc in two places (full evidence:
[`rebuild-idea-consolidation-report-2026-07-07.md`](../planning/rebuild-idea-consolidation-report-2026-07-07.md) §2.3):

- **Item 2 is partially subsumed by an owner decision two days older than this doc:** Stage-2 walk
  row 6 (2026-07-05) already commits a **case/appeal system** as required Phase-B scope. A-14
  anchors the remaining open surface question — banned-user (non-member) **DM intake**, genuinely
  new for this bot since the ticket system is guild-only — to that committed design.
- **Item 1** is anchored to walk row 9's already-committed quarantine build (same join-defense
  family, same audited role seam), as the **first consumer of the A-12 role-scoped authority lane**
  (deny-until-role). Constraint carried: **button-verify, zero-PII, no external calls** — the
  Q-0111 declined tiers 3/4 (fingerprinting / third-party CAPTCHA / IP reputation) stay declined;
  don't re-litigate them via "CAPTCHA" phrasing.
- **Item 3 stays backlog** — and this doc's "not captured as an idea anywhere before" claim was
  **wrong**: a full prior design capture exists at
  [`community-platform-features-2026-06-12.md`](./community-platform-features-2026-06-12.md) §4
  ("Custom commands (TagScript-safe)", routed Roadmap Someday), with a live UX-lab mockup
  (`disbot/views/ux_lab/mockups.py:399-421`) and the grammar family G-11 already minted pending.
  Nothing can evaporate; it is L2-community-shaped, not band-2 moderation work.
