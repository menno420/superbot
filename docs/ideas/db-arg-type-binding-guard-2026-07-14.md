# Idea — a call-site guard for `db.*` argument type-binding (str vs BIGINT `user_id`)

> **Status:** `ideas` — raised 2026-07-14 (forty-seventh Q-0107 reconciliation pass). **Class:**
> friction→guard (enforce, don't exhort — Q-0132) · **Sector:** S3 (self-improving workflow / CI
> guards) · **Origin:** band-#2100 reconciliation (#2089).

## The friction (observed this band)

PR **#2089** fixed `!mine` crashing on **every** open: `build_grid_embed` passed a stringified
`suid` to `db.get_skills`, but `player_skills.user_id` is **BIGINT** (shared with `game_xp`), not
the legacy **TEXT** `user_id` that the other mining reads use. asyncpg cannot encode a `str` as
`int8`, so it raised `DataError` at runtime — in production, on the owner's screen, caught by a
**Discord screen-recording**, not by CI.

**Why CI was green:** `tests/unit/views/test_mining_grid_view.py` mocks the `db` module with
`AsyncMock`, so the real asyncpg type binding never ran — a str/int mismatch is **invisible to a
mocked DB**. This is a recurring, dangerous class: the codebase carries *two* `user_id`
conventions (legacy TEXT vs the shared BIGINT `game_xp`/`player_skills`), and a call site that
stringifies for one and reuses the string for the other type-checks fine, tests green, and dies
only against real Postgres.

## The improvement

A lightweight **AST call-site guard** (`scripts/check_db_arg_types.py`, the `check_architecture`
family) that:

1. Builds a small registry mapping each `utils/db/**` accessor → the declared type of its keyed
   column (TEXT vs BIGINT `user_id`), derived from the migrations / the `db` submodule signatures.
2. At every `db.<fn>(...)` call site, flags an argument that is provably the wrong type for that
   key — e.g. a name bound to `str(user_id)` / a `suid` local passed where the accessor keys on
   BIGINT, and the reverse.

Even a *conservative* version keyed only on the `suid = str(...)` idiom vs the int `user_id` would
have caught #2089 at CI. It closes the exact gap the mocked-DB unit tests leave open, at the root,
without needing a live-Postgres integration run in the fast lane.

Adopt-freely with the standard provenance + kill-switch header (Q-0105): if the type registry
proves noisy or hard to keep in sync across migrations over a few sessions, delete it rather than
work around it. Companion to the real-Postgres regression guard #2089 already added for the single
site — this generalizes that guard to the whole `db.*` surface.

## Why it's worth having

Same instinct as the existing audit-seam / deferred-recovery AST guards: turn a bug that escaped
to production into a check that catches its whole class next time. The bug was owner-visible and
recurred (BUG-0026 → #2089), which is exactly the bar for promoting exhortation into enforcement.
