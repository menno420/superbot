# Native giveaway system — buildable plan (beat GiveawayBot)

> **Status:** `plan` — buildable spec (2026-06-23). Cross-check source before implementing;
> `docs/current-state.md` owns what is live. **Sector:** S1 — Bot product.
> **⚑ Self-initiated** (Q-0172): owner asked for the competitive teardown + a build path, then chose
> "Plan it" — not yet a greenlight to build. Greenlight or redirect before/at build.
>
> **▶ Build progress:** not started. PR 1 ships feature-parity-plus; PRs 2–3 add depth.

## 1. Why

The maintainer shared jagrosh's **GiveawayBot** (the de-facto standard giveaway bot) and asked:
*what can it do, what do we lack, how do we make a better one with more options and more fun?*

**We have no giveaway/raffle system at all** — it is a logged gap
(`docs/ideas/cog-improvement-audit-2026-06-08.md`: "No giveaway or raffle command… next most
requested," tagged a quick-win). The full competitive analysis is captured in
[`docs/ideas/giveaway-competitive-teardown-2026-06-23.md`](../ideas/giveaway-competitive-teardown-2026-06-23.md);
the short version is below.

### What GiveawayBot does (the bar to clear)

| Area | GiveawayBot |
|---|---|
| Start | `/gstart <time> <winners> <prize>` (`30s`/`2h`/`7d`) or `/gcreate` wizard |
| Entry | Click a **button** on the embed (older versions: 🎉 reaction) |
| End / pick | `/gend <id>` ends early; auto-ends on timer; equal-chance draw |
| Reroll | `/greroll <id>` or right-click → Reroll |
| Manage | `/glist`, `/gdelete <id>` (cancel, no winners) |
| Settings | `/gsettings set color/emoji`, `/gsettings show` |

**What GiveawayBot deliberately lacks** (our opening to be *better*): entry **requirements**
(role-gated, account/join age, min messages/XP), **bonus/weighted entries**, **bypass roles**,
**blacklists**, **multi-tier prizes**, **auto-paid prizes** (coins/items/roles), and **scheduled /
recurring** giveaways. It is intentionally a one-trick tool.

### What we already have that GiveawayBot doesn't (substrate to reuse)

- **Hardened raw-reaction / button-entry seam** — `reaction_role_service` (PRs #1234–#1250),
  `starboard_cog` (PR #1259). The audited listener pattern + button-view pattern are proven.
- **Economy** — `economy_service.credit()` (audited) → auto-pay coin prizes; inventory/role grants exist.
- **Automation scheduler** — `automation_scheduler.py` (interval / `scheduled_time` triggers, quiet
  hours, idempotency, auto-disable) → auto-end timers and recurring giveaways without a bespoke loop.
- **DB migration framework + guild_lifecycle teardown** (INV-I), `settings_keys`, audited mutation seam.

## 2. Data model (migration `095_giveaways.sql` — verify next free number against `main` at build; 094 is current)

```sql
-- One row per giveaway. Survives restarts; the scheduler/cog re-reads authoritative state.
CREATE TABLE IF NOT EXISTS giveaways (
    id              BIGSERIAL PRIMARY KEY,
    guild_id        BIGINT  NOT NULL,
    channel_id      BIGINT  NOT NULL,
    message_id      BIGINT,                         -- NULL until the embed is posted
    host_id         BIGINT  NOT NULL,               -- who started it
    prize           TEXT    NOT NULL,
    winner_count    INTEGER NOT NULL DEFAULT 1,
    ends_at         TIMESTAMPTZ NOT NULL,
    status          TEXT    NOT NULL DEFAULT 'running'  -- running | ended | cancelled
                    CHECK (status IN ('running','ended','cancelled')),
    -- requirements (all nullable = "no requirement"), our edge over GiveawayBot
    required_role_id   BIGINT,
    blacklist_role_id  BIGINT,
    min_account_age_days INTEGER,
    min_join_age_days    INTEGER,
    -- prize payout (nullable = manual/IRL prize, parity with GiveawayBot)
    prize_coins     INTEGER,                        -- auto-credited via economy_service
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_giveaways_due ON giveaways (status, ends_at);
CREATE INDEX IF NOT EXISTS idx_giveaways_guild ON giveaways (guild_id);

-- One row per entrant. weight>1 = bonus entries (booster/level perks) — GiveawayBot can't do this.
CREATE TABLE IF NOT EXISTS giveaway_entries (
    giveaway_id BIGINT  NOT NULL REFERENCES giveaways(id) ON DELETE CASCADE,
    user_id     BIGINT  NOT NULL,
    weight      INTEGER NOT NULL DEFAULT 1,
    entered_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (giveaway_id, user_id)
);

-- Recorded winners (draw + reroll history → auditable, re-rollable).
CREATE TABLE IF NOT EXISTS giveaway_winners (
    giveaway_id BIGINT  NOT NULL REFERENCES giveaways(id) ON DELETE CASCADE,
    user_id     BIGINT  NOT NULL,
    drawn_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    is_reroll   BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (giveaway_id, user_id)
);
```

Bootstrap DDL stays frozen (ships only as a migration). All three tables are guild-keyed (directly or
via FK) → register teardown in `guild_lifecycle.py` (INV-I), mirroring `_teardown_role_menus` /
starboard. Per-guild defaults (embed color, button emoji — the `/gsettings` parity surface) live in a
small `giveaway_settings(guild_id PK, color, emoji, enabled)` table **or** reuse existing
`settings_keys` — decide at build; a dedicated table mirrors starboard and is simpler to teardown.

## 3. Layering (mirror the starboard / reaction-roles seam exactly)

- **`utils/db/giveaways.py`** — typed CRUD only (`create`, `get`, `list_active`, `list_due`,
  `set_message`, `set_status`, `add_entry`, `remove_entry`, `list_entries`, `record_winners`,
  `delete_for_guild`). No logic. `pool.*` lives **only** here.
- **`services/giveaway_service.py`** — the audited mutation seam. `create` / `end` / `cancel` /
  `reroll` emit `audit.action_recorded` (subsystem `giveaway`), exactly like
  `starboard_service.configure`. Holds the **eligibility check** (role/age/blacklist), the
  **weighted draw** (`random` over an entry list expanded by `weight`, distinct winners), and the
  **prize payout** call to `economy_service.credit()` when `prize_coins` is set. Returns typed
  outcomes; the cog does Discord I/O. High-volume *entry* events are **not** audited (mirrors the
  reaction-role self-assign decision).
- **`cogs/giveaway_cog.py`** — command surface + the entry button listener. Commands (prefix +
  slash, match the repo's existing dual-surface cogs):
  - `!giveaway start <duration> <winners> <prize>` (+ optional `--role @r --coins N --minage Nd`)
  - `!giveaway end <id>` · `!giveaway reroll <id>` · `!giveaway cancel <id>` · `!giveaway list`
  - a `GiveawayEntryView(BaseView)` with one "🎉 Enter" button → `giveaway_service.add_entry`
    (re-check eligibility **at click time**, per the discord-views rule — opening ≠ authorizing).
  - Register in the cog loader + `guild_lifecycle` teardown.
- **Auto-end:** a `scheduled_time`/interval automation handler (or a light `tasks.loop`) polls
  `list_due()` and calls `giveaway_service.end()`. **Prefer the existing automation scheduler** over a
  new loop — add an action kind `end_due_giveaways` to `automation_registry` (+ migration 032 CHECK,
  per its lock-step test) rather than hand-rolling a timer.

## 4. Behaviour rules (the correctness caveats, made explicit)

1. **Re-read authoritative state on draw.** End/reroll reads entries from the DB, not from a cached
   count — robust against restarts and missed button clicks (same reason starboard recounts).
2. **Eligibility at entry time AND at draw time.** Check role/age/blacklist when the button is
   clicked (reject with an ephemeral reason) *and* filter again at draw (a user may have lost the
   role since). Bypass: a configured bypass/booster role skips requirements.
3. **Weighted draw, distinct winners.** Expand entries by `weight`, sample `winner_count` *distinct*
   users; if entrants < winners, everyone wins (GiveawayBot behaviour).
4. **Reroll** excludes already-recorded winners by default; records the new pick with `is_reroll=TRUE`.
5. **Prize payout is best-effort + audited.** If `prize_coins` set, `economy_service.credit()` each
   winner inside the end transaction; log + surface any failure, never silently drop.
6. **Idempotent auto-end.** `status` flips `running → ended` under the same guard the scheduler uses;
   a double-fire is a no-op (the #843 idempotency discipline).
7. **Bounds / fast-path:** disabled guild, no entrants, already-ended → early typed return.

## 5. Arch & contracts checklist (binding)

- All writes through `giveaway_service`; emit `audit.action_recorded` for host actions
  (`docs/runtime_contracts.md` §9). No `pool.execute` outside `utils/db/`.
- Prize payout goes through `economy_service.credit()` — **never** a direct economy DB write.
- New guild-keyed tables → `guild_lifecycle.py` teardown (INV-I).
- View extends `BaseView`; re-checks eligibility at callback time (discord-views rule). No cog import
  from views; no view import from services.
- Entry button listener guards mirror `role_cog` (bot-ignore, member-resolve).
- Tests: service eligibility matrix (role/age/blacklist/bypass); weighted-draw distribution +
  distinct-winner + everyone-wins edge; reroll-excludes-winners; payout-on-end; DB round-trip;
  guild-teardown purge; auto-end idempotency — mirror `tests/unit/services/test_starboard_service*.py`
  and `test_reaction_role_service*.py`.

## 6. PR breakdown (2–3 PRs max)

- **PR 1 — foundation + parity-plus v1:** migration 095 + `utils/db/giveaways.py` +
  `giveaway_service` (create/end/reroll/cancel, eligibility, weighted draw, coin payout) +
  `giveaway_cog` (`!giveaway` group + `GiveawayEntryView` button) + auto-end via the automation
  scheduler + wiring + teardown + tests. **Ships a working giveaway that already beats GiveawayBot**
  (button entry + requirements + weighted entries + auto-paid coin prizes).
- **PR 2 — depth & polish:** `/gsettings`-parity (per-guild color/emoji) + a `BaseView` management
  panel (create/list/end from a hub button — wire into the Community hub `🎁` slot; the "Giveaways"
  notification role already exists in `role_packs.py`) + multi-tier prizes + bypass-role config +
  live entry-count embed updates.
- **PR 3 (owner-gated) — recurring/scheduled giveaways** via the scheduler (daily/weekly auto-draw)
  and **entry-task** giveaways ("be in voice", "reach level N this week"). Gated because recurring
  auto-payouts touch the economy faucet (star-/giveaway-farming economics → owner decision, same
  caution as the starboard XP bonus).

## 7. Verification (before each PR)

```bash
python3.10 scripts/check_architecture.py --mode strict
python3.10 scripts/check_quality.py --full
python3.10 scripts/check_docs.py --strict
```

## 8. Open questions for the owner

1. **Prize default:** auto-paid **coins** (economy-integrated, our edge) the headline, with manual/IRL
   prizes as a text-only fallback — or keep v1 text-only like GiveawayBot and add payout in PR 2?
   (Plan assumes coins in PR 1; it's the differentiator and the seam is one `credit()` call.)
2. **Bonus-entry source:** which perks grant extra weight — server boosters, XP level, a configured
   role? (Plan supports a `weight` column; the *policy* that sets it is the open part.)
3. **Auto-end mechanism:** reuse the automation scheduler (recommended — no new loop, idempotent) or a
   dedicated `tasks.loop`? (Plan recommends the scheduler.)
4. **Command surface:** mirror GiveawayBot's `/g*` names for muscle-memory, or our `!giveaway <sub>`
   group style? (Plan uses the group style; aliases are cheap to add.)
