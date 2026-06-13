# 2026-06-13 — Welcome v1 + server counters (band slot 6, Q-0110)

> **Status:** `complete`

**PR:** #775 (`claude/wonderful-fermat-ud5hwi`) — opened ready at first push, merged
in-turn on CI green.
**Band:** the second Q-0107 [band queue](../docs/planning/reconciliation-pass-2026-06-12-night.md)
slot 6 — the **final slice of the safety/community lane** (slots 4–6 now complete).

## Context

Continuation prompt: "continue where the last session ended." The previous session
merged server event logging v1 (#774, slot 5), so the live band-queue item was **slot 6
— welcome v1 + counters (Q-0110)**. Open-PR check first (#771/#766/#704 were
ledger/idea/owner PRs — none claimed the lane).

## What shipped

Owner scope (Q-0110): **welcome** = join/leave embed + entry role, embed-first (PIL card
= phase 2); **counters** = the scheduled channel-rename quick-win. Both are the
`mock_welcome_ab` / `mock_counters` UX shapes made real.

**welcome** (new `welcome` subsystem):
- `services/welcome_config.py` — `WelcomePolicy` read model; injection-safe
  `{user}/{server}/{count}` `render_template` (plain `.replace`, not `str.format`, so a
  stray brace never raises).
- `services/welcome_service.py` — embed builders + fail-safe `handle_member_join`/
  `handle_member_leave`; the optional entry role routes through the **audited**
  `role_automation.apply` (`actor_type="system"`) — no parallel role/audit path.
- `cogs/welcome/schemas.py` + `cogs/welcome_cog.py` — settings group (channel/role
  pickers via `input_hint`), `on_member_join`/`on_member_remove` listeners, `!welcome`
  summary, Help hook. Advisory `welcome.member_greeted`.

**counters** (new `counters` subsystem):
- `services/counter_config.py` — `CounterPolicy` with an `active` enumeration folding the
  master switch + bindings; length-capped `render_counter_name`.
- `services/counter_service.py` — `compute_counts` (total via `member_count`, bots from
  the cache, humans = remainder) + `sync_guild` (fail-safe per guild + per channel,
  change-detection); advisory `counters.updated`.
- `cogs/counters/schemas.py` + `cogs/counters_cog.py` — settings group + the
  `@tasks.loop(minutes=10)` rename loop (**never per join** — Discord's ~2/10-min rename
  cap; change-detection keeps it under) + `!counters` summary + Help hook.

Both default OFF (master switch) → a fresh guild is unaffected; **no migration** (scalar
`welcome_*`/`counters_*` KV settings).

## The key design call — two hub-less new subsystems

Applied the #774 session's extend-before-mint rubric (family plan §3.7): **checked** for
an existing subsystem to extend — there is none for greetings or stat-channels, so both
are genuine new mints (each has its own identity/lifecycle: welcome = member events,
counters = a scheduled loop). The non-obvious part: I made both **hub-less** (no
`parent_hub`). The Community hub surfaces *every* `parent_hub=="community"` child to all
users with **no tier filter** (`views/community/hub.py`), so parenting these
admin-config features there would dump operator config into the user-facing hub. Hub-less
+ admin `visibility_tier` + the Help hook + `!settings` + `!welcome`/`!counters` is the
right discoverability shape (the `ai`/`channel`/`ux_lab` precedent). This consciously
extended the help-render-paths `_TOP_LEVEL` pin.

## Process notes — the new-subsystem cascade, twice

`scripts/new_subsystem.py check` is the executable cascade list — it caught every missing
touch-point (registry · settings_keys re-export · INITIAL_EXTENSIONS · events_catalogue ·
surface-map row + counts · settings-customization 24-field section · ownership · nav-map).
Two surfaces it does **not** cover, both caught only by the full suite, both bit me:
- **`test_guild_resources_invariant`** — raw `guild.get_channel`/`guild.get_role` is
  banned; route through `core.runtime.resources.resolve_*`. Easy to miss because the raw
  call "works" — only the AST gate flags it. (Worth adding to the family-plan seam table.)
- **`test_help_render_paths::test_advanced_top_level_set_today`** — a hub-less subsystem
  joins `_TOP_LEVEL`, which is pinned to an exact list; the pin must be consciously updated.
- Plus the black↔ruff trailing-comma dance on lines black split (COM812) — the PostToolUse
  hook fixes this on `Edit` but **not on `Write`-created files**, so new files need a manual
  `ruff --fix` + `black` pass.

**Verification:** `check_quality --full` green (9292 passed) · `check_architecture
--mode strict` 0 errors · `check_docs`/`check_current_state_ledger` strict clean · live
boot on Galaxy Bot (real Postgres): `✅ Loaded cogs.welcome_cog` + `✅ Loaded
cogs.counters_cog`, `Logged in`, command_descriptions built 0-errored, **0
ERROR/CRITICAL**. 65 new tests.

## 💡 Session idea (Q-0089)

**A "Safety & Community" operator landing** — the lane now has **four** admin-config
subsystems (automod, logging, welcome, counters; image-mod + security coming) that are
deliberately scattered across hubs (automod/logging → moderation; welcome/counters →
hub-less) for good per-feature reasons. But the family plan frames them as **one
platform**, and there is no single operator front door that says "here's your whole
automated safety+community layer, here's what's on/off." Idea: a `!safety`-style landing
(or a Settings supergroup) that lists every lane subsystem with its master-flag state +
a jump to each `!settings` group. Why I believe in it: going hub-less was right for the
*user* hub, but it left the *operator* without the "one platform" view the plan promises;
this is the missing front door, and it composes cleanly from the existing
`SubsystemSchema` registry (read-only, zero new mutation path). Dedup-checked
`docs/ideas/` — captured fresh as
[`ideas/safety-community-operator-landing-2026-06-13.md`](../docs/ideas/safety-community-operator-landing-2026-06-13.md).

## ⟲ Previous-session review (Q-0102) — server event logging v1 (#774)

**Did well:** the standout call was *extending* the `logging` subsystem instead of minting
a new one — it paid **zero** pinned-surface cascade and the session correctly named that
as the whole-session win, then generalised it into the family-plan §3.7 extend-vs-mint
rubric. That rubric is exactly what let *this* session make its mint/extend decision
quickly and correctly. High-leverage, well-recorded.

**Missed / could improve:** the rubric it added lives only in prose, in a single **lane
doc** (the family plan). The decision it governs — "extend or mint?" — is faced by *every*
future subsystem, most of which will never open that family plan. The guidance has no home
on the path an agent actually walks when adding a subsystem (`scripts/new_subsystem.py`,
`docs/helper-policy.md`).

**Concrete system improvement (initiated here):** I added the extend-vs-mint question as
the **first line of `scripts/new_subsystem.py scaffold`'s output** — so the tool an agent
runs *to create* a subsystem now asks "should this extend an existing one instead?" before
printing any boilerplate. That moves the #774 rubric from a lane doc onto the executable
path, which is where it changes behaviour. (Tooling/docs — free-rein; no CLAUDE.md change.)

## Docs audit (Q-0104)

`check_current_state_ledger --strict` clean (ledger has #775; trimmed #729/#730/#731 to the
archive to clear the soft ratchet). `check_docs --strict` clean (every spec/binding/key in
the customization map; both subsystem docs + ownership + nav-map + family plan reachable).
No owner decisions made this session (Q-0110 was already answered) — nothing new for the
router. Band queue + family plan §4 both mark slot 6 ✅; the safety/community band (slots
4–6) is complete.
