# 2026-07-12 — Hub upkeep: stale rebuild pointers in current-state docs

> **Status:** in-progress
> **Branch:** `claude/hub-upkeep-2026-07-12` · **PR:** pending
> **Venue:** remote container (worker session, orchestrated). **📊 Model:** Fable 5 (Claude 5 family).
> **Scope:** docs-only upkeep — three stale rebuild pointers in the current-state band, verified
> by a completed audit at HEAD `87bbe1d`, cross-checked against superbot-next `origin/main@33d3073`.

## Arc

Audit (done upstream) found three places where the hub's current-state docs still describe the
rebuild as gated/idea-stage, contradicting this repo's own S3 record (gates RETIRED by
Q-0241/#1776, 2026-07-07) and the live superbot-next repo (50/51 parity rows ported per
`parity/parity.yml@33d3073`). This session implements exactly those three corrections:

- **Fix A** — `docs/current-state/S4-docs.md` ~L255: "Still behind the G1 owner gate; no new-repo
  code yet" → gates retired + rebuild LIVE in superbot-next.
- **Fix B** — `docs/current-state/S4-docs.md` ~L271–273: 2026-06-30 owner steer re-badged as
  **historical/superseded** (not deleted) with a note on what shipped since.
- **Fix C** — `docs/current-state.md` L67 (S3 sector-table row): stale "▶ next: the FOUR program
  sessions — launch index READY" tail (all four ran days ago) → rebuild-LIVE pointer with the
  07-13 brief §3 + canonical plan as plan of record. Leading sector/status cells untouched.

## Shipped

- (pending flip) the three doc corrections above, quality-mirror green.

## Findings

- Evidence for A: `docs/current-state/S3-ai-memory.md:198` ("RETIRED by Q-0241/#1776
  (2026-07-07)") and `docs/current-state.md:67`.
- Evidence for B: kit v1.0.0 extraction (#1878–#1884 per S4's own Recently-shipped entry);
  superbot-next `control/status.md@33d3073` pins kit v1.15.0.
- Evidence for C: `.sessions/2026-07-09-*` founding cards + the round-3 arc #1953…#1978;
  superbot-next `parity/parity.yml@33d3073`.

## Session enders

- **Context delta:**
  - needed-but-not-pointed-to: none — the audit handed this session exact file/line targets.
  - pointed-to-but-unneeded: none.
  - discovered-by-hand: `owner/next-session-brief-2026-07-13.md` lives under `docs/owner/`;
    current-state.md's link convention is relative to `docs/` (`owner/...`, `planning/...`).
- **Decisions made alone:** kept Fix B's original bullet text intact under the historical badge
  (re-badge, don't rewrite) per the audit's instruction; used `docs/`-relative link forms in
  Fix C to match the file's existing convention.
- **Flagged for maintainer:** `control/status.md` heartbeat drift (37/49 figure, "43rd recon
  pass", #1999/#2003 pointers) is also stale but **deliberately left untouched** — that file
  belongs to the hub seat.
- **🛠 Friction → guard (Q-0194):** none.

## 📤 Run report

- **Did:** implemented the three audited corrections to stale rebuild pointers in
  `docs/current-state.md` + `docs/current-state/S4-docs.md`. **Outcome:** pending (flips with
  Status → complete once the quality mirror passes).
- **Shipped:** Fix A/B/C above; this card.
- **Run type:** orchestrated docs-only upkeep (worker seat), decide-and-flag.
- **⚑ Owner decisions needed:** none.
- **⚑ Owner manual steps:** none.
- **⚑ Self-initiated (Q-0172):** none beyond link-form/badge micro-choices noted under
  "Decisions made alone" — scope was fully specified by the audit.
- **↪ Next:** hub seat picks up the `control/status.md` heartbeat drift flagged above.

## 📊 Telemetry

| PRs merged | CI-red rounds | rule trips | ideas contributed | ideas groomed |
|---|---|---|---|---|
| 0 (1 opened, auto-merge path) | 0 | 0 | 0 | 0 |
