# Session — games-economy faucet/sink diagnostic (`!platform economy`)

> **Status:** `complete`

## Why

The live ▶ Next action (current-state, band-#930 decade queue §4): build the read-only
faucet/sink economy diagnostic so the owner can *observe* whether the games economy inflates
instead of guessing from static balance sims. Gate cleared — respec (#912) + structures sinks
(#905 Forge / #910 Home) now emit real sink reasons. Turn-key plan:
`docs/planning/games-economy-faucet-sink-diagnostic-plan-2026-06-15.md`.

## What I'm shipping (this PR)

A read-only operator read model that sums the **economy audit ledger** (`economy_audit_log`,
already written on every coin movement) into a per-guild **faucet vs. sink** view — coins
minted, drained, net flow, mint:drain ratio + verdict, and the per-reason breakdown over a
time window — surfaced as `!platform economy [days]` beside `media` / `event_bus`. No new
writes, no new reasons, content-free (counts + coin totals only, no per-user rows).

- `utils/db/economy.py` — `economy_flow_by_reason(guild_id, *, since=None)` pure read
  (`SELECT reason, SUM(delta), COUNT(*) ... GROUP BY reason`), windowed by `occurred_at`.
- `services/economy_flow_service.py` (new) — `EconomyFlowReport`/`ReasonFlow` + `build_flow_report`;
  classifies each reason by the **sign** of its summed delta (self-cleaning — new reasons sort
  automatically), computes totals/ratio/verdict (inflating ⚠ / draining / balanced / no activity).
- `cogs/diagnostic/_platform_embeds.py` — `build_economy_flow_embed`; `diagnostic_cog.py` —
  `!platform economy [days]` (alias `coinflow`).
- Tests: `tests/unit/services/test_economy_flow_service.py` (split/sort/ratio/edge cases) +
  `tests/unit/db/test_economy_db_txn.py` (SQL-shape: group-by, windowed `occurred_at`).

## Verification

`check_quality.py --full` green (9905 passed) · `check_architecture.py --mode strict` 0 errors.
mypy clean (697 files). The PR's only red check is the born-red session gate (Q-0133), which
clears on this card flipping to `complete`.

## Handoff (▶ next)

Repointed the live ▶ Next action to **myprofile PR A — read-only profile card** (decade-queue
slot 3, `ready`). The faucet/sink diagnostic (slot 2) is **shipped pending merge as PR #937**;
the next session reconciles it into current-state Recently-shipped (ledger ratchet is at 20 —
archive an old entry when adding it). **`diagnostic_cog.py` is now 799/800 LOC** — the next
`!platform` subcommand must decompose the cog's `platform_*` group first (see the session idea).

## 💡 Session idea (Q-0089)

**Extract the `!platform` command group into a `cogs/diagnostic/` cog mixin.** This session hit the
800-LOC cog ceiling adding one thin `!platform` subcommand — the *embed builders* already moved out
to `_platform_embeds.py` (the F-3 decompose), but the ~30 command *registrations* (`platform_status`,
`platform_media`, …) still live in `diagnostic_cog.py`, which is now at 799/800. discord.py command
groups can be defined on a base/mixin class the cog inherits, so a `PlatformCommandsMixin` in
`cogs/diagnostic/platform_group.py` would let the `!platform` surface keep growing without fighting
the cog ceiling. Dedup-checked `docs/ideas/`: the closest entries are the general cog-improvement
audit and the views-residence guard — neither proposes the platform-group mixin extraction. Worth a
small idea file; it's the structurally-correct unblock for the next `!platform` subcommand rather
than shaving docstrings to stay under 800 (what this session had to do).

## ⟲ Previous-session review (Q-0102)

The previous run (BUG-0013, the 1v1 challenge-timer fix) was clean — root-caused the leaked
`_ChallengeView` timeout, added the `_resolved` guard + `self.stop()`, and named a regression test —
and notably it was *diagnosed* by the Hermes `intake` skill (gpt-5.4-mini), the loop's first real
end-to-end live bug catch. What it shows about the *system*: the bug-book → dispatch path works, but
there's no automated check that a bug-book entry marked **FIXED** actually has its named regression
test present and passing on `main`. A tiny `scripts/check_bugbook_tests.py` (parse each FIXED entry's
"Regression test:" path, assert the file exists) would close the gap where a "FIXED" claim drifts
from reality — the same "verify, don't assert" discipline the dispatch routine applies to its own
work. (Captured as the candidate, not built here — one idea per session.)

## Doc audit (Q-0104)

`check_quality --full` green; arch 0; mypy clean. Did **not** add #937 to current-state
Recently-shipped (convention: merged PRs only — it's unmerged at write time; next session
reconciles). Repointed the live ▶ pointer instead. No new owner decisions this session (a
dispatched plan slice, no Q-block). The plan doc stays `plan` until the PR merges.
