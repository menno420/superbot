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

None of these are foundational/architectural — they're feature-level additions that fit the
existing moderation/security subsystem ownership and don't need a K0-K10 kernel decision the way the
channel-role-authority gap does (see
[`channel-role-scoped-authority-gap-2026-07-07.md`](./channel-role-scoped-authority-gap-2026-07-07.md)).
Reasonable to route as: (1) the join-verification gate as a small addition to `security_cog.py`'s
existing join-defense family; (2) ban-appeal as a specialized ticket category rather than a new
subsystem; (3) trigger→response as a standalone small feature whenever there's appetite, lowest
priority of the three. None block the rebuild; whoever ports the moderation/security subsystem in
Sequence C's port bands should decide whether these three port forward as new manifest-declared
features or stay backlog.
