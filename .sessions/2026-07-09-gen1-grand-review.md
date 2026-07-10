# 2026-07-09 — Gen-1 grand review + cleanup (fleet-wide)

> **Status:** `complete`

- **📊 Model:** claude-fable-5 · high · ultracode multi-agent session (7 readers, 9 PR
  reviewers, 3 diagnostics, 5 refuters; ~1.9M subagent tokens + main loop)

## Arc

Owner-directed ultracode session: independent review of everything the gen-1 Projects
fleet did, across all six repos, with adversarial verification; drive every open PR
terminal; produce the grand-review report + a send-ready wrap-up email candidate.

1. Added the 5 sibling repos to session scope, cloned all, opened this PR born-red in the
   first minutes (Q-0189), armed auto-merge (Q-0127).
2. Fanned out discovery (17 agents: per-repo corpus readers, Gmail thread reader, one
   reviewer per open PR, parity-red diagnosis, old-vs-new gap map, email fact audit),
   then 5 adversarial refuters over the drafted sections.
3. Acted on every verdict — see "Shipped".

## Shipped

- **docs/eap/gen1-grand-review-2026-07-09.md** — the verified report (gap map · PR sweep ·
  email fact audit · wind-down audit · gen-2 synthesis · efficiency verdict · ⚑ owner
  actions).
- **docs/eap/gen1-wrapup-email-final-candidate.md** — send-ready candidate (3 material
  corrections applied; all placeholders resolved except Part 1 = owner's slot; supersedes
  draft v2 as the send-candidate).
- **PR sweep to zero:** superbot #1910 (owner-merged mid-session, review concurs) ·
  superbot-next #95 fix-then-merged (conflict resolved, suite 1,132 green) + **#97**
  (this session's fix PR: worldcard Reply-shape bug + README-first red-orientation doc +
  README/current-state drift) · superbot-games #5 → #11 (squash-ancestry conflicts
  resolved locally, 73/73 green on exact head) → #14 (+ dated status addendum) —
  mining lane fully landed, wind-down complete · substrate-kit #49 + #26 ratified-by-merge
  (labels kept; PL-011 now law; B1 run-3 unblocked; #26 needed a git-push branch update —
  the API-authored update-branch commit never triggers CI, the known #778-class wall) ·
  fleet-manager #12/#13 self-merged by their lane, post-merge reviews concur.
- **Parity-red verdict:** superbot-next's golden-parity `report` job is red **by design**
  (owner's red-until-parity dashboard; decisions.md says never-required; gate leg green).
  Reproduced locally byte-identical. Fix was orientation (README-first.md), not greening —
  plus the one genuine crash-class bug it surfaced, fixed in #97.

## Findings routed

- Fact-audit corrections → applied in the final candidate (1,815 PRs; "three labs"; kit
  wind-down complete; freshness updates).
- Gen-2 synthesis (7 inter-lane disagreements + 10 amendment candidates) → report §6, for
  the fleet-manager blueprint owner.
- Live datapoint: superbot's Stop hook demanded committing a harness-generated
  `settings.local.json` permission change while the auto-mode classifier denied it as
  self-modification — recorded in report §7 + email friction 1 (the
  permission-inconsistency class, reproduced inside the wind-down itself). Resolved by
  reverting the file once the needing agent finished.

## Context delta

- **Needed but not pointed to:** the workflow-results NULL quirk (journal `result` values
  null while agent transcripts hold the real StructuredOutput payloads — recover by
  extracting `tool_use` blocks from `agent-*.jsonl`); the shallow-clone traps
  (`fetch origin <branch>` silently not creating remote-tracking refs — use explicit
  refspecs; "refusing to merge unrelated histories" → `--unshallow`); API-authored
  update-branch commits never trigger CI (push via git instead).
- **Pointed to but didn't need:** docs/eap/README.md (named in orientation material but
  does not exist); the CodeGraph MCP surface (unused — this session was cross-repo
  docs/PR work, not superbot code navigation).

## 💡 Session idea

The fleet-manifest's per-lane cells go stale within hours (kit row said v1.0.0/637 while
the kit was at v1.6.0/722 on its own main). Since every lane already writes a
machine-readable `control/status.md` heartbeat, a tiny manager-side checker
(`check_manifest_freshness.py`: compare each manifest row's last-seen against the lane
repo's status header, red if older) would convert the manifest from hand-maintained prose
into a verified dashboard — the same "enforce, don't exhort" move (Q-0132) that fixed the
claims ledger.

## ⟲ Previous-session review

The eap-email-draft-v2 session (#1910) did the single most valuable thing right: it
committed the draft as a repo artifact with a "supersedes / don't send both" header and
explicit placeholders, which made this session's finalization mechanical rather than
archaeological. Two misses, both small: it relayed "~1,900 merged PRs" without recounting
(actual: 1,815 — exactly the class its own friction 13 warns about), and it listed kit
#74/#75 as in flight when both had merged ~3 hours before it pushed (a freshness sweep of
§(e)/(f) against live GitHub at write time would have caught both). System improvement
shipped: the final candidate's §(f) is now a "state at send time" section that a future
session regenerates wholesale instead of patching line-by-line — cheaper to re-derive than
to audit.

## Close-out

- Claim file `docs/owner/claims/claude-vigilant-rubin-0wuxk2.md` deleted in the final
  commit (Q-0126/Q-0195).
- Docs audit: new docs reachable (linked from this card + each other + PR body);
  reconciliation marker untouched (next pass at #1920 records this merge — benign
  newest-merge lag per Q-0166).
- ⚑ Self-initiated: superbot-next #97 (worldcard fix + README-first + drift fixes) —
  contained, tested, merged on green; the dated addendum line appended to
  games `control/status-mining.md` during the #14 merge (one-writer courtesy note:
  lane closed, truth-preservation for gen-2 boot).
