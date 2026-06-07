# 2026-06-07 — Server-management PR10 (fourth slice): post-action message cleanup

- **Arc:** Session framed as a **test of the documentation structure** — "locate the next
  planned stage and execute as much as you can safely do." The read path
  (`CLAUDE.md → collaboration-model → current-state → AGENT_ORIENTATION` task route → folio →
  **status tracker** → `roadmap.md`) all agreed: **server-management → remaining PR10**. Source
  confirmed the three contained slices shipped (the third, #558 warn-escalation, despite
  `current-state` still tagging it "pending"). The **entire** remaining PR10 queue is the
  cross-cutting remainder, so I surfaced the three items with risk analysis via
  `AskUserQuestion`; maintainer chose **post-action cleanup**. Branch
  `claude/awesome-feynman-UADHl` off merged `main` (`61d44d4`, #566). **PR #567.**
- **Shipped (PR10 fourth slice):**
  - **`post_action_cleanup`** (enum none/kick/ban/both) + **`post_action_cleanup_limit`**
    (1–500, default 100); schema → **v4**; keys `MOD_POST_ACTION_CLEANUP[_LIMIT]`. **Default
    OFF**, no migration (scalar/KV).
  - **`moderation_config`** — two fields on `ModerationPolicy`, `effective_…_limit` clamp, pure
    `cleanup_applies_to(action, policy)` (fail-safe on unknown → never sweeps).
  - **`moderation_service.kick`/`.ban`** take an optional invoking `channel`, return a frozen
    **`CleanupOutcome`**, and **own** the orchestration at the seam (one place, not copied into
    cog + modals). The sweep is **requested from** `services.history_cleanup`
    (new author-scoped `build_author_cleanup_plan` + shared `apply_history_cleanup_plan`) — so
    moderation re-implements **no** deletion mechanics (roadmap §430). Best-effort: a missing
    Read History / Manage Messages → `blocked` outcome, **never undoes** the action; only a
    non-empty sweep is audited (`post_action_cleanup`, teal 🧽 in `server_logging`, mod channel).
  - **Root-cause dedup found en route:** extracted the `!cleanuphistory` delete loop into
    `apply_history_cleanup_plan`, so the command and the moderation sweep share **one** delete
    path (helper-policy 2-caller rule).
- **Why this was the right "safe" envelope:** all three remaining PR10 items genuinely sit in
  the act-vs-ask "ask" zone (the tracker flagged them as cross-cutting). I built the one the
  owner picked, default-OFF + irreversible-aware, and **deferred** the other two as each their
  own decision: **mod/trusted roles + capabilities** (the per-capability tier matrix
  `capability-authority.md` defers to an ADR-005 revisit) and dedicated/optional **public log
  destinations** (server-logging routing + a privacy call).
- **Drift fix:** reconciled `current-state.md` — #558 (warn-escalation) and #566 (cross-area
  roadmap) were still tagged "pending" though merged in `main`. The exact living-ledger drift
  the doc structure exists to catch.
- **Tests:** new `tests/unit/services/test_history_cleanup.py` (author-plan + apply);
  `cleanup_applies_to`/clamp/policy in `test_moderation_config.py`; kick/ban-cleanup
  (configured/disabled/no-channel/blocked/empty-sweep) in `test_moderation_service.py`;
  `post_action_cleanup` shape + drift guard + **v4** in `test_moderation_schemas.py`;
  command-map doc updated for the doc-pin tests.
- **Gates:** `check_quality --full` green (**7788 passed**, 16 skipped; black/isort/ruff/mypy);
  `check_architecture --mode strict` **0 errors**; `check_docs` green. (Sandbox had no live boot
  this session — pure config/service change, default-OFF.) **For project state see
  `docs/current-state.md`; authoritative queue is the server-management status tracker.**
