# Idea — an "audit-seam coverage" checker (catch unaudited mutations at authoring time)

> **Status:** `ideas` — not approved. Captured 2026-07-05 (Q-0089) from the "save fixes" session
> (PR #1728).
> **Subsystem:** none (cross-cutting, `scripts/` tooling)

## The pattern this would catch

Four of the eight Stage-2 "save fixes" (#1728) were the **same defect class**: a code path that
performs a real mutation *without ever reaching the audited seam* (`emit_audit_action`):

- **bug #3** — admin cog load/unload/reload + restart + log-level: runtime mutations, zero audit.
- **bug #5** — security raid-lockdown slowmode: a direct `channel.edit()` that bypassed
  `ChannelLifecycleService` (and thus its audit companion).
- **bug #6** — the word/strict toggles wrote `utils.db` directly (no audit) and `!cleanuphistory`
  called `apply_history_cleanup_plan` directly while moderation routed the *same* function through
  the audited `_record_action`.

Each was invisible until a human walked the subsystem. The existing
`test_no_direct_channel_mutations` invariant catches *one* narrow slice (channel mutations in
`channel_cog` + `views/channels`) — this session widened it to `security_service` (the
friction→guard for bug #5), but that is a whack-a-mole, file-by-file allowlist.

## The idea

A general **audit-coverage checker** (AST-based, on the repo's own graph — same family as
`check_architecture.py`) that flags any function which performs a **state mutation** whose success
path does **not** reach `emit_audit_action` (directly or through a known audited seam):

- **Mutation signals:** a call to `<x>.edit()/.delete()/.set_permissions()/.clone()` on a
  Discord object; a `pool.execute`/`INSERT`/`UPDATE`/`DELETE` outside `utils/db/`; a call into a
  known mutation-table write helper (e.g. `db.add_prohibited_word`, `db.set_wordfilter_strict`).
- **Audited-seam signals:** the function (or a callee it delegates to) reaches
  `emit_audit_action`, or routes through a registered `*_mutation` / lifecycle service that does.
- **Verdict:** a mutation with no reachable audit → a finding, unless allow-listed in
  `architecture_rules/` with a reason (the same bypass mechanism `check_architecture` uses).

This turns "did we remember to audit this?" from a subsystem-walk discovery into a CI signal —
it would have caught bugs #3/#5/#6 at authoring time.

## Why it's disposable / graduated (Q-0105)

Start it **advisory** (warn-only, unverified): the reachability analysis for "does this eventually
audit?" is exactly the kind of heuristic that false-positives (the CodeGraph `dead-unresolved`
lesson). Run it a few sessions, confirm its findings against ground truth, and only then promote it
to a hard gate. If it proves noisy across multiple sessions, delete it — the subsystem walk is the
backstop.

## Prior art in-repo

- `scripts/check_architecture.py` + `architecture_rules/` (the AST + allowlist pattern to reuse).
- `tests/unit/invariants/test_no_direct_channel_mutations.py` (the narrow, per-file version this
  generalizes).
- The mutation-seam rule in `.claude/CLAUDE.md` and `docs/ownership.md` (the contract it enforces).
