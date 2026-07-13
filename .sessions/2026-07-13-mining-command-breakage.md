# 2026-07-13 — Fix `!mine` breakage: str user_id passed to a BIGINT-keyed read

> **Status:** `complete`
> **Branch:** `claude/mining-command-breakage-ypve0d` · **PR:** #2089
> **Venue:** remote container (owner-directed from a Discord screen-recording). **📊 Model:** Opus 4.8 (Claude Opus family).
> **Scope:** one-line runtime bug fix in `build_grid_embed` + a durable regression guard. No schema, no cross-cutting change.

## Arc

**Symptom (from the maintainer's screen-recording).** `!mine` replies
**"⚠️ An unexpected error occurred. Please try again."** every time, while the Mining Hub
(`!minemenu` / the Games-hub "Mining" button) and every hub button work. The error is a
non-ephemeral `ctx.send`, so it comes from `bot1.py`'s `on_command_error` — i.e. the `mine`
**command itself raised**.

**Root cause.** `!mine` → `MiningCog.mine` → `build_grid_embed`. That builder computes
`suid = str(user_id)` and (correctly) passes `suid` to the TEXT-keyed mining reads
(`mining_player_state`, `mining_equipment`, `mining_discovered` all use a TEXT `user_id`).
But it also called `db.get_skills(suid, guild_id)` — and `player_skills.user_id` is **BIGINT**
(shared with `game_xp`, not the legacy TEXT column). asyncpg cannot encode a `str` as int8, so
it raised `DataError: 'str' object cannot be interpreted as an integer` on **every** open. The
Mining Hub never reads `player_skills` on its overview path, which is why only `!mine` broke.

**Provenance.** The offending line was introduced by `0c4b70b6` (BUG-0026, 2026-06-27, "wire
light_radius + luck into gameplay") — before that `build_grid_embed` never read skills, so `!mine`
worked. Every other `get_skills(...)` call site in the repo (7 in services, 2 in `skills_panel`)
passes the int `user_id`; `grid_mine_view.py:48` was the lone outlier.

**Why the tests were green.** `tests/unit/views/test_mining_grid_view.py` mocks the `db` module
functions with `AsyncMock`, so the real asyncpg type binding never ran — a str/int mismatch is
invisible to a mocked DB. Confirmed by booting a real Postgres (all 104 migrations applied),
seeding a progressed player, and running the actual path: `get_skills(str)` → `DataError`,
`get_skills(int)` → OK, and `build_grid_embed` with the int fix builds the embed end-to-end.

**Other-errors sweep (owner's second ask).** Smoke-tested every mining embed builder + workflow op
against the same real Postgres: **16/17 pass; only `build_grid_embed` failed** (this bug).
Grepped the whole repo for the same footgun class (stringified id → BIGINT-keyed fn, and the
reverse) — `grid_mine_view.py:48` is the **sole** instance; `character_hub` etc. stringify
correctly. The mining subsystem is otherwise clean.

## Shipped

- **Fix** — `disbot/views/mining/grid_mine_view.py`: `get_skills(suid, …)` → `get_skills(user_id, …)`
  with a comment on the TEXT-vs-BIGINT `user_id` split so it doesn't regress.
- **Regression guard** — `tests/unit/views/test_mining_grid_view.py`:
  `test_build_grid_embed_passes_int_user_id_to_bigint_keyed_reads` pins BOTH halves — `get_skills`
  gets the **int** id; the TEXT-keyed reads get the **str**. Verified it **fails on the old code**
  (`assert '1234' == 1234`) and passes with the fix — a real guard, not a rubber stamp.
- Quality mirror: `python3.10 scripts/check_quality.py --full` → **All checks passed ✓**
  (13996 passed, 42 skipped, 2 xfailed) · `check_architecture --mode strict` → exit 0
  (only pre-existing known warnings). Clear the claim file at close.

## Enders

- **⟲ Previous-session review** (`2026-07-12-hub-upkeep`): a tight, well-scoped docs-only fix that
  cross-checked the sibling repo before editing — good discipline. What it (and the wider session
  chain) *missed* is the class of bug found here: **the mining unit tests mock the DB, so no test
  in the suite exercises a real asyncpg type binding.** System improvement surfaced & acted on:
  this session adds a call-arg **type-contract** assertion (cheapest CI-runnable guard for a
  mock-hidden str/int mismatch), and the idea below proposes generalizing it.
- **💡 Session idea** — *TEXT-vs-BIGINT `user_id` lint*: a tiny AST/checker rule that flags any
  `db.<fn>(<arg>, …)` where `<fn>`'s first param is annotated `user_id: int` but `<arg>` is a
  known-str expression (`str(...)`, a `suid`/`*_str` name), and the reverse for `user_id: str`.
  This bug lived a fortnight behind green mocks; one grep-cheap enforcing check would catch the
  whole class at edit time. Filed for grooming, not built this session (kept the PR to the fix).
- **⚑ Self-initiated:** none beyond the owner-directed fix + its regression guard + this idea note.

## Verification note

Real-Postgres repro + the 17-path mining smoke test were run in a throwaway cluster in the session
scratchpad (not committed). The durable artifact is the mocked call-arg contract test above, which
runs in CI without a database.
