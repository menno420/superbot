# 2026-06-17 — Routine review + autonomous-workflow hardening

> **Status:** `in-progress`
> Owner-live session. Reviewing the **first full unattended-routine day** (~20h, ~#1017–#1025
> + the band-#1020 reconciliation pass), then routing the owner's observations to their durable
> homes and applying the contained workflow fixes he steered in-session (`AskUserQuestion`,
> 2026-06-17). Born-red per Q-0133; flip to `complete` after the owner reviews the governance-doc
> edits.

## Goal

The owner's first full day back. He let the two-routine fleet run unattended from ~02:00 with no
interference and gave a brain-dump of observations. This session: **review** what the routines did,
and **map** the useful points to the repo (ideas / router decisions / config fixes), per his ask.

## Review of the 20h run (the headline finding)

The fleet did **high-quality, self-auditing work** — every log verifies CI, reviews its predecessor,
contributes an idea, and writes a run report; the reconciliation pass even pruned a self-inflicted
~2,000-word drift surface. **The one real systemic problem is exactly the one the owner spotted:**
reconciliation fires every **30** PRs but only plans the next **~9**, so the buildable queue drains
and dispatch fires start hitting "exhausted lane / plan-first / owner-paced" walls (the BTD6 floor
lane is now fully consumed). "Running out of plans" is real and has a precise, fixable cause.

## Plan (what this session ships)

- **Planning depth** — reconciliation plans the FULL band (depth ≥ the 30-PR cadence, as larger
  initiatives or more slices) + a **low-backlog flag** so a thin idea backlog triggers a dedicated
  planning session instead of filler. → `CLAUDE.md` + both routine prompts. (Q-0164)
- **Routine self-labeling** — each session log declares its run type (`routine` / `manual`);
  surfaced as a badge on the dashboard updates feed so the owner can see routine work at a glance.
  (Q-0165)
- **Drift-on-sight** — spotted ledger/docs drift is fixed immediately, not deferred to the
  reconciliation failsafe (bugs-first applies to docs). (Q-0166)
- **Updates freshness** — `dashboard.json` regenerates on every source-touching merge to `main`, so
  the updates feed stops lagging ~30 PRs behind. (Q-0167)
- **Hermes plain-language house style** — ONE sample report drafted for owner review (preview-first,
  then roll out). (Q-0168)
- **Owner review-inbox / communication website** — captured as idea + plan (build later). (Q-0169)
- **Claude skills + automation shortlist** — captured as idea. (Q-0170)

## 📤 Run report

- **Did:** review the first unattended-routine day + route the owner's observations to durable homes + apply the steered workflow fixes · **Outcome:** _pending close_
- **Shipped:** _pending — this PR_
- **Run type:** manual (owner-live)
- **⚑ Owner decisions needed:** Q-0164…Q-0170 recorded with provenance; the Hermes sample (Q-0168) + review-inbox shape (Q-0169) await the owner's read
- **⚑ Owner manual steps:** re-paste the two updated routine prompts into their console configs (CLAUDE.md/prompt edits only take effect once pasted)
- **↪ Next:** _pending close_
