# Rebuild status-site Project — kickoff (Custom Instructions + startup prompt, 2026-07-08)

> **Status:** `plan` — paste-in Custom Instructions + startup prompt for a **second,
> separate** Claude Code Project, distinct from the rebuild Project
> ([`rebuild-project-kickoff-2026-07-08.md`](rebuild-project-kickoff-2026-07-08.md)).
> **Provenance:** owner directive 2026-07-08, decided via the directing session's
> question panel (see [`rebuild-direction-handoff-2026-07-08.md`](rebuild-direction-handoff-2026-07-08.md)
> for that session's role).

## Why this Project exists — two goals, one build

1. **A genuinely useful artifact:** a live status page for the rebuild — PR velocity
   across `superbot-next` + `substrate-kit`, port-band/kernel progress, the decision
   ledger, open `question-router.md` items, the `golden-parity` replay ratio, and
   `verified_live` coverage. This turns the manual GitHub-API status pulls the
   directing session has been doing by hand into something that just exists.
2. **A controlled capability test**, deliberately separate from goal 1: can a fresh
   Project take a "build one finished, deployed thing" task **end to end** —
   create its own repo, write working frontend + backend code, provision real
   infrastructure, deploy, and wire up live data — with no owner hand-holding beyond
   the setup below? This is the **first test of Railway access from a Project**;
   nothing in the rebuild Project has touched Railway at all yet.

**Known overlap, accepted on purpose:** `botsite/console/` in the `superbot` repo
already does something similar (session reports, ideas/bugs counters, changelog) on
the **production** Railway project. Extending that would be cheaper, but would test
almost nothing about repo/infra provisioning — the owner explicitly chose the
duplicate-scope option so the Railway/repo-creation capability actually gets
exercised. This Project's output does **not** replace `botsite/console`; if it turns
out better, a future session can retire the old one — that decision is out of scope
here.

## Scope

**In scope:** design + build + deploy one status site covering the rebuild's own
progress, hosted on its own new Railway project, in its own new repo.

**Explicitly not in scope:** touching `superbot`, `superbot-next`, or `substrate-kit`
beyond read access for data; touching the **production** Railway project
(`reliable-grace` — the live bot + its Postgres) in any way, ever.

## Owner setup (do once, before pasting the Custom Instructions)

1. **New GitHub repo**, e.g. `menno420/rebuild-status` — private, auto-init with a
   README (so it's non-empty; matches the pattern that worked cleanly for
   `superbot-next`/`substrate-kit` — an empty repo's first commit is walled for
   agents, `create_or_update_file` bypasses it, but starting non-empty avoids the
   friction entirely).
2. **New Claude Code Project.** Repo list = **four repos**: `menno420/superbot`,
   `menno420/superbot-next`, `menno420/substrate-kit` (all **read** — data sources),
   `menno420/rebuild-status` (the build target).
3. Paste the **Custom Instructions** (below) into Project Settings.
4. Send the **startup prompt** (below) to the coordinator.

**Railway credential — owner-decided, risk accepted explicitly:** this Project uses
the **same full-access account token** every other agent container already holds (per
the standing Q-0213 convention: full access is deliberate project-wide, not scoped per
task). This means it *can* reach the production bot's Railway project and database,
not just its own. The one binding guardrail carried over unchanged: **no automation
ever calls a `*Delete`/`*Restore`/data-loss mutation without an explicit owner ask** —
restated in the Custom Instructions below so this Project inherits it, not just the
rebuild Project.

## Custom Instructions (paste-in)

---

This Project builds and deploys one thing: a live status site for the SuperBot
rebuild. Your two goals, in order: (1) ship a genuinely useful, correct site; (2) do
it with minimal owner involvement — this is a test of whether you can take a
build-and-deploy task fully end to end, including provisioning real infrastructure.

ORIENTATION — read before building. `menno420/superbot`'s
`docs/planning/rebuild-status-site-project-kickoff-2026-07-08.md` (this doc) is your
brief. For DATA SOURCES, read (read-only, across all three source repos):
`docs/planning/rebuild-canonical-plan-2026-07-06.md` §5 (the step sequence, so you
know what "progress" means), and in `superbot-next` + `substrate-kit`:
`docs/decisions.md` (the decision ledger), `docs/question-router.md` (open owner
questions), `manifest.snapshot.json` + the `golden-parity` workflow's `report` job
history (parity ratio), and each repo's PR/commit history (velocity, band sequence).
For an existing PATTERN worth reading (not copying wholesale — your stack choice is
yours to make): `superbot`'s `botsite/` app is a working FastAPI-plus-static-JSON
site already deployed on Railway; its README explains the data-export pattern
(`scripts/export_dashboard_data.py` generates a JSON blob the app only reads, never
touching the bot's live code). You are free to use a different stack if you judge it
better for this task — state why in your first status report either way.

THE GOAL: build `menno420/rebuild-status` into a small web app that shows, refreshed
on a schedule you choose (polling the GitHub API is enough — no webhooks required):
PR velocity + recent activity across `superbot-next` and `substrate-kit`; kernel/port
band progress (derive this from the decision ledger's D-NNNN entries and PR titles —
there is no single "progress" field, you'll need to build a reasonable heuristic and
say so); the decision ledger itself, browsable; open `question-router.md` items, if
any; the `golden-parity` report-job ratio (ported/replayable subsystems out of the
full corpus) over time; `verified_live` registry coverage. Gate it behind SOME access
control (a shared-secret/password gate is enough — this doesn't need real auth) since
it will show internal decision/progress data the owner wants private for now.

INFRASTRUCTURE — this is the part being tested. Create a new Railway project
(distinct from the existing `reliable-grace` production project — never touch that
one) and deploy this site to it, entirely through the Railway API using the account
token available in your environment. If you cannot reach the Railway API at all from
this container, that is itself the most important finding to report — say so plainly
rather than working around it silently.

FORWARD-ONLY GIT, same discipline as the rebuild Project: fresh branch → PR →
squash-merge in your own repo; never force-push, delete a remote branch, or amend a
pushed commit anywhere.

THE ONE HARD RAIL, carried over from the main bot's own Railway convention (Q-0213):
**you hold a full-access Railway account token that can reach the production bot's
project and database. Never call a delete/restore/destructive mutation against
ANYTHING outside the new project you create for this site — and never against
anything, even in your own project, without stating exactly what you're about to
delete first and getting an explicit owner go-ahead.** This is the one place "decide
and flag, never wait" does not apply — destructive Railway mutations are the
exception, not the rule.

HOW TO WORK. Decide and flag on everything else — pick reasonable defaults for stack,
layout, auth mechanism, refresh cadence; note the choice and move on. Send a status
report at each real milestone (repo scaffolded, first local build working, Railway
project created, first deploy live, data wired up, access-gate in place) — and
explicitly call out anywhere you got stuck or worked around a limitation, since that's
exactly the signal this test exists to produce.

---

## Startup prompt (paste-in, first message to the coordinator)

---

Build and deploy a live status site for the SuperBot rebuild. Start by reading
`menno420/superbot`'s `docs/planning/rebuild-status-site-project-kickoff-2026-07-08.md`
— it has the full brief, data sources to read from, and the one hard safety rail
(never touch the production Railway project or call a destructive mutation without
asking first).

Build it in `menno420/rebuild-status` (already created, non-empty). Show rebuild
progress pulled from `superbot-next` and `substrate-kit`'s real GitHub state — PR
activity, decision ledger, open owner questions, parity ratio. Gate access behind
something simple. Deploy it on a **new** Railway project you create yourself via the
API — this is a real test of whether that works, so if you hit a wall, tell me
plainly rather than quietly giving up on it. Pick your own stack and defaults; note
your choices as you go rather than asking first. Send a status report at each real
milestone.

---

## What "success" looks like (for scoring this Project against the rebuild Project)

Same two-axis frame as the rebuild Project's directing session uses
([`rebuild-direction-handoff-2026-07-08.md`](rebuild-direction-handoff-2026-07-08.md)),
plus a third axis unique to this test:

1. **Directing quality** — same as always: are owner-only items (if any come up)
   batched and flagged, not dripped or attempted-then-blocked?
2. **Self-correctness** — is the deployed site actually correct (real data, not
   placeholder/fabricated numbers — see the audit checklist's stub-file lesson,
   [`rebuild-project-audit-checklist-2026-07-08.md`](rebuild-project-audit-checklist-2026-07-08.md)),
   and does it stay working after the initial deploy?
3. **Infra capability (new)** — did repo creation, Railway project creation, and
   deploy actually work unattended, or did the Project stall/silently avoid the
   infrastructure parts of the task? This is the headline finding for the ongoing
   Claude Code Projects EAP evaluation
   ([`projects-eap-evaluation-log.md`](projects-eap-evaluation-log.md)) — record it
   there regardless of outcome.
