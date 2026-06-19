# 2026-06-19 — Repo structure: governance + supply-chain + CI baseline

> **Status:** `complete`

## Arc

Owner uploaded three external repo-review reports (two Dutch research passes + a Markdown review
reconciling them) and asked for **a comprehensive plan to improve the repo structure**. Cross-checked
every recommendation against live source + recorded owner decisions (the reports are *input to verify*,
never orders — and a prior structure review already settled the code-layout question: **no filesystem
reorg**, Q-0151). The genuine remaining gap is the **outward-facing governance / supply-chain /
operational** layer. Owner chose in-session (`AskUserQuestion`): **LICENSE = MIT**, scope = **plan +
docs + CI config** (greenlighting the `.github/` executable-config changes — the CLAUDE.md Q-0106
exception; provenance **Q-0177**).

## Shipped (PR #1064)

- **The plan:** [`planning/repo-structure-improvement-plan-2026-06-19.md`](../docs/planning/repo-structure-improvement-plan-2026-06-19.md)
  — a verification table (each report claim → live finding → *already-shipped* / *deliberately-decided*
  / *genuine-gap*), a prioritized P0–P3 backlog, routed decisions, S5 roadmap slot.
- **Governance foundation:** `LICENSE` (MIT), `SECURITY.md`, `CONTRIBUTING.md`, `CITATION.cff`.
- **Supply-chain / CI:** `.github/dependabot.yml` (pip root + dashboard + actions), `codeql.yml`
  (Python SAST, non-blocking), `dashboard-ci.yml` (runs the previously-skipped `tests/unit/dashboard/`
  + `mypy dashboard/`), `.github/ISSUE_TEMPLATE/` + `PULL_REQUEST_TEMPLATE.md`.
- **Root-fixed bug** (surfaced wiring dashboard CI): fresh install pulled `httpx 0.28`, which persists
  per-request `cookies=` into the shared module-scoped `TestClient` → a login cookie leaked into the
  later "requires-login" tests (63 pass / 2 fail). Made the `client` fixture function-scoped
  (`tests/unit/dashboard/test_app.py`) → **65 pass**, `mypy dashboard/` clean. A live demo of the
  dependency-pin gap the plan flags.
- **Routed (Q-0177):** dependency-lock strategy · control-API hardening · pointer-README (Q-0151b) ·
  roadmap→labeled-issue mirror. **Owner manual steps:** enable Dependabot alerts/security-updates +
  private vuln reporting; optionally make codeql/dashboard-ci required; confirm MIT copyright name.

Verification: `check_quality.py --full` ✓ (10704 passed) · `check_architecture --mode strict` exit 0 ·
`check_docs --strict` ✓ · dashboard suite 65 pass.

## Continuation (the handoff)

The first buildable follow-up is the **P1 dependency-lock plan** (Q-0177 option a — `pip-tools`
lockfile for the dashboard first, then the bot), which would make the `httpx 0.28`-class break
impossible. After that: the backup *restore* drill (P2) and SHA-pinning Actions (pairs with Dependabot).
Control-API hardening (P2) waits on the owner (write-surface "don't rush" zone).

## Context delta

- **Needed but not pointed to:** that `scripts/check_docs.py` scopes **`docs/**` only** — root
  governance files (`LICENSE`/`SECURITY.md`/`CONTRIBUTING.md`/`CITATION.cff`) are entirely outside its
  badge/link/reachability checks. Had to read the checker to confirm root files need no `Status:` badge.
  Also the born-red ↔ auto-merge ↔ Q-0127 (MCP PR doesn't trigger the enabler) interplay is spread
  across several CLAUDE.md bullets — a single "opening a PR from a session" checklist would help.
- **Pointed to but didn't need:** the `current-state.md` ▶ Next action mega-paragraph — enormous and
  almost entirely S1/S2 bot-product lane history; near-zero signal for a governance/ops task. The
  roadmap S5 lane + the architecture-atlas capture carried the orientation.
- **Discovered by hand:** the httpx ≥0.28 per-request-cookie-persistence behavior change (reverse-engineered
  from the failure + deprecation warning); and that dashboard Python is *already* black/isort/ruff-checked
  by the main job (it's not in their exclude list), so the real CI gap was only test-execution + `mypy`.

## Decisions made alone (ratify or correct)

- **LICENSE copyright holder = "Menno van Hattum"** (derived from the owner email). Flagged in Q-0177 +
  as an owner manual step — trivial to correct.
- **CodeQL query suite = `security-extended`** (security-focused, no quality noise; dial-able in the workflow).
- **`dashboard-ci.yml` as a separate `paths`-filtered workflow** (not a second job in `code-quality.yml`)
  — isolates dashboard concerns + only runs on dashboard changes. Non-required until the owner opts in.

## Flagged for maintainer (known limits)

- `codeql.yml` + `dashboard-ci.yml` are **not required checks** until added to branch protection — a
  future dashboard test break would not block a merge yet (owner manual step in Q-0177).
- CodeQL's **first run may surface findings** to triage (Security → Code scanning).
- Dashboard deps are **still version ranges** — the lockfile decision is routed (Q-0177 P1.1), not done;
  `dashboard-ci` is the early-warning net until then. The per-request-cookies **deprecation warnings**
  remain (a larger test-modernization is a deferred follow-up).

## ⟲ Previous-session review (Q-0102)

Previous session: [`2026-06-19-consistency-back-button-triage.md`](2026-06-19-consistency-back-button-triage.md)
(#1059). **Did well:** exemplary Q-0120 discipline — it traced all 7 `back_button` findings to their
construction sites rather than trusting the plan's prediction, and correctly concluded "allowlist, not a
code change" without manufacturing a fix. **Could improve / system observation:** it's the 4th in a chain
of single-rule micro-triage sessions (#1056/#1057/#1058/#1059) that each rewrite the same files —
including the **enormous `current-state.md` ▶ Next action paragraph**, which self-warns about parallel-merge
collisions. The unexecuted `repo-manageability-2026-06-12` idea #2 (cap + auto-archive Recently-shipped,
break the mega-header into per-lane bullets) would directly cut that per-session friction. **System
improvement:** that idea is overdue — every micro-session pays the mega-header tax; promoting it to a small
plan would pay back across the whole session chain. (I felt the same tax this session — see Context delta.)

## 💡 Session idea (Q-0089)

**Contributor-doc / governance-files presence + freshness guard** —
[`ideas/governance-files-presence-guard-2026-06-19.md`](../docs/ideas/governance-files-presence-guard-2026-06-19.md).
A tiny stdlib `scripts/check_governance_files.py` asserting the new root files stay present **and** that
the repo paths cited in `CONTRIBUTING.md`/`SECURITY.md` still resolve — `check_docs` scopes `docs/**`
only, so these are unguarded, and the *first thing a new contributor runs* is the commands those docs
cite. "Executable verification over prose" applied to the governance layer. Dedup-checked; worth having.

## 📊 Doc audit (Q-0104)

- Plan in `docs/planning/` ✓ · idea in `docs/ideas/` + README index ✓ · decision in router **Q-0177** ✓ ·
  roadmap **S5** entry ✓ · session card ✓ — all homed + reachable (`check_docs --strict` green).
- **Ledger:** the SessionStart banner + `check_current_state_ledger --strict` flag #1053/#1055/#1060/#1061
  — all **newer than the recon marker #1050**, i.e. the "newest-merge lag → next pass records" exception
  (Q-0166), and already deferred by #1058/#1059 to the **#1080 reconciliation pass**. Not this session's
  drift; not added here (Q-0124 — a manual session pursues its task, not the docs pass).
- My PR #1064 records into the ledger after it merges (the next recon pass / a follow-up), not pre-merge.

## 📤 Run report

- **Did:** shipped the outward-facing governance + supply-chain + CI baseline (license/security/contributing
  + Dependabot/CodeQL/dashboard-CI + templates) + the comprehensive plan, and root-fixed a dashboard test
  bug en route. · **Outcome:** shipped
- **Shipped:** #1064 — LICENSE/SECURITY.md/CONTRIBUTING.md/CITATION.cff · `.github/dependabot.yml` ·
  `codeql.yml` · `dashboard-ci.yml` · issue/PR templates · the plan + router Q-0177 + roadmap S5 · the
  `httpx 0.28` test-isolation fix.
- **Run type:** `manual`
- **⚑ Owner decisions needed:** **Q-0177** — dependency-lock strategy · control-API hardening depth/timing
  · pointer-README go/no-go (Q-0151b) · roadmap→labeled-issue mirror (agent rec: don't adopt GitHub
  Projects wholesale).
- **⚑ Owner manual steps:** enable **Dependabot alerts + security updates** + **private vulnerability
  reporting** (Settings → Code security) · optionally add **codeql** + **dashboard-ci** to required checks ·
  confirm the **MIT copyright holder** name in `LICENSE`.
- **⚑ Self-initiated:** `none` (owner-directed task; the dashboard test fix was an in-scope bug surfaced by
  the dashboard-CI work, not an unprompted feature build).
- **↪ Next:** the Q-0177 routed decisions; first buildable = the **P1 dependency-lock plan** (`pip-tools`
  lockfile, dashboard first).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1064, auto-merge on green) |
| CI-red rounds | 1 (born-red session gate by design) |
| Repo-rule trips | 0 (arch strict exit 0; quality --full green first try) |
| New ideas contributed | 1 (governance-files presence guard) |
| Ideas groomed | 1 (gap-analysis §6 toolchain-rot-watch → closed by Dependabot; backup restore-drill routed) |
