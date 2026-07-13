# Generated web-data artifacts — the one merge-conflict recipe

> **Status:** `reference` — how to resolve merge conflicts on the committed generated
> artifacts (`dashboard/data/dashboard.json` + the botsite exports). One recipe, one
> helper script; attribute-level alternatives were tested and ruled out below. Source
> wins: `scripts/export_dashboard_data.py` (the producer),
> `scripts/resolve_generated_conflicts.py` (the resolver),
> `.github/workflows/dashboard-data-refresh.yml` (the churn source).

## The conflict class

The 2-hourly `dashboard-data-refresh.yml` workflow regenerates
`dashboard/data/dashboard.json` and lands it on `main` through an auto-merging PR
(`chore(dashboard): refresh generated data` — e.g. #2062, #2063, #2067). Meanwhile most
working branches *also* regenerate the artifacts as guard collateral (session cards feed the
Updates panel; env-var changes feed the env inventory). Result: every refresh merge on `main`
re-conflicts every open branch that touched the generated files — PR #2061 hit it **three
times in one night** (2026-07-12→13; branch merges `1cc99af`, `c3db76c`, `a1c95fb`).

The conflicted files are **pure generator output** — `scripts/export_dashboard_data.py` is
the single producer, nobody hand-edits them, and CI's freshness guard
(`scripts/check_generated_artifacts_fresh.py`) compares structure, not text. A text-level
merge of them is therefore meaningless; the only correct resolution is *regenerate from the
merged sources*.

Affected paths (the producer's outputs):

- `dashboard/data/dashboard.json`
- `botsite/data/site.json`
- `botsite/data/console.json`
- `botsite/site/data.js`

**Not** affected: the `*_data_contract.json` files — those are hand-versioned; a conflict
there is a real semantic conflict and must be merged for real.

## The recipe

Resolve **only right before landing** (resolving earlier just re-conflicts on the next
2-hour refresh). When your `git merge origin/main` stops on these files:

```
python3.10 scripts/resolve_generated_conflicts.py
```

It takes the incoming side for the generated paths (`git checkout --theirs -- …`; during a
rebase the sides invert and it uses `--ours`), re-runs `export_dashboard_data.py` against
the merged working tree (which already contains both sides' sources, so the regenerated
output is the true post-merge artifact), stages the result, and lists any remaining
non-generated conflicts for you to resolve normally. `--dry-run` previews.

By hand (identical semantics):

```
git checkout --theirs -- dashboard/data/dashboard.json botsite/data/site.json \
    botsite/data/console.json botsite/site/data.js
python3.10 scripts/export_dashboard_data.py
git add dashboard/data/dashboard.json botsite/data/site.json \
    botsite/data/console.json botsite/site/data.js
```

(Only conflicted paths need the `checkout --theirs`, but stage all four after the regen —
one producer run refreshes them together, and committing them together keeps the artifacts
mutually consistent on one build sha. Never `git add` the `*_data_contract.json` files as
part of this recipe.)

## Why not git attributes? (tested 2026-07-13, real data)

Three-way test corpus: `dashboard.json` at `df5ee69` (base), `a1c95fb~1` (branch regen),
`cce250f` (refresh commit). A normal `git merge-file` exits 4 — the real conflict class
reproduced.

- **`merge=union` — ruled out.** `git merge-file --union` exits 0 but **corrupts the
  JSON**: both sides' lines are kept, yielding duplicate `meta.generated_at`/`build` keys
  and unbalanced braces — `json.load` fails (`Expecting ',' delimiter: line 8 column 5`).
  Union is right for the append-only ledgers already in `.gitattributes`; it is wrong for
  any structured JSON. Do not "fix" this class by extending union to these files.
- **Custom merge driver — ruled out.** A driver only runs where every clone has configured
  `git config merge.<name>.driver …`; fresh agent clones never have it, and with the
  attribute set but no driver configured git silently falls back to the normal conflicting
  merge (verified in a scratch repo). GitHub's server-side merge/conflict machinery never
  runs custom drivers, so the PR page would still show the conflict regardless.
- **`-merge` / binary attribute — ruled out.** It just forces the conflict earlier without
  resolving anything; the recipe above is still needed, so the attribute adds nothing.

What *did* ship in `.gitattributes`: `linguist-generated=true` for the four paths, so
GitHub collapses their churn in PR diffs (cosmetic only — same treatment as
`disbot/data/btd6/**`).

## Future work (flagged, not this slice)

The root fix is for refresh commits to stop touching tracked paths at all (serve the feed
from a service/artifact instead of a committed JSON). That is a website-architecture
change (`dashboard/` is a decoupled Railway service that can only serve committed files) —
too invasive for a tooling slice; route it via `docs/ideas/` if it earns a lane.
