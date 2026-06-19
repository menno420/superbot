# 2026-06-19 — Fleet B6: SHA-pin third-party GitHub Actions

> **Status:** `complete`

## Arc

Lane B unit **B6** of the [ultracode fleet brief](../docs/planning/ultracode-fleet-plan-2026-06-19.md) —
SHA-pin the third-party GitHub Actions across all workflows (supply-chain hardening that
pairs with the now-active Dependabot, which bumps the SHAs going forward).

## Shipped (#1088)

Rebuilt on current `main` after the now-active Dependabot bumped several action majors
mid-run (checkout→v7, cache→v5, github-script→v9, codeql→v4), which had made the original
branch conflict. Pinned every third-party `uses:` tag to its resolved 40-char commit SHA
with a trailing version comment (Dependabot reads the comment):

- `actions/checkout@v7` → `9c091bb…`
- `actions/cache@v5` → `27d5ce7…`
- `actions/github-script@v9` → `3a2844b…`
- `actions/setup-python@v6` → `a309ff8…`
- `actions/upload-artifact@v4` → `ea165f8…`
- `github/codeql-action/{analyze,autobuild,init}@v4` → `8aad20d…`
- (`peter-evans/create-pull-request` was already SHA-pinned on main.)

Local-action (`./…`) and reusable-workflow refs left untouched. No workflow logic changed —
only the `@ref` of third-party `uses:` lines. All 8 workflow files YAML-parse; the pinned
SHAs are the live tag commits (resolved via `git ls-remote`), and CI itself exercises them.

> Rebuilt by the fleet orchestrator after a mid-run container restart + ongoing Dependabot
> major bumps made the original agent's branch stale/conflicting.

## 📤 Run report

- **Did:** SHA-pinned all third-party Actions across 8 workflows (fleet B6). · **Outcome:** shipped
- **Shipped:** #1088
- **Run type:** `routine · dispatch`
- **⚑ Owner decisions needed:** `none`
- **⚑ Owner manual steps:** `none`
- **⚑ Self-initiated:** B6 — docs/planning/ultracode-fleet-plan-2026-06-19.md (ungated CI/supply-chain)
- **↪ Next:** Dependabot now bumps these SHAs going forward.

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1088, on green) |
| CI-red rounds | 1 (born-red gate + 1 Dependabot-conflict rebuild) |
| Actions SHA-pinned | 6 distinct actions across 8 workflows |
| New ideas contributed | 0 (fleet completion run) |
| Ideas groomed | 0 |
