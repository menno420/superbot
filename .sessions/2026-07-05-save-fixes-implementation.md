# 2026-07-05 — Stage-2 "save fixes" implementation (queued current-bot bug fixes)

> **Status:** `complete` — the deliberate final flip (born-red gate, Q-0133). Full CI mirror green:
> black/isort/ruff + mypy (881 files) + check_docs --strict + check_architecture (0 errors) + 14095
> tests pass (the only pytest errors are the 5 pre-existing `test_atlas`/grimp cases — grimp is
> dev-only and absent in real CI, and they occur identically on clean main).

## What this session did

Executed the handoff from the 2026-07-05 Stage-2 subsystem walk
(`docs/planning/rebuild-stage2-subsystem-walk-2026-07-05.md` §7): implemented the **8 owner-decided
"fix now" current-bot bugs** (§7.1), each with unit coverage. Framed by the rebuild-backport
strategy — maximize **safe executable lock-in** (audit-seam completeness, lifecycle guarantees,
authority correctness, restart-safety) in the *current* bot while deliberately **refusing** the
Class-C feature scope (§7.2 case/appeal, quarantine, auto-close) that would grow a second
half-built architecture beside the old one.

Each of the 8 specs (a prior session's output) was independently verified against live source by a
parallel skeptic-fleet workflow *before* implementation — which sharpened three of them (below).

## Shipped (PR #1728)

**8 bug fixes (root-cause; audit-seam / lifecycle / authority correctness):**
1. **settings** (`ai_policy_mutation` + `settings_mutation`) — the AI typed-policy projection is a
   separate write from the committed KV write; a failure used to be swallowed while the audit said
   "changed" (silent drift). Now: bounded retry in `project_from_legacy_settings` (self-heals
   transients) + the pipeline surfaces an exhausted failure as `projection_committed=False` and
   logs it at ERROR. **Rejected the spec's "same transaction" option** (a 4-file cross-module
   refactor that breaks the emit-after-commit contract) — recorded why.
2. **admin** — `bot_spam` → `bot-spam` one-line typo (dead startup greeting).
3. **admin** — audit trail on 5 high-privilege runtime mutations (cog load/unload/reload, restart,
   log-level) via best-effort cog-layer `emit_audit_action` (mirrors `proof_channel._emit_prize_audit`).
4. **moderation** — `/moderation` slash now honours the configured `moderator_role`
   (`_require_mod_slash` → `can_execute`). **Refinement:** also **drops** `@default_permissions`
   — keeping it would leave the bug half-fixed (Discord hides the slash from exactly the role-only
   mods the fix admits). Matches the runtime-only authority of `!modmenu` + the panel.
5. **security** — raid-lockdown slowmode routed through the audited `ChannelLifecycleService`
   `set_slowmode` seam (was a bare `channel.edit()`), `actor_type="system"`.
6. **cleanup** — word/strict toggles + `!cleanuphistory` bulk delete routed through audited seams
   (new `services/prohibited_words_service.py`; `moderation_service.apply_channel_cleanup`).
   **Refinement:** fixed **two extra** unaudited surfaces the spec missed (the add/remove modals)
   and a `views`-layer direct-DB write in `_WordMenuView`.
7. **role** — 3 guild-scoped tables (`role_thresholds`, `role_automation_exemptions`,
   `reaction_roles`) were never cleaned on guild-leave; added teardown steps + 3 `utils.db.roles`
   helpers + corrected two false "self-cleans" comments.
8. **proof_channel** — timed prize locks now persist their unlock deadline (migration 104 +
   `utils/db/proof_channel_locks.py`) and a boot reconcile sweep unlocks lapsed locks / reschedules
   pending ones — the channel no longer stays locked forever after a restart. (This is exactly the
   `deferred-action-restart-recovery-checker` idea the previous session captured — bug 8 is a
   confirmed instance.)

**Lock-in extras:** friction→guard — the `test_no_direct_channel_mutations` invariant now also
scans `security_service` (the bypass class bug #5 was). ~30 new unit tests across the 8 fixes.
`docs/ownership.md` updated (cleanup + proof_channel rows were stale after these changes).

**Deferred (NOT in #1728, needs design/owner UX):** §7.2 case/appeal, bulk moderation, quarantine,
voice-channel-creation wiring, ticket config-fields + slash + auto-close, auto-mod-tier panels,
role slash mirrors; and the zero-risk §7.2 deletions (orphaned capability strings, dead
`RoleHubView`) — the deletions-verification agent didn't complete, so I kept this PR to the 8
verified fixes rather than ship unverified deletions.

## Context delta

- **Needed but not pointed to:** the two ownership.md rows (cleanup / proof_channel) that my
  changes made stale weren't flagged by any checker — I found them by reading ownership.md while
  doing the Q-0104 audit. (The new "audit-seam coverage checker" idea would not catch *doc* drift;
  a doc-vs-code ownership checker remains a gap.)
- **Pointed to but didn't need:** nothing significant — the walk doc §7 specs were precise
  (`file:line` + the seam to mirror), which made the verify-then-implement loop fast.
- **Discovered by hand:** `cog_manager.py`'s docstring already declares it exists to hold
  `admin_cog` overflow under the 800-LOC ceiling — so it was the right home when my audit helper
  pushed `admin_cog` to 859 (fixed by moving `_emit_admin_runtime_audit` + `_LogLevelModal` there
  → 782). The 800-LOC ceiling trap (CLAUDE.md) bit exactly as documented — caught by the local CI
  mirror, not by eyeballing.
- **Decisions made alone (ratify):** (a) **dropped `/moderation`'s `@default_permissions`** —
  a visible client-side UX change (the slash becomes visible to all members; non-mods denied at
  runtime). I judged it necessary to actually deliver the owner-decided bug #4 fix (the panel
  precedent the owner cited is runtime-only), and reversible. (b) `!cleanuphistory` now writes a
  `mod_logs` row (via the shared `_record_action` fan-out) — faithful to the spec's "same wrapper"
  and gives operator parity, but it does put a cleanup action in the moderation log.
- **Flagged for maintainer:** the `default_permissions` removal (4b above) is the one visible
  behavior change to confirm on the live bot. The AI-projection fix makes drift *loud + self-healing*
  but does not make the two writes atomic — a *persistent* projection failure still leaves real
  drift (now flagged, not silent); the durable belt-and-suspenders is a periodic re-projection
  reconciler (noted as a follow-up, not built).
- **🛠 Friction → guard:** bug #5's direct-`channel.edit()` bypass slipped past
  `test_no_direct_channel_mutations` because that invariant only scanned `channel_cog` + channel
  views → **widened it to scan `security_service`** (test-tier guard, shipped this PR). The broader
  version (scan every service/cog for unaudited mutations) is filed as the Q-0089 idea below rather
  than hand-rolled per-file forever.

## ⟲ Previous-session review (Q-0102)

Previous session = the **Stage-2 subsystem walk** (#1725, 2026-07-05). Strong: it produced exactly
the artifact this session needed — 8 bug specs with `file:line` anchors *and* the audited seam to
mirror for each, so verification was confirmation not archaeology. It also correctly scoped itself
(docs-only, queued the fixes) rather than half-implementing them live.

**What it could have done better, from this vantage:** three of its eight specs had drifted or
incomplete details that only surfaced under source-verification — bug #4's spec didn't mention that
the `app_perms_or_owner` decorator must be *removed* (not supplemented) or that `default_permissions`
would still hide the command; bug #6's spec missed two unaudited modal surfaces and a view→DB write;
bug #1's "same transaction" remedy is not cleanly feasible. **Concrete improvement:** a walk that
queues a fix should note its *confidence* per spec (e.g. "seam confirmed, call-sites grep-verified"
vs "sketch") so the implementing session knows which specs to re-derive vs trust — the walk already
did `file:line` anchoring, one step short of a confidence tag. (This is a light extension, not a
gap — the specs were good enough that verify-then-build was smooth.)

## 💡 Session idea (Q-0089)

[`audit-seam-coverage-checker-2026-07-05.md`](../docs/ideas/audit-seam-coverage-checker-2026-07-05.md)
— a general AST checker (on the repo's own graph, `architecture_rules/` allowlist) that flags any
function performing a state mutation whose success path never reaches `emit_audit_action`.
**Genuine belief:** four of this session's eight fixes (#3/#5/#6) were the identical "unaudited
mutation" class, each found only by a human walk; this would catch that class in CI. Start advisory
(Q-0105), graduate on proof. Dedup-checked against the existing `deferred-action-restart-recovery-checker`
idea (different class — that one is restart-recovery, this is audit-coverage).

## 🧹 Grooming (Q-0015)

Advanced the [`deferred-action-restart-recovery-checker`](../docs/ideas/deferred-action-restart-recovery-checker-2026-07-05.md)
idea toward a plan by adding a *confirmed second production instance*: bug #8 (proof_channel timed
unlock) is exactly the gap that idea describes, now fixed — so the checker would have two real
positives to validate against (security raid-lockdown was already noted). That strengthens the case
for building it next.

## 📋 Docs audit (Q-0104)

- `docs/ownership.md` — updated the `cleanup` and `proof_channel` rows (both went stale from this
  session's new audited seams + the new `proof_channel_locks` table).
- `docs/planning/rebuild-stage2-subsystem-walk-2026-07-05.md` §7 — added an IMPLEMENTED status
  banner for §7.1 pointing at #1728 (durable home for "what's left").
- New docs: 1 idea file + its README index entry.
- `docs/current-state.md` Recently-shipped: **not** touched — convention is merged-PRs-only; the
  next Q-0107 reconciliation pass (due at #1740) records #1728.
- `check_quality.py --check-only` (incl. `check_docs`) green; `check_architecture --mode strict`
  0 errors.

## 📤 Run report

- **Did:** implemented the 8 queued Stage-2 current-bot bug fixes (audit-seam / lifecycle /
  authority correctness) + tests + a friction→guard, into the current bot. · **Outcome:** shipped
- **Shipped:** #1728 — the "save fixes" (8 root-cause bug fixes; ~30 new tests; migration 104; 2
  new service/db modules; ownership.md + walk-doc §7 updated)
- **Run type:** `manual` (owner-directed ultracode session)
- **⚑ Owner decisions needed:** none blocking — but **confirm on the live bot** the one visible UX
  change: `/moderation` is now visible to all members (runtime-denied for non-mods) because its
  client-side `@default_permissions` hide was dropped to fully fix bug #4.
- **⚑ Owner manual steps:** none (merge auto-deploys; migration 104 self-applies at boot).
- **⚑ Self-initiated:** the Q-0089 audit-seam-coverage-checker idea (captured, not built); the
  friction→guard invariant widening (shipped) — both flagged per Q-0172/Q-0194.
- **↪ Next:** the §7.2 committed feature scope (case/appeal, quarantine, ticket fields, auto-mod
  panels, …) + the §7.2 zero-risk deletions, then continue the Stage-2 walk at L1c (owner-live).

## 📊 Telemetry

| Metric | Value |
|---|---|
| PRs merged this session | 1 (#1728, on green) |
| CI-red rounds | 0 on the PR — the 800-LOC ceiling trip + cog move was caught by the local full CI mirror before the code push (the mirror's whole purpose); the born-red gate red is the intended hold, not a round |
| Repo-rule trips | 1 (`test_cog_size` 800-LOC ceiling on `admin_cog.py` — caught locally, fixed by relocating to `cog_manager.py`) |
| New ideas contributed | 1 (Q-0089 audit-seam-coverage-checker) |
| Ideas groomed | 1 (advanced the restart-recovery-checker idea with a 2nd confirmed instance) |
