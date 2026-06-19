# Repo-structure improvement plan — governance, supply-chain & operations baseline

> **Status:** `plan` — prioritized improvement program derived from three owner-uploaded
> external reviews, **cross-checked against live source** (2026-06-19). **Not blanket
> implementation approval.** Source code and merged PRs win over this doc. Owner decisions
> for this plan are recorded as **Q-0177** in
> [`docs/owner/maintainer-question-router.md`](../owner/maintainer-question-router.md).

## What this is

The owner uploaded three external repo reviews — two Dutch research passes (one with no repo
access, one with live access) and a Markdown review reconciling them — and asked for **a
comprehensive plan to improve the repo structure**. Per `.claude/CLAUDE.md`, an external review
is *input to verify against shipped source, never an order*. Every recommendation below was
checked against live source before being kept, reframed, or dropped.

### Headline verdict

The reviews' **direction is correct on one axis and already-settled on another**:

- **Code/directory structure** — the reviews (especially the earlier *architecture-atlas*
  review) already drove a decision: **keep the modular monolith; do not reorganize the tree.**
  `src/` layout, feature-package migration, and a big reorg were all evaluated and **rejected**
  (the answer is "a better lens — generated facts/drift checks — not a reorg"). See
  [`docs/ideas/architecture-atlas-and-structure-review-2026-06-16.md`](../ideas/architecture-atlas-and-structure-review-2026-06-16.md)
  and Q-0151. **This plan does not touch the directory layout.**
- **Outward-facing governance / supply-chain / operations** — this is the **genuine gap** and
  the subject of this plan. The repo is exceptionally strong on *internal* docs/planning
  machinery (roadmap, ideas backlog, current-state ledger, reconciliation passes, production
  readiness maps) but thin on the *external* OSS-hygiene + supply-chain + CI-parity layer.

The reviews also recommend a few things the repo **deliberately decided against** (a mandatory
root README; moving planning into GitHub Issues/Projects). Those are reframed below, not adopted
blindly — the repo's deliberate posture (docs-first; the developer dashboard as the planning
surface) is the verified ground truth.

## Verification table — every recommendation vs. live source

| Review recommendation | Live finding (2026-06-19) | Verdict |
|---|---|---|
| Add a `LICENSE` | **Absent.** Repo is "all rights reserved" — no legal reuse. | **Genuine gap → SHIPPED this session** (MIT, owner Q-0177). |
| Add `SECURITY.md` | **Absent.** Bot has a token-gated control API + secrets; no disclosure path. | **Genuine gap → SHIPPED.** |
| Add `CONTRIBUTING.md` | **Absent.** Agent-first repo with no human on-ramp. | **Genuine gap → SHIPPED** (bridges humans into the agent workflow). |
| Add `CITATION.cff` | **Absent.** | Minor gap → **SHIPPED** (trivial, owner picked full scope). |
| Add a root `README` | **Intentionally absent** (`repo-navigation-map.md`: "docs/ is the documentation surface"); owner Q-0151b = *optional 5-line pointer, not built now*. | **Deliberately decided → routed, not forced** (ready 5-line pointer in Q-0177 for owner's call). |
| Enable Dependabot | **No `.github/dependabot.yml`.** Runtime deps are version *ranges*; no freshness watch. | **Genuine gap → SHIPPED** (also closes gap-analysis §6 toolchain-rot-watch). |
| Enable CodeQL / code scanning | **No SAST workflow.** | **Genuine gap → SHIPPED** (`codeql.yml`, non-blocking). |
| Pin runtime deps / lockfile | **Confirmed:** `requirements.txt` + `dashboard/requirements.txt` use ranges; only `requirements-dev.txt` is pinned. **Live proof:** a fresh dashboard install resolved `httpx 0.28` and broke 2 tests this session (see below). | **Genuine gap → ROUTED** (strategy decision, Q-0177). |
| Run dashboard tests in CI | **Confirmed:** `code-quality.yml` installs only the bot's `requirements.txt`, so `tests/unit/dashboard/` `importorskip` and **skip**; dashboard is never type-checked. | **Genuine gap → SHIPPED** (`dashboard-ci.yml`). |
| Issue forms + PR template | **Absent** (`.github/` had only `workflows/`). | **Gap → SHIPPED** (config keeps planning in docs by design). |
| Mirror planning into GitHub Issues/Projects | **Deliberate:** planning lives in `docs/` + the developer dashboard (the chosen surface; a public bug form + GitHub-issue mirror are already planned). | **Reframed → do NOT adopt GitHub Projects naively.** Optional lightweight roadmap→labeled-issue mirror only (P3). |
| Harden the control API (HMAC, idempotency, token rotation) | Real defense-in-depth exists (dormant-by-default, bearer token, rate limiter, bot re-resolves authority); the named hardening is **not yet a dedicated plan**. | **Genuine gap → ROUTED** (owner-paced; control-API writes are the owner's "don't rush" zone). |
| Test backup/restore | **Backup *integrity* check shipped** (`backup-db.yml` CREATE TABLE-count gate, idea `backup-integrity-check-2026-06-13`). A *restore drill* is **not** done. | **Partially shipped → restore-drill ROUTED** (P2). |
| Declarative `INITIAL_EXTENSIONS` registry | The 43 extensions are **already classified** (extension-taxonomy crosswalk, PR #958, CI-guarded). A phase/dependency *load* registry is a further step. | **Mostly addressed → narrow follow-up** (P3, low priority). |
| Reorganize the tree / `src/` layout / feature packages | **Already evaluated and rejected** (Q-0151; modular monolith kept). | **Endorse the rejection — no action.** |
| Add `CHANGELOG.md` / SemVer releases | The living `current-state.md` ledger + reconciliation passes serve as the change record; the bot is **continuously deployed** (merge→Railway), so SemVer releases are low-value. | **Reframed → not adopted** (note in plan; revisit only if the substrate-kit is published as a package). |

## Shipped this session (PR for branch `claude/focused-goldberg-mviel4`)

**Governance foundation** (root, free-rein docs + owner-greenlit): `LICENSE` (MIT), `SECURITY.md`,
`CONTRIBUTING.md`, `CITATION.cff`.

**Supply-chain / CI** (`.github/`, owner-greenlit in-session under the Q-0106 exception, Q-0177):
- `.github/dependabot.yml` — weekly pip (root + `dashboard/`) + github-actions version updates.
- `.github/workflows/codeql.yml` — Python SAST, weekly + on PR, non-blocking.
- `.github/workflows/dashboard-ci.yml` — installs both dep sets, runs `tests/unit/dashboard/`
  (previously skipped) + `mypy dashboard/` (previously unchecked).
- `.github/ISSUE_TEMPLATE/` (bug + feature forms + chooser config) + `.github/PULL_REQUEST_TEMPLATE.md`.

**Root-fixed bug surfaced while wiring dashboard CI** (a live demonstration of the dependency-pin
gap): on a fresh install the dashboard suite was **63 pass / 2 fail**. `httpx>=0.28` now *persists*
per-request `cookies=` into the shared module-scoped `TestClient`, so an earlier login test's cookie
leaked into the later "requires-login" assertions (→ 200 instead of a redirect). Fixed by making the
`client` fixture function-scoped (`tests/unit/dashboard/test_app.py`) → **65 pass**, `mypy dashboard/`
clean. This is exactly the class the dashboard CI job now guards against.

## Prioritized backlog (the work beyond this session)

Batched into the repo's 2–3-PR plan convention. Impact/effort are relative; "route" names the gate.

### P0 — governance & legal (highest leverage, lowest risk) — ✅ done this session
LICENSE / SECURITY / CONTRIBUTING / CITATION. *Owner manual follow-ups* (repo Settings, can't be done
from a PR): enable **GitHub private vulnerability reporting**; confirm the MIT copyright holder name.

### P1 — supply-chain & CI parity — mostly done this session; two follow-ups
1. **Dependency reproducibility (ROUTED, Q-0177).** Adopt a constraints/lock strategy so fresh
   installs don't drift (the `httpx 0.28` break is the worked example). Options in Q-0177:
   (a) `pip-tools` compiled `requirements.lock` for bot + dashboard; (b) tighten the existing ranges
   to known-good ceilings; (c) keep ranges + rely on Dependabot + the new dashboard CI as the
   early-warning net. *Recommendation:* (a) for the dashboard first (it deploys separately and just
   broke), then the bot. **2-PR plan** once the option is chosen.
2. **Make the new checks *required* + enable Dependabot security updates (owner manual step).**
   `codeql` and `dashboard-ci` are non-blocking until the owner adds them to branch protection;
   Dependabot *alerts + security updates* are a repo-Settings toggle. Listed in Q-0177.

### P2 — operational hardening (owner-paced)
1. **Control-API hardening (ROUTED, Q-0177)** — request signing (HMAC + timestamp), idempotency keys
   on writes, token rotation. Sequence behind the dashboard live-editor write lane (same owner "don't
   rush" zone). **1–2 PR plan** when greenlit.
2. **Backup *restore* drill** — extend `backup-db.yml` (integrity check already shipped) with a
   scheduled restore-into-throwaway-Postgres verification + a recovery runbook. Builds on idea
   `backup-integrity-check-2026-06-13`. **1 PR.**
3. **SHA-pin third-party Actions** — current convention is major-tag pins; SHA-pinning is the
   supply-chain hardening the reviews flag. Pairs naturally with Dependabot (which can bump SHAs).

### P3 — polish / optional
1. **Optional 5-line pointer README** (Q-0151b) — owner pre-blessed as optional; ready text in Q-0177.
2. **Lightweight roadmap→labeled-issue mirror** — *only if* the owner wants public visibility; the
   dashboard remains the primary planning surface (do not adopt GitHub Projects wholesale).
3. **Declarative extension load registry** — phase/dependency metadata for `INITIAL_EXTENSIONS` on top
   of the existing taxonomy crosswalk (low priority; ordering works today).
4. **Contributor-doc freshness guard** — see the session idea
   [`docs/ideas/governance-files-presence-guard-2026-06-19.md`](../ideas/governance-files-presence-guard-2026-06-19.md).

## Routed owner decisions & manual steps (Q-0177)

**Decisions** (in the router): dependency-lock strategy (P1.1); control-API hardening depth/timing
(P2.1); pointer-README go/no-go (P3.1); whether to mirror the roadmap to labeled issues (P3.2).

**Owner manual steps** (off-repo / repo-Settings — cannot be done from a PR):
1. Enable **Dependabot alerts + security updates** (Settings → Code security).
2. Enable **private vulnerability reporting** (Settings → Code security) so `SECURITY.md` route 1 works.
3. Optionally add **`codeql`** and **`dashboard-ci`** to **branch protection / required checks**.
4. Confirm the **MIT copyright holder** name in `LICENSE` (currently "Menno van Hattum").

## Sector placement & metrics

Homed under roadmap **S5 — Operations / control-plane** (with a governance facet) — see
[`docs/roadmap.md`](../roadmap.md). Acceptance for the program: a fresh clone has an unambiguous
license + disclosure path; dependency updates and SAST findings surface automatically; dashboard
tests + types are enforced; and dependency installs are reproducible. This session clears the first
three; reproducibility is the routed P1 follow-up.

## Builds on (existing captures — not duplicated)

[`architecture-atlas-and-structure-review-2026-06-16`](../ideas/architecture-atlas-and-structure-review-2026-06-16.md)
(no-reorg decision) · [`hardening-roadmap-2026-06-12`](production-readiness/hardening-roadmap-2026-06-12.md)
(production-risk backlog) · [`gap-analysis-2026-06-11`](../ideas/gap-analysis-2026-06-11.md) (toolchain-rot
watch, data export/erasure) · [`repo-manageability-2026-06-12`](../ideas/repo-manageability-2026-06-12.md)
· `backup-integrity-check-2026-06-13`.
