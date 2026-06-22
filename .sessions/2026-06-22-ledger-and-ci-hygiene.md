# 2026-06-22 — ledger drift fix + design-system CI-coverage gap (post-botsite hygiene)

> **Status:** `complete` — born-red card (Q-0133) flipped green as the final step.
> Routine · dispatch ("Continue from where you left off" after PR #1305 + #1308 merged).
> PR #1317 → auto-merges on green (Q-0123).

## Arc (what I'm about to do)

Both botsite slices this session merged (#1305 React foundation, #1308 contract guard). The
SessionStart hook flagged **real ledger drift** (Q-0166 fix-on-sight): **#1279 (reaction-roles
PR 6 — PIL banner cards)** merged but is *under* the reconciliation marker #1291, so it's a
genuine miss, not benign newest-merge lag → fix now. While fixing it I caught a **CI-coverage
gap I introduced in #1308**: the TS contract test (`data.test.ts`) reads
`botsite/data/site_data_contract.json`, but `design-system-ci.yml` is `paths`-filtered to
`design-system/**`, so a change to the contract (or the botsite producer) alone wouldn't re-run
the TS guard. This is a small, safe, docs+CI hygiene turn — no runtime code.

This PR:
1. **Ledger drift (#1279)** — record reaction-roles PR 6 as shipped in `current-state.md` (both
   reaction-roles bullets) + the S1 sector file; correct the stale "PR 6 … remains" prose so only
   the gated web builder (Surface A) is shown outstanding. `check_current_state_ledger --strict`
   green afterward.
2. **CI-coverage gap** — add `botsite/data/site_data_contract.json` + `botsite/site_data.py` to
   `design-system-ci.yml`'s push + PR `paths`, so a contract/producer change re-runs the
   cross-package TS guard (#1308's design↔data seam).
3. **Stale-claim GC** — delete my two merged-branch claim files (`s56i3y`, `s56i3y-2`) the
   `check_stale_claims` GC flagged.

## Shipped (PR #1317)

- **Ledger drift (#1279) — fixed.** Recorded reaction-roles **PR 6 (PIL banner cards, #1279)** as
  shipped in `current-state.md` (both reaction-roles bullets, L266 + L291) + the S1 sector file,
  correcting the stale "PR 6 … remains" prose so only the gated web builder (Surface A) shows
  outstanding. `check_current_state_ledger --strict` green.
- **design-system CI-coverage gap — closed.** `design-system-ci.yml` push + PR `paths` now include
  `botsite/data/site_data_contract.json` + `botsite/site_data.py`, so a change to the cross-package
  contract (or the producer that owns it) re-runs the TS guard `data.test.ts` added in #1308 —
  previously a contract edit alone wouldn't trigger the design-system leg. YAML validated.
- **ruff tool-pin drift — fixed (bonus fix-on-sight).** `check_tool_pins` flagged `requirements-dev.txt`
  pinning `ruff==0.15.18` while code-quality.yml + .pre-commit-config.yaml (+ the local install) all
  pin `0.15.14` — a lone Dependabot bump in #1315 (the comment literally warned of it). Realigned
  `requirements-dev.txt` **down to 0.15.14** to match what CI actually runs (zero behavior change;
  2-of-3 + local already agreed). `check_quality --check-only` now fully green.
- **Stale-claim GC.** Deleted my two merged-branch claim files (`s56i3y`, `s56i3y-2`);
  `check_stale_claims` now reports 0 stale.
- **Verification:** `check_docs --strict` ✓ · `check_current_state_ledger --strict` ✓ ·
  `check_tool_pins` ✓ · `check_quality --check-only` ✓ · `check_stale_claims` 0 stale ·
  design-system-ci.yml YAML valid. No runtime code touched.

## Session enders

- **♻ Grooming (Q-0015):** no idea-lifecycle move this turn — it's a pure fix-on-sight hygiene PR
  (ledger/CI/pins). The migration lane's next move (PR 2 cutover) stays owner-paced; the S1 sector
  ▶ Next pointer (PR 2) from #1305 is unchanged and accurate.
- **💡 Session idea (Q-0089):** *A grouped-or-ignore Dependabot config for the three-places-pinned
  tools.* This exact ruff drift (#1315 → fixed here) will recur every time Dependabot bumps a
  lint/format tool in `requirements-dev.txt` alone, because the other two pin-sites
  (code-quality.yml, .pre-commit-config.yaml) aren't `pip`/npm manifests Dependabot tracks. Idea:
  either a Dependabot `groups`/`ignore` rule for black/isort/ruff/mypy (don't auto-bump the
  three-places tools), OR a tiny CI check that *fails the Dependabot PR* when it desyncs the trio
  (turn `check_tool_pins` into a blocking CI step — it's currently local-only, which is why #1315's
  drift reached main). Logged; the CI-step half is a clean, safe dispatch slice.
- **⟲ Previous-session review:** my own #1308 (this turn's predecessor) shipped a genuinely useful
  cross-package contract guard — but introduced the **CI-paths gap fixed here**: a guard that reads
  a file outside its own CI's `paths` filter only runs when *its* package changes, so it can't see a
  drift originating in the *other* package. **System note:** whenever a test reaches across a
  `paths`-filtered CI boundary, the filter must include *both* sides — worth a one-line rule in the
  web-tier CI docs (a cross-package test is only as good as the trigger that runs it).
- **🧾 Doc audit (Q-0104):** `check_docs --strict` ✓; ledger reconciled (#1279); the ruff-drift fix
  + CI-paths fix are recorded here; ledger auto-updates for #1317 on merge (newer than marker, benign
  lag). Nothing left only in chat.

## ⚑ Self-initiated: yes (Q-0172, low-risk) — none of these three fixes was dispatched, but all are
   **fix-on-sight drift** the tooling itself flagged (the SessionStart ledger warning · `check_tool_pins`
   · the #1308 CI-paths gap I could see), which CLAUDE.md Q-0166 makes a standing obligation, not an
   invented feature. Docs/CI/pins only, fully reversible → self-merged on green.

## 📤 Run report

- **Did:** post-botsite hygiene — fixed three fix-on-sight drifts the tooling flagged: ledger miss (#1279 reaction-roles PR 6), a design-system CI-paths gap (the #1308 cross-package contract guard wasn't re-run by contract edits), and a ruff tool-pin drift (#1315's lone Dependabot bump); plus stale-claim GC. · **Outcome:** shipped
- **Shipped:** #1317 — `current-state.md`/S1 ledger reconciliation, `design-system-ci.yml` paths, `requirements-dev.txt` ruff 0.15.18→0.15.14, 2 stale claims removed. No runtime code.
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** **yes (low-risk)** — three fix-on-sight drifts the tooling itself flagged (Q-0166 obligation), docs/CI/pins only, fully reversible → self-merged on green.
- **↪ Next:** botsite React-SPA migration **PR 2** — serve the built React bundle from `botsite/` + flip `/` to React last; ⚠️ needs a **manual browser click-through** (zero console errors), so best run attended / owner-previewed, not flipped blind unattended. The #1305 foundation + #1308 contract guard + this turn's CI-paths fix make the data side of that cutover trustworthy. Other open lanes: Project Moon runtime PR 1 (ingestion — network + IP/licensing-sensitive → weigh ask-first); a clean dispatch slice = make `check_tool_pins` a **blocking CI step** so a Dependabot three-places desync (like #1315's) can't reach main again (this turn's logged idea).
