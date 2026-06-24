# Bot-migration assistant — buildable plan (detect → map → replicate → retire other bots)

> **Status:** `plan` — buildable spec (2026-06-24). Cross-check source before implementing;
> `docs/current-state.md` owns what is live. **Sector:** S1 — Bot product.
> **⚑ Self-initiated context:** owner asked in chat whether the bot can recognize other bots, map what
> they offer, replicate it, and retire them; chose **capture idea + write a plan** (not a build
> greenlight) and **catalog targets = top general bots + ticket/support bots first**. Greenlight or
> redirect before/at build.
>
> **▶ Build progress:** not started. PR 1 ships detect-and-report (read-only); PR 2 replicates; PR 3
> (owner-gated) retires.
>
> Idea capture: [`docs/ideas/bot-migration-assistant-2026-06-24.md`](../ideas/bot-migration-assistant-2026-06-24.md).
> Lineage: the *in-product engine* on top of the **V-14 feature-mining** lane
> ([`competitive-teardown`](../ideas/competitive-teardown-2026-06-10.md) ·
> [`competitive-positioning-north-star`](../ideas/competitive-positioning-north-star-2026-06-23.md) ·
> [`free-for-everyone-mission`](../ideas/free-for-everyone-mission-2026-06-21.md)).

## 1. Why

The maintainer's product goal is **easy configuration + all-inclusive functionality**. The single
highest-leverage expression of that is *consolidation*: a server runs MEE6 + Dyno + Ticket Tool + …, and
SuperBot offers to **replace all of them for free**. This feature makes that switch a guided one-flow
experience instead of a manual per-bot reconfiguration: SuperBot inventories the *other* bots, tells the
operator which SuperBot subsystems replace each, helps configure those, and then offers to remove the
now-redundant bots.

It is the literal user-facing payoff of [`free-for-everyone-mission`](../ideas/free-for-everyone-mission-2026-06-21.md)
("one free bot replaces 5+ paywalled ones") and the *live-in-server* counterpart to the **V-14**
teardown lane (which harvests rivals' features into our backlog by hand).

## 2. The one hard constraint (drives the whole design)

**Discord exposes no API for one bot to introspect another bot's commands.**
`GET /applications/{id}/commands` requires *that application's own bot token*; legacy prefix commands
have no introspection at all. So "find out what bot X offers" **cannot** be a live read — it must be
**inference** from:

1. **Identity** — each present bot's **application id** (stable) + display name. Detection itself is
   trivial: iterate `guild.members` for `m.bot and m.id != bot.user.id` (`member.bot` is already used in
   `security_cog`/`welcome_cog`; `intents.members` is on in `disbot/bot1.py`).
2. **A curated catalog** keyed by application id → known headline features → the SuperBot subsystem(s)
   that replace each. This is the long-lived asset; it grows independently of the engine.
3. **Observable signals** for the unknown tail — roles a bot holds/created, channels it manages,
   webhooks/integrations it owns.
4. **Honest fallback** — unknown bot → "we detected `X`, can't auto-map it; here's what SuperBot offers,
   pick what to enable." Never overclaim.

**Design rule:** the UI must never present inference as ground truth. Every mapping line is "this bot
*likely* does Y," and the replace step is operator-confirmed.

## 3. Data — the competitor catalog

A static, human-curated map. Recommend a single source of truth shared with the V-14 teardown docs
(**one source, two consumers** — the same discipline the repo applies to the subsystem registry). Format
options (decide at build): a checked-in `disbot/data/competitor_bots.py` constant, or a `*.yml` loaded at
startup. Shape per entry:

```python
# application id -> what it is + what replaces it
CompetitorBot(
    app_id=159985870458322944,          # MEE6
    name="MEE6",
    aka=["Mee6"],
    features=[                           # human-curated; each maps to >=1 SuperBot subsystem key
        Feature("leveling/XP",        replaces=["xp"]),
        Feature("automod",            replaces=["moderation"]),     # + automod sub-features
        Feature("welcome messages",   replaces=["server_management"]),
        Feature("reaction roles",     replaces=["server_management"]),
        Feature("custom commands",    replaces=["server_management"]),
    ],
)
```

`replaces` values are **validated against `utils/subsystem_registry.py` keys** at load (a test pins this
— a typo'd subsystem key fails CI), mirroring how setup recommendations re-validate against live schema.

### Initial catalog scope (owner pick: top general + tickets/support)

| Bot | App-id anchor | Headline features → SuperBot subsystem |
|---|---|---|
| **MEE6** | yes | leveling→`xp` · automod→`moderation` · welcome→`server_management` · reaction roles→`server_management` |
| **Dyno** | yes | automod→`moderation` · custom commands→`server_management` · autoroles→`server_management` · logging→`server_management` |
| **Carl-bot** | yes | reaction roles→`server_management` · automod→`moderation` · logging→`server_management` · starboard→`starboard` |
| **ProBot** | yes | welcome/leave→`server_management` · automod→`moderation` · leveling→`xp` |
| **Ticket Tool** | yes | support tickets→`ticket` |
| **Tickety / Helper.gg** | yes | support tickets→`ticket` |

(App ids are looked up + verified at build — never hard-coded from memory. The catalog ships with the
~6 above; adding the economy/engagement tier — Tatsu/UnbelievaBoat/Arcane — is a later catalog-only PR,
no engine change.)

## 4. Layering (mirror the existing setup-section + advisor + moderation seams)

- **`disbot/data/competitor_bots.py`** (or yml + loader) — the catalog (§3). Pure data; no logic.
- **`services/bot_migration_snapshot.py`** *(or extend `guild_snapshot.collect()`)* — a privacy-vetted
  read of the **other bots present** + their roles/channels/integrations. Stays operator-visible-metadata
  only (no message content), per the `guild_snapshot` contract. New narrow reads:
  `guild.webhooks()` / `guild.integrations()` (not enumerated today) — optional, Phase-2+.
- **`services/bot_migration_advisor.py`** — the mapper. Consumes (snapshot, catalog) → a list of
  `SetupRecommendation`s (reuse the existing `SetupAdvisor`/`setup_plan` types). Pure, deterministic,
  testable; no Discord I/O. For known bots it emits "enable/bind subsystem S" recommendations; for
  unknown bots it emits an advisory "manual pick" finding.
- **`views/setup/sections/bot_migration.py`** — a new `SetupSection` (slug `bot_migration`) registered in
  `services/setup_sections.py` at import, appearing as a wizard step. Renders the detected-bots report
  (PR 1), stages recommendations into the draft (PR 2), and surfaces the guarded retire step (PR 3).
- **Retirement** reuses `services/moderation_service.kick(member, *, reason, actor_id, channel)` — already
  audited, hierarchy-checked, permission-gated. No new removal primitive.

No architecture change: this is a feature-layer composition of existing seams. The replication writes go
through **Final Review → `setup_operations.apply_operations()`** (audited + atomic + reversible), exactly
like every other setup section.

## 5. Behaviour rules (the correctness caveats, explicit)

1. **Never read another bot's commands** — discovery is catalog + observable signals only (§2).
2. **Inference is labelled as inference** — "likely does Y," never "does Y." Unknown bots degrade to the
   operator-pick fallback, never a guess.
3. **Replication is staged, not applied directly** — recommendations flow through the draft → Final
   Review gate (eligibility/authority re-checked at apply, like all setup ops).
4. **Retirement is gated, confirmed, and last** — offered only after the operator confirms the
   replacement subsystem is configured; one explicit confirmation **per bot**; never automatic.
5. **Permission/hierarchy honesty** — if SuperBot lacks Kick-Members or loses the role-hierarchy check,
   *advise the operator to remove the bot manually* rather than failing silently (reuse the moderation
   service's existing hierarchy guard; surface its outcome).
6. **Some state can't migrate** — another bot's economy balances / XP history can't be carried over, only
   restarted fresh. The report says so plainly per feature.
7. **Exclude ourselves + system bots** — never list SuperBot; treat the server-owner-installed
   integration bots (e.g. the server's own webhook apps) distinctly from feature bots.

## 6. Arch & contracts checklist (binding)

- Catalog `replaces` keys validated against `subsystem_registry` (test-pinned).
- Snapshot extension stays within the `guild_snapshot` privacy contract (no message content/member PII
  beyond the bot roster).
- All replication writes via Final Review → `setup_operations` (audited; no `pool.execute` outside
  `utils/db/`).
- Removal via `moderation_service.kick` only — emits `audit.action_recorded` already.
- New section extends the section registry; view extends `BaseView`; re-checks operator authority at
  callback time (discord-views rule — opening ≠ authorizing). No cog import from views; no view import
  from services.
- Tests: catalog↔registry key validity; advisor mapping matrix (known bot → expected recommendations;
  unknown bot → advisory); snapshot excludes self + non-bots; retire step gated on confirmation +
  permission/hierarchy; draft round-trip through Final Review.

## 7. PR breakdown (≤3 PRs)

- **PR 1 — Detect & report (read-only, zero risk):** the catalog (§3, initial 6 bots) +
  `bot_migration_snapshot` (bot roster) + `bot_migration_advisor` (mapping) + the `bot_migration` setup
  section rendering "Detected bots → what SuperBot replaces," with the unknown-bot fallback. **Ships
  standalone value** (an operator sees their consolidation opportunity) and proves the catalog before any
  mutation exists.
- **PR 2 — Replicate:** turn matched features into staged `SetupOperation`s routed through Final Review
  (reuse the advisor → draft → apply path). Optional snapshot enrichment (webhooks/integrations) for
  better unknown-bot inference.
- **PR 3 (owner-gated) — Retire:** the guarded per-bot kick step (§5 rules 4–5), behind a "replacement
  configured" gate + explicit confirmation. Gated because kicking another bot is outward-facing and
  effectively irreversible (re-invite needed) — owner-confirm the UX/copy before it ships.

## 8. Verification (before each PR)

```bash
python3.10 scripts/check_architecture.py --mode strict
python3.10 scripts/check_quality.py --full
python3.10 scripts/check_docs.py --strict
```

## 9. Open questions for the owner

1. **Catalog home** — a checked-in Python constant, or a `*.yml` (+ loader) shared with the V-14
   teardown docs as one source of truth? (Plan recommends one shared source; format is a build detail.)
2. **Unknown-bot aggressiveness** — how hard to infer from roles/channels vs. always defer to the
   operator? (Plan defaults to conservative: known-bot mapping is confident, unknown is operator-pick.)
3. **Entry point** — only inside the `/setup` wizard, or also a standalone `!migrate` / `!replacebots`
   command? (Plan ships it as a setup section; a command alias is cheap to add.)
4. **Retire UX (PR 3)** — confirmation copy, batch-kick vs. one-at-a-time, and behaviour when SuperBot
   lacks permission/hierarchy (plan: advise manual removal). Owner-gated, so decided at PR 3.
5. **Catalog growth cadence** — who curates new entries, and do we want a contributor-facing format so
   the catalog can grow without an engine change?
