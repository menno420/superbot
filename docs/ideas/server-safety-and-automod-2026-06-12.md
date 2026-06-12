# Server safety, automod, logging, and image moderation (2026-06-12)

> **Status:** `ideas` — distilled from research uploaded by the owner
> (2026-06-12: competitor analysis + Discord/AI integration reference docs).
> Dedup-checked against `competitive-teardown-2026-06-10.md`, `gap-analysis-2026-06-11.md`,
> `fun-and-ease-brainstorm-2026-06-09.md`, and the roadmap. **Not a plan, not approval.**
> Route through `ideas/README.md` before touching any code.

## Context

Competitor bots (Carl-bot, Dyno, Arcane, YAGPDB, Koya, Double Counter) give server staff
four safety layers SuperBot currently lacks:
1. **Proactive automod** — automated message filtering before moderation is needed.
2. **Comprehensive event logging** — full audit trail of server activity visible to staff.
3. **AI-driven image moderation** — scanning uploaded images for NSFW/violent content.
4. **Account security** — detecting alt accounts, raids, and anonymizing proxies on join.

SuperBot's moderation service (warnings, timeouts, kicks, bans, escalation ladders) is
the *manual* layer; these four are the *automated* layer below it. All four should route
through the existing `moderation_service` for actions, emit audit events, and be
configurable per guild.

---

## 1. Automod rules engine

### What competitors do

Carl-bot and Dyno filter spam, scam/invite links, mass mentions, attachment floods, and
excessive emoji/caps, with per-rule actions (warn/timeout/kick) and escalation. YAGPDB
lets admins write rule triggers (starts-with, contains, exact, regex) with configurable
violator counts before an action fires. Koya's automod adds attachment and poll filters
plus scam-URL detection.

### SuperBot gap

SuperBot has no `on_message` filter layer. Staff must notice and react manually; the
moderation service only records after the fact.

### Proposed design

A `services/automod_service.py` that:

- Listens for `on_message` via the event bus.
- Evaluates a per-guild rule set stored in the DB (one row per rule: type, threshold,
  action, channels/roles excluded).
- Rule types (starting minimal): **spam** (N messages in T seconds) · **invite links**
  (discord.gg/ pattern) · **mass mentions** (≥N @mentions in one message) · **excessive
  caps** (>X% uppercase) · **blacklisted words** (configurable per guild).
- Actions: delete message → call `moderation_service.warn()` with escalation intact.
- Config UI: a dedicated automod panel in the moderation hub or setup wizard.

### Sizing and risk

Medium scope. The service itself is small; the config UI and the per-guild rule store
are the bulk. Risk: false positives (overblocking legit messages) — needs an
"exempt roles" and "exempt channels" safety valve from day one. Privacy: only message
text is evaluated server-side, no external calls.

### Current overlap

The competitive teardown (open-source lane #15) lists "Trigger→response expressions
(Nadeko/ReTrigger)" as a fit-4 candidate; that is the *response* half. This is the
*filtering* half — different enough to warrant a separate concept. Automod is also
mentioned in the uploaded competitor analysis as an "Important improvement."

### Route

→ **Q-0108** (discuss: which rule types to start with; actions policy) once the
maintainer has seen this file. Then: structured plan in `docs/planning/`.

---

## 2. Server logging service

### What competitors do

Carl-bot logs deleted messages, edited messages, role changes, bans, kicks, and invite
usage to a dedicated `#mod-log` channel. Arcane adds voice-channel joins/leaves and
member join/leave events. All allow configuring which event types go to which channel.

### SuperBot gap

SuperBot logs moderation *actions* (via `emit_audit_action`) to the audit system, but
there is no passive event log for:
- Message edits and deletions (staff can't review what was said).
- Member join/leave events (onboarding diagnostics, ban-evader detection).
- Role grants and revocations not made by the bot itself.
- Voice channel activity.

### Proposed design

A `services/server_logging_service.py` that:

- Subscribes to Discord events: `on_message_delete`, `on_message_edit`,
  `on_member_join`, `on_member_remove`, `on_member_update` (role changes),
  `on_voice_state_update`.
- Formats and posts to a configurable `#server-log` channel per event type.
- Per-guild config: enable/disable per event category, separate channel per category.
- Respects the existing audit service — does not duplicate moderation action logs.
- Config exposed in the setup wizard and a settings panel.

### Sizing and risk

Small-medium. Mostly event handlers + embed formatting. Risk: high volume in large
servers (paginate or rate-limit log posts). Sensitive: deleted-message logging can
feel invasive — document clearly in setup that staff can see deleted messages.

### Route

→ **Q-0109** (discuss: scope of events, channel-per-type vs. single channel, privacy
note in setup wizard). Then: plan.

---

## 3. Image moderation service

### What the research established

Three viable approaches, ordered by cost:

| Provider | Cost | Coverage | Bot limit |
|---|---|---|---|
| **OpenAI omni-moderation-latest** | Free | Sexual, harassment, violence, hate, self-harm | 20 MB per image |
| **API4AI NSFW Recognition** | Affordable paid tiers | SFW vs. NSFW + confidence score | REST API |
| **Hive Moderation** | Higher cost, no free tier | 50+ categories (nudity, violence, drugs, weapons, hate symbols) | REST API |

OpenAI's moderation endpoint accepts both text and images, returns category scores,
and is free. This makes it a natural first-pass filter before any other service.
Hive is enterprise-grade and the only one covering hate symbols + weapons — likely
overkill for most community servers.

### SuperBot gap

No image-scanning layer exists. Users can post any image; the bot has no automated
gate before it reaches the channel.

### Proposed design

A `services/image_moderation_service.py` that:

- Intercepts `on_message` if the message has image attachments.
- Downloads the image (up to the bot's 8 MiB per-attachment limit — see the
  `docs/operations/discord-platform-limits.md` reference).
- Sends to the chosen moderation provider asynchronously (OpenAI by default, since free).
- If a category score exceeds a configurable threshold: delete the message, issue a
  warn via `moderation_service`, emit an audit event, and optionally notify the user.
- Per-guild config: enable/disable, which provider, per-category thresholds.
- Requires: `message_content` intent (already enabled), manage-messages permission.

### Privacy and data

Images are sent to a third-party API. The setup wizard must inform server operators
that uploads may be analyzed externally; users must be informed via server rules
or a terms channel. Hive and API4AI both require a key; OpenAI keys are already used
in the AI cog.

### Sizing and risk

Medium. The async pipeline + configurable thresholds + UI are the main work.
Key risk: false positives (innocent image flagged). Mitigation: confidence threshold
≥0.80 before action; audit event lets staff review and dismiss.

### Route

→ **Q-0108** (combine with automod discussion: does the maintainer want image scanning?
Which tier — free OpenAI-only vs. paid NSFW specialist?). Then: plan.

---

## 4. Security service — alt detection, raid prevention, VPN blocking

### What Double Counter does

Double Counter fingerprints device, browser, network, and behaviour signals to flag
alternate accounts on join. It provides raid detection (pattern-recognition on mass
joins), invisible captcha challenges, VPN/proxy/Tor blocking via IP reputation
databases, and a real-time dashboard showing confidence scores and recommended actions
per flagged user.

### SuperBot gap

No account-join screening. Raid events, alt-account evaders, and VPN-masked bans are
handled only after manual discovery.

### Proposed design

A `services/security_service.py` with opt-in modules:

- **Raid detection** — monitor join rate; if >N joins in T seconds, trigger a lockdown
  (slowmode up, new-account joins paused) and alert staff. Fully self-contained, no
  external API required.
- **New-account filter** — reject or quarantine accounts younger than N days on join
  (configurable threshold). Simple, zero privacy cost.
- **Alt detection** — flag accounts that join with unusual shared patterns (IP range
  overlaps require an external service; shared device fingerprinting needs a captcha
  gateway). **High privacy impact** — requires explicit owner approval and user disclosure.
- **VPN/proxy blocking** — integrate a third-party IP reputation DB on join. Privacy
  cost: every join sends an IP query externally. Legitimate VPN users (privacy-conscious
  members) would be affected.

### Privacy and risk assessment

The simple tiers (raid detection, account-age filter) are low-risk and self-contained.
The advanced tiers (alt-detection, VPN blocking) have real privacy and legal implications:
GDPR applicability depends on where users are based; the owner is EU-based. These must
be explicitly opt-in for the server, disclosed in server rules, and gated on the
maintainer's explicit sign-off.

### Route

→ **Q-0111** (discuss: which security tiers are wanted; privacy/legal comfort level;
raid detection and account-age filter can be approved independently of the advanced tiers).

---

## Routing summary (updated 2026-06-12 — owner decisions via Q-0108/Q-0109/Q-0111)

| Idea | Size | Risk | Decision | Next destination |
|---|---|---|---|---|
| Automod rules engine (4 rule types) | Medium | Low (false positives) | **APPROVED** (Q-0108) | Plan `services/automod_service.py` |
| Server logging service (3 event categories + configurable channels) | Small–medium | Low (privacy note in setup) | **APPROVED** (Q-0109) | Plan `services/server_logging_service.py` |
| Image moderation — OpenAI-only | Medium | Low (free, existing key) | **APPROVED** (Q-0108) | Plan `services/image_moderation_service.py` |
| Image moderation — paid tier (API4AI / Hive) | — | — | **DECLINED** | Someday if needed |
| Security service — tiers 1+2 (raid detection, account-age filter) | Small | Low | **APPROVED** (Q-0111) | Plan `services/security_service.py` |
| Security service — tiers 3+4 (alt detection, VPN blocking) | — | High (GDPR) | **DECLINED** | Not pursuing |
