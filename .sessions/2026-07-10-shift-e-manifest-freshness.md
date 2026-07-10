# 2026-07-10 — fleet-manifest freshness checker (overnight shift, session E)

> **Status:** `in-progress`
> **Branch:** `claude/shift-e-manifest-freshness` · **PR:** TBD

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
