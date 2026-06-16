# Session — dashboard finalized-state vision (synthesize report + Codex PR 998 → one north-star plan)

> **Status:** `in-progress`

## What I'm about to do (born-red declaration, Q-0133)

Owner uploaded a deep-research report (`f53d0b97-deepresearchreport1.md`, Dutch) and asked me to review
it **plus Codex's PR #998**, compare both to what the repo already has, **filter the good ideas**, and
turn the result into **one comprehensive plan document that envisions the finalized state of the website
and the bot's configuration capabilities**. Close PR #998 once its material is captured; route any
genuine open questions to the doc / the question router.

- **Finding:** both the report and PR #998 are independent external reviews that largely *re-derive*
  conclusions the repo already reached in two existing plans — `developer-dashboard-plan.md` (live record
  + near-term roadmap) and `dashboard-live-editor-plan.md` (the L0–L3 build sequence). What's genuinely
  **missing** is a single **north-star vision** doc tying the zones, the navigation model, the full
  config-capability map, the data/freshness architecture, the **manifest spine**, and the security-ring
  model into one finalized-state picture. That is the deliverable.
- **Plan:** write `docs/planning/dashboard-vision-finalized-state.md` as the umbrella vision the two
  existing plans become execution tracks under (no parallel source of truth — heavy cross-links, defer
  execution detail to them). Link it from both plans (guarantees `check_docs --strict` reachability).
  Route the genuinely-open architectural forks (manifest-spine go/no-go; owner-zone future scope) to the
  router as **Q-0161**, with safe defaults captured in the doc for every open question.
- **Then:** close Codex PR #998 with a courteous reason (superseded; its useful material — the
  route-trust inventory, the manifest JSON schema, the readiness table — folded into the new doc).

Docs-only; no `disbot/` runtime, no auth, no mutations.

## What shipped

_(filled in at close)_
