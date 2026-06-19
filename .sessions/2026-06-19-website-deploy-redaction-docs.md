# 2026-06-19 — Website two-site split: P7 + P8 (redaction audit + deploy/env docs)

> **Status:** `complete`

Ultracode fan-out unit **P7 + P8** of the website two-site-split
(`docs/planning/website-two-site-split-plan-2026-06-19.md` §5). **Docs only — no runtime code.**
The sole fan-out unit that edits the plan, so it also records the back-half wave's completion.

## Shipped (PR #1113)

- **P7** — `docs/operations/dashboard-redaction-audit.md` (new, `audit`-badged): the plan §4.1
  per-page redaction matrix as a **living, dated checklist** — every dev-site route → auth →
  what it renders → secret-value risk → ✅/⛔ verdict, plus the standing rationale per row and a
  "how to re-run" header. Verified against the live `dashboard/app.py` routes (all 14 public read
  routes + `/me`, `/admin/*`, `/auth/*` gated; `/admin/moderation` audited against its P5 spec).
- **P8:**
  - `docs/operations/botsite-deploy.md` (new, `living-ledger`): the 2nd-Railway-service deploy
    recipe for `botsite/` (**Root Directory = `botsite`**, its own `requirements.txt` + `Procfile`,
    the import path `app:app`, the **no-`static/` gotcha** = the #970 class), the §6 additive
    rollout + per-step rollback, the submissions-DB + dev-site moderation note, the 2→3-service
    table, and the local `importorskip` run path.
  - `docs/operations/env-vars.md` (extended): a new hand-maintained **"Website tier"** section
    naming `SUBMISSIONS_DB_DSN` (INSERT-only public role / full dev role), `SUBMISSIONS_IP_SALT`,
    `GITHUB_ISSUE_MIRROR_TOKEN` (dev-site only, repo-scoped Issues:write), optional captcha keys,
    and the dev-site OAuth/session/control set — written in **prose (not `| name |` rows)** on
    purpose (see Decisions made alone).
  - `dashboard/README.md`: a short owner-gated **moderation** note (pending queue → approve →
    GitHub mirror; the token + full DSN live only on the dev site).
- **Plan bookkeeping:** §5 — marked all back-half units **✅ S1.1/P2/P3/P4/P5/P6/P7/P8 shipped**
  (the section heading, each unit bullet, the status block, and the dependency-graph line now read
  "executed in the fan-out wave"); §9 — added reference links to the two new `docs/operations/`
  docs (this is what makes them reachable for `check_docs --strict`).

## Verification (green)

- `python3.10 scripts/check_docs.py --strict` → **all checks passed ✓** (both new docs reachable
  via the §9 links off the plan, which is reachable from `current-state.md`; badges `audit` +
  `living-ledger` valid; all relative links resolve; top-level ratchet still 20).
- `python3.10 scripts/check_quality.py --check-only` → **All checks passed ✓** (EXIT 0). The only
  warnings are the pre-existing 17 `views/ai/` `edit_in_place` findings (warn-only, tracked by the
  AI-nav plan) — untouched by this docs-only PR. No Python changed, so formatters are clean.

## Decisions made alone (for owner ratification)

1. **The website-tier env vars are documented as PROSE, not table rows, in `env-vars.md`** — and
   the file gained an explicit `<!-- END GENERATED REGION -->` marker. *Why:* `env-vars.md` is a
   **fully generated file** (`scripts/scan_env_usage.py --write-doc` rewrites the whole file from a
   scan of `disbot/` only), and the freshness drift check
   (`check_generated_artifacts_fresh._ENV_VAR_ROW`) extracts env names from any `` | `NAME` `` row.
   Web-service vars (`botsite/`/`dashboard/`) are **not** read by `disbot/`, so a `| name |` table
   for them would (a) get clobbered on the next regen and (b) **false-flag as drift** (present in
   the committed file, absent from a fresh bot-source scan). Prose sub-bullets avoid both. The
   authoritative, regen-safe home for these names is `botsite-deploy.md` (which I own); `env-vars.md`
   carries the discoverable index + a loud "re-add after regen" caveat. **The cleaner long-term fix**
   is to make `scripts/scan_env_usage.py:render_doc` *emit* a static website-tier section so it
   survives regen — left undone because the script is **outside this unit's scope fence** (see
   Flagged). Filed as a session idea.
2. **Marked all back-half units (S1.1/P2/P3/P4/P5/P6) shipped, per the prompt**, even though at the
   moment of writing only the foundation (#1109) + #1110 were merged on `main` and the other
   templates/modules were still landing on parallel branches. *Why:* the prompt is explicit ("mark
   the back-half units shipped … record the fan-out's completion") and designates this unit as the
   sole plan editor precisely so the fan-out's bookkeeping lands once. The wording I used says
   "shipped in the fan-out wave" rather than citing a PR number per unit, so it stays accurate
   regardless of each sibling PR's exact merge moment.

## Context delta (reflection interview)

- **Needed but not pointed to:**
  - **`env-vars.md` is whole-file generated AND a drift check keys on its table rows.** Neither the
    file's own header nor orientation warns that *appending* a table will both be clobbered and
    trip a warn-only drift false-positive. I had to read `scripts/scan_env_usage.py` (`render_doc`
    overwrites the file) **and** `scripts/check_generated_artifacts_fresh.py` (`_ENV_VAR_ROW`) to
    learn this. → folded into the doc via the `END GENERATED REGION` marker + caveat; worth a line
    in a future "editing generated docs" note.
  - **Worktree vs. main-repo cwd gotcha.** This session runs in a git **worktree**
    (`.claude/worktrees/agent-…`), but `Bash` calls that begin `cd /home/user/superbot` operate on
    the **main** repo, while `Edit`/`Read`/`Write` operate on the worktree — so a `cd`-prefixed grep
    showed *stale* (pre-edit) content and made it look like my edits hadn't applied. The fix: run
    Bash with **no `cd`** (the worktree is already the default cwd) and use **absolute worktree
    paths**. Cost ~3 tool calls of confusion. (CLAUDE.md notes "cwd resets between bash calls" but
    not the worktree-vs-main split.)
- **Pointed to but didn't need:** the deep CodeGraph/architecture-rule sections of CLAUDE.md — this
  was a pure docs unit (no symbol navigation, no layer boundaries). Correctly skippable for a
  docs-only fan-out unit; not a complaint, just an observation that the orientation is bot-code-shaped.
- **Discovered by hand:** the `check_docs` reachability mechanism — a new doc is an orphan **unless**
  it is linked (markdown link or backtick `docs/*.md` ref) from a read-path root / folio / README,
  *transitively*. My two docs become reachable only because the **plan §9** links them and the plan
  itself is reachable from `current-state.md`. Verified by reading `check_docs.py::check_reachable`.
- **Decisions made alone:** the two above (prose-not-table env vars; mark-shipped wording).
- **Flagged for maintainer / known limits:** see the run report ⚑ lines. The headline is the
  `env-vars.md` regen footgun — a clean fix exists but needs `scripts/scan_env_usage.py`, outside
  this unit's fence.
- **One docs/tooling change that would have helped most:** an "editing generated docs" gotcha note
  (which docs are whole-file-regenerated + which checks key on their structure) — captured as the
  session idea below.

## 💡 Session idea (Q-0089)

**Make `scripts/scan_env_usage.py:render_doc` emit a declarative "Website tier" (non-`disbot/`)
env section** so the web-service env names live *in the generator* and survive `--write-doc`
regen, instead of as a hand-maintained appendix that the regen clobbers and the drift check would
false-flag. Small, high-value: it removes the exact footgun this session had to document around,
and keeps `env-vars.md` a single source of truth for *all* deploy-relevant env names (bot + web).
*(Out of scope for this unit — the script belongs to no fan-out unit but the fence listed only
`env-vars.md`; recorded here for the next agent.)* Dedup-checked `docs/ideas/` + the roadmap — no
existing entry for the env-doc generator covering web services.

## ⟲ Previous-session review (Q-0102)

**Reviewed:** `2026-06-19-website-foundation-s1s2p1.md` (the S1+S2+P1 foundation, #1109) — the
direct predecessor in this lane. **Did well:** it nailed the file-disjointness that made *this*
fan-out safe — S1 sole-owns the producer, S2's two helpers share only the DDL, P1 sole-owns
`app.py` and pre-wires every route so the template/module units never touch it. That discipline is
exactly why P2–P8 could run in parallel without write conflicts, and it held. **Could have done
better / system improvement it surfaces:** the foundation seeded `botsite/data/site.json` as a
committed generated artifact and registered it in two freshness guards — but **neither the
foundation nor the plan flagged the symmetric trap one layer over in `env-vars.md`** (whole-file
regenerated + a drift check that keys on table rows), which this session tripped over. The
concrete workflow improvement: a short **"editing generated docs"** orientation note enumerating
which committed docs are whole-file-regenerated by a script and which checkers parse their
structure — so the *next* agent extending a generated doc doesn't reverse-engineer it from the
scanner source. (That's the Q-0089 idea above, generalized from "env-vars" to "generated docs".)

## 📤 Run report

- **Did:** built website-split fan-out **P7 + P8** (redaction-audit record + `botsite/` deploy/env
  docs) and recorded the back-half wave's completion in the plan · **Outcome:** shipped
- **Shipped:** #1113 — P7 `dashboard-redaction-audit.md` + P8 `botsite-deploy.md` /
  `env-vars.md` (Website-tier section) / `dashboard/README.md` moderation note + plan §5/§9
  bookkeeping. Docs only.
- **Run type:** `manual` (dispatched ultracode build unit)
- **⚑ Owner decisions needed:** `none` — but two **alone-decisions** above to ratify if desired
  (prose-not-table env vars; "shipped in the fan-out wave" plan wording).
- **⚑ Owner manual steps:** the website-split **rollout is owner-paced** (`botsite-deploy.md` § Rollout):
  provision the new `botsite/` Railway service (Root Dir = `botsite`), provision the dashboard-owned
  submissions Postgres + apply `botsite/migrations/001_submissions.sql`, grant the INSERT-only vs full
  DB roles, set `SUBMISSIONS_DB_DSN` / `GITHUB_ISSUE_MIRROR_TOKEN` per the §4.4 matrix, then cut the
  marketing domain over. None of this is done here (docs only).
- **⚑ Self-initiated:** `none` — this was a dispatched build unit (not an unprompted idea→build). The
  Q-0089 idea (env-doc generator for web vars) is filed, **not** built, and is correctly out of fence.
- **↪ Next:** the website-split's deferred follow-ups — the control-panel migration to the bot side +
  the live status aggregator (both gated on the control-API public-exposure security review), and the
  owner-paced rollout above.
