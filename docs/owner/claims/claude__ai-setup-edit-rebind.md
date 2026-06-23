- `claude/ai-setup-edit-rebind` · **AI-setup Edit: re-pick target for `bind` suggestions (self-initiated)** —
  completes #1386's Edit affordance. Currently Edit renames `create` suggestions and only *explains* for
  `bind`; this lets Edit on a `bind` suggestion open a channel/role select to re-pick the existing target
  in place (apply_retarget → swap target_id/name → accept → advance). Propose-only (no writes; applies via
  the gated Final Review). Self-initiated follow-on (flagged per Q-0172). Scope:
  `disbot/views/setup/ai_review/per_recommendation.py`, `tests/`. 2026-06-23 · PR (this session, auto-merge on green)
