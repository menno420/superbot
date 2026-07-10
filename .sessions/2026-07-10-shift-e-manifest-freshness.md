# 2026-07-10 — fleet-manifest freshness checker (overnight shift, session E)

> **Status:** `complete`
> **Branch:** `claude/shift-e-manifest-freshness` · **PR:** #1923

**Intent:** shift-plan item **K4** — `scripts/check_manifest_freshness.py`, an
advisory checker comparing each `docs/eap/fleet-manifest.md` row's Last-seen cell
against the lane repo's `control/status.md` `updated:` header. **Design decision
(decide-and-flag):** the network half uses **git transport** (shallow
`git fetch --depth 1` + `git cat-file`), NOT the GitHub REST API the idea file
named — the REST API is proxy-blocked in agent containers ("GitHub access is not
enabled for this session", verified live this session) while git is
authenticated, so an API-based checker would fail in exactly the environment the
reconciliation routine runs it in. Mechanism live-verified against
menno420/fleet-manager before building. Fail-open on any network error (row →
SKIP, exit 0); NOT CI-wired (Q-0105 advisory header). Plus one checklist line in
`docs/operations/autonomous-routines.md` and the idea-file re-badge.
K5 (coordinator self-review, docs-only) follows as a second PR if capacity remains.

## What shipped

- **`scripts/check_manifest_freshness.py`** (Q-0105 unverified header): parses the
  manifest table (project · repos · Last-seen), reads each lane repo's live state
  over git transport, and reports per-row verdicts at day precision:
  `FRESH` / `STALE` (status.md `updated:` newer than Last-seen) / `DRIFT`
  (HEAD-only activity signal for repos without a status file — advisory even
  under `--strict`) / `SKIP` (fail-open on any network/parse failure). Repo
  fetches are cached across rows (superbot-games appears twice); `--strict`
  exits 1 on confirmed STALE only, never on DRIFT/SKIP. Not CI-wired by design
  (needs network + sibling-repo credentials).
- **19 unit tests** (`tests/unit/scripts/test_check_manifest_freshness.py`):
  parsing halves on inline fixtures + the real committed manifest; classification
  matrix (stale/fresh/same-day, status-outranks-HEAD, DRIFT-never-strict-fails);
  the git-transport half against *local* fixture repos via a repointed
  `_repo_url` (zero network in tests); fail-open pinned.
- **First live run** (the Q-0105 first verification): 11 rows — 9 fresh,
  **2 stale (trading-lab, venture-lab — both ground-truthed by hand:
  venture-lab's `updated: 2026-07-10T03:26:55Z` vs manifest `2026-07-09`)**,
  0 drift, 0 skipped. The stale rows are left for the **manager Project's
  re-stamp** — `docs/eap/fleet-manifest.md` is the manager's sole-writer file
  (fleet protocol), so this session reports rather than edits it.
- **Reconciliation-routine checklist line** in
  `docs/operations/autonomous-routines.md` (run the checker during the docs
  pass; note STALE rows for the manager; never re-stamp from superbot).
- Idea re-badged `historical` (`fleet-manifest-freshness-checker-2026-07-10.md`)
  + `docs/ideas/README.md` index entry updated.

## Verification

- `python3.10 scripts/check_quality.py --full` — first run found exactly one
  defect: `F401 'sys' imported but unused` in the new script (fixed); pytest leg
  `13898 passed, 49 skipped, 2 xfailed in 145.05s`, mypy green. Post-fix
  `check_quality.py --check-only` — `All checks passed ✓` (exit 0); only the
  import line changed between the runs.
- `python3.10 scripts/check_architecture.py --mode strict` — exit 0 (0 errors,
  37 known warnings — down from the scout baseline's 50 after Session D's fix).
- `python3.10 scripts/check_docs.py --strict` — exit 0, all checks passed;
  Recently-shipped at the 20 ratchet.
- `python3.10 scripts/check_current_state_ledger.py --strict` — exit 0 (benign
  newest-merge lag only; the #1920-boundary recon PR #1922 is open and owns it).
- New suite: `19 passed in 0.50s`.

## Session enders

- **💡 Session idea** — `check_manifest_freshness --stamp`: emit the corrected
  Last-seen cells as a copy-paste patch block so the manager's re-stamp is as
  free as the detection now is ("detection free → fix free"), while keeping the
  sole-writer discipline (superbot never edits the manifest; the manager pastes).
  Dedup-grepped `docs/ideas/` — nothing covers checker-to-restamp handoff.
  Small; natural follow-up inside the existing script.
- **⟲ Previous-session review (Session D, #1920)** — Strong session: the Q-0120
  source-check caught the shift plan's stale premise (the 6 baseview sites
  already had comments) and fixed the *checker* at root cause instead of
  papering over it, and it converted that friction into an idea
  (`shift-plan-premise-verify-lines-2026-07-10.md`). One improvement it
  surfaces: when Session D deferred K4 as "more than a ride-along" partly on
  the unverified GitHub-API network half, a single 10-second probe (`curl
  api.github.com` → 403) would have pinned the feasibility fact into the
  handoff and saved the next session the discovery. Deferral notes should carry
  one cheap probe result when feasibility is the reason for deferral — that
  slots directly into Session D's own premise-verify-lines idea rather than
  needing a new mechanism.
- **Docs audit (Q-0104)** — ledger entry for #1923 added to
  `docs/current-state.md` Recently-shipped (trimmed to the 20 ratchet);
  `check_docs --strict` + `check_current_state_ledger --strict` green; no owner
  decisions were made this session (design call was decide-and-flag, recorded
  here + in the PR body); nothing chat-only left undocumented.
- **⚑ Flags** — (1) 2 STALE manifest rows (trading-lab, venture-lab) reported
  for the manager's re-stamp, not fixed here (sole-writer file). (2) Design
  deviation from the idea capture: git transport instead of GitHub REST API
  (rationale above; recorded in the idea file's Shipped block). (3) K4 was
  shipped with the network half **fully verified live** — not stubbed — so the
  shift-plan's fallback lane (offline-half-only / DRAFT) was not needed.
