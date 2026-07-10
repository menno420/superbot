# Fleet-manifest freshness checker (2026-07-10)

> **Status:** `ideas` — capture, not a plan, not approval.
> **Subsystem:** tooling / EAP program record.

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
