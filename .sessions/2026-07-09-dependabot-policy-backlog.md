# 2026-07-09 — Dependabot PR policy (owner decision) + backlog review/merge

> **Status:** `in-progress`

## What I did

The owner decided dependabot policy (2026-07-09, verbatim words preserved in
**router Q-0256**): dependabot PRs are **reviewed by the first session that
sees them, then merged**; major version bumps are **fix-then-merge** if the
adaptation is contained, else a **dedicated-session work item**.

**Policy recorded:**

- **Q-0256** (DIRECTED) appended to the question router — owner's answer
  verbatim + the three-point rule it sets.
- Durable rule home: `docs/operations/repo-settings-state.md` § **Dependabot
  PR policy** (next to the auto-merge/token facts it depends on).
- Visibility at the moment of "sight": note in `docs/AGENT_ORIENTATION.md`
  § Any task (the session-start open-PR overlap scan is where dependabot PRs
  get seen), and the reconciliation routine's DISPOSITION OPEN PRs step
  (`docs/operations/autonomous-routines.md`) now names open `dependabot/*`
  PRs as merge candidates — the 2026-07-08 pass (#1861) left 6 green
  dependabot PRs untouched, which was the failsafe gap.
- **Q-0257** (DISCUSS) — extending `auto-merge-enabler.yml` to arm dependabot
  PRs is owner-gated executable config, so it's proposed (with a recommend-
  against: the owner's "reviewed by the first session" wording argues against
  blanket auto-arming), not shipped.

**Backlog executed (all 6 PRs to terminal state, per-PR review = diff +
changelog + real-usage grep, CI green on head verified before each merge):**

- **#1765 psutil ≥5.9.0 → ≥7.2.2 (MAJOR)** — merged after real assessment:
  superbot uses only `Process().memory_info().rss` (bot1.py RSS sampler),
  `cpu_percent()` + `virtual_memory()` (diagnostic_helpers) — all unchanged
  through 7.2.x per the upstream changelog; the 6.0/7.0 removals
  (`memory_info_ex`, `connections()`) are unused; the floor pin means fresh
  Railway builds already installed 7.x; full suite green with 7.2.2. No code
  change needed.
- **#1764 discord.py ≥2.7.1,<2.8** — merged (patch floor within pinned minor).
- **#1763 anthropic ≥0.116,<1.0** — merged (provider surface is
  `AsyncAnthropic` + `messages.create`, stable across the range).
- **#1766 Pillow ≥12.3,<13** — merged (minor floor within pinned major).
- **#1762 uvicorn 0.50.0 → 0.50.2 (botsite floor + dashboard lockfile)** —
  merged; dashboard-tests + botsite-tests green on head.
- **#1761** — **closed as superseded**: its dashboard-only diff is a strict
  subset of #1762 (root-pip and dashboard-pip dependabot groups overlapped on
  the same `dashboard/requirements.*` lines) — *not* a true duplicate pair,
  a finding now recorded in the policy section.

Ledger entry added to `docs/current-state.md` ▶ Recently shipped for the
batch. Docs-only session — zero `disbot/` runtime code.

## Context delta

- **Needed but not pointed to:** nothing pointed at the fact that the two
  "duplicate" uvicorn PRs came from *different dependabot ecosystems* (root
  pip scans `botsite/` + `dashboard/` requirements too) — now captured in the
  policy section.
- **Pointed to but didn't need:** n/a.
- **Decisions made alone (decide-and-flag, Q-0240):** merge order (major
  first, then patches, then the multi-file group) — arbitrary-safe since all
  hunks were disjoint; #1761 closed rather than rebased (its entire diff was
  already on main via #1762); Q-0257 written recommend-against rather than
  neutral, because the owner's own wording decides it.

## ⚑ Self-initiated

- Reconciliation-routine disposition step amended to name dependabot PRs
  (docs-level guard, free lane per Q-0194 split) — the routine was the
  failsafe that had already missed this class once.

## 💡 Session idea

`scripts/check_dependabot_backlog.py` — a small checker the reconciliation
routine (and any session with a `GITHUB_TOKEN`) can run: list open
`dependabot/*` PRs and **fail/warn when any has sat >48h with green CI**.
Today's friction class ("no merge actor, nobody's job") currently has only
docs-level guards — exhortation; a checker makes the recon pass red when the
backlog rots, which is the "enforce, don't exhort" (Q-0132) end-state. Cheap:
one paginated `gh api`/REST call + an age threshold.

## ⟲ Previous-session review

Previous session pair (#1883 KL-6 exporter telemetry → #1884 console.json
shape contract) executed its *own* session idea the same day — the
idea-to-execution loop working as designed, and the hand-authored telemetry
convention it seeded is already being followed (this session appends its
row). Improvement it surfaces: the "append your telemetry row at close"
convention lives only in `telemetry/README.md` — a session that doesn't
happen to read the previous card misses it (I found it by accident).
`scripts/check_session_log.py` (or the `/session-close` skill checklist)
should warn when a new `.sessions/` card lands without a matching
`model-usage.jsonl` row — checker lane, free to ship; left as a concrete
follow-up rather than done here (out of this session's scope).

## Documentation audit

- `python3.10 scripts/check_current_state_ledger.py --strict` — green; the
  dependabot batch is recorded in the ledger *now* (not left to marker lag);
  this session's own PR #1886 is the benign newest-merge lag the next pass
  records (marker at #1861, next pass due at #1890).
- `python3.10 scripts/check_docs.py --strict` — green.
- New owner decision → router (Q-0256) ✓; durable home
  (`repo-settings-state.md`) ✓; orientation visibility (AGENT_ORIENTATION +
  autonomous-routines) ✓; owner-gated proposal → DISCUSS Q-0257 ✓.
- Backlog grooming (Q-0015): skipped — the session's secondary capacity went
  into the 6-PR disposition sweep + the routine-prompt guard; noted honestly.

## Close

Claim file `docs/owner/claims/claude__dependabot-policy-backlog.md` deleted at
close. PR #1886 opened ready + auto-merge (squash) armed at open; the session
gate holds it red until this badge flips, then it merges on green CI.
Telemetry row appended to `telemetry/model-usage.jsonl` (task_class
review/verify).
