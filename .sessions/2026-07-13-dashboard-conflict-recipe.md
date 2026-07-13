# 2026-07-13 — Durable mitigation for the generated-artifact merge-conflict class

> **Status:** `complete`
> **Branch:** `claude/dashboard-conflict-recipe` · **PR:** #2072
> **Venue:** remote container (worker session, orchestrated). **📊 Model:** Fable 5 (Claude 5 family).
> **Scope:** tooling/gitattributes/docs ONLY — zero runtime behavior change (nothing under
> `disbot/` touched; the new script lives in `scripts/` and is never imported by the bot).

## Arc

The 2-hourly `dashboard-data-refresh.yml` workflow lands `chore(dashboard): refresh generated
data` merges on `main` (e.g. #2062, #2063, #2067), and every open branch that also regenerated
`dashboard/data/dashboard.json` (+ botsite exports) — which guard collateral makes routine —
re-conflicts on those files at every refresh merge. PR #2061 hit this 3× overnight 2026-07-12→13
(branch merges `1cc99af`, `c3db76c`, `a1c95fb` — the tip is literally "Merge origin/main into
claude/mineverse-flag-2 (regenerate dashboard data)"). The known-working manual recipe was
take-theirs + regenerate, re-derived by hand each time. This session codified it.

## Shipped (PR #2072)

- **`scripts/resolve_generated_conflicts.py`** — stdlib-only resolver: during a conflicted
  merge/rebase, take the incoming side for the four producer outputs (`--theirs` in a merge,
  `--ours` in a rebase where the sides invert), re-run `scripts/export_dashboard_data.py`
  against the merged tree (its sources contain both sides, so the regen is the true post-merge
  artifact), stage all four outputs together (one build sha), report remaining non-generated
  conflicts. Contract JSONs deliberately excluded (hand-versioned = real conflicts).
- **`docs/operations/generated-data-merge-recipe.md`** — the recipe + the empirical evidence
  ruling out the attribute-level alternatives (below); linked from `ci-what-runs-where.md`
  row 13.
- **`.gitattributes`** — `linguist-generated=true` for the four paths (GitHub diff collapsing,
  same treatment as `disbot/data/btd6/**`) + a do-NOT-union warning comment.

## Mechanism — evaluated empirically, decided-and-flagged

Three-way corpus: real `dashboard.json` at `df5ee69` (base) / `a1c95fb~1` (branch regen) /
`cce250f` (refresh). Normal `git merge-file` exits 4 — the class reproduced.

- **`merge=union` — ruled out:** exits 0 but corrupts (both sides' lines kept → duplicate
  `meta.generated_at`/`build` keys, unbalanced braces; `json.load` fails
  `Expecting ',' delimiter: line 8 column 5`). Right for the append-only ledgers already in
  `.gitattributes` (#1003); wrong for structured JSON.
- **Custom merge driver — ruled out:** needs per-clone `git config merge.<name>.driver`
  (fresh agent clones never have it; with the attribute set but no driver configured, git
  silently falls back to the normal conflicting merge — verified in a scratch repo), and
  GitHub's server-side merges never run custom drivers.
- **`-merge`/binary — ruled out:** only forces the conflict; resolves nothing.
- **Chosen:** codify take-theirs+regenerate (script + doc). Root fix (refresh stops touching
  tracked paths) flagged as future work in the recipe doc — too invasive for this slice.

**End-to-end verification:** scratch worktree, two branches with divergent `dashboard.json`
regens → `git merge` → `CONFLICT (content)` → resolver → exit 0, conflict cleared, valid JSON
with fresh `meta.build.commit` from the merged tree, artifacts staged, "No other conflicts".
CI mirror: `python3.10 scripts/check_quality.py --full` → **All checks passed ✓** (13884
passed, 49 skipped, 2 xfailed; mypy clean over 881 files).

## Decisions made alone

- Resolver stages **all four** producer outputs after regen (not just the conflicted ones) so
  the artifacts stay mutually consistent on one build sha.
- Telemetry `task_class` written as `tooling` — the slice is dev tooling + docs; none of the 8
  Q-0248 classes fits exactly (nearest: docs-only, which would understate the script). Off-list
  precedent exists in the feed (`ci-fix`).

## Context delta

- **Needed but not pointed to:** the four generated-output paths live only as constants inside
  `scripts/export_dashboard_data.py`; nothing routed from "conflict on dashboard.json" to a
  recipe. Fixed: `ci-what-runs-where.md` row 13 now routes to the recipe doc, and the
  `.gitattributes` warning routes anyone about to "fix" it with union.
- **Discovered by hand:** with a merge attribute set but no driver configured, git silently
  does the normal conflicting merge — no warning. Recorded in the recipe doc.
- **Pointed to but didn't need:** none notable.

## 🛠 Friction → guard

Friction: local `python3.10 -m mypy disbot/` false-red ("discord.ext has no attribute
commands") from a **stale .mypy_cache** after installing requirements into a warm container;
`rm -rf .mypy_cache` cleared it. Guard shipped: none (a cache-wipe pre-step in check_quality
would slow every run; noting here + the run report is proportionate — promote to a
`--fresh-cache` flag idea if it recurs).

## 💡 Session idea

**Teach `dashboard-data-refresh.yml` to skip when only volatile keys changed.** The workflow
diffs the whole `dashboard.json`; if the only delta is `meta.build`/counts-neutral churn it
still opens a refresh PR, maximizing the conflict window this session mitigated. A
structural-diff gate (reusing `check_dashboard_data.check_structural_drift`) would cut refresh
merges — fewer conflicts at the source. (Deduped: `docs/ideas/` has nothing on refresh-PR
frequency.)

## ⟲ Previous-session review

Reviewed `2026-07-13-mineverse-flag-2.md` (#2061): excellent security round (6 CodeQL alerts
fixed same-session, none dismissed) and honest draft-hold discipline. Gap this session closes:
it absorbed 3 refresh-merge conflicts as manual toil without converting the friction into a
guard (Q-0194) — understandable mid-feature, but exactly the class that should have produced
this recipe a night earlier. System improvement: this card + recipe are that conversion.

## Documentation audit

New doc reachable (`ci-what-runs-where.md` row 13 links it); no owner decisions taken that
need a router Q (tooling + docs, reversible, decide-and-flag); ledger untouched (no merged-PR
entry to add — auto-merge lands #2072 after this flip; the reconciliation routine records it).

## ♻️ Backlog grooming

Config/tooling session; the 💡 idea above is the grooming contribution (routes the conflict
class toward its source-side fix).

## 📤 Run report

- **Did:** codified take-theirs+regenerate for generated web-data merge conflicts (script +
  recipe doc + gitattributes), union/custom-driver ruled out empirically · **Outcome:** shipped
- **Shipped:** #2072 — resolver script + recipe + linguist-generated marks (tooling/docs only,
  zero runtime)
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (dispatched task; the refresh-skip idea filed above, not built)
- **↪ Next:** if refresh conflicts persist, build the structural-diff skip in
  `dashboard-data-refresh.yml` (this card's 💡 idea)
