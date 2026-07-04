# Central admin guild + central logging guild — the bot's HQ (2026-07-02)

> **Status:** `ideas` — owner idea, captured from chat 2026-07-02 (*"a dedicated logging server and
> admin server for the bot, one server where it's possible to manage the settings of every server
> if necessary, one that could get logging from all servers as well, with the dedicated railway
> webhooks etc"*). Not approved for implementation — except the Railway-webhook piece, which was
> **executed same-session** (see §4).

## The idea

Two dedicated Discord guilds (or one guild with two category zones — owner's taste) forming the
bot's operations HQ:

1. **The admin guild** — a place where the platform owner manages **any** server's bot
   configuration without joining it: pick a guild → open its settings/diagnostics/setup panels
   scoped to *that* guild.
2. **The central logging guild** — receives logging from all servers plus the platform feeds
   (Railway deploy/volume alerts — now live, §4 — bot errors, health findings, guild joins/leaves).

## §1 Admin guild — mechanism

The authority half already exists: **Q-0212** gives the bot owner full bot-config authority in any
guild *they are in*; this idea removes the "they are in" clause by adding a **guild selector** on
an owner-only admin hub — cross-guild `PanelContext` (origin guild = HQ, **target guild** = the
one being configured). Every mutation still flows through the audited pipelines with the actor
recorded as platform-owner + the cross-guild context in the audit payload.

- **Rebuild tie-in (clean):** the design spec's `PanelContext` gains a `target_guild` distinct
  from origin; the manifest declares the admin hub with `capability_required` resolving to
  platform-owner only. Naturally a Phase-4 "platform ops" subsystem.
- **Current bot (retrofit):** heavier — panel contexts assume interaction-guild = config-guild
  throughout. A minimal v1: owner-only `!admin guilds` selector that opens the existing settings
  hub with an overridden guild context; needs a careful audit of every seam that reads
  `ctx.guild`. Worth its own plan before building.

## §2 Central logging guild — the privacy split (owner decision needed)

Two very different lanes hide in "logging from all servers":

- **Platform/ops lane — uncontroversial, do first:** bot health findings, error reports, guild
  join/leave, deploy + volume alerts (live, §4), routine/dispatch summaries. No member content;
  pure operator telemetry. Mechanism: the bot posts to HQ channels directly (it is in the HQ
  guild), driven by the existing EventBus/health seams.
- **Member-content lane — needs an explicit owner policy:** mirroring per-guild server logs
  (message edits/deletes, moderation) into HQ **moves member content out of its guild**. Options,
  in increasing exposure: aggregate/redacted summaries only → full mirror for owner-run guilds
  only → full mirror everywhere. Interacts with the redaction discipline, the design spec §10.3
  retention/deletion inventory, and the same "content leaves the guild" boundary that keeps image
  moderation opt-in. **Recommend deciding this per the §10.3 privacy contract before any mirror
  ships.**

## §3 Bootstrap options

The owner creates the guild(s) and invites the bots (recommended — ownership, naming, taste), or
an agent creates one via the test bot under Q-0213 (possible below the 10-guild limit; bot-owned
guilds have ownership-transfer quirks — workable but second choice). Either way agents wire the
channels/webhooks/rules; that operation is now scripted and proven (§4).

## §4 Executed same-session: the Railway alerts restore

The owner's original Railway webhook channel was accidentally deleted from the test server, but
the **Railway notification rule survived**, pointing at the dead Discord webhook (verified 404).
Restored under Q-0213, all read-back-verified, webhook token never printed: `#railway-alerts`
channel + "Railway Alerts" webhook created in MineSnakeBotTest via Galaxy Bot; the existing rule
(id `8d8fc9b4…`, all `Deployment.* / VolumeAlert.* / Monitor.*` events for `reliable-grace`)
updated in place to the new URL (hash-receipt match); a restoration notice posted through the
webhook proves the Discord half. **When the HQ guild exists, moving the feed = one new Discord
webhook + one `notificationRuleUpdate`** — a five-minute, known-good operation.

> **⚡ UPDATE (same day, later):** the HQ guild is **live** — the owner created **"Superbot Admin"**
> (`1522099141671653417`) and the feed moved there exactly as predicted: `#railway-alerts`
> (`1522212273240801510`) + webhook via Galaxy Bot, rule re-pointed in place, verified. The old
> test-guild channel is retired (owner may delete it). **Owner decisions landed with it:**
> production SuperBot stays OUT of HQ for now (avoid state pollution; Galaxy Bot is HQ's operator),
> and **the rebuilt bot inherits SuperBot's token at cutover** — the owner independently confirmed
> the design spec §5 flip model ("when the rebuilt bot matches and exceeds the current state of
> superbot we will use superbot's token"). The §1 admin-guild surfaces should therefore be designed
> for the rebuild's grammar first (HQ = the rebuild's operator console), with any current-bot
> retrofit strictly optional.

## Route

S1/S5 · supersedes the destination question in
[`railway-deploy-alerts-discord-webhook-2026-07-02.md`](./railway-deploy-alerts-discord-webhook-2026-07-02.md)
(the alert feed exists; HQ becomes its final home). The admin-guild half wants a small plan of its
own (the `ctx.guild` seam audit) before any build; the ops-logging lane is buildable freely; the
member-content mirror is **owner-gated on the §2 policy**.
