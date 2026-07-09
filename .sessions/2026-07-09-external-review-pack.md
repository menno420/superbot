# 2026-07-09 — external-review-pack

> **Status:** `complete` — PR #1903; pack shipped, banner link added, all raw URLs verified live.

**Intent:** Owner-directed (fleet-manager coordinator, 2026-07-09): write
`docs/eap/external-review-pack-2026-07-09.md` — the single entry-point document for
**outside** reviewers (ChatGPT agent / Codex / deep-research sessions; no GitHub auth,
public-web access only) auditing the fleet. Docs-only PR.

## What shipped (PR #1903)

- `docs/eap/external-review-pack-2026-07-09.md` — five sections: (1) the program in one
  page (10 Projects / 9 repos / committed-file message bus); (2) the central root-cause
  question every reviewer must classify (our setup vs. platform limits vs. deficient work),
  with the four-reviewer internal findings stated honestly as claims-to-check; (3) a
  per-repo register — purpose, live `control/status*` phase/health at 16:22Z, key entry
  docs as raw.githubusercontent.com URLs, and 3–5 boldest falsifiable claims per repo with
  evidence pointers; (4) the required report shape (findings table with a/b/c root-cause
  class, per-claim verified/refuted/could-not-verify verdicts, exactly 3 recommendations);
  (5) integrity notes (repos are the record; fleet reports may be wrong; Q-0120 cross-check
  before acting).
- `docs/eap/fleet-review-2026-07-09.md` — banner link to the pack (reachability for
  `check_docs --strict`, same pattern as PR #1897).
- `telemetry/model-usage.jsonl` — this session's row (Q-0194 guard: card-adding PR).

**Grounding:** fleet manifest + fleet quality review via `git show FETCH_HEAD`; every other
repo's live `control/status*` fetched via GitHub MCP at compile time (superbot-next 16:05Z,
substrate-kit 15:26Z, websites 16:30Z, fable5 15:01Z, sonnet5 16:15Z, trading/opus48/games
still manager seeds — staleness disclosed in the pack). Every raw URL in the pack was
HEAD-checked (curl, all 200; two 404 candidates corrected before publishing: superbot has
no root README, envdrift's module is `cli.py`/`parser.py` not `check.py`). trading PR #1
re-verified still an open draft at 16:22Z.

## Session enders

- **⚑ Self-initiated:** none — owner-directed via the fleet-manager coordinator; judgment
  calls (marking trading/opus48/games status files as stale seeds; noting the warn-escalation
  fix PR #80 supersedes the audit's pre-fix description; flagging sonnet5 as least-audited)
  are honesty framing inside the directed scope, flagged in the pack itself.
- **💡 Session idea:** the pack is a dated snapshot that will drift (status files churn
  hourly). Add a tiny "external-pack freshness" line to the manager's rollup routine: when
  compiling a new day's pack, diff each repo's status timestamp against the pack's compile
  time and regenerate §3's phase/health lines mechanically — the claims/URLs are stable,
  only the heartbeat lines rot. Dedup-grepped `docs/ideas/` (`external review`, `raw url`,
  `outside audit`) — nothing covers it.
- **⟲ Previous-session review** (`2026-07-09-fleet-spec-heartbeat-mirror`, PR #1898): clean
  thin-mirror change — it applied the kit's relay request exactly and cited the KF-2
  boundary. Improvement it surfaces: cross-repo relay requests arrive via status-file
  `notes:` prose, which a busy manager can miss; a structured `relay:` field in the status
  format would make them mechanically harvestable. Kept as a remark (the format is kit-owned;
  superbot only mirrors it).
- **Docs audit:** new doc reachable from `docs/eap/fleet-review-2026-07-09.md` banner
  (`check_docs --strict` green locally); no ledger impact beyond benign newest-merge lag
  (Q-0166 exception); no new owner decisions to route — Q-0120/Q-0194 doctrine only applied.
- Claim file `docs/owner/claims/claude-external-review-pack.md` deleted at close.
