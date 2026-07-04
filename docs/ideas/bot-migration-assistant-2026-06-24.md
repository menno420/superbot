# Bot-migration assistant — detect → map → replicate → retire other bots (2026-06-24)

> **Status:** `ideas` — captured from an owner chat request (the maintainer asked whether the bot can
> recognize *other* bots in a server, find out what they offer, suggest steps to replicate their
> functions with SuperBot, and delete the old bots once setup is complete). He chose **capture**
> over plan/build, then (same chat) chose **capture idea + write a plan** → promoted to a buildable
> plan: [`docs/planning/bot-migration-assistant-plan-2026-06-24.md`](../planning/bot-migration-assistant-plan-2026-06-24.md)
> (catalog seed = top general bots + ticket/support bots). Nothing is approved for *build* yet — the
> plan is plan-first.
> **Subsystem:** setup
> **Lineage:** the *in-product engine* on top of the **V-14 competitive feature-mining** lane —
> [`competitive-teardown-2026-06-10.md`](./competitive-teardown-2026-06-10.md),
> [`competitive-positioning-north-star-2026-06-23.md`](./competitive-positioning-north-star-2026-06-23.md),
> [`free-for-everyone-mission-2026-06-21.md`](./free-for-everyone-mission-2026-06-21.md). V-14 harvests
> rivals' features into *our backlog by hand*; this idea is the bot doing **detect → map → replicate →
> retire** *live in a server*, which is the user-facing payoff of "free **and** all-in-one."

## Shipped precedent — XP/level data carry-over (2026-07-01)

The first **data carry-over** slice of the "replicate" phase shipped independently, owner-requested:
a **level-migration importer** that scans another bot's level-up channel (Arcane is the live case —
it has *no* import API, confirmed) and copies the announced levels into SuperBot's chat XP, raise-only
and audited. See `docs/operations/xp-migration.md` and `services/xp_migration.import_levels`. This
partially answers the plan's open "scope of replication" caveat (§"Open questions"): it proves some
competitor state (leveling) **can** be carried over via channel scraping, not only re-started fresh —
and the `import_levels(guild, records, …)` seam is provider-agnostic, so a future *direct* provider
(e.g. MEE6's public leaderboard API) or the migration-advisor feeds the same audited import. When this
idea is promoted to build, the XP importer is the reusable pattern for the "carry over user data" step.

## The idea, in the owner's words

> "The goal of my bot is easy configuration and all-inclusive functionality, so one thing that would
> be a major improvement is if the bot can recognize other bots, find out which things they offer, and
> suggest steps to replicate their functions in the server, as well as to delete the old bots from the
> server once setup is complete."

This is a **bot-migration / consolidation assistant**: the operator runs one flow, SuperBot inventories
the server's *other* bots, tells them which SuperBot subsystems replace each, helps configure those, and
then offers to kick the now-redundant bots. It is the literal embodiment of the consolidation wedge in
[`free-for-everyone-mission`](./free-for-everyone-mission-2026-06-21.md): *one free bot replaces 5+
paywalled ones*.

## Four jobs — three easy, one hard

| # | Job | Verdict | Why |
|---|-----|---------|-----|
| 1 | **Recognize other bots** | ✅ Easy | `member.bot` is already used across the codebase (`security_cog`, `welcome_cog`); `intents.members` + `intents.message_content` are on (`disbot/bot1.py`). Iterating `guild.members` for `m.bot` (excluding ourselves) is trivial. Each carries a stable **application id** + name. |
| 2 | **Find out what they offer** | ⚠️ **Hard — the crux** | See below. There is **no Discord API** for one bot to read another bot's commands. |
| 3 | **Suggest steps to replicate** | ✅ Fits existing pipeline | The setup advisor → draft → Final Review machinery already turns "here is the server + a recommendation" into staged, audited, atomically-applied `SetupOperation`s. A migration plan is just another producer of those. |
| 4 | **Retire the old bots** | ✅ Reuses moderation | `services/moderation_service.kick()` already exists — audited, permission-gated, hierarchy-checked. Kicking a redundant bot is a guarded, confirmed call. |

## The hard part (Job 2) — and the realistic design

**Constraint (verified):** `GET /applications/{id}/commands` requires *that application's own bot token*.
A bot **cannot** enumerate another bot's slash commands via the API, and legacy prefix commands have no
introspection at all. So we cannot programmatically "read what bot X does."

**What we *can* observe and lean on instead:**

1. **Identity** — each present bot's **application id** (stable) + display name.
2. **A curated catalog** keyed by application id: the top ~20–30 popular bots (MEE6, Dyno, Carl-bot,
   Ticket Tool, UnbelievaBoat, Tatsu, ProBot, …) → their well-known headline feature set → **the
   SuperBot subsystem that replaces each** (the target side is `utils/subsystem_registry.py`). This
   curated catalog is the real heart of the feature; it needs human-verified content, not clever code,
   and it overlaps almost entirely with the work the **V-14 teardown** already does by hand — so the
   two lanes should share one data source.
3. **Observable signals** for the unknown/long tail — the **roles** a bot created or holds, the
   **channels** it manages, the **webhooks / integrations** it owns (`guild.webhooks()`,
   `guild.integrations()` — *not enumerated today; small new reads*). These hint at what a bot is doing
   even when it isn't in the catalog.
4. **Fallback for unknown bots** — "we detected `X`, can't auto-map it; here's what SuperBot offers,
   pick what to enable." Never guess.

The catalog grows over time; the engine doesn't change. This is the same "explicit data + heuristic
fallback" shape the repo already favors.

**Detect enhancement — announcer fingerprinting (from the XP-import lane, 2026-07-01).** The shipped
XP importer already has a per-bot announcer-format registry (`utils/xp_migration.FORMATS`) keyed by
regex. A cheap "detect" win reuses it: sample recent messages per channel, match each present bot's
**application id** + the format regexes, and surface *"MEE6's level-ups look present in #levels — import?"*
This auto-detects both **which bot** and **which channel** without the operator naming either — the
same fingerprinting the migration assistant needs for its broader detect phase, prototyped narrowly on
leveling first.

## How it docks into existing seams (no architecture change)

This is a **feature-layer extension**, confirmed by a read of the setup/moderation subsystems:

- **A new setup section** (e.g. `bot_migration`) registered in `services/setup_sections.py`, appearing
  as a wizard step alongside channels/roles/etc.
- **A migration advisor** modeled on `services/setup_ai_advisor.py` (same `SetupAdvisor` protocol):
  consumes a snapshot, emits `SetupRecommendation`s, which stage as `SetupOperation`s in the draft and
  apply through **Final Review** (so every replication step is audited + reversible).
- **Snapshot extension** — `services/guild_snapshot.py` (or a sibling `BotMigrationSnapshot`) gains a
  privacy-vetted "other bots present + their roles/channels/integrations" view. (The current snapshot
  deliberately excludes the member list; a bot-only enumeration is a narrow, justified addition.)
- **A `BotFeatureCatalogue`** — the curated app-id → competitor-features → SuperBot-subsystem map.
- **Guarded retirement** — a confirmation step per bot calling `moderation_service.kick()`, gated on
  "you've configured the replacement" + Kick-Members permission + role hierarchy.

## Suggested phasing (when promoted to a plan)

1. **Phase 1 — Detect & report** (read-only, zero risk): list the bots present, identify known ones from
   the catalog, show "MEE6 here likely does leveling + automod + welcome → SuperBot covers all three."
2. **Phase 2 — Replicate**: turn matched features into a staged draft routed through Final Review.
3. **Phase 3 — Retire**: after the operator confirms the replacement is live, offer a guarded
   per-bot kick.

The migration catalog is the long-lived asset and grows independently of the three phases.

## Open questions for a planning session

- **Catalog source of truth** — share one dataset with the V-14 teardown harvest, or keep a separate
  app-id-keyed runtime catalog? (Recommend: one shared source, two consumers.)
- **Unknown-bot UX** — how aggressively to infer from roles/channels vs. always defer to the operator.
- **Retirement safety** — confirmation copy, the "replacement actually configured" gate, what to do when
  SuperBot lacks the permission/hierarchy to kick (advise the operator instead).
- **Privacy** — the snapshot extension stays operator-visible-metadata only (no message content), per
  the existing `guild_snapshot` contract.
- **Scope of replication** — some competitor features (e.g. another bot's *economy balances*) cannot be
  migrated, only re-started fresh; the assistant should be honest about what it can and can't carry over.

## Risks / honest caveats

- The catalog is **manual curation** — its quality is the feature's quality. Stale entries mislead.
- **Capability discovery is inference, never ground truth** for Job 2; the UI must never overclaim "bot X
  does Y" with false confidence.
- **Kicking another bot is irreversible-ish** (re-invite needed) and outward-facing — must be explicitly
  operator-confirmed, never automatic.
