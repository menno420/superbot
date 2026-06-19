# Web-tier + PR-machinery centralization — proposal (2026-06-19)

> **Status:** `plan` — a proposal, owner-directed by the "if multiple things take care of two sides of one
> problem, find a better centralized way — correctness first" mandate (2026-06-19). Nothing here is
> implemented yet; each item says *why it's deferred to a focused PR* rather than rushed into a bundle,
> because the things being centralized are **working CI/merge plumbing** and correctness comes first.

## 1. Web CI: `dashboard-ci.yml` + `botsite-ci.yml` → one `web-ci.yml` matrix

**The two sides.** Two near-identical workflows test the two web services: `dashboard-ci.yml` (installs
`requirements.txt` + `dashboard/requirements.txt`, runs `mypy dashboard/` + `pytest tests/unit/dashboard`)
and `botsite-ci.yml` (the same for `botsite/`). They exist because the main `code-quality.yml` installs only
the bot's `requirements.txt`, so each web service's tests `importorskip` and skip, and neither is
type-checked. They are genuine twins — the textbook "two sides of one problem (test the web tier)."

**The centralized form.** One `web-ci.yml` with a **matrix over the services**:

```yaml
strategy:
  matrix:
    service:
      - { name: dashboard, reqs: dashboard/requirements.txt, tests: tests/unit/dashboard }
      - { name: botsite,   reqs: botsite/requirements.txt,   tests: tests/unit/botsite }
# install: requirements.txt + ${{ matrix.service.reqs }}
# mypy ${{ matrix.service.name }}/  ·  pytest ${{ matrix.service.tests }}
```

`paths:` becomes the union (`dashboard/**`, `botsite/**`, both test dirs, the workflow file). One file, one
place to add the next web service (a third matrix row), no copy-paste drift.

**Why deferred (not done in the foundation-follow-through PR).** Replacing `dashboard-ci.yml` — a *working*
required-ish check — is higher blast-radius than *adding* `botsite-ci.yml`. Correctness-first says: ship the
additive `botsite-ci.yml` now (gets the bot site tested immediately, unblocks the fan-out's CI), and do the
matrix unification as its **own focused PR** where both matrix legs are verified green before the two
per-service files are deleted. **Acceptance for that PR:** both `dashboard` and `botsite` matrix jobs run +
pass on a PR touching each service; then delete `dashboard-ci.yml` + `botsite-ci.yml`.

## 2. PR-sync machinery: `pr-auto-update.yml` + `pr-conflict-guard.yml`

**The two sides.** Both react to *"`main` moved → an open PR is now out of sync"* (both trigger on
`push: main` and enumerate open PRs): `pr-auto-update` updates **BEHIND** `claude/*` PRs; `pr-conflict-guard`
posts a red status on **DIRTY** ones. The states are mutually exclusive per PR, so conceptually it's one
sweep split in two.

**Honest assessment.** They are *defensibly* separate: different actions (mutate the branch vs post a commit
status), different tokens/permissions (`pr-auto-update` needs `contents:write` + `ROUTINE_PAT` to attribute
the merge to a user so `reconciliation-trigger` keeps firing; `pr-conflict-guard` needs `statuses:write` +
`GITHUB_TOKEN`, because `ROUTINE_PAT` lacks status-write — the #966 lesson). Merging them into one job is
possible (a job can hold both permissions and pick the right token per step) but adds complexity. So the
*biggest, lowest-risk* centralization is **not** merging the workflows — it's the duplication *inside* them:

- **The eligibility/carve-out predicate is duplicated.** "Is this PR auto-managed?" = `claude/*` head **and
  not** labelled `needs-hermes-review` / `do-not-automerge`. That rule is written out in **both**
  `pr-auto-update.yml` and `auto-merge-enabler.yml` (and implied in the conflict guard). If a carve-out label
  changes, three files must change in lockstep. **Recommendation (do first, low-risk):** extract it to one
  source of truth — a tiny `scripts/pr_auto_managed.py` (or a documented shared `jq` filter snippet) that all
  three workflows call. One place defines "auto-managed."
- **Optional follow-up (medium-risk):** a single `push: main` **"PR-sync keeper"** that, per open PR, does
  *update-if-BEHIND / red-if-DIRTY / clear-else* in one enumeration. If pursued, it **must preserve the
  #1106 fix** (poll through GitHub's async-`UNKNOWN` mergeability window before deciding) — that bug is
  exactly the kind a careless merge would reintroduce.

## 3. The broader pattern (note, don't force)

Several workflows touch "PR lifecycle / mergeability" — `auto-merge-enabler`, `pr-auto-update`,
`pr-conflict-guard`, and the `code-quality` born-red session-gate. It's tempting to consolidate them, but
each is currently single-purpose and working. **Centralize where there is genuine duplication (the
eligibility predicate, the open-PR enumeration) — not for its own sake.** The correctness-first rule is:
a unified workflow must be *demonstrably* equivalent (same triggers, tokens, carve-outs, and the #1106
race fix) before it replaces working plumbing.

## Recommended order

1. **Now (shipped alongside this doc):** additive `botsite-ci.yml` — bot-site tests + `mypy botsite/` run.
2. **Focused PR A:** extract the auto-managed-PR predicate to one source of truth (#2 first bullet).
3. **Focused PR B:** `web-ci.yml` matrix replacing the two per-service CI files (#1), both legs verified.
4. **Optional PR C:** the unified PR-sync keeper (#2 second bullet), preserving the #1106 race fix.

## Builds on / references

`.github/workflows/{dashboard-ci,botsite-ci,pr-auto-update,pr-conflict-guard,auto-merge-enabler}.yml` ·
the #1106 conflict-guard `UNKNOWN`-race fix · `docs/planning/website-two-site-split-plan-2026-06-19.md` (the
split this web-tier work serves).
