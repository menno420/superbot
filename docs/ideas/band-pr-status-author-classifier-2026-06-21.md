# Idea — `band_pr_status --themes`: draft grouped-entry skeleton from touched paths

> **Status:** `ideas` · **Lane:** workflow tooling (reconciliation routine) · **Size:** S · **Risk:** low
> **Raised:** 2026-06-21 (band-#1260 Q-0107 pass, Q-0089 session idea)

## The pain

Every reconciliation pass hand-themes the band's merged PRs into grouped Recently-shipped entries.
The expensive half is the **opaque merge-commit PRs**: many `claude/*` branches (peaceful-mayer,
ecstatic-babbage, funny-franklin, …) squash- or merge-commit with a title like
`Merge pull request #1251 from menno420/claude/peaceful-mayer-rgc20t` — which says *nothing* about
what shipped. This pass had to run `git show --stat <merge-sha>` for **eleven** such PRs to read the
file fan-out and infer the theme (e.g. `disbot/services/btd6_upgrade_detail_service.py` +
`scripts/parse_gamedata.py` → "BTD6 buff-uptime data"). `band_pr_status.py` (#1181) already classifies
**merged / closed / open**, but not **theme**.

## The idea

A small `--themes` mode (or a sibling script) that, for each merged PR in the band, reads the merge/
squash commit's touched files and groups by **top-level path prefix** (`disbot/cogs/`,
`disbot/services/btd6_*`, `disbot/views/roles/`, `docs/planning/`, `dashboard/`, `botsite/`) plus the
squash-title verb, then emits a **draft grouped-entry skeleton** — one bullet per inferred theme with the
PR numbers and the dominant path — that the pass *edits* rather than reconstructs cold. It is a starting
point, not the final prose: the agent still writes the human summary, but no longer reverse-engineers
*what each opaque merge-commit PR did* by hand.

## Why it's worth having

The reconciliation routine is mechanising itself one chore at a time — the **trim actuator** (#1181,
band-#1170 idea) and the **callout prune** (band-#1230, done in-band) are both solved; band-PR **theming**
is the next-most-manual chore and the natural next lever. Stdlib, read-only, disposable (Q-0105).

→ relates `scripts/band_pr_status.py` · `scripts/trim_recently_shipped.py` · the reconciliation routine
STEP 2.
