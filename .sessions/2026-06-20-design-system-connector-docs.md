# 2026-06-20 — Design-system docs: connector-vs-`/design-sync` correction

> **Status:** `in-progress`

## Arc

Follow-up to PR #1175 (same session). The owner clarified they enabled Claude Design via the
**GitHub connector**, not the repo's `/design-sync` path — so the design-system README (which
documented only `/design-sync`) misdescribed how they actually work, and my earlier "re-run
`/design-sync`" advice was wrong. Owner approved a docs correction (AskUserQuestion 2026-06-20).

## Plan / shipped

- `design-system/README.md` — make the **GitHub connector** the primary documented path
  (repo = source of truth; merging *is* the sync; refresh the project to pick up new commits);
  keep `/design-sync` as a labelled alternative; fix the loop step + Build/Stack mentions.
- `docs/AGENT_ORIENTATION.md` — add the missing **"Touching the public site / design-system /
  Claude Design"** route (the orientation gap flagged in the #1175 log) pointing at the README.
- `.github/workflows/design-system-ci.yml` — correct the one-line comment about how the
  library reaches Claude Design.
- `docs/owner/active-work.md` — clear the now-merged #1175 + #1168 claims; claim this PR.

## Verification

Docs-only (no code change). `design-system-ci` re-runs via the `design-system/**` path filter
and stays green (typecheck/build untouched). README anchor link checked.

## Session enders

Continuation of the #1175 session — its full enders (idea Q-0089, grooming Q-0015,
prev-session review Q-0102, doc audit Q-0104, telemetry) live in
`.sessions/2026-06-20-design-system-landing-page.md` and are not duplicated here, to avoid
hallucinated ceremony (the Q-0089/Q-0102 bar). One genuine note this follow-up surfaces:
**doc accuracy degrades silently when a tool's UX differs from what we assumed** — the README
asserted `/design-sync` as *the* path with no provenance date, so nothing flagged it when the
owner's actual setup (connector) diverged. Cheap guard for next time: write integration docs
around *what the repo guarantees* (the buildable library) and label *external-product UX*
(how Claude Design ingests it) as "as of <date>, verify", since that half can drift without a
repo change.

## 📤 Run report

- **Did:** corrected the design-system docs to document the GitHub-connector workflow the owner
  actually uses (was `/design-sync`-only) + closed the AGENT_ORIENTATION website-route gap. ·
  **Outcome:** docs-only PR, auto-merge on green.
- **Run type:** `manual` (owner-directed follow-up).
- **⚑ Owner decisions needed:** `none`.
- **⚑ Self-initiated:** the `AGENT_ORIENTATION` route + `active-work` cleanup + workflow-comment
  fix (bundled proactively as connected drift); the README fix itself was owner-requested.
- **↪ Next:** owner refreshes/reopens Claude Design and confirms the new full-page components
  appear (merging #1175 published them via the connector).
