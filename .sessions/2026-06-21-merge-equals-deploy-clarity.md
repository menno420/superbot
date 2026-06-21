# 2026-06-21 — "Merge = deploy" clarity (kill the "restart is yours" misinformation)

> **Status:** `complete` — owner directive Q-0193 (in-chat). PR #1247, auto-merge on green.

> **Run type:** `manual` (owner-directed, in-chat)

## Arc

Owner caught a real error: at the end of the role-presets session (#1245) I told him "the production
restart is still yours" — but **Railway auto-deploys `main` on every merge**, so a merged change is
live on its own. The owner's point was two-fold: (1) the factual claim is wrong, and (2) the fact that
I parroted it means the deploy reality is buried / the docs are too crowded.

Fixed at the **roots** so the next agent stops repeating it — *less* noise, not more:

1. **`docs/operations/production-deployment.md`** — added an unmissable **"Merge = deploy"** lead on
   *How code reaches production* (it already said this correctly, just not loudly), and dropped the
   misleading "restarts … stay the maintainer's" shorthand from the consequence bullet.
2. **`.claude/CLAUDE.md`** — rewrote the binding shorthand "**Merge ≠ deploy** — production
   restart/prod-checks stay the maintainer's" (the line agents internalize and copy) to "**Merging IS
   deploying** … never tell the maintainer to restart/deploy a merge." Owner-directed in-session →
   applied under the Q-0106 live-owner exception, citing **Q-0193**.
3. **`docs/owner/maintainer-question-router.md`** — **Q-0193** provenance.
4. **`.session-journal.md`** — one prevention line next to the already-accurate auto-deploy fact.

## Findings / decisions

- **The canonical doc was already right, just buried.** `production-deployment.md` literally said "an
  agent merging a green session PR *is* triggering a production deploy" — but it was the *second* bullet,
  under a heading that led with the GitHub-integration mechanics, and it repeated the same "Merge ≠
  deploy / restarts stay the maintainer's" shorthand that misleads. The fix was a loud lead + dropping
  the shorthand, not new facts.
- **The misinformation spread by copy.** Session cards free-write the `⚑ Owner manual steps` line by
  copying prior cards; "Merge ≠ deploy: prod restart stays yours" propagated that way (it's in several
  `.sessions/*` cards, incl. my own #1245). Fixing the *binding* line in CLAUDE.md + the canonical doc
  cuts it at the source agents copy from. (See Session idea for a guard.)
- **Accurate division of labour (now stated once, clearly):** merge → Railway auto-redeploy `worker` →
  live in minutes (deploy = restart). Maintainer's: **live verification, rollback, eval walks** + any
  per-PR *data* step a change explicitly names (`!btd6ops seed-data`; an operator button to clear stale
  rows — e.g. the #1245 "🧹 Clear Missing"). NOT the deploy/restart.

## Context delta

- **Needed but not pointed to:** that the "restart is yours" claim was *already* flagged "scattered and
  partly wrong" by the 2026-06-16 act-on-review session — yet it persisted because that pass fixed the
  *autonomous-loop* docs but left the CLAUDE.md auto-merge bullet + the session-card habit. The lesson:
  a misinformation fix has to hit the *most-copied* surface (the binding bullet), not just one doc.
- **Decision made alone:** treat this as a docs-root fix + a Q-block, not a sprawling find-and-replace
  of every `.sessions/*` card (those are immutable history; rewriting them is noise — fix the source).
- **Weak point / unverified:** I did *not* grep-replace the stale phrasing out of older `.sessions/*`
  cards (history, left as-is) or the terser `ai-project-workflow.md:410` "Merge ≠ deploy." (it's in the
  Q-0084 autonomy-grant context where it's defensible) — both deliberate, to avoid the crowding the
  owner objected to. The Session idea proposes a guard instead.
- **One docs/tooling change that would help:** the guard below.

## 📤 Run report

- **Did:** corrected "Merge = deploy" at the canonical doc + binding CLAUDE.md line + router Q-0193 +
  journal · **Outcome:** shipped (PR #1247, docs-only, auto-merge on green)
- **Shipped:** #1247 — "Merge = deploy" clarity (Q-0193)
- **Run type:** `manual`
- **CI:** `check_quality.py --check-only` green (black/isort/ruff/check_docs/check_consistency); docs-only,
  no mypy/pytest impact.
- **⚑ Owner decisions needed:** none (owner-directed correction).
- **⚑ Owner manual steps:** none — and that is the whole point: **this PR auto-deploys on merge like any
  other; nothing for you to restart or deploy.**
- **⚑ Self-initiated:** none (direct owner directive). The router Q-0193 + journal note are the
  durable-home parts of the same directive.
- **↪ Next:** optional — the regression guard in the Session idea.

## 💡 Session idea

**A banned-phrase guard for the "Merge = deploy" canon.** Now that Q-0193 makes "Merge = deploy" the
canonical statement, add a tiny `check_docs`/`check_consistency` rule (or a `scripts/` grep guard) that
**fails CI if a tracked doc or a new `.sessions/*` card reintroduces** "Merge ≠ deploy", "restart is
yours", or "prod restart stays the maintainer's" *without* naming a concrete per-PR data step. It would
have caught my #1245 card at write time — the exact surface the misinformation spreads through — and
keeps the fix from silently regressing as cards keep getting copied. Cheap (one regex over `docs/` +
`.sessions/`), warn-then-error like the consistency linter. Dedup-checked `docs/ideas/` — not captured
(the closest, `settings-presets`, is unrelated).

## ⟲ Previous-session review

The previous session (`2026-06-21-role-presets-and-management-ux.md`, #1245) — my own — did the
four-thread role overhaul well and caught two real issues locally via `--full` before pushing. **What it
got wrong:** its run report's `⚑ Owner manual steps` line said "Merge ≠ deploy: the prod restart stays
yours" — copied uncritically from the prior reaction-roles card, and *factually wrong* (Railway
auto-deploys). That single stale-by-copy line is what prompted this whole session. **System improvement:**
exactly the banned-phrase guard above — the session-card `⚑ Owner manual steps` line is a high-traffic
copy surface, and a one-line CI check there stops a wrong operational claim from propagating across dozens
of cards. The self-audit loop worked as designed: session N+1 caught session N's drift.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 0 (pending #1247, auto-merge on green) |
| CI-red rounds | 0 real (born-red HOLD only, by design) |
| Repo-rule trips | 0 |
| New ideas contributed | 1 (banned-phrase "Merge = deploy" guard) |
| Ideas groomed | 0 (focused owner-directed correction) |
