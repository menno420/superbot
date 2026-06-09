# BTD6 data refresh pipeline — fetch-everything-on-update (plan)

> **Status:** `plan` — design + ready-to-run command chain. The **manual chain
> below works today**, and the **`workflow_dispatch`-only GitHub Actions workflow
> is committed**: [`.github/workflows/btd6-data-refresh.yml`](../../.github/workflows/btd6-data-refresh.yml)
> (PR **#633**, 2026-06-09 — scoreboard Lane 5, per the Q-0049 sign-off: manual
> one-click trigger, **no schedule**, opens a reviewable PR, never pushes to
> main). The scheduled variant stays not-approved — adding any `schedule:`/cron
> trigger needs a new owner ask. Only the `--all` cutover tail remains gated
> (see below).

## Goal (maintainer, 2026-06-08)

A system that **reliably re-fetches all relevant game data whenever BTD6 updates**
— ideally on a **schedule / interval**, so the committed data never silently goes
stale against a new patch. The dump (`Btd6ModHelper/btd6-game-data`) is re-exported
each patch; we want a repeatable "pull → extract everything → audit → report"
motion, not a hand-run one-off.

## The building blocks already exist

Every step is a tested command in `scripts/`; the pipeline is *chaining* them, not
new extraction logic:

| Step | Command | What it does |
|---|---|---|
| 1. Pull | `git clone --depth 1 …/btd6-game-data /tmp/btd6gd` | fresh dump (not vendored) |
| 2. Guard | `parse_gamedata.py --dump … --validate-anchors` | abort if the dump moved unexpectedly (Dart 200 / Super 2500) |
| 3. Map all | `parse_gamedata.py --dump … --all` | full game-native extract (the cutover output) |
| 4. Safe refresh | `parse_gamedata.py --dump … --overlay` | conservative uniquely-keyed numeric refresh (no name regressions) |
| 5. Audit | `parse_gamedata.py --dump … --audit` | per-field fidelity (must stay nothing-SUSPECT) |
| 6. Coverage map | `btd6_gamedata_inventory.py --dump … --full-map --out docs/btd6/btd6-dump-coverage-map.md` | regenerates the per-domain "what's in each file" + fetch-status map |
| 7. Decode inventory | `btd6_decode_inventory_report.py` | refreshes the SHA-pinned decode roll-up |

**Manual chain that works right now** (the "fetch everything at once" primitive):

```bash
DUMP=/tmp/btd6gd
git clone --depth 1 https://github.com/Btd6ModHelper/btd6-game-data "$DUMP"
python3.10 scripts/parse_gamedata.py --dump "$DUMP" --validate-anchors || exit 1
python3.10 scripts/parse_gamedata.py --dump "$DUMP" --overlay          # safe refresh
python3.10 scripts/parse_gamedata.py --dump "$DUMP" --audit            # must stay clean
python3.10 scripts/btd6_gamedata_inventory.py --dump "$DUMP" --full-map \
    --out docs/btd6/btd6-dump-coverage-map.md
python3.10 scripts/btd6_decode_inventory_report.py --dump "$DUMP" \
    > docs/btd6/btd6-decode-inventory-v55.md                            # if dump SHA changed
```

## The gate (why "fetch everything" ≠ "commit everything")

- **`--overlay` is auto-safe**: it only writes uniquely-keyed numbers (cost, upgrade
  cost/xp by `(path,tier)`, tier-level range/footprint) and is name-frozen by
  `assert_names_preserved`. An automated job can run it and open a PR unattended.
- **`--all` (the full cutover) is NOT auto-safe yet**: it rewrites the committed
  stats to the game-native shape, which still needs the zone/buff/subtower tail +
  the name guard + ~25 value-pinned test updates (see decode-status). So the
  automation **stops at overlay + audit + the coverage/inventory docs** and leaves
  the cutover a human-reviewed step.

## Automation — GitHub Actions *(committed, dispatch-only)*

> **Committed 2026-06-09 (PR #633, Lane 5):** the real workflow is
> [`.github/workflows/btd6-data-refresh.yml`](../../.github/workflows/btd6-data-refresh.yml)
> — **the file wins over the historical sketch below.** Differences from the sketch:
> **no `schedule:`** (Q-0049 — cron was never approved; a new trigger needs a new owner
> ask), an opt-in default-false `regenerate_decode_inventory` input (decision 3 below),
> minimal `permissions:` + a `concurrency` queue, the audit report piped to the run
> Summary page, and `create-pull-request` SHA-pinned at v8.1.1. Run it from the GitHub
> **Actions** tab → *BTD6 Data Refresh (manual)* → *Run workflow*. A no-diff run opens
> no PR (the normal outcome between game patches). Prerequisite: repo Settings → Actions
> must allow workflows to create PRs; CI doesn't auto-run on the bot-opened PR (close &
> reopen it, or push to its branch).

Historical sketch (kept for context only — the committed file above is authoritative):

```yaml
# .github/workflows/btd6-data-refresh.yml  (PROPOSAL)
name: BTD6 data refresh
on:
  schedule: [{ cron: "0 6 * * 1" }]   # weekly, Monday 06:00 UTC
  workflow_dispatch: {}
jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.10" }
      - run: pip install -r requirements.txt
      - run: git clone --depth 1 https://github.com/Btd6ModHelper/btd6-game-data /tmp/btd6gd
      - run: python3.10 scripts/parse_gamedata.py --dump /tmp/btd6gd --validate-anchors
      - run: python3.10 scripts/parse_gamedata.py --dump /tmp/btd6gd --overlay
      - run: python3.10 scripts/parse_gamedata.py --dump /tmp/btd6gd --audit
      - run: python3.10 scripts/btd6_gamedata_inventory.py --dump /tmp/btd6gd --full-map --out docs/btd6/btd6-dump-coverage-map.md
      - uses: peter-evans/create-pull-request@v6
        with:
          branch: auto/btd6-data-refresh
          title: "BTD6 data refresh (auto)"
          body: "Automated overlay refresh + regenerated coverage map. Review the diff."
```

On a no-op patch the diff is empty and no PR opens. On a real patch the PR carries
the overlay delta + the regenerated coverage map (whose file-count fingerprint
flags new/removed content) for review.

## Open decisions (maintainer)

1. **Cadence/trigger.** ~~Weekly cron (simple) vs. **patch-detect**~~ — **DECIDED
   2026-06-09 (Q-0049, gate-lifting interview): manual `workflow_dispatch` only; no
   schedule of any kind.** A scheduled/cron variant would need a new owner ask.
2. **Where the 320 MB clone runs.** ~~GitHub Actions vs. the bot's
   `automation_scheduler`~~ — **RESOLVED by the committed workflow (#633): GitHub
   Actions**, into `/tmp` (temp storage, never committed). **ADR-001** keeps state out
   of the runtime, so the CI job was the better fit.
3. **Scope of the auto-commit.** ~~Overlay-only (recommended) vs. also regenerating
   the decode-inventory each run~~ — **RESOLVED in the committed workflow (#633) per
   this doc's own recommendation:** the default scope is overlay + coverage map; the
   decode-inventory roll-up is an **opt-in, default-false dispatch input**
   (`regenerate_decode_inventory`) for when the dump SHA moved.

## Status / next

- **Done (2026-06-08):** the coverage-map step (#6) — `--full-map` +
  [`btd6-dump-coverage-map.md`](btd6-dump-coverage-map.md), regenerable per pull.
- **Done (2026-06-09, PR #633 — Lane 5):** the **`workflow_dispatch`-only workflow**
  ([`btd6-data-refresh.yml`](../../.github/workflows/btd6-data-refresh.yml)). Verified
  against a live clone before commit: anchors OK, overlay 0-change no-op, audit
  0-SUSPECT, coverage map byte-identical. Same PR fixed a latent regeneration trap at
  the root: `btd6_decode_inventory_report.py` now emits the `Status:` badge that
  `check_docs.py --strict` requires (it had been hand-added to the committed artifact
  only, so any regeneration — workflow or the manual chain above — stripped it and
  would have reddened the refresh PR's doc-hygiene gate; pinned by test now).
- **Gated:** the full `--all` cutover (decode-status steps 1–5).
