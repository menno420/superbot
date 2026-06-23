- `claude/ai-setup-edit-button` · **AI-setup advisor: Accept · Deny · Edit (the Q-0048 finalize)** —
  owner-directed (Q-0048 decision 2026-06-23: AI applies setup changes but only after confirmation, with
  three per-suggestion buttons accept/deny/edit). The propose→stage→Final-Review→audited-apply path already
  exists (#1355/#1357/#1361 + `views/setup/ai_review/`); this adds the missing **Edit** affordance on the
  per-recommendation walkthrough (rename Reject→Deny; add Edit → modal to rename a `create` suggestion before
  accepting). Stays propose-only (no DB/Discord writes here — apply remains the gated Final Review). Scope:
  `disbot/views/setup/ai_review/per_recommendation.py`, `tests/unit/views/setup/ai_review/`. 2026-06-23 ·
  PR (this session, auto-merge on green)
