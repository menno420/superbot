# 2026-06-19 — Ground-truth audit protocol + plan-code-drift check

> **Status:** `complete`

Owner-directed (router **Q-0181**) follow-up to the 2026-06-19 review that found A3/A4 plans
shipped-but-`plan`-badged — the "why didn't the docs-cleanup check plans vs code?" thread.

## Shipped
- **`scripts/check_plan_code_drift.py`** — flags `plan`-badged docs whose named implementation already
  exists in `disbot/` (`STRONG` = named file + plan-specific symbol; a specificity filter drops shared
  infra like `BaseView`/`SettingSpec`). Catches A3/A4; narrows 36 plans → ~7 STRONG candidates. Advisory
  (`--strict` to gate once trusted). Lint-clean (black/ruff).
- **`docs/operations/ground-truth-audit-protocol.md`** — the reusable *"verify against code, not badges"*
  contract; template = `docs/audits/repo-wide-audit-2026-05-29.md` (the 22-auditor fan-out, owner's depth bar).
- Router **Q-0181** — provenance + the *proposed* (not-yet-applied) session-close / Stop-hook wiring.

## ⟲ Previous-session review
The ultracode-review verification earlier this session was shallow — cheap proxies (doc badges,
commit-message grep) over the code — so it mis-fingered B3 (actually shipped #960) and missed A2's
mislabel. The durable fix is now structural (this check + protocol), not "remember to verify." System
improvement: ground-truth verification is now both **invokable** (the protocol) and **partly automated**
(the check), closing the recurring badge-drift class instead of relying on prompt wording.

## 💡 Session idea
A **diff-aware Stop-hook** that maps a session's touched `disbot/` files → the plans that name them →
a rebadge prompt, so every session reconciles the plans it actually shipped (captured as the proposed
half of Q-0181).
