# 2026-06-19 — Website split: owner identity vision + fan-out enablers

> **Status:** `complete`

## Arc

Foundation S1+S2+P1 merged (#1109). Before launching the parallel back-half fan-out, the owner gave the
binding **site identity + experience vision** and a standing **correctness/centralization mandate**. This
PR folds the vision into the plan (so the fan-out builds to it), adds the missing bot-site CI, and captures
the centralization design the mandate asks for. Non-overlapping with the (now-merged) foundation agent.

## Shipped (this PR)

- **Site identity & experience — binding brief** added to the plan (owner's words):
  - Positioning: all-in-one — *"Add SuperBot and you can remove every other bot from your server."*
  - Feel: fun-but-professional, simple, self-explanatory, browsable in seconds.
  - **Interactive command reference:** every command is clickable → detail (use-cases · aliases ·
    permissions · examples · **notes** · **status finished/in-progress** · **linked ideas**).
  - **Discoverability:** project the repo's real commands ↔ aliases ↔ ideas ↔ status, linked by
    cog/command, into a safe navigable shape (redaction lens still applies).
- **Plan §5 reshaped for the vision:** new unit **S1.1** (enrich `site.json` per-command data — description/
  use-cases, `status`, `linked_ideas`, `notes`; each from a real source, redaction-whitelisted fail-closed,
  with the ambiguous derivations flagged as open decisions + recommendations). **P2** reshaped from a static
  table → the **interactive command + feature browser**. Dep graph updated (`S1.1 → P2`; foundation merged).
- **`.github/workflows/botsite-ci.yml`** (additive twin of `dashboard-ci.yml`): runs `tests/unit/botsite/`
  + `mypy botsite/`, so the bot-site tests actually execute in CI instead of `importorskip`-skipping (the
  gap from the fastapi-install discussion) — and the fan-out PRs get real CI.
- **`docs/planning/web-tier-centralization-proposal-2026-06-19.md`** (the centralization mandate): designs
  one `web-ci.yml` matrix (dashboard + botsite) to replace the two per-service files, and the PR-machinery
  de-duplication (single source of truth for the "auto-managed PR" predicate, optional unified PR-sync
  sweep preserving the #1106 race fix). Deliberately deferred to focused follow-up PRs — correctness-first,
  don't churn working CI in a bundle.

## Context delta

- The owner's vision is **not just copy** — it extends the *data contract*: the interactive browser needs
  enriched per-command data (status, linked ideas, notes), so S1.1 (a producer + whitelist extension) is a
  new prerequisite for P2. Folding it in *before* the fan-out means the back-half builds the right thing.
- Correctness/centralization mandate applied honestly: I added the **safe additive** `botsite-ci.yml` now
  and **designed** (didn't rush) the `web-ci.yml` matrix + PR-machinery de-dup — because the things to
  centralize are working CI/merge plumbing.

## 📤 Run report

- **Did:** folded the owner's binding site-identity/experience vision into the plan; reshaped §5 (added
  S1.1 data-enrichment unit, made P2 the interactive browser); added `botsite-ci.yml`; wrote the web-tier +
  PR-machinery centralization proposal. · **Outcome:** shipped.
- **Run type:** `manual` (owner go-ahead + vision).
- **⚑ Self-initiated:** `botsite-ci.yml` (closes a real CI gap the foundation missed) + the centralization
  proposal (owner mandate) — both flagged for review.
- **⚑ Owner decisions surfaced (S1.1):** `status` derivation source · idea→command linking method ·
  per-command notes source — each with a recommended default; the build run defaults them unless owner says.
- **↪ Next:** (1) a focused PR 2 — control-panel architecture lock (router Q-0179 + plan §7.4) + the rollout
  & control-API-security-review ops checklists; (2) then **launch the fan-out** — S1.1 → P2 (interactive
  browser) ∥ P3–P8 — once this enabler PR is merged.
