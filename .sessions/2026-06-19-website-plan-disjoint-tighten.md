# 2026-06-19 — Pre-ultracode: make the website-plan §5 decomposition truly file-disjoint

> **Status:** `complete`

## Arc

The owner is about to dispatch the website two-site-split plan (`website-two-site-split-plan-2026-06-19.md`)
to an **ultracode** parallel build fleet and asked what to clear up first. A parallel fleet can't
coordinate at the file level — file-disjointness *is* the mechanism — so §5 was reviewed for collisions.

## Findings (the plan promised "exclusive file sets" but violated it)

- **`botsite/app.py` claimed by three "parallel" units** (P1 skeleton, P2 reference-page routes, P4
  `/submit` route) — guaranteed write collision, hedged with "if P1 lands a thin shell / otherwise fold."
- **`scripts/export_dashboard_data.py` claimed by two** (S1 subset emitter, P3 changelog parse) — hedged
  "coordinate with S1 or fold."
- **Unresolved either/ors a fleet can't pick:** S2's module shape (`dashboard_db/` *or* per-service
  helpers), P4's rate-limiter ("copy *or* shared import").
- **`site.json` whitelist not pinned to exact keys** → S1's redaction guard would be non-deterministic.
- A latent `botsite/README.md` double-claim (P1 + P8).

## Fix (shipped — §5 rewrite)

- **Single-owner files:** S1 owns `export_dashboard_data.py` end-to-end (subset emitter **+ the
  bot_changelog parse** + `site.json`); **P1 owns `botsite/app.py` and wires ALL routes up front**, so no
  back-half unit edits it. Moved P1 into the **serial foundation** (S1 → {S2, P1} → parallel P2–P8).
- **Back half now truly disjoint:** P2/P3 own only templates; P4 owns `botsite/submit.py` (fills P1's
  stub router) + `ratelimit.py` (pinned: **copy**, no shared import) + `submit.html`; P5 dev-site
  moderation; P6 `github_mirror.py`; P7 the redaction-audit doc only; P8 a new `botsite-deploy.md` +
  env-vars (P8 no longer touches `botsite/README.md`).
- **S2 pinned:** one DDL/migration + two independent helpers (`botsite/submissions_db.py` INSERT-only,
  `dashboard/submissions_db.py` SELECT/UPDATE) sharing only the table contract, not code.
- **`site.json` whitelist pinned** to exact top-level keys (meta/counts/catalogue/commands/bot_changelog).
- **Build-without-live-infra** note added: every unit builds code+tests against a test DB + mocked GitHub;
  owner provisions Railway/Postgres/token at rollout — so no unit blocks on infra.

## Context delta

- The plan is now genuinely dispatchable to a parallel fleet: serial `S1 → {S2, P1}`, then 7 file-disjoint
  back-half units. The remaining owner-side items are **not build blockers** — provisioning at rollout, and
  the (deferred, security-review-gated) control-panel→3rd-service decision, which is out of the first wave.

## 📤 Run report

- **Did:** pre-ultracode review of §5; folded the `app.py` (×3) and `export_dashboard_data.py` (×2)
  collisions into single owners, pinned the S2 module shape / rate-limiter / `site.json` whitelist, added a
  build-without-infra note. · **Outcome:** shipped — the decomposition is now truly file-disjoint.
- **Run type:** `manual` (owner question → readiness fix).
- **⚑ Self-initiated:** the §5 tightening — contained, reversible plan edit that makes the doc honor its own
  "exclusive file set" contract; flagged here for review.
- **↪ Next:** dispatch §5 to ultracode — serial `S1 → {S2, P1}`, then parallel `P2–P8`.
