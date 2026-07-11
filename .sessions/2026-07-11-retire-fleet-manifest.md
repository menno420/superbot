# 2026-07-11 — Retire fleet-manifest to a pointer stub (fm roster canonical)

> **Status:** `complete`
> **Run type:** dispatched (coordinator order — the superbot-side follow-up the fm
> parallel-run findings doc explicitly routed here)
> **Model/time:** fable-5 · 2026-07-11 · PR #1974

## What was about to happen (born-red declaration)

Per the phase-2 decision in fleet-manager PR #59 (merge `b0639a9`, findings: fm
`docs/findings/manifest-parallel-run-2026-07-11.md`), reduce `docs/eap/fleet-manifest.md`
to a pointer stub at the fleet-manager generated roster (`menno420/fleet-manager`
`docs/roster.md`), retire `check_manifest_freshness.py` (scripts/) per its own Q-0105
kill-switch header (+ its test + runbook/doc wiring), and update pointing docs.

## What happened

- **Spec verified at source:** fleet-manager fetched to `b0639a9` (FETCH_HEAD ==
  ls-remote); read the parallel-run findings (manifest ~33.5h stale, 5 live lanes
  missing, 9/10 live-lane rows wrong; only the websites trigger id survived) and
  roster gen #4. The findings doc itself routes this exact slice to superbot.
- **`docs/eap/fleet-manifest.md` → dated pointer stub** (supersession notice, canonical
  pointer, the why with citations; history in git). The 11 re-stamp items deliberately
  NOT hand-fixed — retiring dual maintenance is the point.
- **Checker retired per its own kill-switch:** `check_manifest_freshness.py` (scripts/)
  + its 19-test suite deleted. Its Q-0105 header called it a disposable convenience
  guard ("delete this script if it proves unreliable… the manifest + lane repos are the
  source of truth") — with the manifest no longer maintained, its premise is gone. It was
  never CI-wired (by its own design note); the only live wiring was the
  reconciliation-routine checklist line in `docs/operations/autonomous-routines.md`,
  now replaced with the roster pointer + the roster's own >24h-stale kill-switch rule.
- **Pointing docs updated:** `docs/eap/README.md` index entry; ideas index + both idea
  files (`fleet-manifest-freshness-checker` marked RETIRED; `reconcile-fleet-runtime-digest`
  re-pointed at the roster/heartbeats); supersession notes in
  `docs/planning/fleet-coordination-protocol-2026-07-09.md` and
  `docs/planning/round3-dispatch-runbook-2026-07-10.md` (REGISTRY TRUTH bullet).
  Historical records (.sessions, pass records, overnight review) left as history.
- **Ledger:** `docs/current-state.md` #1974 entry added (top of Recently shipped).

## Gates

- `python3.10 scripts/check_quality.py --check-only` → **All checks passed ✓** (after
  fixing 6 pinned-path findings its check_docs leg raised on cross-repo/deleted paths —
  re-phrased so backticked tokens carry the `fleet-manager` repo prefix).
- `python3.10 scripts/check_docs.py --strict` → **all checks passed ✓** (exit 0). One new
  warn-only advisory avoided by de-linking the cross-repo successor URL in the stub banner
  (check_supersede_integrity can only resolve local successors — see the session idea).
- `python3.10 scripts/check_current_state_ledger.py --strict` → exit 0 (21 merged PRs
  newer than marker #1950 = benign newest-merge lag, informational).

## 💡 Session idea

**Cross-repo successor syntax for `check_supersede_integrity.py`** — the checker flags any
markdown-linked successor it can't resolve locally as a "phantom successor", but a
supersession whose successor lives in a sibling repo (this session's exact case: the
manifest's successor is fm `docs/roster.md`) has no representable form today; the honest
workaround was demoting the link to a bare URL. Teach the banner grammar a
`repo:path` / `owner/repo path` successor form the checker treats as
verified-by-convention (or verifies over git transport like the retired checker did).
Worth having: cross-repo supersession is now the *normal* direction of travel — superbot
docs increasingly hand off to fleet-manager/kit homes, and each hand-off currently either
warns or hides its successor. Dedup-grepped `docs/ideas/` (`supersede`, `cross-repo`) — no
existing capture. Small; kept log-only per Q-0089.

## ⟲ Previous-session review

The games-retro/mineverse packages session (07-11, opus-4.8) did the two-owner-picks →
two paste-ready founding packages flow cleanly, and its review even proposed adding a
"Q-0259 games slots: 3/3 packaged" tracking line *to the fleet-manifest* — which this
session just retired. That's not a knock (the manifest was the registry when it wrote
that); it IS the workflow improvement: **track-the-target lines belong in the generated
roster's inputs (lane heartbeats / fm planning), not in hand-maintained superbot docs** —
any "add a line to the manifest" instinct should now route to fm or the lane's
`control/status.md`, or it recreates the drift class this PR just deleted. Concretely:
the previous session's good idea survives by living in fm's roster generation, not here.

## Documentation audit (Q-0104)

`check_docs --strict` ✓, `check_current_state_ledger --strict` ✓ (benign lag only),
`check_quality --check-only` ✓. Nothing chat-only left homeless: the decision provenance
lives in the fm findings doc + this card + the #1974 ledger entry; the verbatim
kill-switch reasoning is quoted in the PR body. Claim file deleted this commit.

## 📤 Run report

- **⚑ Owner decisions needed:** none (phase-2 was decided-and-flagged in fm PR #59; this
  is its routed follow-up — veto path: revert #1974, the manifest history is in git)
- **⚑ Owner manual steps:** none
- **⚑ Self-initiated:** none (dispatched slice; the session idea stays log-only, not promoted)
