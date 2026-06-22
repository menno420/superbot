# Session — 2026-06-22 · Karma (thanks/upvote reputation) — plan-first

> **Status:** `complete` — plan-first deliverable landed; no `disbot/` code (implementation awaits the owner's 5 design answers).

**Run type:** owner-directed (one-word prompt "Karma"). **Branch:** `claude/peaceful-franklin-klgw3f`.
**Trigger:** maintainer dropped the idea "Karma"; clarified via AskUserQuestion → **plan it first**,
flavor **thanks/upvote reputation**. Deliverable is a `docs/planning/` plan + roadmap horizon, then
await go-ahead to build (no implementation this session).

## What I'm about to do

Design a **Karma** subsystem: members grant each other reputation (thanks/upvote), tracked per-user
with an audited mutation seam and a leaderboard provider — modelled on the existing economy/XP
patterns (DB layer → `*_service.py` with audit + EventBus emit → cog → settings spec → invariant
test → leaderboard provider). Produce: (1) an idea-capture in `docs/ideas/`, (2) a buildable plan in
`docs/planning/` (2–3 PR slices), (3) a `docs/roadmap.md` Someday/Next horizon row + `docs/planning/README.md`
index entry. Plan-only — no `disbot/` code.

## What changed

Plan-only, docs-only (no `disbot/` code):
- **Idea capture:** [`docs/ideas/karma-reputation-system-2026-06-22.md`](../docs/ideas/karma-reputation-system-2026-06-22.md)
  — the thanks/upvote reputation idea + why-it-fits + the anti-abuse framing + 5 open Qs.
- **Buildable plan:** [`docs/planning/karma-reputation-plan-2026-06-22.md`](../docs/planning/karma-reputation-plan-2026-06-22.md)
  — full design mirrored on economy/XP: two tables (`karma` + append-only `karma_audit_log`), the
  db→service→cog layering with concrete signatures, settings keys, a `KarmaProvider` leaderboard
  category, an INV-K write-seam invariant, a 2–3-PR slice, a risk checklist, and 5 owner-gating
  design questions with a recommended default direction.
- **Roadmap horizon:** added a **Later (owner-directed, plan-first)** Karma row to the S1 community
  lane in `docs/roadmap.md`; indexed the plan in the S1 table of `docs/planning/README.md`.
- **Research grounding:** mapped economy/xp/leaderboard via an Explore agent + direct source reads
  (`rank_providers.py` `_PROVIDERS` registry, `events_catalogue.py`, `ownership.md` rows) so every
  code-pointer in the plan is real as of `7ec747e`.

⚑ **Self-initiated:** none — owner-directed (the maintainer dropped "Karma"; AskUserQuestion
confirmed plan-first + thanks/upvote flavor). The plan is owner-gated on 5 design answers before PR 1.

## 💡 Session idea (Q-0089)

[`audited-score-subsystem-scaffold`](../docs/ideas/audited-score-subsystem-scaffold-2026-06-22.md) —
economy/xp/karma are the **same six-piece "audited per-user score" shape** built by hand (db seam +
audit_log + service + event-catalogue entry + INV test + rank provider). Designing karma meant hand-
copying all six. Proposes a `new_score_subsystem` scaffold + a **leaderboard-parity guard** (every
score table has a `RankProvider` or an explicit exclusion) so the two easy-to-forget pieces are never
skipped. Genuinely surfaced by *doing* this plan, not filler.

## ⟲ Previous-session review (Q-0102)

The band-#1320 reconciliation pass (the immediately-prior session) was a clean routine pass and left
the ledger in sync (SessionStart confirmed `Ledger: in sync ✓`, next recon at #1350) — nothing to
fix there. **System improvement (initiated):** this session hit a gap the workflow doesn't name — a
**one-word idea drop** ("Karma") has no documented intake convention, so I fell back to
AskUserQuestion (intent + flavor) before committing a session, which worked well. Worth promoting:
the idea-intake docs (`docs/ideas/README.md`) could state explicitly that a *terse/ambiguous* drop
should be disambiguated with one AskUserQuestion (build-now / capture / plan-first × flavor) **before**
opening a born-red PR — turning what I improvised into a repeatable step. Captured here rather than
edited into the binding doc on my own initiative (Q-0106).

## 📋 Doc audit (Q-0104)

- `check_docs --strict` → **all checks passed ✓** (421→422 docs; new idea/plan files reachable via the
  ideas README index, planning README S1 table, and the roadmap row; badges valid).
- No merged-PR ledger impact (nothing shipped to `disbot/`), so `current-state.md` Recently-shipped is
  untouched — correct for a plan-only session.
- No new owner *decision* to route to the question router; the 5 design questions are owner-gating and
  live in the plan §7 (the right home until the owner answers).
- Architecture: docs-only, no layer surface touched (`check_architecture`: no files to check).
