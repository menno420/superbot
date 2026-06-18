# 2026-06-16 — dashboard `/status` page (live status & health surface)

> **Status:** `complete` — shipped; small/contained → auto-merges on green (Q-0113).

## Arc

Scheduled DISPATCH run, empty work order → advance the next plan slice. The buildable `ready`
decade-queue is consumed and both open PRs (#929, #941) are `needs-hermes-review` carve-outs (not my
merge authority). The live active lane is the **developer dashboard** (owner explicitly wants to keep
building it). Per the dashboard plan's "⭐ Next session — start here", the remaining **read-only**
Q-0156 surfaces were *live status/health* + *games & economy*; `/games` shipped (#983), so this run
shipped the last one: **status/health**.

## Shipped (this PR — #985)

New **`/status`** dashboard page — same low-risk shape as every other page (separate Railway service,
never imports `disbot/`, reads committed `dashboard.json`, no migration, no external egress):

- **Deployed build banner** — `meta.build` (new): git-derived commit / subject / date / branch the
  data was generated from. Answers the owner's headline *"live status"* question ("is my latest merge
  live?") — the dashboard auto-redeploys on merge + serves committed data, so the recorded commit is
  the deployed snapshot's version. `_git_meta()` is guarded → `{}` on any failure (git absent in a
  build image must degrade to "unavailable", never crash the export).
- **Health grid** — the 11 inventory counts as cards linking to their detail pages.
- **Bug health** — open vs fixed from `bugs[].status` (amber-flagged list when any are open; green
  "all resolved" otherwise).
- **Access tier distribution** — visible subsystems per permission tier.
- Files: `scripts/export_dashboard_data.py` (+`_git_meta`/`meta.build`) · `dashboard/app.py`
  (`/status`) · `dashboard/templates/status.html` (new) · `base.html` nav · regenerated
  `dashboard/data/dashboard.json` · `tests/unit/dashboard/test_app.py` (+`/status` smoke + a
  dedicated assertion) · `tests/unit/scripts/test_export_dashboard_data.py` (+`meta.build` test) ·
  dashboard plan + current-state de-staled.

**Verified:** `check_quality --full` GREEN (10211 passed, 37 skipped) — incl. the 19 app smoke tests
run for real after a local `pip install fastapi httpx jinja2`; `check_architecture --mode strict` 0
errors (only pre-existing `views/xp` known warnings). Regenerated `dashboard.json` carries the new
`meta.build` block; the regeneration also picked up one stale idea count (72→73).

## Context delta

- **Needed but not pointed to:** nothing new — the dashboard plan's "⭐ Next session — start here"
  routed this cleanly (data shape, "regenerate + commit after changing sources", the `static/`
  gotcha). That section is doing its job as the lane's entry point.
- **Discovered by hand:** `dashboard.json` is committed and regenerated **in-session**, so
  `meta.generated_at` / the new `meta.build` record the commit *at regeneration time* (the parent of
  the commit that ships the JSON), not Railway deploy time. Good enough as a "deployed version" proxy
  since the JSON ships in the same merge — documented in the `_git_meta` docstring + the page copy.
- **Decision made alone:** put the build banner behind a guarded git call returning `{}` on failure
  (rather than a hard dependency or a Railway-env read), so the export stays pure-stdlib and the page
  degrades to "build info unavailable". Low-risk, reversible.
- **Flagged:** the `meta.build` commit names the JSON's *parent* commit, never its own (chicken-and-egg
  — the JSON is committed inside the commit it would name). The page copy says "the version this page
  is rendering"; acceptable, but if the owner wants the exact deployed SHA, Railway's
  `RAILWAY_GIT_COMMIT_SHA` env at runtime would be the precise source (a future enhancement, needs the
  app to read env at request time).

## 💡 Session idea

**A `/status` "is my latest merge live?" check via Railway's runtime git env.** Today the build banner
shows the commit the *data* was generated from (the JSON's parent). Railway injects
`RAILWAY_GIT_COMMIT_SHA` into the running service at deploy time — the dashboard app could read it at
request time and show *both* "data built from `<sha>`" and "**service running** `<sha>`", turning the
status page into a genuine deploy-freshness check (green when they match, "redeploy pending" when the
service SHA is behind). Small, read-only, no new dep. Dedup-checked `docs/ideas/` + the dashboard plan
roadmap — not already captured. Worth having because it closes the one honesty gap in this PR's build
banner.

## ⟲ Previous-session review

The previous run (`2026-06-16-conflict-guard-noise-refine`) did the right thing well: it took an
owner-flagged noise problem, chose the scope via `AskUserQuestion`, and *verified the bash logic with
a 6-case `gh` stub before pushing* — exactly the discipline a workflow-YAML change needs (those don't
run under the pytest mirror). One genuine miss: it left the change "UNVERIFIED against a real DIRTY PR
end-to-end" with no follow-up mechanism — the kind of thing that quietly never gets confirmed.
**System improvement it surfaces:** the run report's `↪ Next` line ("watch the first real
behind/conflict case") is a real pending verification, but nothing *carries* it forward — it lives
only in that session's log. The `📤 Run report` footer could grow a lightweight `⏳ Pending
verification` line that Hermes rolls forward across runs until ticked, so "verify in prod when the
case arises" doesn't evaporate. (Captured as a small workflow note, not built this run — it's a
process tweak, not in my dispatched scope.)

## 📤 Run report

- **Did:** shipped the `/status` dashboard page (deployed-build banner + inventory + bug/access
  health), the last Q-0156 read-only surface · **Outcome:** PR #985, auto-merges on green
- **Shipped:** #985 — `/status` route + `meta.build` git context + template + nav + tests + docs
- **⚑ Owner decisions needed:** `none` for this slice. (Standing: the dashboard's next lane — the
  Q-0156 live help/panel editor — needs the owner's auth choice (Discord OAuth) before build; Phase 2
  needs the auth-method + DB decision.)
- **⚑ Owner manual steps:** `none` (Railway auto-redeploys `/status` on merge to `main`).
- **↪ Next:** dashboard read-only lane is consumed — next buildable work is a **PLAN-FIRST** slice
  (AI §7 next workflow family · Hermes bug-triage `gh issue create` Q-0121) or owning the live-editor
  design (Q-0156, owner-auth-gated). Sharpened in current-state ▶ NEXT.
- **⏳ Pending verification:** confirm `/status` renders on the live Railway service after this merges
  (the build banner against the real deployed SHA).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs opened this session | 1 (#985, auto-merges on green) |
| CI-red rounds | 1 (the intentional born-red session gate; 1 ruff COM812 fixed pre-merge) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (the runtime-SHA deploy-freshness check) |
| Ideas groomed | 0 |
