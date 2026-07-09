# Websites Project — kickoff (Custom Instructions + startup prompt, 2026-07-09)

> **Status:** `plan` — paste-in Custom Instructions + startup prompt for a **third**,
> separate Claude Code Project (distinct from the rebuild Project and from
> `superbot`'s own sessions). Target repo: **`menno420/websites`** (owner-created
> 2026-07-08, currently empty).
> **Provenance:** owner directive 2026-07-09, refined through the directing session's
> question panel + follow-up conversation (see
> [`rebuild-direction-handoff-2026-07-08.md`](rebuild-direction-handoff-2026-07-08.md)
> for that session's role).
> **Supersedes:** [`rebuild-status-site-project-kickoff-2026-07-08.md`](rebuild-status-site-project-kickoff-2026-07-08.md)
> (rebadged historical) — that doc scoped a narrower single-site test; the owner
> subsequently decided the target repo should be the **permanent consolidated home
> for all websites**, not a one-off.

## What this Project is — a sibling rebuild track, not a new one-off site

Same relationship `superbot-next` has to `superbot`: **`websites` is to the two
existing sites (`dashboard/`, `botsite/`, both living inside `superbot`) what
`superbot-next` is to the bot** — same substrate-kit foundation, same philosophy
(keep the ideas and functionality, rebuild the implementation), applied to the web
properties instead of the bot. The existing sites keep running untouched on the
production Railway project until their replacements are actually ready — nothing
about this Project touches live infrastructure other than its own new Railway
project.

## Sequence — three steps, the third explicitly deferred

1. **Adopt substrate-kit** into `menno420/websites` — identical procedure to
   `superbot-next`'s step 1: `python3 dist/bootstrap.py adopt` from
   `menno420/substrate-kit`, fresh-from-kit, never a copy of `superbot`. Doc
   skeletons, decision ledger, orientation/namespace/seam checkers, staged hooks —
   same artifact set `superbot-next` got.
2. **Build the control-plane / oversight site** — the genuinely new deliverable,
   and the first thing to actually ship. Two halves, from the owner's own framing:
   - **Readiness board**: per-repo (`superbot`, `superbot-next`, `substrate-kit`,
     and `websites` itself once it has its own settings) — is the ruleset actually
     configured? Are the required checks correct AND currently green (not just "a
     workflow exists")? Is CODEOWNERS present/enforced? Are secrets present? Is
     auto-merge armed? **Data source: `superbot`'s
     [`docs/operations/repo-settings-state.md`](../operations/repo-settings-state.md)**
     — this site is that ledger's own planned "Phase 3" (see
     [`per-repo-settings-state-ledger-2026-07-08.md`](per-repo-settings-state-ledger-2026-07-08.md)),
     generalized across repos instead of reinvented. Read that ledger's current
     rows as the seed data model; building `scripts/generate_repo_settings_state.py`
     (that plan's Phase 2, auto-generating the ledger from the API) is in scope here
     too if it makes the board real data instead of a static snapshot — your call
     how to sequence it.
   - **Journal browser**: session logs (`.sessions/`), decision ledgers
     (`docs/decisions.md` in each repo), question-routers, PR history — across all
     repos, linked straight into GitHub, not narrated/summarized. The point is the
     owner can look and know, without asking an agent to go fetch and summarize
     GitHub state every time.
   - Why this can't just be added to `dashboard/` or `botsite/`: both are scoped to
     `superbot` alone and predate the multi-repo rebuild world; neither has any
     notion of cross-repo state, and both serve different audiences (old-bot
     reference catalogue; public-ish activity feed) than an owner-only control
     plane. Full reasoning was worked through with the owner in the directing
     session's chat (2026-07-08/09) if you want the complete thread — not
     duplicated here, this doc states the conclusion.
   - Gate access behind something simple (a shared-secret/password gate is
     enough — this doesn't need real auth) since it shows internal
     decision/progress data the owner wants private for now.
3. **Named, deferred phase — do NOT build this on the first run without a fresh
   explicit go-ahead:** rework `dashboard/` and `botsite/` (both currently in
   `superbot`, read-only source for you) into `websites` — same general ideas, UI
   feel, and functionality, rebuilt implementation, same way `superbot-next` is
   rebuilding the bot rather than copying it. This is real, wanted work, not a
   maybe — it's sequenced *after* step 2 because step 2 is net-new and doesn't
   require deciding anything about the live sites first. When you reach this step,
   flag it as a milestone in a status report and describe your plan before writing
   code, rather than silently starting — this is the one place in this Project's
   scope where "decide and flag, never wait" pauses for a real check-in, because it
   touches the shape of tools the owner uses today, not just infrastructure.

## Infrastructure

Empty repo (`git push` first-publish is walled for agents; use the GitHub Contents
API's `create_or_update_file` to seed the first commit, exactly like `superbot-next`
and `substrate-kit` did — full precedent in
[`docs/operations/repo-settings-state.md`](../operations/repo-settings-state.md)'s
capability-facts table).

**Railway**: create a new Railway project (distinct from the existing
`reliable-grace` production project — never touch that one) via the account token
available in your environment (owner's explicit choice: same full-access token every
agent container already holds, not a scoped project token — informed choice,
trade-off already surfaced and accepted). If you cannot reach the Railway API at all
from this container, that is itself the most important finding to report — say so
plainly rather than working around it silently.

**THE ONE HARD RAIL**, unchanged from the earlier draft of this plan: you hold a
full-access Railway account token that can reach the production bot's project and
database. Never call a delete/restore/destructive mutation against ANYTHING outside
the new project you create for this work — and never against anything, even in your
own project, without stating exactly what you're about to delete first and getting
an explicit owner go-ahead. This is the one place "decide and flag, never wait" does
not apply to infrastructure either — destructive Railway mutations are the
exception, not the rule.

## Owner setup (do once, before pasting the Custom Instructions)

1. Repo already created: `menno420/websites` (empty).
2. **New Claude Code Project.** Repo list = **four repos**: `menno420/websites`
   (write, the build target), `menno420/superbot` (read — source for `dashboard/`
   and `botsite/` when step 3 starts, and for the rebuild's own data), `menno420/superbot-next`
   + `menno420/substrate-kit` (read — data sources for the readiness board + journal
   browser).
3. Paste the **Custom Instructions** (below) into Project Settings.
4. Send the **startup prompt** (below) to the coordinator.

## Custom Instructions (paste-in)

---

This Project is the permanent new home for SuperBot's web properties — a sibling
rebuild track to the bot rebuild itself. Your relationship to the two existing sites
(`dashboard/` and `botsite/`, both living in `menno420/superbot`) is the same
relationship `superbot-next` has to `superbot`: same substrate-kit foundation, same
philosophy — keep the ideas and functionality, rebuild the implementation. The
existing sites keep running untouched until their replacements are ready; nothing
here touches them directly except reading their source for reference later.

ORIENTATION — read before building. `menno420/superbot`'s
docs/planning/websites-project-kickoff-2026-07-09.md (this doc) is your brief.
Also read (read-only, from `superbot`): docs/operations/repo-settings-state.md (the
per-repo settings ledger — your readiness board's seed data), docs/planning/per-repo-settings-state-ledger-2026-07-08.md
(that ledger's own plan, including its Phase 2/3), and `dashboard/README.md` +
`botsite/README.md` (what the existing sites do today, for step 3 later — read now
for context, don't build against them yet).

THE GOAL, IN ORDER:
1. Adopt substrate-kit into `menno420/websites` FIRST — `python3 dist/bootstrap.py
   adopt` from `menno420/substrate-kit`, fresh-from-kit, never a copy of `superbot`.
   The repo is currently EMPTY — seed its first file via the GitHub Contents API
   (`create_or_update_file`), after which normal branch-push git works (this is the
   one walled git action for agents; the Contents API bypasses it, already proven
   working on `superbot-next` and `substrate-kit`).
2. THEN build the control-plane / oversight site: a readiness board (per-repo —
   superbot, superbot-next, substrate-kit, and websites itself — is the ruleset
   configured, are the right checks required AND currently green, is CODEOWNERS
   enforced, are secrets present, is auto-merge armed) seeded from
   docs/operations/repo-settings-state.md's data model, generalized across repos;
   and a journal browser (session logs, decision ledgers, question-routers, PR
   history across all repos, linked into GitHub, not narrated). Gate access behind
   something simple — this shows internal data the owner wants private for now.
   Pick your own stack and defaults; note your choices as you go.
3. Reworking `dashboard/` and `botsite/` into this repo (same ideas/functionality,
   rebuilt implementation) is real, wanted, in-scope work — but NOT for you to start
   autonomously on this first run. When you reach the point of starting it, stop and
   describe your plan in a status report first; that's the one deliberate check-in
   point in an otherwise decide-and-flag Project, because it touches tools the owner
   uses today.

FORWARD-ONLY GIT, same discipline as the rebuild Project: fresh branch → PR →
squash-merge in your own repo; never force-push, delete a remote branch, or amend a
pushed commit anywhere.

INFRASTRUCTURE. Create a new Railway project (never the existing production
`reliable-grace` project) and deploy through the Railway API using the account token
available in your environment. If you can't reach it at all, report that plainly.

THE ONE HARD RAIL: you hold a full-access Railway account token reaching the
production bot's project and database too. Never call a delete/restore/destructive
mutation against anything outside your own new project — and never against anything,
even your own, without stating exactly what you're about to delete and getting an
explicit owner go-ahead first. This is the one exception to decide-and-flag.

HOW TO WORK. Decide and flag on everything else — stack, layout, auth mechanism,
refresh cadence, sequencing within steps 1-2. Send a status report at each real
milestone (kit adopted, first local build working, Railway project created, first
deploy live, readiness board wired to real data, journal browser working) and
explicitly call out anywhere you got stuck or worked around a limitation.

---

## Startup prompt (paste-in, first message to the coordinator)

---

Build the permanent new home for SuperBot's websites. Start by reading
`menno420/superbot`'s `docs/planning/websites-project-kickoff-2026-07-09.md` — it has
the full brief, why this repo exists, and the one hard safety rail (never touch the
production Railway project or call a destructive mutation without asking first).

Work in `menno420/websites` (already created, currently empty — you'll need to seed
its first commit via the Contents API). First: adopt substrate-kit into it, same way
`superbot-next` did. Then: build a control-plane site showing per-repo readiness
(rulesets, required checks actually green, CODEOWNERS, secrets, auto-merge) across
`superbot`/`superbot-next`/`substrate-kit`, plus a browser for session logs and
decision ledgers across all three, linked into GitHub. Gate access behind something
simple. Deploy on a new Railway project you create yourself.

Reworking the two existing sites (`dashboard/`, `botsite/` in `superbot`) into this
repo is real future work, but don't start it on this run — when you get there, stop
and describe your plan first. Pick your own stack and defaults for everything else;
note your choices as you go. Send a status report at each real milestone.

---

## What "success" looks like

Same frame as [`rebuild-status-site-project-kickoff-2026-07-08.md`](rebuild-status-site-project-kickoff-2026-07-08.md)
laid out (directing quality / self-correctness / infra capability) — unchanged by
this doc superseding it; re-read that doc's final section if you need the full
three-axis scoring rubric when reviewing this Project's status reports.
