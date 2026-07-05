# 2026-07-05 — Stage-2 "save fixes" implementation (queued current-bot bug fixes)

> **Status:** `in-progress` — born-red card (held by `check_session_gate` until the deliberate
> final flip). This session implements the 8 owner-decided "fix now" current-bot bugs queued by the
> 2026-07-05 Stage-2 subsystem walk (§7.1) plus zero-risk §7.2 deletions and §7.4 verification tests.

## What this session is doing

Executing the handoff from `docs/planning/rebuild-stage2-subsystem-walk-2026-07-05.md` §7 — the
owner's stated plan for "an Opus session that fixes the 7 queued bugs and starts implementing some
of §7.2's committed scope into the current bot." Framed by the rebuild-backport strategy: maximize
**safe executable lock-in** of accepted rebuild decisions (audit-seam completeness, lifecycle
guarantees, authority correctness, restart-safety) in the *current* bot — while deliberately
refusing the Class-C "new design" items (case/appeal, quarantine, auto-close) that would grow a
second half-built architecture. Every spec is verified against live source before implementation
(the specs are a prior session's output → input to verify, per the working agreement).

## Scope (this PR)

**§7.1 — 8 bug fixes (root-cause, audit-seam/lifecycle/authority correctness):**
1. settings AI-projection non-transactional drift
2. admin `bot_spam`/`bot-spam` typo (dead startup greeting)
3. admin — audit trail on 5 high-privilege mutations
4. moderation `/moderation` slash ignores configured `moderator_role`
5. security raid-lockdown slowmode bypasses audit seam
6. cleanup — two unaudited mutation paths (word/strict toggles + `!cleanuphistory`)
7. role — 3-of-8-table guild-teardown gap + false "self-cleans" comment
8. proof_channel — restart leaves channel locked forever (in-memory-only deadline)

**Zero-risk §7.2 lock-in (deletions with confirmed zero references):** orphaned capability strings
(channel ×5, role ×3), dead `views/roles/main_panel.py` `RoleHubView` — included only where the
verification lane confirms zero live references.

**§7.4 — verification-gap tests** wherever the above touches previously-untested paths.

**Deferred (out of this PR — need design/owner-facing UX, per backport discipline):** case/appeal
system, bulk moderation actions, quarantine, voice-channel-creation wiring, ticket config-field
exposure + slash mirrors + auto-close, auto-mod-tier panel consolidation, role slash mirrors.

<!-- The Did/Outcome/enders/telemetry are filled in at the deliberate final flip to `complete`. -->
