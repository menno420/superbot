# Fleet-manifest freshness checker (2026-07-10)

> **Status:** `historical` — implemented (PR #1923, 2026-07-10) · raised 2026-07-10 (night-prep, #1915)
> · **RETIRED 2026-07-11 (PR #1974)**: the checker + test were deleted per the script's own Q-0105
> kill-switch header when `docs/eap/fleet-manifest.md` was superseded by the fleet-manager
> **generated roster** (`menno420/fleet-manager` `docs/roster.md`; phase-2 decision, fm PR #59 +
> fm `docs/findings/manifest-parallel-run-2026-07-11.md`) — the staleness class it policed died
> structurally, exactly the outcome the manifest header predicted. Code history in git.
> **Subsystem:** tooling / EAP program record.
>
> **Shipped:** `scripts/check_manifest_freshness.py` + `tests/unit/scripts/test_check_manifest_freshness.py`
> (PR #1923), plus the reconciliation-routine checklist line in
> `docs/operations/autonomous-routines.md`. **One design change from this capture:** the network
> half reads over **git transport** (shallow `git fetch --depth 1` + `git cat-file`), not the
> GitHub REST API named below — the REST API is proxy-blocked in agent containers ("GitHub access
> is not enabled for this session") while git is credential-injected, so the API version would fail
> exactly where the routine runs. First live run (2026-07-10): 11 rows — 9 fresh, **2 stale**
> (trading-lab, venture-lab; both ground-truthed by hand), 0 drift, 0 skipped. Advisory-only,
> fail-open, not CI-wired (it needs network + sibling-repo credentials, so it must never gate).

**One line:** a small checker (`scripts/check_manifest_freshness.py`) that compares each
`docs/eap/fleet-manifest.md` row's last-seen cell against the lane repo's
`control/status.md` `updated:` header (GitHub API read) and reports red when a row is
older — converting the manifest from hand-maintained prose into a verified dashboard.

**Why:** the gen-1 grand review (PR #1911 §5) found the manifest cells stale within hours
of seeding — the kit-lab row said "v1.0.0, 637 tests" while the kit's own main was at
v1.6.0/722; the superbot-next row said "no wind-down reaction" while the retro pair sat
merged on its main. Every cell had a machine-readable source of truth the row simply
lagged. Same "enforce, don't exhort" move (Q-0132) that fixed the claims ledger; the
2026-07-10 night-prep PR (#1915) did this reconcile by hand — this checker makes it free.

**First step:** advisory-only script (Q-0105 header: unverified, delete-if-unreliable)
comparing the six core-lane rows; wire into the reconciliation routine's checklist, not
CI. Alternate home if the manager Project prefers: fleet-manager, next to its rollup.

**Size:** small (one script + a routine-prompt line).
