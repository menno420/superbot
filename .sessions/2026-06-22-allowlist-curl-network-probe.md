# 2026-06-22 — Allow read-only network probes (curl) + claim-ledger drift prune

> **Status:** `complete`

## What I did
Owner-directed in-session change (PR #1274): moved `curl` from the permissions `ask` list to
`allow` in `.claude/settings.json` (plus the `timeout` wrapper) so read-only network probes — e.g.
the `timeout 15 curl -sS -o /dev/null …` wiki-feasibility check that prompted this run — no longer
interrupt. Destructive / external / DB / other-network commands stay gated in `ask` (`wget`,
`docker`, `railway`, `psql`, `pg_dump`, `pg_restore`, `rm -r*`, `rmdir`, force-push, `git clean -f`,
`sudo`). JSON validated (`python3.10 -m json.tool`). Also pruned one stale `active-work.md` claim
(BUG-0023, PR #1272 already merged — drift-on-sight, Q-0166).

Owner-directed (Q-0106 in-session exception — the owner is the live reviewer for executable-config
edits). Q-0191: owner-directed → merge immediately on green; auto-merge armed.

## Context — this was a dispatch fire interrupted by an owner config request
Started as a scheduled empty-fire dispatch run. Oriented (current-state ▶ Next action, newest
`.sessions` log, bug-book) and assessed the buildable lanes before the owner interrupted with the
config request. The lane assessment (handoff below) is the substantive finding.

## Handoff — buildable-lane assessment for the next dispatch run
The open bugs are all blocked: **BUG-0011** (Hermes-infra, needs a clean VPS foreground repro),
**BUG-0019 #1** (`always_reply` design fork — routed to owner), **BUG-0009 newest-towers** (data-gated,
needs sourced release-order data). The headline buildable lanes from the band-#1260 ▶ Next action are
each a poor fit for an *unattended* self-merge run, which is the honest gap behind the standing
"ungated self-merge subset stays thinner" caveat:
- **Project Moon runtime PR 1** (Q-0192, marquee) — network IS available (limbus.wiki.gg → 200), but
  Slice A ingests **datamined third-party game data** with explicit IP sensitivity (recon §1b caveat:
  "Project Moon's IP stance is stricter than Ninja Kiwi's"). Committing externally-sourced data
  autonomously brushes the external-data safety brake → wants owner confirmation on the source/licensing
  approach; later steps touch groundedness-critical AI runtime → `needs-hermes-review`.
- **AI-panel in-place nav PR 1** — explicitly "written for a session with runtime context / the joint
  live-session cadence (Q-0086)"; needs a live guild walk → weak unattended fit.
- **procedures→skills Batch 2** — edits `.claude/CLAUDE.md` (Q-0106-sensitive; born-red for owner review).
- **botsite React-SPA migration** — large frontend program.

Recommendation for an unattended fire: prefer a contained, offline-verifiable, IP-clean slice (or a
`needs-hermes-review` lane the owner will verify), and route the IP/licensing question for Project Moon
data to the owner before committing scraped data.

## 💡 Session idea (Q-0089)
**Self-healing read-only allowlist for unattended runs.** This run *stalled on a permission prompt* for
a legitimately-safe `curl` probe — fine when the owner is watching, fatal to a truly-unattended routine
(it just hangs). Idea: run the existing `/fewer-permission-prompts` scan as a low-cadence dispatch
ender (or a dedicated routine) that mines recent transcripts for **read-only** commands that hit
`ask`/prompted and proposes allowlist additions — so the allowlist drifts toward "no read-only safe
command ever blocks an unattended run," while write/exfil/destructive commands stay gated. Grounded in
exactly what happened here.

## ⟲ Previous-session review (Q-0102)
The band-#1260 reconciliation pass was strong — clean open-PR disposition with *explicit* recorded
heuristics, and it honestly carried the "ungated self-merge subset stays thinner" caveat forward. What
this run surfaced as the concrete next improvement: that caveat is real but **unactionable as prose** —
a scheduled empty-fire run still has to discover mid-run that every headline lane needs a human. The
planner (reconciliation pass) should tag each queued lane with an **unattended-fit flag**
(offline-verifiable? self-mergeable? needs-live-verify? external-data/IP?), so the dispatch routine can
pick a lane it can actually *complete and merge* unattended instead of stalling. (Captured as the
forward direction; not promoted to a plan this run.)

## 📤 Run report
- **Did:** owner-directed config change (curl `ask`→`allow` + timeout wrapper) + drift-on-sight prune of
  a stale `active-work.md` claim; oriented + assessed buildable lanes (handoff above) · **Outcome:** shipped (PR #1274, auto-merge armed)
- **Shipped:** PR #1274 — `.claude/settings.json` permission tweak + `active-work.md` prune + this card
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** none (the Project-Moon data IP/licensing question is *recommended* for a
  future build run, not owed now)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (config change was owner-directed; the claim prune is drift-fix-on-sight, Q-0166)
- **↪ Next:** band-#1260 queue stands; see the buildable-lane assessment above before an unattended fire.
