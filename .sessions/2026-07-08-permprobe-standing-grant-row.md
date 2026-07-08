# 2026-07-08 — Permission probe: standing-grant row (not-attempted record)

> **Status:** `complete`

**Scope:** docs-only. Record the standing-grant probe row (Project custom-instructions
standing authorization vs. the auto-mode destructive-git classifier) as an honest
NOT-ATTEMPTED result — the receiving coordinator session exposed no Bash tool, so the
protocol's no-sub-agent requirement could not be met and zero classifier interactions
occurred. Appends an addendum to
`docs/planning/projects-eap-permission-probe-report-2026-07-08.md` and one entry to
`docs/planning/projects-eap-evaluation-log.md`. No `test/permprobe-*` branch is touched.

## What shipped (PR #1842)

- **`## Addendum — standing-grant row (2026-07-08)`** in the probe report: the verbatim
  standing-grant text under test, the no-sub-agent protocol (tests #7/#8 re-run in the
  receiving session's own Bash tool), the result (**NOT ATTEMPTED — zero attempts, zero
  classifier interactions; neither ALLOW nor DENY**, because the receiving webagent-driven
  coordinator session has no Bash tool and its only execution path is the sub-agent layer the
  protocol excludes), the verified read-only state (verbatim `ls-remote` permprobe heads;
  `test/permprobe-instr-0708` never created; nothing touched), the product-friction note
  (dispatcher had no visibility into the target session's toolset), and the recommendation
  (re-run from a session type with a direct Bash tool, e.g. CLI Claude Code carrying the same
  Project custom instructions).
- **One eval-log entry** (`docs/planning/projects-eap-evaluation-log.md`, axis: use-case fit,
  weight: friction) pointing at the addendum.
- Verification before writing: report + tests #7/#8 confirmed on `origin/main`; permprobe
  heads recorded verbatim (`claude/permprobe-clearpath-0708` @ `b4abf2b6`,
  `test/permprobe-0708` @ `462f145e`); no open PR / claim overlapped these files (only
  dependabot PRs open).
- Hard rails honored: no `test/permprobe-*` operation of any kind (read-only `ls-remote`
  only); probe tests #7/#8 not attempted in any form; no runtime code touched.

**Provenance:** coordinator-dispatched (Projects EAP evaluation bookkeeping), not
self-initiated.

## ⚑ Self-initiated
None — coordinator-dispatched docs record.

## 💡 Session idea (Q-0089)

**Dispatch-time toolset preconditions on dispatched task prompts.** This row failed silently
at routing: a protocol premised on a direct Bash tool was dispatched into a session type that
has none, discoverable only *after* dispatch, from inside. Fix at the workflow layer: dispatched
task prompts (coordinator → session, routine → session) carry an explicit
`requires: <tools>` line, and the receiving session's *first* action is a self-check that
aborts fast with a "toolset mismatch" report instead of improvising through an excluded path.
Pairs with (and is distinct from) the clearpath session's environment-capability-matrix idea:
that maps *operations vs. gating layers*; this adds *session-type toolset rows* + an enforcing
preflight, turning routing mistakes into one-line fast failures. Dedup: grepped `docs/ideas/`
for capability/toolset/manifest/dispatch — nearest are
`agent-env-credential-smoke-check-2026-06-14.md` (credentials, not toolsets) and the #1839
capability-matrix idea (gating layers, not session-type routing); neither covers the dispatch
precondition.

## ⟲ Previous-session review (Q-0102)

Reviewed `.sessions/2026-07-08-email-two-layer-flagship.md`: strong session — it corrected a
now-inaccurate flagship claim promptly after #1839's finding, aligned to the authoritative
addendum rather than re-deriving from a screenshot, and its "⚑ Live corroboration" note
(auto mode denied its own force-push mid-session, first-hand) is exactly the lived-incident
evidence the EAP guidebook asks for. Improvement it surfaces for the system: that session hit
the force-push wall and recovered by shipping from a fresh branch — a recovery pattern that
lives only in that card. This session's idea (dispatch-time toolset preconditions) is the same
class of fix generalized: known environment walls should be encoded where dispatchers and
sessions read them *before* acting, not rediscovered per-session.

## 📋 Documentation audit (Q-0104)

Ran `python3.10 scripts/check_docs.py --strict` (all checks passed) and
`python3.10 scripts/check_quality.py --check-only` (all checks passed). The session's durable
outputs live in their homes: probe evidence → the report addendum; EAP observation → the
evaluation log; process record → this card. No new owner decisions were made (nothing for the
question router); the ledger entry for PR #1842 lands via the normal reconciliation flow
(benign newest-merge lag). Nothing from this session exists only in chat.
