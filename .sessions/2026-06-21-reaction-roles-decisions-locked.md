# 2026-06-21 — Reaction-roles plan: owner decisions locked + analytics added

> **Status:** `complete` — follow-up to #1215/#1216/#1217. Owner answered the four open design
> forks (via the question panel) and accepted a new addition. Recorded the decisions in the plan
> so it's fully specified. Docs-only → self-merge on green.

> **Run type:** `manual`

## Arc

Owner answered all four §9 forks (all matched the recommendations):
1. **Surface priority → in-Discord first**, web builder later.
2. **Default menu style → dropdown** (both supported).
3. **Free temp roles → build it** (beats Carl's Patreon gate) — promoted to PR 4.
4. **Role-pickup analytics → yes** (my proposed addition) — added as §10 / PR 5.

Rewrote plan §9 from "open questions" → "Decisions LOCKED (2026-06-21)" with an updated PR map
(core arc PR 1–3 + waves PR 4 temp roles, PR 5 analytics, PR 6 optional PIL, Surface A web), added
§10 (analytics: aggregate pickup counts + archive-nudge in Diagnostics, nearly free on the audited
seam, a Carl differentiator), and reconciled the old "temp = stretch" bullet to "PR 4 decided".

## 📤 Run report

- **Did:** locked the owner's four design decisions into the plan + added the role-pickup analytics wave · **Outcome:** shipped (plan now fully specified)
- **Shipped:** #1218 — lock decisions + add analytics (docs-only)
- **Run type:** `manual`
- **⚑ Owner decisions needed:** none — all four forks resolved. Remaining is a go/hold on starting the build.
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (the analytics addition was proposed and owner-accepted in-session)
- **↪ Next:** build **reaction-roles PR 1** (audited `reaction_role_service` + migration 078) — fully unblocked, no pending decisions; then PR 2 (in-Discord dropdown builder + edit/themes/templates)

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 3 (#1215, #1216, #1217); 1 pending (#1218) |
| CI-red rounds | 0 |
| Repo-rule trips | 0 |
| New ideas contributed | 1 prior (channel-deployed primitive); analytics folded into the plan |
| Ideas groomed | 0 |
