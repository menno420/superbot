# Plan — Karma (thanks/upvote reputation) subsystem

> **Status:** `plan` — buildable spec, owner-directed (2026-06-22). Answers the maintainer's one-word
> prompt "Karma" + the AskUserQuestion clarification (**plan-first**, flavor **thanks/upvote
> reputation**). **No code shipped this session** — this is the design; implementation awaits the
> owner's answers to the 5 open questions in §7. Verify against source before building (the economy/XP
> code-pointers below are current as of `7ec747e`). Idea capture:
> [`../ideas/karma-reputation-system-2026-06-22.md`](../ideas/karma-reputation-system-2026-06-22.md).

## 1. The ask

> "Karma" — owner, 2026-06-22. Clarified: a **thanks/upvote reputation** system where members grant
> each other karma; tracked per-user with a leaderboard. Plan it first, then await go-ahead.

Karma is a **peer** signal distinct from the two existing per-user scores:

| Score | Source | What it measures | Owner service |
|---|---|---|---|
| XP | the bot (chatting) | activity | `services/xp_service.py` |
| Coins | the bot (daily/work/games) | economy balance | `services/economy_service.py` |
| **Karma** | **other members** | **how much the community values you** | **`services/karma_service.py`** (new) |

Design filter — **Q-0190 free-for-everyone:** karma is pure social reputation, non-spendable, no
paywall, no P2W.

## 2. Architecture — mirror economy/XP exactly

The economy/XP subsystems already encode the audited-mutation pattern this needs. Karma reuses it
1:1 (the layering keeps `scripts/check_architecture.py` green):

```
cog (cogs/karma_cog.py)  ──calls──▶  service (services/karma_service.py)  ──┬─▶ db (utils/db/karma.py)
   !thanks / !karma / /karma           give() / get_user_record()          ├─▶ insert_karma_audit()  (append-only)
   reaction listener (phase 3)         validates → writes → audits → emits └─▶ bus.emit("karma.granted")
                                                                                       │
leaderboard provider (services/rank_providers.py KarmaProvider) ◀── reads `karma` ─────┘
audit/log subscriber (services/server_logging) ◀── on("karma.granted") ── (existing generic pattern)
```

**Invariant (mirrors INV-F/INV-G):** every karma write goes through `karma_service.py`. No
`db.credit_karma` outside the service — enforced by a new AST invariant test (§5, PR 1).

## 3. Data model

Two tables, added via a **migration** (`disbot/migrations/NNN_karma.sql` — `create_tables()` is frozen;
new tables go only in migrations). Shapes copied from `economy` + `economy_audit_log`.

**`karma`** — per-user running totals (PK `user_id, guild_id`):

| Column | Type | Notes |
|---|---|---|
| `user_id` | bigint | |
| `guild_id` | bigint | |
| `karma_points` | int | running total, clamped `>= 0` |
| `received_count` | int | lifetime grants received |
| `given_count` | int | lifetime grants given (for the daily-cap UX + abuse review) |
| `last_received` | timestamptz | last time they got karma |

**`karma_audit_log`** — append-only, the anti-abuse + history source of truth (mirrors
`economy_audit_log`, migration 014):

| Column | Type | Notes |
|---|---|---|
| `id` | bigint identity PK | |
| `occurred_at` | timestamptz default now() | |
| `guild_id` | bigint | |
| `from_user` | bigint | granter |
| `to_user` | bigint | recipient |
| `delta` | int | `+1` per grant (signed leaves room for a future downvote) |
| `source` | text | `"command"` / `"reaction"` |
| `reason` | text null | optional free-text |

Indexes: `(guild_id, to_user, occurred_at DESC)` (recipient history + leaderboard tie-break),
`(guild_id, from_user, occurred_at DESC)` (cooldown + daily-cap queries).

> **Anti-abuse uses the audit log, not extra state.** "Has *from* thanked *to* in the last window?"
> and "how many grants has *from* made today?" are both index-covered queries over `karma_audit_log` —
> exactly how `economy_flow_service` reads `economy_audit_log`. No separate cooldown table.

## 4. The layers (concrete files + signatures)

### 4a. DB layer — `disbot/utils/db/karma.py` (new)
Low-level only; called **exclusively** by the service. Mirror `utils/db/economy.py`:

```python
async def get_karma(user_id, guild_id) -> dict                       # SELECT row or zero-dict
async def credit_karma(user_id, guild_id, amount, conn=None) -> int  # upsert + RETURNING karma_points (GREATEST(0, …))
async def insert_karma_audit(guild_id, from_user, to_user, delta, source, reason, conn=None) -> None
async def recent_grant_count(guild_id, from_user, to_user, since) -> int   # cooldown check
async def grants_given_since(guild_id, from_user, since) -> int            # daily-cap check
async def top_karma(guild_id, limit=10) -> list[dict]                      # leaderboard
```

### 4b. Service — `disbot/services/karma_service.py` (new)
The single write seam. Mirror `economy_service.py` / `xp_service.py`:

```python
EVT_KARMA_GRANTED = "karma.granted"   # add to core/events_catalogue.py KNOWN_EVENTS

@dataclass(frozen=True)
class KarmaGrant:
    to_user: int
    new_total: int
    delta: int
    source: str

class KarmaError(Exception): ...
class SelfKarmaError(KarmaError): ...
class KarmaCooldownError(KarmaError): ...   # carries retry-after
class KarmaDailyCapError(KarmaError): ...

async def give(guild_id, *, from_user, to_user, amount=1, source, reason=None) -> KarmaGrant:
    # 1. validate: from_user != to_user (SelfKarmaError); amount > 0
    # 2. anti-abuse: recent_grant_count(...) within KARMA_COOLDOWN → KarmaCooldownError
    #                grants_given_since(... start-of-day) >= KARMA_DAILY_CAP → KarmaDailyCapError
    # 3. write:   new_total = await db.credit_karma(to_user, guild_id, amount)
    # 4. audit:   await db.insert_karma_audit(guild_id, from_user, to_user, amount, source, reason)
    # 5. emit:    await bus.emit(EVT_KARMA_GRANTED, guild_id=..., from_user=..., to_user=...,
    #                            delta=amount, new_total=new_total, source=source)
    return KarmaGrant(to_user, new_total, amount, source)

async def get_user_record(guild_id, user_id) -> KarmaRecord | None
```
Bot-author / self checks that need Discord objects (is the target a bot?) live in the **cog** before
calling the service; the service owns the data-level rules (self-id, cooldown, cap).

### 4c. Settings — `disbot/utils/settings_keys/karma.py` (new) + `cogs/karma/schemas.py`
```python
KARMA_ENABLED          = "karma_enabled"            # bool, default True
KARMA_COOLDOWN         = "karma_cooldown"           # seconds, per (giver→receiver), default 3600
KARMA_DAILY_CAP        = "karma_daily_cap"          # grants/giver/day, default 10
KARMA_REACTION_ENABLED = "karma_reaction_enabled"   # bool, default False (phase 3)
KARMA_EMOJI            = "karma_emoji"              # reaction-grant emoji, default ⭐
KARMA_LOG_CHANNEL      = "karma_log_channel"        # optional announcement channel
```
Re-export from `settings_keys/__init__.py`; declare `SettingSpec`s in `cogs/karma/schemas.py`
(`register_schemas()` called from `cog_load()`), read via `services.settings_resolution.resolve_setting`.

### 4d. Cog — `disbot/cogs/karma_cog.py` (new)
- `!thanks @user [reason]` (alias `!karma give @user`) — prefix; rejects self/bot at the cog layer,
  calls `karma_service.give(..., source="command")`, renders the new total + a friendly cooldown/cap
  message on the typed errors.
- `!karma [member]` — show a karma card (points, received/given counts, rank).
- `/karma` — ephemeral slash panel.
- `cog_load()` — `register_schemas()`.

### 4e. Leaderboard — `KarmaProvider` in `disbot/services/rank_providers.py`
Add a `RankProvider` subclass (`name="karma"`, `display_title="✨ Karma Leaderboard"`, `top()` →
`db.top_karma`, `member_rank()` → rank query) and append `KarmaProvider()` to the `_PROVIDERS` dict
(+ an alias e.g. `"rep" → "karma"` in `ALIASES`). No leaderboard-cog change needed — the category
selector is registry-driven.

### 4f. Docs (ship with the code)
- `docs/ownership.md` — add `karma` table-owner row, the service-owner row (+ `INV-K` note), the
  `karma_audit_log` append-only row, and the `karma.granted` event-payload row.
- `docs/subsystems/karma.md` — new folio (mirror `games.md` / economy structure).
- `docs/agent/index.yml` — a `karma` manifest entry (then rebuild the context pack per the
  context-compiler rule).

## 5. PR slicing (2–3 PRs)

**PR 1 — Foundation + audited seam** (root/debt-free base, no UI risk):
- migration (both tables) · `utils/db/karma.py` · `services/karma_service.py` (`give` + anti-abuse +
  `get_user_record` + `karma.granted` catalogue entry) · `settings_keys/karma.py` + `cogs/karma/schemas.py`
- `tests/unit/invariants/test_no_direct_karma_writes.py` (INV-K, AST: no `db.credit_karma`/
  `insert_karma_audit` outside the service) · `tests/unit/services/test_karma_service.py`
  (grant, self-karma reject, cooldown, daily-cap, audit row, event payload) + a concurrent test
- `docs/ownership.md` rows + `docs/subsystems/karma.md` folio.

**PR 2 — Cog + leaderboard + UX** (the player-facing half):
- `cogs/karma_cog.py` (`!thanks`, `!karma` card, `/karma`) · `KarmaProvider` in `rank_providers.py`
- help-menu integration · cog/command tests.

**PR 3 — Reaction-grant + milestones (optional, owner-gated):**
- `on_raw_reaction_add` listener behind `KARMA_REACTION_ENABLED` (reuses the reaction-roles raw seam),
  granting `source="reaction"` · milestone event + optional `KARMA_LOG_CHANNEL` announcement ·
  **karma roles** (auto-assign a role at thresholds, via `role_grants`) if Q4 = yes.

Each PR is independently mergeable and leaves the bot in a working state (PR 1 ships the seam with no
user surface; PR 2 turns it on).

## 6. Risk / invariants checklist
- Layering: cog → service → db only; no `services → views`; `check_architecture --mode strict` green.
- Every mutation audited + `emit_audit_action`-compatible; INV-K guards the write seam.
- New event registered in `core/events_catalogue.py` (else EventBus warns).
- New **runtime** dep: none. New tables: migration-only (bootstrap frozen).
- Anti-abuse covered by tests (self/cooldown/cap) — the highest-value tests in the suite for this feature.

## 7. Open questions for the owner (gate PR 1)
1. **Grant surface** — command-only, reaction-only, or **both** (recommended: command in PR 2,
   reaction behind a setting in PR 3)?
2. **Downvotes** — positive-only (recommended; avoids a harassment vector), or allow negative karma?
   The `delta`-signed schema leaves the door open either way.
3. **Pure reputation vs. economy bridge** — keep karma non-spendable (recommended, matches the chosen
   flavor), or ever let it convert to coins / unlock perks?
4. **Karma roles** — auto-assign a role at thresholds (e.g. "Trusted Helper" @ 50)? Phase 3, or skip?
5. **Defaults** — cooldown (proposed 1h per giver→receiver) and daily cap (proposed 10/giver/day) OK?

> Recommended default direction if the owner doesn't want to decide each: **both surfaces (reaction
> off by default), positive-only, pure reputation, karma-roles deferred to a later phase, defaults as
> proposed.** PRs 1–2 ship that; PR 3 + karma-roles wait on Q1/Q4.
