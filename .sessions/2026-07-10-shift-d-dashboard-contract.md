# 2026-07-10 — dashboard.json pinned-feed contract, first slice (overnight shift, session D)

> **Status:** `in-progress`
> **Branch:** `claude/shift-d-dashboard-contract` · **PR:** #1920

**Intent:** shift-plan item **K3** — apply the #1884 console pinned-feed-contract
pattern to `dashboard/data/dashboard.json` (the ~12-page websites surface with no
contract), scoped to ONE family slice: `meta` + `bugs`. Ride-alongs: **Q2**
(baseview warnings) and **Q1** (`trim_recently_shipped` docs pass).
Idea: `docs/ideas/pinned-feed-contract-for-dashboard-json-2026-07-09.md`.

## What shipped

- **K3 — dashboard feed contract, first slice.** New versioned
  `dashboard/data/dashboard_data_contract.json` (version 1) with **slice
  semantics** — deliberately unlike the console contract's total whitelist, only
  the families listed in `contracted_families` are pinned (`meta` + `bugs`);
  every other family stays free until it is added, family-by-family, with a
  version bump (the idea's designed growth path). Producer side:
  `DASHBOARD_CONTRACT_FILE` / `DASHBOARD_SCHEMA_VERSION` /
  `DASHBOARD_CONTRACTED_FAMILIES` / `DASHBOARD_META_FIELDS` /
  `DASHBOARD_BUG_FIELDS` parity constants in `export_dashboard_data.py` and a
  `meta.schema_version` stamp; feed regenerated (only additive `schema_version`
  plus normal refresh churn the dashboard-data-refresh workflow lands anyway).
  Checker side: fail-closed `check_dashboard_contract` (producer⇄contract
  parity · contracted-families-present · schema-version equality · per-record
  guaranteed fields; meta subset, bugs exact) + `--dashboard-contract` CLI flag
  in `check_dashboard_data.py`. **14 new tests** incl. the
  committed-file-passes-contract guard and a slice-semantics test (an
  un-contracted extra family is NOT a finding).
- **Q2 — resolved at root cause, not as planned (Q-0120 source check).** The
  shift plan claimed the 6 `views/` sites *lacked* justifying comments — stale:
  all 6 have carried the `# Extends discord.ui.View directly (not BaseView): …`
  comment since #1871 (2026-07-08). The plan's "warning count drops" prediction
  was also impossible: `check_baseview_inheritance` never read comments, so
  documented views warned forever (an exhortation-only rule clause). Root-cause
  fix (Q-0194, checker tier): the checker now **recognizes the in-tree
  convention** (a `#` comment carrying "discord.ui.View directly" within the 6
  lines above the class def) and stays silent; the warning message + YAML rule
  description now name the convention. The **5 remaining undocumented sites**
  (deathmatch `_DuelView`/`_ChallengeView`, logging provision/select views,
  settings `_DisabledHelpHookView`) were each verified genuinely
  lifecycle-justified against source and documented (comment-only, zero runtime
  delta). baseview warnings **13 → 0**; +4 checker tests (documented-silences,
  marker-in-string and far-comment negatives, undocumented-warns).
  **Ratchet preserved:** the first cut re-pointed the conformance frozenset
  (`test_view_base_class_conformance.py`) at the now-empty warning set, which
  broke its lockstep partner (`test_panel_base_class_allowlist_parity.py`) and
  — worse — would have let any NEW direct view in on the strength of a
  self-written comment. Final design: the checker takes
  `respect_justifying_comments` (default True for the warn path); the
  conformance ratchet passes `False` and keeps pinning the **raw** 13-entry
  inventory, so the comment silences the day-to-day warning while the conscious
  allowlist review gate stays. Parity test and YAML allowlist untouched.
- **Q1 — ledger trim.** #1920 entry added, then `trim_recently_shipped.py
  --apply` moved the 3 oldest bullets to the archive (23 → 20); archive span
  eyeballed, `check_current_state_ledger.py --strict` exit 0 (24-PR benign
  newest-merge lag noted informationally — recon at the #1920 boundary is
  routine-owned, Q-0124, not this session's lane).
- **Docs:** idea file annotated "first slice SHIPPED (#1920)" with the remaining
  families enumerated (badge stays `ideas` — still live; `in-progress` is not an
  allowed badge token, `check_docs` caught the attempt); ideas README entry updated.

## Verification

- `python3.10 -m pytest tests/unit/scripts/test_check_dashboard_data.py -q` — 47 passed.
- `python3.10 -m pytest tests/unit/scripts/test_check_architecture.py -q` — 21 passed.
- `python3.10 scripts/check_dashboard_data.py --dashboard-contract --site --console` — OK, 0 warnings.
- `python3.10 scripts/check_architecture.py --mode strict` — 0 errors, 36 warnings
  (`by check: layer_boundary=31, raw_sql=5`; baseview_inheritance gone).
- `python3.10 scripts/check_quality.py --full` — full CI mirror (result recorded below).
- `check_docs --strict` / `check_current_state_ledger --strict` — green.

## ⚑ Flags

- **⚑ Self-initiated:** the `check_architecture` baseview justifying-comment
  recognition + the 5 comment-only documentation sites (the shift plan's Q2 as
  written was already done in-tree; this is the Q-0194 friction→guard root-cause
  version of it — checker tier, free to ship). Contract-slice family choice
  (`meta` + `bugs`) decided-and-flagged per Q-0240: bugs is websites-rendered,
  producer-constructed fixed-key (strongest exact check), and mirrors the proven
  console family.
- **⚑ PR number is #1920** — the Q-0107 recon *boundary* number. The
  reconciliation pass is routine-owned (Q-0124); `reconciliation-trigger` opens
  the `reconcile` issue as merges cross the boundary. This PR deliberately does
  not touch that lane.
- **⚑ Telemetry `task_class`** — no "tooling" class exists in the JSONL corpus;
  used `test writing` as closest (same call as session A/B).

## 💡 Session idea

`docs/ideas/shift-plan-premise-verify-lines-2026-07-10.md` — scout-report /
shift-plan items carry a one-line `verify:` command proving the item's *premise*
still holds at pick-up (distinct from the fix-verification line). Born from Q2's
stale premise this shift: a 5-second `grep -L` would have killed the item at
scout time. Cheap for the scout (paste the command it already ran), mechanical
Q-0120 for every consumer.

## ⟲ Previous-session review (sessions B & C)

**Session B (#1919, K2 `--remote` + Q1 + Q3)** did the hard part well: a
mid-shift conflict against #1918 was resolved by merging main forward (no
rebase), and the `--remote` scan closes a real pre-PR race window — this session
used the claims protocol it documented. Two observations: (1) B's Q1 trim was
back over the ratchet within ~3 hours (22 by session D start) because every
session appends its own ledger bullet — trimming as a *ride-along* is treadmill
work; the durable fix would be running the trim inside whichever automated pass
already touches the ledger (dashboard-refresh or the recon routine), worth a
line in a future plan. (2) **Session C is a cautionary blank:** a branch existed
briefly and was deleted with nothing published — no card, no claim, no trace in
the repo beyond the coordinator's memory. The born-red-card-first protocol
(Q-0133/Q-0189) exists precisely so a dead session leaves a visible tombstone;
C's disappearance validates opening the card in the first minutes, before any
build work.

## Documentation audit

Ledger entry #1920 present; trim applied and archive span verified; idea file +
README index updated; no owner decisions were made (nothing for the router); no
chat-only conclusions left unhomed. Claim file deleted in the final commit.
