# Starboard / Hall of Fame — buildable plan

> **Status:** `plan` — buildable spec (2026-06-21). Cross-check source before implementing;
> `docs/current-state.md` owns what is live. **Sector:** S1 — Bot product.
> **⚑ Self-initiated** (Q-0172): promoted from idea B1 after the reaction-roles arc hardened the
> raw-reaction seam this reuses. Not yet owner-reviewed — greenlight or redirect before/at build.
>
> **▶ Build progress:** **PR 1 MERGED (#1259, 2026-06-21)** — migration 083 (`starboard_settings`
> + `starboard_entries`) + `utils/db/starboard` + audited `services.starboard_service`
> (`configure`/`disable` + `handle_star_change`) + `cogs/starboard_cog` (raw-reaction listener +
> `!starboard` config group) + `bot1` registration + `guild_lifecycle` teardown.
> **PR 2 shipped (2026-06-22, dispatch routine) — the config/correctness/UX subset of §6:**
> migration 084 (`self_star` column + `starboard_ignore_channels` table); **self-star exclusion** (the
> author's own ⭐ is discounted unless opted in — `handle_star_change(author_starred=…)` policy in the
> service, the reactor-membership fact in the cog); **ignore-channels** (per-guild list, listener gate +
> audited add/remove + `!starboard ignore/unignore`); a **`BaseView` config panel**
> (`views/starboard/config_panel.py`, opened by `!starboard panel` — channel/threshold/self-star/ignore
> all editable). **The optional XP bonus is deferred** (it couples the starboard to the economy and
> invites star-farming → wants owner input). Emoji stays ⭐-default with a configurable column (§8).

## 1. Why

`docs/ideas/fun-and-ease-brainstorm-2026-06-09.md` §B1 captured Starboard as **"Size S-M · Risk low ·
Route: quick-win / plan"** — the classic zero-typing community-memory feature SuperBot lacks, and the
[reaction-roles overhaul plan](reaction-roles-overhaul-plan-2026-06-21.md) §6 named it **"the
highest-value, lowest-risk next Carl-parity item"** precisely because it **reuses the now-hardened
raw-reaction seam** (the audited `reaction_role_service` listener pattern, PRs #1234–#1250). N
⭐-reactions on any message → the message is immortalized in a hall-of-fame channel with a jump link;
the embed live-updates its star count and is removed if it falls back below threshold.

## 2. Data model (migration `NNN_starboard.sql` — next free number; verify against `main` at build)

```sql
-- Per-guild config: where + how many stars. One row per guild.
CREATE TABLE IF NOT EXISTS starboard_settings (
    guild_id   BIGINT  PRIMARY KEY,
    channel_id BIGINT  NOT NULL,            -- the hall-of-fame channel
    threshold  INTEGER NOT NULL DEFAULT 3,  -- stars needed to enter
    emoji      TEXT    NOT NULL DEFAULT '⭐',-- the trigger emoji
    self_star  BOOLEAN NOT NULL DEFAULT FALSE, -- count the author's own star?
    enabled    BOOLEAN NOT NULL DEFAULT TRUE
);

-- One row per source message that has reached/entered the board. The mapping
-- source→starboard message is what makes recount edits + dedupe possible.
CREATE TABLE IF NOT EXISTS starboard_entries (
    guild_id           BIGINT  NOT NULL,
    source_message_id  BIGINT  NOT NULL,
    starboard_message_id BIGINT,            -- NULL until first posted
    star_count         INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (guild_id, source_message_id)
);
CREATE INDEX IF NOT EXISTS idx_starboard_entries_guild ON starboard_entries (guild_id);
```

Bootstrap DDL stays frozen (these ship only as a migration). Both tables are guild-keyed → register
teardown in `guild_lifecycle.py` (INV-I), mirroring `_teardown_role_menus`.

## 3. Layering (mirror the reaction-roles seam exactly)

- **`utils/db/starboard.py`** — typed CRUD only (`get_settings`, `set_settings`, `get_entry`,
  `upsert_entry`, `set_entry_message`, `delete_entry`, `delete_for_guild`). No logic. `pool.*` lives
  **only** here.
- **`services/starboard_service.py`** — the audited mutation seam. Config writes (`configure`,
  `disable`) emit `audit.action_recorded` (subsystem `starboard`), exactly like
  `reaction_role_service.set_message_mode`. The **count→post/edit/delete** decision
  (`handle_star_change`) lives here, returns a typed outcome; the cog does the Discord I/O. Member
  star events are **not** audited (high-volume, mirrors the reaction-role self-assign decision).
- **`cogs/starboard_cog.py`** — `on_raw_reaction_add` / `on_raw_reaction_remove` filtered to the
  guild's configured emoji (reuse the exact guard shape from `role_cog`: ignore bots, resolve member,
  delegate to the service), plus a small config surface (`!starboard #channel [threshold]`,
  `!starboard off`, or a `BaseView` panel — match the role-hub style). Register in the cog loader +
  `guild_lifecycle` teardown.

## 4. Behaviour rules (the "low risk" caveats from §B1, made explicit)

1. **Recount, don't increment.** On any ⭐ add/remove, re-read the live reaction count from the source
   message (`message.reactions`) rather than trusting a delta — robust against missed events /
   restarts (the same reason the role menus re-read authoritative state).
2. **Self-star** ignored unless `self_star=TRUE` (subtract the author's own reaction from the count).
3. **Threshold crossing:** count ≥ threshold and no entry yet → post the embed (author, content/jump
   link, attachment preview, ⭐ count), store `starboard_message_id`. Already posted → **edit** the
   count. Count drops below threshold → **delete** the starboard message + zero the entry (keep the
   row for re-entry, or delete it — decide at build; deleting is simpler).
4. **Dedupe:** the `(guild_id, source_message_id)` PK guarantees one starboard post per message; the
   stored `starboard_message_id` makes edit-in-place idempotent.
5. **Don't starboard the starboard:** ignore reactions whose channel **is** the configured starboard
   channel, and ignore the bot's own messages there.
6. **Bounds:** ignore if no settings row / disabled / emoji mismatch (fast-path return, like
   `reaction_roles_enabled`).

## 5. Arch & contracts checklist (binding)

- All writes through `starboard_service`; emit `audit.action_recorded` for config
  (`docs/runtime_contracts.md` §9). No `pool.execute` outside `utils/db/`.
- New guild-keyed tables → `guild_lifecycle.py` teardown (INV-I).
- Cog filters/guards mirror `role_cog` raw-reaction listeners (bot-ignore, member-resolve).
- `settings_keys` not needed (config is its own table), but the trigger emoji/threshold are read
  through the service, never hard-coded in the cog.
- Tests: service `handle_star_change` (post / edit / delete / self-star / below-threshold); DB
  round-trip; guild-teardown purge — mirror `tests/unit/services/test_reaction_role_service*.py`.

## 6. PR breakdown (2 PRs max)

- **PR 1 — foundation + working v1:** migration + `utils/db/starboard.py` + `starboard_service` +
  `starboard_cog` (listener + minimal `!starboard` config) + wiring + teardown + tests. Ships a
  working starboard.
- **PR 2 — polish (SHIPPED 2026-06-22, dispatch):** `self_star` exclusion + ignore-channels list + a
  `BaseView` config panel (`!starboard panel`). **Deferred follow-up (PR 3, owner-gated):** the optional
  XP bonus to the starred author — it couples the starboard to the game economy and invites star-farming,
  so the reward economics want an owner decision before it ships (per-guild custom-emoji *UI* can ride the
  same follow-up; the emoji *column* already exists).

## 7. Verification (before each PR)

```bash
python3.10 scripts/check_architecture.py --mode strict
python3.10 scripts/check_quality.py --full
python3.10 scripts/check_docs.py --strict
```

## 8. Open question for the owner

Trigger emoji fixed to ⭐ for v1, or configurable from the start? (Plan supports configurable via the
`emoji` column; v1 could hard-default ⭐ and expose config in PR 2.) Build can proceed with the
configurable column + a ⭐ default either way.
