# 2026-06-23 — Fishing bait-crafting (close the catch→cook→bait economy loop)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Routine · dispatch (empty-fire schedule; promotes the `fishing-bait-crafting-2026-06-22`
> idea → build, Q-0172). PR #1338 → auto-merges on green (Q-0123).

## Arc

Empty-fire dispatch run, no work order. The product lanes that need creds/browser/network
are all gated (BTD6 live `llm_judge` battery · botsite React PR 2 cutover (attended browser) ·
Project Moon ingest (network/IP-sensitive)), so I promoted the cleanest **fully-offline-testable**
S1 idea — **bait crafting from caught fish** ([idea](../ideas/fishing-bait-crafting-2026-06-22.md))
— to a shipped build (idea → build in one hop, Q-0172). It builds directly on the just-shipped
bait layer (#1329/#1337) and the cook/campfire loop (#1289): small caught fish become a
*gameplay-native* second source of bait beside the coin shop, closing
`catch → craft → bait → bigger catch`.

## Shipped (PR #1338)

- **`utils/fishing/bait.py`** (pure) — `BaitRecipe` + `CRAFT_RECIPES` (worm/minnow = 3 fish ≤ rank 3;
  grub/spinner = 5 fish ≤ rank 6; lure = 6 fish ≤ rank 9). The premium combo (`feast`) is
  deliberately **not** craftable — it stays a pure coin sink (the top-end spend reason).
  `CRAFTABLE_KEYS`, `craft_recipe`, `recipe_text`, `craftable_key_for` (key/name resolver).
- **`services/fishing_workflow.py`** — `craft_bait` op + `_plan_fish_spend` (smallest-rank-first
  greedy, so the player keeps their bigger catches). An inventory→bait conversion in ONE
  `db.transaction()` (Q-0071), mirroring `cook`/`buy_bait` — **no coin debit**, stacks like a
  same-bait purchase, replaces a different loaded bait. `BaitCraftResult`.
- **`views/fishing/bait_shop.py`** — a "Craft from fish" select (craftable baits only, recipe in
  the description) + a "Craft from fish" recipe field on the panel embed.
- **`cogs/fishing_cog.py`** — `!craftbait [bait]` (alias `baitcraft`): with a name crafts directly,
  bare opens the bait panel (where the Craft select lives).
- **Tests:** +9 recipe/resolver cases in `tests/unit/utils/test_fishing_bait.py`; +8 `craft_bait` /
  `_plan_fish_spend` cases in `tests/unit/services/test_fishing_workflow_bait.py`.
- **Regenerated generated artifacts** (the new `!craftbait` command): `botsite/data/site.json`,
  `botsite/site/data.js`, `dashboard/data/dashboard.json` (command count 383 → 384) via
  `python3.10 scripts/export_dashboard_data.py`.

## Verification

- `python3.10 scripts/check_quality.py --full` → **All checks passed** (11916 passed, 47 skipped,
  2 xfailed). · `check_architecture --mode strict` → **0 errors** (49 pre-existing warnings).
- Targeted: 32/32 fishing bait tests; 79/79 freshness + botsite tests.

## Process note (for the next run)

Hit the CLAUDE.md "don't hand-run bare black over a broad scope" trap: after the `--full` flagged
black, I ran `python3.10 -m black disbot/ tests/ scripts/`, which reformatted **353 files** —
because **CI excludes `tests/` from black/isort/ruff**, the committed test tree is deliberately
unformatted, and the broad run churned all of it. Reverted everything except my 6 target files,
then re-confirmed with `--check-only`. **Lesson: trust `check_quality.py` (pinned scope) — never
bare-black `tests/` to chase a red signal.**

## Session enders

- **♻ Grooming (Q-0015):** moved the `fishing-bait-crafting-2026-06-22` idea down its lifecycle
  `ideas → shipped` (idea file re-statused with the as-built note + the implementing symbols).
- **💡 Session idea (Q-0089):** *A "Cook all" / "Craft all eligible" bulk affordance on the
  campfire + bait panels.* Both `cook` and now `craft_bait` operate one batch at a time; a player
  with 40 minnow clicks the craft select repeatedly. A single "use everything eligible" button
  (bounded by a sane cap) would smooth the grind without changing the economy. Small, contained,
  on the existing seams — a clean next turn-key slice. Logged, not built here (kept scope to the
  idea I promoted).
- **⟲ Previous-session review:** the #1320 tool-pins-CI-guard run was exemplary dispatch hygiene —
  it not only built the guard but *extended* it to genuinely cover all three pin sources (its own
  message had been over-promising) and added the first unit test, applying the "a guard that
  under-checks is worse than none" instinct. What it could not foresee (no fault): the `code-quality`
  workflow still hard-codes its tool versions inline, so the three-places rule isn't yet collapsed to
  one — which is exactly the idea it logged. **System note:** the born-red/auto-merge loop worked
  cleanly again this run; the one rough edge is that the *first* `code-quality` failure webhook
  (born-red card) looks alarming out of context — a session that didn't know Q-0133 might "fix" a
  non-bug. Worth a one-line note in the dispatch prompt that the first born-red CI failure is
  expected and self-resolves on the `complete` flip (captured as a candidate, not applied — CLAUDE.md
  is read-only to an autonomous run).
- **📋 Doc audit (Q-0104):** S1 sector file de-staled (bait-crafting moved shipped→done in the
  "next startable" line + added to recently-shipped); idea re-statused; ledger entry for #1338 is
  the next reconciliation pass's job (the born-red card is the in-flight signal). No drift spotted
  in the bug book or current-state hub.

## 📤 Run report

- **Run type:** routine · dispatch
- **⚑ Self-initiated:** promoted `fishing-bait-crafting-2026-06-22` (idea) → build → ship with no
  dispatch/owner ask (Q-0172) — a fully reversible, test-covered S1 game feature.
- **⚑ Owner-decisions:** none
- **⚑ Owner-manual-steps:** none (merge auto-deploys to Railway, Q-0193; `fishing_bait` table
  already exists from migration 091 — no new migration).
