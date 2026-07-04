# 2026-07-01 — PROD hotfix: fishing `dock` command collided with `sail`'s `dock` alias (crash loop)

> **Status:** `complete`

**Incident:** Railway `worker` in a boot crash loop (restart every ~30s, never reaching the
gateway). Reported via attached deploy logs. Owner-directed live session. ⚑ **Self-initiated:**
the guard-generalization below (broadening the duplicate-token CI check to catch *same-cog*
collisions) goes beyond the literal one-line alias fix — added as root-cause prevention for the
whole same-cog collision shape.

## Root cause (confirmed from the deploy logs)

```
❌ Failed to load cogs.fishing_cog: CommandRegistrationError:
   The command dock is already an existing command or alias.
→ Subsystem 'fishing' has no loaded commands — marking INTERNAL
→ entry_point 'fish'/'fishlog' declared by 'fishing' is not a loaded command
→ Identity-contract findings | total=2 | fatal=2 | STRICT=on | abort=yes
→ Identity-contract: STRICT mode aborting startup.
```

A **same-cog** top-level token collision inside `FishingCog`:

- `!sail` (`disbot/cogs/fishing_cog.py:112`) has carried `dock` as an **alias** since `98a692d`
  (2026-06-29) — "dock back on shore", the venue toggle.
- **PR #1599 / commit `8744a7b`** (`feat(fishing): Dock — bite-speed coral structure`) added a
  first-class command literally **named** `dock` (the Tide Pool's sibling: view + embed + audited
  build seam + tests, all keyed to `structures.DOCK = "dock"`).

At `add_cog`, `sail` registers first (claiming alias `dock`); the new `dock` command's name then
collides → `CommandRegistrationError` → the whole cog fails to load → its declared entry points
(`fish`, `fishlog`) vanish → STRICT identity-contract aborts boot. Crash loop, never reaches the
gateway → offline.

## Why CI didn't catch it (the guard gap)

The `give` crash (2026-06-29) added `test_no_duplicate_top_level_command_names_across_cogs`, but it
de-duplicated claimants **by cog** (`len(set(cogs)) > 1`) — so a single cog claiming a token twice
(here `dock` = `sail`'s alias **and** the `dock` command's name, both in `FishingCog`) looked like
*one* claimant and slipped through. This fell in the gap **between** the two existing guards:
Q-0200's exact-name guard is same-*module* but matches `def` names (sees `def sail` ≠ `def dock`),
and the cross-cog guard dedupes by cog. Neither models a same-cog **name-vs-alias** clash. The
runtime `command_surface_ledger` can't help either — it only sees commands *after* they load, which
a collision prevents.

## What changed

- **`disbot/cogs/fishing_cog.py`** — dropped the vestigial `dock` alias from `!sail`
  (`aliases=["setsail", "dock"]` → `["setsail"]`); the new `!dock` structure command owns the name
  (its natural, discoverable entry point). `!sail` + `!setsail` still fully cover the venue toggle;
  docstring reworded ("dock back on shore" → "return to shore") so nothing implies `!dock` toggles.
- **`tests/unit/invariants/test_extension_integrity.py`** — broadened the guard (enforce, don't
  exhort — Q-0194/Q-0132): `_top_level_command_tokens` → `_top_level_command_claims`, now counting
  distinct **commands** per token (identity-deduped, so a command's own name+aliases is one claim
  but two commands are two). Renamed `…_across_cogs` → `test_no_duplicate_top_level_command_tokens`
  — it now catches **same-cog and cross-cog** token collisions uniformly. Regression-proven: with
  the alias re-added it fails `!dock: FishingCog.dock, FishingCog.sail`; removed, it's green. A full
  scan found **no other** same-cog collisions in the bot.
- **`docs/owner/maintainer-question-router.md`** — updated the Q-0211 enforcement reference to the
  renamed/broadened guard (drift-on-sight, Q-0166).
- **Generated data** — regenerated `dashboard/data/dashboard.json`, `botsite/data/site.json`,
  `botsite/site/data.js` so the displayed alias lists no longer show `!dock` under `sail` (command
  *names* unchanged, so no structural-drift surface moved; timestamp/changelog churn is volatile).

## Verification

- `python3.10 scripts/check_quality.py --full` → **green**: `All checks passed ✓`
  (black + isort + ruff + mypy + **13433 passed, 48 skipped, 2 xfailed**; artifacts fresh).
- `python3.10 scripts/check_architecture.py --mode strict` → **exit 0** (only pre-existing `[known]`
  warnings; `fishing_cog` / the guard test unmentioned — no new violations).
- `python3.10 scripts/check_current_state_ledger.py --strict` → in sync.
- Guard regression: re-adding the alias ⇒ test fails `!dock: FishingCog.dock, FishingCog.sail`;
  removing ⇒ 60/60 green. Full-bot scan: no other same-cog token collisions.
- CI `code-quality` green except the intentional born-red session gate (this card), flipped to
  `complete` as the deliberate final step.

**Recovery:** merge → Railway auto-redeploys `worker` → bot back within minutes (the merge IS the
deploy; no manual restart — Q-0193). **Live-verify** the worker reaches the gateway post-merge (the
one step CI can't prove — no Discord runtime in CI).

## 💡 Session idea (Q-0089)

**CI "boot smoke test": construct a real `commands.Bot` and `await load_extension` for every
`config.INITIAL_EXTENSIONS`, asserting all load.** `test_extension_integrity` covers this class
*statically* (importable + coroutine `setup` + token-collision scan), but a real `load_extension`
would catch the *whole* `add_cog` failure surface end-to-end — token collisions, a raising
`cog_load`, duplicate view `custom_id`s, a bad `app_commands` tree — not just the subset a static
walk can model. This is now the **second** boot-crash collision in ~2 days (give cross-cog, dock
same-cog); each was a shape the static guards had to be *extended* to cover after the fact. A live
boot test would front-run the next unknown shape. (Idea only — needs a no-DB `setup_hook` path and a
fake token; gate behind a marker if slow. Worth a `docs/ideas/` file if it survives review.)

## ⟲ Previous-session review (Q-0102)

The previous session (`2026-07-01-fishing-dock-structure`, PR #1599) shipped the Dock feature
well — clean structure math, audited build seam, byte-identical unbuilt-cast path, thorough tests.
But it introduced the boot-crash: it registered a top-level command **named** `dock` without
grepping the existing token surface for `dock` (present as `!sail`'s alias since 2026-06-29). Its
own tests (`test_dock_registered_and_named`, the begin_cast fold) exercised the *structure logic*
but **never actually loaded the cog**, so the collision was invisible to them. **System improvement
(shipped this session):** the same-cog token guard now closes the exact hole, so this fails at CI
instead of at boot. **Deeper, recurring lesson:** *nothing verifies a merge actually stayed up in
prod* — same as the 2026-06-29 `give` review. Two boot-crashes in two days is a strong signal to
prioritize both a **live boot smoke test** (the idea above) and a **post-merge prod-health check**
(the 2026-06-29 degrade-don't-die territory).

## 📋 Doc audit (Q-0104)

- Ledger in sync at start and end (`check_current_state_ledger --strict` exit 0); PR #1600 will be
  recorded by the next reconciliation pass (#1620) — no self-referential placeholder (the pattern
  the early-PR-open rule removed).
- Owner router: no new *decision* (mechanical bug fix + test-guard extension, not product intent).
  Updated the existing **Q-0211** reference to the renamed guard for accuracy.
- New/changed docs reachable; no chat-only knowledge left un-homed (the guard-gap analysis lives in
  the test docstring + this card).

## Context delta (reflection interview)

- **Needed but not pointed to:** the three-layer collision-guard model (Q-0200 same-*module* `def`
  names · cross-cog token guard · runtime ledger) and the **gap between them** — reconstructed from
  the 2026-06-29 session log + guard source. Now captured in the guard's own docstring.
- **Pointed to but didn't need:** CodeGraph / broad orientation — this was a tight, log-driven
  root-cause fix; `grep` + reading two files carried it.
- **Discovered by hand:** the dashboard/site **freshness structural surface excludes aliases**
  (`_STRUCTURAL_SURFACES.commands` keys on `(cog, name)`), so an alias-only change causes no gated
  drift — reverse-engineered from `check_dashboard_data.py`.
- **Decisions made alone:** (a) remove `sail`'s vestigial alias rather than rename the `dock`
  *command* (the feature owns the name; renaming would ripple through `structures.DOCK`, tests,
  docs, artifacts). (b) broaden **+ rename** the existing guard rather than add a parallel same-cog
  test (one uniform guard > two). (c) regenerate artifacts despite the alias-only change (the public
  site/dashboard *display* alias lists). All reversible, none product-intent.
- **Flagged for maintainer / known limit:** the fix is static- and regression-test-proven but **not
  boot-tested in CI** (no Discord runtime) — the real end-to-end proof is the Railway redeploy;
  please confirm the worker reaches the gateway after merge.
- **🛠 Friction → guard:** *Friction* — a same-cog name-vs-alias command-token collision crash-looped
  prod and **no existing guard caught it** (it fell between the same-module and cross-cog guards).
  *Guard shipped (enforcing, free-to-ship test — Q-0194/Q-0132):* broadened
  `test_no_duplicate_top_level_command_tokens` to count distinct commands per token, so the same-cog
  shape now fails at CI. Regression-proven. No hook / settings / CLAUDE.md change needed.
