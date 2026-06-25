# Session — 2026-06-25 · Essential Setup PR 2 — extras menu + "Check my setup"

> **Status:** `complete` — shipped. Run type: routine · dispatch.

## What I did

Empty-fire dispatch run. The bug-book root-fix backlog is gated (BUG-0009 newest-towers is
data-gated; BUG-0019 #1 is an owner design fork), so I took the explicit S1 ▶-next plan slice:
**Essential Setup wizard restructure — PR 2** (plan
`docs/planning/setup-wizard-restructure-plan-2026-06-24.md` §7). PR **#1449**.

Both additions hang off the "All done" summary (`EssentialSummaryView`), both plain-language (the
jargon guard covers `essential_setup.py` — it's not in the baseline, so any banned term fails CI):

- **More to set up (Extras menu)** — `ExtrasMenuView` + `build_extras_embed` + `_Extra`/`_EXTRAS`: a
  one-screen menu of the seven optional features the spine doesn't cover (Hall of Fame `!starboard` ·
  live member counts `!counters` · raid/new-account protection `!security` · image filtering `!imagemod`
  · Thanks & Karma `!karma` · AI helper `!aimenu` · reaction roles `!reactroles`), each with what it does
  + the command to open its full setup, and a Back button to the summary.
- **Check my setup** — `build_check_setup_embed` over `services.setup_readiness.collect`: a "how set up
  are you" headline + a ✅/➖ list of the six essentials in outcome language (no bindings/settings/
  subsystem vocabulary), shown ephemerally.

**Deviation noted (judgment over plan):** the original spec said each extra is "a one-action step". I
surfaced each with its **setup command** (the discoverability win — the audit's core goal) rather than
re-implementing every feature's config inside the spine (a much larger per-feature effort duplicating
the existing panels). Full per-extra in-wizard config is a later follow-on. **Native giveaways are
intentionally absent** — that subsystem isn't built yet; listing a command would mislead.

Files: `disbot/views/setup/essential_setup.py` (+ ~190 LOC, additive — no new cog/command/artifact),
`tests/unit/views/setup/test_essential_setup.py` (+11 tests, 57 total green). Docs de-staled: the plan
(§7 + build-progress banner) and the S1 sector file. **CI mirror green** (`check_quality.py --full`:
12534 passed; `check_architecture.py --mode strict`: 0 new; jargon guard: 0 new; `setup_wizard_sim.py`:
PASS).

## Handoff / next

**S1 ▶ next = setup-wizard PR 3** (retire dead/legacy spine sections + **rework** the Advanced
draft→Final-Review editor — Q-E: "currently most of it does not do anything"). PR 3 is heavier and
riskier than PR 2 (it audits each Final-Review action and wires up or strips the dead ones), so it
wants its own focused session and likely `needs-hermes-review`... *(retired — every PR auto-merges on
green now, Q-0197)* — just open it born-red and let it merge on green. Other live S1 startables
unchanged: Project Moon runtime PR 1 · botsite React-SPA migration PR 2.

## 💡 Session idea (Q-0089)

*Extras-menu live status badges* — the extras menu currently lists every optional feature with its
command, but doesn't show whether each is already on. A cheap follow-up: have `build_extras_embed`
take the same readiness snapshot `build_check_setup_embed` already fetches and prefix each extra with
✅/➖ (and re-word "Open with `!x`" → "Already on — manage with `!x`" when configured). One readiness
read, big discoverability gain — the operator instantly sees what's left. Captured here rather than a
full idea file (it's a small, decided-lane follow-on to this PR, not a standalone concept).

## ⟲ Previous-session review (Q-0102)

Previous run = the **25th Q-0107 reconciliation pass** (band-#1440, #1441). It did the reconciliation
discipline well — grouped ledger entries, trimmed to 20, reset the marker, planned a full next band
with no THIN flag, and even caught/avoided the "claim in prose, forget the file edit" drift class by
re-badging the band-#1410 record `historical`. One genuine miss: it left a **stale claim file**
(`docs/owner/claims/claude-jolly-johnson-rqf8wt.md`, the band-#1380 pass, long since merged) in place —
the per-claim-file layout (Q-0195) is supposed to be self-cleaning on session close, but a
reconciliation routine that only touches docs apparently skipped the claim sweep. **System
improvement:** `scripts/check_session_log.py` (or the Stop hook) could flag claim files whose branch
has no matching open PR *and* is already merged to `main` — a one-line "stale claim, delete it" nudge
would close this leak. I deleted the stale claim this run.

## 📤 Run report

- **Run type:** routine · dispatch
- **What shipped:** PR #1449 — Essential Setup PR 2 (extras menu + "Check my setup").
- **⚑ Self-initiated:** none (took the explicit S1 ▶-next plan slice; the deviation is an
  implementation choice within that slice, flagged above).
- **⚑ Owner-decisions:** none (no new owner decisions; works within Q-0202–Q-0205, Q-A).
- **⚑ Owner-manual-steps:** none (a merge auto-deploys; no data/seed step — no data file changed).
- **Bug-book:** no entries fixed (the two open root-fix-backlog items stay gated); none newly opened.
- **Doc audit (Q-0104):** ledger in sync (no merged-PR delta this run beyond the born-red card);
  plan + S1 sector de-staled; deleted the stale `claude-jolly-johnson-rqf8wt` claim.

